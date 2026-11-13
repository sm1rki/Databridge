"""CSV Writer implementation for DataBridge."""

import csv
from typing import Any, Dict, List, Optional
from .base import BaseWriter, WriterError


class CSVWriter(BaseWriter):
    """Writer for saving records into CSV format."""

    def write(
        self,
        records: List[Dict[str, Any]],
        file_path: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        include_headers: bool = True,
        fieldnames: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        self.prepare_directory(file_path)
        cleaned = self.clean_records(records)

        # Collect fieldnames in order of appearance
        if not fieldnames:
            ordered_keys: List[str] = []
            for r in cleaned:
                for k in r.keys():
                    if k not in ordered_keys:
                        ordered_keys.append(k)
            fieldnames = ordered_keys

        try:
            with open(file_path, "w", newline="", encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore")
                if include_headers and fieldnames:
                    writer.writeheader()
                for rec in cleaned:
                    writer.writerow(rec)
        except Exception as e:
            raise WriterError(f"Ошибка записи в CSV файл '{file_path}': {str(e)}", path=file_path, original_error=e)
