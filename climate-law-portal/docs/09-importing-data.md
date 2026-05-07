# 9. Importing data — three ways to load cases in bulk

The project ships with **three custom Django commands** for importing cases
in bulk. All three live in `cases/management/commands/`.

| Command | Use when you have… |
|---------|--------------------|
| `ingest_cases` | A folder of `.txt` judgment files (the default 5,000) |
| `import_cases_csv` | A spreadsheet exported as CSV |
| `import_cases_json` | A JSON file from another system |

All three are **idempotent**: re-running them skips files already imported.
And all three accept a `--reset` flag to wipe the database first (use with
care).

## 1. `ingest_cases` — bulk-load .txt files

This is what we use for the bundled 5,000 cases.

### Default usage

```powershell
python manage.py ingest_cases
```

Looks for `.txt` files in `./all_text_cases/` and imports them all.

### Options

```
--path PATH       Folder of .txt files (default: BASE_DIR/all_text_cases)
--limit N         Only import the first N files (handy for smoke tests)
--reset           Delete every existing case first
--batch-size N    DB insert batch size (default: 500)
```

### Examples

```powershell
# Smoke test on 25 files
python manage.py ingest_cases --limit 25

# Import from a different folder
python manage.py ingest_cases --path C:\backups\cases

# Wipe the DB and start fresh
python manage.py ingest_cases --reset
```

### What it does internally

1. Scans the folder for `*.txt`.
2. For each file:
   * Parses the filename like `B2_Complaint_42_2023.txt` to extract prefix,
     number, and year.
   * Reads the body of the file.
   * Detects the court name from the document header.
   * Detects the respondent name (looks for "VERSUS … Respondent").
   * Classifies the violation type via keyword rules
     (`effluent`/`BOD` → water pollution, `noise level` → noise, etc.).
   * Builds a short summary from the first substantial paragraph.
   * Auto-generates tags from prefix + violation + content keywords.
   * Auto-generates a unique URL slug.
3. Bulk-inserts in batches of 500 rows.
4. Skips files already imported (looks at `source_file` field).

### Filename convention

```
<PREFIX>_Complaint_<NUM>_<YEAR>.txt
```

* `<PREFIX>` — any alphanumeric token (e.g. `B2`, `B3`, `CR`).
* `<NUM>` — complaint number.
* `<YEAR>` — 4-digit year.

If a filename doesn't match this pattern, the file is still imported but
gets a generic title.

## 2. `import_cases_csv` — bulk-load CSV files

### Required columns

```
case_title          (required, must be non-empty)
```

### Optional columns

```
court, country, year, violation_type, summary, full_text, tags, source_file
```

* Column names are case-insensitive.
* Extra columns are ignored.
* `tags` can be a comma-separated string (`"a,b,c"`) **or** a JSON list
  (`'["a","b","c"]'`).
* `year` parses to an integer (1900–2100 accepted; otherwise stored as null).

### Example CSV (`cases.csv`)

```csv
case_title,court,country,year,violation_type,summary,tags
"Galaxy Mills v. EPA","Punjab Tribunal","Pakistan",2018,water_pollution,"BOD exceedance","NEQS,effluent"
"Acme Cement v. EPA","Punjab Tribunal","Pakistan",2020,air_pollution,"Stack PM violations","emission,PM"
```

### Usage

```powershell
python manage.py import_cases_csv path/to/cases.csv

# wipe first
python manage.py import_cases_csv path/to/cases.csv --reset

# different encoding
python manage.py import_cases_csv path/to/cases.csv --encoding utf-8-sig
```

> **Beginner tip:** When Excel saves CSVs, it sometimes uses Windows-1252
> encoding. If you see strange characters after import, try
> `--encoding cp1252` or save the file as "CSV UTF-8" in Excel.

## 3. `import_cases_json` — bulk-load JSON files

The JSON file must be a top-level **list** of objects. Each object uses the
same keys as the CSV.

### Example JSON (`cases.json`)

```json
[
  {
    "case_title": "Galaxy Mills v. EPA",
    "court": "Punjab Environmental Tribunal",
    "country": "Pakistan",
    "year": 2018,
    "violation_type": "water_pollution",
    "summary": "BOD exceedance",
    "full_text": "Long judgment text…",
    "tags": ["NEQS", "effluent"]
  },
  {
    "case_title": "Acme Cement v. EPA",
    "year": 2020,
    "violation_type": "air_pollution",
    "tags": "emission, PM"
  }
]
```

### Usage

```powershell
python manage.py import_cases_json path/to/cases.json
python manage.py import_cases_json path/to/cases.json --reset
```

## Best practices

### Test on a small slice first

```powershell
python manage.py ingest_cases --limit 10
```

If something looks wrong in the database, fix the importer or your data
**before** running on the full set.

### Always back up before `--reset`

```powershell
# back up the SQLite DB
cp db.sqlite3 db.sqlite3.bak
```

For Postgres, use:

```bash
pg_dump $DATABASE_URL > backup.sql
```

### Inspect the result

```powershell
python manage.py shell -c "from cases.models import Case; print(Case.objects.count())"
```

Or open `/admin/cases/case/` in a browser.

### Re-running is safe

Both `ingest_cases` and the CSV/JSON importers track what's already been
imported (via the `source_file` field for `.txt`, and slug uniqueness for
CSV/JSON). Re-running skips duplicates rather than crashing.

## Adding your own importer

If you have a different data source (a website, an API, an Excel sheet),
you can write your own command.

1. Create a new file: `cases/management/commands/my_importer.py`
2. Use this skeleton:

```python
from django.core.management.base import BaseCommand
from cases.models import Case

class Command(BaseCommand):
    help = "What this importer does."

    def add_arguments(self, parser):
        parser.add_argument("source")     # e.g. URL or file path

    def handle(self, *args, **opts):
        source = opts["source"]
        # ... do your import here ...
        Case.objects.create(case_title="...", year=2024, ...)
        self.stdout.write(self.style.SUCCESS("Done."))
```

3. Run it:

```powershell
python manage.py my_importer https://example.com/data.json
```

## Where to go next

→ [10-deployment.md](10-deployment.md) — pushing the site to the public
internet.
