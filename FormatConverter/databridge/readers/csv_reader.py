"""CSV Reader implementation for DataBridge."""

import csv
import io
from typing import Any, Dict, List, Optional
from .base import BaseReader, ReaderError


class CSVReader(BaseReader):
    """Reader for CSV files supporting custom delimiters, headers, and encodings."""

    def read(
        self,
        file_path: str,
        delimiter: Optional[str] = None,
        has_headers: bool = True,
        encoding: str = "utf-8",
        header_names: Optional[List[str]] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        self.validate_file_exists(file_path)

        # Try specified encoding, fallback to utf-8-sig and cp1251 if UnicodeDecodeError
        content: str = ""
        used_encoding = encoding
        for enc in [encoding, "utf-8-sig", "utf-8", "cp1251", "latin-1"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                used_encoding = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            raise ReaderError(f"Не удалось прочитать файл '{file_path}': несовместимая кодировка.", path=file_path)

        if not content.strip():
            return []

        # Auto-detect delimiter if not specified
        if not delimiter:
            try:
                sample = content[:4096]
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=",;\t|")
                delimiter = dialect.delimiter
            except Exception:
                delimiter = ","

        try:
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            rows = [row for row in reader if row and any(cell.strip() for cell in row)]
        except Exception as e:
            raise ReaderError(f"Ошибка парсинга CSV в файле '{file_path}': {str(e)}", path=file_path, original_error=e)

        if not rows:
            return []

        records: List[Dict[str, Any]] = []

        if has_headers:
            headers = [h.strip() for h in rows[0]]
            # Handle duplicate headers if any
            unique_headers: List[str] = []
            seen_headers: Dict[str, int] = {}
            for h in headers:
                name = h if h else "unnamed"
                if name in seen_headers:
                    seen_headers[name] += 1
                    unique_headers.append(f"{name}_{seen_headers[name]}")
                else:
                    seen_headers[name] = 1
                    unique_headers.append(name)

            data_rows = rows[1:]
            for row_idx, row in enumerate(data_rows, start=2):
                record: Dict[str, Any] = {"_row_number": row_idx}
                for i, header in enumerate(unique_headers):
                    val = row[i] if i < len(row) else ""
                    record[header] = val
                records.append(record)
        else:
            if header_names:
                headers = header_names
            else:
                max_cols = max(len(r) for r in rows)
                headers = [f"col_{i+1}" for i in range(max_cols)]

            for row_idx, row in enumerate(rows, start=1):
                record = {"_row_number": row_idx}
                for i, header in enumerate(headers):
                    val = row[i] if i < len(row) else ""
                    record[header] = val
                records.append(record)

        return records
