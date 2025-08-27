# tsurugi-udf

**tsurugi-udf** は [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb) 向けのユーザー定義関数 (`UDF: User-Defined Function`) を開発・利用するためのツール群です。

本リポジトリは以下の 2 つのモジュールから構成されています:

- **[udf-plugin-builder](./udf-plugin-builder/)**\
  **Tsurugi Database**にロード可能な `UDF プラグイン` (共有ライブラリ（shared object）) を自動生成・ビルドする仕組み
- **[udf-plugin-viewer](./udf-plugin-viewer/)**\
  生成した `UDF プラグイン`のメタデータをロードし、内容を表示するためのツール

______________________________________________________________________

## 背景と目的

従来の **Tsurugi Database** では、`SQL` から利用可能な関数はあらかじめ組み込まれた **built-in 関数** のみに限られていました。たとえば以下のような呼び出しです:

```sql
SELECT length(c0) FROM t;
```

今回の `UDF` 機能により、利用者が独自に関数を定義し、それを SQL から呼び出せるようになりました。

```sql
SELECT sayhello(c0) FROM t;
```

このように、**built-in 関数** とは別に **独自の UDF を SQL 関数と同様の形で利用可能** となります。

______________________________________________________________________

## UDF 機能の仕組み

**Tsurugi Database** の `UDF`は、外部プログラムとの連携に `gRPC` を利用しています。
その内部構成は次のようになります。

- **Tsurugi Database** 本体は `gRPC クライアント` として振る舞う
- `UDF` 処理を担当する 外部 `gRPC サーバ` を呼び出し、必要な処理を実行
- サーバから返された応答を、`SQL` 実行の戻り値 として利用

この **「gRPC クライアント機能」** を担っているのが `UDF プラグイン` です。

`UDF プラグイン`は `udf-plugin-builder` によって 共有ライブラリ（shared object） として生成され、**Tsurugi Database** の起動時に自動的にロードされます。ロードされたプラグインは `SQL` から通常の関数のように呼び出すことができ、その裏側で `gRPC` 通信を通じて外部サーバとやり取りします。

______________________________________________________________________

## 利用手順

以下は簡易的な利用手順です。ビルド等の詳細な手順は[リンク先](./udf-plugin-builder/README.md)を参照してください。

1. `udf-plugin-builder` を利用して `UDF プラグイン` (共有ライブラリ（shared object）) を生成する。
1. 生成した `UDF プラグイン` を、**Tsurugi Database** を起動するマシン上の任意のフォルダに配置する(/home/tsurugidb/plugins)
1. `tsurugi.ini` に以下を追加してロードパス(/home/tsurugidb/plugins)と gRPCサーバのURL(localhost:50051) を指定する

```ini
[SQL]
loader_path=/home/tsurugidb/plugins
grpc_url=localhost:50051
```

4. `gRPC サーバ`を起動します。サーバの起動タイミングは、`UDF` 実行直前まで遅らせることも可能です。
1. **Tsurugi Database** を起動し、`SQL` から `UDF` を呼び出す。

```sql
CREATE TABLE t (c0 VARCHAR(255));
INSERT INTO t (c0) VALUES ('how are you?');
-- sayhello はudf-plugin-builderでUDFとして用意済み
SELECT sayhello(c0) FROM t;
```

もし `gRPC サーバ`側が `" hello"` を追加する処理をしていれば、結果は次のようになります:

```
[c0: VARCHAR]
[how are you? hello]
```

______________________________________________________________________

## モジュール詳細

### udf-plugin-builder

`udf-plugin-builder` は **UDF プラグインを生成するビルドシステム** です。Protocol Buffers と gRPC を用いて `.proto` ファイルからコードを生成し、CMake により共有ライブラリをビルドします。

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
cmake .. -DPROTO_PATH="proto" \
-DPROTO_FILES="proto/sample.proto;proto/extra.proto" \ 
-DPLUGIN_API_NAME="my_udf"
make
```

#### CMake オプション

| オプション名 | 説明 | 既定値 |
|---------------------|----------------------------------------------------------------------|--------|
| `PROTO_PATH` | `.proto` ファイルが置かれているディレクトリへのパス | `proto` |
| `PROTO_FILES` | コンパイル対象とする `.proto` ファイルのリスト（`;` 区切りで指定）。2番目以降のファイルは、先頭の `.proto` ファイルから import されるものに限定してください。importされないファイルを指定した場合、動作は保証されません | `proto/sample.proto; proto/complex_types.proto; proto/primitive_types.proto` |
| `PLUGIN_API_NAME` | 生成されるプラグイン API ライブラリのターゲット名（`lib<name>.so` になる） | `plugin_api` |

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
