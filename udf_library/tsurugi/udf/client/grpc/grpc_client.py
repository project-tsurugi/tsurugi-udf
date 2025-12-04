import grpc
from pathlib import Path
from ..client import BlobRelayClient
from tsurugi.udf.model import tsurugi_types_pb2


class GrpcBlobRelayClient(BlobRelayClient):

    def __init__(self, context: grpc.ServicerContext):
        self._context = context
        # self._session_id = context.invocation_metadata() ...

    def download_blob(self, ref: tsurugi_types_pb2.BlobReference, destination: Path):
        raise NotImplementedError()

    def upload_blob(self, source: Path) -> tsurugi_types_pb2.BlobReference:
        raise NotImplementedError()