# tsurugi-udf

**tsurugi-udf** is a collection of tools for developing and using `User-Defined Functions (UDFs)` for [Tsurugi](https://github.com/project-tsurugi/tsurugidb).

This repository consists of the following modules:

- [Tsurugi UDF plugin toolchain](udf-plugin/README.md)
- [Tsurugi UDF Python library](udf-library/python/README.md)

## Documents

- [Overview (ja)](docs/udf-overview_ja.md)
- [Tsurugi UDF documentation index (ja)](docs/README.md)

## Requirements

The required software depends on the module and development workflow.

Python package dependencies are installed automatically by `pip` based on each module's `pyproject.toml`. You do not normally need to install those packages individually.

### Common prerequisites

| Component | Version | Description |
| --------- | ------- | ----------- |
| **Python** | ≥ 3.10 | Python runtime |
| **pip** | ≥ 24.0 | Python package installer |

### Python UDF development

`grpcio-tools` is required to generate Python source code from Protocol Buffers definitions.

```sh
python -m pip install "grpcio-tools==1.82.1"
```

It provides the `grpc_tools.protoc` command used to generate files such as `*_pb2.py` and `*_pb2_grpc.py`.

### Additional prerequisites for the UDF plugin toolchain

The following components are required to build and use the [Tsurugi UDF plugin toolchain](udf-plugin/README.md).

| Component | Version | Description |
| -------------------- | -------------------------------------- | ------------------------------------------------------- |
| **python3-dev** | Corresponding to the Python version | Python headers required to build the pybind11 extension |
| **CMake** | ≥ 3.15 | Build system configuration |
| **C++ compiler** | C++17 or later, such as g++ or clang++ | C++ compilation |
| **protoc** | ≥ 3.12.4 | Protocol Buffers compiler |
| **gRPC C++ library** | ≥ 1.30.2 | gRPC C++ runtime and development library |
| **grpc_cpp_plugin** | Same version as gRPC | gRPC C++ source-code generation plugin |
| **ninja** | ≥ 1.10.1 | Build backend for CMake |
| **nlohmann_json** | ≥ 3.10.5 | JSON library |

### Python dependencies installed automatically

Install each module with `pip`:

```sh
python -m pip install ./udf-plugin
python -m pip install ./udf-library/python
```

#### UDF plugin toolchain

Runtime dependencies:

- `jinja2`
- `protobuf`

Build dependencies:

- `pybind11`
- `scikit-build-core`
- `setuptools`
- `wheel`

#### UDF Python library

Runtime dependencies:

- `grpcio`
- `protobuf`

The authoritative dependency definitions and version constraints are maintained in each module's `pyproject.toml`.

### Test dependencies

Install the `test` extra to run tests.

For the UDF plugin toolchain:

```sh
cd udf-plugin
python -m pip install -e ".[test]"
python -m pytest
```

For the UDF Python library:

```sh
cd udf-library/python
python -m pip install -e ".[test]"
python -m pytest
```

The `test` extra installs:

- `pytest`
- `pytest-xdist`

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
