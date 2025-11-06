# tsurugi-udf

**tsurugi-udf** は [Tsurugi Database](https://github.com/project-tsurugi/tsurugidb) 向けのユーザー定義関数 (`UDF: User-Defined Function`) を開発・利用するためのツール群です。

本リポジトリは以下の 2 つのモジュールから構成されています:

- **[udf-plugin-builder](./udf-plugin-builder/)**\
  **Tsurugi Database**にロード可能な `UDF プラグイン` (共有ライブラリ（shared object）) を自動生成・ビルドする仕組み
- **[udf-plugin-viewer](./udf-plugin-viewer/)**\
  生成した `UDF プラグイン`のメタデータをロードし、内容を表示するためのツール

______________________________________________________________________

## 目的

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

## UDF の仕組み

**Tsurugi Database** の `UDF`は、外部プログラムとの連携に `gRPC` を利用しています。
その内部構成は次のようになります。

- **Tsurugi Database** 本体は `gRPC クライアント` として振る舞う
- `UDF` 処理を担当する 外部 `gRPC サーバ` を呼び出し、必要な処理を実行
- サーバから返された応答を、`SQL` 実行の戻り値 として利用

この **「gRPC クライアント機能」** を担っているのが `UDF プラグイン` です。

`UDF プラグイン`は `udf-plugin-builder` によって 共有ライブラリ（shared object） として生成され、**Tsurugi Database** の起動時に自動的にロードされます。ロードされたプラグインは `SQL` から通常の関数のように呼び出すことができ、その裏側で `gRPC` 通信を通じて外部サーバとやり取りします。

## UDF 定義手順

**Tsurugi Database** の `UDF`は[proto 3](https://protobuf.dev/programming-guides/proto3/)に従ってprotoファイルで定義します。具体例は以下の通りです。

例: `hello.proto`

```proto
syntax = "proto3";

message HelloRequest {
  string name = 1;
}

message HelloReply {
  string message = 1;
}

service GreetingService {
  rpc SayHello (HelloRequest) returns (HelloReply);
}
```

ただし本モジュールでは[proto 3](https://protobuf.dev/programming-guides/proto3/)のすべての機能は利用できません。現在の制約は以下の通りです。

## .proto ファイル定義ルール

- `syntax = "proto3";` を必ず指定する
- `package tsurugidb` 以下にメッセージを定義してはいけない
- `message` 通常はネスト不可。tsurugidb.udf.value パッケージで使用される型なら**第二階層まで** 定義可能（第三階層以降は非対応）
- `repeated` は利用不可（将来対応予定）
- `oneof` は利用可
- `rpc` メソッドは **Unary RPC** のみ対応（Streaming RPC は非対応）
- **rpc 名は SQL 関数名になるため一意である必要がある**
- 戻り値は複数指定不可
- リクエストメッセージのフィールド順 = SQL 関数の引数順

## gRPCサーバ

[gPRC公式内のquickstar](https://grpc.io/docs/languages/python/quickstart/)を参考にgRPCサーバを構築してください。ただし**Tsurugi Database**の[proto 3](https://protobuf.dev/programming-guides/proto3/)の記述に関しては上記制限があるので注意してください。

### 例

1. 前述の`hello.proto`を用意

1. `protoc` でコード生成\
   Python の場合:

   ```sh
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. hello.proto
   ```

   これにより `hello_pb2.py` と `hello_pb2_grpc.py` が生成されます。

1. gRPC サーバを実装\
   例: `hello_server.py`

   ```python
   from concurrent import futures
   import grpc
   import hello_pb2
   import hello_pb2_grpc

   class GreetingServiceServicer(hello_pb2_grpc.GreetingServiceServicer):
       def SayHello(self, request, context):
           return hello_pb2.HelloReply(message=request.name + " hello")

   def serve():
       server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
       hello_pb2_grpc.add_GreetingServiceServicer_to_server(GreetingServiceServicer(), server)
       server.add_insecure_port('[::]:50051')
       server.start()
       server.wait_for_termination()

   if __name__ == "__main__":
       serve()
   ```

この流れにより **.proto ファイル → コード生成 → gRPC サーバ実装** が対応付けられます。

______________________________________________________________________

## 利用方法

上記を踏まえた利用方法は以下の通りです

### 前提環境

### C++ 側

- CMake 3.14 以降
- protoc
- grpc_cpp_plugin
- C++17 対応コンパイラ (g++, clang++)
- nlohmann_json

### Python 側

- Python 3.8 以降
- jinja2
- pybind11
- scikit-build-core

______________________________________________________________________

### 利用手順

以下は簡易的な利用手順です。ビルド等の詳細な手順は[リンク先](./udf-plugin-builder/README.md)を参照してください。

1. `.proto` ファイルを作成する
1. gRPC サーバを実装する
1. `udf-plugin-builder` を利用して `UDF プラグイン` (共有ライブラリ（shared object）) を生成する。
1. 生成した `UDF プラグイン` を、**Tsurugi Database** を起動するマシン上の任意のフォルダに配置する(/home/tsurugidb/plugins)
1. `tsurugi.ini` に以下を追加してプラグインディレクトリロードパス( plugin_directory=/home/tsurugidb/plugins)と gRPCサーバのendpoint(endpoint=localhost:50051) 、セキュアな通信の有無(secure=false)を指定する

```ini
[udf]
    plugin_directory=/home/tsurugidb/plugins
    endpoint=localhost:50051
    secure=false
```

1. `gRPC サーバ`を起動します。サーバの起動タイミングは、`UDF` 実行直前まで遅らせることも可能です。
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

### 注意事項

- SQL 側の関数名は **大文字小文字を区別しない**\
  `sayhello` と `SayHello` は同一と見なされる。
- 関数名は一意である必要がある。

______________________________________________________________________

## モジュール詳細

### udf-plugin-builder

`udf-plugin-builder` は **UDF プラグインを生成するツール** です。Protocol Buffers と gRPC を用いて `.proto` ファイルからコードを生成します。

#### インストール手順

##### 共通モジュールのインストール

```bash
cd tsurugi-udf
cd common
pip install .
```

#####

##### udf-plugin-builderインストール

```bash
cd tsurugi-udf
cd udf-plugin-builder
pip install .
```

#### 利用方法

```bash
udf-plugin-builder --proto_file sample.proto
```

配下にlibplugin_api.so libplugin_api.iniが生成されます

| オプション               | 型                   | デフォルト値                               | 説明                                                                                                                                                 |
| :------------------ | :------------------ | :----------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--proto_file`      | 複数指定可| `proto/sample.proto`                 | ビルド対象の `.proto` ファイルを指定します。複数ファイルをスペース区切りで指定可能です。<br>例：<br>`--proto_file proto/sample.proto proto/complex_types.proto proto/primitive_types.proto` |
| `--proto_path`      | 文字列                 | `なし`（未指定時は最初の `.proto` のディレクトリを使用） | `.proto` ファイルを含むディレクトリを指定します。`protoc` が依存ファイルを解決する際に使用されます。                                                                                        |
| `--tmp`             | 文字列                 | `"tmp"`                              | 一時的なビルド用ディレクトリを指定します。ビルド後は自動的に削除されます。                                                                                                              |
| `--plugin_api_name` | 文字列                 | `"plugin_api"`                       | 出力されるプラグインライブラリの名前を指定します。<br>例：`--plugin_api_name my_udf` → 出力ファイル名は `libmy_udf.so` / `libmy_udf.ini` になります。                                       |
| `--grpc_url`        | 文字列                 | `"localhost:50051"`                  | gRPC サーバーの URL を指定します（CMake に渡される設定値として利用されます）。                                                                                                    |

______________________________________________________________________

### udf-plugin-viewer

`udf-plugin-viewer` は **生成済み UDF プラグインのメタデータを表示するツール** です。Python インターフェースと pybind11 を利用してプラグインを読み込み、その情報を確認できます。

#### インストール

```bash
cd tsurugi-udf
cd udf-plugin-viewer
pip install .
```

詳細は [udf-plugin-viewer/README.md](./udf-plugin-viewer/README.md) を参照してください。

______________________________________________________________________

## ライセンス

本プロジェクトは [Apache License, Version 2.0](./LICENSE) の下で提供されています。
