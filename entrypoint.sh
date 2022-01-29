#!/bin/sh

# Set settings env variable
export DJANGO_SETTINGS_MODULE=melting_potlist.settings

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Start Django server
gunicorn melting_potlist.asgi:application -w 4 -k uvicorn.workers.UvicornWorker
# gunicorn melting_potlist.wsgi:application --bind 0.0.0.0:8000
# daphne -b 0.0.0.0 -p 8000 melting_potlist.asgi:application
