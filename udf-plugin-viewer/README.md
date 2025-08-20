# udf-plugin-viewer

`udf-plugin-viewer` は **生成済み UDF プラグインのメタデータを表示するツール** です。\
Python インターフェースと pybind11 を利用してプラグインを読み込み、\
その情報を確認できます。

______________________________________________________________________

## 依存関係

- CMake 3.14 以降
- Python 3.8 以降
- pybind11
- scikit-build-core
- ninja
- nlohmann_json
- Protobuf
- gRPC

______________________________________________________________________

## インストール

```bash
cd udf-plugin-viewer
pip install .
```

## アンインストール

```bash
pip uninstall udf-plugin-viewer
```

______________________________________________________________________

## 利用例

udf-plugin-viewer path_to_plugin.so
