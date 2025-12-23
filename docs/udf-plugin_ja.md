# udf-plugin

本書では UDF プラグインを生成、管理するための各ツールについて説明します。

## 概要

`udf-plugin` は、Tsurugi UDF が提供する UDF プラグイン関連ツールを提供する Python パッケージです。

`udf-plugin` パッケージには以下のツールが含まれます。

- `udf-plugin-builder` : [UDF 関数インターフェースの定義](./udf-proto_ja.md) に基づいて作成した `.proto` ファイルから、UDF プラグインを生成するツールです。
- `udf-plugin-viewer` : 生成した UDF プラグインのメタデータを表示するツールです。

## 前提環境

| コンポーネント | バージョン | 備考 |
| -------------- | --------- | ---- |
| **Python** | ≥ 3.10 | Python 3.9 未満は利用不可 |
| **pip** | ≥ 24.0 | Ubuntu 22 環境で `python3-pip` パッケージで導入した場合はアップグレードが必要 |

その他、実行環境に必要なコンポーネントについての詳細は [tsurugi-udf/README.md](https://github.com/project-tsurugi/tsurugi-udf/blob/master/README.md) を参照してください。

### Dockerfile

```dockerfile
FROM ubuntu:22.04

RUN apt update -y && apt install -y build-essential cmake libboost-serialization-dev libgrpc-dev libgrpc++-dev libprotobuf-dev ninja-build protobuf-compiler protobuf-compiler-grpc python3 python3-pip
RUN pip3 install --upgrade pip
```

> [!IMPORTANT]
> Ubuntu 22.04 では pip のデフォルトバージョンが古いため、`pip3 install --upgrade pip` で更新する必要があります。

## インストール方法

`udf-plugin` を利用するには、[tsurugi-udf](https://github.com/project-tsurugi/tsurugi-udf) リポジトリのソースコードを取得し、これに含まれる `udf-plugin` Python パッケージをインストールします。

以下は `udf-plugin` のインストール手順例です。

```sh
# tsurugi-udf のソースアーカイブのダウンロードと展開
$ TSURUGI_UDF_VERSION="0.1.0"
$ curl -OL https://github.com/project-tsurugi/tsurugi-udf/archive/refs/tags/${TSURUGI_UDF_VERSION}.tar.gz
$ tar xf ${TSURUGI_UDF_VERSION}.tar.gz
$ cd tsurugi-udf-${TSURUGI_UDF_VERSION}

# udf-plugin のインストール
$ cd udf-plugin
$ pip install .
```

一般ユーザでインストールした場合、以下の場所にパッケージとスクリプトがインストールされます。

- パッケージ: `$HOME/.local/lib/pythonX.Y/site-packages`
- スクリプト: `$HOME/.local/bin`

## `udf-plugin-builder`

`udf-plugin-builder` は [UDF 関数インターフェースの定義](./udf-proto_ja.md) に基づいて作成した `.proto` ファイルから、UDF プラグインを生成するツールです。

最もシンプルな利用例は以下の通りです。

```bash
$ udf-plugin-builder --proto-file helloworld.proto
```

これにより、現在のディレクトリに UDF プラグインを構成する以下のファイルが生成されます。

- `libhelloworld.so` : プラグインライブラリファイル
- `libhelloworld.ini` : プラグイン設定ファイル

### `udf-plugin-builder` のオプション

`udf-plugin-builder` は以下のコマンドラインオプションをサポートしています。

```bash
$ udf-plugin-builder
usage: udf-plugin-builder [-h] --proto-file PROTO_FILE [PROTO_FILE ...]
                          [--proto-path PROTO_PATH [PROTO_PATH ...]]
                          [--build-dir BUILD_DIR]
                          [--name NAME]
                          [--grpc-endpoint GRPC_ENDPOINT]
                          [--output-dir OUTPUT_DIR]
udf-plugin-builder: error: the following arguments are required: --proto-file
```

| オプション | 必須 | デフォルト | 説明 |
| ---------- | ---- | ---------- | ---- |
| `--proto-file` | **Yes** | なし | ビルド対象の `.proto` ファイルを指定します。複数ファイルをスペース区切りで指定可能です。<br>例：`--proto-file proto/sample.proto proto/tsurugi_types.proto` |
| `--proto-path` | No | `--proto-file` で最初に指定したファイルのディレクトリパス | `.proto` ファイルを含むディレクトリを指定します。 `protoc` が依存ファイルを解決する際に使用されます。 |
| `--build-dir` | No | `tmp/` | CMake ビルドで使用する一時ディレクトリを指定します。ビルド後は自動的に削除されます。 |
| `--name` | No | 最初に指定した `proto` ファイル名 (拡張子を除く) | 生成されるプラグインライブラリファイル名（`.so`）およびプラグイン設定ファイル（`.ini`）のベース名を指定します。 <br>例：`--name my_udf` → 出力ファイルは `libmy_udf.so` / `libmy_udf.ini` になります。 |
| `--grpc-endpoint` | No | `dns:///localhost:50051` | gRPC サーバのエンドポイントを指定します（`.ini` に反映されます）。 |
| `--output-dir` | No | `.` | 生成される `.so` と `.ini` ファイルを配置するディレクトリを指定します。 |

### `udf-plugin-builder` の環境変数

`udf-plugin-builder` はその内部で実行する CMake ビルドの挙動を制御するために以下の環境変数をサポートしています。

- `BUILD_TYPE`
  - CMake ビルドタイプを指定します。`Release` , `RelWithDebInfo` , `Debug` を指定可能です。デフォルトは `RelWithDebInfo` です。
  - `Debug` を指定した場合、コマンド実行時に CMakeのログが出力されます。エラー時の解析に有用です。

### `.proto` の制約とバリデーションエラー

`--proto-file` に指定した `.proto` ファイルが以下の制約に該当する場合、`udf-plugin-builder` はエラーを出力して終了します。
- rpc メソッド名が Tsurugi の予約語と一致した場合
- rpc メソッドのレスポンスメッセージにフィールドを1つも持たないメッセージ型が指定された場合
- rpc メソッドのレスポンスメッセージに `oneof` フィールドを持つメッセージ型が指定された場合

`.proto` の制約についての詳細は [UDF 関数インターフェースの定義](./udf-proto_ja.md) を参照してください。

### `tsurugidb.udf` メッセージ型 の利用

[UDF 関数インターフェースの定義](./udf-proto_ja.md) で説明した `tsurugidb.udf` メッセージ型を利用する場合、以下の通りにオプションを指定します。

- `--proto-path` に以下の2つのディレクトリを指定する
  - UDF関数インターフェース を定義した `.proto` ファイルのディレクトリ
  - `tsurugi-udf/proto` ディレクトリ
- `--proto-file` に以下の2つのファイルパスを指定する
  - UDF関数インターフェース を定義した `.proto` ファイルのファイルパス
  - `tsurugi-udf/proto/tsurugidb/udf/tsurugi_types.proto` のファイルパス

例:

- 現在のディレクトリに `my.proto` という UDF 関数インターフェースを定義した `.proto` ファイルを配置
- `${TSURUGI_UDF_DIR}` に `tsurugi-udf` リポジトリを配置

```sh
$ udf-plugin-builder --proto-path . ${TSURUGI_UDF_DIR}/proto --proto-file my.proto ${TSURUGI_UDF_DIR}/proto/tsurugidb/udf/tsurugi_types.proto
```

## UDF プラグインの構成

`udf-plugin-builder` を実行すると、UDF プラグインを構成する以下のファイルが生成されます。

- プラグインライブラリファイル（`.so`）
- プラグイン設定ファイル（`.ini`）

### プラグインライブラリファイル（`.so`）

Tsurugi が生成した UDF を実行するための拡張用共有ライブラリです。

ファイル名は `lib{name}.so` です。 `name` 部分は `udf-plugin-builder` の `--name` オプションで指定した文字列です。

### プラグイン設定ファイル（`.ini`）

UDF プラグインの設定情報を含む ini 形式のファイルです。

ファイル名は `lib{name}.ini` です。`name` 部分は `udf-plugin-builder` の `--name` オプションで指定した文字列です。

プラグイン設定ファイルは以下の設定項目を含みます。

```ini
[udf]
enabled=true
endpoint=dns:///localhost:50051
secure=false
```

| パラメータ名 | 型 | 説明 | 備考 |
| ---------- | ---- | ---- | ---- |
| `enabled` | Boolean (true/false) | UDF プラグインの有効/無効を指定。デフォルト値は `true` | `false` に指定した場合、UDF プラグインが Tsurugi にデプロイされていても UDF は無効化されます。 |
| `endpoint` | String | この UDF プラグインに対応する宛先 gRPC サーバのエンドポイント。デフォルト値は `udf-plugin-builder` の `--grpc-endpoint` オプションで指定した値。 | この項目を未指定にした場合、Tsurugi 構成ファイル（`tsurugi.ini`）- `[udf]` セクションの `endpoint` パラメータの値が使用されます。 |
| `secure` | Boolean (true/false) | gRPC との通信にセキュアな通信路を利用するかどうか。現時点では `false` のみサポート。 | この項目を未指定にした場合、Tsurugi 構成ファイル (`tsurugi.ini`) - `[udf]` セクションの `secure` パラメータの値が使用されます。 |

## UDF プラグインのデプロイ

生成した UDF プラグインを Tsurugi にデプロイすることで、UDF が利用可能になります。

UDF プラグインのデプロイは、Tsurugi が停止している状態で、UDF プラグインの構成ファイル（プラグインライブラリファイル（`.so`）とプラグイン設定ファイル（`.ini`））を Tsurugi のプラグイン配置ディレクトリに配置します。

プラグイン配置ディレクトリは、Tsurugi 構成ファイル（`tsurugi.ini`）の `[udf]` セクションにある `plugin_directory` パラメータで指定します。デフォルトでは `${TSURUGI_HOME}/var/plugins` です。

詳細は [tsurugidb - Configuration file parameters](https://github.com/project-tsurugi/tsurugidb/blob/master/docs/config-parameters.md) の `udf` セクションを参照してください。

### デプロイに関する注意事項

- UDF プラグインは Tsurugi の起動時に読み込まれます。Tsurugi を起動中に UDF プラグインを配置しても反映されません。
- プラグイン配置ディレクトリには複数の UDF プラグインを配置できますが、異なる UDF プラグインに同一の UDF 関数名が含まれていると、関数名の衝突によりエラーとなります。
- UDF プラグインを構成するファイルはプラグイン配置ディレクトリの直下に配置する必要があります。サブディレクトリに配置した場合、Tsurugi は UDF プラグインを認識しません。

## `udf-plugin-viewer`

`udf-plugin-viewer` は生成した UDF プラグインのメタデータを表示するツールです。

`udf-plugin-viewer` は表示したい UDF プラグインのプラグインライブラリファイル（`.so`）を指定して実行します。

```bash
$ udf-plugin-viewer path_to_plugin.so
```

実行すると gRPC サービス定義に関する情報の他、UDF プラグインの生成元となった `.proto` ファイル情報とファイル名、UDF プラグインのバージョン情報などが JSON 形式で表示されます。

```sh
[gRPC] ok file: /path/to/libhelloworld.so detail: Loaded successfully
```

```json
[
  {
    "package_name": "",
    "services": [
      {
        "service_index": 0,
        "service_name": "Greeter",
        "functions": [
          {
            "function_index": 0,
            "function_name": "SayHello",
            "function_kind": 0,
            "input_record": {
              "record_name": "HelloRequest",
              "columns": [
                {
                  "index": 0,
                  "column_name": "name",
                  "type_kind": "string",
                  "oneof_index": null,
                  "oneof_name": null,
                  "nested_record": null
                }
              ]
            },
            "output_record": {
              "record_name": "HelloReply",
              "columns": [
                {
                  "index": 0,
                  "column_name": "message",
                  "type_kind": "string",
                  "oneof_index": null,
                  "oneof_name": null,
                  "nested_record": null
                }
              ]
            }
          },
          {
            "function_index": 1,
            "function_name": "SayHelloAgain",
            "function_kind": 0,
            "input_record": {
              "record_name": "HelloRequest",
              "columns": [
                {
                  "index": 0,
                  "column_name": "name",
                  "type_kind": "string",
                  "oneof_index": null,
                  "oneof_name": null,
                  "nested_record": null
                }
              ]
            },
            "output_record": {
              "record_name": "HelloReply",
              "columns": [
                {
                  "index": 0,
                  "column_name": "message",
                  "type_kind": "string",
                  "oneof_index": null,
                  "oneof_name": null,
                  "nested_record": null
                }
              ]
            }
          }
        ]
      }
    ],
    "file_name": "helloworld.proto",
    "version": {
      "major": 1,
      "minor": 0,
      "patch": 0
    }
  }
]
```
