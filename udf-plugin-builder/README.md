# udf-plugin-builder

## 概要

**udf-plugin-builder** は、[Tsurugi Database](https://github.com/project-tsurugi/tsurugidb) 向けの\
**UDF (User-Defined Function) プラグイン**と**プラグイン設定ファイル**を自動生成するツールです。

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

`udf-plugin-builder` を実行すると、以下のファイルが生成されます。

- **プラグイン本体 (.so)**

  - 例: `libmy_udf.so`
  - TsurugiDB がロードする共有ライブラリです。

- **設定ファイル (.ini)**

  - 例: `libmy_udf.ini`
  - `.so` と同じディレクトリに配置され、TsurugiDB が自動的に認識します。
  - 内容は以下の形式です。

```ini
[udf]
enabled=true
endpoint=localhost:50002
secure=false
```

- `enabled` .soを読み込むか否か？
- `endpoint` … gRPC サーバのエンドポイント (`host:port` 形式)
- `secure` … 認証方式（現状は `false` のみサポート）

注 `.ini` は自分で作成・編集することも可能ですが、デフォルトでは `.so` とペアで生成されるため、そのまま利用できます。

______________________________________________________________________

## .proto 記述ルール（制約）

`udf-plugin-builder` では Protocol Buffers (`proto3`) の全機能は利用できません。\
現在の制約は以下の通りです。

- `syntax = "proto3";` を必ず指定する
- `package tsurugidb` 以下にメッセージを定義してはいけない
- `message` は **第二階層まで** 定義可能（第三階層以降は非対応）
- `repeated` は利用不可（将来対応予定）
- `oneof` は利用可
- `rpc` メソッドは **Unary RPC** のみ対応（Streaming RPC は非対応）
- **rpc 名は SQL 関数名になるため一意である必要がある**
- 戻り値は複数指定不可
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

### インストール方法

```bash
cd tsurugi-udf
cd udf-plugin-builder
pip install .
```

______________________________________________________________________

## CMake オプション

| オプション               | 型                   | デフォルト値                               | 説明                                                                                                                                                 |
| :------------------ | :------------------ | :----------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--proto_file`      | 複数指定可| `proto/sample.proto`                 | ビルド対象の `.proto` ファイルを指定します。複数ファイルをスペース区切りで指定可能です。<br>例：<br>`--proto_file proto/sample.proto proto/complex_types.proto proto/primitive_types.proto` |
| `--proto_path`      | 文字列                 | `なし`（未指定時は最初の `.proto` のディレクトリを使用） | `.proto` ファイルを含むディレクトリを指定します。`protoc` が依存ファイルを解決する際に使用されます。                                                                                        |
| `--tmp`             | 文字列                 | `"tmp"`                              | 一時的なビルド用ディレクトリを指定します。ビルド後は自動的に削除されます。                                                                                                              |
| `--plugin_api_name` | 文字列                 | `"plugin_api"`                       | 出力されるプラグインライブラリの名前を指定します。<br>例：`--plugin_api_name my_udf` → 出力ファイル名は `libmy_udf.so` / `libmy_udf.ini` になります。                                       |
| `--grpc_url`        | 文字列                 | `"localhost:50051"`                  | gRPC サーバーの URL を指定します（CMake に渡される設定値として利用されます）。                                                                                                    |

______________________________________________________________________

## Tsurugi Database 設定

1. 生成した `.so` と `.ini` を TsurugiDB のプラグインディレクトリに配置（例: `/home/tsurugidb/plugins`）
1. `tsurugi.ini` にロードパスを追加

```ini
[udf]
    plugin_directory=/home/nishimura/grpc
    endpoint=localhost:50051
    secure=false
```

- `plugin_directory` はディレクトリを指定
- 複数のプラグインを配置可能だが、**rpc 名の競合は禁止**
- tsurugi.iniのendpointおよびsecureは個別設定ファイル（`.ini`）で指定されていない場合に適用されるgrpc_urlです。

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
