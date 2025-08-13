# UDF定義リストの生成方法

## UDF定義リスト定義

UDF定義リスト定義は[../../include/udf/plugin_api.h](../../include/udf/plugin_api.h)のXX_descriptor(XXはprotoのデータ構造に対応)

## UDF定義リスト

抽象クラスplugin_api.hの具象クラスをPythonの[jinja](https://jinja.palletsprojects.com/en/stable/)テンプレートで生成

テンプレートは- [../../udf-plugin-builder/templates/plugin_api_impl.cpp.j2](../../udf-plugin-builder/templates/plugin_api_impl.cpp.j2)

## テンプレートにデータを渡す処理

python機能を活用

[../../udf-plugin-builder/generate.py](../../udf-plugin-builder/generate.py)

.pb ファイル（--descriptor_set_out で生成したファイル）を Python 用 Protocol Buffers ランタイムの google.protobuf.descriptor_pb2 モジュールを使って FileDescriptorSet 型にデシリアライズし、その構造化データを Jinja2 テンプレートの入力として利用する。

参考: [google.protobuf.descriptor_pb2](https://googleapis.dev/python/protobuf/latest/google/protobuf/descriptor_pb2.html)