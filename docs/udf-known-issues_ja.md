# Tsurugi UDF 既知の問題

## 既知の問題

本書では、Tsurugi UDF に関する既知の問題について説明します。
特別な記載が無い限り、これらの問題は将来のバージョンで修正、もしくは制限を緩和する対応を計画しています。

### 同一の `message` 名を持つ複数のUDFプラグインをデプロイしてTsurugiを起動すると不正終了する。

**問題:**

同一パッケージ上の複数の `.proto` ファイルから同一の `message` 名を持つUDFプラグイン生成、デプロイしてTsurugiを起動すると起動エラーとなります。

これ自体は [UDF 関数インターフェースの定義](./udf-proto_ja.md) にも記載している通り仕様上の制約ですが、起動エラーとなった場合、Tsurugiが正しい起動エラーシーケンスを経ずに不正に終了してしまうため、 `/dev/shm` や `/var/lock` ( `tsurugi.ini` の `pid_directory` ディレクトリ配下 ) などにロックファイルやプロセスIDファイルが残ってしまい、次回以降の起動やクライアントからの接続時に想定外のエラーや動作を引き起こす可能性があります。

本問題が発生した場合、以下のようなエラーが `tgctl start` 実行プロセスの標準エラー出力に出力されます。

```
[libprotobuf ERROR google/protobuf/descriptor_database.cc:175] Symbol name "DummyDuplicateMessage" conflicts with the existing symbol "DummyDuplicateMessage".
[libprotobuf FATAL google/protobuf/descriptor.cc:1382] CHECK failed: GeneratedDatabase()->Add(encoded_file_descriptor, size):
terminate called after throwing an instance of 'google::protobuf::FatalException'
  what():  CHECK failed: GeneratedDatabase()->Add(encoded_file_descriptor, size):
** Aborted at 1771925242 (unix time) try "date -d @1771925242" if you are using GNU date ***
PC: @                0x0 (unknown)
*** SIGABRT (@0x3e80003497b) received by PID 215419 (TID 0x750b77135880) from PID 215419; stack trace: ***
...
```

UDFプラグインのロード処理はトランザクションログの読み込み処理が終わった後に実行されるため、トランザクションログのサイズが大きい場合は長時間のトランザクションログの読み込み処理がかかった後に上記の起動エラーが発生することになります。この点からも、UDFプラグインをデプロイする際にはこの制約に該当しないよう注意してください。

また、このエラーが発生した後は、Tsurugiのプロセス (`tsurugidb` プロセス)が停止していることを確認した上で、 `/dev/shm` や `/var/lock` ( `tsurugi.ini` の `pid_directory` ディレクトリ配下 ) などにロックファイルやプロセスIDファイルが残っていないか確認し、もし残っている場合は削除してください。

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

### クライアントタイムアウト設定に未対応

**問題:**

現時点の Tsurugi UDF では、gRPC クライアントのタイムアウト設定に対応していません。
