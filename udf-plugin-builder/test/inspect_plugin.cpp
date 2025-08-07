#include "descriptor_impl.h"
#include "udf/plugin_api.h"
#include "udf/plugin_loader.h"
#include "udf/udf_loader.h"
#include <dlfcn.h>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using namespace plugin::udf;

int main(int argc, char** argv) {
    std::unique_ptr<plugin_loader> loader = std::make_unique<udf_loader>();
    if (argc < 2) {
        std::cerr << "Usage: inspect_plugin <path_to_plugin.so>" << std::endl;
        return 1;
    }

    const char* so_path = argv[1];
    loader->load(so_path);
    auto apis = loader->apis();

    for (const auto* api : apis) {
        const auto& pkgs = api->packages();
        for (const auto* pkg : pkgs) {
            std::cout << "Package: " << pkg->package_name() << std::endl;

            for (const auto* svc : pkg->services()) {
                std::cout << "  Service: " << svc->service_name() << std::endl;
                std::cout << "    Index: " << svc->service_index() << std::endl;
                for (const auto* fn : svc->functions()) {
                    std::cout << "    Function: " << fn->function_name() << std::endl;
                    std::cout << "      Index: " << fn->function_index() << std::endl;
                    std::cout << "      Kind: " << plugin::udf::to_string(fn->function_kind())
                              << std::endl;

                    const auto& input = fn->input_record();
                    std::cout << "      Input record: " << input.record_name() << std::endl;
                    for (const auto* col : input.columns()) {
                        std::cout << "        - " << col->column_name() << " : "
                                  << plugin::udf::to_string(col->type_kind()) << std::endl;
                    }

                    const auto& output = fn->output_record();
                    std::cout << "      Output record: " << output.record_name() << std::endl;
                    for (const auto* col : output.columns()) {
                        std::cout << "        - " << col->column_name() << " : "
                                  << plugin::udf::to_string(col->type_kind()) << std::endl;
                    }
                }
            }
        }
    }
    loader->unload_all();
    return 0;
}
