import os
import sys
from pathlib import Path
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.core.wsgi import get_wsgi_application

# Vercel Python runtime entrypoint for Django.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portal_transparencia.settings")

app = get_wsgi_application()


def _as_bool(value: Optional[str], *, default: int = 0) -> bool:
    if value is None:
        return bool(default)
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _ensure_bootstrap_superuser() -> None:
    password = (os.getenv("DJANGO_BOOTSTRAP_ADMIN_PASSWORD") or "").strip()
    if not password:
        return

    username = (os.getenv("DJANGO_BOOTSTRAP_ADMIN_USERNAME") or "admin").strip() or "admin"
    email = (os.getenv("DJANGO_BOOTSTRAP_ADMIN_EMAIL") or "").strip()

    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
        },
    )

    changed = created
    if email and user.email != email:
        user.email = email
        changed = True
    if not user.is_staff:
        user.is_staff = True
        changed = True
    if not user.is_superuser:
        user.is_superuser = True
        changed = True
    if not user.check_password(password):
        user.set_password(password)
        changed = True

    if changed:
        user.save()


def _apply_pending_migrations() -> None:
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    if executor.migration_plan(targets):
        call_command("migrate", interactive=False, run_syncdb=True, verbosity=0)


if _as_bool(os.getenv("DJANGO_AUTO_MIGRATE_ON_BOOT"), default=True):
    _apply_pending_migrations()

_ensure_bootstrap_superuser()
