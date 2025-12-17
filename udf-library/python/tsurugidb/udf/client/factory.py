from .client import BlobRelayClient
from .grpc._constants import KEY_TRANSPORT

import grpc
import importlib
import logging
import re

from typing import ContextManager

PATTERN_TRANSPORT = re.compile(r"[a-z][a-z0-9_]*")

PLUGIN_PACKAGE_PREFIX = "tsurugidb.udf.client."

PLUGIN_ENTRY_POINT = "create_blob_client"

DEFAULT_TRANSPORT = "stream"

LOGGER_NAME = 'tsurugidb.udf.blob.factory'

logger = logging.getLogger(LOGGER_NAME)

def create_blob_client(context: grpc.ServicerContext) -> ContextManager[BlobRelayClient]:
    """Create a StreamBlobRelayClient from the given gRPC context.

    Args:
        context: The gRPC ServicerContext to parse metadata from.

    Returns:
        A context manager that yields a BlobRelayClient.

    Raises:
        ValueError: If the transport plugin is invalid or unsupported.

    Metadata keys:
        X-TSURUGI-BLOB-TRANSPORT       transport plugin name, default "stream" (string)
        X-TSURUGI-BLOB-SESSION         session ID (integer)
        X-TSURUGI-BLOB-ENDPOINT        gRPC URI (dns:///...)
        X-TSURUGI-BLOB-SECURE          whether to use a secure channel (boolean)
        X-TSURUGI-BLOB-<*>             additional keys for each transport plugin

    Note:
        This function dynamically loads a transport plugin based on the
        'X-TSURUGI-BLOB-TRANSPORT' metadata value.
        This searches for a module named "tsurugidb.udf.client.<transport>".
        The plugin module must define a 'create_blob_client' function that takes a
        gRPC context (grpc.ServicerContext) and returns a context manager yielding a BlobRelayClient.
    """
    metadata = {key.lower(): value for key, value in context.invocation_metadata()}
    transport = metadata.get(KEY_TRANSPORT, DEFAULT_TRANSPORT)
    if not PATTERN_TRANSPORT.match(transport):
        raise ValueError(f"invalid {KEY_TRANSPORT.upper()}={transport}")

    plugin_path = PLUGIN_PACKAGE_PREFIX + transport
    try:
        logger.debug("start loading BLOB relay transport module: %s", plugin_path)
        plugin = importlib.import_module(plugin_path)
        logger.debug("finish loading BLOB relay transport module: %s", plugin_path)
    except ImportError as e:
        raise ValueError(f"unsupported BLOB relay transport: {transport}") from e
    if not hasattr(plugin, PLUGIN_ENTRY_POINT):
        raise ValueError(f"""BLOB relay transport plugin "{transport}" must have entry-point ({plugin_path}.{PLUGIN_ENTRY_POINT}) """)
    return getattr(plugin, PLUGIN_ENTRY_POINT)(context)

__all__ = [
    "create_blob_client",
]
