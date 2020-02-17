#!/bin/sh

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Start Django server
gunicorn melting_potlist.wsgi:application --bind 0.0.0.0:8000