"""
Import cases from a CSV file.

Expected columns (case-insensitive, extra columns ignored):
    case_title, court, country, year, violation_type,
    summary, full_text, tags, source_file

`tags` may be either a comma-separated string or a JSON list.

Usage:
    python manage.py import_cases_csv path/to/cases.csv [--reset] [--encoding utf-8]
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cases.models import Case


REQUIRED_COLUMNS = {"case_title"}
OPTIONAL_COLUMNS = {
    "court", "country", "year", "violation_type",
    "summary", "full_text", "tags", "source_file",
}


def _parse_year(value):
    if value in (None, ""):
        return None
    try:
        y = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    if 1900 <= y <= 2100:
        return y
    return None


def _parse_tags(value):
    if not value:
        return []
    text = str(value).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            pass
    return [t.strip() for t in text.split(",") if t.strip()]


class Command(BaseCommand):
    help = "Bulk-import Case rows from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to CSV file.")
        parser.add_argument("--reset", action="store_true", help="Delete all cases before import.")
        parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8).")
        parser.add_argument("--batch-size", type=int, default=500)

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["csv_path"]).expanduser().resolve()
        if not path.exists():
            raise CommandError(f"CSV not found: {path}")

        if opts["reset"]:
            n = Case.objects.count()
            Case.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {n} existing cases."))

        created = 0
        skipped = 0
        buffer: list[Case] = []
        used_slugs: set[str] = set(Case.objects.values_list("slug", flat=True))

        with path.open("r", encoding=opts["encoding"], newline="") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                raise CommandError("CSV has no header row.")
            headers = {h.lower() for h in reader.fieldnames}
            missing = REQUIRED_COLUMNS - headers
            if missing:
                raise CommandError(f"CSV is missing required columns: {sorted(missing)}")

            for row in reader:
                row = {k.lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                title = (row.get("case_title") or "").strip()
                if not title:
                    skipped += 1
                    continue

                case = Case(
                    case_title=title,
                    court=row.get("court", "") or "",
                    country=row.get("country", "Pakistan") or "Pakistan",
                    year=_parse_year(row.get("year")),
                    violation_type=(row.get("violation_type") or "other").strip() or "other",
                    summary=row.get("summary", "") or "",
                    full_text=row.get("full_text", "") or "",
                    source_file=row.get("source_file", "") or "",
                )
                case.set_tags(_parse_tags(row.get("tags")))
                case.slug = self._unique_slug(title, used_slugs)
                buffer.append(case)

                if len(buffer) >= opts["batch_size"]:
                    Case.objects.bulk_create(buffer)
                    created += len(buffer)
                    buffer.clear()

            if buffer:
                Case.objects.bulk_create(buffer)
                created += len(buffer)

        self.stdout.write(self.style.SUCCESS(
            f"CSV import complete. Created={created}  Skipped={skipped}"
        ))

    @staticmethod
    def _unique_slug(title: str, used: set[str]) -> str:
        from django.utils.text import slugify

        base = slugify(title)[:200] or "case"
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        return slug
