"""Unit tests for Excel reader and writer."""

import os
import tempfile
import unittest
from databridge.writers.excel_writer import ExcelWriter
from databridge.readers.excel_reader import ExcelReader


class TestExcel(unittest.TestCase):
    """Test suite for Excel I/O."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.records = [
            {"id": 1, "name": "Иван", "email": "ivan@mail.ru", "score": 95.5},
            {"id": 2, "name": "Мария", "email": "maria@mail.ru", "score": 88.0},
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_excel_write_and_read(self):
        file_path = os.path.join(self.temp_dir.name, "test.xlsx")
        writer = ExcelWriter()
        writer.write(self.records, file_path, sheet_name="Students")

        self.assertTrue(os.path.exists(file_path))

        reader = ExcelReader()
        read_records = reader.read(file_path, sheet_name="Students")
        self.assertEqual(len(read_records), 2)
        self.assertEqual(read_records[0]["name"], "Иван")
        self.assertEqual(read_records[1]["name"], "Мария")
        self.assertEqual(read_records[0]["id"], 1)


if __name__ == "__main__":
    unittest.main()
