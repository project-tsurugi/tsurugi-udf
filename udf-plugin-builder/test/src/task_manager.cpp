#include "task_manager.h"
#include "udf/generic_client.h"
#include "udf/generic_record_impl.h"
#include <exception>
#include <functional>
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <vector>
using namespace plugin::udf;
void TaskManager::shutdown() {
    tasks_.clear();
    clients_.clear();
    loader_.reset();
}
void TaskManager::register_task(std::function<void()> fn) { tasks_.push_back(std::move(fn)); }

void TaskManager::run_tasks() const {
    for (size_t i = 0; i < tasks_.size(); ++i) {
        try {
            tasks_[i]();
        } catch (const std::exception& ex) {
            std::cerr << "[TaskManager] Exception in task " << i << ": " << ex.what() << std::endl;
        } catch (...) { std::cerr << "[TaskManager] Unknown exception in task " << i << std::endl; }
    }
}
void TaskManager::set_loader(std::unique_ptr<plugin::udf::plugin_loader> l) {
    loader_ = std::move(l);
}
plugin::udf::plugin_loader* TaskManager::get_loader() const { return loader_.get(); }
void TaskManager::set_functions() {
    auto plugins = (loader_)->get_plugins();
    for (const auto& plugin : plugins) {
        print_plugin_info(std::get<0>(plugin));
        auto factory = std::get<1>(plugin);
        if (!factory) {
            std::cerr << "[main] Factory creation failed" << std::endl;
            return;
        }
        std::cerr << "[main] Factory created: " << factory << std::endl;
        auto channel = grpc::CreateChannel("localhost:50051", grpc::InsecureChannelCredentials());
        auto raw_client = factory->create(channel);
        if (!raw_client) {
            std::cerr << "[main] generic_client creation failed" << std::endl;
            return;
        }
        clients_.push_back(std::shared_ptr<generic_client>(raw_client));
    }
}
void TaskManager::register_rpc_tasks() {
    for (const auto& client : clients_) {
        // SayHello
        register_task([client]() {
            std::cout << "[task] SayHello connect" << std::endl;
            generic_record_impl request;
            request.add_string("hello");

            generic_record_impl response;
            grpc::ClientContext context;
            client->call(context, {0, 0}, request, response);

            if (auto cursor = response.cursor()) {
                if (auto result = cursor->fetch_string()) {
                    std::cout << "SayHello received: " << *result << std::endl;
                }
            }
        });

        // AddIntOne
        register_task([client]() {
            std::cout << "[task] AddIntOne connect" << std::endl;
            generic_record_impl request;
            request.add_int4(42);

            generic_record_impl response;
            grpc::ClientContext context;
            client->call(context, {0, 1}, request, response);

            if (auto cursor = response.cursor()) {
                if (auto result = cursor->fetch_int4()) {
                    std::cout << "AddIntOne received: " << *result << std::endl;
                }
            }
        });

        // SayGoodbye
        register_task([client]() {
            std::cout << "[task] SayGoodbye connect" << std::endl;
            generic_record_impl request;
            request.add_string("Alice");
            request.add_string("See you!");
            request.add_string("Goodbye string");

            generic_record_impl response;
            grpc::ClientContext context;
            client->call(context, {0, 2}, request, response);

            if (auto cursor = response.cursor()) {
                while (auto result = cursor->fetch_string()) {
                    std::cout << "SayGoodbye received: " << *result << std::endl;
                }
            }
        });

        // SayWorld
        register_task([client]() {
            std::cout << "[task] SayWorld connect" << std::endl;
            generic_record_impl request;
            request.add_string("world");

            generic_record_impl response;
            grpc::ClientContext context;
            client->call(context, {0, 3}, request, response);

            if (auto cursor = response.cursor()) {
                if (auto result = cursor->fetch_string()) {
                    std::cout << "SayWorld received: " << *result << std::endl;
                }
            }
        });

        // DecDecimal
        register_task([client]() {
            std::cout << "[task] DecDecimal connect" << std::endl;
            generic_record_impl request;
            request.add_string("Dec");
            request.add_int4(3);

            generic_record_impl response;
            grpc::ClientContext context;
            client->call(context, {0, 4}, request, response);

            if (auto cursor = response.cursor()) {
                if (auto result = cursor->fetch_int8()) {
                    std::cout << "DecDecimal received: " << *result << std::endl;
                }
            }
        });
    }
}
