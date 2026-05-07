# 6. Search and views — how the pages are built

A "view" is a Python function that handles a request and returns a response.
This page walks through every view in the project and explains how the search
works.

## Where the views live

```
cases/views.py     ← the main views: home, search, case detail
core/views.py      ← about, health, custom 404/500
```

## The URL → view mapping

The whole URL routing for the cases app is in `cases/urls.py`:

```python
app_name = "cases"

urlpatterns = [
    path("",                     views.home_view,             name="home"),
    path("search/",              views.search_view,           name="search"),
    path("case/<int:pk>/",       views.case_detail_by_pk_only,name="detail_short"),
    path("case/<int:pk>/<slug:slug>/", views.case_detail_view, name="detail"),
]
```

| URL | View | What it does |
|-----|------|--------------|
| `/` | `home_view` | Shows the homepage |
| `/search/?q=NEQS` | `search_view` | Returns search results |
| `/case/42/` | `case_detail_by_pk_only` | Redirects to the canonical URL with a slug |
| `/case/42/galaxy-mills/` | `case_detail_view` | Shows the case detail page |

## `home_view` — the homepage

```python
def home_view(request):
    total_cases = Case.objects.count()
    recent_cases = Case.objects.order_by("-created_at")[:8]
    by_violation = (
        Case.objects.values("violation_type")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    years = (
        Case.objects.exclude(year__isnull=True)
        .values_list("year", flat=True)
        .distinct().order_by("-year")
    )
    return render(request, "cases/home.html", {...})
```

It gathers four pieces of data:
* total case count
* the 8 most recently added cases
* counts of cases per violation type (for the chart)
* the list of years that have cases (for the dropdown filter)

Then renders `templates/cases/home.html`.

## `search_view` — the heart of the site

```python
def search_view(request):
    query     = request.GET.get("q", "").strip()
    year      = request.GET.get("year", "").strip()
    violation = request.GET.get("violation", "").strip()
    sort      = request.GET.get("sort", "relevance").strip() or "relevance"

    qs = (
        Case.objects.all()
        .search(query)
        .filter_year(year)
        .filter_violation(violation)
    )

    if sort == "newest":
        qs = qs.order_by("-year", "-created_at")
    elif sort == "oldest":
        qs = qs.order_by("year", "created_at")
    elif sort == "title":
        qs = qs.order_by("case_title")
    else:  # relevance fallback
        qs = qs.order_by("-year", "case_title")

    paginator = Paginator(qs, settings.CASES_PER_PAGE)
    page_number = request.GET.get("page") or 1
    page = paginator.get_page(page_number)

    return render(request, "cases/search_results.html", {...})
```

### Step by step

1. **Read query parameters** from the URL (`?q=NEQS&year=2024`).
2. **Build the queryset** by chaining the helper methods we defined on
   `CaseQuerySet` (see [05-models-and-database.md](05-models-and-database.md)).
3. **Sort** based on the `sort` parameter.
4. **Paginate** — split the long list into pages of `CASES_PER_PAGE` items
   (default 20).
5. **Render** the template with all the data.

### About `Paginator`

Django's `Paginator` does the math:

```python
paginator = Paginator(queryset_with_5000_items, 20)  # 20 per page
page = paginator.get_page(2)                         # second page
page.object_list   # the 20 items for that page
page.number        # 2
page.paginator.num_pages  # 250
page.has_next, page.has_previous  # booleans
```

`get_page()` is forgiving — if the user asks for page 9999, it returns the
last page instead of crashing.

## `case_detail_view` — show one case

```python
def case_detail_view(request, pk: int, slug: str | None = None):
    case = get_object_or_404(Case, pk=pk)
    related = (
        Case.objects.filter(violation_type=case.violation_type)
        .exclude(pk=case.pk)
        .order_by("-year")[:5]
    )
    return render(request, "cases/case_detail.html",
                  {"case": case, "related": related})
```

Notes:

* `get_object_or_404` looks up the case by its primary key (`pk`); if no row
  matches, Django automatically returns a 404 page.
* It **doesn't check the slug** — that's a deliberate choice so old links
  with a stale slug still work.
* The "Related cases" sidebar is just other cases with the same violation
  type, newest first, capped at 5.

## `case_detail_by_pk_only` — the short URL

```python
def case_detail_by_pk_only(request, pk: int):
    case = get_object_or_404(Case, pk=pk)
    return case_detail_view(request, pk=pk, slug=case.slug)
```

Lets `/case/42/` work without a slug — useful for short shareable links.

## Other views (in `core/views.py`)

```python
def about_view(request):
    return render(request, "core/about.html")

def health_view(request):
    return HttpResponse("ok", content_type="text/plain")

def handler404(request, exception=None):
    return render(request, "core/404.html", status=404)

def handler500(request):
    return render(request, "core/500.html", status=500)
```

* `about_view` — the about page.
* `health_view` — returns plain text "ok". Used by Render's health check.
* `handler404` / `handler500` — registered in
  `climate_law_portal/urls.py` so Django shows our custom error pages.

## How the search performs

Despite searching across `case_title`, `summary`, `full_text`, `court`, and
`tags`, queries return in <100 ms on SQLite for 5,000 rows because:

* Django's ORM compiles the Python expression into a single efficient SQL
  query (no Python loops involved).
* `db_index=True` on `year` and `violation_type` makes filtering instant.
* `LIKE '%foo%'` on a 10 KB text column over 5,000 rows is well under SQLite's
  performance ceiling.

For 100,000+ rows you'd want **PostgreSQL full-text search**:

```python
from django.contrib.postgres.search import SearchVector
qs.annotate(search=SearchVector("case_title", "full_text")).filter(search="foo")
```

…but for our scale, plain `LIKE` is plenty.

## What does `request.GET` contain?

For URL `/search/?q=NEQS&year=2024&page=3`:

```python
request.GET = QueryDict({
    "q":    ["NEQS"],
    "year": ["2024"],
    "page": ["3"],
})
request.GET.get("q") == "NEQS"
```

`request.GET` is read-only; for forms you'd use `request.POST`.

## Where to go next

→ [07-templates-and-styling.md](07-templates-and-styling.md) — how the views'
data turns into HTML.
