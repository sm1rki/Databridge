"""Field mapping and column renaming for DataBridge."""

from typing import Any, Dict, List, Optional
from ..validators.models import ValidationConfig


class FieldMapper:
    """Handles field renaming and column selection."""

    def __init__(self, mapping: Optional[Dict[str, str]] = None, config: Optional[ValidationConfig] = None):
        self.mapping = dict(mapping or {})
        if config:
            # Merge config.mapping
            self.mapping.update(config.mapping)
            # Also check if any field rule has an alias
            for f in config.fields:
                if f.alias:
                    self.mapping[f.name] = f.alias

    def map_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Rename keys in record according to mapping rules."""
        mapped: Dict[str, Any] = {}
        for k, v in record.items():
            new_key = self.mapping.get(k, k)
            mapped[new_key] = v
        return mapped

    def map_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rename keys across all records."""
        return [self.map_record(r) for r in records]
