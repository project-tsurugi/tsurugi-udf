# udf-plugin-builder

## 概要

**udf-plugin-builder** は、[Tsurugi Database](https://github.com/project-tsurugi/tsurugidb) 向けの
**UDF (User-Defined Function) プラグイン** を自動生成・ビルドするためのビルドシステムです。

Tsurugi Database の UDF は **gRPC** を利用して外部サービスと通信します。
ユーザーは `.proto` ファイルで関数インターフェースを定義し、`udf-plugin-builder` を用いて
UDF プラグインを生成することで、SQL から外部処理を透過的に呼び出せます。

______________________________________________________________________

## 利用の流れ

1. `.proto` ファイルで UDF のインターフェースを定義
1. gRPC サーバに処理を実装 (本文書では gRPC サーバ実装の詳細には触れません)
1. `udf-plugin-builder` で UDF プラグインをビルド（共有ライブラリ生成）
1. `tsurugi.ini` にプラグインロードパスと gRPC サーバ URL を設定
1. gRPC サーバを起動
1. SQL から UDF を呼び出す

______________________________________________________________________

## .proto 記述規則（制約）

`udf-plugin-builder` では Protocol Buffers (`proto3`) のすべての機能は利用できません。
現在の制約は以下の通りです。

- `syntax = "proto3";` を必ず指定する
- `package tsurugidb` 以下にメッセージを定義してはいけない
- `message` は **第一階層のみ** 定義可能（ネストしたメッセージは不可、将来対応予定）
- `repeated` は利用できない
- `oneof` は利用できない（オーバーロードや可変引数は現状非対応、将来対応予定）
- **rpc 名は SQL 関数名として利用されるため、service や package に関わらず一意である必要がある**
- 戻り値は **単一フィールドのみサポート**（将来的には複数フィールドも対応予定）
- リクエストメッセージの **フィールド定義順** が SQL 関数の引数順に対応する

______________________________________________________________________

## Tsurugi Database 型と Protocol Buffers 型の対応

| Tsurugi Database | Protocol Buffers(Scalar Value Types) |
|------------------|---------------------------------------|
| `INT` | int32, uint32, sint32, fixed32, sfixed32, bool |
| `BIGINT` | int64, uint64, sint64, fixed64, sfixed64 |
| `REAL` | float |
| `FLOAT` | float |
| `DOUBLE` | double |
| `CHAR` | string |
| `CHARACTER` | string |
| `VARCHAR` | string |
| `CHAR VARYING` | string |
| `CHARACTER VARYING` | string |
| `BINARY` | bytes |
| `VARBINARY` | bytes |
| `BINARY VARYING` | bytes |

______________________________________________________________________

## 例

### `.proto` 定義

proto/hello.proto

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
mkdir build
cd build
cmake .. \
  -DPROTO_PATH="proto" \
  -DPROTO_FILES="proto/hello.proto" \
  -DPLUGIN_API_NAME="my_udf"
make
```

______________________________________________________________________

### CMake オプション

| オプション名 | 説明 | 既定値 |
|--------------|------|--------|
| `PROTO_PATH` | `.proto` ファイルが置かれているディレクトリへのパス | `proto` |
| `PROTO_FILES` | コンパイル対象の `.proto` ファイルリスト（`;` 区切り）。2番目以降のファイルは先頭ファイルから import されるものに限定。import されないファイルを指定した場合は未定義動作。 | `proto/sample.proto; proto/complex_types.proto; proto/primitive_types.proto` |
| `PLUGIN_API_NAME` | 生成されるプラグイン API ライブラリのターゲット名（`lib<name>.so` になる） | `plugin_api` |

______________________________________________________________________

## Tsurugi Database 設定

1. 生成した UDF プラグインを、Tsurugi Database を起動するマシン上の任意フォルダに配置 (/home/tsurugidb/plugins)
1. tsurugi.ini に以下を追加してロードパスと gRPC サーバ URL を指定

```ini
[SQL]
loader_path=/home/tsurugidb/plugins
grpc_url=localhost:50051
```

※ loader_path はフォルダまたはファイルを指定可能で、複数プラグインがある場合もロード可能。ただし rpc 名の競合は不可。競合時は起動時にエラーとなる。

______________________________________________________________________

## UDF 利用例

```sql
CREATE TABLE t (c0 VARCHAR(255));
INSERT INTO t (c0) VALUES ('how are you?');
-- SQLでは関数名は大文字小文字を無視して呼び出し可能
SELECT sayhello(c0) FROM t;
```

### 実行結果例

```
sayhello
----------------
how are you? hello
```
