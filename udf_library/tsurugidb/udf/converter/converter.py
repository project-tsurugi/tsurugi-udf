from datetime import date, time, datetime, timedelta, timezone
from decimal import Decimal
from tsurugidb.udf.model.tsurugi_types_pb2 import (
    Decimal as PbDecimal,
    Date as PbDate,
    LocalTime as PbLocalTime,
    LocalDatetime as PbLocalDatetime,
    OffsetDatetime as PbOffsetDatetime,
)


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


# message Date {
#  // the number of days since 1970-01-01.
#  sint32 days = 1;
# }
EPOCH_DATE = date(1970, 1, 1)


def to_pb_date(d: date) -> PbDate:
    delta = d - EPOCH_DATE
    return PbDate(days=delta.days)


def from_pb_date(pb_date: PbDate) -> date:
    return EPOCH_DATE + timedelta(days=pb_date.days)


# message LocalTime {
#  // the number of nanoseconds since midnight.
#  sint64 nanos = 1;
# }
def to_pb_local_time(t: time) -> PbLocalTime:
    nanos = (
        t.hour * 3600_000_000_000
        + t.minute * 60_000_000_000
        + t.second * 1_000_000_000
        + t.microsecond * 1000
    )
    # time does not have nanosecond precision, so microsecond * 1000
    return PbLocalTime(nanos=nanos)


def from_pb_local_time(pb_time: PbLocalTime) -> time:
    total_nanos = pb_time.nanos
    hours, rem = divmod(total_nanos, 3600_000_000_000)
    minutes, rem = divmod(rem, 60_000_000_000)
    seconds, nanos = divmod(rem, 1_000_000_000)
    microseconds = nanos // 1000
    return time(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)


# message LocalDatetime {
#  // offset seconds from epoch (1970-01-01 00:00:00) at the local time zone.
#  sint64 offset_seconds = 1;
#  // nano-seconds adjustment [0, 10^9-1].
#  uint32 nano_adjustment = 2;
# }
EPOCH_DATETIME = datetime(1970, 1, 1)


def to_pb_local_datetime(dt: datetime) -> PbLocalDatetime:
    delta = dt - EPOCH_DATETIME
    offset_seconds = int(delta.total_seconds())
    nano_adjustment = dt.microsecond * 1000
    return PbLocalDatetime(
        offset_seconds=offset_seconds, nano_adjustment=nano_adjustment
    )


def from_pb_local_datetime(pb_dt: PbLocalDatetime) -> datetime:
    dt = EPOCH_DATETIME + timedelta(
        seconds=pb_dt.offset_seconds, microseconds=pb_dt.nano_adjustment // 1000
    )
    return dt


# message OffsetDatetime {
#  // offset seconds from epoch (1970-01-01 00:00:00Z).
#  sint64 offset_seconds = 1;
#  // nano-seconds adjustment [0, 10^9-1].
#  uint32 nano_adjustment = 2;
#  // timezone offset in minute.
#  sint32 time_zone_offset = 3;
# }
def to_pb_offset_datetime(dt: datetime) -> PbOffsetDatetime:
    if dt.tzinfo is None:
        tz_offset_min = 0
    else:
        tz_offset_min = int(dt.utcoffset().total_seconds() // 60)
    delta = dt.astimezone(timezone.utc) - EPOCH_DATETIME.replace(tzinfo=timezone.utc)
    offset_seconds = int(delta.total_seconds())
    nano_adjustment = dt.microsecond * 1000
    return PbOffsetDatetime(
        offset_seconds=offset_seconds,
        nano_adjustment=nano_adjustment,
        time_zone_offset=tz_offset_min,
    )


def from_pb_offset_datetime(pb_dt: PbOffsetDatetime) -> datetime:
    dt_utc = EPOCH_DATETIME.replace(tzinfo=timezone.utc) + timedelta(
        seconds=pb_dt.offset_seconds,
        microseconds=pb_dt.nano_adjustment // 1000,
    )
    tz = timezone(timedelta(minutes=pb_dt.time_zone_offset))
    return dt_utc.astimezone(tz)
