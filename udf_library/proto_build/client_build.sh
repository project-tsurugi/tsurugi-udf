#!/bin/bash
TSURUGI_DIR=${HOME}/git/tsurugidb
RELAY=${TSURUGI_DIR}/data-relay-grpc
PRO=${RELAY}/protos/blob_relay
OUT=../tsurugi/udf/client/grpc

python3 -m grpc_tools.protoc \
	-I ${PRO} \
	--python_out=${OUT} \
	--grpc_python_out=${OUT} \
	${PRO}/blob_reference.proto \
	${PRO}/blob_relay_local.proto \
	${PRO}/blob_relay_streaming.proto

# --- Fix imports in generated pb2 files ---
for f in ${OUT}/*pb2*.py; do
	# "import xxx_pb2" → "from . import xxx_pb2"
	sed -i -E 's/^import ([a-zA-Z0-9_]+_pb2)/from . import \1/' "$f"

	# "from xxx_pb2 import ..." → "from .xxx_pb2 import ..."
	sed -i -E 's/^from ([a-zA-Z0-9_]+_pb2)/from .\1/' "$f"
done
