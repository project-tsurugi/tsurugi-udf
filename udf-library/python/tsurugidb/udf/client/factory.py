from .grpc.grpc_client import GrpcBlobRelayClient
from .grpc._constants import KEY_TRANSPORT

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


def create_blob_client(context):
    return GrpcBlobRelayClient(context)
