from pytest import raises
from unittest.mock import Mock

import grpc

from tsurugidb.udf.client.stream import ClientConfig

def test_client_config_parse():
    context = Mock(spec=grpc.ServicerContext)
    context.invocation_metadata.return_value = [
        ("X-TSURUGI-BLOB-SESSION", "123"),
        ("X-TSURUGI-BLOB-ENDPOINT", "dns:///localhost:50051"),
    ]
    config = ClientConfig.parse(context)
    assert config.session_id == 123
    assert config.endpoint == "dns:///localhost:50051"
    assert config.secure is False
    assert config.chunk_size == 1024 * 1024

def test_client_config_parse_options():
    context = Mock(spec=grpc.ServicerContext)
    context.invocation_metadata.return_value = [
        ("X-TSURUGI-BLOB-SESSION", "123"),
        ("X-TSURUGI-BLOB-ENDPOINT", "dns:///localhost:50051"),
        ("X-TSURUGI-BLOB-SECURE", "true"),
        ("X-TSURUGI-BLOB-STREAM-CHUNK-SIZE", "4096"),
    ]
    config = ClientConfig.parse(context)
    assert config.secure is True
    assert config.chunk_size == 4096

def test_client_config_parse_missing_session():
    context = Mock(spec=grpc.ServicerContext)
    context.invocation_metadata.return_value = [
        ("X-TSURUGI-BLOB-ENDPOINT", "dns:///localhost:50051"),
    ]
    with raises(ValueError):
        ClientConfig.parse(context)

def test_client_config_parse_invalid_session():
    context = Mock(spec=grpc.ServicerContext)
    context.invocation_metadata.return_value = [
        ("X-TSURUGI-BLOB-SESSION", "INVALID"),
        ("X-TSURUGI-BLOB-ENDPOINT", "dns:///localhost:50051"),
    ]
    with raises(ValueError):
        ClientConfig.parse(context)

def test_client_config_parse_missing_endpoint():
    context = Mock(spec=grpc.ServicerContext)
    context.invocation_metadata.return_value = [
        ("X-TSURUGI-BLOB-SESSION", "123"),
    ]
    with raises(ValueError):
        ClientConfig.parse(context)

def test_client_config_parse_invalid_secure():
    context = Mock(spec=grpc.ServicerContext)
    context.invocation_metadata.return_value = [
        ("X-TSURUGI-BLOB-SESSION", "123"),
        ("X-TSURUGI-BLOB-ENDPOINT", "dns:///localhost:50051"),
        ("X-TSURUGI-BLOB-SECURE", "not-a-bool"),
    ]
    with raises(ValueError):
        ClientConfig.parse(context)

def test_client_config_parse_invalid_chunk_size():
    context = Mock(spec=grpc.ServicerContext)
    context.invocation_metadata.return_value = [
        ("X-TSURUGI-BLOB-SESSION", "123"),
        ("X-TSURUGI-BLOB-ENDPOINT", "dns:///localhost:50051"),
        ("X-TSURUGI-BLOB-STREAM-CHUNK-SIZE", "not-an-int"),
    ]
    with raises(ValueError):
        ClientConfig.parse(context)
