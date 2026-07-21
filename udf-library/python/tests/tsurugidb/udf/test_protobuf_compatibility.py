import importlib

import pytest


PB2_MODULES = [
    "tsurugidb.udf.tsurugi_types_pb2",
    "tsurugidb.udf.client.grpc.blob_reference_pb2",
    "tsurugidb.udf.client.grpc.blob_relay_local_pb2",
    "tsurugidb.udf.client.grpc.blob_relay_streaming_pb2",
]

PB2_GRPC_MODULES = [
    "tsurugidb.udf.client.grpc.blob_reference_pb2_grpc",
    "tsurugidb.udf.client.grpc.blob_relay_local_pb2_grpc",
    "tsurugidb.udf.client.grpc.blob_relay_streaming_pb2_grpc",
]


def test_protobuf_runtime_supports_7_35_generated_code() -> None:
    from google.protobuf import runtime_version

    runtime_version.ValidateProtobufRuntimeVersion(
        runtime_version.Domain.PUBLIC,
        7,
        35,
        0,
        "",
        "compatibility_test.proto",
    )


@pytest.mark.parametrize("module_name", PB2_MODULES)
def test_generated_protobuf_module_can_be_imported(module_name: str) -> None:
    module = importlib.import_module(module_name)

    assert module.DESCRIPTOR is not None


@pytest.mark.parametrize("module_name", PB2_GRPC_MODULES)
def test_generated_grpc_module_can_be_imported(module_name: str) -> None:
    module = importlib.import_module(module_name)

    assert module is not None
