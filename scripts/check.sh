#! /bin/sh

# shellcheck disable=SC2046
cd $(dirname "$0")/.. || exit

failed=0

echo "\n-------------------- Black --------------------"
./.venv/bin/black . || failed=1

# Disabled, da aufgrund der Volltextsuche PostgreSQL nötig ist
#echo "\n-------------------- Tests --------------------"
#./.venv/bin/python manage.py test --parallel 20 || failed=1

echo "\n-------------------- Ruff --------------------"
./.venv/bin/ruff . || failed=1

echo "\n-------------------- Validate Templates --------------------"
./.venv/bin/python manage.py validate_templates || failed=1

echo "\n-------------------- MyPy --------------------"
./.venv/bin/mypy . || failed=1

if [ "$failed" -ne 0 ] ; then
    echo "!!! CHECK FAILED !!!"
    exit 1
fi


