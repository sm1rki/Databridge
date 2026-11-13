"""Unit tests for DataBridge file readers."""

import os
import tempfile
import unittest
from databridge.readers.csv_reader import CSVReader
from databridge.readers.json_reader import JSONReader
from databridge.readers.xml_reader import XMLReader
from databridge.readers.factory import get_reader, ReaderError


class TestReaders(unittest.TestCase):
    """Test suite for format readers."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_csv_reader_with_headers(self):
        file_path = os.path.join(self.temp_dir.name, "test.csv")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com\n")

        reader = CSVReader()
        records = reader.read(file_path)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["id"], "1")
        self.assertEqual(records[0]["name"], "Alice")
        self.assertEqual(records[1]["name"], "Bob")
        self.assertEqual(records[0]["_row_number"], 2)

    def test_csv_reader_without_headers(self):
        file_path = os.path.join(self.temp_dir.name, "no_header.csv")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("100,Charlie\n200,Dave\n")

        reader = CSVReader()
        records = reader.read(file_path, has_headers=False)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["col_1"], "100")
        self.assertEqual(records[0]["col_2"], "Charlie")

    def test_csv_custom_delimiter(self):
        file_path = os.path.join(self.temp_dir.name, "semicolon.csv")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("id;name;city\n1;Elena;Moscow\n2;Ivan;Tomsk\n")

        reader = CSVReader()
        records = reader.read(file_path, delimiter=";")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1]["city"], "Tomsk")

    def test_json_reader_array(self):
        file_path = os.path.join(self.temp_dir.name, "test.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('[{"id": 1, "name": "Anna"}, {"id": 2, "name": "Boris"}]')

        reader = JSONReader()
        records = reader.read(file_path)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["id"], 1)
        self.assertEqual(records[1]["name"], "Boris")

    def test_json_reader_nested_wrapper(self):
        file_path = os.path.join(self.temp_dir.name, "nested.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('{"items": [{"id": 1, "name": "Item 1"}]}')

        reader = JSONReader()
        records = reader.read(file_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "Item 1")

    def test_xml_reader_flat(self):
        file_path = os.path.join(self.temp_dir.name, "test.xml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("""<records>
                <record><id>1</id><name>Victor</name></record>
                <record><id>2</id><name>Olga</name></record>
            </records>""")

        reader = XMLReader()
        records = reader.read(file_path)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["name"], "Victor")
        self.assertEqual(records[1]["id"], "2")

    def test_reader_file_not_found(self):
        reader = CSVReader()
        with self.assertRaises(ReaderError):
            reader.read("non_existent_file_12345.csv")

    def test_auto_detect_reader_by_extension(self):
        csv_r = get_reader("data.csv")
        self.assertIsInstance(csv_r, CSVReader)
        json_r = get_reader("data.json")
        self.assertIsInstance(json_r, JSONReader)
        xml_r = get_reader("data.xml")
        self.assertIsInstance(xml_r, XMLReader)


if __name__ == "__main__":
    unittest.main()
