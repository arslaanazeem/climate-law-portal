"""
Import cases from a JSON file.

The JSON file must contain a top-level list of objects. Each object
supports the same keys as the CSV importer:
    case_title (required), court, country, year, violation_type,
    summary, full_text, tags (list or comma-string), source_file

Usage:
    python manage.py import_cases_json path/to/cases.json [--reset]
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from cases.models import Case


def _parse_year(value):
    if value in (None, ""):
        return None
    try:
        y = int(value)
    except (TypeError, ValueError):
        return None
    return y if 1900 <= y <= 2100 else None


def _parse_tags(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [t.strip() for t in str(value).split(",") if t.strip()]


class Command(BaseCommand):
    help = "Bulk-import Case rows from a JSON file (a top-level list of objects)."

    def add_arguments(self, parser):
        parser.add_argument("json_path")
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--batch-size", type=int, default=500)

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["json_path"]).expanduser().resolve()
        if not path.exists():
            raise CommandError(f"JSON not found: {path}")

        with path.open("r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except json.JSONDecodeError as exc:
                raise CommandError(f"Invalid JSON: {exc}") from exc

        if not isinstance(data, list):
            raise CommandError("Top-level JSON must be a list of objects.")

        if opts["reset"]:
            n = Case.objects.count()
            Case.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {n} existing cases."))

        used_slugs: set[str] = set(Case.objects.values_list("slug", flat=True))
        buffer: list[Case] = []
        created = skipped = 0

        for raw in data:
            if not isinstance(raw, dict):
                skipped += 1
                continue
            title = (raw.get("case_title") or "").strip()
            if not title:
                skipped += 1
                continue

            case = Case(
                case_title=title,
                court=(raw.get("court") or "").strip(),
                country=(raw.get("country") or "Pakistan").strip() or "Pakistan",
                year=_parse_year(raw.get("year")),
                violation_type=(raw.get("violation_type") or "other").strip() or "other",
                summary=raw.get("summary") or "",
                full_text=raw.get("full_text") or "",
                source_file=(raw.get("source_file") or "").strip(),
            )
            case.set_tags(_parse_tags(raw.get("tags")))
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
            f"JSON import complete. Created={created}  Skipped={skipped}  Total={len(data)}"
        ))

    @staticmethod
    def _unique_slug(title: str, used: set[str]) -> str:
        base = slugify(title)[:200] or "case"
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        return slug
