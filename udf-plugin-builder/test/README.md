# udf-plugin-builder-test

## 利用方法

```bash
mkdir build
cd build
cmake ..
make
./inspect_plugin ../../build/libplugin_api.so
```

## 解説

`make` を実行すると以下の3つの実行ファイルが生成されます。

- **inspect_plugin**\
  `libplugin_api.so` をロードし、その中に組み込まれた gRPC クライアントを起動するプログラムです。

- **rpc_server**\
  gRPC サーバ。テストを行う前に事前に起動しておく必要があります。

- **rpc_client**\
  gRPC クライアント。`rpc_server` との疎通確認を行うために利用します。

## テスト手順

1. まず `rpc_server` を起動します。

1. 次に `rpc_client` を起動し、クライアントとサーバ間で gRPC 通信が行えていることを確認します。

1. 通信が確認できたら以下を実行します。

   ```bash
   ./inspect_plugin ../../build/libplugin_api.so
   ```

   - `inspect_plugin` の第1引数には `libplugin_api.so` のパスを渡します。
   - 実行すると、`inspect_plugin` が `libplugin_api.so` に組み込まれた gRPC クライアントを起動し、gRPC 通信を行います。
   - クライアントに通信結果が表示されればテスト成功です。

1. さらに、**gRPC サーバを起動せずに `inspect_plugin` を実行し、通信が失敗することを確認**してください。これにより、通信が正しくサーバ依存で動作していることが確認できます。

______________________________________________________________________

以上で通信テストは終了です。
