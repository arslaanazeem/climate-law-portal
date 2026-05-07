# 4. How Django works (a plain-English primer)

If you've never used Django, this page explains the core ideas with as little
jargon as possible. After reading it, the rest of the docs will make sense.

## What is Django?

Django is a **web framework** written in Python. A "framework" is a kit of
prebuilt parts you assemble to make a website. Instead of writing a server
from scratch, you fill in the bits that are unique to your project (data
shapes, pages, URLs) and Django handles the boring plumbing (HTTP, sessions,
routing, security).

## The big picture: how a request flows through Django

When a user clicks a link, this is what happens:

```
   Browser                   Django                       Database
      |                        |                              |
      | --- "GET /search/" --> |                              |
      |                        |  1. Look up URL /search/     |
      |                        |     in urls.py               |
      |                        |                              |
      |                        |  2. Call the matching        |
      |                        |     view function in views.py|
      |                        |                              |
      |                        |  3. View asks the database   |
      |                        |     for matching cases   --> |
      |                        |                              |
      |                        |  <-- 4. DB returns rows      |
      |                        |                              |
      |                        |  5. View hands rows to       |
      |                        |     a template               |
      |                        |                              |
      |                        |  6. Template renders HTML    |
      |                        |                              |
      | <--- HTML response --- |                              |
      |                        |                              |
```

Six steps. Three Django files (`urls.py`, `views.py`, a template). One
database query. **That's basically the whole framework.**

---

## The five main concepts

### 1. **URLs** (in `urls.py`)
A URL pattern is a rule that says "if the user visits this address, run this
function." Example:

```python
path("search/", views.search_view, name="search")
```

Means: "When someone goes to `/search/`, call `search_view()`."

### 2. **Views** (in `views.py`)
A view is a Python function that handles a request and returns a response.
Example:

```python
def home_view(request):
    return render(request, "cases/home.html", {"total_cases": 5000})
```

Means: "Build a response by rendering `home.html`, and pass it the variable
`total_cases=5000`."

### 3. **Models** (in `models.py`)
A model is a Python class that maps to a database table. Each field on the
class becomes a column. Example:

```python
class Case(models.Model):
    case_title = models.CharField(max_length=500)
    year = models.IntegerField()
```

Means: "There's a table called `cases_case` with two columns: `case_title`
(text up to 500 chars) and `year` (integer)."

### 4. **Templates** (in `templates/`)
A template is HTML with placeholders. Example:

```html
<h1>Total cases: {{ total_cases }}</h1>
```

Means: "Show an `<h1>` heading; replace `{{ total_cases }}` with the value
the view passed in (5000)."

### 5. **Migrations** (in `cases/migrations/`)
When you change `models.py`, Django writes a "migration" — a Python file
that describes how to update the database. You apply it with
`python manage.py migrate`. **You don't write migrations by hand.**

---

## Apps vs. project

Django splits your code into:

* **One project** (the `climate_law_portal/` folder) — the configuration that
  glues everything together.
* **Multiple apps** (the `core/` and `cases/` folders) — self-contained
  features. Each app has its own `models.py`, `views.py`, `urls.py`, etc.

The idea is that apps could be reused in other projects. In practice for a
small site like this, you often have just two or three.

---

## Following one request through this project

Let's trace what happens when someone searches for "NEQS":

1. **Browser sends:** `GET /search/?q=NEQS`
2. **`climate_law_portal/urls.py`** matches `""` to `cases.urls`. The `/search/`
   part is delegated to `cases/urls.py`.
3. **`cases/urls.py`** matches `search/` to the function `search_view`.
4. **`cases/views.py:search_view`** runs. It:
   * Reads `?q=NEQS` from the request
   * Calls `Case.objects.search("NEQS")` (defined in `cases/models.py`)
   * Django turns that into a SQL query like:
     `SELECT * FROM cases_case WHERE case_title LIKE '%NEQS%' OR full_text LIKE '%NEQS%' …`
   * Database returns matching rows
   * View paginates them (20 per page)
   * View calls `render(request, "cases/search_results.html", {results: …})`
5. **`templates/cases/search_results.html`** is loaded. It extends
   `base.html` (the outer skeleton). Django fills in `{{ … }}` with values.
6. **HTML is sent back to the browser.**

Total time: ~50 milliseconds.

---

## Things Django gives you for free

* **Admin panel** at `/admin/` — auto-generated CRUD interface for every model
* **Authentication** — user accounts, login, password hashing, sessions
* **Forms** — request-data validation
* **CSRF protection** — defends against a common web attack
* **ORM** — write Python instead of SQL: `Case.objects.filter(year=2024)`
* **Migrations** — automatic database schema changes
* **Testing framework** — `python manage.py test`
* **Internationalization** — multi-language support (we don't use it)

That's why Django is called "the web framework for perfectionists with
deadlines" — most of the boring stuff is already done.

---

## Vocabulary cheat-sheet

| Term | Plain-English meaning |
|------|------------------------|
| **request** | A user opening a URL or submitting a form |
| **response** | What Django sends back (usually an HTML page) |
| **view** | A Python function that turns a request into a response |
| **model** | A Python class that becomes a database table |
| **template** | An HTML file with `{{ placeholders }}` |
| **migration** | An auto-generated file that describes a DB change |
| **ORM** | Object-Relational Mapper — write Python, get SQL |
| **app** | A self-contained feature folder (`core/`, `cases/`) |
| **project** | The configuration package (`climate_law_portal/`) |
| **URL pattern** | A rule mapping a URL to a view |

A bigger glossary: [12-glossary.md](12-glossary.md).

---

## Where to go next

→ [05-models-and-database.md](05-models-and-database.md) — the `Case` model
explained line by line.
