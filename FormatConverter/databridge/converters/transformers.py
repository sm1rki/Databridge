"""Field value transformations for DataBridge."""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from ..validators.rules import parse_date, convert_date_format


def transform_upper(value: Any, **kwargs: Any) -> Any:
    """Convert string to uppercase."""
    if value is None:
        return ""
    return str(value).upper()


def transform_lower(value: Any, **kwargs: Any) -> Any:
    """Convert string to lowercase."""
    if value is None:
        return ""
    return str(value).lower()


def transform_strip(value: Any, **kwargs: Any) -> Any:
    """Trim leading and trailing whitespace."""
    if value is None:
        return ""
    return str(value).strip()


def transform_capitalize(value: Any, **kwargs: Any) -> Any:
    """Capitalize first letter."""
    if value is None:
        return ""
    return str(value).capitalize()


def transform_replace_map(value: Any, mapping: Optional[Dict[str, Any]] = None, default: Optional[Any] = None, **kwargs: Any) -> Any:
    """Replace value according to a lookup dictionary."""
    if mapping is None:
        return value
    val_str = str(value) if value is not None else ""
    if val_str in mapping:
        return mapping[val_str]
    # Check case-insensitive
    lower_map = {k.lower(): v for k, v in mapping.items()}
    if val_str.lower() in lower_map:
        return lower_map[val_str.lower()]
    return default if default is not None else value


def transform_timestamp_to_date(value: Any, output_format: str = "%Y-%m-%d", **kwargs: Any) -> Any:
    """Convert Unix timestamp (seconds or milliseconds) to formatted date string."""
    if value is None or str(value).strip() == "":
        return ""
    try:
        val_num = float(value)
        # If timestamp is likely in milliseconds (> 10000000000)
        if val_num > 1e11:
            val_num /= 1000.0
        dt = datetime.fromtimestamp(val_num, tz=timezone.utc)
        fmt = convert_date_format(output_format)
        return dt.strftime(fmt)
    except (ValueError, OverflowError, OSError):
        return value


def transform_format_date(value: Any, input_format: Optional[str] = None, output_format: str = "%Y-%m-%d", **kwargs: Any) -> Any:
    """Reformat a date string from one format to another."""
    if value is None or str(value).strip() == "":
        return ""
    dt = parse_date(value, input_format)
    if dt is None:
        return value
    fmt = convert_date_format(output_format)
    return dt.strftime(fmt)


def transform_default(value: Any, default_value: Any = "", **kwargs: Any) -> Any:
    """Use default value if current value is None or empty."""
    if value is None or str(value).strip() == "":
        return default_value
    return value


TRANSFORMERS: Dict[str, Callable[..., Any]] = {
    "upper": transform_upper,
    "uppercase": transform_upper,
    "lower": transform_lower,
    "lowercase": transform_lower,
    "strip": transform_strip,
    "trim": transform_strip,
    "capitalize": transform_capitalize,
    "replace_map": transform_replace_map,
    "dict_replace": transform_replace_map,
    "timestamp_to_date": transform_timestamp_to_date,
    "format_date": transform_format_date,
    "default": transform_default,
}


def apply_transformation(name: str, value: Any, params: Optional[Dict[str, Any]] = None) -> Any:
    """Apply a named transformation with optional parameters."""
    norm_name = name.lower().strip()
    if norm_name not in TRANSFORMERS:
        return value
    func = TRANSFORMERS[norm_name]
    params = params or {}
    return func(value, **params)
