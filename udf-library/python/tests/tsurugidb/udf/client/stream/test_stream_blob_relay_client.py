from pytest import raises
from unittest.mock import Mock

import grpc

from datetime import timedelta

from tsurugidb.udf.client.grpc import (
    blob_relay_streaming_pb2 as pb_message,
    blob_reference_pb2 as pb_model,
)

from tsurugidb.udf.client.stream import StreamBlobRelayClient
from tsurugidb.udf import BlobRelayError, BlobRelayTimeoutError

def error_mock(code: grpc.StatusCode) -> grpc.RpcError:
    error = grpc.RpcError()
    error.code = Mock(return_value=code)
    return error

def test_download_blob(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(data),
            )
        ),
        pb_message.GetStreamingResponse(
            chunk=data,
        ),
    ])
    destination = tmp_path / "download.bin"
    client.download_blob(
        ref=pb_model.BlobReference(
            storage_id=1,
            object_id=1,
            tag=0,
        ),
        destination=destination,
    )

    assert destination.is_file()
    assert destination.read_bytes() == data

    options = stub.Get.call_args[1]
    assert options.get("timeout") is None

def test_download_clob(tmp_path):
    data = "Hello, CLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(data),
            )
        ),
        pb_message.GetStreamingResponse(
            chunk=data,
        ),
    ])
    destination = tmp_path / "download.bin"
    client.download_clob(
        ref=pb_model.BlobReference(
            storage_id=1,
            object_id=1,
            tag=0,
        ),
        destination=destination,
    )

    assert destination.is_file()
    assert destination.read_bytes() == data

def test_download_blob_empty(tmp_path):
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(b"")

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=0,
            )
        ),
    ])
    destination = tmp_path / "download.bin"
    client.download_blob(
        ref=pb_model.BlobReference(
            storage_id=1,
            object_id=1,
            tag=0,
        ),
        destination=destination,
    )

    assert destination.is_file()
    assert destination.read_bytes() == b""

def test_download_blob_multiple_chunks(tmp_path):
    d0 = "Hello".encode("utf-8")
    d1 = ", ".encode("utf-8")
    d2 = "BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(d0 + d1 + d2)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(d0) + len(d1) + len(d2),
            )
        ),
        pb_message.GetStreamingResponse(
            chunk=d0,
        ),
        pb_message.GetStreamingResponse(
            chunk=d1,
        ),
        pb_message.GetStreamingResponse(
            chunk=d2,
        ),
    ])
    destination = tmp_path / "download.bin"
    client.download_blob(
        ref=pb_model.BlobReference(
            storage_id=1,
            object_id=1,
            tag=0,
        ),
        destination=destination,
    )

    assert destination.is_file()
    assert destination.read_bytes() == d0 + d1 + d2

def test_download_blob_existing(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(data),
            )
        ),
        pb_message.GetStreamingResponse(
            chunk=data,
        ),
    ])
    destination = tmp_path / "download.bin"
    existing = b"EXISTING DATA"
    destination.write_bytes(existing)
    with raises(OSError):
        client.download_blob(
            ref=pb_model.BlobReference(
                storage_id=1,
                object_id=1,
                tag=0,
            ),
            destination=destination,
        )

    assert destination.is_file()
    assert destination.read_bytes() == existing

def test_download_blob_missing_metadata(tmp_path):
    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            chunk=b"INVALID",
        ),
    ])
    destination = tmp_path / "download.bin"

    with raises(BlobRelayError):
        client.download_blob(
            ref=pb_model.BlobReference(
                storage_id=1,
                object_id=1,
                tag=0,
            ),
            destination=destination,
        )

    assert not destination.exists()

def test_download_blob_missing_body(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(data),
            )
        ),
    ])
    destination = tmp_path / "download.bin"
    with raises(BlobRelayError):
        client.download_blob(
            ref=pb_model.BlobReference(
                storage_id=1,
                object_id=1,
                tag=0,
            ),
            destination=destination,
        )

    assert not destination.exists()

def test_download_blob_multiple_metadata(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(data),
            )
        ),
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(data),
            )
        ),
        pb_message.GetStreamingResponse(
            chunk=data,
        ),
    ])
    destination = tmp_path / "download.bin"
    with raises(BlobRelayError):
        client.download_blob(
            ref=pb_model.BlobReference(
                storage_id=1,
                object_id=1,
                tag=0,
            ),
            destination=destination,
        )

    assert not destination.exists()

