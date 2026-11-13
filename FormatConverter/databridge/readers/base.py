"""Base reader interface for DataBridge."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import os


class ReaderError(Exception):
    """Exception raised when an error occurs during reading or parsing a data source."""
    def __init__(self, message: str, path: Optional[str] = None, original_error: Optional[Exception] = None):
        self.path = path
        self.original_error = original_error
        super().__init__(message)


class BaseReader(ABC):
    """Abstract base class for all file readers."""

    @abstractmethod
    def read(self, file_path: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Read records from a file.

        Args:
            file_path: Path to the input file.
            **kwargs: Format-specific options (e.g., delimiter, encoding, sheet_name).

        Returns:
            A list of dictionary records where keys are column/field names.

        Raises:
            ReaderError: If the file cannot be found, opened, or parsed.
        """
        pass

    def validate_file_exists(self, file_path: str) -> None:
        """Validate that the file exists and is readable."""
        if not os.path.exists(file_path):
            raise ReaderError(f"Файл не найден: '{file_path}'", path=file_path)
        if os.path.isdir(file_path):
            raise ReaderError(f"Указанный путь является директорией, а не файлом: '{file_path}'", path=file_path)
        if not os.access(file_path, os.R_OK):
            raise ReaderError(f"Нет прав на чтение файла: '{file_path}'", path=file_path)
