from abc import ABC, abstractmethod
from pathlib import Path
from tsurugidb.udf import *

class BlobRelayClient(ABC):
    """ A client for BLOB relay service. """
    def download(self, ref, destination: Path):
        """ Download BLOB data identified by `blob_ref` and save it to `destination`.

        Args:
            blob_ref (BlobReference): The reference to the BLOB to download.
            destination (Path): The file path where the downloaded BLOB data will be saved.

        Raises:
            BlobRelayError: If an error occurs in the BLOB relay service.
            BlobRelayError: If there is an error during communication.
            OSError: If there is an error writing to the destination file.
        """
        return self.download_blob(ref, destination)

    def upload(self, source: Path):
        """ Upload BLOB data from `source` and return a reference to the uploaded BLOB.

        Args:
            source (Path): The file path of the BLOB data to upload.

        Returns:
            BlobReference: A reference to the uploaded BLOB.

        Raises:
            OSError: If there is an error reading from the source file.
            BlobRelayError: If there is an error during communication.
            BlobRelayError: If an error occurs in the BLOB relay service.
        """
        return self.upload_blob(source)


    @abstractmethod
    def download_blob(self, ref: tsurugi_types_pb2.BlobReference, destination: Path): pass

    @abstractmethod
    def upload_blob(self, source: Path) -> tsurugi_types_pb2.BlobReference: pass
