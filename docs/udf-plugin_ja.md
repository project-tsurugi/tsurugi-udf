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
| **Python** - 開発用パッケージ | ≥ 3.10 | Python 3.9 以前のバージョンは利用不可 |
| **pip** | ≥ 24.0 | Ubuntu 22 環境で `python3-pip` パッケージで導入した場合はアップグレードが必要 |

その他、実行環境に必要なコンポーネントについての詳細は [tsurugi-udf/README.md](https://github.com/project-tsurugi/tsurugi-udf/blob/master/README.md) を参照してください。

### Dockerfile

```dockerfile
FROM ubuntu:22.04

RUN apt update -y && apt install -y build-essential cmake libboost-serialization-dev libgrpc-dev libgrpc++-dev libprotobuf-dev ninja-build protobuf-compiler protobuf-compiler-grpc python3-dev python3-pip
RUN pip3 install --upgrade pip
```

> [!IMPORTANT]
> Ubuntu 22.04 では pip のデフォルトバージョンが古いため、`pip3 install --upgrade pip` で更新する必要があります。

## インストール方法

`udf-plugin` を利用するには、[tsurugi-udf](https://github.com/project-tsurugi/tsurugi-udf) リポジトリのソースコードを取得し、これに含まれる `udf-plugin` Python パッケージをインストールします。

以下は `udf-plugin` のインストール手順例です。

```sh
# tsurugi-udf のソースアーカイブのダウンロードと展開
$ TSURUGI_UDF_VERSION="0.2.0"
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
$ udf-plugin-builder --proto helloworld.proto
```

これにより、現在のディレクトリに UDF プラグインを構成する以下のファイルが生成されます。

- `libhelloworld.so` : プラグインライブラリファイル
- `libhelloworld.ini` : プラグイン設定ファイル

### `udf-plugin-builder` のオプション

`udf-plugin-builder` は以下のコマンドラインオプションをサポートしています。

```bash
$ udf-plugin-builder
usage: udf-plugin-builder [-h] --proto PROTO_FILES [PROTO_FILES ...] [--build-dir BUILD_DIR]
                          [--grpc-plugin GRPC_PLUGIN] [-I INCLUDE] [--grpc-endpoint GRPC_ENDPOINT]
                          [--grpc-transport GRPC_TRANSPORT] [--output-dir OUTPUT_DIR] [--debug] [--clean]
                          [--auto-deps | --no-auto-deps] [--secure] [--disable]
udf-plugin-builder: error: the following arguments are required: --proto
```

| オプション | 必須 | デフォルト | 説明 |
| ---------- | ---- | ---------- | ---- |
| `--proto` | **Yes** | なし |ビルド対象の `.proto` ファイルを指定します。**1つの オプションに対して、複数ファイルをスペース区切りで指定可能です。** <br>例:<br> --proto proto/sample.proto proto/tsurugi_types.proto
| `-I`, `--include` | No |なし | `.proto` の `import` 解決に使用する include パスを指定します。**オプション自体を複数回指定可能です（1回につき1ディレクトリ）。** <br>例:<br> -I /path/to/dir_a -I /path/to/dir_b |
| `--build-dir` | No | `tmp/` | ビルドで使用する一時ディレクトリを指定します。 |
| `--output-dir` | No | `.` | 生成される `.so` と `.ini` ファイルを配置するディレクトリを指定します。 |
| `--grpc-endpoint` | No | `dns:///localhost:50051` | gRPC サーバのエンドポイントを指定します（`.ini` に反映されます）。 |
| `--grpc-transport` | No | `stream` | gRPC 通信方式を指定します（`.ini` に反映されます）。 |
| `--secure` | No | `false` | セキュアな gRPC 接続を有効にします（`.ini` に反映されます）。 |
| `--disable` | No | `false` | 生成される UDF を無効状態で出力します（`.ini` に反映されます）。 |
| `--debug` | No | `false` | デバッグログを有効にします。 |
| `--clean` | No | `false` | ビルド前に`--build_dir`で指定した一時ディレクトリを削除します。 |
| `--auto-deps`, `--no-auto-deps` | No | `--auto-deps` (有効) | `.proto` の `import` で参照された未指定のファイルを自動的にビルド対象に含めます。`--no-auto-deps` を指定した場合、未指定の `.proto` が検出されるとエラーになります。 |

### `.proto` の制約とバリデーションエラー

`--proto` に指定した `.proto` ファイルが以下の制約に該当する場合、`udf-plugin-builder` はエラーを出力して終了します。

- rpc メソッド名が Tsurugi の予約語と一致した場合
- rpc メソッドのリクエストメッセージ、レスポンスメッセージに Protocol Buffers のスカラー型や `udf-library` が提供する `tsurugidb.udf` メッセージ型を直接指定した場合
- rpc メソッドのレスポンスメッセージにフィールドを1つも持たないメッセージ型が指定された場合
- rpc メソッドのレスポンスメッセージに `oneof` フィールドを持つメッセージ型が指定された場合

`.proto` の制約についての詳細は [UDF 関数インターフェースの定義](./udf-proto_ja.md) を参照してください。

### `tsurugidb.udf` メッセージ型 の利用

[UDF 関数インターフェースの定義](./udf-proto_ja.md) で説明した `tsurugidb.udf` メッセージ型を利用する場合、以下の通りにオプションを指定します。

- `-I` (`--include`) オプションを 2回指定して、それぞれ以下のディレクトリを include パスとして追加する
  - UDF関数インターフェース を定義した `.proto` ファイルのディレクトリ
  - `tsurugi-udf/proto` ディレクトリ ( `tsurugi_types.proto` を配置しているディレクトリ)
- `--proto` に以下の1つのファイルパスを指定する
  - UDF関数インターフェース を定義した `.proto` ファイルのファイルパス

`udf-plugin-builder` 実行例:
```sh
$ udf-plugin-builder -I . -I /path/to/tsurugi-udf/proto --proto my.proto
```

> [!NOTE]
>
> - デフォルトで `--auto-deps` オプションが有効なため `tsurugi_types.proto` のファイルパスは`.proto` 内で `import` されていれば自動的にビルド対象へ追加されます。
> - `--no-auto-deps` オプションを指定した場合、`tsurugi_types.proto` のファイルパスを`--proto` に明示的に指定する必要があります。指定しない場合、未指定の `.proto` が検出されたとしてエラー終了します。

## UDF プラグインの構成

`udf-plugin-builder` を実行すると、UDF プラグインを構成する以下のファイルが生成されます。

- プラグインライブラリファイル（`.so`）
- プラグイン設定ファイル（`.ini`）

### プラグインライブラリファイル（`.so`）

Tsurugi が生成した UDF を実行するための拡張用共有ライブラリです。

ファイル名は `.proto` ファイル名の先頭に `lib` を付与し、拡張子を `.so` に置換した `lib{name}.so` です。

### プラグイン設定ファイル（`.ini`）

UDF プラグインの設定情報を含む ini 形式のファイルです。
`.proto` 内に `service` が定義されている場合のみ生成されます。

ファイル名は `.proto` ファイル名の先頭に `lib` を付与し、拡張子を `.ini` に置換した `lib{name}.ini` です。

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
| `secure` | Boolean (true/false) | gRPC との通信にセキュアな通信路を利用するかどうか。| この項目を未指定にした場合、Tsurugi 構成ファイル (`tsurugi.ini`) - `[udf]` セクションの `secure` パラメータの値が使用されます。 |
| `transport` | string | gRPCストリーミング通信の方式。デフォルト値は `stream` | |

### UDF プラグインとgRPCサーバの接続設定

生成した UDF プラグインは、プラグイン設定ファイルの `[udf]` セクションの `endpoint` パラメータ (以下 `udf.endpoint` と表記) で指定された宛先 gRPC サーバと接続して通信を行います。デフォルトは `dns:///localhost:50051` です。

UDFを実行するgRPCサーバを Tsurugi と同一ホスト上で動作させる場合、かつgRPCサーバの接続ポートを上記デフォルト値に合わせて実行する場合は `udf.endpoint` はそのままの設定で問題ありませんが、gRPCサーバを Tsurugi と異なるホスト上で動作させる場合や接続ポートを変更する場合は、TsurugiがUDFを実行するgRPCサーバに接続できるように `udf.endpoint` を適切に設定してください。

## UDF プラグインのデプロイ

生成した UDF プラグインを Tsurugi にデプロイすることで、UDF が利用可能になります。

UDF プラグインのデプロイは、Tsurugi が停止している状態で、UDF プラグインの構成ファイル（プラグインライブラリファイル（`.so`）とプラグイン設定ファイル（`.ini`））を Tsurugi のプラグイン配置ディレクトリに配置します。

プラグイン配置ディレクトリは、Tsurugi 構成ファイル（`tsurugi.ini`）の `[udf]` セクションにある `plugin_directory` パラメータで指定します。デフォルトでは `${TSURUGI_HOME}/var/plugins` です。

詳細は [tsurugidb - Configuration file parameters](https://github.com/project-tsurugi/tsurugidb/blob/master/docs/config-parameters.md) の `udf` セクションを参照してください。

### デプロイに関する注意事項

- UDF プラグインは Tsurugi の起動時に読み込まれます。Tsurugi を起動中に UDF プラグインを配置しても反映されません。
- プラグイン配置ディレクトリには複数の UDF プラグインを配置できますが、異なる UDF プラグインに同一パッケージの `.proto` 内で定義された同一の UDF 関数名が含まれていると、Tsurugi起動時に関数名の衝突によりエラーとなります。
  - このエラー発生時におけるTsurugiの既知の制約があります。詳しくは [Tsurugi UDF 既知の制約](./udf-known-issues_ja.md) を参照してください。
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

プラグイン設定ファイルを持たないプラグインライブラリファイル( `service` を定義していない `.proto` から生成されたプラグインライブラリファイル) については `udf-plugin-viewer` で情報を表示することはできません。
