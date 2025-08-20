# tsurugi-udf

**tsurugi-udf** は [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb) 向けの\
ユーザー定義関数 (UDF: User-Defined Function) を開発・利用するためのツール群です。

本リポジトリは以下の 2 つのモジュールから構成されています:

- **[udf-plugin-builder](./udf-plugin-builder/)**\
  Tsurugi にロード可能な UDF プラグイン (`.so`) を自動生成・ビルドする仕組み

- **[udf-plugin-viewer](./udf-plugin-viewer/)**\
  生成した UDF プラグインのメタデータをロードし、内容を表示するためのツール

______________________________________________________________________

## モジュール概要

### udf-plugin-builder

`udf-plugin-builder` は **UDF プラグインを生成するビルドシステム** です。\
Protocol Buffers と gRPC を用いて `.proto` ファイルからコードを生成し、\
CMake により共有ライブラリ (`.so`) をビルドします。

#### 依存関係

- CMake 3.14 以降
- Python 3.8 以降
- protobuf
- jinja2
- protoc (Protocol Buffers compiler)
- grpc_cpp_plugin
- C++17 対応コンパイラ (g++, clang++)
- pybind11
- scikit-build-core
- ninja
- nlohmann_json

#### ビルド方法

```bash
cd udf-plugin-builder
mkdir build
cd build
cmake ..
make
```

詳細は [udf-plugin-builder/README.md](./udf-plugin-builder/README.md) を参照してください。

______________________________________________________________________

### udf-plugin-viewer

`udf-plugin-viewer` は **生成済み UDF プラグインのメタデータを表示するツール** です。\
Python インターフェースと pybind11 を利用してプラグインを読み込み、\
その情報を確認できます。

#### インストール

```bash
cd udf-plugin-viewer
pip install .
```

#### アンインストール

```bash
pip uninstall udf-plugin-viewer
```

詳細は [udf-plugin-viewer/README.md](./udf-plugin-viewer/README.md) を参照してください。

______________________________________________________________________

## ライセンス

本プロジェクトは [Apache License, Version 2.0](./LICENSE) の下で提供されています。
