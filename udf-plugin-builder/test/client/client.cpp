#include "udf/generic_client_factory.h"
#include "udf/generic_record_impl.h"
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <memory>

using namespace plugin::udf;
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
        std::cout << "SayHello connect" << std::endl;
        generic_record_impl request;
        request.add_string("hello");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 0}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_string()) {
                std::cout << "Greeter received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "IntAddInt connect" << std::endl;
        generic_record_impl request;
        request.add_int4(42);

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 1}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int4()) {
                std::cout << "Greeter received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "SayGoodbye connect" << std::endl;
        generic_record_impl request;
        request.add_string("Alice");
        request.add_string("See you!");
        request.add_string("Goodbye string");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 2}, request, response);

        if (auto cursor = response.cursor()) {
            while (auto result = cursor->fetch_string()) {
                std::cout << "Greeter SayGoodbye received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "SayWorld connect" << std::endl;
        generic_record_impl request;
        request.add_string("world");

        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 3}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_string()) {
                std::cout << "Byer SayWorld received: " << *result << std::endl;
            }
        }
    }
    {
        std::cout << "DecDecimal connect" << std::endl;
        generic_record_impl request;
        request.add_string("Dec");
        request.add_int4(3);
        generic_record_impl response;
        grpc::ClientContext context;

        client->call(context, {0, 4}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int8()) {
                std::cout << "Byer DecDecimal received: " << *result << std::endl;
            }
        }
    }

    tsurugi_destroy_generic_client(client.release());
    tsurugi_destroy_generic_client_factory(factory);

    return 0;
}
