"""End-to-end test suite — exercises models, search, views, admin, commands."""
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from cases.models import Case


class CaseModelTests(TestCase):
    def test_slug_auto_generated_and_unique(self):
        a = Case.objects.create(case_title="Same Title", year=2020)
        b = Case.objects.create(case_title="Same Title", year=2021)
        self.assertEqual(a.slug, "same-title")
        self.assertNotEqual(a.slug, b.slug)
        self.assertTrue(b.slug.startswith("same-title"))

    def test_tag_helpers(self):
        c = Case(case_title="Tag Test")
        c.set_tags(["NEQS", " neqs ", "Effluent", ""])
        self.assertEqual(c.tag_list, ["NEQS", "Effluent"])
        self.assertEqual(c.tags, "NEQS, Effluent")

    def test_short_summary_truncation(self):
        long_text = "x" * 500
        c = Case.objects.create(case_title="Long", summary=long_text)
        self.assertLessEqual(len(c.short_summary), 281)
        self.assertTrue(c.short_summary.endswith("…"))

    def test_get_absolute_url_uses_pk_and_slug(self):
        c = Case.objects.create(case_title="Routing Test", year=2022)
        url = c.get_absolute_url()
        self.assertIn(str(c.pk), url)
        self.assertIn(c.slug, url)


class CaseSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Case.objects.create(
            case_title="Effluent discharge — Galaxy Mills",
            court="Punjab Environmental Tribunal, Lahore",
            year=2018,
            violation_type="water_pollution",
            summary="BOD and COD exceedance at industrial outfall.",
            full_text="The respondent's effluent breached NEQS standards.",
            tags="effluent, NEQS",
        )
        Case.objects.create(
            case_title="Stack emissions — Crescent Steel",
            court="Punjab Environmental Tribunal, Lahore",
            year=2022,
            violation_type="air_pollution",
            summary="PM and SO2 above NEQS limits.",
            full_text="Stack emissions exceeded permissible NEQS levels for PM and SO2.",
            tags="emission, PM, SO2",
        )
        Case.objects.create(
            case_title="Noise complaint — Steel Mill",
            court="Punjab Environmental Tribunal, Lahore",
            year=2020,
            violation_type="noise_pollution",
            summary="Noise above 85 dB at boundary.",
            full_text="Boundary noise readings exceeded 85 dB.",
            tags="noise",
        )

    def test_search_matches_title_summary_fulltext(self):
        self.assertEqual(Case.objects.search("Galaxy").count(), 1)
        self.assertEqual(Case.objects.search("PM").count(), 1)
        self.assertEqual(Case.objects.search("85 dB").count(), 1)

    def test_search_empty_returns_all(self):
        self.assertEqual(Case.objects.search("").count(), 3)
        self.assertEqual(Case.objects.search(None).count(), 3)

    def test_filter_year_and_violation(self):
        self.assertEqual(Case.objects.filter_year(2020).count(), 1)
        self.assertEqual(Case.objects.filter_violation("air_pollution").count(), 1)

    def test_filter_year_with_invalid_input(self):
        self.assertEqual(Case.objects.filter_year("not-a-year").count(), 3)


class HomePageTests(TestCase):
    def test_home_renders(self):
        Case.objects.create(case_title="Demo Case", year=2021, violation_type="other")
        resp = self.client.get(reverse("cases:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Climate Law Intelligence Portal")
        self.assertContains(resp, "Demo Case")

    def test_about_and_health(self):
        self.assertEqual(self.client.get(reverse("about")).status_code, 200)
        h = self.client.get(reverse("health"))
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.content, b"ok")


class SearchViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(45):
            Case.objects.create(
                case_title=f"NEQS Case {i:03d}",
                year=2020 + (i % 5),
                violation_type="water_pollution" if i % 2 == 0 else "air_pollution",
                summary="Effluent and emission tests.",
                full_text="Detailed judgment text.",
            )

    def test_search_results_paginated(self):
        resp = self.client.get(reverse("cases:search"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "cases found")

    def test_pagination_page_two(self):
        resp = self.client.get(reverse("cases:search") + "?page=2")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Page 2 of")

    def test_pagination_out_of_range_returns_last_page(self):
        resp = self.client.get(reverse("cases:search") + "?page=99999")
        self.assertEqual(resp.status_code, 200)

    def test_filters_combine(self):
        resp = self.client.get(
            reverse("cases:search") + "?q=NEQS&year=2024&violation=water_pollution"
        )
        self.assertEqual(resp.status_code, 200)


class CaseDetailTests(TestCase):
    def setUp(self):
        self.case = Case.objects.create(
            case_title="Detail Test",
            year=2023,
            violation_type="water_pollution",
            full_text="A long judgment.",
        )

    def test_detail_canonical(self):
        resp = self.client.get(self.case.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Detail Test")
        self.assertContains(resp, "Full text")

    def test_detail_short_url(self):
        resp = self.client.get(reverse("cases:detail_short", args=[self.case.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_detail_404_for_unknown_pk(self):
        resp = self.client.get("/case/9999999/")
        self.assertEqual(resp.status_code, 404)

    def test_detail_tolerates_wrong_slug(self):
        resp = self.client.get(f"/case/{self.case.pk}/wrong-slug/")
        self.assertEqual(resp.status_code, 200)


class AdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            "admin", "admin@example.com", "passw0rd-strong"
        )
        self.client = Client()
        self.client.force_login(self.admin)

    def test_admin_changelist_loads(self):
        Case.objects.create(case_title="Admin Test", year=2022)
        resp = self.client.get("/admin/cases/case/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Admin Test")

    def test_admin_can_add_case(self):
        resp = self.client.post(
            "/admin/cases/case/add/",
            data={
                "case_title": "Admin Add",
                "slug": "admin-add",
                "court": "Test",
                "country": "Pakistan",
                "year": 2024,
                "violation_type": "other",
                "summary": "x",
                "full_text": "y",
                "tags": "a",
                "source_file": "",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Case.objects.filter(case_title="Admin Add").exists())


class IngestCommandTests(TestCase):
    def test_ingest_directory(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "B2_Complaint_42_2023.txt").write_text(
                """PUNJAB ENVIRONMENTAL TRIBUNAL
LAHORE
COMPLAINT NO. 42/2023
EPA
...Complainant
VERSUS
**Acme Industries (Pvt) Ltd**
...Respondent

JUDGMENT
The respondent discharged industrial effluent in breach of NEQS,
exceeding BOD and COD limits.
""",
                encoding="utf-8",
            )
            call_command("ingest_cases", path=str(folder))
            qs = Case.objects.all()
            self.assertEqual(qs.count(), 1)
            c = qs.first()
            self.assertIn("Complaint No. 42/2023", c.case_title)
            self.assertEqual(c.year, 2023)
            self.assertEqual(c.country, "Pakistan")
            self.assertEqual(c.violation_type, "water_pollution")

    def test_ingest_skips_already_ingested(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "B2_Complaint_1_2020.txt").write_text("dummy", encoding="utf-8")
            call_command("ingest_cases", path=str(folder))
            call_command("ingest_cases", path=str(folder))  # second run
            self.assertEqual(Case.objects.count(), 1)


class CSVImportTests(TestCase):
    def test_csv_import(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.csv"
            with path.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow([
                    "case_title", "court", "country", "year", "violation_type",
                    "summary", "full_text", "tags", "source_file",
                ])
                writer.writerow([
                    "CSV Case 1", "Lahore HC", "Pakistan", "2021", "air_pollution",
                    "Summary", "Body", "csv,test", "csv1.txt",
                ])
            call_command("import_cases_csv", str(path))
            self.assertEqual(Case.objects.count(), 1)
            c = Case.objects.first()
            self.assertEqual(c.year, 2021)
            self.assertEqual(c.tag_list, ["csv", "test"])


class JSONImportTests(TestCase):
    def test_json_import(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            payload = [{
                "case_title": "JSON Case 1",
                "court": "Lahore HC",
                "year": 2020,
                "violation_type": "water_pollution",
                "summary": "x",
                "full_text": "y",
                "tags": ["json", "test"],
            }]
            path.write_text(json.dumps(payload), encoding="utf-8")
            call_command("import_cases_json", str(path))
            self.assertEqual(Case.objects.count(), 1)
            c = Case.objects.first()
            self.assertEqual(c.tag_list, ["json", "test"])


class ErrorHandlerTests(TestCase):
    def test_404_handler(self):
        resp = self.client.get("/this-page-does-not-exist-xyz/")
        self.assertEqual(resp.status_code, 404)
