#!/bin/bash
python3 -m grpc_tools.protoc \
    -I ../../proto \
    --python_out=../tsurugi/udf/model \
    ../../proto/tsurugi_types.proto
