#include "test_all.grpc.pb.h"
#include "test_all.pb.h"
#include <cstdint>
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <memory>
#include <string>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class TestServiceImpl final : public TestService::Service {

    // @see https://protobuf.dev/programming-guides/proto3/#scalar
    Status EchoInt32(
        ServerContext* context, const Int32Request* request, Int32Reply* reply) override {
        int32_t value = 32;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoInt64(
        ServerContext* context, const Int64Request* request, Int64Reply* reply) override {
        int64_t value = 64;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoFloat(
        ServerContext* context, const FloatRequest* request, FloatReply* reply) override {
        float value = 3.14;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoDouble(
        ServerContext* context, const DoubleRequest* request, DoubleReply* reply) override {
        double value = 2.718;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoString(
        ServerContext* context, const StringRequest* request, StringReply* reply) override {
        std::string prefix("Hello ");
        reply->set_result(prefix + request->value());
        return Status::OK;
    }
    Status EchoBytes(
        ServerContext* context, const BytesRequest* request, BytesReply* reply) override {
        std::string prefix("Bytes: ");
        reply->set_result(prefix + request->value());
        return Status::OK;
    }
    Status EchoBool(ServerContext* context, const BoolRequest* request, BoolReply* reply) override {
        reply->set_result(!request->value());
        return Status::OK;
    }
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    TestServiceImpl test_service;

    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&test_service);
    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    RunServer();
    return 0;
}
