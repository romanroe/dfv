#! /bin/sh

# shellcheck disable=SC2046
cd $(dirname "$0")/.. || exit

./scripts/check.sh && \
poetry build && \
poetry publish
