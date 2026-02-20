# Tsurugi UDF Plugin Toolchain

**Tsurugi UDF** is a comprehensive toolchain for developing and utilizing `User-Defined Functions (UDFs)` for the [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb).

This toolchain integrates two main modules:

- **udf-plugin-builder**\
  A Python-based build tool for creating UDF plugins. It compiles `.proto` files and generates shared object (`.so`) plugin files and configuration files (`.ini`) using CMake.

- **udf-plugin-viewer**\
  A Python-based tool for inspecting the metadata of compiled UDF plugins. It loads `.so` plugin modules and displays structural information, such as packages, services, functions, and schemas.

## User's guide(ja)

- **[udf-plugin](../docs/udf-plugin_ja.md)**

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
  --I proto \
  --proto proto/sample.proto proto/complex_types.proto proto/primitive_types.proto \
  --grpc-endpoint dns:///localhost:50051
```

**Options**:

| Option | Description | Default | Required |
| ----------------- | --------------------------------------------------------- | ------------------------ | -------- |
| `--proto` | Path(s) to `.proto` file(s). Multiple files supported. | None | **Yes** |
| `-I`, `--include` | Directory containing `.proto` files. | First `.proto` file | No |
| `--grpc-endpoint` | gRPC server endpoint for communication. | `dns:///localhost:50051` | No |
| `--build-dir` | Temporary directory for CMake build process. | `tmp/` | No |
| `--output-dir` | Directory for the generated `.so` and `.ini` files. | Current directory (`.`) | No |
| `--grpc-transport` | gRPC transport type. | `stream` | No |
| `--output-dir` | Output directory for `.so` and `.ini`. | `.` | No |
| `--debug` | Enable debug output. | `false` | No |
| `--clean` | Remove build directory before building. | `false` | No |
| `--secure` | Enable secure gRPC connection. | `false` | No |
| `--disable` | Generate disabled UDF (`enabled=false`). | `false` | No |

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
