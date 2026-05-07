#!/usr/bin/env bash
# Render build hook — installs deps, collects static, applies migrations.
set -o errexit
set -o pipefail
set -o nounset

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing requirements"
pip install -r requirements.txt

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Applying database migrations"
python manage.py migrate --noinput

# Create the admin user from env vars (idempotent — no-op if it exists or
# if the env vars aren't set). Required because Render's free tier has no
# shell, so `python manage.py createsuperuser` can't be run interactively.
echo "==> Ensuring admin superuser"
python manage.py ensure_superuser

# If a CASES_INGEST_PATH env var points to a folder of .txt cases, ingest them.
if [[ -n "${CASES_INGEST_PATH:-}" && -d "${CASES_INGEST_PATH}" ]]; then
  echo "==> Ingesting cases from ${CASES_INGEST_PATH}"
  python manage.py ingest_cases --path "${CASES_INGEST_PATH}" || true
fi

echo "==> Build complete"
