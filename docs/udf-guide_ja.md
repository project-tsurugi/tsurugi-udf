# Tsurugi UDF ユーザガイド

本書では Tsurugi UDF の基本的な利用方法を解説します。

## 前提環境

Tsurugi UDF が提供する各ツールは 以下の Python 実行環境が必要です。

| コンポーネント | バージョン | 備考 |
| -------------- | --------- | ---- |
| **Python** | ≥ 3.10 | Python 3.9 以前のバージョンは利用不可 |
| **pip** | ≥ 24.0 | Ubuntu 22 環境で `python3-pip` パッケージで導入した場合はアップグレードが必要 |

その他、実行環境に必要なコンポーネントについての詳細は [tsurugi-udf/README.md](https://github.com/project-tsurugi/tsurugi-udf/blob/master/README.md) を参照してください。

本書では、gRPC 関連のプログラムやソースコードは gRPC 公式ドキュメントの [gRPC - Python Quick start][python-quickstart] の内容に基づいた Python による例を示します。

- [gRPC - Python Quick start][python-quickstart]

本書の手順例を試す場合、事前にこのドキュメントの手順を実行してPythonによる gRPC サービスの実装と実行ができる環境を整えておくとよいでしょう。

### Tsurugi 実行環境について

本書では、Tsurugi と UDF の処理を実行する gRPC サーバ が同一マシン上で動作する手順を示します。

Tsurugi のセットアップ手順については [Tsurugi Getting Started](https://github.com/project-tsurugi/tsurugidb/blob/master/docs/getting-started_ja.md) などを参照してください。

## UDFの作成・登録手順

UDF を作成して Tsurugi 上で利用可能にするには、以下の手順を実行します。

- UDF のインターフェース定義
  - UDF のインターフェースを gRPC サービスとして定義した `.proto` ファイルを作成する
- UDF のサービス実装と実行
  - UDF の処理を gRPC サービスとして実装し、これを gRPC サーバ上で実行する
- UDF プラグインの生成
  - `udf-plugin-builder` を利用して UDF プラグインを生成する
- UDF プラグインのデプロイ
  - UDF プラグインを Tsurugi にデプロイする


### UDF のインターフェース定義

UDF のインターフェース（関数名や関数の引数、戻り値の型など）を gRPC サービスとして定義するための サービス定義ファイル（`.proto` ファイル）を作成します。
Tsurugi の UDF は [proto3][proto-3] に従って `.proto` ファイルを記述します。

[gRPC - Python Quickstart][python-quickstart] の内容に基づいた `.proto` ファイルの定義例は以下の通りです。

`helloworld.proto`

```proto
syntax = "proto3";

// The greeting service definition.
service Greeter {
  // Sends a greeting
  rpc SayHello (HelloRequest) returns (HelloReply) {}
  // Sends another greeting
  rpc SayHelloAgain (HelloRequest) returns (HelloReply) {}
}

// The request message containing the user's name.
message HelloRequest {
  string name = 1;
}

// The response message containing the greetings
message HelloReply {
  string message = 1;
}
```

> [!IMPORTANT]
> Tsurugi の UDF 向けの `.proto` ファイル記述の制約として、**`.proto` ファイルの先頭には必ず `syntax = "proto3";` を指定する** 必要があります。
> [gRPC - Python Quickstart][python-quickstart] で作成した `.proto` ファイルにこれが含まれていない場合は、この定義を追加してください。

`.proto` ファイル内の RPC メソッド名（`rpc` に続くメソッド名、上記例では `SayHello` や `SayHelloAgain`）が、Tsurugi の UDF 関数名として利用されます。
また、`.proto` ファイル内で定義されるメッセージ型（`message` に続く型名、上記例では `HelloRequest` や `HelloReply`）は、UDF の引数型および戻り値型として利用されます。

その他、Tsurugi 固有の `.proto` ファイルの記述ルールや制約については [udf-proto_ja.md](./udf-proto_ja.md) を参照してください。

### UDF のサービス実装と実行

[UDF のインターフェース定義](#udf-のインターフェース定義) で作成した gRPCサービスの定義に従って gRPC サービスを実装し、 gRPC サーバ上で実行します。

[gRPC - Python Quickstart][python-quickstart] では [gRPC tools](https://pypi.org/project/grpcio-tools/) を使って Python の gRPC 関連のソースコード生成を行い、gRPC サーバを実行する手順が説明されています。ここではその手順に従って gRPC サーバを構築する方法を説明します。

以降の手順では、[UDF のインターフェース定義](#udf-のインターフェース定義) で作成した `helloworld.proto` が現在のディレクトリにあるものとします。
まず、`grpc_tools.protoc` Python モジュールを使って `.proto` ファイルから gRPC 関連の Python ソースコードを生成します。[gRPC - Python Quickstart][python-quickstart] の例からは、ディレクトリパスのみを変更しています。

```sh
$ python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. helloworld.proto
```

これにより、 `helloworld_pb2.py` と `helloworld_pb2_grpc.py` という 2 つの Python ソースコードファイルが生成されます。

次に、同じディレクトリに `greeter_server.py` を作成し、gRPC サーバの実装を記述します。
以下のソースコードは [gRPC - Python Quickstart][python-quickstart] の例と全く同じものです。

`greeter_server.py`

```python
"""The Python implementation of the GRPC helloworld.Greeter server."""

from concurrent import futures
import logging

import grpc
import helloworld_pb2
import helloworld_pb2_grpc


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message="Hello, %s!" % request.name)

    def SayHelloAgain(self, request, context):
        return helloworld_pb2.HelloReply(message="Hello, again, %s!" % request.name)

def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
```

作成した `greeter_server.py` を実行して gRPC サーバを起動します。

```sh
$ python greeter_server.py
```

[gRPC - Python Quickstart][python-quickstart] の例ではこの後に gRPC クライアントを実行してサーバと通信する手順を説明していますが、Tsurugi の UDF として利用する場合は gRPC クライアントは Tsurugi 本体が担うため、ここでの gRPC クライアントの実装は不要です。

gRPC サーバの動作確認などのために Python の gRPC クライアントを実装して実行したい場合は、[gRPC - Python Quickstart][python-quickstart] の手順に従ってください。

### UDF プラグインの生成

Tsurugi UDF において、UDF に対応した gRPC サービスを呼び出す gRPC クライアントの機能を担う Tsurugi の拡張機能が UDF プラグインです。UDF プラグインは `udf-plugin-builder` を利用して生成します。

`udf-plugin-builder` は [UDF のインターフェース定義](#udf-のインターフェース定義) で作成した `.proto` ファイルを指定して実行することで、UDF プラグインを構成するプラグインライブラリファイルやプラグイン設定ファイルを生成します。

#### `udf-plugin` のセットアップ

`udf-plugin-builder` を利用するには、[tsurugi-udf](https://github.com/project-tsurugi/tsurugi-udf) リポジトリのソースコードを取得し、これに含まれるPythonパッケージ `udf-plugin` をインストールします。

以下は  `udf-plugin` のインストール手順例です。

```sh
# tsurugi-udf のソースアーカイブのダウンロードと展開
$ TSURUGI_UDF_VERSION="0.1.0"
$ curl -OL https://github.com/project-tsurugi/tsurugi-udf/archive/refs/tags/${TSURUGI_UDF_VERSION}.tar.gz
$ tar xf ${TSURUGI_UDF_VERSION}.tar.gz
$ cd tsurugi-udf-${TSURUGI_UDF_VERSION}

# udf-plugin のインストール
$ cd udf-plugin
$ pip install .
```

#### `udf-plugin-builder` の実行

`udf-plugin-builder` を実行して UDF プラグインを生成します。以下は `helloworld.proto` をもとに UDF プラグインを生成する例です。

```sh
$ udf-plugin-builder --proto-file helloworld.proto
```

これにより、現在のディレクトリに以下のファイルが生成されます。

- `libhelloworld.so` : プラグインライブラリファイル
- `libhelloworld.ini` : プラグイン設定ファイル

### UDF プラグインのデプロイ

生成した UDF プラグインを Tsurugi にデプロイすることで、UDF が利用可能になります。

UDF プラグインのデプロイは、Tsurugi が停止している状態で、UDF プラグインの構成ファイルを Tsurugi のプラグイン配置ディレクトリに配置します。プラグイン配置ディレクトリのデフォルトは `${TSURUGI_HOME}/var/plugins` です。

`udf-plugin-builder` で生成した UDF プラグインの構成ファイルを、UDF プラグイン配置ディレクトリに移動します。

```sh
mv libhelloworld.so libhelloworld.ini ${TSURUGI_HOME}/var/plugins/
```

UDF プラグインを配置したら、Tsurugi を起動します。

```sh
$ tgctl start
```

これで、Tsurugi から UDF を呼び出す準備が整いました。

## UDF の実行

Tsurugi を起動した後、SQL から UDF を通常の関数と同様に呼び出すことができます。
ここでは `tgsql` を使って UDF を呼び出す例を示します。

```sql
-- UDF確認用テーブルとデータ作成
tgsql> CREATE TABLE t (c0 VARCHAR(255));
tgsql> INSERT INTO t (c0) VALUES ('Tsurugi');
tgsql> SELECT c0 FROM t;
[c0: VARCHAR(255)]
[Tsurugi]

-- UDF "SayHello" の呼び出し
tgsql> SELECT SayHello(c0) FROM t;
[@#0: VARCHAR(*)]
[Hello, Tsurugi!]

-- UDF "SayHelloAgain" の呼び出し
tgsql> SELECT SayHelloAgain(c0) FROM t;
[@#0: VARCHAR(*)]
[Hello, again, Tsurugi!]
```

なお、SQL内でのUDF関数の記述は大文字/小文字を区別しません。

[python-quickstart]: https://grpc.io/docs/languages/python/quickstart/
[proto-3]: https://protobuf.dev/programming-guides/proto3/
