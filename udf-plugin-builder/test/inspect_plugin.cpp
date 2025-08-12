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
    grpc_init();

    if (argc < 2) {
        std::cerr << "Usage: inspect_plugin <path_to_plugin.so>" << std::endl;
        return 1;
    }
    const char* so_path = argv[1];
    {
        std::unique_ptr<plugin_loader> loader = std::make_unique<udf_loader>();
        loader->load(so_path);
        auto factory = loader->get_factory();
        if (!factory) {
            std::cerr << "[main] Factory creation failed" << std::endl;
            return 1;
        }
        std::cerr << "[main] Factory created: " << factory << std::endl;
        auto channel = grpc::CreateChannel("localhost:50051", grpc::InsecureChannelCredentials());
        auto raw_client = factory->create(channel);
        if (!raw_client) {
            std::cerr << "[main] generic_client creation failed" << std::endl;
            return 1;
        }
        std::unique_ptr<generic_client> client(raw_client);
        try {
            std::cout << "[main] SayHello connect" << std::endl;
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
        } catch (const std::exception& ex) {
            std::cerr << "[main] Exception during RPC call: " << ex.what() << std::endl;
        }
        try {
            std::cout << "[main] AddIntOne connect" << std::endl;
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
        } catch (const std::exception& ex) {
            std::cerr << "[main] Exception during RPC call: " << ex.what() << std::endl;
        }
        try {
            std::cout << "[main] SayWolrd connect" << std::endl;
            generic_record_impl request;
            request.add_string("world");

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 2}, request, response);

            if (auto cursor = response.cursor()) {
                if (auto result = cursor->fetch_string()) {
                    std::cout << "Greeter received: " << *result << std::endl;
                }
            }
        } catch (const std::exception& ex) {
            std::cerr << "[main] Exception during RPC call: " << ex.what() << std::endl;
        }
        try {
            std::cout << "[main] DecDecimal connect" << std::endl;
            generic_record_impl request;
            request.add_string("Dec");
            request.add_int4(3);
            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 3}, request, response);

            if (auto cursor = response.cursor()) {
                if (auto result = cursor->fetch_int8()) {
                    std::cout << "Greeter received: " << *result << std::endl;
                }
            }
        } catch (const std::exception& ex) {
            std::cerr << "[main] Exception during RPC call: " << ex.what() << std::endl;
        }
        client.reset();
        channel.reset();
        loader->unload_all();
        grpc_shutdown();
    }
    return 0;
}