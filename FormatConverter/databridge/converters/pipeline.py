"""Conversion pipeline orchestrator for DataBridge."""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..readers.factory import get_reader
from ..writers.factory import get_writer
from ..writers.csv_writer import CSVWriter
from ..validators.engine import ValidationEngine, ValidationResult
from .transformers import apply_transformation
from .mapper import FieldMapper


@dataclass
class PipelineResult:
    """Execution statistics and outcome of a conversion pipeline."""
    input_file: str
    output_file: Optional[str] = None
    errors_file: Optional[str] = None
    report_file: Optional[str] = None
    total_records: int = 0
    valid_records: int = 0
    error_records: int = 0
    validation_result: Optional[ValidationResult] = None
    converted_records: List[Dict[str, Any]] = field(default_factory=list)
    output_format: Optional[str] = None


class ConversionPipeline:
    """End-to-end pipeline connecting readers, validators, transformers, and writers."""

    def __init__(
        self,
        validator_engine: Optional[ValidationEngine] = None,
        field_mapper: Optional[FieldMapper] = None,
        skip_invalid: bool = True,
        cast_types: bool = True,
    ):
        self.validator_engine = validator_engine
        self.field_mapper = field_mapper
        self.skip_invalid = skip_invalid
        self.cast_types = cast_types

    def run(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        to_format: Optional[str] = None,
        errors_file: Optional[str] = "errors.csv",
        input_options: Optional[Dict[str, Any]] = None,
        output_options: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Execute full pipeline:
        Read -> Validate -> Save Errors -> Transform & Map -> Write Output.
        """
        input_opts = input_options or {}
        output_opts = output_options or {}

        # 1. Read input records
        reader = get_reader(input_file)
        raw_records = reader.read(input_file, **input_opts)

        res = PipelineResult(
            input_file=input_file,
            output_file=output_file,
            total_records=len(raw_records),
        )

        records_to_process = raw_records
        invalid_records: List[Dict[str, Any]] = []

        # 2. Validation
        if self.validator_engine:
            val_res = self.validator_engine.validate(raw_records)
            res.validation_result = val_res
            res.valid_records = val_res.valid_count
            res.error_records = val_res.error_count
            invalid_records = val_res.invalid_records

            if self.skip_invalid:
                records_to_process = val_res.valid_records
            else:
                records_to_process = raw_records
        else:
            res.valid_records = len(raw_records)
            res.error_records = 0

        # 3. Save errors to errors_file if any errors found
        if invalid_records and errors_file:
            self._save_errors(invalid_records, errors_file)
            res.errors_file = errors_file

        # 4. Transform and cast valid records
        transformed_records: List[Dict[str, Any]] = []
        for rec in records_to_process:
            rec_copy = dict(rec)
            # Remove internal fields
            rec_copy = {k: v for k, v in rec_copy.items() if not k.startswith("_")}

            # Apply transformations from config if available
            if self.validator_engine and self.validator_engine.config:
                for field_rule in self.validator_engine.config.fields:
                    fname = field_rule.name
                    if fname in rec_copy:
                        val = rec_copy[fname]
                        # Apply rule transformations
                        for t in field_rule.transformations:
                            if isinstance(t, str):
                                val = apply_transformation(t, val)
                            elif isinstance(t, dict):
                                t_name = t.get("name", "")
                                t_params = {k: v for k, v in t.items() if k != "name"}
                                val = apply_transformation(t_name, val, t_params)

                        # Type casting if target is JSON or numeric conversion is desired
                        if self.cast_types and val is not None and str(val).strip() != "":
                            if field_rule.type == "integer":
                                try:
                                    val = int(val)
                                except (ValueError, TypeError):
                                    pass
                            elif field_rule.type == "float":
                                try:
                                    val = float(str(val).replace(",", "."))
                                except (ValueError, TypeError):
                                    pass
                            elif field_rule.type == "boolean":
                                val = str(val).strip().lower() in ("true", "1", "yes", "да", "t", "y")

                        rec_copy[fname] = val

            # 5. Field Mapping (column renaming)
            if self.field_mapper:
                rec_copy = self.field_mapper.map_record(rec_copy)

            transformed_records.append(rec_copy)

        res.converted_records = transformed_records

        # 6. Write output if destination path is specified
        if output_file:
            writer = get_writer(output_file, format_override=to_format)
            writer.write(transformed_records, output_file, **output_opts)
            res.output_file = output_file
            res.output_format = to_format or os.path.splitext(output_file)[1].lstrip(".")

        return res

    def _save_errors(self, invalid_records: List[Dict[str, Any]], errors_file: str) -> None:
        """Write invalid records with error explanations to CSV."""
        rows_to_save: List[Dict[str, Any]] = []
        for r in invalid_records:
            row: Dict[str, Any] = {
                "row_number": r.get("_row_number", ""),
                "error_reason": r.get("_error_messages", ""),
            }
            # Include original fields
            for k, v in r.items():
                if not k.startswith("_"):
                    row[k] = v
            rows_to_save.append(row)

        writer = CSVWriter()
        writer.write(rows_to_save, errors_file)
