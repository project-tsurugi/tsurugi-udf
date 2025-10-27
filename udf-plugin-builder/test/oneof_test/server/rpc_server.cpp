#include <iostream>
#include <memory>
#include <string>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "oneof_test.grpc.pb.h"
#include "oneof_test.pb.h"

#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class OneImpl final : public One::Service {
    Status OneofAlpha(ServerContext* context, const Mm* request, Mm* reply) override {
        std::cout << "OneofAlpha" << std::endl;
        std::cout << "a :" << request->a() << std::endl;
        reply->set_a(64 + request->a());
        return Status::OK;
    }
    Status OneofBeta(ServerContext* context, const Ab* request, Mm* reply) override {
        std::cout << "OneofBeta" << std::endl;
        std::cout << "int64_result :" << request->int64_result() << std::endl;
        std::cout << "string_result :" << request->string_result() << std::endl;
        reply->set_a(64 + request->int64_result());
        return Status::OK;
    }
    Status EchoOneOf(ServerContext* context, const MyRequest* request, MyReply* reply) override {
        std::string prefix("Hello ");
        std::cout << "EchoOneOf" << std::endl;
        std::cout << "  prefix: " << prefix << std::endl;
        std::cout << "  request->aaa(): " << request->aaa() << std::endl;
        std::cout << "  oneof request->int64_value(): " << request->int64_value() << std::endl;
        std::cout << "  oneof request->string_value(): " << request->string_value() << std::endl;
        std::cout << "  oneof request->bool_value(): " << request->bool_value() << std::endl;
        std::cout << "  request->bbb(): " << request->bbb() << std::endl;
        std::cout << "  oneof request->int64_value2(): " << request->int64_value2() << std::endl;
        std::cout << "  oneof request->string_value2(): " << request->string_value2() << std::endl;
        std::cout << "  oneof request->bool_value2(): " << request->bool_value2() << std::endl;


        switch(request->arg_case()) {
            case MyRequest::kInt64Value:
                std::cout << "  oneof request->int64_value(): " << request->int64_value() << std::endl;
                break;
            case MyRequest::kStringValue:
                std::cout << "  oneof request->string_value(): " << request->string_value() << std::endl;
                break;
            case MyRequest::kBoolValue:
                std::cout << "  oneof request->bool_value(): " << std::boolalpha << request->bool_value() << std::endl;
                break;
            default: std::cout << "  oneof (arg) not set" << std::endl; break;
        }

        switch(request->aab_case()) {
            case MyRequest::kInt64Value2:
                std::cout << "  oneof request->int64_value2(): " << request->int64_value2() << std::endl;
                break;
            case MyRequest::kStringValue2:
                std::cout << "  oneof request->string_value2(): " << request->string_value2() << std::endl;
                break;
            case MyRequest::kBoolValue2:
                std::cout << "  oneof request->bool_value2(): " << std::boolalpha << request->bool_value2()
                          << std::endl;
                break;
            default: std::cout << "  oneof (aab) not set" << std::endl; break;
        }

        std::ostringstream oss;
        oss << prefix << request->aaa();

        if(request->arg_case() == MyRequest::kInt64Value) {
            oss << request->int64_value();
        } else if(request->arg_case() == MyRequest::kStringValue) {
            oss << request->string_value();
        } else if(request->arg_case() == MyRequest::kBoolValue) {
            oss << (request->bool_value() ? "true" : "false");
        }

        if(request->aab_case() == MyRequest::kInt64Value2) {
            oss << request->int64_value2();
        } else if(request->aab_case() == MyRequest::kStringValue2) {
            oss << request->string_value2();
        } else if(request->aab_case() == MyRequest::kBoolValue2) {
            oss << (request->bool_value2() ? "true" : "false");
        }

        reply->set_string_result(oss.str());
        return Status::OK;
    }
};

void RunServer(const std::string& server_address, const std::string& credentials) {
    OneImpl test_service;


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
            server_address = pt.get<std::string>("udf.url", server_address);
            credentials = pt.get<std::string>("udf.credentials", credentials);
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
