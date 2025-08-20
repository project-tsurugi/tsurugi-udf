# udf-plugin-builder

**udf-plugin-builder** は、Protocol Buffers と gRPC を利用して\
C++ 向けの UDF (User-Defined Function) プラグインを自動生成・ビルドするためのビルドシステムです。

`.proto` ファイルを解析し、gRPC スタブおよび Jinja2 テンプレートを用いた Python スクリプトによる\
プラグイン API 実装を生成し、その後 CMake により共有ライブラリ (`plugin_api.so`) をビルドします。

______________________________________________________________________

## 依存関係

- CMake 3.10 以降
- Python 3.x
  - `protobuf`
  - `jinja2`
- `protoc` (Protocol Buffers コンパイラ)
- `grpc_cpp_plugin`
- C++17 対応コンパイラ (`g++`, `clang++` など)

______________________________________________________________________

## ビルド方法

```bash
mkdir build
cd build
cmake ..
make
```

______________________________________________________________________

## 出力

- **libplugin_api.so**: CMake によりビルドされる共有ライブラリ
