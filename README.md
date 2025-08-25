# tsurugi-udf

**tsurugi-udf** は [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb) 向けのユーザー定義関数 (UDF: User-Defined Function) を開発・利用するためのツール群です。

本リポジトリは以下の 2 つのモジュールから構成されています:

- **[udf-plugin-builder](./udf-plugin-builder/)** Tsurugi にロード可能な UDF プラグイン (`.so`) を自動生成・ビルドする仕組み

- **[udf-plugin-viewer](./udf-plugin-viewer/)** 生成した UDF プラグインのメタデータをロードし、内容を表示するためのツール

______________________________________________________________________

## Tsurugi Database 向けのユーザー定義関数 (UDF: User-Defined Function) 機能

Tsurugi Database では、専用の **共有ライブラリ (shared object)** を起動時にロードすることで、ユーザー定義関数 (UDF) を利用できます。\
UDF を通じて DB 上のデータを gRPC サーバに転送し、その結果を受け取って SQL の実行結果として返すことが可能になります。\
これにより、UDF 関数を **標準の SQL 関数と同様に利用** できるようになります。

### UDF プラグインの生成と設定手順

1. **UDF プラグインの生成**\
   `udf-plugin-builder` を使用して、`.proto` ファイルから UDF 用の shared object を生成します。\
   詳細は [udf-plugin-builder/README.md](./udf-plugin-builder/README.md) を参照してください。

1. **プラグインの配置**\
   生成した shared object を任意のフォルダに配置します。

1. **設定ファイル (tsurugi.ini) の編集**\
   以下の設定を追加し、プラグインのロードパスと通信先 gRPC サーバの URL を指定します。

```ini
[SQL]
loader_path=/path/to/plugins
grpc_url="localhost:50051"
```

### 使用例

例として、以下のような gRPC サービス定義があるとします:

```proto
service Greeter {
  rpc SayHello (StrValue) returns (StrValue);
}
message StrValue { string value = 1; }
```

この `.proto` ファイルを `udf-plugin-builder` でビルドし、`libplugin_api.so` を生成して `/home/tsurugide/plugins` に配置します。\
`tsurugi.ini` に以下を追記します:

```ini
[SQL]
loader_path=/home/tsurugide/plugins
grpc_url="localhost:50051"
```

その後、TsurugiDB と gRPC サーバを起動します:

```bash
tgctl start
tgsql
```

SQL からは次のように UDF を呼び出せます:

```sql
tgsql> create table t (c0 varchar(255));
tgsql> insert into t (c0) values ('how are you?');

tgsql> select sayhello(c0) from t;
```

もし gRPC サーバ側の `sayhello` が引数に `" hello"` を追加して返す処理を実装していた場合、結果は次のようになります:

```
[c0: VARCHAR]
[how are you? hello]
```

このように、UDF は **通常の SQL 関数と同じ感覚で利用可能** です。
Tsurugi DBの型とUDFのProto Typeの対応の詳細は[PROTO_TSURUGITYPES](./docs/internal/PROTO_TSURUGITYPES.md)を参照してください。

______________________________________________________________________

## モジュール概要

### udf-plugin-builder

`udf-plugin-builder` は **UDF プラグインを生成するビルドシステム** です。Protocol Buffers と gRPC を用いて `.proto` ファイルからコードを生成し、CMake により共有ライブラリ (`.so`) をビルドします。

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

`udf-plugin-viewer` は **生成済み UDF プラグインのメタデータを表示するツール** です。Python インターフェースと pybind11 を利用してプラグインを読み込み、その情報を確認できます。

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
