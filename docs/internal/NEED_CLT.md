## gRPCクライアント生成に必要なもの

### 結論

package名から引数の要素名まで(つまりprotoファイルに載ってる情報全部)

### 一般的な.protoとそれに対応する.cppファイル

一般的な.protoとそれに対応する.cppファイルから必要なデータを考察する。必要なデータはコメントで記入

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

## 実装

Pythonの[jinja](https://jinja.palletsprojects.com/en/stable/)テンプレートを利用


- [../../udf-plugin-builder/templates/rpc_client.cpp.j2](../../udf-plugin-builder/templates/rpc_client.cpp.j2)
- [../../udf-plugin-builder/templates/rpc_client.h.j2](../../udf-plugin-builder/templates/rpc_client.h.j2)