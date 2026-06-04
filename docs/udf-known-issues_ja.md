# Tsurugi UDF 既知の問題

## 既知の問題

本書では、Tsurugi UDF に関する既知の問題について説明します。
特別な記載が無い限り、これらの問題は将来のバージョンで修正、もしくは制限を緩和する対応を計画しています。

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

### クライアントタイムアウト設定に未対応

**問題:**

現時点の Tsurugi UDF では、gRPC クライアントのタイムアウト設定に対応していません。
