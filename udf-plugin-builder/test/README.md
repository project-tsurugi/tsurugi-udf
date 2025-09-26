# udf-plugin-builder-test

## 概要

udf-plugin-builder-test は、udf-plugin-builder により生成された共有ライブラリ（shared object）が Tsurugi Database 上で正常に動作することを検証するためのテストです。

本テストを実行することで、ビルドされた UDF プラグインが Tsurugi のプラグインローダ経由で正しくロード・利用可能であるかを確認できます。

## 前提条件

- Tsurugi Database がインストール済みであること
- テストを実行するユーザが必要な権限を有していること

## テスト実行方法

以下のコマンドを実行します。

```bash
./run.sh <tsurugi.ini の loader_path>
```

## 引数

### loader_path

Tsurugi Database の設定ファイル tsurugi.ini に記載された loader_path を指定します。

例:

```
[sql]
loader_path=/tsurugi/grpc
```

## 判定基準

テストの実行結果は、標準出力に以下の形式で表示されます。

### OK: \<テスト名>

→ テストが正常に完了した場合

### NG: \<テスト名>

→ テストが失敗した場合

## 例

OK: load_another
NG: unary_test

※本テストは 終了コードでも成功／失敗を区別します。

- 全てのテストが成功した場合 → 終了コード 0
- いずれかのテストが失敗した場合 → 終了コード 1
