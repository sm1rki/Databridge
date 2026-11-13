"""XML Writer implementation for DataBridge."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Any, Dict, List
from .base import BaseWriter, WriterError


class XMLWriter(BaseWriter):
    """Writer for saving records into XML format."""

    def write(
        self,
        records: List[Dict[str, Any]],
        file_path: str,
        root_tag: str = "records",
        item_tag: str = "record",
        encoding: str = "utf-8",
        **kwargs: Any
    ) -> None:
        self.prepare_directory(file_path)
        cleaned = self.clean_records(records)

        root = ET.Element(root_tag)
        for rec in cleaned:
            item_elem = ET.SubElement(root, item_tag)
            for k, v in rec.items():
                child = ET.SubElement(item_elem, str(k))
                child.text = "" if v is None else str(v)

        try:
            # Generate pretty formatted XML
            rough_string = ET.tostring(root, encoding="utf-8")
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding=encoding)

            with open(file_path, "wb") as f:
                f.write(pretty_xml)
        except Exception as e:
            raise WriterError(f"Ошибка записи в XML файл '{file_path}': {str(e)}", path=file_path, original_error=e)
