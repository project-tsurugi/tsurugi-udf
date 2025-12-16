from .client import BlobRelayClient
from .grpc._constants import KEY_TRANSPORT

import grpc
import importlib
import re

from typing import ContextManager

"""
from tsurugi.udf.client import create_blob_client
from tsurugi.udf.model import tsurugi_types_pb2
from pathlib import Path

def run_udf(context):
    client = create_blob_client(context)
    blob_ref = tsurugi_types_pb2.BlobReference()
    blob_ref.storage_id = 1
    blob_ref.object_id = 42
    blob_ref.tag = 0
    dst = Path("/tmp/out.bin")
    client.download(blob_ref, dst)

    # Upload
    src = Path("/tmp/in.bin")
    new_ref = client.upload(src)

    print("download ->", dst)
    print("upload ref ->", new_ref)

    src = Path("/tmp/in.bin")
    new_ref = client.upload(src)

"""

PATTERN_TRANSPORT = re.compile(r"[a-z][a-z0-9_]*")

PLUGIN_PACKAGE_PREFIX = "tsurugidb.udf.client."

PLUGIN_ENTRY_POINT = "create_blob_client"

DEFAULT_TRANSPORT = "stream"

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

    try:
        plugin = importlib.import_module(PLUGIN_PACKAGE_PREFIX + transport)
    except ImportError as e:
        raise ValueError(f"unsupported BLOB relay transport: {transport}") from e
    if not hasattr(plugin, PLUGIN_ENTRY_POINT):
        raise ValueError(f"""BLOB relay transport plugin "{transport}" must have entry-point ({PLUGIN_PACKAGE_PREFIX + transport}.{PLUGIN_ENTRY_POINT}) """)
    return getattr(plugin, PLUGIN_ENTRY_POINT)(context)

__all__ = [
    "create_blob_client",
]
