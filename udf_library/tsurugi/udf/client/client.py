from abc import ABC, abstractmethod
from pathlib import Path
from tsurugi.udf.model import tsurugi_types_pb2


class BlobRelayClient(ABC):

    def download(self, ref, destination: Path):
        if isinstance(ref, tsurugi_types_pb2.BlobReference):
            return self.download_blob(ref, destination)
        if isinstance(ref, tsurugi_types_pb2.ClobReference):
            return self.download_clob(ref, destination)
        raise TypeError("Unknown reference type")

    def upload(self, source: Path):
        if self._is_binary(source):
            return self.upload_blob(source)
        else:
            return self.upload_clob(source)

    @abstractmethod
    def download_blob(self, ref: tsurugi_types_pb2.BlobReference, destination: Path):
        pass

    @abstractmethod
    def upload_blob(self, source: Path) -> tsurugi_types_pb2.BlobReference:
        pass

    @abstractmethod
    def download_clob(self, ref: tsurugi_types_pb2.ClobReference, destination: Path):
        pass

    @abstractmethod
    def upload_clob(self, source: Path) -> tsurugi_types_pb2.ClobReference:
        pass
