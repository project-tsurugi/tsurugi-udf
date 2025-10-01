#include "task_manager.h"

#include <exception>
#include <functional>
#include <iostream>
#include <vector>

#include "udf/generic_client.h"
#include "udf/generic_record_impl.h"

#include <grpcpp/grpcpp.h>
using namespace plugin::udf;

void print_error(const error_info& err) {
    std::cerr << "RPC failed: code=" << err.code_string() << ", message=" << err.message() << std::endl;
}
void TaskManager::shutdown() {
    tasks_.clear();
    plugins_.clear();
    loader_.reset();
}
void TaskManager::register_task(std::function<void()> fn) { tasks_.push_back(std::move(fn)); }

void TaskManager::run_tasks() const {
    for(size_t i = 0; i < tasks_.size(); ++i) {
        try {
            tasks_[i]();
        } catch(const std::exception& ex) {
            std::cerr << "[TaskManager] Exception in task " << i << ": " << ex.what() << std::endl;
        } catch(...) { std::cerr << "[TaskManager] Unknown exception in task " << i << std::endl; }
    }
}
void TaskManager::set_loader(std::unique_ptr<plugin::udf::plugin_loader> l) { loader_ = std::move(l); }
plugin::udf::plugin_loader* TaskManager::get_loader() const { return loader_.get(); }
void TaskManager::set_functions() {
    auto plugins = (loader_)->get_plugins();
    for(const auto& plugin: plugins) {
        auto factory = std::get<1>(plugin);
        plugins_.emplace_back(
            std::shared_ptr<plugin_api>(std::get<0>(plugin)),
            std::shared_ptr<generic_client>(std::get<1>(plugin))
        );
    }
}
void TaskManager::register_rpc_tasks() {
    for(const auto& tup: plugins_) {
        auto client = std::get<1>(tup);
        auto plugin = std::get<0>(tup);
        print_plugin_info(plugin);
        auto packages = plugin->packages();
        for(const auto* pkg: packages) {
            for(const auto* svc: pkg->services()) {
                for(const auto* fn: svc->functions()) {
                    register_task([client, pkg, svc, fn]() {
                        generic_record_impl request;
                        generic_record_impl response;
                        grpc::ClientContext context;
                        std::cout << "[package] " << pkg->package_name() << std::endl;
                        std::cout << "  [service] " << svc->service_name() << std::endl;
                        std::cout << "    [function] " << fn->function_name() << std::endl;
                        const auto& input = fn->input_record();
                        const auto& output = fn->output_record();
                        std::vector<NativeValue> inputs = column_to_native_values(input.columns());
                        for(const auto& input: inputs) { add_arg_value(request, input); }
                        client->call(context, {0, fn->function_index()}, request, response);
                        std::vector<NativeValue> output_values = cursor_to_native_values(response, output.columns());
                        print_native_values(output_values);
                    });
                }
            }
        }

        register_task([client]() {
            std::cout << "EchoInt32 connect" << std::endl;
            generic_record_impl request;
            request.add_int4(32);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 0}, request, response);
            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_int4()) { std::cout << "EchoInt32 received: " << *result << std::endl; }
            } else {
                std::cerr << "No response cursor\n";
            }
        });
        register_task([client]() {
            std::cout << "EchoInt64 connect" << std::endl;
            generic_record_impl request;
            request.add_int8(64);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 1}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_int8()) { std::cout << "EchoInt64 received: " << *result << std::endl; }
            }
        });
        register_task([client]() {
            std::cout << "EchoUInt32 connect" << std::endl;
            generic_record_impl request;
            request.add_uint4(32);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 2}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_uint4()) { std::cout << "EchoInt32 received: " << *result << std::endl; }
            }
        });
        register_task([client]() {
            std::cout << "EchoUInt64 connect" << std::endl;
            generic_record_impl request;
            request.add_uint8(64);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 3}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_uint8()) {
                    std::cout << "EchoUInt64 received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "EchoSInt32 connect" << std::endl;
            generic_record_impl request;
            request.add_int4(32);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 4}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_int4()) { std::cout << "EchoSInt32 received: " << *result << std::endl; }
            }
        });
        register_task([client]() {
            std::cout << "EchoSInt64 connect" << std::endl;
            generic_record_impl request;
            request.add_int8(64);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 5}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_int8()) { std::cout << "EchoSInt64 received: " << *result << std::endl; }
            }
        });
        register_task([client]() {
            std::cout << "EchoFloat connect" << std::endl;
            generic_record_impl request;
            request.add_float(3.14f);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 6}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_float()) { std::cout << "EchoFloat received: " << *result << std::endl; }
            }
        });
        register_task([client]() {
            std::cout << "EchoDouble connect" << std::endl;
            generic_record_impl request;
            request.add_double(3.14);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 7}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_double()) {
                    std::cout << "EchoDouble received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "EchoString connect" << std::endl;
            generic_record_impl request;
            request.add_string("Hello, world!");

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 8}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_string()) {
                    std::cout << "EchoString received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "EchoBytes connect" << std::endl;
            generic_record_impl request;
            request.add_string("Hello, world!");

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 9}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_string()) {
                    std::cout << "EchoBytes received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "BoolRequest connect" << std::endl;
            generic_record_impl request;
            request.add_bool(true);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 10}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_bool()) { std::cout << "EchoBool received: " << *result << std::endl; }
            }
        });
        register_task([client]() {
            std::cout << "Fixed32Request connect" << std::endl;
            generic_record_impl request;
            request.add_uint4(32);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 11}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_uint4()) {
                    std::cout << "Fixed32Request received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "Fixed64Request connect" << std::endl;
            generic_record_impl request;
            request.add_uint8(64);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 12}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_uint8()) {
                    std::cout << "Fixed64Request received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "SFixed32Request connect" << std::endl;
            generic_record_impl request;
            request.add_int4(32);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 13}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_int4()) {
                    std::cout << "SFixed32Request received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "SFixed64Request connect" << std::endl;
            generic_record_impl request;
            request.add_int8(64);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 14}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_int8()) {
                    std::cout << "SFixed64Request received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "ConcatInt32String connect" << std::endl;
            generic_record_impl request;
            request.add_int4(2);
            request.add_string("three");
            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 15}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_string()) {
                    std::cout << "ConcatInt32Stringg received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "ConcatStringInt32 connect" << std::endl;
            generic_record_impl request;
            request.add_string("one");
            request.add_int4(2);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 16}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_string()) {
                    std::cout << "ConcatStringInt32 received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "SumInt32Int64 connect" << std::endl;
            generic_record_impl request;
            request.add_int4(1);
            request.add_int8(2);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 17}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_int8()) {
                    std::cout << "SumInt32Int64 received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "MultiplyFloatDouble connect" << std::endl;
            generic_record_impl request;
            request.add_float(1.0f);
            request.add_double(2.0);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 18}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_double()) {
                    std::cout << "MultiplyFloatDouble received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "CombineStringBytes connect" << std::endl;
            generic_record_impl request;
            request.add_string("one");
            request.add_string("two");

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 19}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_string()) {
                    std::cout << "CombineStringBytes received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "FormatBoolInt32String connect" << std::endl;
            generic_record_impl request;
            request.add_bool(true);
            request.add_int4(42);
            request.add_string("Hello");

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 20}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_string()) {
                    std::cout << "FormatBoolInt32String received: " << *result << std::endl;
                }
            }
        });
        register_task([client]() {
            std::cout << "UseAllTypes connect" << std::endl;
            generic_record_impl request;
            request.add_int4(42);
            request.add_int8(64);
            request.add_uint4(32);
            request.add_uint8(64);
            request.add_int4(32);
            request.add_int8(64);
            request.add_uint4(32);
            request.add_uint8(64);
            request.add_int4(32);
            request.add_int8(64);
            request.add_float(3.14f);
            request.add_double(3.14);
            request.add_string("Hello, world!");
            request.add_string("Hello, world!");
            request.add_bool(true);

            generic_record_impl response;
            grpc::ClientContext context;

            client->call(context, {0, 21}, request, response);

            auto err = response.error();
            if(err) {
                print_error(*err);
            } else if(auto cursor = response.cursor()) {
                if(auto result = cursor->fetch_string()) {
                    std::cout << "UseAllTypes received: " << *result << std::endl;
                }
            }
        });
    }
}
