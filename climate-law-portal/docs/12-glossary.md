# 12. Glossary — every technical term, explained

A reference for terms that appear in the docs and code. Skim it once, then
look things up as you go.

## Project & web basics

**Backend** — the part of the website that runs on a server (Python +
Django, in our case). Responsible for data and logic.

**Frontend** — what the browser displays (HTML, CSS, JavaScript). Our
frontend is server-rendered HTML — no React or Vue.

**Server** — a computer that responds to web requests. In development the
server is your laptop; in production it's a Linux box at Render.

**Client** — a program that makes requests. Usually a browser. Sometimes a
mobile app or `curl`.

**HTTP** — the protocol clients and servers speak: GET, POST, etc.

**URL** — Uniform Resource Locator. The address of a page, e.g.
`https://example.com/search/?q=foo`.

**Query string** — the part of a URL after `?`, e.g. `?q=foo&year=2024`.

## Python ecosystem

**Python** — the programming language. We use 3.10+.

**pip** — Python's package installer. `pip install django` adds Django to
the active environment.

**Virtual environment (`.venv`)** — an isolated folder of packages so this
project's dependencies don't clash with other Python projects.

**`requirements.txt`** — a list of pip packages this project needs.

**Module** — a Python file. `models.py` is a module.

**Package** — a folder of Python files with an `__init__.py`. `cases/` is a
package.

## Django jargon

**Project** — the configuration package (`climate_law_portal/`). Contains
`settings.py`, `urls.py`, `wsgi.py`. There's only one per Django site.

**App** — a self-contained feature folder (`cases/`, `core/`). A project
has many apps.

**Model** — a Python class that maps to a database table (`Case` in our
project).

**Field** — one column of a model (`case_title`, `year`).

**Migration** — an auto-generated Python file that describes a database
schema change. Created with `makemigrations`, applied with `migrate`.

**ORM** (Object-Relational Mapper) — Django's tool for converting Python
queries (`Case.objects.filter(year=2024)`) into SQL. So you don't write
raw SQL.

**View** — a Python function that handles a request. Defined in `views.py`.

**Template** — an HTML file with `{{ placeholders }}`. Rendered by a view.

**URL pattern** — an entry in `urls.py` mapping a URL to a view.

**Reverse URL lookup** — the opposite: given a view name, find the URL.
Done in templates with `{% url 'cases:detail' case.pk %}`.

**Context** — the dictionary of variables a view passes to a template.

**Context processor** — a function that adds variables to **every**
template's context (used for `SITE_NAME`).

**Manager** (`Case.objects`) — the default object you query through:
`Case.objects.all()`, `Case.objects.filter(...)`.

**QuerySet** — a lazy list-of-rows that Django builds. Doesn't hit the
database until you iterate or count it.

**Migration** — see above; tells the DB how to change shape.

**Middleware** — a function that runs before/after every view. Used for
session handling, CSRF protection, etc.

**Static files** — CSS, JS, images. Served directly without going through
Django.

**Media files** — user-uploaded files. We don't have any.

**Slug** — a URL-friendly text string, like `galaxy-mills-pvt-ltd`.

**Superuser** — a Django user with full admin permissions.

**CSRF** — Cross-Site Request Forgery. A security threat. Django blocks it
by default for POST requests.

## Database

**Database** — a structured store of data. Our project uses SQLite locally
and PostgreSQL in production.

**Table** — a named collection of rows. The `cases_case` table holds Case
records.

**Row** — one entry, e.g. one case.

**Column / field** — one attribute of a row, e.g. `case_title`.

**Index** — a fast lookup table the DB maintains for a column. Speeds up
filtering.

**Primary key (`pk`)** — a unique row identifier. Django auto-creates one
called `id`.

**Foreign key** — a field that points to a row in another table. (We don't
use one yet.)

**SQL** — Structured Query Language. The language databases speak.

**SQLite** — a file-based DB. Single file, zero setup. Great for
development, OK for small production sites.

**PostgreSQL** — a real, network-attached DB server. Recommended for
production.

**Migration** — a file describing how to change a DB schema (add a
column, etc.).

## Web servers & deployment

**WSGI** — Web Server Gateway Interface. The Python standard for talking
to web servers.

**ASGI** — like WSGI but supports async. We don't use it.

**gunicorn** — a production WSGI server. Multiple worker processes, fast,
battle-tested.

**Workers** — gunicorn process count. More workers = more concurrency.

**whitenoise** — a Python library that lets your Django process serve
static files efficiently in production. Avoids needing a separate Nginx.

**Render** — a hosting provider with a generous free tier. We deploy here.

**Procfile** — a file declaring "this is the command to start the web
server". Used by Render and Heroku.

**Build command** — the command run during deploy to install deps and
prepare the app. Ours is `./build.sh`.

**Start command** — the command to actually run the app. Ours is
`gunicorn climate_law_portal.wsgi:application`.

**Health check** — Render pings `/health/` to verify the app is live.

**Environment variable** — a key-value pair set outside the code (e.g. in
the Render dashboard). Read with `os.environ.get("KEY")`.

**`.env` file** — a file holding env vars for local development. Excluded
from Git.

**`SECRET_KEY`** — a long random string Django uses to sign sessions and
CSRF tokens. **Never share it publicly.**

**Production** — the version of the site real users visit. `DEBUG=False`,
HTTPS, gunicorn, Postgres.

**Development** — the version on your laptop. `DEBUG=True`, runserver,
SQLite.

**Staging** — an in-between environment used for testing. We don't have
one.

## Git & GitHub

**Git** — version control system. Tracks every change to your code so you
can roll back, branch, merge.

**Repository (repo)** — the folder Git tracks. Includes a hidden `.git/`
subfolder with the history.

**Commit** — a snapshot of your code with a message.

**Branch** — a parallel line of development. The main one is usually
called `main`.

**Push** — upload commits from your laptop to GitHub.

**Pull** — download commits from GitHub to your laptop.

**GitHub** — a website that hosts Git repos. Free for public projects.

**Pull request (PR)** — a proposed merge of one branch into another. Used
for code review.

**`.gitignore`** — a file listing things Git should ignore (`db.sqlite3`,
`__pycache__/`, `.env`).

## HTTP status codes you'll see

**200 OK** — page rendered successfully.

**302 Found / 301 Moved Permanently** — redirect. The browser follows it.

**404 Not Found** — page doesn't exist. We have a custom 404 template.

**500 Internal Server Error** — your code crashed. Look at the logs.

**401 Unauthorized / 403 Forbidden** — auth or permissions failed.

**429 Too Many Requests** — rate-limited. Doesn't apply to us.

## Common acronyms in the cases corpus

These are not Django jargon but appear in the data:

* **PEPA** — Pakistan Environmental Protection Act, 1997
* **NEQS** — National Environmental Quality Standards
* **EPA** — Environmental Protection Agency
* **EPO** — Environmental Protection Order
* **EIA / IEE** — Environmental Impact Assessment / Initial Environmental Examination
* **BOD** — Biochemical Oxygen Demand (water quality metric)
* **COD** — Chemical Oxygen Demand
* **TSS** — Total Suspended Solids
* **PM** — Particulate Matter (air quality metric)
* **SO₂** — Sulphur Dioxide
* **NOx** — Nitrogen Oxides

## Where to go next

You've now read all the docs. 🎉 Re-read whichever ones felt fuzzy, then
play with the code. The best way to learn is to break things and fix them.

→ [README.md](README.md) — table of contents
