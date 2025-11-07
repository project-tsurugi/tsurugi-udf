# tsurugi-udf

**tsurugi-udf** is a collection of tools for developing and using `User-Defined Functions (UDFs)` for [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb)
.

This repository consists of three main modules:

- **[udf-plugin-common](common/README.md)**\
   A shared utilities and definitions used by both udf-plugin-builder and udf-plugin-viewer.

- **[udf-plugin-builder](docs/udf-plugin-builder_ja.md)**\
  A build toolchain that automatically generates and compiles UDF plugins (shared libraries) loadable by Tsurugi Database.

- **[udf-plugin-viewer](docs/udf-plugin-viewer_ja.md)**\
  A viewer tool that loads and displays metadata from generated UDF plugins.

## Requirements

### C++ Side

| Component | Version | Description |
|------------|----------|--------------|
| **CMake** | ≥ 3.14 | Build system configuration |
| **C++ Compiler** | C++17 or later (e.g., g++, clang++) | Required for modern C++ features |
| **protoc** | Latest | Protocol Buffers compiler |
| **grpc_cpp_plugin** | Latest | gRPC C++ code generation plugin |
| **Protobuf** | Latest | Protocol Buffers runtime |
| **gRPC** | Latest | gRPC C++ library |
| **ninja** | Recommended | Fast build backend for CMake |

______________________________________________________________________

### Python Side

| Component | Version | Description |
|------------|----------|--------------|
| **Python** | ≥ 3.8 | |
| **pip** | Latest recommended | Python package manager |
| **jinja2** | Latest | Template engine for code generation |
| **pybind11** | Latest | C++/Python binding library |
| **scikit-build-core** | Latest | CMake-based Python build tool |
| **nlohmann_json** | Latest | JSON support |

______________________________________________________________________

## License

[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
