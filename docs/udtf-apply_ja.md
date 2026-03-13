# ユーザー定義表値関数 (UDTF)

本書では Tsurugi UDF のユーザー定義表値関数 (UDTF: User-Defined Table-valued Function) の概要と利用方法について説明します。

## UDTF とは

[Tsurugi UDF ユーザガイド](./udf-guide_ja.md) で説明しているUDF（または UDSF: User-Defined Scalar Function）は、スカラー値を引数として受け取り、1つのスカラー値を返す関数です。元となるテーブルの各行に対して1度呼び出され、1つの結果値を返します。

これに対して、UDTF はスカラー値を引数として受け取り、複数行・複数列の表値（テーブル）を返す関数です。元となるテーブルの各行に対して1度呼び出され、0行以上の表値を返します。

UDTF は `APPLY` 演算子を使って SQL から呼び出します。

```sql
SELECT * FROM t1 APPLY f(t1.a, t1.b) AS u1
```

## APPLY 演算子

`APPLY` 演算子は Tsurugi 独自の SQL 拡張構文です（T-SQL 方言を参考にしています）。SQL 標準には存在せず、SQL 標準の `JOIN LATERAL` の限定版に相当します。

```sql
SELECT <列リスト>
FROM <左表>
[CROSS | OUTER] APPLY <表値関数呼び出し> [AS] <エイリアス名>
```

- `CROSS APPLY`（デフォルト）: 表値関数の結果が空の場合、左表のその行を**出力しない**
  - SQL 標準の `INNER JOIN LATERAL ... ON TRUE` に相当
- `OUTER APPLY`: 表値関数の結果が空の場合、左表のその行を**保持**し、右表側の列は `NULL` で埋める
  - SQL 標準の `LEFT OUTER JOIN LATERAL ... ON TRUE` に相当
- `APPLY` の型指定を省略した場合は `CROSS APPLY` として動作する

### `CROSS APPLY`

**カンマ区切りのタグを行に展開する**というシンプルな UDTF を使って、`APPLY` 構文の動きを確認します。

テーブル `products`:

| product_id | name     | tags            |
|------------|----------|-----------------|
| 1          | Apple    | food,fresh,sale |
| 2          | Notebook | stationery      |
| 3          | Eraser   | （空文字）      |

カンマ区切り文字列を要素ごとに行に展開する `Split` UDTF を `APPLY` 演算子で呼び出します。

```sql
tgsql> SELECT p.product_id, p.name, t.item AS tag, t.pos
FROM products AS p
CROSS APPLY Split(p.tags) AS t

[product_id: INT, name: VARCHAR(*), tag: VARCHAR(*), pos: INT]
[1, Apple, food, 1]
[1, Apple, fresh, 2]
[1, Apple, sale, 3]
[2, Notebook, stationery, 1]
```

`products` の 1 行が、`tags` の要素数だけ行に展開されています。
`Split` の結果が空（タグなし）だった product_id=3 の行は、デフォルトの `APPLY` (`CROSS APPLY`) の動作により出力されません。

### `OUTER APPLY`

`OUTER APPLY` を指定すると、結果が空の行も保持され、右表側の列が `NULL` になります。

```sql
SELECT p.product_id, p.name, t.item AS tag, t.pos
FROM products AS p
OUTER APPLY Split(p.tags) AS t

[product_id: INT, name: VARCHAR(*), tag: VARCHAR(*), pos: INT]
[1, Apple, food, 1]
[1, Apple, fresh, 2]
[1, Apple, sale, 3]
[2, Notebook, stationery, 1]
[3, Eraser, NULL, NULL]
```

### `APPLY` 演算子を指定可能な位置

UDSF と UDTF では、SQL 文中で指定できる位置が異なります。

UDSF は**値式** (`value-expression`) として扱われるため、`SELECT` 句・`WHERE` 句・`HAVING` 句など、値を記述できる場所であればどこでも使用できます。

