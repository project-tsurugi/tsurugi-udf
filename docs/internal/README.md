# 内部資料

## UDF Plugin Builder

`udf-plugin-builder` は、以下の 3 つの主要コンポーネントから構成されます

1. **UDF 定義リスト (UDF Definition List)**
1. **gRPC クライアント (gRPC Client)**
1. **LOADER**

各コンポーネントの生成方法およびビルド手順は以下の通りです。

______________________________________________________________________

### 1. UDF 定義リストの生成

UDF 定義リストの作成方法は、[UDF_DEFINE_LIST.md](UDF_DEFINE_LIST.md) を参照してください。

______________________________________________________________________

### 2. gRPC クライアントの生成

gRPC クライアントの作成方法については、[NEED_CLT.md](NEED_CLT.md) を参照してください。

______________________________________________________________________

### 3. LOADER の生成

LOADER の作成方法については、[LOADER.md](LOADER.md) を参照してください。

______________________________________________________________________

### 4. ビルド手順

上記 3 つのコンポーネントを以下の CMakeLists.txt を使用してビルドします：

- [../../udf-plugin-builder/CMakeLists.txt](../../udf-plugin-builder/CMakeLists.txt)

ビルドが成功すると、`libplugin_api.so` という UDF プラグインが生成されます。

## UDF Plugin Viewer

`udf-plugin-builder` で生成された UDF 定義リストを Python 側で利用するために、対応する Python 構造体にデータを保持し、必要に応じてシリアライズできる仕組みを提供します。

### 1. Python 側構造体

UDF 定義リストを表現する Python 構造体は、以下のモジュールで定義されています

- [../../py/common/descriptors.py](../../py/common/descriptors.py)

> 注: この構造体は、C++ で生成された UDF 定義リストの各メンバーや関数情報を反映しています。

### 2. Python マッピング

pybind11 を通じてC++のデータをpythonにマッピングします。マッピングは以下のモジュールで定義されています

- [../../udf-plugin-viewer/bindings.cpp](../../udf-plugin-viewer/bindings.cpp)


### 3.JSON 形式でのダンプ

Python の標準 `json` モジュールを用いて、構造体の内容を JSON にシリアライズします。シリアライズは以下のモジュールで定義されています

- [../../udf-plugin-viewer/udf_plugin_viewer/__main__.py](../../udf-plugin-viewer/udf_plugin_viewer/__main__.py)

### 4. ビルド手順

pipを使ってビルド管理

- [../../udf-plugin-viewer/pyproject.toml](../../udf-plugin-viewer/pyproject.toml)