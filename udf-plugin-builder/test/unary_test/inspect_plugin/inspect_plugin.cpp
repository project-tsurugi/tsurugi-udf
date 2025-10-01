#include <dlfcn.h>
#include <iostream>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

#include "task_manager.h"
#include "udf/descriptor_impl.h"
#include "udf/generic_client.h"
#include "udf/generic_client_factory.h"
#include "udf/generic_record_impl.h"
#include "udf/plugin_api.h"
#include "udf/plugin_loader.h"
#include "udf/udf_loader.h"

#include <grpcpp/grpcpp.h>

using namespace plugin::udf;
int main(int argc, char** argv) {
    if(argc < 2) {
        std::cerr << "Usage: inspect_plugin <path_to_plugin.so>" << std::endl;
        return 1;
    }
    const char* so_path = argv[1];
    TaskManager manager;
    std::unique_ptr<plugin_loader> loader = std::make_unique<udf_loader>();
    loader->load(so_path);
    manager.set_loader(std::move(loader));
    grpc_init();
    manager.set_functions();
    manager.register_rpc_tasks();
    manager.run_tasks();
    manager.shutdown();
    grpc_shutdown();
    return 0;
}
