# 3. Project structure — a guided tour

This page explains **every file and folder** in the project, what it does,
and whether you'll need to edit it.

## Top-level layout

```
climate-law-portal/
├── manage.py                  ← Django's command-line entrypoint
├── requirements.txt           ← list of Python packages we need
├── runtime.txt                ← Python version for the server
├── Procfile                   ← tells Render how to start the site
├── render.yaml                ← deployment blueprint for Render
├── build.sh                   ← script run on Render before each deploy
├── gunicorn.conf.py           ← production web-server tuning
├── README.md                  ← short project intro
├── DEPLOY_GUIDE.txt           ← deployment walkthrough
├── .gitignore                 ← files Git should ignore
├── .env.example               ← template for environment variables
│
├── climate_law_portal/        ← project package (settings, URLs)
├── core/                      ← Django app — site-wide pages
├── cases/                     ← Django app — the case database
│
├── templates/                 ← HTML files
├── static/                    ← CSS, images, fonts
│
├── all_text_cases/            ← 5,000 judgment .txt files (the data)
└── docs/                      ← this documentation 📚
```

Below, each item is explained one by one.

---

## Top-level files

### `manage.py`
Django's swiss-army knife. **You don't edit this file.** You *run* it:

* `python manage.py runserver` — starts the dev server
* `python manage.py migrate` — applies database migrations
* `python manage.py createsuperuser` — makes an admin user
* `python manage.py shell` — opens an interactive Python prompt with Django loaded
* `python manage.py ingest_cases` — our custom command, loads the 5,000 cases

### `requirements.txt`
A plain-text list of the Python packages this project needs. Currently:
```
Django, gunicorn, whitenoise, dj-database-url, psycopg2-binary
```
**Edit when:** you add a new library (`pip install something` then add it here).

### `runtime.txt`
A single line: `python-3.12.4`. Tells Render which Python version to use.
**Edit when:** you upgrade Python.

### `Procfile`
Tells Render how to start the web service. Two lines:
```
web: gunicorn climate_law_portal.wsgi:application --config gunicorn.conf.py
release: python manage.py migrate --noinput
```
The `release` line runs migrations automatically on every deploy.
**You rarely edit this.**

### `render.yaml`
The "Blueprint" file Render uses to set up the entire stack — web service,
PostgreSQL database, environment variables — in one click.
**Edit when:** you change the deployment shape (e.g. add a worker process).

### `build.sh`
Bash script Render runs **before** starting the web server on every deploy. It:
1. Upgrades pip
2. Installs `requirements.txt`
3. Runs `collectstatic` (gathers static files into one folder)
4. Runs `migrate` (applies any new database changes)
5. Optionally runs `ingest_cases` if `CASES_INGEST_PATH` is set

### `gunicorn.conf.py`
Production-server tuning. Sets number of workers, timeouts, log settings.
**Don't touch unless you know why.**

### `.gitignore`
Tells Git to ignore certain files (like `db.sqlite3`, `__pycache__/`, `.env`).
**Edit if:** you generate a new type of file you don't want committed.

### `.env.example`
A template for **environment variables** (configuration secrets). To use it,
copy to `.env` and fill in values. Django reads them automatically.

### `README.md` and `DEPLOY_GUIDE.txt`
Human-readable guides. The README is for visitors to the GitHub repo;
DEPLOY_GUIDE walks you through publishing the site online.

---

## `climate_law_portal/` — the project package

This folder is the **project's brain**. It contains the central configuration.

```
climate_law_portal/
├── __init__.py     ← marks this folder as a Python package (empty)
├── settings.py     ← THE BIG ONE — every config lives here
├── urls.py         ← project-wide URL routing
├── wsgi.py         ← entrypoint for production servers (gunicorn)
└── asgi.py         ← entrypoint for async servers (we don't use it, but it's standard)
```

### `settings.py`
The most important file in any Django project. It defines:

* `DEBUG` — `True` for development, `False` in production
* `SECRET_KEY` — a long random string Django uses for security
* `ALLOWED_HOSTS` — domain names allowed to serve the site
* `INSTALLED_APPS` — list of all apps (admin, auth, our `core` and `cases`)
* `MIDDLEWARE` — request-processing pipeline
* `DATABASES` — where data is stored (SQLite locally, Postgres in prod)
* `TEMPLATES` — where to find HTML files
* `STATIC_URL` and `STATICFILES_DIRS` — where CSS/images live

