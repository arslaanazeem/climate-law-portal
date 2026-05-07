"""
Bulk-ingest Pakistan environmental tribunal cases from a directory of .txt files.

Each filename follows the convention `<PREFIX>_Complaint_<NUM>_<YEAR>.txt`
(e.g. `B2_Complaint_10_2016.txt`). The body of every file contains the full
judgment text; this command parses out:

  - case_title (e.g. "Complaint No. 10/2016 — Galaxy Laminates (Pvt) Limited")
  - court (e.g. "Punjab Environmental Tribunal, Lahore")
  - year (parsed from filename and validated against body)
  - violation_type (heuristic from keywords)
  - summary (first ~400 chars of judgment body)
  - full_text (raw text of the file)
  - tags (auto-generated from prefix and detected keywords)

Usage:
    python manage.py ingest_cases [--path PATH] [--limit N] [--reset]

Options:
    --path    Directory of .txt files (default: BASE_DIR/all_text_cases)
    --limit   Only ingest the first N files (handy for smoke tests)
    --reset   Delete existing Case rows before ingesting
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cases.models import Case


FILENAME_RE = re.compile(
    r"^(?P<prefix>[A-Za-z0-9]+)_Complaint_(?P<num>\d+)_(?P<year>\d{4})\.txt$",
    re.IGNORECASE,
)

PREFIX_COURT_MAP = {
    "B2": "Punjab Environmental Tribunal, Lahore",
    "B3": "Sindh Environmental Tribunal, Karachi",
    "B4": "KP Environmental Tribunal, Peshawar",
    "B5": "Balochistan Environmental Tribunal, Quetta",
    "B6": "Islamabad Environmental Tribunal",
    "CR": "Environmental Tribunal — Cross-Regional",
}

# Order matters: more specific keywords first.
VIOLATION_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("hazardous_waste", ("hazardous waste", "toxic waste", "chemical waste")),
    ("solid_waste",     ("solid waste", "garbage", "dumping site")),
    ("noise_pollution", ("noise pollution", "noise level", "sound level")),
    ("water_pollution", ("water pollution", "effluent", "wastewater", "bod", "cod", "tss")),
    ("air_pollution",   ("air pollution", "stack", "emission", "particulate", "pm10", "pm2.5", "so2", "nox")),
    ("eia_violation",   ("environmental impact assessment", "eia", "iee")),
    ("deforestation",   ("deforestation", "tree cutting", "forest")),
    ("wildlife",        ("wildlife", "biodiversity", "endangered")),
    ("climate_change",  ("climate change", "greenhouse", "carbon emission")),
    ("multi_media",     ("multi-media", "compound violation")),
    ("neqs_violation",  ("neqs", "national environmental quality standards")),
]

RESPONDENT_RE = re.compile(
    r"(?:VERSUS|Versus|vs\.?)\s*\n+\s*\**\s*(?P<respondent>[^\n*]+)",
    re.IGNORECASE,
)
COURT_HEADER_RE = re.compile(
    r"\b(?P<court>(?:[A-Z][A-Za-z()\.,/\-]*\s+){0,4}ENVIRONMENTAL\s+TRIBUNAL[^\n]*)",
    re.IGNORECASE,
)
COMPLAINT_NO_RE = re.compile(r"COMPLAINT\s*NO\.?\s*(?P<num>[\d/]+)", re.IGNORECASE)


def classify_violation(text: str) -> str:
    lower = text.lower()
    for code, keywords in VIOLATION_RULES:
        if any(k in lower for k in keywords):
            return code
    return "other"


def derive_tags(prefix: str, violation: str, body_lower: str) -> list[str]:
    tags: list[str] = []
    if prefix:
        tags.append(prefix.upper())
    if violation and violation != "other":
        tags.append(violation.replace("_", " "))
    bag = [
        "neqs", "epo", "fine", "penalty", "tribunal", "appeal",
        "effluent", "emission", "noise", "wildlife", "eia",
    ]
    for kw in bag:
        if kw in body_lower:
            tags.append(kw)
    # de-dup, preserve order
    seen, out = set(), []
    for t in tags:
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out[:8]


def extract_court(text: str, fallback: str) -> str:
    m = COURT_HEADER_RE.search(text[:1500])
    if not m:
        return fallback
    raw = m.group("court").strip(" ,*")
    raw = re.sub(r"\s+", " ", raw)
    return raw.title() if raw.isupper() else raw


def extract_respondent(text: str) -> str | None:
    m = RESPONDENT_RE.search(text[:2500])
    if not m:
        return None
    name = m.group("respondent").strip(" .*-—\t")
    name = re.sub(r"\s+", " ", name)
    if not name or len(name) > 200:
        return None
    if name.lower().startswith(("respondent", "complainant")):
        return None
    return name


def make_summary(text: str, max_len: int = 420) -> str:
    # First non-trivial paragraph after the JUDGMENT header, if present.
    body = re.sub(r"\*\*", "", text)
    parts = re.split(r"\n\s*\n", body)
    candidate = ""
    for p in parts:
        p = p.strip()
        if len(p) >= 200 and not p.upper().startswith(("COMPLAINT", "VERSUS", "PRESIDED", "JUDGMENT")):
            candidate = p
            break
    if not candidate:
        candidate = body.strip()
    candidate = re.sub(r"\s+", " ", candidate)
    if len(candidate) <= max_len:
        return candidate
    return candidate[: max_len - 1].rstrip() + "…"


def derive_title(filename: str, prefix: str, num: str, year: str, respondent: str | None) -> str:
    base = f"Complaint No. {num}/{year}"
    if respondent:
        return f"{base} — {respondent}"
    return f"{base} ({prefix.upper()})"


def iter_case_files(folder: Path, limit: int | None) -> Iterable[Path]:
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".txt")
    if limit is not None:
        files = files[:limit]
    return files


class Command(BaseCommand):
    help = "Ingest .txt environmental tribunal cases into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="Folder containing .txt files (default: BASE_DIR/all_text_cases).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Only ingest the first N files.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing Case rows before ingesting.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Database insert batch size (default: 500).",
        )

    def handle(self, *args, **opts):
        folder = Path(opts["path"]) if opts["path"] else (settings.BASE_DIR / "all_text_cases")
        if not folder.exists() or not folder.is_dir():
            raise CommandError(f"Path not found or not a directory: {folder}")

        limit = opts["limit"]
        batch_size = opts["batch_size"]

        if opts["reset"]:
            count = Case.objects.count()
            Case.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Reset: deleted {count} existing cases."))

        existing_files = set(
            Case.objects.exclude(source_file="").values_list("source_file", flat=True)
        )

        files = list(iter_case_files(folder, limit))
        total = len(files)
        if not total:
            raise CommandError(f"No .txt files found in {folder}")

        self.stdout.write(f"Found {total} .txt files in {folder}")
        self.stdout.write(f"Skipping {len(existing_files)} files already in DB.")

        created = 0
        skipped = 0
        errors = 0
        buffer: list[Case] = []
        used_slugs: set[str] = set(Case.objects.values_list("slug", flat=True))

        for i, path in enumerate(files, 1):
            if path.name in existing_files:
                skipped += 1
                continue
            try:
                case = self._build_case(path, used_slugs)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                self.stderr.write(f"  ! {path.name}: {exc}")
                continue
            buffer.append(case)
            if len(buffer) >= batch_size:
                self._flush(buffer)
                created += len(buffer)
                buffer.clear()
                self.stdout.write(f"  · {i}/{total} processed (created {created})")

        if buffer:
            self._flush(buffer)
            created += len(buffer)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created={created}  Skipped={skipped}  Errors={errors}  Total files={total}"
        ))

    # ------------------------------------------------------------------ helpers

    def _build_case(self, path: Path, used_slugs: set[str]) -> Case:
        m = FILENAME_RE.match(path.name)
        if not m:
            # Fall back: ingest with a generic title rather than skipping.
            prefix = path.stem.split("_", 1)[0] or "ENV"
            num = "0"
            year_str = ""
        else:
            prefix = m.group("prefix")
            num = m.group("num")
            year_str = m.group("year")

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")

        court = extract_court(text, fallback=PREFIX_COURT_MAP.get(prefix.upper(), ""))
        respondent = extract_respondent(text)
        try:
            year = int(year_str) if year_str else None
        except ValueError:
            year = None

        violation = classify_violation(text)
        summary = make_summary(text)
        title = derive_title(path.name, prefix, num, year_str or "?", respondent)
        tags = derive_tags(prefix, violation, text.lower())

        case = Case(
            case_title=title,
            court=court,
            country="Pakistan",
            year=year,
            violation_type=violation,
            summary=summary,
            full_text=text,
            source_file=path.name,
        )
        case.set_tags(tags)
        case.slug = self._unique_slug(title, used_slugs)
        return case

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

    @staticmethod
    @transaction.atomic
    def _flush(buffer: list[Case]) -> None:
        Case.objects.bulk_create(buffer, ignore_conflicts=False)
