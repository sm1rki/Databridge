"""Unit tests for DataBridge field transformers and mapper."""

import unittest
from databridge.converters.transformers import (
    apply_transformation,
    transform_upper,
    transform_lower,
    transform_strip,
    transform_capitalize,
    transform_replace_map,
    transform_timestamp_to_date,
    transform_format_date,
    transform_default,
)
from databridge.converters.mapper import FieldMapper


class TestTransformers(unittest.TestCase):
    """Test suite for transformations."""

    def test_upper_lower_strip_capitalize(self):
        self.assertEqual(transform_upper("hello"), "HELLO")
        self.assertEqual(transform_lower("WORLD"), "world")
        self.assertEqual(transform_strip("  spaces  "), "spaces")
        self.assertEqual(transform_capitalize("moscow"), "Moscow")

    def test_replace_map(self):
        mapping = {"M": "Male", "F": "Female"}
        self.assertEqual(transform_replace_map("M", mapping=mapping), "Male")
        self.assertEqual(transform_replace_map("f", mapping=mapping), "Female")
        self.assertEqual(transform_replace_map("X", mapping=mapping, default="Unknown"), "Unknown")

    def test_timestamp_to_date(self):
        # 1577836800 is 2020-01-01 00:00:00 UTC
        res = transform_timestamp_to_date(1577836800, output_format="YYYY-MM-DD")
        self.assertEqual(res, "2020-01-01")

    def test_format_date(self):
        res = transform_format_date("15.01.1999", input_format="DD.MM.YYYY", output_format="YYYY-MM-DD")
        self.assertEqual(res, "1999-01-15")

    def test_default_value(self):
        self.assertEqual(transform_default(None, default_value="N/A"), "N/A")
        self.assertEqual(transform_default("", default_value="Standard"), "Standard")
        self.assertEqual(transform_default("Present", default_value="N/A"), "Present")

    def test_apply_transformation_helper(self):
        self.assertEqual(apply_transformation("upper", "test"), "TEST")
        self.assertEqual(apply_transformation("strip", "  abc  "), "abc")


class TestFieldMapper(unittest.TestCase):
    """Test suite for field mapping."""

    def test_mapping_renames_keys(self):
        mapper = FieldMapper(mapping={"old_id": "id", "user_mail": "email"})
        rec = {"old_id": "1", "user_mail": "test@mail.ru", "age": 25}
        mapped = mapper.map_record(rec)

        self.assertEqual(mapped["id"], "1")
        self.assertEqual(mapped["email"], "test@mail.ru")
        self.assertEqual(mapped["age"], 25)
        self.assertNotIn("old_id", mapped)


if __name__ == "__main__":
    unittest.main()
