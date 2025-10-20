#include <iostream>
#include <memory>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "error_info.h"
#include "generic_client_factory.h"
#include "generic_record_impl.h"

#include <grpcpp/grpcpp.h>

using namespace plugin::udf;
// @see https://protobuf.dev/programming-guides/proto3/#scalar

void print_error(const error_info& err) {
    std::cerr << "RPC failed: code=" << err.code() << ", message=" << err.message() << std::endl;
}
int main(int argc, char** argv) {
    std::string grpc_url = "localhost:50051";
    std::string credentials = "insecure";

    if(argc >= 2) {
        std::string ini_file = argv[1];
        boost::property_tree::ptree pt;
        try {
            boost::property_tree::ini_parser::read_ini(ini_file, pt);
            grpc_url = pt.get<std::string>("grpc.url", grpc_url);
            credentials = pt.get<std::string>("grpc.credentials", credentials);
            std::cout << "[INFO] Loaded gRPC settings from " << ini_file << "\n";
        } catch(const boost::property_tree::ini_parser_error& e) {
            std::cerr << "[WARN] Failed to read ini file '" << ini_file << "': " << e.what() << "\n";
            std::cerr << "[INFO] Using default gRPC settings\n";
        }
    } else {
        std::cout << "[INFO] No ini file specified. Using default gRPC settings\n";
    }

    auto channel = grpc::CreateChannel(grpc_url, grpc::InsecureChannelCredentials());

    generic_client_factory* factory = tsurugi_create_generic_client_factory("Greeter");
    if(! factory) {
        std::cerr << "Factory creation failed\n";
        return 1;
    }

    std::unique_ptr<generic_client> client(factory->create(channel));
    if(! client) {
        std::cerr << "Client creation failed\n";
        tsurugi_destroy_generic_client_factory(factory);
        return 1;
    }
    {
        std::cout << "NestedHello connect" << std::endl;
        generic_record_impl request;
        request.add_string("world");
        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 0}, request, response);
        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) { std::cout << "fetch_string received: " << *result << std::endl; }
        } else {
            std::cerr << "No response cursor\n";
        }
    }
    {
        std::cout << "DecimalOne connect" << std::endl;
        generic_record_impl request;
        request.add_string("aaaaa");
        request.add_int4(32);
        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 1}, request, response);
        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int4()) { std::cout << "fetch_int4 received: " << *result << std::endl; }
            if(auto result = cursor->fetch_int8()) { std::cout << "fetch_int8 received: " << *result << std::endl; }
            if(auto result = cursor->fetch_string()) { std::cout << "fetch_string received: " << *result << std::endl; }
        } else {
            std::cerr << "No response cursor\n";
        }
    }
    {
        std::cout << "DecimalTwo connect" << std::endl;
        generic_record_impl request;
        request.add_int4(32);
        request.add_string("aaaaa");
        request.add_int4(32);
        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 2}, request, response);
        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int4()) { std::cout << "fetch_int4 received: " << *result << std::endl; }
            if(auto result = cursor->fetch_int8()) { std::cout << "fetch_int8 received: " << *result << std::endl; }
            if(auto result = cursor->fetch_string()) { std::cout << "fetch_string received: " << *result << std::endl; }
        } else {
            std::cerr << "No response cursor\n";
        }
    }
    tsurugi_destroy_generic_client(client.release());
    tsurugi_destroy_generic_client_factory(factory);

    return 0;
}
