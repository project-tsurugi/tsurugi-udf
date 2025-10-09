# udf-plugin-builder

## 概要

**udf-plugin-builder** は、[Tsurugi Database](https://github.com/project-tsurugi/tsurugidb) 向けの\
**UDF (User-Defined Function) プラグイン**と**プラグイン設定ファイル**を自動生成・ビルドするためのツールです。

Tsurugi Database の UDF は **gRPC** を利用して外部サービスと通信します。\
ユーザーは `.proto` ファイルで関数インターフェースを定義し、`udf-plugin-builder` を用いて\
UDF プラグインを生成することで、SQL から外部処理を透過的に呼び出せます。

______________________________________________________________________

## 利用の流れ

1. `.proto` ファイルで UDF のインターフェースを定義
1. gRPC サーバに処理を実装（本ツールではサーバ実装は対象外）
1. `udf-plugin-builder` を使って UDF プラグイン（`.so`）と設定ファイル（`.ini`）をビルド
1. `tsurugi.ini` にプラグインロードパスを設定
1. gRPC サーバを起動
1. SQL から UDF を呼び出す

______________________________________________________________________

## ビルド成果物

`make` を実行すると、以下のファイルが生成されます。

- **プラグイン本体 (.so)**

  - 例: `libmy_udf.so`
  - TsurugiDB がロードする共有ライブラリです。

- **設定ファイル (.ini)**

  - 例: `libmy_udf.ini`
  - `.so` と同じディレクトリに配置され、TsurugiDB が自動的に認識します。
  - 内容は以下の形式です。

```ini
[grpc]
url=localhost:50001
credentials=insecure
```

- `url` … gRPC サーバのエンドポイント (`host:port` 形式)
- `credentials` … 認証方式（現状は `insecure` のみサポート）

注 `.ini` は自分で作成・編集することも可能ですが、デフォルトでは `.so` とペアで生成されるため、そのまま利用できます。

______________________________________________________________________

## .proto 記述ルール（制約）

`udf-plugin-builder` では Protocol Buffers (`proto3`) の全機能は利用できません。\
現在の制約は以下の通りです。

- `syntax = "proto3";` を必ず指定する
- `package tsurugidb` 以下にメッセージを定義してはいけない
- `message` は **第一階層のみ** 定義可能（ネスト禁止、将来対応予定）
- `repeated` は利用不可（将来対応予定）
- `oneof` は引数のみ利用可、戻り値で利用不可（将来対応予定）
- `rpc` メソッドは **Unary RPC** のみ対応（Streaming RPC は非対応）
- **rpc 名は SQL 関数名になるため一意である必要がある**
- 戻り値は単一フィールドのみ対応（将来拡張予定）
- リクエストメッセージのフィールド順 = SQL 関数の引数順

______________________________________________________________________

## 型対応表

| Tsurugi Database | Protocol Buffers 型 |
|------------------|---------------------|
| `INT` | int32, uint32, sint32, fixed32, sfixed32 |
| `BIGINT` | int64, uint64, sint64, fixed64, sfixed64 |
| `BOOLEAN` | bool |
| `REAL` / `FLOAT` | float |
| `DOUBLE` | double |
| `CHAR` / `VARCHAR` / `CHARACTER` / `CHARACTER VARYING` | string |
| `BINARY` / `VARBINARY` / `BINARY VARYING` | bytes |

______________________________________________________________________

## 例

### `.proto` 定義例

`proto/hello.proto`

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

### ビルド方法

```bash
cd udf-plugin-builder
mkdir build && cd build
cmake ..   -DCMAKE_BUILD_TYPE=Release   -DPROTO_PATH="proto"   -DPROTO_FILES="proto/hello.proto"   -DPLUGIN_API_NAME="my_udf"
make
```

______________________________________________________________________

## CMake オプション

| オプション名 | 説明 | 既定値 |
|--------------|------|--------|
| `PROTO_PATH` | `.proto` ファイル検索用ディレクトリ（`-I` と同等） | `proto` |
| `PROTO_FILES` | ビルド対象 `.proto` ファイルリスト（`;` 区切り） | `proto/sample.proto;proto/complex_types.proto;proto/primitive_types.proto` |
| `PLUGIN_API_NAME` | 生成されるライブラリ名 (`lib<name>.so`) | `plugin_api` |
| `GRPC_URL` | `.ini` に埋め込まれる gRPC サーバ URL | `localhost:50051` |

______________________________________________________________________

## PROTO_PATH と PROTO_FILES の指定

- `PROTO_PATH` は protoc の `-I` と同様の意味です。\
  `.proto` ファイル検索用のディレクトリを指定します。
- `PROTO_FILES` はコンパイル対象の `.proto` ファイルのリストです。
- 両方とも **相対パスか絶対パスのどちらかを統一して指定する必要** があります。
  - 例: 相対パスの場合

    ```bash
    -DPROTO_PATH="proto" -DPROTO_FILES="proto/hello.proto"
    ```

  - 例: 絶対パスの場合

    ```bash
    -DPROTO_PATH="/home/user/udf-plugin-builder/proto" -DPROTO_FILES="/home/user/udf-plugin-builder/proto/hello.proto"
    ```

______________________________________________________________________

## Tsurugi Database 設定

1. 生成した `.so` と `.ini` を TsurugiDB のプラグインディレクトリに配置（例: `/home/tsurugidb/plugins`）
1. `tsurugi.ini` にロードパスを追加

```ini
[SQL]
loader_path=/home/tsurugidb/plugins
grpc_url=localhost:50051
```

- `loader_path` はディレクトリまたは単一ファイルを指定可能
- 複数のプラグインを配置可能だが、**rpc 名の競合は禁止**
- tsurugi.iniのgrpc_urlは設定ファイル（`.ini`）が見つからない場合に適用されるgrpc_urlです。

______________________________________________________________________

## UDF 利用例

```sql
CREATE TABLE t (c0 VARCHAR(255));
INSERT INTO t (c0) VALUES ('how are you?');
-- SQL では関数名は大文字小文字を区別しない
SELECT sayhello(c0) FROM t;
```

### 実行結果例

```
sayhello
----------------
how are you? hello
```
