# UDF Converter

`udf_converter` is a Python library for converting between Python native types and `Tsurugi's` protobuf types (`tsurugidb.udf.value.*`).

Currently, the following type conversion is supported:

| Protobuf Type              | Python Type       | Protobuf -> Python   | Python -> Protobuf   |
|----------------------------|-----------------|-------------------|-------------------|
| tsurugidb.udf.value.Decimal | decimal.Decimal | `from_pb_decimal`  | `to_pb_decimal`    |

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
from decimal import Decimal
from udf_converter.converter import to_pb_decimal, from_pb_decimal

# Convert Python Decimal to protobuf Decimal
x = Decimal("123.45")
pb = to_pb_decimal(x)
print(pb)

# Convert protobuf Decimal back to Python Decimal
y = from_pb_decimal(pb)
print(y)
```

### Result

```bash
unscaled_value: "09"
exponent: -2

123.45
```

## Recovery if Module Not Found

* Ensure you installed the package for the correct Python version
* Make sure the Python user site is on your `PYTHONPATH`.

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
