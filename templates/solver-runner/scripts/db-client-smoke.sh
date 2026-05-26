#!/usr/bin/env bash
set -euo pipefail

sqlite_result="$(
  sqlite3 ":memory:" \
    "create table checks(id integer primary key, name text not null); insert into checks(name) values ('solver-runner'); select count(*) from checks;"
)"

if [[ "${sqlite_result}" != "1" ]]; then
  echo "sqlite smoke expected 1, got ${sqlite_result}" >&2
  exit 1
fi

psql --version | grep -q "psql"

echo "db-client-smoke: sqlite execution and psql availability verified"

