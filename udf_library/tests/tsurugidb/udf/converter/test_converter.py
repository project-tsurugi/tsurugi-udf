from tsurugidb.udf import (
    Decimal as PbDecimal,
    Date as PbDate,
    LocalTime as PbTime,
    LocalDatetime as PbDatetime,
    OffsetDatetime as PbOffsetDatetime,

    to_pb_decimal,
    from_pb_decimal,
    to_pb_date,
    from_pb_date,
    to_pb_local_time,
    from_pb_local_time,
    to_pb_local_datetime,
    from_pb_local_datetime,
    to_pb_offset_datetime,
    from_pb_offset_datetime,
)
from decimal import (
    Decimal as PyDecimal,
)
from datetime import (
    date as PyDate,
    time as PyTime,
    datetime as PyDatetime,
    timezone,
    timedelta,
)

def test_to_pb_decimal_zero():
    value = PyDecimal("0")
    pb_decimal = to_pb_decimal(value)

    assert pb_decimal.exponent == 0
    assert pb_decimal.unscaled_value == int.to_bytes(0, 1, byteorder='big', signed=True)

def test_to_pb_decimal_positive():
    value = PyDecimal("123")
    pb_decimal = to_pb_decimal(value)

    assert pb_decimal.exponent == 0
    assert pb_decimal.unscaled_value == int.to_bytes(123, 1, byteorder='big', signed=True)

def test_to_pb_decimal_negative():
    value = PyDecimal("-123.45")
    pb_decimal = to_pb_decimal(value)

    assert pb_decimal.exponent == -2
    assert pb_decimal.unscaled_value == int.to_bytes(-12345, 2, byteorder='big', signed=True)

def test_to_pb_decimal_positive_exponent():
    value = PyDecimal("123.45")
    pb_decimal = to_pb_decimal(value)

    assert pb_decimal.exponent == -2
    assert pb_decimal.unscaled_value == int.to_bytes(12345, 2, byteorder='big', signed=True)

def test_to_pb_decimal_negative_exponent():
    value = PyDecimal("12345E+2")
    pb_decimal = to_pb_decimal(value)

    assert pb_decimal.exponent == 2
    assert pb_decimal.unscaled_value == int.to_bytes(12345, 2, byteorder='big', signed=True)


def test_from_pb_decimal_zero():
    pb_decimal = PbDecimal()
    pb_decimal.exponent = 0
    pb_decimal.unscaled_value = int.to_bytes(0, 1, byteorder='big', signed=True)

    value = from_pb_decimal(pb_decimal)
    assert value == PyDecimal("0")

def test_from_pb_decimal_positive():
    pb_decimal = PbDecimal()
    pb_decimal.exponent = 0
    pb_decimal.unscaled_value = int.to_bytes(123, 1, byteorder='big', signed=True)

    value = from_pb_decimal(pb_decimal)
    assert value == PyDecimal("123")

def test_from_pb_decimal_negative():
    pb_decimal = PbDecimal()
    pb_decimal.exponent = -2
    pb_decimal.unscaled_value = int.to_bytes(-12345, 2, byteorder='big', signed=True)

    value = from_pb_decimal(pb_decimal)
    assert value == PyDecimal("-123.45")

def test_from_pb_decimal_positive_exponent():
    pb_decimal = PbDecimal()
    pb_decimal.exponent = -2
    pb_decimal.unscaled_value = int.to_bytes(12345, 2, byteorder='big', signed=True)

    value = from_pb_decimal(pb_decimal)
    assert value == PyDecimal("123.45")

def test_from_pb_decimal_negative_exponent():
    pb_decimal = PbDecimal()
    pb_decimal.exponent = 2
    pb_decimal.unscaled_value = int.to_bytes(12345, 2, byteorder='big', signed=True)

    value = from_pb_decimal(pb_decimal)
    assert value == PyDecimal("12345E+2")


