#include <iostream>
#include <memory>
#include <string>

#include "test_all.grpc.pb.h"
#include "test_all.pb.h"
#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class TestServiceImpl final : public TestService::Service {
    Status EchoString(
        ServerContext* context, const StringRequest* request, StringReply* reply) override {
        std::string prefix("Hello ");
        reply->set_result(prefix + request->value());
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
