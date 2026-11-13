"""Unit tests for DataBridge validation rules and engine."""

import unittest
from databridge.validators.models import FieldRule, ValidationConfig
from databridge.validators.engine import ValidationEngine
from databridge.validators.rules import (
    validate_type,
    validate_range,
    validate_pattern,
    validate_length,
)


class TestValidators(unittest.TestCase):
    """Test suite for individual validation rules."""

    def test_type_integer_valid(self):
        ok, msg = validate_type("123", "integer")
        self.assertTrue(ok)
        self.assertIsNone(msg)

        ok, msg = validate_type(456, "integer")
        self.assertTrue(ok)
        self.assertIsNone(msg)

    def test_type_integer_invalid(self):
        ok, msg = validate_type("abc", "integer")
        self.assertFalse(ok)
        self.assertIn("не является целым числом", msg)

        ok, msg = validate_type("12.34", "integer")
        self.assertFalse(ok)

    def test_type_float_valid_and_invalid(self):
        ok, _ = validate_type("3.1415", "float")
        self.assertTrue(ok)
        ok, _ = validate_type("3,14", "float")
        self.assertTrue(ok)
        ok, _ = validate_type("not-a-float", "float")
        self.assertFalse(ok)

    def test_type_boolean(self):
        self.assertTrue(validate_type("true", "boolean")[0])
        self.assertTrue(validate_type("1", "boolean")[0])
        self.assertTrue(validate_type("да", "boolean")[0])
        self.assertFalse(validate_type("maybe", "boolean")[0])

    def test_type_date(self):
        self.assertTrue(validate_type("1999-01-15", "date", "YYYY-MM-DD")[0])
        self.assertTrue(validate_type("15.01.1999", "date", "DD.MM.YYYY")[0])
        self.assertFalse(validate_type("invalid-date", "date", "YYYY-MM-DD")[0])

    def test_range_numeric(self):
        self.assertTrue(validate_range(25, min_val=16, max_val=100)[0])
        self.assertFalse(validate_range(15, min_val=16, max_val=100)[0])
        self.assertFalse(validate_range(200, min_val=16, max_val=100)[0])

    def test_pattern_regex(self):
        email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
        self.assertTrue(validate_pattern("ivan@mail.ru", email_pattern)[0])
        self.assertFalse(validate_pattern("ivan.mail.ru", email_pattern)[0])
        self.assertFalse(validate_pattern("ivan@@mail.ru", email_pattern)[0])

    def test_length_min_max(self):
        self.assertTrue(validate_length("hello", min_length=2, max_length=10)[0])
        self.assertFalse(validate_length("a", min_length=2, max_length=10)[0])
        self.assertFalse(validate_length("this is too long string", min_length=2, max_length=10)[0])


class TestValidationEngine(unittest.TestCase):
    """Test suite for full validation engine against record batches."""

    def setUp(self):
        self.config = ValidationConfig(
            fields=[
                FieldRule(name="id", type="integer", required=True, unique=True),
                FieldRule(name="email", type="string", required=True, pattern=r"^[^@]+@[^@]+\.[^@]+$"),
                FieldRule(name="age", type="integer", min=16, max=100),
                FieldRule(name="name", type="string", required=True, min_length=2),
            ]
        )
        self.engine = ValidationEngine(self.config)

    def test_all_valid_records(self):
        records = [
            {"_row_number": 1, "id": "1", "name": "Иван", "email": "ivan@mail.ru", "age": "25"},
            {"_row_number": 2, "id": "2", "name": "Мария", "email": "maria@mail.ru", "age": "30"},
        ]
        res = self.engine.validate(records)
        self.assertEqual(res.total_count, 2)
        self.assertEqual(res.valid_count, 2)
        self.assertEqual(res.error_count, 0)
        self.assertTrue(res.is_success)

    def test_required_field_missing(self):
        records = [
            {"_row_number": 1, "id": "1", "name": "", "email": "ivan@mail.ru", "age": "25"},
        ]
        res = self.engine.validate(records)
        self.assertEqual(res.error_count, 1)
        self.assertEqual(res.errors[0].field, "name")
        self.assertEqual(res.errors[0].rule, "required")

    def test_unique_constraint(self):
        records = [
            {"_row_number": 1, "id": "1", "name": "Иван", "email": "ivan@mail.ru"},
            {"_row_number": 2, "id": "1", "name": "Пётр", "email": "petr@mail.ru"},
        ]
        res = self.engine.validate(records)
        self.assertEqual(res.valid_count, 1)
        self.assertEqual(res.error_count, 1)
        self.assertEqual(res.errors[0].rule, "unique")
        self.assertEqual(res.errors[0].row_number, 2)

    def test_multiple_errors_in_single_record(self):
        records = [
            {"_row_number": 1, "id": "not-an-id", "name": "A", "email": "bad-email", "age": "500"},
        ]
        res = self.engine.validate(records)
        self.assertEqual(res.error_count, 1)
        self.assertGreaterEqual(len(res.errors), 3)


if __name__ == "__main__":
    unittest.main()
