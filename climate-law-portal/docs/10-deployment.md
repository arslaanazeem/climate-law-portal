# 10. Deployment — putting the site online

This page is a **summary** of how deployment works. The detailed
step-by-step walkthrough is in `DEPLOY_GUIDE.txt` at the project root —
follow that one for the actual deploy.

## What "deployment" means

Up to now, your site only runs on your laptop at `127.0.0.1`. **Deploying**
means publishing it on the public internet so anyone with a URL can visit it.

For a small Django site, you need:

1. A place to host the **web service** (Python + gunicorn) — Render, Fly.io,
   Railway, Heroku, etc.
2. A **PostgreSQL** database that survives restarts (because Render's free
   filesystem is ephemeral).
3. A **GitHub repository** to push code to.
4. A **domain name** (optional — Render gives you a free `*.onrender.com`).

We use **Render** because it's free and one-click.

## What's already wired up for you

The project root has all the deployment files:

| File | What it does |
|------|--------------|
| `requirements.txt` | List of Python packages |
| `runtime.txt` | Python version (`python-3.12.4`) |
| `Procfile` | Tells Render how to start the web server |
| `gunicorn.conf.py` | Production server tuning (workers, timeouts) |
| `render.yaml` | Blueprint — provisions web + Postgres in one click |
| `build.sh` | Runs on every deploy: pip install, migrate, ingest |

## The render.yaml blueprint, explained

```yaml
databases:
  - name: climate-law-portal-db
    plan: free
    databaseName: climate_law_portal
    user: climate_law_portal

services:
  - type: web
    name: climate-law-portal
    runtime: python
    plan: free
    buildCommand: "./build.sh"
    startCommand: "gunicorn climate_law_portal.wsgi:application --config gunicorn.conf.py"
    healthCheckPath: /health/
    autoDeploy: true
    envVars:
      - key: DJANGO_DEBUG
        value: "0"
      - key: DJANGO_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: climate-law-portal-db
          property: connectionString
      - key: CASES_INGEST_PATH
        value: ./all_text_cases
```

What this does:

* Provisions a free PostgreSQL database (`climate-law-portal-db`).
* Provisions a free web service (`climate-law-portal`).
* Wires them together: `DATABASE_URL` is auto-injected.
* Auto-generates a `SECRET_KEY`.
* Sets `DJANGO_DEBUG=0` so production-mode error pages show.
* Sets `CASES_INGEST_PATH` so `build.sh` auto-loads the 5,000 cases on the
  first deploy.

## What `build.sh` does

```bash
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
if [[ -n "$CASES_INGEST_PATH" && -d "$CASES_INGEST_PATH" ]]; then
  python manage.py ingest_cases --path "$CASES_INGEST_PATH"
fi
```

So on every deploy:

1. Install / update Python packages
2. Bundle static files (CSS) for whitenoise to serve
3. Apply database migrations
4. Optionally ingest cases (idempotent — skips already-loaded files)

## What gunicorn is

Django's built-in `runserver` is **only for development**. In production you
need a battle-tested WSGI server. **Gunicorn** is the standard choice:
multi-process, fast, simple.

The `Procfile`:

```
web: gunicorn climate_law_portal.wsgi:application --config gunicorn.conf.py
release: python manage.py migrate --noinput
```

* `web:` — start the web server.
* `release:` — runs once after every deploy, before `web:` accepts traffic.

## Environment variables

Django reads its config from environment variables in production:

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `DJANGO_SECRET_KEY` | yes | dev-fallback | Render auto-generates this |
| `DJANGO_DEBUG` | no | "1" | Set to "0" in prod |
| `DJANGO_ALLOWED_HOSTS` | no | `.onrender.com,localhost` | Comma-separated |
| `DATABASE_URL` | no | SQLite | Postgres connection string |
| `CASES_PER_PAGE` | no | "20" | Search results per page |
| `WEB_CONCURRENCY` | no | 2 | Gunicorn workers |
| `CASES_INGEST_PATH` | no | (none) | If set, ingest on each build |

## The full deploy walkthrough

For the actual click-by-click instructions, open
**`DEPLOY_GUIDE.txt`** at the project root. It covers:

1. Creating a GitHub repo
2. Pushing your code
3. Signing up at Render
4. Clicking "Blueprint" and selecting your repo
5. Watching the deploy logs
6. Getting your permanent URL
7. Updating the site later (just `git push`)

## Free-tier caveats — read these

| Caveat | Mitigation |
|--------|------------|
| Web service sleeps after 15 min of no traffic; first hit takes 30–60 s | Use UptimeRobot to ping `/health/` every 5 min |
| Free Postgres expires after 90 days | Back up with `pg_dump`, migrate to a new free DB or upgrade to $7/mo |
| Filesystem is ephemeral — SQLite would be wiped | We use Postgres, so this isn't a problem |
| 500 build minutes/month | Plenty for a hobby project |

## Where to go next

→ [11-troubleshooting.md](11-troubleshooting.md) — when things go wrong.
