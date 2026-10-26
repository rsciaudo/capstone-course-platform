#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env first." >&2
  exit 1
fi

psql_in_db() {
  docker compose exec -T db \
    sh -c 'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"' \
    psql "$@"
}

psql_in_db -q <<'SQL'
SET client_min_messages TO warning;
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);
SQL

shopt -s nullglob
files=("$root"/db/migrations/*.sql)
if [[ "${#files[@]}" -eq 0 ]]; then
  echo "No migration files found."
  exit 0
fi

for file in "${files[@]}"; do
  name="$(basename "$file")"
  already="$(printf '%s\n' "SELECT 1 FROM schema_migrations WHERE filename = :'filename';" \
    | psql_in_db -tA -v filename="$name")" || exit 1
  already="${already//[[:space:]]/}"

  if [[ "$already" == "1" ]]; then
    echo "Already applied: $name"
    continue
  fi

  echo "Applying: $name"
  {
    cat "$file"
    cat <<'SQL'

INSERT INTO schema_migrations (filename) VALUES (:'filename');
SQL
  } | psql_in_db --single-transaction -v filename="$name"
done
