"""Excel (.xlsx) Writer implementation for DataBridge."""

from typing import Any, Dict, List, Optional
from datetime import datetime, date
from .base import BaseWriter, WriterError


class ExcelWriter(BaseWriter):
    """Writer for saving records into Excel (.xlsx) format."""

    def write(
        self,
        records: List[Dict[str, Any]],
        file_path: str,
        sheet_name: str = "Sheet1",
        fieldnames: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        self.prepare_directory(file_path)
        cleaned = self.clean_records(records)

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            raise WriterError(
                "Модуль 'openpyxl' не установлен. Для записи в Excel установите его командой: pip install openpyxl",
                path=file_path
            )

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name

            if not fieldnames:
                ordered_keys: List[str] = []
                for r in cleaned:
                    for k in r.keys():
                        if k not in ordered_keys:
                            ordered_keys.append(k)
                fieldnames = ordered_keys

            # Write header
            if fieldnames:
                header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
                header_align = Alignment(horizontal="center", vertical="center")

                ws.append(fieldnames)
                for col_idx in range(1, len(fieldnames) + 1):
                    cell = ws.cell(row=1, column=col_idx)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_align

                # Write data
                for rec in cleaned:
                    row_vals = []
                    for f in fieldnames:
                        v = rec.get(f, "")
                        if isinstance(v, (date, datetime)):
                            v = v.isoformat()
                        row_vals.append(v)
                    ws.append(row_vals)

                # Adjust column widths nicely
                for col in ws.columns:
                    col_letter = col[0].column_letter
                    max_len = 0
                    for cell in col:
                        val_str = str(cell.value or "")
                        if len(val_str) > max_len:
                            max_len = len(val_str)
                    ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

            wb.save(file_path)
        except Exception as e:
            raise WriterError(f"Ошибка записи в Excel файл '{file_path}': {str(e)}", path=file_path, original_error=e)
