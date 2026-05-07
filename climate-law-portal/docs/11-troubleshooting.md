# 11. Troubleshooting — common errors and how to fix them

Most beginner errors fall into one of these buckets. Find your symptom, apply
the fix.

## "Python is not recognized"

**Symptom:**
```
'python' is not recognized as an internal or external command...
```

**Cause:** Python isn't installed, or it's installed but not on the PATH.

**Fix:**
1. Reinstall Python from https://www.python.org/downloads/.
2. **On the first installer screen, tick "Add Python to PATH".**
3. Close and reopen your terminal.
4. Try again: `python --version`.

## "No module named django"

**Symptom:**
```
ModuleNotFoundError: No module named 'django'
```

**Cause:** You haven't activated the virtual environment, or you haven't
installed dependencies into it.

**Fix:**
```powershell
.\.venv\Scripts\Activate.ps1     # Windows
# or:  source .venv/bin/activate  (macOS/Linux)
pip install -r requirements.txt
```

If the activate script doesn't exist, you skipped the `python -m venv .venv`
step. Re-run that.

## "PowerShell cannot run scripts because execution policy"

**Symptom (Windows):**
```
File .\.venv\Scripts\Activate.ps1 cannot be loaded because running scripts
is disabled on this system.
```

**Fix (one-time, opens permissions for your user):**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Confirm with `Y`. Then re-activate.

## "Port 8000 is already in use"

**Symptom:**
```
Error: That port is already in use.
```

**Cause:** Another program (or another runserver) is bound to port 8000.

**Fix — pick a different port:**
```powershell
python manage.py runserver 8765
```
Then visit `http://127.0.0.1:8765/`.

## "OperationalError: no such table: cases_case"

**Cause:** You haven't run migrations yet.

**Fix:**
```powershell
python manage.py migrate
```

## Home page shows "0 cases"

**Cause:** You haven't ingested any data.

**Fix:**
```powershell
python manage.py ingest_cases
```

## "DisallowedHost at /" in production

**Symptom:**
```
DisallowedHost: Invalid HTTP_HOST header: 'your-domain.com'.
You may need to add 'your-domain.com' to ALLOWED_HOSTS.
```

**Cause:** When `DEBUG=False`, Django requires `ALLOWED_HOSTS` to contain
the domain the user is visiting.

**Fix:** Add the domain to the `DJANGO_ALLOWED_HOSTS` env var in Render.
Comma-separated:

```
.onrender.com,law.example.com
```

Then click "Manual Deploy" → "Deploy latest commit".

## "CSRF verification failed"

**Symptom:** Submitting a form returns "CSRF verification failed."

**Cause:** Production sites need `CSRF_TRUSTED_ORIGINS` set if they're served
behind a proxy (Render does this automatically with the included settings).

**Fix:** Make sure your custom domain is included in
`CSRF_TRUSTED_ORIGINS`. By default we include `https://*.onrender.com`. For
a custom domain, edit `climate_law_portal/settings.py`.

## Search returns no results when it should

**Cause:** Most likely a typo, or the case really doesn't contain the term.
The search is **case-insensitive** but otherwise literal — no fuzzy
matching, no stemming.

**Diagnose:**
```powershell
python manage.py shell
```
```python
from cases.models import Case
Case.objects.search("YOUR TERM").count()
Case.objects.filter(full_text__icontains="YOUR TERM").count()
```

If both return 0, the term genuinely doesn't appear in any case.

## Pagination is broken / "EmptyPage" error

**Cause (in older code):** asking for a page beyond the last one.

**This is already fixed in `cases/views.py`:** we use `paginator.get_page()`
instead of `paginator.page()`, which auto-clamps to the last page rather
than crashing.

If you see `EmptyPage` in production, you've replaced `get_page` with
`page` somewhere — switch back.

## "static file not found" or unstyled site in production

**Cause:** `collectstatic` didn't run, or `whitenoise` isn't in `MIDDLEWARE`.

**Fix:** Verify `MIDDLEWARE` in `settings.py` includes
`whitenoise.middleware.WhiteNoiseMiddleware` right after the
SecurityMiddleware. Then trigger a redeploy:

```powershell
git commit --allow-empty -m "Trigger redeploy"
git push
```

## Render build fails on `pip install psycopg2-binary`

**Cause:** Build tools missing on certain runtime versions.

**Fix:** Make sure your `requirements.txt` says:

```
psycopg2-binary>=2.9,<3 ; sys_platform != "win32"
```

The `binary` variant ships pre-compiled wheels and avoids the need for
`gcc` and `libpq-dev`.

## "no such column" after editing the model

**Cause:** You changed `models.py` but didn't make a new migration.

**Fix:**
```powershell
python manage.py makemigrations cases
python manage.py migrate
```

## Tests fail with "table already exists"

**Cause:** A previous test run left a stale test DB.

**Fix:**
```powershell
python manage.py test --keepdb=False
```

Or just delete `db.sqlite3.test` and try again. (Django normally cleans up
on its own — this only happens if a test crashed mid-run.)

## "Render build succeeded but my changes aren't live"

**Cause:** Browser cache.

**Fix:** Hard-reload — `Ctrl + F5` (Windows / Linux) or `Cmd + Shift + R`
(macOS). Or open an incognito window.

## I deleted db.sqlite3 — how do I get the data back?

The database is regenerated empty. To get the cases back:

```powershell
python manage.py migrate
python manage.py ingest_cases
```

If you had data that wasn't in `all_text_cases/` (e.g. things you added via
the admin), they're gone unless you had a backup.

## I broke something — how do I undo?

If you're using Git (recommended):

```powershell
git status                    # see what changed
git diff                      # see the changes
git checkout -- file.py       # revert one file to the last commit
git reset --hard HEAD         # nuke ALL uncommitted changes (DESTRUCTIVE)
```

If you don't use Git yet, learn now — it's the single best
career-skills-per-hour investment available.

## Where to go next

→ [12-glossary.md](12-glossary.md) — the meaning of every technical term
in this project.
