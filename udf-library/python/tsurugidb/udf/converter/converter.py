from datetime import date, time, datetime, timedelta, timezone
from decimal import Decimal
from .. import (
    Decimal as PbDecimal,
    Date as PbDate,
    LocalTime as PbLocalTime,
    LocalDatetime as PbLocalDatetime,
    OffsetDatetime as PbOffsetDatetime,
)

def to_pb_decimal(value: Decimal) -> PbDecimal:
    """Converts a standard library Decimal to Protocol Buffer Decimal message.

    Args:
        value: The decimal value to convert.

    Returns:
        Protocol Buffer message of the decimal.

    Raises:
        ValueError: If the decimal value is infinite or NaN.
    """
    if not value.is_finite():
        raise ValueError("Only finite decimal values are supported.")

    sign, digits, exponent = value.as_tuple()
    unscaled_int = 0
    for d in digits:
        unscaled_int = unscaled_int * 10 + d
    if sign == 1:
        unscaled_int = -unscaled_int
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


def from_pb_decimal(message: PbDecimal) -> Decimal:
    """Converts a Protocol Buffer Decimal message to standard library Decimal.

    Args:
        message: Protocol Buffer message of the decimal to convert.

    Returns:
        Standard library Decimal value.
    """

    unscaled_int = int.from_bytes(message.unscaled_value, byteorder="big", signed=True)
    exponent = message.exponent
    return Decimal(unscaled_int) * (Decimal(10) ** exponent)


_EPOCH_DATE = date(1970, 1, 1)

def to_pb_date(value: date) -> PbDate:
    """Converts a standard library date to Protocol Buffer Date message.

    Args:
        value: The date value to convert.

    Returns:
        Protocol Buffer message of the date.
    """
    delta = value - _EPOCH_DATE
    return PbDate(days=delta.days)


def from_pb_date(message: PbDate) -> date:
    """Converts a Protocol Buffer Date object to standard library date.

    Args:
        message: Protocol Buffer message of the date to convert.

    Returns:
        Standard library date value.
    """
    return _EPOCH_DATE + timedelta(days=message.days)


def to_pb_local_time(value: time) -> PbLocalTime:
    """Converts a standard library time to Protocol Buffer LocalTime message.

    This ignores the timezone information of the input time.

    Args:
        value: The time value to convert.

    Returns:
        Protocol Buffer message of the time.
    """
    value = value.replace(tzinfo=None)
    nanos = (
        value.hour * 3_600_000_000_000
        + value.minute * 60_000_000_000
        + value.second * 1_000_000_000
        + value.microsecond * 1000
    )
    # time does not have nanosecond precision, so microsecond * 1000
    return PbLocalTime(nanos=nanos)


def from_pb_local_time(message: PbLocalTime) -> time:
    """Converts a Protocol Buffer LocalTime message to standard library time.

    The returned time will have no timezone information (tzinfo=None).
    Nanosecond precision is truncated to microsecond precision.

    Args:
        message: Protocol Buffer message of the time to convert.

    Returns:
        Standard library time without timezone information.
    """
    total_nanos = message.nanos
    hours, rem = divmod(total_nanos, 3_600_000_000_000)
    minutes, rem = divmod(rem, 60_000_000_000)
    seconds, nanos = divmod(rem, 1_000_000_000)
    microseconds = nanos // 1000
    return time(
        hour=hours,
        minute=minutes,
        second=seconds,
        microsecond=microseconds
    )


_EPOCH_DATETIME = datetime(1970, 1, 1)

def to_pb_local_datetime(value: datetime) -> PbLocalDatetime:
    """Converts a standard library datetime to Protocol Buffer LocalDatetime message.

    This ignores the timezone information of the input datetime.

    Args:
        value: The datetime value to convert.

    Returns:
        Protocol Buffer message of the datetime.
    """
    value = value.replace(tzinfo=None)
    delta = value - _EPOCH_DATETIME
    offset_seconds = int(delta.total_seconds())
    nano_adjustment = value.microsecond * 1000
    return PbLocalDatetime(
        offset_seconds=offset_seconds,
        nano_adjustment=nano_adjustment
    )

def from_pb_local_datetime(message: PbLocalDatetime) -> datetime:
    """Converts a Protocol Buffer LocalDatetime message to standard library datetime.

    The returned datetime will have no timezone information (tzinfo=None).
    Nanosecond precision is truncated to microsecond precision.

    Args:
        message: Protocol Buffer message of the datetime to convert.

    Returns:
        Standard library datetime without timezone information.
    """

    dt = _EPOCH_DATETIME + timedelta(
        seconds=message.offset_seconds,
        microseconds=message.nano_adjustment // 1000
    )
    return dt

def to_pb_offset_datetime(value: datetime) -> PbOffsetDatetime:
    """Converts a standard library datetime to Protocol Buffer OffsetDatetime message.

    If the input datetime has no timezone information (tzinfo is None),
    it is treated as the system's local timezone.

    Args:
        value: The datetime value to convert.

    Returns:
        Protocol Buffer message of the datetime.

    Raises:
        ValueError: If the input datetime has no timezone information and
        the system's local timezone cannot be determined for it.
    """

    if value.tzinfo is None:
        try:
            value = value.astimezone()
        except Exception as e:
            raise ValueError(f"Cannot determine system's local timezone for the given datetime: {value}") from e

    delta = value.astimezone(timezone.utc) - _EPOCH_DATETIME.replace(tzinfo=timezone.utc)
    offset_seconds = int(delta.total_seconds())
    nano_adjustment = value.microsecond * 1000
    tz_offset = int(value.utcoffset().total_seconds()) // 60
    return PbOffsetDatetime(
        offset_seconds=offset_seconds,
        nano_adjustment=nano_adjustment,
        time_zone_offset=tz_offset,
    )


def from_pb_offset_datetime(message: PbOffsetDatetime) -> datetime:
    """Converts a Protocol Buffer OffsetDatetime message to standard library datetime.

    Nanosecond precision is truncated to microsecond precision.

    Args:
        message: Protocol Buffer message of the datetime to convert.

    Returns:
        Standard library datetime with timezone information.
    """

    dt_utc = _EPOCH_DATETIME.replace(tzinfo=timezone.utc) + timedelta(
        seconds=message.offset_seconds,
        microseconds=message.nano_adjustment // 1000,
    )
    tz = timezone(timedelta(minutes=message.time_zone_offset))
    return dt_utc.astimezone(tz)

__all__ = [
    'to_pb_decimal', 'from_pb_decimal',
    'to_pb_date', 'from_pb_date',
    'to_pb_local_time', 'from_pb_local_time',
    'to_pb_local_datetime', 'from_pb_local_datetime',
    'to_pb_offset_datetime', 'from_pb_offset_datetime',
]
