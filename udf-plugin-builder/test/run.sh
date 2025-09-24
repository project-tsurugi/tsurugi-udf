#!/bin/bash 
set -euo pipefail

OUT_DIR=${1:-$(pwd)}
LIST=(load_another unary_test)
for i in ${LIST[@]}
do
    (
      cd "$i"
      ./run.sh
      cp "build/lib${i}.ini" "$OUT_DIR"
      cp "build/lib${i}.so"  "$OUT_DIR"
    )
done

for i in ${LIST[@]}
do
    (
      echo "$i/build/rpc_server_${i} $OUT_DIR/lib${i}.ini"
      echo "tgsql -c ipc:tsurugi --script $i/script/test.sql"
    )
done
echo "tgctl shutdonw ; tgctl start"

