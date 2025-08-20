#include <iostream>
#include <memory>
#include <string>

#include "sample.grpc.pb.h"
#include "sample.pb.h"
#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using myapi::Byer;
using myapi::Greeter;

class GreeterServiceImpl final : public Greeter::Service {
    Status SayHello(
        ServerContext* context, const StringValue* request, StringValue* reply) override {
        std::string prefix("Hello ");
        reply->set_value(prefix + request->value());
        return Status::OK;
    }
    Status IntAddInt(
        ServerContext* context, const Int32Value* request, Int32Value* reply) override {
        int sum = request->value() + 1;
        reply->set_value(sum);
        return Status::OK;
    }
    Status SayGoodbye(
        ServerContext* context, const ::myapi::Byebye* request, ::myapi::Byebye* reply) override {
        std::string combined = request->bye().value() + request->bye().message();
        combined += request->str();
        ::myapi::Bye* new_bye = reply->mutable_bye();
        new_bye->set_value(request->bye().value());
        new_bye->set_message(request->bye().message());
        reply->set_str(combined);
        return Status::OK;
    }
};

class ByerServiceImpl final : public Byer::Service {
    Status SayWorld(
        ServerContext* context, const StringValue* request, StringValue* reply) override {
        std::string prefix("World ");
        reply->set_value(prefix + request->value());
        return Status::OK;
    }
    Status DecDecimal(ServerContext* context, const tsurugidb::udf::value::Decimal* request,
        tsurugidb::udf::value::LocalTime* reply) override {
        std::cout << request->unscaled_value() << " " << request->exponent() << std::endl;
        return Status::OK;
    }
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    GreeterServiceImpl greeter_service;
    ByerServiceImpl byer_service;

    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&greeter_service);
    builder.RegisterService(&byer_service);
    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    RunServer();
    return 0;
}
