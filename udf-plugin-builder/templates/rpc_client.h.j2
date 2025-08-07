#pragma once

#include "sample.grpc.pb.h"
#include "udf/generic_client.h"
#include <grpcpp/grpcpp.h>
#include <memory>
#include <string>

using myapi::Byer;
using myapi::Greeter;

using namespace plugin::udf;
class rpc_client : public generic_client {
  public:
    explicit rpc_client(std::shared_ptr<grpc::Channel> channel);

    void call(grpc::ClientContext& context, function_index_type function_index,
        generic_record& request, generic_record& response) const override;

  private:
    std::unique_ptr<Greeter::Stub> greeter_stub_;
    std::unique_ptr<Byer::Stub> byer_stub_;
};
