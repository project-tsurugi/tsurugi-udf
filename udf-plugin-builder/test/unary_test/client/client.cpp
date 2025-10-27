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
            grpc_url = pt.get<std::string>("udf.url", grpc_url);
            credentials = pt.get<std::string>("udf.credentials", credentials);
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
        std::cout << "EchoInt32 connect" << std::endl;
        generic_record_impl request;
        request.add_int4(32);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 0}, request, response);
        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int4()) { std::cout << "EchoInt32 received: " << *result << std::endl; }
        } else {
            std::cerr << "No response cursor\n";
        }
    }
    {
        std::cout << "EchoInt64 connect" << std::endl;
        generic_record_impl request;
        request.add_int8(64);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 1}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int8()) { std::cout << "EchoInt64 received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "EchoUInt32 connect" << std::endl;
        generic_record_impl request;
        request.add_uint4(32);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 2}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_uint4()) { std::cout << "EchoInt32 received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "EchoUInt64 connect" << std::endl;
        generic_record_impl request;
        request.add_uint8(64);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 3}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_uint8()) { std::cout << "EchoUInt64 received: " << *result << std::endl; }
        }
    }
    // sint32	int32_t
    {
        std::cout << "EchoSInt32 connect" << std::endl;
        generic_record_impl request;
        request.add_int4(32);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 4}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int4()) { std::cout << "EchoSInt32 received: " << *result << std::endl; }
        }
    }
    // sint64	int64_t
    {
        std::cout << "EchoSInt64 connect" << std::endl;
        generic_record_impl request;
        request.add_int8(64);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 5}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int8()) { std::cout << "EchoSInt64 received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "EchoFloat connect" << std::endl;
        generic_record_impl request;
        request.add_float(3.14f);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 6}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_float()) { std::cout << "EchoFloat received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "EchoDouble connect" << std::endl;
        generic_record_impl request;
        request.add_double(3.14);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 7}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_double()) { std::cout << "EchoDouble received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "EchoString connect" << std::endl;
        generic_record_impl request;
        request.add_string("Hello, world!");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 8}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) { std::cout << "EchoString received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "EchoBytes connect" << std::endl;
        generic_record_impl request;
        request.add_string("Hello, world!");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 9}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) { std::cout << "EchoBytes received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "BoolRequest connect" << std::endl;
        generic_record_impl request;
        request.add_bool(true);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 10}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_bool()) { std::cout << "EchoBool received: " << *result << std::endl; }
        }
    }
    // fixed32	uint32_t
    {
        std::cout << "Fixed32Request connect" << std::endl;
        generic_record_impl request;
        request.add_uint4(32);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 11}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_uint4()) {
                std::cout << "Fixed32Request received: " << *result << std::endl;
            }
        }
    }
    // fixed64	uint64_t
    {
        std::cout << "Fixed64Request connect" << std::endl;
        generic_record_impl request;
        request.add_uint8(64);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 12}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_uint8()) {
                std::cout << "Fixed64Request received: " << *result << std::endl;
            }
        }
    }
    // sfixed32	int32_t
    {
        std::cout << "SFixed32Request connect" << std::endl;
        generic_record_impl request;
        request.add_int4(32);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 13}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int4()) {
                std::cout << "SFixed32Request received: " << *result << std::endl;
            }
        }
    }
    // sfixed64	int64_t
    {
        std::cout << "SFixed64Request connect" << std::endl;
        generic_record_impl request;
        request.add_int8(64);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 14}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int8()) {
                std::cout << "SFixed64Request received: " << *result << std::endl;
            }
        }
    }
    // rpc ConcatInt32String     (Int32StringRequest)     returns (Int32StringReply);
    {
        std::cout << "ConcatInt32String connect" << std::endl;
        generic_record_impl request;
        request.add_int4(2);
        request.add_string("three");
        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 15}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) {
                std::cout << "ConcatInt32Stringg received: " << *result << std::endl;
            }
        }
    }
    // rpc ConcatStringInt32(StringInt32Request) returns(StringInt32Reply);

    {
        std::cout << "ConcatStringInt32 connect" << std::endl;
        generic_record_impl request;
        request.add_string("one");
        request.add_int4(2);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 16}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) {
                std::cout << "ConcatStringInt32 received: " << *result << std::endl;
            }
        }
    }
    // rpc SumInt32Int64(Int32Int64Request) returns(Int32Int64Reply);

    {
        std::cout << "SumInt32Int64 connect" << std::endl;
        generic_record_impl request;
        request.add_int4(1);
        request.add_int8(2);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 17}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_int8()) { std::cout << "SumInt32Int64 received: " << *result << std::endl; }
        }
    }
    {
        std::cout << "MultiplyFloatDouble connect" << std::endl;
        generic_record_impl request;
        request.add_float(1.0f);
        request.add_double(2.0);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 18}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_double()) {
                std::cout << "MultiplyFloatDouble received: " << *result << std::endl;
            }
        }
    }
    // rpc CombineStringBytes(StringBytesRequest) returns(StringBytesReply);
    {
        std::cout << "CombineStringBytes connect" << std::endl;
        generic_record_impl request;
        request.add_string("one");
        request.add_string("two");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 19}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) {
                std::cout << "CombineStringBytes received: " << *result << std::endl;
            }
        }
    }
    // rpc FormatBoolInt32String(BoolInt32StringRequest) returns(BoolInt32StringReply);
    {
        std::cout << "FormatBoolInt32String connect" << std::endl;
        generic_record_impl request;
        request.add_bool(true);
        request.add_int4(42);
        request.add_string("Hello");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 20}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) {
                std::cout << "FormatBoolInt32String received: " << *result << std::endl;
            }
        }
    }
    // rpc UseAllTypes (AllTypesRequest) returns (AllTypesReply);
    {
        std::cout << "UseAllTypes connect" << std::endl;
        generic_record_impl request;
        request.add_int4(42);
        request.add_int8(64);
        request.add_uint4(32);
        request.add_uint8(64);
        request.add_int4(32);
        request.add_int8(64);
        request.add_uint4(32);
        request.add_uint8(64);
        request.add_int4(32);
        request.add_int8(64);
        request.add_float(3.14f);
        request.add_double(3.14);
        request.add_string("Hello, world!");
        request.add_string("Hello, world!");
        request.add_bool(true);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 21}, request, response);

        auto err = response.error();
        if(err) {
            print_error(*err);
        } else if(auto cursor = response.cursor()) {
            if(auto result = cursor->fetch_string()) { std::cout << "UseAllTypes received: " << *result << std::endl; }
        }
    }
    tsurugi_destroy_generic_client(client.release());
    tsurugi_destroy_generic_client_factory(factory);

    return 0;
}
