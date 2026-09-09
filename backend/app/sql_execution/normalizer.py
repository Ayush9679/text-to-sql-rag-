from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID


class ResultNormalizer:
    """Converts database values to deterministic JSON-safe Python values."""

    def normalize(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, dict):
            return {str(key): self.normalize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.normalize(item) for item in value]
        raise TypeError(f"Unsupported database value type: {type(value).__name__}")

    def normalize_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.normalize(row) for row in rows]
