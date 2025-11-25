from decimal import Decimal
from tsurugi.udf.model.tsurugi_types_pb2 import Decimal as PbDecimal


def to_pb_decimal(value: Decimal) -> PbDecimal:
    sign, digits, exponent = value.as_tuple()
    unscaled_int = 0
    # -123.45
    # sign  -1
    # digits 1,2,3,4,5
    # exponent -2
    for d in digits:
        unscaled_int = unscaled_int * 10 + d
    # 12345
    if sign == 1:
        unscaled_int = -unscaled_int
    # -12345
    if unscaled_int == 0:
        unscaled_bytes = b"\x00"
    else:
        byte_length = (unscaled_int.bit_length() + 8) // 8
        unscaled_bytes = unscaled_int.to_bytes(
            byte_length,
            byteorder="big",
            signed=True,
        )

    pb = PbDecimal()
    pb.unscaled_value = unscaled_bytes
    pb.exponent = exponent
    return pb


def from_pb_decimal(pb: PbDecimal) -> Decimal:
    unscaled_int = int.from_bytes(pb.unscaled_value, byteorder="big", signed=True)

    exponent = pb.exponent

    return Decimal(unscaled_int) * (Decimal(10) ** exponent)
