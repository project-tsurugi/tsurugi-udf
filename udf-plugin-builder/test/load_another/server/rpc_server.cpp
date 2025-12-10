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

class GreeterServiceImpl final : public Greeter::Service {
    Status SayHello(ServerContext* context, const StringValue* request, StringValue* reply) override {
        std::string prefix("Hello ");
        std::cerr << "SayHello" << std::endl;
        std::cerr << "  prefix: " << prefix << std::endl;
        std::cerr << "  request->value(): " << request->value() << std::endl;
        reply->set_value(prefix + request->value());
        return Status::OK;
    }
    Status IntAddInt(ServerContext* context, const Int32Value* request, Int32Value* reply) override {
        std::cerr << "IntAddInt" << std::endl;
        std::cerr << "  request->value(): " << request->value() << std::endl;
        int sum = request->value() + 1;
        reply->set_value(sum);
        return Status::OK;
    }
    Status EmptyReq(ServerContext* context, const Empty* request, Int32Value* reply) override {
        std::cerr << "EmptyReq" << std::endl;
        reply->set_value(111);
        return Status::OK;
    }
};

class ByerServiceImpl final : public Byer::Service {
    Status SayWorld(ServerContext* context, const StringValue* request, StringValue* reply) override {
        std::string prefix("World ");
        std::cerr << "SayWorld" << std::endl;
        std::cerr << "  prefix: " << prefix << std::endl;
        std::cerr << "  request->value(): " << request->value() << std::endl;
        reply->set_value(prefix + request->value());
        return Status::OK;
    }
};
void RunServer(const std::string& server_address, const std::string& secure) {
    GreeterServiceImpl greeter_service;
    ByerServiceImpl byer_service;

    grpc::ServerBuilder builder;

    if(secure == "false") {
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    } else {
        std::cerr << "[WARN] Unsupported secure: " << secure << " (falling back to false)\n";
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    }

    builder.RegisterService(&greeter_service);
    builder.RegisterService(&byer_service);

    std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    std::string server_address = "0.0.0.0:50051";
    std::string secure = "false";

    if(argc >= 2) {
        std::string ini_file = argv[1];
        boost::property_tree::ptree pt;
        try {
            boost::property_tree::ini_parser::read_ini(ini_file, pt);
            server_address = pt.get<std::string>("udf.endpoint", server_address);
            secure = pt.get<std::string>("udf.secure", secure);
            std::cout << "[INFO] Loaded gRPC settings from " << ini_file << "\n";
        } catch(const boost::property_tree::ini_parser_error& e) {
            std::cerr << "[WARN] Failed to read ini file '" << ini_file << "': " << e.what() << "\n";
            std::cerr << "[INFO] Using default gRPC settings\n";
        }
    } else {
        std::cout << "[INFO] No ini file specified. Using default gRPC settings\n";
    }

    RunServer(server_address, secure);
    return 0;
}
