#include <iostream>
#include <memory>
#include <string>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "complex_types.pb.h"
#include "nested_test.grpc.pb.h"
#include "nested_test.pb.h"

#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class NestedImpl final : public Nested::Service {
    Status NestedHello(ServerContext* context, const SimpleValue* request, SimpleValue* reply) override {
        std::cout << "[NestedHello]" << std::endl;
        std::cout << "value :" << request->value() << std::endl;
        reply->set_value("hello" + request->value());
        return Status::OK;
    }
    Status
    DecimalOne(ServerContext* context, const tsurugidb::udf::value::Decimal* request, SimpleValue* reply) override {
        std::cout << "[DecimalOne]" << std::endl;
        std::cout << "unscaled_value size: " << request->unscaled_value().size()
                  << ", exponent: " << request->exponent() << std::endl;

        reply->set_value("DecimalOne received");
        return Status::OK;
    }

    Status DecimalTwo(ServerContext* context, const AddDecimal* request, SimpleValue* reply) override {
        std::cout << "[DecimalTwo]" << std::endl;
        std::cout << "i32: " << request->i32() << std::endl;
        std::cout << "unscaled_value size: " << request->dec().unscaled_value().size()
                  << ", exponent: " << request->dec().exponent() << std::endl;

        reply->set_value("DecimalTwo received");
        return Status::OK;
    }
};

void RunServer(const std::string& server_address, const std::string& credentials) {
    NestedImpl test_service;


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
