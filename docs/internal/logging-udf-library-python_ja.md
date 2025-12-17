# udf-library (Python) におけるロギング

## 方針

* Python 標準の `logging` モジュールを使用してログを出力
* `DEBUG` レベルのみでログを出力
* ログメッセージ言語は英語のみ

## ロガー名

| ロガー名 | 概要 | 主な出力 |
| -------- | ---- | -------- |
| `tsurugidb.udf.blob.factory` | BLOB クライアントの汎用ファクトリ | トランスポートプラグインの探索 |
| `tsurugidb.udf.blob.stream.factory` | ストリーミング BLOB クライアントのファクトリ | チャンネルの初期化, 終了 |
| `tsurugidb.udf.blob.stream.client` | ストリーミング BLOB クライアント | リクエスト送信, レスポンス受信 |

----
Note:

本来はモジュール名などをロガー名に指定することが多いが、モジュール階層が固まっていないため、上記のようにモジュール構造とは別の階層を導入した。

別のトランスポートプラグインを追加する場合、 `tsurugidb.udf.blob.<transport>` というロガー名の利用を推奨する。

また、BLOB 転送以外の機能セットを UDF から利用可能にする場合、 `tsurugidb.udf.<feature>` というロガー名の利用を推奨する。

## 各種設定

### アプリケーション

アプリケーションでは、標準の方法でロガーの設定を行う:

```python
import logging

# すべての DEBUG ログを有効化
logging.basicConfig(level=logging.DEBUG)

# ストリーミング BLOB クライアントのログのみをを有効化
logging.getLogger("tsurugidb.udf.blob.stream").setLevel(logging.DEBUG)
```

### テスト

テスト実行時には、`pytest` の `--log-cli-level` オプションを使用してログレベルを設定する:

```sh
# すべての DEBUG ログを有効化
pytest --log-cli-level=DEBUG

# ストリーミング BLOB クライアントのログのみを有効化
pytest --log-cli-level=DEBUG --log-cli-filter="tsurugidb.udf.blob.stream"
```
