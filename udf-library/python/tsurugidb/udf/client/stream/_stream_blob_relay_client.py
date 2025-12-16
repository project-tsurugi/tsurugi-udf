# package: tsurugidb.udf.client.stream

import grpc
import time
from datetime import timedelta
from pathlib import Path
from typing import Type, TypeVar

from ... import (
    BlobRelayClient,
    BlobRelayError,
    BlobReference as UdfBlobReference,
    ClobReference as UdfClobReference,
)

from ..grpc import (
    blob_relay_streaming_pb2 as pb_message,
    blob_relay_streaming_pb2_grpc as pb_service,
    blob_reference_pb2 as pb_model,
)

T = TypeVar("T", bound=UdfBlobReference | UdfClobReference)

class StreamBlobRelayClient(BlobRelayClient):
    """An implementation of BlobRelayClient that exchanges BLOBs via gRPC streaming."""

    __API_VERSION = 1

    def __init__(
            self,
            stub: pb_service.BlobRelayStreamingStub,
            session_id: int,
            *,
            chunk_size: int = 1_048_576):
        """Creates a new instance.

        Args:
            stub: The gRPC stub to use for communication with the BLOB relay service.
            session_id: The session ID for the BLOB relay service.
            chunk_size: The size of each chunk to use when streaming data. Default is 1,048,576 bytes (1 MB).
        """
        self.__stub = stub
        self.__session_id = session_id
        self.__chunk_size = chunk_size

    @classmethod
    def api_version(cls) -> int:
        """Returns the API version of this client implementation.

        Returns:
            The API version as an integer.
        """
        return cls.__API_VERSION

    def __deadline_timestamp(self, timeout: float | None) -> float | None:
        if timeout is not None:
            return time.time() + timeout
        return None

    def __download_internal(
            self,
            ref: pb_model.BlobReference,
            destination: Path,
            timeout: float | None = None) -> None:
        req = pb_message.GetStreamingRequest(
            api_version=self.api_version(),
            session_id=self.__session_id,
            blob=ref,
        )
        try:
            with destination.open("xb") as fp:
                expected_size: int | None = None
                saw_metadata = False
                actual_size = 0
                for resp in self.__stub.Get(req, deadline=self.__deadline_timestamp(timeout)):
                    if not saw_metadata:
                        # first time - receive metadata
                        saw_metadata = True
                        if not resp.HasField("metadata"):
                            raise BlobRelayError("invalid response: missing metadata")
                        metadata = resp.metadata
                        if metadata.HasField("blob_size"):
                            expected_size = metadata.blob_size
                    # rest times - receive chunks
                    else:
                        if not resp.HasField("chunk"):
                            raise BlobRelayError("invalid response: missing chunk")
                        chunk = resp.chunk
                        fp.write(chunk)
                        actual_size += len(chunk)

                if expected_size is not None and actual_size != expected_size:
                    raise BlobRelayError(f"download size mismatch: expected {expected_size}, got {actual_size}")

        except OSError as e:
            raise BlobRelayError(f"exception occurred during writing downloaded file: {e}") from e
        except grpc.RpcError as e:
            raise BlobRelayError(f"download failed: {e}") from e
    def __upload_internal(
            self,
            source: Path,
            timeout: float | None = None) -> pb_model.BlobReference:
        try:
            blob_size = source.stat().st_size

            def gen():
                # first time - send metadata
                yield pb_message.PutStreamingRequest(
                    metadata=pb_message.PutStreamingRequest.Metadata(
                        api_version=self.api_version(),
                        session_id=self.__session_id,
                        blob_size=blob_size,
                    )
                )
                # rest times - send chunks
                with source.open("rb") as fp:
                    while True:
                        buf = fp.read(self.__chunk_size)
                        if not buf:
                            break
                        yield pb_message.PutStreamingRequest(chunk=buf)

            resp = self.__stub.Put(gen(), deadline=self.__deadline_timestamp(timeout))
            return resp.blob

        except OSError as e:
            raise BlobRelayError(f"exception occurred during reading file to upload: {e}") from e
        except grpc.RpcError as e:
            raise BlobRelayError(f"upload failed: {e}") from e

    def __to_pb_reference(self, ref: UdfBlobReference | UdfClobReference) -> pb_model.BlobReference:
        return pb_model.BlobReference(
            storage_id=ref.storage_id,
            object_id=ref.object_id,
            tag=ref.tag,
            # pb_reference has no provisioned field since relay service does not use it for now
        )

    def __from_pb_reference(self, ref: pb_model.BlobReference, return_class: Type[T]) -> T:
        return return_class(
            storage_id=ref.storage_id,
            object_id=ref.object_id,
            tag=ref.tag,
            provisioned=False,  # provisioned field is not relevant for relay service
        )

    def download_blob(self, ref: UdfBlobReference, destination: Path) -> None:
        ref_pb = self.__to_pb_reference(ref)
        return self.__download_internal(ref_pb, destination)

    def download_clob(self, ref: UdfClobReference, destination: Path) -> None:
        ref_pb = self.__to_pb_reference(ref)
        return self.__download_internal(ref_pb, destination)

    def upload_blob(self, source: Path) -> UdfBlobReference:
        ref_pb = self.__upload_internal(source)
        return self.__from_pb_reference(ref_pb, UdfBlobReference)

    def upload_clob(self, source: Path) -> UdfClobReference:
        ref_pb = self.__upload_internal(source)
        return self.__from_pb_reference(ref_pb, UdfClobReference)

__all__ = [
    "StreamBlobRelayClient",
]
