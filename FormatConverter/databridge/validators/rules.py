"""Validation rule implementations for DataBridge."""

import re
from datetime import datetime, date
from typing import Any, Optional, Tuple


DATE_FORMAT_MAPPINGS = [
    ("YYYY", "%Y"),
    ("YY", "%y"),
    ("MM", "%m"),
    ("DD", "%d"),
    ("HH", "%H"),
    ("mm", "%M"),
    ("ss", "%S"),
]


def convert_date_format(fmt: str) -> str:
    """Convert user-friendly format string like 'YYYY-MM-DD' to strftime format '%Y-%m-%d'."""
    res = fmt
    for token, strf in DATE_FORMAT_MAPPINGS:
        res = res.replace(token, strf)
    return res


def parse_date(value: Any, fmt: Optional[str] = None) -> Optional[datetime]:
    """Parse a date value given an optional format or try common formats."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)

    val_str = str(value).strip()
    if not val_str:
        return None

    if fmt:
        strf_fmt = convert_date_format(fmt)
        try:
            return datetime.strptime(val_str, strf_fmt)
        except ValueError:
            return None

    # Common date formats fallback
    common_formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]
    for candidate in common_formats:
        try:
            return datetime.strptime(val_str, candidate)
        except ValueError:
            continue
    return None


def validate_type(value: Any, expected_type: str, date_format: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate that value conforms to the expected type.
    Returns (is_valid, error_message).
    """
    if value is None or str(value).strip() == "":
        return True, None

    expected_type = expected_type.lower().strip()
    val_str = str(value).strip()

    if expected_type == "integer":
        try:
            # Must be a whole number, e.g. "123" or "-45"
            val_float = float(val_str)
            if not val_float.is_integer() and "." in val_str:
                return False, f"ожидалось целое число (integer), получено '{val_str}'"
            int(val_str)
            return True, None
        except ValueError:
            return False, f"не является целым числом (integer): '{val_str}'"

    elif expected_type == "float":
        try:
            float(val_str.replace(",", "."))
            return True, None
        except ValueError:
            return False, f"не является числом с плавающей точкой (float): '{val_str}'"

    elif expected_type == "string":
        return True, None

    elif expected_type == "boolean":
        lowered = val_str.lower()
        if lowered in ("true", "false", "1", "0", "yes", "no", "да", "нет", "t", "f", "y", "n"):
            return True, None
        return False, f"не является логическим значением (boolean): '{val_str}'"

    elif expected_type == "date":
        dt = parse_date(val_str, date_format)
        if dt is None:
            fmt_hint = f" (ожидался формат {date_format})" if date_format else ""
            return False, f"не соответствует формату даты{fmt_hint}: '{val_str}'"
        return True, None

    return True, None


def validate_range(
    value: Any,
    min_val: Optional[Any] = None,
    max_val: Optional[Any] = None,
    expected_type: Optional[str] = None,
    date_format: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Validate min/max boundaries for numbers and dates."""
    if value is None or str(value).strip() == "":
        return True, None

    # Handle dates
    if expected_type == "date":
        parsed_val = parse_date(value, date_format)
        if parsed_val is None:
            return True, None  # type error will catch this

        if min_val is not None:
            parsed_min = parse_date(min_val, date_format)
            if parsed_min and parsed_val < parsed_min:
                return False, f"раньше минимальной даты ({min_val})"
        if max_val is not None:
            parsed_max = parse_date(max_val, date_format)
            if parsed_max and parsed_val > parsed_max:
                return False, f"позже максимальной даты ({max_val})"
        return True, None

    # Handle numeric range
    try:
        num = float(str(value).replace(",", "."))
    except ValueError:
        return True, None

    if min_val is not None:
        try:
            min_num = float(min_val)
            if num < min_num:
                return False, f"меньше минимума ({min_val})"
        except ValueError:
            pass

    if max_val is not None:
        try:
            max_num = float(max_val)
            if num > max_num:
                return False, f"вне диапазона ({value} > max {max_val})"
        except ValueError:
            pass

    return True, None


def validate_pattern(value: Any, pattern: str) -> Tuple[bool, Optional[str]]:
    """Validate string matches regular expression."""
    if value is None or str(value).strip() == "":
        return True, None

    val_str = str(value)
    try:
        if not re.search(pattern, val_str):
            return False, "не соответствует формату"
        return True, None
    except re.error as e:
        return False, f"ошибка регулярного выражения: {str(e)}"


def validate_length(
    value: Any,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """Validate string length."""
    if value is None:
        val_str = ""
    else:
        val_str = str(value)

    if min_length is not None and len(val_str) < min_length:
        return False, f"длина строки ({len(val_str)}) меньше минимальной ({min_length})"

    if max_length is not None and len(val_str) > max_length:
        return False, f"длина строки ({len(val_str)}) превышает максимальную ({max_length})"

    return True, None
