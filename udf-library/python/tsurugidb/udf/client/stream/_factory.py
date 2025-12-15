from ._stream_blob_relay_client import StreamBlobRelayClient
from ..grpc import blob_relay_streaming_pb2_grpc as pb_service
from ..grpc._constants import (
    KEY_PREFIX,
    KEY_SESSION,
    KEY_ENDPOINT,
    KEY_SECURE,
    DEFAULT_SECURE,
)

from contextlib import contextmanager
from datetime import timedelta
from typing import Iterator, ContextManager

import grpc

KEY_STREAM_CHUNK_SIZE = KEY_PREFIX + "stream-chunk-size"

DEFAULT_STREAM_CHUNK_SIZE = 1_048_576

class ClientConfig:
    """Represents a configuration for StreamBlobRelayClient."""

    def __init__(
            self,
            session_id: int,
            endpoint: str,
            *,
            secure: bool = DEFAULT_SECURE,
            chunk_size: int = DEFAULT_STREAM_CHUNK_SIZE):
        """Creates a new instance.

        Args:
            session_id: The session ID for the BLOB relay service.
            endpoint: The gRPC endpoint URI for the BLOB relay service.
            secure: Whether to use a secure gRPC channel.
            chunk_size: The size of each chunk to use when streaming data. Default is 1,048,576 bytes (1 MB).
        """
        self.session_id = session_id
        self.endpoint = endpoint
        self.secure = secure
        self.chunk_size = chunk_size

    @classmethod
    def parse(cls, context: grpc.ServicerContext) -> "ClientConfig":
        """Parses the configuration from the given gRPC context.

        Args:
            context: The gRPC ServicerContext to parse metadata from.

        Returns:
            A ClientConfig instance.

        Raises:
            ValueError: If required metadata is missing or invalid.

        Metadata keys:
            X-TSURUGI-BLOB-SESSION           session ID (integer)
            X-TSURUGI-BLOB-ENDPOINT          gRPC URI (dns:///...)
            X-TSURUGI-BLOB-SECURE            whether to use a secure channel (boolean)
            X-TSURUGI-BLOB-STREAM-CHUNK-SIZE chunk size for uploading BLOB data, default 1048576 (integer)
            X-TSURUGI-BLOB-STREAM-DEADLINE   optional deadline in seconds (integer)
        """

        md = {key.lower(): value for key, value in context.invocation_metadata()}

        session_id_str = md.get(KEY_SESSION)
        endpoint = md.get(KEY_ENDPOINT)
        secure_str = md.get(KEY_SECURE)
        chunk_size_str = md.get(KEY_STREAM_CHUNK_SIZE)

        if not session_id_str or not session_id_str.isdigit():
            raise ValueError(f"missing or invalid {KEY_SESSION.upper()}")
        session_id = int(session_id_str)

        if not endpoint:
            raise ValueError(f"missing {KEY_ENDPOINT.upper()}")

        if secure_str:
            if secure_str.lower() not in ("true", "false"):
                raise ValueError(f"invalid {KEY_SECURE.upper()}={secure_str}: must be 'true' or 'false'")
            secure = secure_str.lower() == "true"
        else:
            secure = DEFAULT_SECURE

        if chunk_size_str:
            if not chunk_size_str.isdigit():
                raise ValueError(f"invalid {KEY_STREAM_CHUNK_SIZE.upper()}={chunk_size_str}: must be an integer")
            chunk_size = int(chunk_size_str)
        else:
            chunk_size = DEFAULT_STREAM_CHUNK_SIZE

        return ClientConfig(
            session_id=session_id,
            endpoint=endpoint,
            secure=secure,
            chunk_size=chunk_size,
        )

def create_blob_client(context: grpc.ServicerContext) -> ContextManager[StreamBlobRelayClient]:
    """Create a StreamBlobRelayClient from the given gRPC context.

    Args:
        context: The gRPC ServicerContext to parse metadata from.
    Returns:
        A context manager that yields a StreamBlobRelayClient.
    """
    config = ClientConfig.parse(context) # if error occurs, channel creation is not done
    return create_blob_client_from_config(config)

@contextmanager
def create_blob_client_from_config(config: ClientConfig) -> Iterator[StreamBlobRelayClient]:
    """Create a StreamBlobRelayClient from the given ClientConfig.

    Args:
        config: The ClientConfig to use for creating the client.
    Returns:
        A context manager that yields a StreamBlobRelayClient.
    """
    if config.secure:
        credentials = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel(config.endpoint, credentials)
    else:
        channel = grpc.insecure_channel(config.endpoint)
    try:
        stub = pb_service.BlobRelayStreamingStub(channel)
        client = StreamBlobRelayClient(
            stub,
            config.session_id,
            chunk_size=config.chunk_size,
            deadline=config.deadline,
        )
        yield client
    finally:
        channel.close()

__all__ = [
    "ClientConfig",
    "create_blob_client",
    "create_blob_client_from_config",
]
