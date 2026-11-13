"""Unit tests for DataBridge file writers."""

import os
import tempfile
import unittest
from databridge.writers.csv_writer import CSVWriter
from databridge.writers.json_writer import JSONWriter
from databridge.writers.xml_writer import XMLWriter
from databridge.readers.csv_reader import CSVReader
from databridge.readers.json_reader import JSONReader
from databridge.readers.xml_reader import XMLReader


class TestWriters(unittest.TestCase):
    """Test suite for format writers."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.records = [
            {"id": "1", "name": "Иван", "email": "ivan@mail.ru", "_row_number": 1},
            {"id": "2", "name": "Мария", "email": "maria@mail.ru", "_row_number": 2},
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_csv_writer(self):
        out_path = os.path.join(self.temp_dir.name, "out.csv")
        writer = CSVWriter()
        writer.write(self.records, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            header_line = f.readline()
        self.assertNotIn("_row_number", header_line)

        reader = CSVReader()
        read_back = reader.read(out_path)
        self.assertEqual(len(read_back), 2)
        self.assertEqual(read_back[0]["name"], "Иван")

    def test_json_writer(self):
        out_path = os.path.join(self.temp_dir.name, "out.json")
        writer = JSONWriter()
        writer.write(self.records, out_path)

        reader = JSONReader()
        read_back = reader.read(out_path)
        self.assertEqual(len(read_back), 2)
        self.assertEqual(read_back[1]["name"], "Мария")

    def test_xml_writer(self):
        out_path = os.path.join(self.temp_dir.name, "out.xml")
        writer = XMLWriter()
        writer.write(self.records, out_path)

        reader = XMLReader()
        read_back = reader.read(out_path)
        self.assertEqual(len(read_back), 2)
        self.assertEqual(read_back[0]["id"], "1")
        self.assertEqual(read_back[0]["name"], "Иван")


if __name__ == "__main__":
    unittest.main()
