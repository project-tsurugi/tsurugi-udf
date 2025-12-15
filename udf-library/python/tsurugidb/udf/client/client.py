from abc import ABC, abstractmethod
from pathlib import Path
from tsurugidb.udf import *


class BlobRelayClient(ABC):
    """A client for BLOB relay service."""

    @abstractmethod
    def download_blob(self, ref: BlobReference, destination: Path):
        """Download BLOB data identified by `blob_ref` and save it to `destination`.

        Args:
            blob_ref (BlobReference): The reference to the BLOB to download.
            destination (Path): The file path where the downloaded BLOB data will be saved.

        Raises:
            BlobRelayError: If an error occurs in the BLOB relay service.
            BlobRelayError: If there is an error during communication.
            OSError: If there is an error writing to the destination file.
        """
        pass

    @abstractmethod
    def download_clob(self, ref: ClobReference, destination: Path):
        """Download CLOB data identified by `blob_ref` and save it to `destination`.

        Args:
            clob_ref (ClobReference): The reference to the BLOB to download.
            destination (Path): The file path where the downloaded BLOB data will be saved.

        Raises:
            BlobRelayError: If an error occurs in the BLOB relay service.
            BlobRelayError: If there is an error during communication.
            OSError: If there is an error writing to the destination file.
        """
        pass

    @abstractmethod
    def upload_blob(self, source: Path) -> BlobReference:
        """Upload BLOB data from `source` and return a reference to the uploaded BLOB.

        Args:
            source (Path): The file path of the BLOB data to upload.

        Returns:
            BlobReference: A reference to the uploaded BLOB.

        Raises:
            OSError: If there is an error reading from the source file.
            BlobRelayError: If there is an error during communication.
            BlobRelayError: If an error occurs in the BLOB relay service.
        """
        pass

    @abstractmethod
    def upload_clob(self, source: Path) -> ClobReference:
        """Upload CLOB data from `source` and return a reference to the uploaded CLOB.

        Args:
            source (Path): The file path of the CLOB data to upload.

        Returns:
            ClobReference: A reference to the uploaded CLOB.

        Raises:
            OSError: If there is an error reading from the source file.
            BlobRelayError: If there is an error during communication.
            BlobRelayError: If an error occurs in the BLOB relay service.
        """
        pass


__all__ = [
    "BlobRelayClient",
]
