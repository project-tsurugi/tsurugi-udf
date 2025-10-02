#include <iostream>
#include <memory>
#include <string>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "sample.grpc.pb.h"
#include "sample.pb.h"

#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class TestServiceImpl final : public TestService::Service {
    Status EchoOneOf(ServerContext* context, const MyRequest* request, MyReply* reply) override {
        std::string prefix("Hello ");
        std::cerr << "EchoOneOf" << std::endl;
        std::cerr << "  prefix: " << prefix << std::endl;
        std::cerr << "  request->aaa(): " << request->aaa() << std::endl;
        std::cerr << "  oneof request->int64_value(): " << request->int64_value() << std::endl;
        std::cerr << "  oneof request->string_value(): " << request->string_value() << std::endl;
        std::cerr << "  oneof request->bool_value(): " << request->bool_value() << std::endl;
        std::cerr << "  request->bbb(): " << request->bbb() << std::endl;
        std::cerr << "  oneof request->int64_value2(): " << request->int64_value2() << std::endl;
        std::cerr << "  oneof request->string_value2(): " << request->string_value2() << std::endl;
        std::cerr << "  oneof request->bool_value2(): " << request->bool_value2() << std::endl;

        reply->set_int64_result(64 + request->int64_value());
        reply->set_string_result(prefix + request->string_value());
        return Status::OK;
    }
};

void RunServer(const std::string& server_address, const std::string& credentials) {
    TestServiceImpl test_service;


    grpc::ServerBuilder builder;

    if(credentials == "insecure") {
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    } else {
        std::cerr << "[WARN] Unsupported credentials: " << credentials << " (falling back to insecure)\n";
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    }

    builder.RegisterService(&test_service);

    std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    std::string server_address = "0.0.0.0:50051";
    std::string credentials = "insecure";

    if(argc >= 2) {
        std::string ini_file = argv[1];
        boost::property_tree::ptree pt;
        try {
            boost::property_tree::ini_parser::read_ini(ini_file, pt);
            server_address = pt.get<std::string>("grpc.url", server_address);
            credentials = pt.get<std::string>("grpc.credentials", credentials);
            std::cout << "[INFO] Loaded gRPC settings from " << ini_file << "\n";
        } catch(const boost::property_tree::ini_parser_error& e) {
            std::cerr << "[WARN] Failed to read ini file '" << ini_file << "': " << e.what() << "\n";
            std::cerr << "[INFO] Using default gRPC settings\n";
        }
    } else {
        std::cout << "[INFO] No ini file specified. Using default gRPC settings\n";
    }

    RunServer(server_address, credentials);
    return 0;
}
