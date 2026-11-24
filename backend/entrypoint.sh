#!/bin/sh
# Container entrypoint for the backend image.
# With RUN_MIGRATIONS=true it prepares the database first: it enables the
# pg_trgm extension (product search) and applies migrations. Then it runs
# the command it was given.
set -eu

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Enabling the pg_trgm extension..."
  python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
"
  echo "Applying migrations..."
  python manage.py migrate --noinput
fi

exec "$@"
