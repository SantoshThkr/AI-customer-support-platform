#!/bin/sh
set -e

# Apply pending migrations before starting the API.
alembic upgrade head

exec "$@"
