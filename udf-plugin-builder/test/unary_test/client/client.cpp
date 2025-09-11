#include "udf/generic_client_factory.h"
#include "udf/generic_record_impl.h"
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <memory>

using namespace plugin::udf;
// @see https://protobuf.dev/programming-guides/proto3/#scalar
int main() {
    auto channel = grpc::CreateChannel("localhost:50051", grpc::InsecureChannelCredentials());

    generic_client_factory* factory = tsurugi_create_generic_client_factory("Greeter");
    if (!factory) {
        std::cerr << "Factory creation failed\n";
        return 1;
    }

    std::unique_ptr<generic_client> client(factory->create(channel));
    if (!client) {
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

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int4()) {
                std::cout << "EchoInt32 received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "EchoInt64 connect" << std::endl;
        generic_record_impl request;
        request.add_int8(64);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 1}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int8()) {
                std::cout << "EchoInt64 received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "EchoUInt32 connect" << std::endl;
        generic_record_impl request;
        request.add_uint4(32);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 2}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_uint4()) {
                std::cout << "EchoInt32 received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "EchoUInt64 connect" << std::endl;
        generic_record_impl request;
        request.add_uint8(64);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 3}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_uint8()) {
                std::cout << "EchoUInt64 received: " << *result << std::endl;
            }
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

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int4()) {
                std::cout << "EchoSInt32 received: " << *result << std::endl;
            }
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

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int8()) {
                std::cout << "EchoSInt64 received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "EchoFloat connect" << std::endl;
        generic_record_impl request;
        request.add_float(3.14f);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 6}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_float()) {
                std::cout << "EchoFloat received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "EchoDouble connect" << std::endl;
        generic_record_impl request;
        request.add_double(3.14);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 7}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_double()) {
                std::cout << "EchoDouble received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "EchoString connect" << std::endl;
        generic_record_impl request;
        request.add_string("Hello, world!");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 8}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_string()) {
                std::cout << "EchoString received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "EchoBytes connect" << std::endl;
        generic_record_impl request;
        request.add_string("Hello, world!");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 9}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_string()) {
                std::cout << "EchoBytes received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "BoolRequest connect" << std::endl;
        generic_record_impl request;
        request.add_bool(true);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 10}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_bool()) {
                std::cout << "EchoBool received: " << *result << std::endl;
            }
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

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_uint4()) {
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

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_uint8()) {
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

        std::cout << "SFixed32Request call" << std::endl;
        client->call(context, {0, 13}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int4()) {
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

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int8()) {
                std::cout << "SFixed64Request received: " << *result << std::endl;
            }
        }
    }
    tsurugi_destroy_generic_client(client.release());
    tsurugi_destroy_generic_client_factory(factory);

    return 0;
}
