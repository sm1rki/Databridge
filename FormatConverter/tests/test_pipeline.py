"""Integration tests for DataBridge conversion pipeline."""

import os
import tempfile
import unittest
from databridge.validators.models import FieldRule, ValidationConfig
from databridge.validators.engine import ValidationEngine
from databridge.converters.mapper import FieldMapper
from databridge.converters.pipeline import ConversionPipeline
from databridge.readers.json_reader import JSONReader
from databridge.readers.csv_reader import CSVReader
from databridge.reporters.html_reporter import HTMLReporter


class TestPipeline(unittest.TestCase):
    """End-to-end integration tests."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create sample input CSV with 1 valid and 1 invalid record
        self.input_csv = os.path.join(self.temp_dir.name, "input.csv")
        with open(self.input_csv, "w", encoding="utf-8") as f:
            f.write(
                "id,name,email,age,birth_date\n"
                "1,  иван  ,ivan@mail.ru,25,1999-01-15\n"
                "2,Мария,maria.mail.ru,200,1994-05-20\n"
            )

        self.config = ValidationConfig(
            fields=[
                FieldRule(name="id", type="integer", required=True, unique=True),
                FieldRule(
                    name="name",
                    type="string",
                    required=True,
                    transformations=["strip", "capitalize"],
                ),
                FieldRule(
                    name="email",
                    type="string",
                    required=True,
                    pattern=r"^[^@]+@[^@]+\.[^@]+$",
                ),
                FieldRule(name="age", type="integer", min=16, max=100),
            ],
            mapping={"birth_date": "birthday"},
        )
        self.validator_engine = ValidationEngine(self.config)
        self.field_mapper = FieldMapper(config=self.config)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_pipeline_csv_to_json_with_validation_and_errors(self):
        output_json = os.path.join(self.temp_dir.name, "output.json")
        errors_csv = os.path.join(self.temp_dir.name, "errors.csv")

        pipeline = ConversionPipeline(
            validator_engine=self.validator_engine,
            field_mapper=self.field_mapper,
            skip_invalid=True,
        )

        res = pipeline.run(
            input_file=self.input_csv,
            output_file=output_json,
            errors_file=errors_csv,
        )

        self.assertEqual(res.total_records, 2)
        self.assertEqual(res.valid_records, 1)
        self.assertEqual(res.error_records, 1)

        # Check output JSON has 1 valid converted and mapped record
        reader = JSONReader()
        out_records = reader.read(output_json)
        self.assertEqual(len(out_records), 1)
        rec = out_records[0]
        self.assertEqual(rec["name"], "Иван")  # strip + capitalize applied!
        self.assertEqual(rec["birthday"], "1999-01-15")  # mapped!
        self.assertEqual(rec["id"], 1)  # cast to integer!

        # Check errors CSV was created and contains row 2
        csv_reader = CSVReader()
        err_records = csv_reader.read(errors_csv)
        self.assertEqual(len(err_records), 1)
        self.assertEqual(err_records[0]["row_number"], "3")
        self.assertIn("не соответствует формату", err_records[0]["error_reason"])

    def test_html_report_generation(self):
        report_html = os.path.join(self.temp_dir.name, "report.html")
        pipeline = ConversionPipeline(
            validator_engine=self.validator_engine,
            skip_invalid=True,
        )
        res = pipeline.run(
            input_file=self.input_csv,
            output_file=os.path.join(self.temp_dir.name, "out.json"),
        )
        reporter = HTMLReporter()
        reporter.generate(
            output_path=report_html,
            input_file=self.input_csv,
            validation_result=res.validation_result,
        )
        self.assertTrue(os.path.exists(report_html))
        with open(report_html, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("DataBridge", content)
        self.assertIn("maria.mail.ru", content)


if __name__ == "__main__":
    unittest.main()
