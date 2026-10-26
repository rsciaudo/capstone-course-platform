#!/usr/bin/env bash
# Apply untracked SQL files in db/migrations and record them in schema_migrations.
# Runs psql inside the Compose db service, so PostgreSQL is not installed on the host.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${POSTGRES_USER:?POSTGRES_USER is required in .env}"
: "${POSTGRES_DB:?POSTGRES_DB is required in .env}"

psql_exec() {
  docker compose exec -T db \
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"
}

psql_exec <<'SQL'
create table if not exists schema_migrations (
  filename text primary key,
  applied_at timestamptz not null default now()
);
SQL

shopt -s nullglob
files=(db/migrations/*.sql)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No migration files in db/migrations."
  exit 0
fi

for file in "${files[@]}"; do
  filename="$(basename "$file")"

  if [[ ! "$filename" =~ ^[0-9A-Za-z._-]+$ ]]; then
    echo "Refusing migration filename: $filename" >&2
    exit 1
  fi

  applied="$(psql_exec -tA -c "select 1 from schema_migrations where filename = '${filename}'")" || exit 1
  applied="${applied//[[:space:]]/}"

  if [[ "$applied" == "1" ]]; then
    echo "already applied: $filename"
    continue
  fi

  echo "applying: $filename"
  {
    echo "begin;"
    cat "$file"
    echo "insert into schema_migrations (filename) values ('${filename}');"
    echo "commit;"
  } | psql_exec
done
