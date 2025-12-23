# udf-library (for Python)

## 概要

`udf-library` は、Python で UDF の gRPC サービスを実装する際に利用する Python ライブラリです。

本ライブラリは `tsurugidb.udf` パッケージを提供し、主に以下のクラス群で構成されています。

- [データ型](#データ型)
  - Protocol Buffer の基本型で表現できない、Tsurugi の SQL のデータ型を表現するためのクラス群を提供します ([`tsurugidb.udf` メッセージ型](udf-proto_ja.md#tsurugidbudf-メッセージ型))
- [データ型変換](#データ型変換)
  - Python の標準データ型と [`tsurugidb.udf` メッセージ型](udf-proto_ja.md#tsurugidbudf-メッセージ型) 間の変換関数を提供します。
- [BLOB クライアント](#blob-クライアント)
  - BLOB / CLOB データの読み書きを行うためのクライアント API を提供します。

## 前提環境

| コンポーネント | バージョン | 備考 |
| -------------- | --------- | ---- |
| **Python** | ≥ 3.10 | Python 3.9 未満は利用不可 |
| **pip** | ≥ 24.0 | Ubuntu 22 環境で `python3-pip` パッケージで導入した場合はアップグレードが必要 |

その他、実行環境に必要なコンポーネントについての詳細は [tsurugi-udf/README.md](https://github.com/project-tsurugi/tsurugi-udf/blob/master/README.md) を参照してください。

## インストール方法

本ライブラリを利用するには、[tsurugi-udf](https://github.com/project-tsurugi/tsurugi-udf) リポジトリのソースコードを取得し、これに含まれる `udf-library` Python パッケージをインストールします。

以下は `udf-library` のインストール手順例です。

```sh
# tsurugi-udf のソースアーカイブのダウンロードと展開
$ TSURUGI_UDF_VERSION="0.1.0"
$ curl -OL https://github.com/project-tsurugi/tsurugi-udf/archive/refs/tags/${TSURUGI_UDF_VERSION}.tar.gz
$ tar xf ${TSURUGI_UDF_VERSION}.tar.gz
$ cd tsurugi-udf-${TSURUGI_UDF_VERSION}

# udf-library のインストール
$ cd udf-library
$ pip install .
```

> [!IMPORTANT]
> Ubuntu 22.04 では pip のデフォルトバージョンが古いため、`pip3 install --upgrade pip` で更新する必要があります。

## `tsurugidb.udf` パッケージ

本ライブラリは `tsurugidb.udf` パッケージを提供します。これを利用するには `tsurugidb.udf` パッケージを import してください。

```python
from tsurugidb.udf import *
...
```

基本的に、Tsurugi UDF を実装する上で必要なクラスは、上記の `import` で利用可能になります。

## データ型

Tsurugi の SQL のデータ型のうち、Protocol Buffers の基本型で表現できないデータ型を表現するためのクラス群を提供します。

これは [`tsurugidb.udf` メッセージ型](udf-proto_ja.md#tsurugidbudf-メッセージ型) に対応しており、各メッセージと同じパッケージ、同じ名前で Python のクラスを提供しています。

利用可能な Python のクラスは以下の通りです:

- `tsurugidb.udf.Decimal`
- `tsurugidb.udf.Date`
- `tsurugidb.udf.LocalTime`
- `tsurugidb.udf.LocalDatetime`
- `tsurugidb.udf.OffsetDatetime`
- `tsurugidb.udf.BlobReference`
- `tsurugidb.udf.ClobReference`

以下に、`Decimal` 型を使用する例を示します。この例では、gRPC サービスの実装で `types_pb2` モジュール（`.proto` ファイルから自動生成されたモジュール）を使用しています。

```python
import grpc
import types_pb2
import types_pb2_grpc

from tsurugidb.udf import *
...
    def DecimalReturn(self, request, context):
        """Decimal 型フィールドを受け取り、そのまま返す"""
        decimal_value = request.value;
        print(f"Received Decimal: unscaled_value={int.from_bytes(decimal_value.unscaled_value, byteorder='big', signed=True)}, exponent={decimal_value.exponent}")
        return types_pb2.DecimalValue(value=decimal_value)

```

`Decimal` 型は、10 進数を表現するために `unscaled_value`（符号付き整数のバイト列）と `exponent`（指数部）から構成されます。
このままでは扱いにくいため、次項の [データ型変換](#データ型変換) で提供する変換関数を利用して、Python 上でこれらのデータ型を扱いやすくします。

## データ型変換

前項の [データ型](#データ型) で紹介したそれぞれのクラスに対し、本ライブラリは対応する Python データ型との相互変換を行う関数を提供しています。

例えば、引数に渡された `tsurugidb.udf.Decimal` クラスの値を、 Python の `decimal.Decimal` クラスの値に変換したり、その逆の変換を行うことができます。

これらを利用して、UDF の引数として受け取った [`tsurugidb.udf` メッセージ型](udf-proto_ja.md#tsurugidbudf-メッセージ型) を Python の標準データ型に変換し、処理が完了したら Python の標準データ型を `tsurugidb.udf` メッセージ型に変換して UDF の戻り値として返すことができます。

現時点では、以下のデータ型の変換に対応しています。

| `tsurugidb.udf` メッセージ型 | Python データ型 | 変換関数: `tsurugidb.udf` => Python | 変換関数: Python => `tsurugidb.udf` |
| -------------------------- | --------------- | ----------------- | ----------------- |
| `tsurugidb.udf.Decimal` | `decimal.Decimal` | `from_pb_decimal` | `to_pb_decimal` |
| `tsurugidb.udf.Date` | `datetime.date` | `from_pb_date` | `to_pb_date` |
| `tsurugidb.udf.LocalTime` | `datetime.time` | `from_pb_local_time` | `to_pb_local_time` |
| `tsurugidb.udf.LocalDatetime` | `datetime.datetime` | `from_pb_local_datetime` | `to_pb_local_datetime` |
| `tsurugidb.udf.OffsetDatetime` | `datetime.datetime` | `from_pb_offset_datetime` | `to_pb_offset_datetime` |

いずれも、`from_pb_xxx` 関数が `tsurugidb.udf` メッセージ型から Python データ型への変換を行い、`to_pb_xxx` 関数が Python データ型から `tsurugidb.udf` メッセージ型への変換を行います。

以下に `tsurugidb.udf.Decimal` 型を扱う UDF 実装内で変換関数を利用する例を示します。

```python
from tsurugidb.udf import *
...
    def DecimalAdd(self, request, context):
        """2つの Decimal 型フィールドを受け取り、その和を返す"""
        value1 = from_pb_decimal(request.f1)
        value2 = from_pb_decimal(request.f2)
        result = value1 + value2
        print(f"[DecimalAdd] Received: f1={value1} (type={type(value1).__name__}), f2={value2} (type={type(value2).__name__}), sum={result} (type={type(result).__name__})")
        return types_pb2.DecimalValue(value=to_pb_decimal(result))
```

## BLOB クライアント

[データ型](#データ型) セクションで紹介した `tsurugidb.udf.BlobReference` (BLOB 参照) および `tsurugidb.udf.ClobReference` (CLOB 参照) 型は、いずれも BLOB / CLOB のデータ本体を直接含んでいません。
これは、gRPC のメッセージ長の制限で、大きな BLOB / CLOB データを直接 gRPC メッセージでやり取りできないためです。

BLOB クライアントは、これらの BLOB / CLOB データの読み書きを行うための API で、 `tsurugidb.udf.BlobRelayClient` クラスのサブクラスとして提供しています。
Tsurugi からの指示で `BlobRelayClient` の実装を切り替え、適切な方法で Tsurugi に接続を行い BLOB / CLOB データの送受信を行います。

`BlobRelayClient` は、以下のメソッドを提供しています。

- `download_blob(self, ref: BlobReference, destination: Path, *, timeout: timedelta | None = None) -> None:`
  - `BlobReference` に対応する BLOB データを Tsurugi からダウンロードし、指定したローカルファイルパスに保存します。
- `download_clob(self, ref: ClobReference, destination: Path, *, timeout: timedelta | None = None) -> None:`
  - `ClobReference` に対応する CLOB データを Tsurugi からダウンロードし、指定したローカルファイルパスに保存します。
- `upload_blob(self, source: Path, *, timeout: timedelta | None = None) -> BlobReference:`
  - 指定したローカルファイルパス上の BLOB ファイルを Tsurugi へアップロードし、対応する `BlobReference` を返します。
- `upload_clob(self, source: Path, *, timeout: timedelta | None = None) -> ClobReference:`
  - 指定したローカルファイルパス上の CLOB ファイルを Tsurugi へアップロードし、対応する `ClobReference` を返します。

`BlobRelayClient` は抽象クラスであり、 `tsurugidb.udf.create_blob_client(context)` 関数を利用して `BlobRelayClient` のインスタンスを生成します。
`context` 引数には、 gRPC サービスのコンテキストオブジェクト (`grpc.ServicerContext`) を指定します。

以下は、`BlobRelayClient` を利用して BLOB データをダウンロードする例です。

```python
from pathlib import Path
from tsurugidb.udf import *
...
    def DownloadBlob(self, request, context):
        """BlobReference を受け取り、BLOB をダウンロードして VARBINARY として返す"""
        with create_blob_client(context) as client:
            blob_path = Path("/tmp/blob.dat")

            client.download_blob(request.value, blob_path, timeout=timedelta(seconds=60))
            with open(blob_path, 'rb') as f:
                blob_data = f.read()

            return blobs_pb2.VarbinaryValue(value=blob_data)

    def UploadBlob(self, request, context):
        """VARBINARY を受け取り、BLOB をアップロードして BlobReference を返す"""
        with create_blob_client(context) as client:
            blob_path = Path("/tmp/blob.dat")

            with open(blob_path, 'wb') as f:
                f.write(request.value)
            ref = client.upload_blob(blob_path, timeout=timedelta(seconds=60))

            return blobs_pb2.BlobValue(value=ref)

```

>[!NOTE]
> BLOB クライアントは、 Tsurugi の内部で動作している [BLOB中継サービス](https://github.com/project-tsurugi/data-relay-grpc) と gRPC 通信を行います

## その他の機能

### ロギング

本ライブラリは Python 標準の `logging` モジュールを利用してログを出力します。本ライブラリのログレベルを変更したい場合は、以下のように設定します。

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

現時点では、 [BLOB クライアント](#blob-クライアント) の内部において `DEBUG` レベルでログ出力が行われています。
