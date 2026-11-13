"""Factory for creating format readers in DataBridge."""

import os
from typing import Optional
from .base import BaseReader, ReaderError
from .csv_reader import CSVReader
from .json_reader import JSONReader
from .xml_reader import XMLReader
from .excel_reader import ExcelReader


EXTENSION_MAP = {
    ".csv": "csv",
    ".tsv": "csv",
    ".txt": "csv",
    ".json": "json",
    ".xml": "xml",
    ".xlsx": "excel",
    ".xls": "excel",
}


def get_reader_for_format(fmt: str) -> BaseReader:
    """Get reader instance by format name."""
    fmt = fmt.lower().strip()
    if fmt in ("csv", "tsv"):
        return CSVReader()
    elif fmt == "json":
        return JSONReader()
    elif fmt == "xml":
        return XMLReader()
    elif fmt in ("excel", "xlsx", "xls"):
        return ExcelReader()
    else:
        raise ReaderError(f"Неподдерживаемый формат данных для чтения: '{fmt}'. Поддерживаются: csv, json, xml, excel.")


def get_reader(file_path: str, format_override: Optional[str] = None) -> BaseReader:
    """
    Get reader based on file extension or explicit format override.
    """
    if format_override:
        return get_reader_for_format(format_override)

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in EXTENSION_MAP:
        raise ReaderError(
            f"Не удалось определить формат файла по расширению '{ext}' для '{file_path}'. "
            f"Используйте поддерживаемые расширения (.csv, .json, .xml, .xlsx) или укажите формат явно."
        )

    return get_reader_for_format(EXTENSION_MAP[ext])
