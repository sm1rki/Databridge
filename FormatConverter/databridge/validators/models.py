"""Data models for validation rules and errors in DataBridge."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationError:
    """Represents a single validation error on a field in a record."""
    row_number: int
    field: str
    value: Any
    message: str
    rule: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_number": self.row_number,
            "field": self.field,
            "value": str(self.value) if self.value is not None else "",
            "message": self.message,
            "rule": self.rule,
        }

    def __str__(self) -> str:
        return f"Строка {self.row_number}: поле \"{self.field}\" {self.message}"


@dataclass
class FieldRule:
    """Validation and transformation specification for a single field."""
    name: str
    type: Optional[str] = None  # integer, float, string, date, boolean
    required: bool = False
    unique: bool = False
    min: Optional[Any] = None
    max: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    format: Optional[str] = None  # for dates, e.g. YYYY-MM-DD or %Y-%m-%d
    allowed_values: Optional[List[Any]] = None
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    alias: Optional[str] = None  # mapped output name


@dataclass
class ValidationConfig:
    """Overall schema configuration."""
    fields: List[FieldRule] = field(default_factory=list)
    mapping: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    def get_field_rule(self, name: str) -> Optional[FieldRule]:
        for f in self.fields:
            if f.name == name:
                return f
        return None
