"""Excel (.xlsx) Reader implementation for DataBridge."""

from typing import Any, Dict, List, Optional
from datetime import datetime, date
from .base import BaseReader, ReaderError


class ExcelReader(BaseReader):
    """Reader for Excel (.xlsx) files using openpyxl."""

    def read(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        has_headers: bool = True,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        self.validate_file_exists(file_path)

        try:
            import openpyxl
        except ImportError:
            raise ReaderError(
                "Модуль 'openpyxl' не установлен. Для работы с файлами Excel установите его командой: pip install openpyxl",
                path=file_path
            )

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            raise ReaderError(f"Ошибка открытия Excel файла '{file_path}': {str(e)}", path=file_path, original_error=e)

        if sheet_name and sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.active

        if ws is None:
            return []

        rows: List[List[Any]] = []
        for row in ws.iter_rows(values_only=True):
            # Check if row is not completely empty
            if any(cell is not None and str(cell).strip() != "" for cell in row):
                rows.append(list(row))

        if not rows:
            return []

        records: List[Dict[str, Any]] = []

        def serialize_cell(val: Any) -> Any:
            if val is None:
                return ""
            if isinstance(val, (datetime, date)):
                return val.isoformat()
            return val

        if has_headers:
            headers = [str(cell).strip() if cell is not None else f"col_{idx+1}" for idx, cell in enumerate(rows[0])]
            data_rows = rows[1:]
            for row_idx, row in enumerate(data_rows, start=2):
                rec: Dict[str, Any] = {"_row_number": row_idx}
                for i, header in enumerate(headers):
                    val = row[i] if i < len(row) else ""
                    rec[header] = serialize_cell(val)
                records.append(rec)
        else:
            max_cols = max(len(r) for r in rows)
            headers = [f"col_{i+1}" for i in range(max_cols)]
            for row_idx, row in enumerate(rows, start=1):
                rec = {"_row_number": row_idx}
                for i, header in enumerate(headers):
                    val = row[i] if i < len(row) else ""
                    rec[header] = serialize_cell(val)
                records.append(rec)

        return records
