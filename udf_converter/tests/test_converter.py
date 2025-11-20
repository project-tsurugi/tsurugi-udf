import pytest
from decimal import Decimal
from udf_converter.converter import to_pb_decimal, from_pb_decimal

@pytest.mark.parametrize("value_str", [
    "0",
    "1",
    "-1",
    "123.45",
    "-9876.54321",
    "1e10",
    "-1e-5",
])
def test_decimal_roundtrip(value_str):
    original = Decimal(value_str)
    pb = to_pb_decimal(original)
    restored = from_pb_decimal(pb)
    assert restored == original, f"Failed for {value_str}: got {restored}"

