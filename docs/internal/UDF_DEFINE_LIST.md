# UDF 定義リストの生成方法

`udf-plugin-builder` における UDF 定義リストの生成手順は、以下の通りです。

______________________________________________________________________

## 1. UDF 定義リスト定義

UDF 定義リストは、以下のヘッダーファイルに定義されています：

- [../../include/udf/plugin_api.h](../../include/udf/plugin_api.h)

> 注: 各 `XX_descriptor` は、対応する Protobuf データ構造に紐づいています（`XX` は proto のメッセージ名）。

______________________________________________________________________

## 2. UDF 定義リストの生成

抽象クラス `plugin_api` の具象クラスを、Python の [Jinja2](https://jinja.palletsprojects.com/en/stable/) テンプレートを用いて生成します。

テンプレートファイルは以下です：

- [../../udf-plugin-builder/templates/plugin_api_impl.cpp.j2](../../udf-plugin-builder/templates/plugin_api_impl.cpp.j2)

このテンプレートを元に、UDF 定義リストの C++ 実装コードが自動生成されます。

______________________________________________________________________

## 3. テンプレートにデータを渡す処理

生成処理は Python で実装されています：

- [../../udf-plugin-builder/generate.py](../../udf-plugin-builder/generate.py)

手順は以下の通りです：

1. `.pb` ファイル（`--descriptor_set_out` で生成）を用意する。
1. Python 用 Protocol Buffers ランタイムの [`google.protobuf.descriptor_pb2`](https://googleapis.dev/python/protobuf/latest/google/protobuf/descriptor_pb2.html) モジュールを使用し、`.pb` ファイルを `FileDescriptorSet` 型にデシリアライズする。
1. デシリアライズされた構造化データを Jinja2 テンプレートに渡して、C++ コードを生成する。

______________________________________________________________________

> 注: このプロセスにより、UDF 定義リストは Protobuf のデータ構造に基づいた具象クラスとして自動生成されます。
