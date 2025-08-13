# gRPC クライアント生成手順

`udf-plugin-builder` における gRPC クライアント生成の流れを、例示を通して順を追って説明します。

______________________________________________________________________

## 1. 例示: サンプル .proto ファイル、C++ファイル

まず、生成に必要な情報を理解するために、以下のサンプル .proto ファイルおよび対応するC++ファイルを見てみます。(生成に必要な情報はC++ファイルのコメント風に記入)

[../../udf-plugin-builder/proto/sample.proto](../../udf-plugin-builder/proto/sample.proto)

```CPP
syntax = "proto3";

package myapi;

import "primitive_types.proto";
import "complex_types.proto";

service Greeter {
  rpc SayHello (StringValue) returns (StringValue);
}
```

[../../udf-plugin-builder/proto/primitive_types.proto](../../udf-plugin-builder/proto/primitive_types.proto)

```CPP
syntax = "proto3";
message StringValue { string value = 1; }
```

[../../udf-plugin-builder/proto/complex_types.proto](../../udf-plugin-builder/proto/complex_types.proto)

rpc_client.h

```CPP
// sample.proto由来のgRPC サービスのスタブ（クライアント側）やサーバのインターフェース
#include "sample.grpc.pb.h"
#include "udf/generic_client.h"
#include <grpcpp/grpcpp.h>
#include <memory>
#include <string>

using namespace plugin::udf;
class rpc_client : public generic_client {
  public:
    explicit rpc_client(std::shared_ptr<grpc::Channel> channel);

    void call(grpc::ClientContext& context, function_index_type function_index,
        generic_record& request, generic_record& response) const override;

  private:
    //protoのpackage名::service名::Stub service名_stub_
    std::unique_ptr<myapi::Greeter::Stub> Greeter_stub_;
};
```

rpc_client.cpp

```CPP
#include "rpc_client.h"
// sample.proto由来のheader Protocol Buffers メッセージの定義と操作コード
#include "sample.grpc.pb.h"
// sample.proto由来のgRPC サービスのスタブ（クライアント側）やサーバのインターフェース
#include "sample.pb.h"

#include <iostream>
#include <stdexcept>

using grpc::ClientContext;
using grpc::Status;
using namespace plugin::udf;
rpc_client::rpc_client(std::shared_ptr<grpc::Channel> channel)
    :
    Greeter_stub_(
        //protoのpackage名::service名::NewStub
        myapi::Greeter::NewStub(channel)
    )
void rpc_client::call(ClientContext& context, function_index_type function_index,
    generic_record& request, generic_record& response) const {
    auto cursor = request.cursor();
    if (!cursor) { throw std::runtime_error("request cursor is null"); }

    response.reset();
    auto fail = [&response]() { response.add_string("RPC failed"); };
    switch (function_index.second) {
        case 0: {
            // service.protoに記述した引数の型
            StringValue req;
            // service.protoに記述した戻り値の型
            StringValue rep;
              //引数の型に対応した、こちらが用意したfetch_(C++ネイティブ型)関数
              auto arg0 = cursor->fetch_string();
              if (!arg0) { throw std::runtime_error("No input arg0"); }
              // primitive_types.protoに記述した引数の要素名 set_要素名
              req.set_value(*arg0);
              // ->関数名
              Status status = Greeter_stub_->SayHello(&context, req, &rep);
              if (status.ok()) {
                // 戻り値の型に対応した、こちらが用意したfetch_(C++ネイティブ型)関数
                // primitive_types.protoに記述した戻り値の要素名 
                  response.add_string(rep.value());
              } else {
                  fail();
              }
              break;
        }
```

この例を見ると、gRPC クライアント生成に必要な情報は次のように自然に把握できます:

- package 名 (`myapi`)
- service 名 (`Greeter`)
- RPC メソッド名 (`SayHello`)
- 引数の型 (`StringValue`) と戻り値の型 (`StringValue`)
- 引数の各要素名 (`value`) と戻り値の要素名 (`value`)

## 2. 実装: テンプレートによる自動生成

Python の [Jinja2](https://jinja.palletsprojects.com/en/stable/) を用いて、上記の情報をもとに C++ コードを自動生成します。

使用するテンプレート:

- [../../udf-plugin-builder/templates/rpc_client.cpp.j2](../../udf-plugin-builder/templates/rpc_client.cpp.j2)
- [../../udf-plugin-builder/templates/rpc_client.h.j2](../../udf-plugin-builder/templates/rpc_client.h.j2)

これにより、`.proto` ファイルの package 名、service 名、RPC メソッド、引数と戻り値の情報から、自動的に C++ gRPC クライアントコードが生成されます。
