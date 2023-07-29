#! /bin/sh

# shellcheck disable=SC2046
cd $(dirname "$0")/.. || exit

DB_HOST=localhost poetry run python manage.py reset_db --noinput
DB_HOST=localhost poetry run python manage.py migrate
DB_HOST=localhost poetry run python manage.py devdata
