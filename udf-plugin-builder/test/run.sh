#!/usr/bin/env bash
# shfmt -i 4 -ci -sr -w run.sh
set -euo pipefail

status=0
OUT_DIR=${1:-$(pwd)}
LIST=(load_another unary_test oneof_test nested_test)
pids=()

cleanup() {
    echo "Cleaning up..."
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" > /dev/null 2>&1; then
            echo "Killing rpc_server (PID=$pid)"
            kill "$pid" || true
        fi
    done
}
trap cleanup EXIT

# 各UDFビルド
for i in "${LIST[@]}"; do
    (
        cd "$i"
        ./run.sh
        cp "build/lib${i}.ini" "$OUT_DIR"
        cp "build/lib${i}.so" "$OUT_DIR"
    )
done

tgctl shutdown || true
tgctl start

for i in "${LIST[@]}"; do
    "$i/build/rpc_server_${i}" "$OUT_DIR/lib${i}.ini" >&"log.${i}" &
    pid=$!
    pids+=("$pid")
    echo "Started rpc_server_${i} (PID=$pid)"
done

for i in "${LIST[@]}"; do
    tgsql -c ipc:tsurugi --script "$i/script/test.sql" >&"log.${i}_tgsql" || status=1
    grep "@#0" "log.${i}_tgsql" >&"log.${i}_result" || true
    if diff "$i/result/log.result" "log.${i}_result" > /dev/null 2>&1; then
        echo "OK: $i"
    else
        echo "NG: $i"
        status=1
    fi
done

exit $status
