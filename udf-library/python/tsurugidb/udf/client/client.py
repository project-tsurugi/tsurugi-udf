from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path
from tsurugidb.udf import BlobReference, ClobReference


class BlobRelayError(RuntimeError):
    """Error raised by BlobRelayClient implementations."""

class BlobRelayTimeoutError(BlobRelayError):
    """Error raised when a BlobRelayClient operation times out."""

class BlobRelayClient(ABC):
    """A client for BLOB relay service."""

    @abstractmethod
    def download_blob(self, ref: BlobReference, destination: Path, *, timeout: timedelta | None = None) -> None:
        """Download BLOB data identified by `ref` and save it to `destination`.

        Args:
            ref: The reference to the BLOB to download.
            destination: The file path where the downloaded BLOB data will be saved.
            timeout: timeout duration for the operation, or None for no timeout.

        Raises:
            BlobRelayError: If an error occurs in the BLOB relay service.
            BlobRelayError: If there is an error during communication.
            BlobRelayTimeoutError: If the operation times out.
            OSError: If there is an error writing to the destination file.
        """
        pass

    @abstractmethod
    def download_clob(self, ref: ClobReference, destination: Path, *, timeout: timedelta | None = None) -> None:
        """Download CLOB data identified by `ref` and save it to `destination`.

        Args:
            ref: The reference to the CLOB to download.
            destination: The file path where the downloaded CLOB data will be saved.
            timeout: timeout duration for the operation, or None for no timeout.

        Raises:
            BlobRelayError: If an error occurs in the BLOB relay service.
            BlobRelayError: If there is an error during communication.
            BlobRelayTimeoutError: If the operation times out.
            OSError: If there is an error writing to the destination file.
        """
        pass

    @abstractmethod
    def upload_blob(self, source: Path, *, timeout: timedelta | None = None) -> BlobReference:
        """Upload BLOB data from `source` and return a reference to the uploaded BLOB.

        Args:
            source: The file path of the BLOB data to upload.
            timeout: timeout duration for the operation, or None for no timeout.

        Returns:
            A reference to the uploaded BLOB.

        Raises:
            OSError: If there is an error reading from the source file.
            BlobRelayError: If there is an error during communication.
            BlobRelayError: If an error occurs in the BLOB relay service.
            BlobRelayTimeoutError: If the operation times out.
        """
        pass

    @abstractmethod
    def upload_clob(self, source: Path, *, timeout: timedelta | None = None) -> ClobReference:
        """Upload CLOB data from `source` and return a reference to the uploaded CLOB.

        Args:
            source: The file path of the CLOB data to upload.
            timeout: timeout duration for the operation, or None for no timeout.

        Returns:
            A reference to the uploaded CLOB.

        Raises:
            OSError: If there is an error reading from the source file.
            BlobRelayError: If there is an error during communication.
            BlobRelayError: If an error occurs in the BLOB relay service.
            BlobRelayTimeoutError: If the operation times out.
        """
        pass


__all__ = [
    "BlobRelayError",
    "BlobRelayTimeoutError",
    "BlobRelayClient",
]
