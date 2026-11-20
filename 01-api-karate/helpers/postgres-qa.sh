#!/usr/bin/env bash
set -euo pipefail

action=$1
run_id=$2
port=$3
[[ "$run_id" =~ ^[a-f0-9]{32}$ && "$port" =~ ^[0-9]{4,5}$ ]]

installation="$HOME/.local/share/visiontext-postgres/portable"
postgres="$installation/usr/lib/postgresql/16/bin"
if [[ -x "$postgres/postgres" ]]; then
    export LD_LIBRARY_PATH="$installation/usr/lib/x86_64-linux-gnu"
else
    postgres=/usr/lib/postgresql/16/bin
fi
runtime="/tmp/visiontext-karate-$run_id"
export PGDATA="$runtime/data"

case "$action" in
    start)
        if [[ ! -x "$postgres/postgres" ]]; then
            echo 'Instala PostgreSQL 16 en Ubuntu WSL o prepara sus binarios portables.' >&2
            exit 1
        fi
        if [[ -z "$VT_QA_DB_PASSWORD" ]]; then exit 1; fi
        mkdir -m 700 -- "$runtime"
        "$postgres/initdb" --auth=scram-sha-256 --username=karate --locale=C --encoding=UTF8 \
            --pwfile=<(printf '%s\n' "$VT_QA_DB_PASSWORD")
        "$postgres/pg_ctl" start --wait --log="$runtime/postgres.log" \
            --options="-h 127.0.0.1 -p $port -k $runtime"
        ;;
    stop)
        if [[ -d "$runtime" ]]; then
            [[ "$(realpath -- "$runtime")" == "$runtime" ]]
            if "$postgres/pg_ctl" status >/dev/null 2>&1; then
                "$postgres/pg_ctl" stop --wait --mode fast
            fi
            rm -rf -- "$runtime"
        fi
        ;;
    *)
        printf 'Acción PostgreSQL no reconocida.\n' >&2
        exit 1
        ;;
esac
