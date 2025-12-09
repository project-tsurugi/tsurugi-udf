# UDF Library

`udf_library` is a Python library for converting between Python native types and `Tsurugi's` protobuf types (`tsurugidb.udf.*`).

Currently, the following type conversion is supported:

| Protobuf Type | Python Type | Protobuf -> Python | Python -> Protobuf |
|----------------------------|-----------------|-------------------|-------------------|
| tsurugidb.udf.Decimal | decimal.Decimal | `from_pb_decimal` | `to_pb_decimal` |
| tsurugidb.udf.Date | datetime.date | `from_pb_date` |`to_pb_date`|
| tsurugidb.udf.LocalTime | datetime.time | `from_pb_local_time` | `to_pb_local_time`|
| tsurugidb.udf.LocalDatetime | datetime.datetime | `from_pb_local_datetime` | `to_pb_local_datetime`|
| tsurugidb.udf.OffsetDatetime | datetime.datetime | `from_pb_offset_datetime` | `to_pb_offset_datetime`|

## Requirements

| Component | Version | Description |
| ---------------- | ------- | -------------------------------------------------- |
| **Python** | ≥ 3.10 | Required Python version for running the library |
| **pip** | ≥ 24.0 | Python package manager for installing dependencies |
| **setuptools** | ≥ 65.0 | Build system backend for packaging the library |
| **wheel** | ≥ 0.38 | Required to build wheel distributions |
| **grpcio-tools** | ≥ 1.56 | gRPC & protobuf code generation tools |
| **protobuf** | ≥ 4.24 | Required for working with protobuf message types |

## Installation

```bash
pip install .
```

Requires Python 3.10+ and protobuf library.

## Example

```python
from tsurugidb.udf import *
from decimal import Decimal
from datetime import date, time, datetime, timezone, timedelta
from tsurugidb.udf.converter import (
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

# ----------------------------
# Protobuf sample values
# ----------------------------
decimal = tsurugi_types_pb2.Decimal()
decimal.unscaled_value = b"\x01\x23"
decimal.exponent = -2
print("Decimal:")
print("  unscaled_value:", decimal.unscaled_value)
print("  exponent:", decimal.exponent)

date_pb = tsurugi_types_pb2.Date()
date_pb.days = 19500
print("\nDate:")
print("  days:", date_pb.days)

local_time_pb = tsurugi_types_pb2.LocalTime()
local_time_pb.nanos = 3600 * 10**9
print("\nLocalTime:")
print("  nanos:", local_time_pb.nanos)

local_dt_pb = tsurugi_types_pb2.LocalDatetime()
local_dt_pb.offset_seconds = 1690000000
local_dt_pb.nano_adjustment = 123456789
print("\nLocalDatetime:")
print("  offset_seconds:", local_dt_pb.offset_seconds)
print("  nano_adjustment:", local_dt_pb.nano_adjustment)

offset_dt_pb = tsurugi_types_pb2.OffsetDatetime()
offset_dt_pb.offset_seconds = 1690000000
offset_dt_pb.nano_adjustment = 987654321
offset_dt_pb.time_zone_offset = 540
print("\nOffsetDatetime:")
print("  offset_seconds:", offset_dt_pb.offset_seconds)
print("  nano_adjustment:", offset_dt_pb.nano_adjustment)
print("  time_zone_offset:", offset_dt_pb.time_zone_offset)

blob_ref = tsurugi_types_pb2.BlobReference()
blob_ref.storage_id = 1
blob_ref.object_id = 42
blob_ref.tag = 0
clob_ref = tsurugi_types_pb2.ClobReference()
clob_ref.storage_id = 2
clob_ref.object_id = 99
clob_ref.tag = 7
print("\nBlobReference:", blob_ref)
print("ClobReference:", clob_ref)

# ----------------------------
# Conversion examples
# ----------------------------

# Decimal
x = Decimal("123.45")
pb_decimal = to_pb_decimal(x)
print("\nPython Decimal -> Protobuf Decimal:", pb_decimal)
y = from_pb_decimal(pb_decimal)
print("Protobuf Decimal -> Python Decimal:", y)

# Date
d = date(2023, 5, 15)
pb_date = to_pb_date(d)
print("\nPython date -> Protobuf Date:", pb_date)
d2 = from_pb_date(pb_date)
print("Protobuf Date -> Python date:", d2)

# LocalTime
t = time(14, 30, 15, 123456)
pb_time = to_pb_local_time(t)
print("\nPython time -> Protobuf LocalTime:", pb_time)
t2 = from_pb_local_time(pb_time)
print("Protobuf LocalTime -> Python time:", t2)

# LocalDatetime
dt = datetime(2023, 5, 15, 14, 30, 15, 123456)
pb_local_dt = to_pb_local_datetime(dt)
print("\nPython datetime -> Protobuf LocalDatetime:", pb_local_dt)
dt2 = from_pb_local_datetime(pb_local_dt)
print("Protobuf LocalDatetime -> Python datetime:", dt2)

# OffsetDatetime
dt_tz = datetime(2023, 5, 15, 14, 30, 15, 123456, tzinfo=timezone(timedelta(hours=9)))
pb_offset_dt = to_pb_offset_datetime(dt_tz)
print("\nPython datetime with tz -> Protobuf OffsetDatetime:", pb_offset_dt)
dt2_tz = from_pb_offset_datetime(pb_offset_dt)
print("Protobuf OffsetDatetime -> Python datetime with tz:", dt2_tz)


```

### Result

```bash
Decimal:
  unscaled_value: b'\x01#'
  exponent: -2

Date:
  days: 19500

LocalTime:
  nanos: 3600000000000

LocalDatetime:
  offset_seconds: 1690000000
  nano_adjustment: 123456789

OffsetDatetime:
  offset_seconds: 1690000000
  nano_adjustment: 987654321
  time_zone_offset: 540

BlobReference: storage_id: 1
object_id: 42

ClobReference: storage_id: 2
object_id: 99
tag: 7


Python Decimal -> Protobuf Decimal: unscaled_value: "09"
exponent: -2

Protobuf Decimal -> Python Decimal: 123.45

Python date -> Protobuf Date: days: 19492

Protobuf Date -> Python date: 2023-05-15

Python time -> Protobuf LocalTime: nanos: 52215123456000

Protobuf LocalTime -> Python time: 14:30:15.123456

Python datetime -> Protobuf LocalDatetime: offset_seconds: 1684161015
nano_adjustment: 123456000

Protobuf LocalDatetime -> Python datetime: 2023-05-15 14:30:15.123456

Python datetime with tz -> Protobuf OffsetDatetime: offset_seconds: 1684128615
nano_adjustment: 123456000
time_zone_offset: 540

Protobuf OffsetDatetime -> Python datetime with tz: 2023-05-15 14:30:15.123456+09:00
```

## Using tsurugi_types.proto in Python via protoc

When you have a .proto file that references tsurugi_types.proto and you want to compile it for Python, you may encounter import issues. By default, the generated Python code uses:

```python
import tsurugi_types_pb2 as tsurugi__types__pb2
```

However, if tsurugi_types_pb2.py is part of a Python package (e.g., tsurugidb.udf.model), this import will fail at runtime. We need to modify it to include the full package path:

```python
from tsurugidb.udf.model import tsurugi_types_pb2 as tsurugi__types__pb2
```

## Recovery if Module Not Found

- Ensure you installed the package for the correct Python version
- Make sure the Python user site is on your `PYTHONPATH`.

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
