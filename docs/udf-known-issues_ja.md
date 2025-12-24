# Tsurugi UDF 既知の問題

## 既知の問題

本書では、Tsurugi UDF に関する既知の問題について説明します。
特別な記載が無い限り、これらの問題は将来のバージョンで修正、もしくは制限を緩和する対応を計画しています。

### `tsurugidb.udf` メッセージ型を含むUDF プラグインを複数デプロイすることができない

**問題:**

`tsurugidb.udf` メッセージ型を利用するUDF プラグイン ( `tsurugi_types.proto` をインポートしているUDF プラグイン) を複数デプロイすると、Tsurugi 起動時に以下のようなエラーが発生し、Tsurugi の起動に失敗します。

```
[libprotobuf ERROR google/protobuf/descriptor_database.cc:120] File already exists in database: tsurugidb/udf/tsurugi_types.proto
[libprotobuf FATAL google/protobuf/descriptor.cc:1382] CHECK failed: GeneratedDatabase()->Add(encoded_file_descriptor, size):
terminate called after throwing an instance of 'google::protobuf::FatalException'
  what():  CHECK failed: GeneratedDatabase()->Add(encoded_file_descriptor, size):
```

> [!NOTE]
> **ワークアラウンド:**
> `tsurugidb.udf` メッセージ型を利用するUDFは1つのUDF プラグインにまとめて生成してデプロイしてください。

### 複数の引数にoneofを使用できない

**問題:**

protoのメッセージ定義の複数のフィールドにそれぞれ `oneof` を使った定義を行い、UDF呼び出し時に引数に対してそれぞれ異なる型を指定すると、以下のようなエラーが発生しUDFの実行に失敗します。


```proto
message NumericOneOfTwo {
  oneof f1 {
    int32 f1_int32 = 1;
    int64 f1_int64 = 2;
    float f1_float = 3;
    double f1_double = 4;
  }
  oneof f2 {
    int32 f2_int32 = 5;
    int64 f2_int64 = 6;
    float f2_float = 7;
    double f2_double = 8;
  }
}
message BigintValue {
  int64 value = 1;
}

service Types {
    rpc NumericAdd(NumericOneOfTwo) returns (BigintValue);
}
```

```sql
> SELECT NumericAdd(c_int, 100::bigint) FROM t_types ORDER BY pk ASC;
[@#0: BIGINT]
VALUE_EVALUATION_EXCEPTION (SQL-02011: an error (undefined) occurred:[diagnostic(code=undefined, message='unexpected error occurred during expression evaluation:Multiple fields selected in oneof group 0')])
```

### `NULL` 値に未対応

現時点の Tsurugi UDF では、引数および戻り値に `NULL` 値を指定することはできません。

UDF の引数値が `NULL` の場合、関数呼び出しは gRPC サービス呼び出し前にバリデーションエラーで例外が発生します。
エラーを回避するには `COALESCE` 関数などを利用して `NULL` 値を変換する、もしくは UDF に `NULL` 値が渡されないように呼び出し側で制御してください。

UDF の戻り値については、 Tsurugi UDF では gRPC サービスから `NULL` 値を返却する機能は提供していません。また現時点の Tsurugi UDF は `.proto` の  `optional` フィールドに未対応であるため、レスポンスメッセージのフィールド値を未設定することもできません。

なお、`NULL` 値に関するこれらの制約は、今後のリリースで `.proto` の `optional` フィールドのサポートとともに緩和することを計画しています。

現状の UDF 関数の引数、および戻り値の定義に関する制約の詳細については、 [UDF 関数インターフェースの定義](./udf-proto_ja.md) を参照してください。

### Secure gRPC 通信に未対応

**問題:**

現時点の Tsurugi UDF では、gRPC サービスとの通信にセキュアな通信路 (TLS/SSL) を利用することはできません。
Insecure gRPC 通信のみサポートしています。

UDF に対応する gRPC サーバーは、Insecure gRPC 通信を指定して実行してください。

### クライアントタイムアウト設定に未対応

**問題:**

現時点の Tsurugi UDF では、gRPC クライアントのタイムアウト設定に対応していません。
