"""JSON Writer implementation for DataBridge."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from .base import BaseWriter, WriterError


class JSONWriter(BaseWriter):
    """Writer for saving records into JSON format."""

    def write(
        self,
        records: List[Dict[str, Any]],
        file_path: str,
        indent: int = 2,
        ensure_ascii: bool = False,
        encoding: str = "utf-8",
        root_key: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        self.prepare_directory(file_path)
        cleaned = self.clean_records(records)

        def json_serial(obj: Any) -> Any:
            """JSON serializer for objects not serializable by default."""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            return str(obj)

        data: Any = cleaned
        if root_key:
            data = {root_key: cleaned}

        try:
            with open(file_path, "w", encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent, default=json_serial)
        except Exception as e:
            raise WriterError(f"Ошибка записи в JSON файл '{file_path}': {str(e)}", path=file_path, original_error=e)
