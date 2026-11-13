"""Validation Engine for DataBridge."""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .models import FieldRule, ValidationConfig, ValidationError
from .rules import validate_type, validate_range, validate_pattern, validate_length


class ConfigError(Exception):
    """Exception raised when a configuration file is missing or invalid."""
    pass


@dataclass
class ValidationResult:
    """Summary and details of validation process."""
    total_count: int = 0
    valid_count: int = 0
    error_count: int = 0
    valid_records: List[Dict[str, Any]] = field(default_factory=list)
    invalid_records: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[ValidationError] = field(default_factory=list)
    field_error_counts: Dict[str, int] = field(default_factory=dict)
    rule_error_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.error_count == 0


class ValidationEngine:
    """Engine that executes validation rules against data records."""

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()

    @classmethod
    def load_config(cls, config_path: str) -> "ValidationEngine":
        """Load configuration from YAML or JSON file."""
        if not os.path.exists(config_path):
            raise ConfigError(f"Конфигурационный файл не найден: '{config_path}'")

        _, ext = os.path.splitext(config_path)
        ext = ext.lower()

        data: Dict[str, Any] = {}
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        if ext in (".yaml", ".yml"):
            try:
                import yaml
                data = yaml.safe_load(content) or {}
            except ImportError:
                # Basic fallback YAML parser for standard key-value / lists if PyYAML is missing
                data = cls._parse_simple_yaml(content)
            except Exception as e:
                raise ConfigError(f"Ошибка парсинга YAML файла '{config_path}': {str(e)}")
        else:
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ConfigError(f"Ошибка парсинга JSON файла конфигурации '{config_path}': {str(e)}")

        fields_data = data.get("fields", [])
        field_rules: List[FieldRule] = []
        for item in fields_data:
            if isinstance(item, dict):
                rule = FieldRule(
                    name=item.get("name", ""),
                    type=item.get("type"),
                    required=bool(item.get("required", False)),
                    unique=bool(item.get("unique", False)),
                    min=item.get("min"),
                    max=item.get("max"),
                    min_length=item.get("min_length"),
                    max_length=item.get("max_length"),
                    pattern=item.get("pattern"),
                    format=item.get("format"),
                    allowed_values=item.get("allowed_values"),
                    transformations=item.get("transformations", []),
                    alias=item.get("alias"),
                )
                field_rules.append(rule)

        mapping = data.get("mapping", {})
        options = data.get("options", {})
        config = ValidationConfig(fields=field_rules, mapping=mapping, options=options)
        return cls(config)

    @staticmethod
    def _parse_simple_yaml(content: str) -> Dict[str, Any]:
        """A lightweight fallback parser for the subset of YAML used in data schemas."""
        try:
            # If PyYAML is not yet installed, see if json.loads works
            return json.loads(content)
        except Exception:
            pass

        # Parse basic fields list from yaml text
        fields: List[Dict[str, Any]] = []
        current_field: Optional[Dict[str, Any]] = None
        mapping: Dict[str, str] = {}
        in_fields = False
        in_mapping = False

        for raw_line in content.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("fields:"):
                in_fields = True
                in_mapping = False
                continue
            elif stripped.startswith("mapping:"):
                in_mapping = True
                in_fields = False
                continue

            if in_fields:
                if stripped.startswith("- name:") or stripped.startswith("-"):
                    if current_field:
                        fields.append(current_field)
                    current_field = {}
                    parts = stripped[1:].strip().split(":", 1)
                    if len(parts) == 2 and parts[0].strip() == "name":
                        current_field["name"] = parts[1].strip().strip("\"'")
                elif current_field is not None and ":" in stripped:
                    key, val = stripped.split(":", 1)
                    k = key.strip()
                    v = val.strip().strip("\"'")
                    if v.lower() == "true":
                        current_field[k] = True
                    elif v.lower() == "false":
                        current_field[k] = False
                    elif v.isdigit():
                        current_field[k] = int(v)
                    else:
                        current_field[k] = v

            elif in_mapping and ":" in stripped:
                k, v = stripped.split(":", 1)
                mapping[k.strip()] = v.strip().strip("\"'")

        if current_field:
            fields.append(current_field)

        return {"fields": fields, "mapping": mapping}

    def validate(self, records: List[Dict[str, Any]]) -> ValidationResult:
        """Validate a list of records against configured rules."""
        result = ValidationResult(total_count=len(records))

        # Track uniqueness
        unique_trackers: Dict[str, Set[Any]] = {
            f.name: set() for f in self.config.fields if f.unique
        }

        for record in records:
            row_num = record.get("_row_number", 0)
            record_errors: List[ValidationError] = []

            for field_rule in self.config.fields:
                field_name = field_rule.name
                val = record.get(field_name)

                # Check required
                is_empty = val is None or str(val).strip() == ""
                if field_rule.required and is_empty:
                    err = ValidationError(
                        row_number=row_num,
                        field=field_name,
                        value=val,
                        message="обязательное поле отсутствует или пусто",
                        rule="required"
                    )
                    record_errors.append(err)
                    continue

                if is_empty:
                    # Optional field is empty, skip other checks
                    continue

                # Check type
                if field_rule.type:
                    ok, msg = validate_type(val, field_rule.type, field_rule.format)
                    if not ok:
                        record_errors.append(
                            ValidationError(row_number=row_num, field=field_name, value=val, message=msg or "", rule="type")
                        )

                # Check min/max range
                if field_rule.min is not None or field_rule.max is not None:
                    ok, msg = validate_range(val, field_rule.min, field_rule.max, field_rule.type, field_rule.format)
                    if not ok:
                        record_errors.append(
                            ValidationError(row_number=row_num, field=field_name, value=val, message=msg or "", rule="range")
                        )

                # Check pattern
                if field_rule.pattern:
                    ok, msg = validate_pattern(val, field_rule.pattern)
                    if not ok:
                        record_errors.append(
                            ValidationError(row_number=row_num, field=field_name, value=val, message=msg or "", rule="pattern")
                        )

                # Check min_length / max_length
                if field_rule.min_length is not None or field_rule.max_length is not None:
                    ok, msg = validate_length(val, field_rule.min_length, field_rule.max_length)
                    if not ok:
                        record_errors.append(
                            ValidationError(row_number=row_num, field=field_name, value=val, message=msg or "", rule="length")
                        )

                # Check allowed values
                if field_rule.allowed_values is not None:
                    if str(val) not in [str(av) for av in field_rule.allowed_values]:
                        record_errors.append(
                            ValidationError(
                                row_number=row_num,
                                field=field_name,
                                value=val,
                                message=f"значение недопустимо (разрешены: {field_rule.allowed_values})",
                                rule="allowed_values"
                            )
                        )

                # Check uniqueness
                if field_rule.unique:
                    tracker = unique_trackers[field_name]
                    # Canonicalize for uniqueness check (strings trimmed)
                    norm_val = str(val).strip()
                    if norm_val in tracker:
                        record_errors.append(
                            ValidationError(
                                row_number=row_num,
                                field=field_name,
                                value=val,
                                message=f"значение '{val}' не уникально (уже встречалось ранее)",
                                rule="unique"
                            )
                        )
                    else:
                        tracker.add(norm_val)

            if record_errors:
                result.error_count += 1
                rec_copy = dict(record)
                rec_copy["_errors"] = record_errors
                rec_copy["_error_messages"] = "; ".join(e.message for e in record_errors)
                result.invalid_records.append(rec_copy)
                result.errors.extend(record_errors)

                for err in record_errors:
                    result.field_error_counts[err.field] = result.field_error_counts.get(err.field, 0) + 1
                    result.rule_error_counts[err.rule] = result.rule_error_counts.get(err.rule, 0) + 1
            else:
                result.valid_count += 1
                result.valid_records.append(record)

        return result
