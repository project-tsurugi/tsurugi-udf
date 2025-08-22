#include "task_manager.h"
#include "rpc_tasks.h"
#include "udf/generic_client.h"
#include <exception>
#include <functional>
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <vector>

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
        std::unique_ptr<generic_client> client(raw_client);

        register_rpc_tasks(*this, *client);
        this->run_tasks();
    }
}