```sql
-- SELECT 句での UDSF 呼び出し: 各商品のタグ数を算出する
tgsql> SELECT product_id, name, TagCount(tags) AS tag_count FROM products;
[product_id: INT, name: VARCHAR(*), tag_count: INT]
[1, Apple, 3]
[2, Notebook, 1]
[3, Eraser, 0]

-- WHERE 句での UDSF 呼び出し: タグが 2 個以上の商品に絞り込む
tgsql> SELECT product_id, name FROM products WHERE TagCount(tags) >= 2;
[product_id: INT, name: VARCHAR(*)]
[1, Apple]
```

一方、UDTF は `APPLY` 演算子を介して**テーブル参照** (`table-reference`) として扱われるため、`FROM` 句のテーブル参照の位置で指定できます。
`APPLY` 演算子は `JOIN` などほかのテーブル参照と組み合わせて使用することもできます。

```sql
-- FROM 句での UDTF 呼び出し: タグを行に展開する
-- JOIN と組み合わせて、タグの説明をタグマスタから取得する
SELECT p.product_id, p.name, t.item AS tag, m.description
FROM products AS p
APPLY Split(p.tags) AS t
JOIN tag_master AS m ON t.item = m.tag_name

[product_id: INT, name: VARCHAR(*), tag: VARCHAR(*), description: VARCHAR(*)]
[1, Apple, food, "Food category"]
[1, Apple, fresh, "Freshness category"]
[1, Apple, sale, "Sale category"]
[2, Notebook, stationery, "Stationery category"]
```

UDSFとUDTFの違いについて、以下の表にまとめます。

| 種別 | 引数 | 戻り値 | SQL 構文上の位置 | SQL での呼び出し例 |
|------|------|--------|----------------|-----------------|
| UDSF | スカラー値（0個以上）| スカラー値（1値）| 値式 (`value-expression`) | `SELECT f(x) FROM t` |
| UDTF | スカラー値（0個以上）| 表値（0行以上）  | テーブル参照 (`table-reference`) | `SELECT * FROM t APPLY f(x) AS u` |

