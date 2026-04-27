#!/usr/bin/env sh
set -e

if [ "${WAIT_FOR_DB:-1}" = "1" ]; then
  python - <<'PY'
import os
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portal_transparencia.settings")

from django.db import connections
from django.db.utils import OperationalError

max_attempts = int(os.getenv("DB_MAX_ATTEMPTS", "30"))
sleep_seconds = float(os.getenv("DB_RETRY_SECONDS", "2"))

for attempt in range(1, max_attempts + 1):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
        print("Database connection OK.")
        break
    except OperationalError:
        if attempt == max_attempts:
            raise
        print(f"Database unavailable (attempt {attempt}/{max_attempts}). Retrying...")
        time.sleep(sleep_seconds)
PY
fi

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

exec gunicorn portal_transparencia.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout ${GUNICORN_TIMEOUT:-120}
