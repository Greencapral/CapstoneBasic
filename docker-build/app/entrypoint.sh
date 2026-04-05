#!/bin/sh
set -e

echo "Apply migrations.."
python manage.py migrate

echo "Load initial data from fixture..."
python manage.py loaddata /app/fixtures/customusers_fixture.json

echo "Collect static files.."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
