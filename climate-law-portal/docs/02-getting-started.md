# 2. Getting started — run the site on your own laptop

By the end of this page you will have:

1. Python installed
2. The project's dependencies installed
3. The site running at `http://127.0.0.1:8000/`
4. 5,000 cases loaded into the database
5. A first search performed in your browser

Reading time: 5 min · Doing time: 10 min the first time.

---

## Prerequisites

You need a Windows, macOS, or Linux machine with:

| Tool | Why | How to get it |
|------|-----|---------------|
| **Python 3.10 or newer** | The language the project is written in | https://www.python.org/downloads/ |
| **A terminal** | To type commands | Windows: PowerShell (built-in). macOS: Terminal. Linux: anything. |
| **A web browser** | To view the site | Chrome, Edge, Firefox — anything modern |

> **Beginner tip:** "terminal", "command line", "shell", "PowerShell", and
> "command prompt" all roughly mean the same thing — a window where you type
> text commands instead of clicking buttons.

### Check Python is installed

Open a terminal and type:

```powershell
python --version
```

You should see something like `Python 3.12.4`. If you see "command not found"
or a version below 3.10, install Python from the link above. **On Windows, tick
"Add Python to PATH" in the installer.**

---

## Step 1 — Open the project folder

```powershell
cd D:\EnvTribunalSimulator\Environment_law_portal\climate-law-portal
```

`cd` means **C**hange **D**irectory. Your terminal prompt should now show that
path. Everything below assumes you're inside that folder.

## Step 2 — Create a "virtual environment"

A virtual environment is just an isolated Python folder so this project's
libraries don't mix with other Python programs on your computer.

```powershell
python -m venv .venv
```

This creates a `.venv/` subfolder. You only do this **once per project**.

### Activate it

On Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS / Linux:

```bash
source .venv/bin/activate
```

Your prompt will now have `(.venv)` at the start — that's how you know the
virtual env is active. **Repeat this activation step every time you open a new
terminal to work on this project.**

## Step 3 — Install the dependencies

```powershell
pip install -r requirements.txt
```

This downloads Django, gunicorn, whitenoise, and a few other packages into
`.venv`. Takes ~30 seconds. You only do this **once**.

## Step 4 — Create the database

The project uses **SQLite** locally, which is just a single file (`db.sqlite3`).

```powershell
python manage.py migrate
```

`migrate` reads the project's database "blueprints" (called migrations) and
creates the tables. You'll see a list of "Applying ... OK" lines.

## Step 5 — Load the 5,000 cases

The case files live in `all_text_cases/` — 5,000 plain-text judgments. To
import them all into the database:

```powershell
python manage.py ingest_cases
```

This takes ~60 seconds. You'll see progress like `· 525/5000 processed`.
At the end: `Created=5000  Skipped=0  Errors=0`. Done.

> **Beginner tip:** the command is **idempotent** — if you run it twice, it
> notices the cases are already loaded and skips them. Safe to re-run.

## Step 6 — (Optional) Create an admin user

To use Django's built-in admin panel later:

```powershell
python manage.py createsuperuser
```

It will ask for:
* Username (e.g. `admin`)
* Email (anything works)
* Password (minimum 8 characters)

You can skip this for now — you don't need an admin user to view the site.

## Step 7 — Start the web server

```powershell
python manage.py runserver
```

You'll see:

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**Leave this terminal running.** The server is now serving requests.

## Step 8 — Open the site

In your browser, go to: <http://127.0.0.1:8000/>

You should see the home page with:
* A big search bar
* "5,000 cases indexed"
* Two cards: "Cases by violation type" and "Recently added"

### Try things out

* Search for **"effluent"** — you'll get thousands of results
* Filter by year **2024**
* Click any case title to see the full judgment
* Visit `/admin/` and log in with your superuser (if you made one)

## Step 9 — Stopping the server

When you're done, in the terminal where the server is running:

* Press **Ctrl + C** (Windows / Linux)
* Press **Ctrl + C** (macOS too)

The server stops. You can re-run it anytime with `python manage.py runserver`.

---

## Common first-run problems

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `'python' is not recognized` | Python isn't on PATH | Reinstall Python and tick "Add to PATH" |
| `'pip' is not recognized` after activating venv | Activation didn't work | Re-run the activate command for your OS |
| `Error: That port is already in use` | Another program is using port 8000 | Run on a different port: `python manage.py runserver 8765` |
| `OperationalError: no such table: cases_case` | You forgot Step 4 | Run `python manage.py migrate` |
| Home page shows "0 cases" | You forgot Step 5 | Run `python manage.py ingest_cases` |

For more, see [11-troubleshooting.md](11-troubleshooting.md).

## Where to go next

→ [03-project-structure.md](03-project-structure.md) — guided tour of every file in the repo.
