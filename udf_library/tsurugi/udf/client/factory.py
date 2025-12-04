from .grpc.grpc_client import GrpcBlobRelayClient


def create_blob_client(context):
    return GrpcBlobRelayClient(context)
