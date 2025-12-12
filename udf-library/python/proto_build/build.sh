#!/bin/bash
python3 -m grpc_tools.protoc \
    -I ../../proto \
    --python_out=../tsurugidb/udf/model \
    ../../proto/tsurugi_types.proto
