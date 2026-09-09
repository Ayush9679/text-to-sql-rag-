from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from app.sql_execution.normalizer import ResultNormalizer


def test_normalizer_converts_database_values_deterministically():
    normalizer = ResultNormalizer()
    value = {
        "none": None, "integer": 1, "float": 1.5, "text": "customer",
        "decimal": Decimal("12.50"), "date": date(2026, 8, 20),
        "datetime": datetime(2026, 8, 20, 10, 30), "time": time(10, 30),
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
    }

    normalized = normalizer.normalize(value)

    assert normalized["none"] is None
    assert normalized["decimal"] == "12.50"
    assert normalized["date"] == "2026-08-20"
    assert normalized["datetime"] == "2026-08-20T10:30:00"
    assert normalized["time"] == "10:30:00"
    assert normalized["uuid"] == "12345678-1234-5678-1234-567812345678"


def test_normalizer_handles_nested_rows():
    assert ResultNormalizer().normalize_rows([{"values": (Decimal("1.0"), None)}]) == [
        {"values": ["1.0", None]}
    ]
