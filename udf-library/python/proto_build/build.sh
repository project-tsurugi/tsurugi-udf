#!/bin/bash
python3 -m grpc_tools.protoc \
    -I ../../../proto/tsurugidb/udf \
    --python_out=../tsurugidb/udf/model \
    tsurugi_types.proto
