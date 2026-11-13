"""Base writer interface for DataBridge."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import os


class WriterError(Exception):
    """Exception raised when an error occurs during writing data to file."""
    def __init__(self, message: str, path: Optional[str] = None, original_error: Optional[Exception] = None):
        self.path = path
        self.original_error = original_error
        super().__init__(message)


class BaseWriter(ABC):
    """Abstract base class for all file writers."""

    @abstractmethod
    def write(self, records: List[Dict[str, Any]], file_path: str, **kwargs: Any) -> None:
        """
        Write records to destination file.

        Args:
            records: List of dictionary records to write.
            file_path: Destination path.
            **kwargs: Format-specific writer options.
        """
        pass

    def prepare_directory(self, file_path: str) -> None:
        """Ensure the destination directory exists."""
        dirname = os.path.dirname(file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    def clean_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove internal metadata fields (such as `_row_number`) before writing."""
        cleaned = []
        for r in records:
            cleaned.append({k: v for k, v in r.items() if not k.startswith("_")})
        return cleaned
