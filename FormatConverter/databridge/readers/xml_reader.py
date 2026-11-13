"""XML Reader implementation for DataBridge."""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from .base import BaseReader, ReaderError


class XMLReader(BaseReader):
    """Reader for flat XML files containing collections of records."""

    def read(
        self,
        file_path: str,
        record_tag: Optional[str] = None,
        encoding: str = "utf-8",
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        self.validate_file_exists(file_path)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ReaderError(
                f"Ошибка парсинга XML в файле '{file_path}': {str(e)}",
                path=file_path,
                original_error=e
            )
        except Exception as e:
            raise ReaderError(
                f"Не удалось открыть XML файл '{file_path}': {str(e)}",
                path=file_path,
                original_error=e
            )

        # Detect record elements:
        # If record_tag specified, use it. Otherwise, inspect children of root.
        if record_tag:
            elements = root.findall(f".//{record_tag}")
        else:
            # Common pattern: <root><item>...</item><item>...</item></root>
            elements = list(root)
            if not elements and len(root.attrib) > 0:
                # The root itself might be a single record
                elements = [root]

        records: List[Dict[str, Any]] = []
        for idx, elem in enumerate(elements, start=1):
            rec: Dict[str, Any] = {"_row_number": idx}
            
            # Read attributes first if present
            for attr_name, attr_val in elem.attrib.items():
                rec[attr_name] = attr_val

            # Read child tag values
            for child in elem:
                tag = child.tag
                val = child.text if child.text is not None else ""
                rec[tag] = val.strip()

            # If element has no children but has text
            if len(elem) == 0 and not elem.attrib and elem.text:
                rec["value"] = elem.text.strip()

            records.append(rec)

        return records
