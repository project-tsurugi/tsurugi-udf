# udf-plugin-builder

**udf-plugin-builder** は、Protocol Buffers と gRPC を利用して\
C++ 向けの UDF (User-Defined Function) プラグインを自動生成・ビルドするためのビルドシステムです。

`.proto` ファイルを解析し、gRPC スタブおよび Jinja2 テンプレートを用いた Python スクリプトによる\
プラグイン API 実装を生成し、その後 CMake により共有ライブラリ (`libplugin_api.so`) をビルドします。

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

## 利用方法

1. gRPC サーバと通信させたい関数名・引数・戻り値を設計します。
1. その仕様を [Protocol Buffers v3 の文法](https://protobuf.dev/programming-guides/proto3/) に従い、
   `proto/sample.proto` に記述してください。
   - 元々のサンプル定義は不要なので削除して構いません。
1. Tsurugi 内部では、`.proto` に記載された **message** を最小単位に分解し、\
   `string(varchar)` / `int` / `float` などの基本型にマッピングして SQL 関数として扱います。
1. `Decimal` など Tsurugi 固有のデータ形式で通信したい場合は、\
   `proto/complex_types.proto` の **message 定義** を利用してください。
   - **注意:** `complex_types.proto` のメッセージ名が Tsurugi のデータ型判定に使用されるため、\
     改変した場合の動作は保証されません。
1. 同階層にある `proto/primitive_types.proto` はサンプル用のファイルです。
   - Tsurugi の仕様とは直接結びついていません。メッセージ名の利用は任意です。

______________________________________________________________________

## ビルド方法

```bash
mkdir build
cd build
cmake ..
make

```
