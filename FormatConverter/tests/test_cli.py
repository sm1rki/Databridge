"""Integration tests for DataBridge CLI."""

import os
import tempfile
import unittest
from databridge.cli.main import main


class TestCLI(unittest.TestCase):
    """Test suite for CLI commands."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.input_csv = os.path.join(self.temp_dir.name, "cli_input.csv")
        with open(self.input_csv, "w", encoding="utf-8") as f:
            f.write(
                "id,name,email,age,birth_date\n"
                "1,Иван,ivan@mail.ru,25,1999-01-15\n"
                "2,Мария,maria.mail.ru,30,1994-05-20\n"
            )

        self.config_json = os.path.join(self.temp_dir.name, "schema.json")
        with open(self.config_json, "w", encoding="utf-8") as f:
            f.write("""{
                "fields": [
                    {"name": "id", "type": "integer", "required": true},
                    {"name": "email", "type": "string", "pattern": "^[^@]+@[^@]+\\\\.[^@]+$"}
                ]
            }""")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_stats(self):
        exit_code = main(["stats", self.input_csv])
        self.assertEqual(exit_code, 0)

    def test_cli_convert(self):
        out_json = os.path.join(self.temp_dir.name, "cli_out.json")
        errors_csv = os.path.join(self.temp_dir.name, "cli_errors.csv")
        report_html = os.path.join(self.temp_dir.name, "cli_report.html")

        exit_code = main([
            "convert", self.input_csv,
            "--to", "json",
            "--config", self.config_json,
            "--output", out_json,
            "--errors", errors_csv,
            "--report", report_html,
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(out_json))
        self.assertTrue(os.path.exists(errors_csv))
        self.assertTrue(os.path.exists(report_html))

    def test_cli_validate_with_errors(self):
        exit_code = main([
            "validate", self.input_csv,
            "--config", self.config_json,
        ])
        # Fails with exit code 1 because row 2 has invalid email
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
