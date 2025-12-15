import grpc
from pathlib import Path
from typing import Optional

from tsurugidb.udf import BlobReference as UdfBlobReference
from tsurugidb.udf import ClobReference as UdfClobReference
from . import blob_relay_local_pb2 as pb_local
from . import blob_relay_local_pb2_grpc as pb_local_grpc
from . import blob_relay_streaming_pb2 as pb_stream
from . import blob_relay_streaming_pb2_grpc as pb_stream_grpc
from . import blob_reference_pb2 as pb_reference
from . import blob_reference_pb2_grpc as pb_reference_grpc


from ..client import BlobRelayClient


def to_pb_reference(ref) -> pb_reference.BlobReference:
    return pb_reference.BlobReference(
        storage_id=ref.storage_id,
        object_id=ref.object_id,
        tag=ref.tag,
        # pb_reference has no provisioned field since relay service does not use it for now
    )


class GrpcBlobRelayClient(BlobRelayClient):

    def __init__(self, context: grpc.ServicerContext):
        """
        X-TSURUGI-BLOB-SESSION            session ID
        X-TSURUGI-BLOB-ENDPOINT          gRPC URI (dns:///...)
        X-TSURUGI-BLOB-SECURE            true/false
        X-TSURUGI-BLOB-TRANSPORT         default stream
        X-TSURUGI-BLOB-STREAM-CHUNK-SIZE default 1048576
        """
        super().__init__()
        self._context = context

        md = {item.key.lower(): item.value for item in context.invocation_metadata()}

        self.session_id: Optional[int] = self._get_int(md, "x-tsurugi-blob-session")
        self.endpoint: Optional[str] = md.get("x-tsurugi-blob-endpoint")
        self.secure: Optional[bool] = self._get_bool(md, "x-tsurugi-blob-secure")
        self.transport: str = (md.get("x-tsurugi-blob-transport") or "stream").lower()
        self.chunk_size: int = (
            self._get_int(md, "x-tsurugi-blob-stream-chunk-size") or 1_048_576
        )

        if not self.endpoint:
            raise ValueError("need X-TSURUGI-BLOB-ENDPOINT")

        if self.secure:
            creds = grpc.ssl_channel_credentials()
            self.channel = grpc.secure_channel(self.endpoint, creds)
        else:
            self.channel = grpc.insecure_channel(self.endpoint)

        if self.transport == "stream":
            self.pb = pb_stream
            self.stub = pb_stream_grpc.BlobRelayStreamingStub(self.channel)
        else:
            self.pb = pb_local
            self.stub = pb_local_grpc.BlobRelayLocalStub(self.channel)

    def _get_int(self, md, key):
        v = md.get(key)
        return int(v) if v and v.isdigit() else None

    def _get_bool(self, md, key):
        v = md.get(key)
        if v is None:
            return None
        return v.lower() == "true"

    def download_common(self, ref, destination: Path):
        ref_pb = to_pb_reference(ref)
        try:
            if self.transport == "stream":
                req = self.pb.GetStreamingRequest(
                    api_version=1,
                    session_id=self.session_id,
                    blob=ref_pb,
                )
                with destination.open("wb") as fp:
                    for resp in self.stub.Get(req):
                        which = resp.WhichOneof("payload")
                        if which == "metadata":
                            pass
                        elif which == "chunk":
                            fp.write(resp.chunk)
            else:
                req = self.pb.GetLocalRequest(
                    api_version=1,
                    session_id=self.session_id,
                    blob=ref_pb,
                )
                response = self.stub.Get(req)
                blob_path = Path(response.data.path)
                destination.write_bytes(blob_path.read_bytes())

        except grpc.RpcError as e:
            raise RuntimeError(f"download failed: {e}") from e
        return destination

    def download_blob(self, ref: UdfBlobReference, destination: Path):
        return self.download_common(ref, destination)

    def download_clob(self, ref: UdfClobReference, destination: Path):
        return self.download_common(ref, destination)

    def upload_common(self, source: Path, return_class):
        try:
            if self.transport == "stream":
                blob_size = source.stat().st_size

                def gen():
                    yield self.pb.PutStreamingRequest(
                        metadata=self.pb.PutStreamingRequest.Metadata(
                            api_version=1,
                            session_id=self.session_id,
                            blob_size=blob_size,
                        )
                    )
                    with source.open("rb") as fp:
                        while True:
                            buf = fp.read(self.chunk_size)
                            if not buf:
                                break
                            yield self.pb.PutStreamingRequest(chunk=buf)

                resp = self.stub.Put(gen())
            else:
                req = self.pb.PutLocalRequest(
                    api_version=1,
                    session_id=self.session_id,
                    data=self.pb.BlobFile(path=str(source)),
                )
                resp = self.stub.Put(req)
            return return_class(
                storage_id=resp.blob.storage_id,
                object_id=resp.blob.object_id,
                tag=resp.blob.tag,
                provisioned=False,  # provisioned field is not relevant for uploaded data to relay service
            )
        except grpc.RpcError as e:
            raise RuntimeError(f"upload failed: {e}") from e

    def upload_blob(self, source: Path) -> UdfBlobReference:
        return self.upload_common(source, UdfBlobReference)

    def upload_clob(self, source: Path) -> UdfClobReference:
        return self.upload_common(source, UdfClobReference)
