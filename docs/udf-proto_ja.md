# UDF 関数インターフェースの定義

本書では Tsurugi UDF の関数インターフェースを定義するための `.proto` ファイルの記述方法について説明します。

## 概要

Tsurugi UDF では、UDF 関数の定義を Protocol Buffers の [proto3](https://protobuf.dev/programming-guides/proto3/) の仕様に従って `.proto` ファイルで定義します。

UDF 関数の定義と `.proto` のサービス定義との対応はおおよそ以下の通りです。

- UDF 関数の関数名 : RPCメソッド名 ( `rpc` )
- UDF 関数の引数: RPCのリクエストメッセージ ( `message` )
- UDF 関数の戻り値: RPCのレスポンスメッセージ ( `message` )

作成した `.proto` ファイルは、[udf-plugin-builder](./udf-plugin_ja.md) を用いて gRPC クライアントとなる UDF プラグインを生成する際に利用します。また、gRPC サーバ実装においても [gRPC - Python Quick start](https://grpc.io/docs/languages/python/quickstart/) などの手順に従って、同じ `.proto` ファイルを用いて gRPC サーバ用のコードを生成します。

## UDF 関数と `.proto` ファイルの対応

UDF 関数と `.proto` ファイルの定義との対応について、以下に詳細を示します。また Tsurugi UDF で利用するにあたっては 通常の Protocol Buffers の定義に対していくつか追加の制約がありますので、これについても説明します。

説明のために下記 `helloworld.proto` を例として用います。

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

### ファイル全体の定義

- `syntax = "proto3";` をファイルの先頭に必ず指定する
- `package tsurugidb` 以下にメッセージを定義してはいけない
- 単一の `.proto` ファイル内で、複数の `service` ブロックを定義できない

### 関数の定義

- サービスに含む、すべての RPC メソッドが UDF 関数として扱われる
- RPC メソッド名 ( 例では `rpc` に続く `SayHello` や `SayHelloAgain` ) が UDF 関数名として扱われる
  - サービス名 ( 例では `service` に続く `Greeter` ) は無視される
- **RPC メソッド名は Tsurugi に登録する全ての UDF 関数全体で一意**でなければならない。
  - 通常 Protocol Buffers では `package` , `service` が異なる同名のRPCメソッドを定義できるが、Tsurugiではそれらは同名の関数として扱われるため関数名が衝突する。
- `rpc` メソッドは **Unary RPC** のみ対応（Streaming RPC は非対応）
- RPC メソッド名に Tsurugi の予約語 (Reserved words) を指定することはできない
  - Tsurugi の予約語 については、 [Available SQL features in Tsurugi - Reserved words](https://github.com/project-tsurugi/tsurugidb/blob/master/docs/sql-features.md#reserved-words) を参照

### 引数の定義

- RPC のリクエストメッセージ が UDF 関数の引数として扱われる
  - 例では `rpc SayHello (HelloRequest)` の `HelloRequest` が引数型として扱われる
- `message` に定義したメッセージ型の各フィールドが、UDF関数の引数として扱われる
  - データ型の対応付けは次項で紹介する ([データ型の対応付け](#データ型の対応付け))
- リクエストメッセージのフィールドの定義順 が UDF 関数の引数順 に対応する
  - フィールド順と個数は、UDF 関数の引数順と一致する
  - フィールド番号ではなく、テキストの位置で決定する
- `message` のネストは不可
- `oneof` を指定した場合、その選択肢で関数をオーバーロード定義する
- 単一の選択肢からなる `oneof` を指定した場合、新しいオーバーロードは特に定義しない
  - フィールドが設定済みかどうかを判定するために利用する
- `repeated` は指定不可
- `rpc` に指定するリクエストメッセージに Protocol Buffers のスカラー値型や Tsurugi が提供するメッセージ型（`tsurugidb.udf` パッケージに含む型）を直接指定することはできない
  - 例えば `rpc SayHello (tsurugidb.udf.Decimal) ...` のような定義は不可

### 戻り値の定義

- RPC のレスポンスメッセージ がUDF 関数の戻り値として扱われる
  - 例では `rpc SayHello (HelloRequest) returns (HelloReply)` の `HelloReply` が戻り値型として扱われる
- レスポンスメッセージのフィールドは1つでなければならない
  - 指定したフィールドのデータ型が UDF 関数の戻り値型となる
  - データ型の対応付けは次項で紹介する ([データ型の対応付け](#データ型の対応付け))
- `message` のネストは不可
- `oneof` は指定不可
- `repeated` は指定不可
- `rpc` に指定するレスポンスメッセージに Protocol Buffers のスカラー値型や Tsurugi が提供するメッセージ型（`tsurugidb.udf` パッケージに含む型）を直接指定することはできない
  - 例えば `rpc SayHello (HelloRequest) returns (string)` のような定義は不可

## データ型の対応付け

Tsurugi の型（SQL型）と Protocol Buffers の型の対応付けについては、Tsurugi の型が Protocol Buffers の[スカラー値型](https://protobuf.dev/programming-guides/proto3/#scalar) と直接（一対一で）対応する場合と、Tsurugi が提供するメッセージ型 ( `tsurugidb.udf` メッセージ型 ) が対応する場合がそれぞれあります。

以下は、 Tsurugi の型 と Protocol Buffers の型 の対応表です。

| Tsurugi 型 (SQL型) | Protocol Buffers 型 | 備考 |
| ---------------- | ------------------- | ---- |
| `INT` | `int32`, `uint32`, `sint32`, `fixed32`, `sfixed32` | 4byte 整数 |
| `BIGINT` | `int64`, `uint64`, `sint64`, `fixed64`, `sfixed64` | 8byte 整数 |
| `REAL` / `FLOAT` | `float` | 4byte 浮動小数点数 |
| `DOUBLE` | `double` | 8byte 浮動小数点数 |
| `CHAR` / `VARCHAR` / `CHARACTER` / `CHARACTER VARYING` | `string` | 文字列 |
| `BINARY` / `VARBINARY` / `BINARY VARYING` | `bytes` | バイナリデータ |
| `DECIMAL` | `tsurugidb.udf.Decimal` | 10進型 |
| `DATE` | `tsurugidb.udf.Date` | 日付 |
| `TIME` | `tsurugidb.udf.LocalTime` | ローカル時刻 |
| `TIMESTAMP` | `tsurugidb.udf.LocalDatetime` | ローカル日時 |
| `TIMESTAMP WITH TIME ZONE` | `tsurugidb.udf.OffsetDatetime` | タイムゾーン付き日時 |
| `BLOB` | `tsurugidb.udf.BlobReference` | BLOB参照 |
| `CLOB` | `tsurugidb.udf.ClobReference` | CLOB参照 |

### `tsurugidb.udf` メッセージ型

`tsurugidb.udf` メッセージ型は [tsurugi_types.proto](https://github.com/project-tsurugi/tsurugi-udf/blob/master/proto/tsurugidb/udf/tsurugi_types.proto) に定義されています。

`tsurugi-udf` のソースアーカイブには `proto/tsurugidb/udf/tsurugi_types.proto` に配置されています。

### `tsurugidb.udf` メッセージ型の利用例

`tsurugidb.udf` メッセージ型を利用する場合は、`.proto` ファイル内で `import "tsurugidb/udf/tsurugi_types.proto";` を指定し、当該ファイルをインポートしてください。

以下は `DECIMAL` 型を引数と戻り値に指定したUDF 関数の定義例です。

`decimal_use.proto`

```proto
syntax = "proto3";

import "tsurugidb/udf/tsurugi_types.proto";

service UseDecimal {
    rpc Log10(DecimalOne) returns (DecimalOne);
}

message DecimalOne {
    tsurugidb.udf.Decimal value = 1;
}
```

[gRPC - Python Quick start](https://grpc.io/docs/languages/python/quickstart/) などの手順に従って、 `grpc_tools` を使ってPython 用の gRPC サーバコードを生成する場合、 `tsurugi-udf/proto` ディレクトリを `-I` オプションでインポートパスとして指定する必要があります。

```sh
python -m grpc_tools.protoc -I. -I/path/to/tsurugi-udf/proto --python_out=. --grpc_python_out=. my.proto
```

また、 `udf-plugin-builder` を用いて UDF プラグインを生成する場合、オプションで `tsurugi_types.proto` を利用可能にするよう指定する必要があります。詳しくは [udf-plugin - `tsurugidb.udf` メッセージ型 の利用](./udf-plugin_ja.md#tsurugidbudf-メッセージ型-の利用) を参照してください。

### NULL 値の扱い

Tsurugi UDF では Protocol Buffers (proto3) の `optional` フィールドを利用して、引数や戻り値が NULL 値を取ることができるように定義できます。

`optional` は、フィールドが「設定されているかどうか」を判定できる仕組みです。
Tsurugi UDF では `optional` を指定したフィールドは、Tsurugi上で `NULL` を許容します。

- 引数メッセージのフィールドに `optional` を指定した場合、その引数には SQL から `NULL` を指定できます。
- 戻り値メッセージのフィールドに `optional` を指定した場合、その戻り値として SQL 上の `NULL` を返すことができます。

なお、`NULL` を表すために Tsurugi UDF 独自の型や特別な値を使用するわけではありません。
`optional` フィールドの「未設定状態」を、Tsurugi UDF が SQL の `NULL` として扱います。

#### 引数で NULL を受け取る場合

UDF の引数メッセージに `optional` を指定すると、その引数には SQL から `NULL` を指定できます。

##### proto 定義例

```proto
syntax = "proto3";

message Check {
  optional int64 int64_value = 1;
}

message Result {
  int64 value = 1;
}

service Sample {
  rpc test(Check) returns (Result);
}
```

##### SQL 例

```sql
SELECT test(NULL) FROM ...
```

この場合、`Check.int64_value` は未設定の状態として UDF サーバに渡されます。

UDF サーバ側では、対象フィールドが設定されているかどうかを確認して処理してください。

##### Python によるgRPCサーバ側の実装例

```python
def test(self, request, context):
    if request.HasField("int64_value"):
        # NULL ではない値が指定された場合
        value = request.int64_value
    else:
        # SQL から NULL が指定された場合
        value = None

    response = sample_pb2.Result()
    response.value = 0 if value is None else value
    return response
```

#### 戻り値で NULL を返す場合

戻り値メッセージのフィールドに `optional` を指定すると、その戻り値として `NULL` を返すことができます。

##### proto 定義例

```proto
syntax = "proto3";

message Check {
  int64 int64_value = 1;
}

message Result {
  optional int64 int64_value = 1;
}

service Sample {
  rpc test(Check) returns (Result);
}
```

##### Python によるgRPCサーバ側の実装例

Python の protobuf では、`NULL` という値を明示的に代入するのではなく、対象フィールドを設定しないことで `NULL` を表現します。

```python
def test(self, request, context):
    response = sample_pb2.Result()

    # NULL を返したい場合は int64_value を設定しない
    return response
```

値を返す場合は、通常どおりフィールドに値を設定します。

```python
def test(self, request, context):
    response = sample_pb2.Result()
    response.int64_value = 123
    return response
```

#### APPLY演算子の戻り値で NULL を返す場合

APPLY演算子で複数行を返す場合も、`optional` フィールドを設定しないことで、その行の値を `NULL` として返せます。

##### Python によるgRPCサーバ側の実装例

```python
def _copy_if_present(src, dst) -> None:
    if src.HasField("b_1"):
        dst.b_1 = src.b_1


def return_func_stream(self, request, context):
    for i in range(5):
        response = return_pb2.bytebyte()

        if i < 4:
            _copy_if_present(request, response)

        # i == 4 の最後の1件は何もセットしない
        # そのため SQL 上では NULL として返却される

        yield response
```

##### 返却結果例

```json
{"value":[1,2,3,4]}
{"value":[1,2,3,4]}
{"value":[1,2,3,4]}
{"value":[1,2,3,4]}
{"value":null}
```

#### エラーメッセージ例

`optional` を指定しないフィールドに対して `NULL` を引数に指定した場合、以下のメッセージが出力されます。
```text
VALUE_EVALUATION_EXCEPTION
(SQL-02011: an error (unknown) occurred:
[diagnostic(code=invalid_input_value,
message='関数名 : arguments #引数番号,#引数番号... must not be NULL')])
```

例えば、第2引数と第3引数が `NULL` を許容しない場合は、次のように引数位置が表示されます。

```text
arguments #2, #3 must not be NULL
```

`optional` を指定した場合は引数に `NULL` を指定してもエラーにはなりません。

#### 補足

proto3 の仕様上、`oneof` 内のフィールドに `optional` を指定することはできません。

そのため、`oneof` の選択肢そのものに `optional` を付けて `NULL` を許容することはできません。
`NULL` を許容したい場合は、`oneof` ではなく `optional` フィールドとして定義してください。

なお、同一メッセージ内に `optional` フィールドと `oneof` を別々に定義することは可能です。
