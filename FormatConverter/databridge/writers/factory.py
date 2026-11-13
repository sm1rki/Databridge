"""Factory for creating format writers in DataBridge."""

import os
from typing import Optional
from .base import BaseWriter, WriterError
from .csv_writer import CSVWriter
from .json_writer import JSONWriter
from .xml_writer import XMLWriter
from .excel_writer import ExcelWriter


EXTENSION_MAP = {
    ".csv": "csv",
    ".tsv": "csv",
    ".json": "json",
    ".xml": "xml",
    ".xlsx": "excel",
    ".xls": "excel",
}


def get_writer_for_format(fmt: str) -> BaseWriter:
    """Get writer instance by format name."""
    fmt = fmt.lower().strip()
    if fmt in ("csv", "tsv"):
        return CSVWriter()
    elif fmt == "json":
        return JSONWriter()
    elif fmt == "xml":
        return XMLWriter()
    elif fmt in ("excel", "xlsx", "xls"):
        return ExcelWriter()
    else:
        raise WriterError(f"Неподдерживаемый формат данных для записи: '{fmt}'. Поддерживаются: csv, json, xml, excel.")


def get_writer(file_path: str, format_override: Optional[str] = None) -> BaseWriter:
    """
    Get writer based on file extension or explicit format override.
    """
    if format_override:
        return get_writer_for_format(format_override)

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in EXTENSION_MAP:
        raise WriterError(
            f"Не удалось определить формат для сохранения по расширению '{ext}' файла '{file_path}'. "
            f"Используйте поддерживаемые расширения (.csv, .json, .xml, .xlsx) или укажите формат параметром --to."
        )

    return get_writer_for_format(EXTENSION_MAP[ext])
