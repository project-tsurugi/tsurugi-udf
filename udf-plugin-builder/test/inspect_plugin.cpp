#include "descriptor_impl.h"
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
#include <vector>

using namespace plugin::udf;

void print_plugin_info(const std::vector<plugin_api*>& apis) {
    std::cout << "packages:" << std::endl;

    for (const auto* api : apis) {
        const auto& pkgs = api->packages();
        for (const auto* pkg : pkgs) {
            std::cout << "  - package_name: " << pkg->package_name() << std::endl;
            std::cout << "    services:" << std::endl;

            for (const auto* svc : pkg->services()) {
                std::cout << "      - service_name: " << svc->service_name() << std::endl;
                std::cout << "        service_index: " << svc->service_index() << std::endl;
                std::cout << "        functions:" << std::endl;

                for (const auto* fn : svc->functions()) {
                    std::cout << "          - function_name: " << fn->function_name() << std::endl;
                    std::cout << "            function_index: " << fn->function_index()
                              << std::endl;
                    std::cout << "            function_kind: "
                              << plugin::udf::to_string(fn->function_kind()) << std::endl;

                    const auto& input = fn->input_record();
                    std::cout << "            input_record:" << std::endl;
                    std::cout << "              record_name: " << input.record_name() << std::endl;
                    std::cout << "              columns:" << std::endl;
                    for (const auto* col : input.columns()) {
                        std::cout << "                - column_name: " << col->column_name()
                                  << std::endl;
                        std::cout << "                  type_kind: "
                                  << plugin::udf::to_string(col->type_kind()) << std::endl;
                    }

                    const auto& output = fn->output_record();
                    std::cout << "            output_record:" << std::endl;
                    std::cout << "              record_name: " << output.record_name() << std::endl;
                    std::cout << "              columns:" << std::endl;
                    for (const auto* col : output.columns()) {
                        std::cout << "                - column_name: " << col->column_name()
                                  << std::endl;
                        std::cout << "                  type_kind: "
                                  << plugin::udf::to_string(col->type_kind()) << std::endl;
                    }
                }
            }
        }
    }
}

int main(int argc, char** argv) {
    std::unique_ptr<plugin_loader> loader = std::make_unique<udf_loader>();
    if (argc < 2) {
        std::cerr << "Usage: inspect_plugin <path_to_plugin.so>" << std::endl;
        return 1;
    }

    const char* so_path = argv[1];
    loader->load(so_path);
    auto apis = loader->apis();

    print_plugin_info(apis);

    loader->unload_all();
    return 0;
}
