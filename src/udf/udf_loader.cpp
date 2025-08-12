/*
 * Copyright 2018-2025 Project Tsurugi.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include "udf/udf_loader.h"
#include "udf/generic_client_factory.h"

#include "udf/generic_record_impl.h"
#include <dlfcn.h>
#include <filesystem>
#include <grpcpp/grpcpp.h>
#include <iostream>
namespace fs = std::filesystem;
using namespace plugin::udf;
void udf_loader::load(std::string_view plugin_path) {
    fs::path path(plugin_path);
    if (fs::is_regular_file(path)) {
        if (path.extension() == ".so") {
            std::string full_path = path.string();
            void* handle          = dlopen(full_path.c_str(), RTLD_NOW | RTLD_GLOBAL);
            if (!handle) {
                std::cerr << "Failed to load " << full_path << ": " << dlerror() << std::endl;
            } else {
                handles_.emplace_back(handle);
                create_api_from_handle(handle);
            }
        } else {
            std::cerr << "Specified file is not a .so plugin: " << path << std::endl;
        }
    } else if (fs::is_directory(path)) {
        for (const auto& entry : fs::directory_iterator(path)) {
            if (!entry.is_regular_file()) continue;
            if (entry.path().extension() != ".so") continue;

            std::string full_path = entry.path().string();
            void* handle          = dlopen(full_path.c_str(), RTLD_LAZY);
            if (!handle) {
                std::cerr << "Failed to load " << full_path << ": " << dlerror() << std::endl;
            } else {
                std::cout << "Loaded plugin: " << full_path << std::endl;
                handles_.emplace_back(handle);
                create_api_from_handle(handle);
            }
        }
    } else {
        std::cerr << "Plugin path is not valid: " << path << std::endl;
    }
}

void udf_loader::unload_all() {
    for (void* handle : handles_) {
        if (handle) dlclose(handle);
    }
    handles_.clear();
}
void udf_loader::create_api_from_handle(void* handle) {
    if (!handle) return;

    using create_func_type = plugin_api* (*)();
    auto* create_func      = reinterpret_cast<create_func_type>(dlsym(handle, "create_plugin_api"));

    if (!create_func) {
        std::cerr << "  Failed to find symbol create_plugin_api\n";
        return;
    }

    plugin_api* api = create_func();
    if (!api) {
        std::cerr << "  create_plugin_api returned nullptr\n";
        return;
    }
    apis_.emplace_back(api);
    std::cerr << "  create_func2\n";
    auto* create_func2 = reinterpret_cast<generic_client_factory* (*)(const char*)>(
        dlsym(handle, "tsurugi_create_generic_client_factory"));
    if (!create_func2) {
        std::cerr << "  Failed to find symbol tsurugi_create_generic_client_factory\n";
        return;
    }
    std::cerr << "  create_func2 found\n";
    factory_ = create_func2("Greeter");
}
const std::vector<plugin_api*>& udf_loader::apis() const noexcept { return apis_; }
generic_client_factory* udf_loader::get_factory() const noexcept { return factory_; }
udf_loader::~udf_loader() { unload_all(); }
