# tsurugi-udf

**tsurugi-udf** is a collection of tools for developing and using `User-Defined Functions (UDFs)` for [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb).

This repository consists of two modules:

- **[Tsurugi UDF plugin toolchain](udf-plugin/README.md)**

- **[Tsurugi UDF Python library](udf-library/python/README.md)**

## Tsurugi UDF User's guide(ja)

- **[tsurugi-udf guide(ja)](docs/udf-guide_ja.md)**

## Requirements

### C++ Side

| Component | Version | Description |
|------------|----------|--------------|
| **CMake** | ≥ 3.15 | Build system configuration |
| **C++ Compiler** | C++17 or later (e.g., g++, clang++) | Required for modern C++ features |
| **protoc** | ≥ 3.12.4 | Protocol Buffers compiler |
| **gRPC** | ≥ 1.30.2 | gRPC C++ library |
| **grpc_cpp_plugin** | Same version as gRPC | gRPC C++ code generation plugin |
| **ninja** | ≥ 1.10.1 | Fast build backend for CMake |
| **nlohmann_json** | ≥ 3.10.5 | JSON support |

______________________________________________________________________

### Python Side

| Component | Version | Description |
|------------|----------|--------------|
| **Python** | ≥ 3.10 | Runtime environment |
| **python3-dev** | Corresponding version | Python C API / headers for building pybind11 extensions |
| **pip** | ≥ 24.0 | Python package manager |
| **jinja2** | ≥ 3.1.6 | Template engine for code generation |
| **pybind11** | ≥ 3.0.0 | C++/Python binding library |
| **scikit-build-core** | ≥ 0.11.6 | CMake-based Python build tool |
| **setuptools** | ≥ 80.9.0 | Python packaging library |
| **wheel** | ≥ 0.45.1 | Python wheel package support |
| **pytest** | ≥ 8.4.2 | Testing framework |
| **pytest-xdist** | ≥ 3.8.0 | Parallel test execution |
| **grpcio-tools** | ≥ 1.56 | gRPC & protobuf code generation tools |

______________________________________________________________________

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
