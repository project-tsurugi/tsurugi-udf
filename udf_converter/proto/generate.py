#!/bin/bash
OUT_DIR=../udf_converter
python3 -m grpc_tools.protoc \
    -I . \
    --python_out=${OUT_DIR} \
    tsurugi_types.proto
