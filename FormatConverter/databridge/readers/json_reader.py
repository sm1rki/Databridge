"""JSON Reader implementation for DataBridge."""

import json
from typing import Any, Dict, List, Optional
from .base import BaseReader, ReaderError


class JSONReader(BaseReader):
    """Reader for JSON files, supporting arrays of objects or nested list wrappers."""

    def read(self, file_path: str, encoding: str = "utf-8", root_key: Optional[str] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        self.validate_file_exists(file_path)

        content: str = ""
        for enc in [encoding, "utf-8-sig", "utf-8", "cp1251"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            raise ReaderError(f"Не удалось прочитать файл '{file_path}': несовместимая кодировка.", path=file_path)

        if not content.strip():
            return []

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ReaderError(
                f"Синтаксическая ошибка в JSON файле '{file_path}' (строка {e.lineno}, колонка {e.colno}): {e.msg}",
                path=file_path,
                original_error=e,
            )

        if root_key and isinstance(data, dict) and root_key in data:
            data = data[root_key]
        elif isinstance(data, dict):
            # If the dict contains a single list value (e.g. {"items": [...]}, {"records": [...]}, {"data": [...]})
            list_keys = [k for k, v in data.items() if isinstance(v, list)]
            if len(list_keys) == 1:
                data = data[list_keys[0]]
            else:
                # Single record object wrapped as a one-element list
                data = [data]

        if not isinstance(data, list):
            raise ReaderError(
                f"Ожидался массив объектов (JSON list), но получен тип '{type(data).__name__}' в файле '{file_path}'.",
                path=file_path,
            )

        records: List[Dict[str, Any]] = []
        for idx, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise ReaderError(
                    f"Элемент #{idx} в JSON файле '{file_path}' не является объектом (dict), получен {type(item).__name__}.",
                    path=file_path,
                )
            rec = dict(item)
            rec["_row_number"] = idx
            records.append(rec)

        return records
