# UDF Library

`udf_library` is a Python library for converting between Python native types and `Tsurugi's` protobuf types (`tsurugidb.udf.*`).

Currently, the following type conversion is supported:

| Protobuf Type              | Python Type       | Protobuf -> Python   | Python -> Protobuf   |
|----------------------------|-----------------|-------------------|-------------------|
| tsurugidb.udf.Decimal | decimal.Decimal | `from_pb_decimal`  | `to_pb_decimal`    |

## Requirements

| Component        | Version | Description                                        |
| ---------------- | ------- | -------------------------------------------------- |
| **Python**       | ≥ 3.10  | Required Python version for running the library    |
| **pip**          | ≥ 24.0  | Python package manager for installing dependencies |
| **setuptools**   | ≥ 65.0  | Build system backend for packaging the library     |
| **wheel**        | ≥ 0.38  | Required to build wheel distributions              |
| **grpcio-tools** | ≥ 1.56  | gRPC & protobuf code generation tools              |
| **protobuf**     | ≥ 4.24  | Required for working with protobuf message types   |

## Installation

```bash
pip install .
```

Requires Python 3.10+ and protobuf library.

## Example

```python
from tsurugi.udf.model import tsurugi_types_pb2
from decimal import Decimal
from tsurugi.udf.converter.converter import to_pb_decimal, from_pb_decimal

decimal = tsurugi_types_pb2.Decimal()
decimal.unscaled_value = b"\x01\x23"
decimal.exponent = -2

print("Decimal:")
print("  unscaled_value:", decimal.unscaled_value)
print("  exponent:", decimal.exponent)

date = tsurugi_types_pb2.Date()
date.days = 19500

print("\nDate:")
print("  days:", date.days)

local_time = tsurugi_types_pb2.LocalTime()
local_time.nanos = 3600 * 10**9

print("\nLocalTime:")
print("  nanos:", local_time.nanos)

local_dt = tsurugi_types_pb2.LocalDatetime()
local_dt.offset_seconds = 1690000000
local_dt.nano_adjustment = 123456789

print("\nLocalDatetime:")
print("  offset_seconds:", local_dt.offset_seconds)
print("  nano_adjustment:", local_dt.nano_adjustment)

offset_dt = tsurugi_types_pb2.OffsetDatetime()
offset_dt.offset_seconds = 1690000000
offset_dt.nano_adjustment = 987654321
offset_dt.time_zone_offset = 540

print("\nOffsetDatetime:")
print("  offset_seconds:", offset_dt.offset_seconds)
print("  nano_adjustment:", offset_dt.nano_adjustment)
print("  time_zone_offset:", offset_dt.time_zone_offset)

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


# Convert Python Decimal to protobuf Decimal
x = Decimal("123.45")
pb = to_pb_decimal(x)
print("to_pb_decimal")
print(pb)

# Convert protobuf Decimal back to Python Decimal
print("from_pb_decimal")
y = from_pb_decimal(pb)
print(y)

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

to_pb_decimal
unscaled_value: "09"
exponent: -2

from_pb_decimal
123.45
```

## Recovery if Module Not Found

* Ensure you installed the package for the correct Python version
* Make sure the Python user site is on your `PYTHONPATH`.

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