def test_download_blob_inconsistent_blob_size(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.return_value = iter([
        pb_message.GetStreamingResponse(
            metadata=pb_message.GetStreamingResponse.Metadata(
                blob_size=len(data) - 1,
            )
        ),
        pb_message.GetStreamingResponse(
            chunk=data,
        ),
    ])
    destination = tmp_path / "download.bin"
    with raises(BlobRelayError):
        client.download_blob(
            ref=pb_model.BlobReference(
                storage_id=1,
                object_id=1,
                tag=0,
            ),
            destination=destination,
        )

    assert not destination.exists()

def test_download_blob_server_error(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.side_effect = error_mock(grpc.StatusCode.INTERNAL)
    destination = tmp_path / "download.bin"
    with raises(BlobRelayError):
        client.download_blob(
            ref=pb_model.BlobReference(
                storage_id=1,
                object_id=1,
                tag=0,
            ),
            destination=destination,
        )

    assert not destination.exists()

def test_download_blob_timeout(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    server_file = tmp_path / "server_blob.bin"
    server_file.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Get.side_effect = error_mock(grpc.StatusCode.DEADLINE_EXCEEDED)
    destination = tmp_path / "download.bin"
    with raises(BlobRelayTimeoutError):
        client.download_blob(
            ref=pb_model.BlobReference(
                storage_id=1,
                object_id=1,
                tag=0,
            ),
            destination=destination,
            timeout=timedelta(seconds=10),
        )

    assert stub.Get.call_count == 1
    options = stub.Get.call_args[1]
    assert options.get("timeout") == 10.0

    assert not destination.exists()

def test_upload_blob(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    source = tmp_path / "upload.bin"
    source.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Put.return_value = pb_message.PutStreamingResponse(
        blob=pb_model.BlobReference(
            storage_id=1,
            object_id=2,
            tag=0,
        )
    )

    blob_ref = client.upload_blob(source=source)

    assert stub.Put.call_count == 1
    request = list(stub.Put.call_args[0][0])
    assert len(request) == 2
    assert request[0].metadata.blob_size == len(data)
    assert request[1].chunk == data

    assert blob_ref.storage_id == 1
    assert blob_ref.object_id == 2
    assert blob_ref.tag == 0

    options = stub.Put.call_args[1]
    assert options.get("timeout") is None

def test_upload_clob(tmp_path):
    data = "Hello, CLOB!".encode("utf-8")
    source = tmp_path / "upload.bin"
    source.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Put.return_value = pb_message.PutStreamingResponse(
        blob=pb_model.BlobReference(
            storage_id=1,
            object_id=2,
            tag=0,
        )
    )

    blob_ref = client.upload_clob(source=source)

    assert stub.Put.call_count == 1
    request = list(stub.Put.call_args[0][0])
    assert len(request) == 2
    assert request[0].metadata.blob_size == len(data)
    assert request[1].chunk == data

    assert blob_ref.storage_id == 1
    assert blob_ref.object_id == 2
    assert blob_ref.tag == 0

def test_upload_blob_empty(tmp_path):
    source = tmp_path / "upload.bin"
    source.write_bytes(b"")

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Put.return_value = pb_message.PutStreamingResponse(
        blob=pb_model.BlobReference(
            storage_id=1,
            object_id=2,
            tag=0,
        )
    )

    blob_ref = client.upload_blob(source=source)

    assert stub.Put.call_count == 1
    request = list(stub.Put.call_args[0][0])
    assert len(request) == 1
    assert request[0].metadata.blob_size == 0

    assert blob_ref.storage_id == 1
    assert blob_ref.object_id == 2
    assert blob_ref.tag == 0

def test_upload_blob_multiple_chunks(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    source = tmp_path / "upload.bin"
    source.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
        chunk_size=5,
    )

    stub.Put.return_value = pb_message.PutStreamingResponse(
        blob=pb_model.BlobReference(
            storage_id=1,
            object_id=2,
            tag=0,
        )
    )

    blob_ref = client.upload_blob(source=source)

    assert stub.Put.call_count == 1
    request = list(stub.Put.call_args[0][0])
    assert len(request) == 4
    assert request[0].metadata.blob_size == len(data)
    assert request[1].chunk == data[:5]
    assert request[2].chunk == data[5:10]
    assert request[3].chunk == data[10:]

    assert blob_ref.storage_id == 1
    assert blob_ref.object_id == 2
    assert blob_ref.tag == 0

def test_upload_blob_missing_source(tmp_path):
    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Put.return_value = pb_message.PutStreamingResponse(
        blob=pb_model.BlobReference(
            storage_id=1,
            object_id=2,
            tag=0,
        )
    )

    source = tmp_path / "upload.bin"
    with raises(OSError):
        client.upload_blob(source=source)

def test_upload_blob_server_error(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    source = tmp_path / "upload.bin"
    source.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Put.side_effect = error_mock(grpc.StatusCode.UNAVAILABLE)

    with raises(BlobRelayError):
        client.upload_blob(source=source)

def test_upload_blob_timeout(tmp_path):
    data = "Hello, BLOB!".encode("utf-8")
    source = tmp_path / "upload.bin"
    source.write_bytes(data)

    stub = Mock() # without spec because gRPC stub has no regular methods
    client = StreamBlobRelayClient(
        stub=stub,
        session_id=1,
    )

    stub.Put.side_effect = error_mock(grpc.StatusCode.DEADLINE_EXCEEDED)

    with raises(BlobRelayTimeoutError):
        client.upload_blob(source=source, timeout=timedelta(seconds=5))

    assert stub.Put.call_count == 1
    options = stub.Put.call_args[1]
    assert options.get("timeout") == 5.0
