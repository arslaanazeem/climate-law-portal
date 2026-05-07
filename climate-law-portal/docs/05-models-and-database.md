# 5. Models and the database — how a Case is stored

The whole site is built around one database table: **the cases**. This page
explains how that table is defined and what each column means.

## Where the model lives

```
cases/models.py
```

Open it now and follow along — this page mirrors what's in there.

## The Case class

Here's the model, slightly simplified:

```python
class Case(models.Model):
    case_title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    court = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, default="Pakistan")
    year = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    violation_type = models.CharField(
        max_length=50, choices=VIOLATION_CHOICES, default="other", db_index=True,
    )
    summary = models.TextField(blank=True)
    full_text = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)
    source_file = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

Each line is a **field** = a database column. Let's go through them.

| Field | Type | Meaning |
|-------|------|---------|
| `id` (implicit) | auto-incrementing integer | Django adds this automatically — the unique row number |
| `case_title` | CharField (text up to 500 chars) | Human-readable title |
| `slug` | SlugField (URL-safe text) | Used in URLs like `/case/42/galaxy-mills/` |
| `court` | CharField | Where the case was decided |
| `country` | CharField, defaults to "Pakistan" | Country code |
| `year` | PositiveIntegerField | Year of judgment |
| `violation_type` | CharField with choices | Pre-defined categories like `water_pollution` |
| `summary` | TextField (unlimited length) | Short summary shown in search results |
| `full_text` | TextField | The whole judgment |
| `tags` | CharField | Comma-separated keywords like "NEQS, effluent, fine" |
| `source_file` | CharField | Original filename (used to skip duplicates) |
| `created_at` | DateTimeField | Auto-set when the row is created |
| `updated_at` | DateTimeField | Auto-set when the row is updated |

## Field types in plain English

| Django type | What it stores | Example |
|-------------|---------------|---------|
| `CharField` | Short text, capped length | "Punjab" |
| `TextField` | Long, unlimited text | A 10-page judgment |
| `IntegerField` | Whole numbers | 2023 |
| `PositiveIntegerField` | Whole numbers ≥ 0 | 5000 |
| `BooleanField` | True/False | True |
| `DateTimeField` | Date + time | 2024-01-15 14:30 |
| `SlugField` | Text safe for URLs | "galaxy-mills-pvt-ltd" |
| `ForeignKey` | A link to another table | (we don't use one yet) |

## What `choices=VIOLATION_CHOICES` means

At the top of the file:

```python
VIOLATION_CHOICES = [
    ("air_pollution", "Air Pollution"),
    ("water_pollution", "Water Pollution"),
    ("noise_pollution", "Noise Pollution"),
    ...
]
```

The first item is what's stored in the database (`water_pollution`), the
second is the human-readable label (`"Water Pollution"`). The admin panel and
templates use the label automatically.

## What `db_index=True` does

It tells the database to build a quick lookup table for that column, so
queries like `Case.objects.filter(year=2024)` return instantly even with
millions of rows. We index `year`, `violation_type`, and `country`.

## Custom queries: the `CaseQuerySet`

Django lets you add **shortcut methods** to a model's queryset. We have:

```python
class CaseQuerySet(models.QuerySet):
    def search(self, query):
        return self.filter(
            Q(case_title__icontains=query) |
            Q(summary__icontains=query) |
            Q(full_text__icontains=query) |
            Q(court__icontains=query) |
            Q(tags__icontains=query)
        )

    def filter_year(self, year):
        return self.filter(year=int(year))

    def filter_violation(self, violation):
        return self.filter(violation_type=violation)
```

That's why we can write in our views:

```python
Case.objects.search("effluent").filter_year(2024)
```

`Q` is Django's way of saying "OR". `__icontains` means
"case-**i**nsensitive contains". So `case_title__icontains="effluent"`
becomes `WHERE LOWER(case_title) LIKE LOWER('%effluent%')`.

## Helper properties

```python
@property
def tag_list(self):
    return [t.strip() for t in self.tags.split(",") if t.strip()]
```

Lets templates write `{% for tag in case.tag_list %}` instead of dealing with
the comma-separated string.

```python
@property
def short_summary(self):
    text = (self.summary or self.full_text or "").strip()
    if len(text) <= 280:
        return text
    return text[:277].rstrip() + "…"
```

Used in search results to show a snippet capped at 280 characters.

## How a row gets its slug

```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = self._build_unique_slug()
    super().save(*args, **kwargs)
```

When you save a case without a slug, the model auto-generates one from the
title (`"Galaxy Mills v. EPA"` → `"galaxy-mills-v-epa"`) and adds a number if
there's a clash.

## Migrations: how the table got created

After we wrote `models.py`, we ran:

```powershell
python manage.py makemigrations cases
```

That created `cases/migrations/0001_initial.py` — a Python file describing
the table. Then:

```powershell
python manage.py migrate
```

…actually executed those instructions against the database. The resulting
SQL was roughly:

```sql
CREATE TABLE cases_case (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_title VARCHAR(500),
    slug VARCHAR(255) UNIQUE,
    court VARCHAR(255),
    ...
);
CREATE INDEX cases_case_year_idx ON cases_case(year);
...
```

But you never write that SQL — Django does.

## Inspecting the data yourself

Open a Django shell:

```powershell
python manage.py shell
```

Inside:

```python
from cases.models import Case

# Total cases
Case.objects.count()

# First case
Case.objects.first()

# All 2024 cases
Case.objects.filter(year=2024).count()

# Search example
Case.objects.search("noise").filter_year(2022).count()

# Print the first match
c = Case.objects.search("Galaxy").first()
print(c.case_title, c.year, c.violation_type)
```

Press Ctrl-D (or type `exit()`) to leave.

## Summary

The model is just a Python description of one database table. Everything
else — the admin, the search, the views — uses this class to read and write
rows. **Change `models.py`, run `makemigrations` and `migrate`, and the
schema updates.**

## Where to go next

→ [06-search-and-views.md](06-search-and-views.md) — how the views turn a
request into a search results page.
