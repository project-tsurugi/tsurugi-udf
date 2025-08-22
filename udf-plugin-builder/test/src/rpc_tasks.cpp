#include "rpc_tasks.h"
#include <iostream>
#include "udf/generic_client.h"
#include "udf/generic_record_impl.h"

using namespace plugin::udf;
void register_rpc_tasks(TaskManager& manager, generic_client& client) {
    // SayHello
    manager.register_task([&client]() {
        std::cout << "[task] SayHello connect" << std::endl;
        generic_record_impl request;
        request.add_string("hello");

        generic_record_impl response;
        grpc::ClientContext context;
        client.call(context, {0, 0}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_string()) {
                std::cout << "SayHello received: " << *result << std::endl;
            }
        }
    });

    // AddIntOne
    manager.register_task([&client]() {
        std::cout << "[task] AddIntOne connect" << std::endl;
        generic_record_impl request;
        request.add_int4(42);

        generic_record_impl response;
        grpc::ClientContext context;
        client.call(context, {0, 1}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int4()) {
                std::cout << "AddIntOne received: " << *result << std::endl;
            }
        }
    });

    // SayGoodbye
    manager.register_task([&client]() {
        std::cout << "[task] SayGoodbye connect" << std::endl;
        generic_record_impl request;
        request.add_string("Alice");
        request.add_string("See you!");
        request.add_string("Goodbye string");

        generic_record_impl response;
        grpc::ClientContext context;
        client.call(context, {0, 2}, request, response);

        if (auto cursor = response.cursor()) {
            while (auto result = cursor->fetch_string()) {
                std::cout << "SayGoodbye received: " << *result << std::endl;
            }
        }
    });

    // SayWorld
    manager.register_task([&client]() {
        std::cout << "[task] SayWorld connect" << std::endl;
        generic_record_impl request;
        request.add_string("world");

        generic_record_impl response;
        grpc::ClientContext context;
        client.call(context, {0, 3}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_string()) {
                std::cout << "SayWorld received: " << *result << std::endl;
            }
        }
    });

    // DecDecimal
    manager.register_task([&client]() {
        std::cout << "[task] DecDecimal connect" << std::endl;
        generic_record_impl request;
        request.add_string("Dec");
        request.add_int4(3);

        generic_record_impl response;
        grpc::ClientContext context;
        client.call(context, {0, 4}, request, response);

        if (auto cursor = response.cursor()) {
            if (auto result = cursor->fetch_int8()) {
                std::cout << "DecDecimal received: " << *result << std::endl;
            }
        }
    });
}
