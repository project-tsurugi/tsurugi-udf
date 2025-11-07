# udf-plugin-viewer

## Overview

**udf-plugin-viewer** is a Python-based tool for inspecting the metadata of compiled UDF (User Defined Function) plugins built for **Tsurugi Database**.
It loads a .so plugin module (built via CMake and protobuf) and displays structural information such as packages, services, functions, input/output record schemas and versioning defined in the plugin.

This tool provides developers and operators a quick way to verify and understand what a plugin exports, how it is structured, and confirm compatibility or identify issues.

______________________________________________________________________

## Features

- Load and inspect a compiled .so UDF plugin file
- Display plugin metadata: packages, services, functions, input/output types
- Provide human-readable summary of plugin structure
- Useful for debugging, validation, or documentation of UDF plugins
- Installable via pip

______________________________________________________________________

## Requirements

| Component | Version | Description |
| ---------------- | ----------------------------------- | ------------------------------------------ |
| **CMake** | ≥ 3.14 | Build system configuration |
| **C++ Compiler** | C++17 or later (e.g., g++, clang++) | Needed to compile plugins |
| **Protobuf** | Latest | Protocol Buffers runtime |
| **gRPC** | Latest | gRPC C++ library (if plugin uses services) |
| **pybind11** | Latest | For Python binding to plugin C++ metadata |

______________________________________________________________________

## Installation

You can install the package via pip:

```bash
pip install udf-plugin-viewer
```

For local development:

```bash
pip install -e .
```

## Usage

```bash
udf-plugin-viewer path/to/plugin.so
```

______________________________________________________________________

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
