# package: tsurugidb.udf.client.stream

import grpc
import logging

from contextlib import suppress
from datetime import timedelta
from google.protobuf.text_format import MessageToString
from pathlib import Path
from typing import Type, TypeVar

from ... import (
    BlobRelayClient,
    BlobRelayError,
    BlobRelayTimeoutError,
    BlobReference as UdfBlobReference,
    ClobReference as UdfClobReference,
)

from ..grpc import (
    blob_relay_streaming_pb2 as pb_message,
    blob_relay_streaming_pb2_grpc as pb_service,
    blob_reference_pb2 as pb_model,
)

T = TypeVar("T", bound=UdfBlobReference | UdfClobReference)

LOGGER_NAME = 'tsurugidb.udf.blob.stream.client'

logger = logging.getLogger(LOGGER_NAME)

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

    def __download_internal(
            self,
            ref: pb_model.BlobReference,
            destination: Path,
            timeout: float | None = None) -> None:
        if destination.exists():
            raise FileExistsError(f"destination file already exists: {destination}")

        req = pb_message.GetStreamingRequest(
            api_version=self.api_version(),
            session_id=self.__session_id,
            blob=ref,
        )
        file_staging = False
        try:
            with destination.open("xb") as fp:
                file_staging = True
                expected_size: int | None = None
                saw_metadata = False
                actual_size = 0
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "start downloading BLOB: request=%s, timeout=%s",
                        MessageToString(req, as_one_line=True),
                        timeout)
                for resp in self.__stub.Get(req, timeout=timeout):
                    if not saw_metadata:
                        # first time - receive metadata
                        saw_metadata = True
                        if not resp.HasField("metadata"):
                            raise BlobRelayError("invalid response: missing metadata")
                        metadata = resp.metadata
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(
                                "stream downloading BLOB metadata: %s",
                                MessageToString(metadata, as_one_line=True))
                        if metadata.HasField("blob_size"):
                            expected_size = metadata.blob_size
                    # rest times - receive chunks
                    else:
                        if not resp.HasField("chunk"):
                            raise BlobRelayError("invalid response: missing chunk")
                        chunk = resp.chunk
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug("stream downloading BLOB chunk: size=%d", len(chunk))
                        fp.write(chunk)
                        actual_size += len(chunk)

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "finish downloading BLOB: request=%s, timeout=%s, actual_size=%d",
                        MessageToString(req, as_one_line=True),
                        timeout,
                        actual_size)

                if expected_size is not None and actual_size != expected_size:
                    raise BlobRelayError(f"download size mismatch: expected {expected_size}, got {actual_size}")
            file_staging = False
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                raise BlobRelayTimeoutError("download operation timed out") from e
            raise BlobRelayError(f"download failed: {e}") from e
        finally:
            if file_staging and destination.exists():
                with suppress(Exception):
                    destination.unlink()


    def __upload_internal(
            self,
            source: Path,
            timeout: float | None = None) -> pb_model.BlobReference:
        if not source.exists():
            raise FileNotFoundError(f"source file does not exist: {source}")

        try:
            blob_size = source.stat().st_size

            def gen():
                # first time - send metadata
                metadata = pb_message.PutStreamingRequest.Metadata(
                    api_version=self.api_version(),
                    session_id=self.__session_id,
                    blob_size=blob_size,
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "stream uploading BLOB metadata: %s",
                        MessageToString(metadata, as_one_line=True))
                yield pb_message.PutStreamingRequest(metadata=metadata)
                # rest times - send chunks
                with source.open("rb") as fp:
                    while True:
                        buf = fp.read(self.__chunk_size)
                        if not buf:
                            break
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug("stream uploading BLOB chunk: size=%d", len(buf))
                        yield pb_message.PutStreamingRequest(chunk=buf)

            # NOTE: Client Streaming RPC does not actually start sending data, but keep this logging for symmetry.
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("start uploading BLOB: source=%s, size=%d, timeout=%s", source, blob_size, timeout)
            resp = self.__stub.Put(gen(), timeout=timeout)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "finish uploading BLOB: source=%s, size=%d, timeout=%s, response=%s",
                    source,
                    blob_size,
                    timeout,
                    MessageToString(resp, as_one_line=True))

            return resp.blob

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                raise BlobRelayTimeoutError("upload operation timed out") from e
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

    def __to_seconds(self, timeout: timedelta | int | float | None) -> float | None:
        if timeout is None:
            return None
        if isinstance(timeout, timedelta):
            return timeout.total_seconds()
        return float(timeout)

    def download_blob(self, ref: UdfBlobReference, destination: Path, *, timeout: timedelta | None = None) -> None:
        ref_pb = self.__to_pb_reference(ref)
        return self.__download_internal(ref_pb, destination, timeout=self.__to_seconds(timeout))

    def download_clob(self, ref: UdfClobReference, destination: Path, *, timeout: timedelta | None = None) -> None:
        ref_pb = self.__to_pb_reference(ref)
        return self.__download_internal(ref_pb, destination, timeout=self.__to_seconds(timeout))

    def upload_blob(self, source: Path, *, timeout: timedelta | None = None) -> UdfBlobReference:
        ref_pb = self.__upload_internal(source, timeout=self.__to_seconds(timeout))
        return self.__from_pb_reference(ref_pb, UdfBlobReference)

    def upload_clob(self, source: Path, *, timeout: timedelta | None = None) -> UdfClobReference:
        ref_pb = self.__upload_internal(source, timeout=self.__to_seconds(timeout))
        return self.__from_pb_reference(ref_pb, UdfClobReference)

__all__ = [
    "StreamBlobRelayClient",
]