> [!NOTE]
> SQL構文の詳細は [Available SQL features in Tsurugi](https://github.com/project-tsurugi/tsurugidb/blob/master/docs/sql-features.md) を参照してください。

## UDTF のユースケース例

ここでは UDTF のユースケース例をいくつか紹介します。

### 不特定な件数を返す負荷の高い処理

UDTF が特に力を発揮するのが、1行の入力に対して不特定な複数行の結果を返す必要がある処理や、負荷の高い処理を呼び出す必要がある処理です。

例えば画像データのテーブルに対して物体検出モデルの推論処理を実行し、検出された物体の一覧（物体の種別・スコア・位置）を返す UDTF を考えます。
1枚の画像から複数の物体が検出される可能性があるため、1行の入力に対して結果が複数行になります。

```sql
-- images テーブルの各行に対して物体検出 UDTF をバッチ適用する
SELECT i.image_id, d.label, d.score, d.x, d.y, d.width, d.height
FROM images AS i
APPLY DetectObjects(i.image_data) AS d
WHERE d.score >= 0.8
```

物体検出のような「検出物体数が画像によって異なる」SQLに組み込むには、対象行に対して可変件数の行を返せる UDTF が適しています。

また、 `APPLY` 演算子は gRPC サーバーストリーミングを利用するため、データ転送における大容量データの低遅延性、メモリ効率性などの点で優れたパフォーマンスを発揮します。

### データの一括登録

`APPLY` の結果は通常の `SELECT` 結果と同じように扱えるため、 `INSERT INTO ... SELECT` と組み合わせることで UDTF の出力を別テーブルへ一括登録できます。

物体検出 UDTF を使って、推論結果を `detections` テーブルへ一括書き込む例を示します。

```sql
-- UDTF の推論結果を detections テーブルへ一括登録する
INSERT INTO detections (image_id, label, score, x, y, width, height)
SELECT i.image_id, d.label, d.score, d.x, d.y, d.width, d.height
FROM images AS i
APPLY DetectObjects(i.image_data) AS d
WHERE d.score >= 0.8
```

このSQLを実行すると、 `images` テーブルの全行に対してバッチ推論を実行し、スコアが 0.8 以上の検出結果を `detections` テーブルに書き込みます。

## UDTF 用のgRPCサービスの定義

UDTF 用のgRPCサービスの全体的な定義や実装方法は、以下の点が UDSF 用のものと異なります:
- `.proto` ファイルの定義で、 対応するRPCメソッドを Server Streaming RPC として定義する
  - レスポンスメッセージの定義で `stream` キーワードを付与する
- レスポンスメッセージに複数フィールドを指定することが可能
- gRPCサービスの実装において、Server Streaming RPC に対応する方法でレスポンスを返す

### UDTF の `.proto` ファイル定義

UDTF は gRPC の **Server Streaming RPC** として定義します。
レスポンスメッセージの定義に `stream` キーワードを付与することで UDTF として扱われます。

```proto
syntax = "proto3";

service CsvExpander {
  // UDTF: カンマ区切り文字列を受け取り、各要素と位置をストリームとして返す
  rpc Split (SplitRequest) returns (stream SplitResponse);
}

message SplitRequest {
  string text = 1;
}

message SplitResponse {
  string item     = 1;  // 要素の値    （出力表の第1列）
  int32  pos = 2;  // 要素の位置  （出力表の第2列）
}
```

`rpc` メソッドのレスポンスに `stream` キーワードが付与されている点が UDSF との唯一の違いです。
gRPCサーバ側の実装では、このメソッドが 1つの行を生成するたびにレスポンスを送信し、すべての行を送信し終えたらストリームを終了します。

### 戻り値の定義

UDTF の戻り値の定義は、通常のUDF(UDSF) の戻り値の定義といくつかの点で異なります:

- RPC のレスポンスメッセージ がUDTF 関数の戻り値となる出力表の各行として扱われる
- レスポンスメッセージには `stream` キーワードを付与する必要がある
- レスポンスメッセージのフィールドは **1つ以上** でなければならない
- 各フィールドの **名前**が出力表の**列名**になる
- 各フィールドの**定義順**が出力表の**列順**になる
- 各フィールドの**データ型**が出力表の各列の**データ型**になる
  - データ型の対応付けは UDSF と同様 ([UDF 関数インターフェースの定義](./udf-proto_ja.md) の「データ型の対応付け」を参照)
- `message` のネストは不可
- `oneof` は指定不可
- `optional` は指定不可
- `repeated` は指定不可
- `rpc` に指定するレスポンスメッセージに Protocol Buffers のスカラー値型や Tsurugi が提供するメッセージ型（`tsurugidb.udf` パッケージに含む型）を直接指定することはできない
  - 例えば `rpc Split (SplitRequest) returns (stream string)` のような定義は不可

その他の定義ルールやUDFプラグインの生成方法については UDSF と同様です。詳しくは [UDF 関数インターフェースの定義](./udf-proto_ja.md) や [udf-plugin](./udf-plugin_ja.md) を参照してください。

### gRPCサービスの実装

UDTF に対応する gRPCサービスの実装 では、Server Streaming RPC に対応する方法でレスポンスを返す必要があります。
各言語のgRPCサービスの実装方法については、以下のドキュメントなどを参照してください。
- [Python](https://grpc.io/docs/languages/python/basics/#response-streaming-rpc)
- [Java](https://grpc.io/docs/languages/java/basics/#server-side-streaming-rpc)
- [Go](https://grpc.io/docs/languages/go/basics/#server-side-streaming-rpc)

以下は Python での UDTF に対応する gRPCサービスの実装例です。
UDTF に対応するメソッドにおいて `return` の代わりに `yield` を使って各行を順次返します。

`csv_expander_server.py`

```python
def Split(self, request, context):
    # カンマ区切りで分割し、各要素と位置（1始まり）を yield で返す
    if request.text:
        for pos, item in enumerate(request.text.split(","), start=1):
            yield csv_expander_pb2.SplitResponse(
                item=item.strip(),
                pos=pos,
            )
```

その他の実装については UDSF と同様です。`udf-library` なども同様に利用することができます (詳しくは [udf-library ( for Python )](./udf-library_ja.md) を参照してください)。
