#!/usr/bin/env bash
# shfmt -w

set -euo pipefail

TSURUGI_DIR="${HOME}/git/tsurugidb"
RELAY="${TSURUGI_DIR}/data-relay-grpc/protos"
PACK="data_relay_grpc/proto/blob_relay"
PRO="${RELAY}/${PACK}"

OUT="../tsurugidb/udf/client/grpc"
TMP="$(mktemp -d)"

mkdir -p "${OUT}"

python3 -m grpc_tools.protoc \
	-I "${RELAY}" \
	--python_out="${TMP}" \
	--grpc_python_out="${TMP}" \
	"${PRO}/blob_reference.proto" \
	"${PRO}/blob_relay_local.proto" \
	"${PRO}/blob_relay_streaming.proto"

cp "${TMP}"/data_relay_grpc/proto/blob_relay/*_pb2*.py "${OUT}/"

for f in "${OUT}"/*_pb2*.py; do
	sed -i -E \
		's|from data_relay_grpc\.proto\.blob_relay import ([a-zA-Z0-9_]+_pb2)|from . import \1|' \
		"$f"
done

rm -rf "${TMP}"

echo "OK: pb2 files generated flat under ${OUT}"