If you only ever look at one file in the project, look at this one.

### `urls.py` (project-level)
Maps URL patterns (the part after the domain) to Python functions.
Roughly:
```python
path("admin/", admin.site.urls),
path("",      include("cases.urls")),
path("about/", about_view),
path("health/", health_view),
```
"Anything starting with `/admin/` goes to Django's admin. Anything else falls
through to the cases app. `/about/` and `/health/` have their own views."

### `wsgi.py`
WSGI = "Web Server Gateway Interface". One line you'll never edit.
Production servers (gunicorn) import `application` from this file.

### `asgi.py`
Same idea but for async servers. We include it because Django expects it to
exist; we don't use it.

---

## `core/` — site-wide app

A small Django **app** for things that aren't case-specific.

```
core/
├── __init__.py
├── apps.py                    ← app config (rarely touched)
├── admin.py                   ← empty — no models in this app
├── models.py                  ← empty — no models in this app
├── views.py                   ← about page, health endpoint, error handlers
└── context_processors.py      ← injects SITE_NAME into every template
```

### `views.py` (in core)
* `about_view` — renders `templates/core/about.html`
* `health_view` — returns plain text "ok" — used by Render's health check
* `handler404` and `handler500` — render the custom error pages

### `context_processors.py`
A *context processor* makes a value available in **every** template
automatically. We use it to put `SITE_NAME` and `SITE_TAGLINE` everywhere
without copy-pasting.

---

## `cases/` — the heart of the project

This is the Django app that stores and serves cases.

```
cases/
├── __init__.py
├── apps.py
├── admin.py                   ← Django admin config for the Case model
├── models.py                  ← the Case model — defines DB columns
├── views.py                   ← home, search, case detail
├── urls.py                    ← URL patterns for cases (/, /search/, /case/N/)
├── tests.py                   ← automated tests
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py        ← auto-generated DB schema for the Case model
└── management/
    └── commands/
        ├── __init__.py
        ├── ingest_cases.py        ← reads .txt files into the DB
        ├── import_cases_csv.py    ← reads CSV files into the DB
        └── import_cases_json.py   ← reads JSON files into the DB
```

We dedicate a whole page to each piece:

* `models.py` → see [05-models-and-database.md](05-models-and-database.md)
* `views.py` and `urls.py` → see [06-search-and-views.md](06-search-and-views.md)
* `admin.py` → see [08-admin-panel.md](08-admin-panel.md)
* `management/commands/` → see [09-importing-data.md](09-importing-data.md)

---

## `templates/` — HTML files

```
templates/
├── base.html                  ← outer skeleton (header, footer, CSS link)
├── cases/
│   ├── home.html              ← homepage
│   ├── search_results.html    ← search results page
│   └── case_detail.html       ← single-case page
└── core/
    ├── about.html             ← about page
    ├── 404.html               ← "page not found"
    └── 500.html               ← "server error"
```

Templates are HTML files with `{% ... %}` and `{{ ... }}` placeholders that
Django fills in.

→ Full explanation in [07-templates-and-styling.md](07-templates-and-styling.md).

---

## `static/` — CSS, images, fonts

```
static/
└── css/
    └── site.css               ← all the styling
```

CSS = "Cascading Style Sheets" — the rules that make the page look nice.
Currently just one file.

> **Beginner tip:** During development, Django serves these files
> automatically. In production, the `collectstatic` command (run by `build.sh`)
> copies them into a single folder that whitenoise can serve directly.

---

## `all_text_cases/` — the data

5,000 plain-text files. Each filename follows the pattern:

```
B2_Complaint_10_2016.txt
^^  ^^^^^^^^^ ^^ ^^^^
prefix       num year
```

The `ingest_cases` command parses these into database rows. **Don't edit these
files manually** — re-run the ingest command if you change them.

---

## `docs/` — this folder you're reading

Beginner-friendly documentation. Markdown files (`.md`) — open them in any
text editor or read on GitHub.

---

## Where to go next

→ [04-how-django-works.md](04-how-django-works.md) — a plain-English Django
primer so the file names above make more sense.