def test_to_pb_date_epoch():
    d = PyDate(1970, 1, 1)
    pb_date = to_pb_date(d)
    assert pb_date.days == 0

def test_to_pb_date_after_epoch():
    d = PyDate(2023, 1, 1)
    pb_date = to_pb_date(d)
    assert pb_date.days == (d - PyDate(1970, 1, 1)).days

def test_to_pb_date_before_epoch():
    d = PyDate(1960, 1, 1)
    pb_date = to_pb_date(d)
    assert pb_date.days == (d - PyDate(1970, 1, 1)).days

def test_from_pb_date_epoch():
    pb_date = PbDate()
    pb_date.days = 0
    d = from_pb_date(pb_date)
    assert d == PyDate(1970, 1, 1)

def test_from_pb_date_after_epoch():
    d = PyDate(2023, 1, 1)
    pb_date = PbDate()
    pb_date.days = (d - PyDate(1970, 1, 1)).days
    result_date = from_pb_date(pb_date)
    assert result_date == d

def test_from_pb_date_before_epoch():
    d = PyDate(1960, 1, 1)
    pb_date = PbDate()
    pb_date.days = (d - PyDate(1970, 1, 1)).days
    result_date = from_pb_date(pb_date)
    assert result_date == d


def test_to_pb_local_time_epoch():
    t = PyTime(0, 0, 0)
    pb_time = to_pb_local_time(t)
    assert pb_time.nanos == 0

def test_to_pb_local_time_nanos():
    t = PyTime(12, 34, 56, 789_012)
    pb_time = to_pb_local_time(t)
    expected_nanos = (
        (12 * 60 * 60 + 34 * 60 + 56) * 1_000_000_000 + 789_012_000
    )
    assert pb_time.nanos == expected_nanos

def test_from_pb_local_time_epoch():
    pb_time = PbTime()
    pb_time.nanos = 0
    t = from_pb_local_time(pb_time)
    assert t == PyTime(0, 0, 0)

def test_from_pb_local_time_micros():
    expected_nanos = (
        (12 * 60 * 60 + 34 * 60 + 56) * 1_000_000_000 + 789_012_345
    )
    pb_time = PbTime()
    pb_time.nanos = expected_nanos
    t = from_pb_local_time(pb_time)
    assert t == PyTime(12, 34, 56, 789_012)


def test_to_pb_local_datetime_epoch():
    dt = PyDatetime(1970, 1, 1, 0, 0, 0)
    pb_dt = to_pb_local_datetime(dt)
    assert pb_dt.offset_seconds == 0
    assert pb_dt.nano_adjustment == 0

def test_to_pb_local_datetime_after_epoch():
    dt = PyDatetime(2023, 1, 1, 12, 34, 56, 789_012)
    pb_dt = to_pb_local_datetime(dt)
    expected_offset_seconds = int((dt - PyDatetime(1970, 1, 1)).total_seconds())
    expected_nano_adjustment = 789_012 * 1000
    assert pb_dt.offset_seconds == expected_offset_seconds
    assert pb_dt.nano_adjustment == expected_nano_adjustment

def test_to_pb_local_datetime_before_epoch():
    dt = PyDatetime(1960, 1, 1, 12, 34, 56, 789_012)
    pb_dt = to_pb_local_datetime(dt)
    expected_offset_seconds = int((dt - PyDatetime(1970, 1, 1)).total_seconds())
    expected_nano_adjustment = 789_012 * 1000
    assert pb_dt.offset_seconds == expected_offset_seconds
    assert pb_dt.nano_adjustment == expected_nano_adjustment

def test_from_pb_local_datetime_epoch():
    pb_dt = PbDatetime()
    pb_dt.offset_seconds = 0
    pb_dt.nano_adjustment = 0
    dt = from_pb_local_datetime(pb_dt)
    assert dt == PyDatetime(1970, 1, 1, 0, 0, 0)

