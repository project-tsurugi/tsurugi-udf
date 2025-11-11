# UDF Plugin Builder

## Overview

**udf-plugin-builder** is a Python-based build tool for creating **Tsurugi Database** UDF (User Defined Function) plugins.\
It allows developers to compile `.proto` files and generate shared object (`.so`) plugin files via CMake, directly from the command line or Python.

______________________________________________________________________

## Features

- Build UDF plugins automatically with a single command
- Support multiple `.proto` files
- CMake-based build process
- Automatic temporary directory handling
- Can be installed via **pip**

______________________________________________________________________

## Requirements

### C++ Side

| Component | Version | Description |
|------------|----------|--------------|
| **CMake** | ≥ 3.15 | Build system configuration |
| **C++ Compiler** | C++17 or later (e.g., g++, clang++) | Required for modern C++ features |
| **protoc** | Latest | Protocol Buffers compiler |
| **grpc_cpp_plugin** | Latest | gRPC C++ code generation plugin |
| **Protobuf** | Latest | Protocol Buffers runtime |
| **gRPC** | Latest | gRPC C++ library |
| **ninja** | Recommended | Fast build backend for CMake |

### Python Side

| Component | Version | Description |
|------------|----------|--------------|
| **Python** | ≥ 3.8 | Required runtime |
| **pip** | **≥ 24.0** | Python package manager |
| **tsurugi-udf-common** | ≥ 0.1.0 | Common definitions and utilities for UDF plugins |
| **jinja2** | Latest | Template engine for code generation |
| **protobuf** | Latest | Protocol Buffers library |
| **pybind11** | Latest | C++/Python binding library |
| **scikit-build-core** | Latest | CMake-based Python build tool |
| **nlohmann_json** | Latest | JSON library for C++ |

## Installation

You can install this package using `pip`:

```bash
pip install .
```

To install it locally for development:

```bash
pip install -e .
```

## Usage

### Basic Command

```bash
udf-plugin-builder --proto_file proto/sample.proto
```

### Multiple .proto Files

```bash
udf-plugin-builder --proto_file proto/sample.proto proto/complex_types.proto proto/primitive_types.proto
```

### Specify Proto Path

```bash
udf-plugin-builder --proto_path proto --proto_file proto/sample.proto
```

### Full Example

```bash
udf-plugin-builder \
  --proto_path proto \
  --proto_file proto/sample.proto proto/complex_types.proto proto/primitive_types.proto \
  --plugin_api_name plugin_api \
  --grpc_url localhost:50051
```

## Options

| Option | Description | Default |
| ------------------- | ------------------------------------------------------ | -------------------- |
| `--proto_file` | Path(s) to `.proto` file(s). Multiple files supported. | `proto/sample.proto` |
| `--proto_path` | Directory containing `.proto` files. | `None` |
| `--plugin_api_name` | Plugin API library name. | `plugin_api` |
| `--grpc_url` | gRPC server URL for communication. | `localhost:50051` |
| `--build_dir` | Temporary directory used for CMake build. | `tmp/` |

## How to Test

You can run tests after installing the package:

```bash
pytest
```

or directly with:

```bash
python -m pytest
```

## How to Use

[udf-plugin-builder guide (ja)](../docs/udf-plugin-builder_ja.md)

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
