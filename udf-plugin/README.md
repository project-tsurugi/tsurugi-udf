# Tsurugi UDF Plugin Toolchain

**Tsurugi UDF** is a comprehensive toolchain for developing and utilizing `User-Defined Functions (UDFs)` for the [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb).

This toolchain integrates two main modules:

- **udf-plugin-builder**\
  A Python-based build tool for creating UDF plugins. It compiles `.proto` files and generates shared object (`.so`) plugin files and configuration files (`.ini`) using CMake.

- **udf-plugin-viewer**\
  A Python-based tool for inspecting the metadata of compiled UDF plugins. It loads `.so` plugin modules and displays structural information, such as packages, services, functions, and schemas.

## User's guide(ja)

- **[udf-plugin](../docs/udf-plugin_ja.md)**

## Requirements

### C++ Side

| Component | Version | Description |
|----------------------|---------|----------------------------------------------|
| **CMake** | ≥ 3.15 | Build system configuration |
| **C++ Compiler** | C++17+ | Required for modern C++ features |
| **protoc** | Latest | Protocol Buffers compiler |
| **grpc_cpp_plugin** | Latest | gRPC C++ code generation plugin |
| **Protobuf** | 6.31.1 | Protocol Buffers runtime |
| **gRPC** | Latest | gRPC C++ library |
| **ninja** | Recommended | Fast build backend for CMake |

### Python Side

| Component | Version | Description |
|---------------------|----------|----------------------------------------------|
| **Python** | ≥ 3.10 | |
| **python3-dev** | Corresponding version | Python C API / headers for pybind11 |
| **pip** | ≥ 24.0 | Python package manager |
| **jinja2** | 3.1.6 | Template engine for code generation |
| **pybind11** | 3.0.0 | C++/Python binding library |
| **scikit-build-core** | 0.11.6 | CMake-based Python build tool |
| **setuptools** | 80.9.0 | Python packaging library |
| **wheel** | 0.45.1 | Python wheel package support |
| **pytest** | 8.4.2 | Testing framework |
| **pytest-xdist** | 3.8.0 | Parallel test execution |
| **nlohmann_json** | Latest | JSON support |

## Installation

You can install the toolchain using `pip`:

```bash
pip install tsurugi-udf
```

For development purposes, install it locally:

```bash
pip install -e tsurugi-udf
```

## Usage

### udf-plugin-builder

**Overview**:
`udf-plugin-builder` is used for creating UDF plugins from `.proto` files.

**Example**:

```bash
udf-plugin-builder \
  --proto-path proto \
  --proto-file proto/sample.proto proto/complex_types.proto proto/primitive_types.proto \
  --name plugin_api \
  --grpc-endpoint dns:///localhost:50051
```

**Options**:

| Option | Description | Default | Required |
| ----------------- | --------------------------------------------------------- | ------------------------ | -------- |
| `--proto-file` | Path(s) to `.proto` file(s). Multiple files supported. | None | **Yes** |
| `--proto-path` | Directory containing `.proto` files. | First `.proto` file | No |
| `--name` | Base name for the generated plugin (.so) and `.ini` file. | None | No |
| `--grpc-endpoint` | gRPC server endpoint for communication. | `dns:///localhost:50051` | No |
| `--build-dir` | Temporary directory for CMake build process. | `tmp/` | No |
| `--output-dir` | Directory for the generated `.so` and `.ini` files. | Current directory (`.`) | No |

### udf-plugin-viewer

**Overview**:
`udf-plugin-viewer` is used for inspecting the metadata of compiled UDF plugins.

**Usage**:

```bash
udf-plugin-viewer path/to/plugin.so
```

**Features**:

- Load and inspect a compiled `.so` UDF plugin file or directory.
- Display plugin metadata, including packages, services, functions, and input/output types.
- Provides a human-readable summary of the plugin’s structure.
- Useful for debugging, validation, or documentation of UDF plugins.

## Testing

You can run tests after installing the toolchain:

```bash
pytest
```

or directly with:

```bash
python -m pytest
```

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