def test_from_pb_local_datetime_after_epoch():
    dt = PyDatetime(2023, 1, 1, 12, 34, 56, 789_012)
    expected_offset_seconds = int((dt - PyDatetime(1970, 1, 1)).total_seconds())
    expected_nano_adjustment = 789_012_345

    pb_dt = PbDatetime()
    pb_dt.offset_seconds = expected_offset_seconds
    pb_dt.nano_adjustment = expected_nano_adjustment

    result_dt = from_pb_local_datetime(pb_dt)
    assert result_dt == dt

def test_from_pb_local_datetime_before_epoch():
    dt = PyDatetime(1960, 1, 1, 12, 34, 56, 789_012)
    expected_offset_seconds = int((dt - PyDatetime(1970, 1, 1)).total_seconds()) - 1 # adjust microsecond rounding
    expected_nano_adjustment = 789_012_345

    pb_dt = PbDatetime()
    pb_dt.offset_seconds = expected_offset_seconds
    pb_dt.nano_adjustment = expected_nano_adjustment

    result_dt = from_pb_local_datetime(pb_dt)
    assert result_dt == dt

def test_to_pb_offset_datetime_epoch():
    dt = PyDatetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    pb_dt = to_pb_offset_datetime(dt)
    assert pb_dt.offset_seconds == 0
    assert pb_dt.nano_adjustment == 0
    assert pb_dt.time_zone_offset == 0

def test_to_pb_offset_datetime_with_tz():
    tz = timezone(timedelta(hours=9))  # UTC+9
    dt = PyDatetime(2023, 1, 1, 12, 34, 56, 789_012, tzinfo=tz)
    pb_dt = to_pb_offset_datetime(dt)
    expected_offset_seconds = int((dt.astimezone(timezone.utc) - PyDatetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
    expected_nano_adjustment = 789_012_000
    expected_tz_offset = 9 * 60
    assert pb_dt.offset_seconds == expected_offset_seconds
    assert pb_dt.nano_adjustment == expected_nano_adjustment
    assert pb_dt.time_zone_offset == expected_tz_offset

def test_to_pb_offset_datetime_without_tz():
    dt = PyDatetime(2023, 1, 1, 12, 34, 56, 789_012, tzinfo=None)
    pb_dt = to_pb_offset_datetime(dt)
    expected_offset_seconds = int((dt.astimezone(timezone.utc) - PyDatetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
    expected_nano_adjustment = 789_012_000
    expected_tz_offset = 0
    assert pb_dt.offset_seconds == expected_offset_seconds
    assert pb_dt.nano_adjustment == expected_nano_adjustment
    assert pb_dt.time_zone_offset == expected_tz_offset


def test_from_pb_offset_datetime_epoch():
    pb_dt = PbOffsetDatetime()
    pb_dt.offset_seconds = 0
    pb_dt.nano_adjustment = 0
    pb_dt.time_zone_offset = 0
    dt = from_pb_offset_datetime(pb_dt)
    assert dt == PyDatetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

def test_from_pb_offset_datetime_with_tz():
    tz = timezone(timedelta(hours=9))  # UTC+9
    dt = PyDatetime(2023, 1, 1, 12, 34, 56, 789_012, tzinfo=tz)
    expected_offset_seconds = int((dt.astimezone(timezone.utc) - PyDatetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
    expected_nano_adjustment = 789_012_000
    expected_tz_offset = 9 * 60

    pb_dt = PbOffsetDatetime()
    pb_dt.offset_seconds = expected_offset_seconds
    pb_dt.nano_adjustment = expected_nano_adjustment
    pb_dt.time_zone_offset = expected_tz_offset

    result_dt = from_pb_offset_datetime(pb_dt)
    assert result_dt == dt

# NOTE: test_from_pb_offset_datetime_without_tz is not necessary because
# the tsurugidb.udf.OffsetDatetime always includes its timezone offset.
