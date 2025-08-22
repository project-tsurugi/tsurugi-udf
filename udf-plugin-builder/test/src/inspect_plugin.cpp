#include "descriptor_impl.h"
#include "rpc_tasks.h"
#include "task_manager.h"
#include "udf/generic_client.h"
#include "udf/generic_client_factory.h"
#include "udf/generic_record_impl.h"
#include "udf/plugin_api.h"
#include "udf/plugin_loader.h"
#include "udf/udf_loader.h"
#include <dlfcn.h>
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

using namespace plugin::udf;
int main(int argc, char** argv) {
    TaskManager manager;
    grpc_init();
    if (argc < 2) {
        std::cerr << "Usage: inspect_plugin <path_to_plugin.so>" << std::endl;
        return 1;
    }
    const char* so_path = argv[1];
    {
        std::unique_ptr<plugin_loader> loader = std::make_unique<udf_loader>();
        loader->load(so_path);
        auto plugins = loader->get_plugins();
        for (const auto& plugin : plugins) {
            print_plugin_info(std::get<0>(plugin));
            auto factory = std::get<1>(plugin);
            if (!factory) {
                std::cerr << "[main] Factory creation failed" << std::endl;
                return 1;
            }
            std::cerr << "[main] Factory created: " << factory << std::endl;
            auto channel =
                grpc::CreateChannel("localhost:50051", grpc::InsecureChannelCredentials());
            auto raw_client = factory->create(channel);
            if (!raw_client) {
                std::cerr << "[main] generic_client creation failed" << std::endl;
                return 1;
            }
            std::unique_ptr<generic_client> client(raw_client);

            register_rpc_tasks(manager, *client);
            manager.run_tasks();
        }
    }
    grpc_shutdown();
    return 0;
}
