#!/usr/bin/env bash
# Unified migrate.sh: supports DATABASE_URL as argument or env vars for host/user/db/password
set -euo pipefail

PSQL_OPTS="-v ON_ERROR_STOP=1"
DIR=$(cd "$(dirname "$0")" && pwd)

if [ "$#" -ge 1 ]; then
  DB_URL="$1"
  echo "Applying migrations using DATABASE_URL: $DB_URL"
  for f in "$DIR"/migrations/*.sql; do
    echo "---- applying: $f"
    psql "$DB_URL" -f "$f"
  done
  echo "All migrations applied."
  exit 0
fi

# If no DATABASE_URL, use env vars
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

if [ -z "$DB_PASSWORD" ]; then
  echo "Usage: $0 <DATABASE_URL> OR set DB_HOST, DB_PORT, DB_USER, DB_NAME, DB_PASSWORD env vars"
  exit 1
fi

echo "Running migrations on $DB_NAME as $DB_USER at $DB_HOST $DB_PORT..."
export PGPASSWORD="$DB_PASSWORD"
for migration in "$DIR"/migrations/*.sql; do
  echo "Applying $migration..."
  psql $PSQL_OPTS -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration"
done
unset PGPASSWORD
echo "Migrations complete."
