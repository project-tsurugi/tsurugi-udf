from unittest.mock import Mock

from tsurugidb.udf.client.grpc import (
    blob_relay_streaming_pb2 as pb_message,
    blob_reference_pb2 as pb_model,
)

from tsurugidb.udf.client.stream import StreamBlobRelayClient

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
