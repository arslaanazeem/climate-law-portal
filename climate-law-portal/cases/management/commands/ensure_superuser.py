"""
Idempotently create a Django superuser from environment variables.

Designed for Render's free tier (no shell access) — runs during the build step
in build.sh on every deploy. If the user already exists nothing happens, so
it's safe to leave wired up indefinitely.

Reads the standard Django env vars:
    DJANGO_SUPERUSER_USERNAME   (required)
    DJANGO_SUPERUSER_EMAIL      (optional, defaults to "")
    DJANGO_SUPERUSER_PASSWORD   (required)

If either required var is missing, the command prints a notice and exits 0
(non-fatal) so the build doesn't break for users who haven't set the vars yet.

Usage (locally):
    python manage.py ensure_superuser
"""
from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from DJANGO_SUPERUSER_* env vars if it doesn't exist."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not username or not password:
            self.stdout.write(
                "ensure_superuser: DJANGO_SUPERUSER_USERNAME and "
                "DJANGO_SUPERUSER_PASSWORD env vars are not both set — "
                "skipping superuser creation."
            )
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                f"ensure_superuser: user '{username}' already exists — nothing to do."
            )
            return

        User.objects.create_superuser(
            username=username, email=email, password=password
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"ensure_superuser: created superuser '{username}'."
            )
        )
