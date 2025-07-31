# udf-plugin-builder

**udf-plugin-builder** is a build system that automates the generation and compilation of a UDF (User-Defined Function) plugin for C++ using Protocol Buffers and gRPC. It parses `.proto` files to generate gRPC stubs and a plugin API implementation using a Python script with Jinja2 templates, and then builds the resulting C++ code into a shared library (`plugin_api.so`) using CMake.

## Dependencies

- CMake 3.10 or later
- Python 3.x
  - `protobuf`
  - `jinja2`
- `protoc` (Protocol Buffers compiler)
- `grpc_cpp_plugin`
- C++17-compatible compiler (`g++`, `clang++`, etc.)

## Build

```
mkdir build
cd build
cmake .
make
```
## Output

plugin_api.so: The shared library built by CMake
