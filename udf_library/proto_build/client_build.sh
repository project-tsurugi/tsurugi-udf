#!/bin/bash

TSURUGI_DIR=${HOME}/git/tsurugidb
RELAY=${TSURUGI_DIR}/data-relay-grpc
PRO=${RELAY}/protos/blob_relay
OUT=../tsurugi/udf/client/grpc
for i in blob_reference.proto  blob_relay_local.proto  blob_relay_streaming.proto
do
    python3 -m grpc_tools.protoc -I ${PRO} --python_out=${OUT} ${PRO}/$i
done
