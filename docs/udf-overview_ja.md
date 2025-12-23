# Tsurugi UDF 概要

本書では Tsurugi の ユーザー定義関数 (UDF: User Defined Function) の概要を説明します。

UDF は、外部で作成したプログラムを Tsurugi の関数として呼び出すための仕組みです。
Tsurugi では [gRPC] で作成したプログラムを UDF として登録することで、SQL からほかの関数と同様に呼び出すことができます。

[gRPC]: https://grpc.io/
[Tsurugi UDF ユーザガイド]:./udf-guide_ja.md
[UDF 関数インターフェースの定義]:./udf-proto_ja.md
[udf-plugin]:./udf-plugin_ja.md
[udf-library (for Python)]:./udf-library_ja.md
[Tsurugi UDF 既知の制約]:./udf-known-issues_ja.md

## ビルトイン関数とユーザー定義関数

TsurugiではSQLから利用可能な、あらかじめ組み込まれた [ビルトイン関数](https://github.com/project-tsurugi/tsurugidb/blob/master/docs/sql-features.md#functions) を提供しています。
ビルトイン関数はSQLから以下のように呼び出すことができます。

```sql
-- 文字列の長さを返すビルトイン関数 "CHARACTER_LENGTH" を呼び出す
tgsql> SELECT c0, CHARACTER_LENGTH(c0) FROM t;
[c0: VARCHAR(255), @#1: BIGINT]
[World, 5]
[TsurugiDB, 9]
```

SQL やビルトイン関数の組み合わせで多くの処理を実現可能ですが、複雑な処理や GPU などの外部のデバイスを利用する処理を行いたい場合、ユーザー定義関数 (UDF) を利用できます。
UDF は Tsurugi の外部にプログラムを作成し、それを Tsurugi から呼び出す方式なので、Tsurugi 内部では実現が難しい処理も柔軟に実装できます。

```sql
-- 挨拶を返す UDF "SayHello" を呼び出す
tgsql> SELECT SayHello(c0) FROM t;
[@#0: VARCHAR(*)]
[Hello, World!]
[Hello, TsurugiDB!]
```

以降、 Tsurugi が提供する UDF 機能 を **Tsurugi UDF** と呼称します。

## Tsurugi UDF の特徴 - gRPC と UDFプラグイン

Tsurugi UDFでは、UDF の実行環境に [gRPC] を利用します。

UDF の本体を gRPC サービスとして記述し、Tsurugi からはそのサービスを UDF として呼び出します。

gRPC メソッドは Python, Java, C++, Rust などの様々な言語で実装可能で、様々なエコシステムを活用できます。

また、gRPC サービスを Tsurugi と異なるコンピューター上で動作させ、 Tsurugi からはネットワークを介して gRPC サービスを呼び出すことも可能です。
例えば、GPU を搭載したサーバ上に gRPC サービスを配備し、Tsurugi からはそのサーバ上の gRPC サービスを UDF として呼び出すことで、ほかのノードの GPU を利用した処理を簡単に実行できます。

さらに、関数ごとに UDF 実行環境を異なる環境上に配備することも可能であるため、柔軟で拡張性の高いシステム構成を実現することが可能です。

### Tsurugi UDF の構成要素

Tsurugi UDF の構成は次のようになります。

- UDFの提供者（開発者）は、UDF を **gRPC サービス** として提供する。
  - gRPC サービス を実装する上で、その実装言語や実行環境は問いません。
  - 実装した gRPC サービス を **gRPC サーバ** として実行します。
- Tsurugi本体は、UDF を提供する gRPC サービス に対する **gRPC クライアント** として振る舞う。
  - SQL 内で UDF を呼び出すと、Tsurugiは UDF に対応する gRPC サービス を呼び出し、必要な処理を実行します。
  - gRPC サービスから返された応答を、UDF実行の戻り値として利用します。

この構成において gRPC クライアント を担う Tsurugiの拡張機能が **UDF プラグイン** です。

UDFプラグイン は gRPC サービス を定義した `.proto` ファイルをもとに、Tsurugi UDFが提供する `udf-plugin-builder` コマンドから生成します（詳細は [udf-plugin](./udf-plugin_ja.md) を参照）。
生成した UDF プラグインを Tsurugi に登録することで UDF が利用可能になります。

## サポートする UDF の機能

Tsurugi UDF では、以下の機能をサポートしています。

### 関数インターフェースのサポート

**現在サポートしている機能:**

- ユーザー定義関数（UDF）: スカラー関数として実行するUDFです。単一行に対して単一の値を返します。

**今後サポート予定の機能:**

以下の機能については、現時点では Tsurugi UDF ではサポートしていません。
将来のリリースでのサポートを予定しています。

- ユーザー定義集計関数（UDAF）: 集計関数として実行するUDF。複数行に対して単一の値、または単一の列を返します。
- ユーザー定義表関数（UDTF）: 表関数として実行するUDF。単一行に対して複数の値、または複数のレコード型を返します。

### RPC タイプのサポート

gRPC サービスを定義する際に、それぞれの gRPC メソッドはいくつかの RPC タイプを利用できます。

**現在サポートしている機能:**

- Unary RPC: クライアントがリクエストを送信し、サーバーがそれに対する1つのレスポンスを返す、基本的な通信方式です。スカラー関数の UDF として利用できます。

**今後サポート予定の機能:**

以下の機能については、現時点では Tsurugi UDF ではサポートしていません。
いくつかは将来のリリースでのサポートを予定しています。

- Server Streaming RPC: クライアントがリクエストを送信し、サーバーが複数のレスポンスをストリームとして返す通信方式です。表関数の UDF (UDTF) として利用できます。
- Client Streaming RPC: クライアントが複数のリクエストをストリームとして送信し、サーバーが1つのレスポンスを返す通信方式です。集計関数の UDF (UDAF) として利用できます。
- Bidirectional Streaming RPC: クライアントとサーバーが双方向にストリームを介してメッセージを交換する通信方式です。集計を伴う表関数の UDF として利用できます。

詳細については、 [UDF 関数インターフェースの定義] を参照してください。

### データ型のサポート

Tsurugi UDF では、SQL から UDF を呼び出す際に引数リストに指定されたデータを gRPC リクエストメッセージに変換し、またレスポンスメッセージを SQL の戻り値に変換します。

Tsurugi の SQL がサポートする主要なデータ型を gRPC メッセージとしてサポートしています。

**現在サポートしている機能:**

- `INT`
- `BIGINT`
- `REAL`
- `DOUBLE`
- `CHAR`
- `VARCHAR`
- `BINARY`
- `VARBINARY`
- `DECIMAL`
- `DATE`
- `TIME`
- `TIMESTAMP`
- `TIMESTAMP WITH TIME ZONE`
- `BLOB`
- `CLOB`

**今後サポート予定の機能:**

- `BOOLEAN`
- `ARRAY` (配列型)
- `ROW` (レコード型)
- `NULL` 値

詳細については、[UDF 関数インターフェースの定義] の「データ型の対応付け」セクションを参照してください。

### BLOB / CLOB データのサポート

Tsurugi UDF では、BLOB や CLOB などの大容量のデータ型を取り扱うことができます。

gRPC はリクエストやレスポンスにサイズ制限があるため、あまり大容量のデータを直接送受信することはできませんが、
Tsurugi UDF では BLOB や CLOB を軽量な参照として gRPC メッセージで送受信し、実際のデータは Tsurugi 側で管理する仕組みを提供しています。

gRPC サービスからは、Tsurugi が提供する専用のクライアントライブラリを利用して、BLOB や CLOB のデータを読み書きできます。

詳細については [udf-library (for Python)] の「BLOB / CLOB データの取り扱い」セクションを参照してください。

## UDF ドキュメント

Tsurugi UDF の使い方については、以下のドキュメントを参照してください。

- [Tsurugi UDF ユーザガイド] - Tsurugi UDF の基本的な利用方法とその流れについて説明しています。Tsurugi UDF をはじめて利用する場合、まずはこちらのドキュメントを参照してください。
- [UDF 関数インターフェースの定義] : Tsurugi UDF の関数インターフェースを定義するための `.proto` ファイルの記述方法について説明します。
- [udf-plugin] : UDFプラグイン を生成、管理するための各ツールについて説明します。
- [udf-library (for Python)] : PythonでUDFのgRPCサービスを実装する際に利用する、Pythonライブラリの利用方法について説明します。
- [Tsurugi UDF 既知の制約] : Tsurugi UDF の既知の制約事項について説明します。
