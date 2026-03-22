#!/usr/bin/env bash
set -o errexit

pip install gunicorn django whitenoise dj-database-url psycopg2-binary Pillow
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
chmod +x build.sh