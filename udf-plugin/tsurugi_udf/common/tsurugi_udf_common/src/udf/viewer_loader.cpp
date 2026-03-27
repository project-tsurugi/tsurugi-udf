/*
 * Copyright 2018-2026 Project Tsurugi.
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
#include "viewer_loader.h"

#include <dlfcn.h>
#include <filesystem>
#include <memory>
#include <string>
#include <utility>

namespace fs = std::filesystem;

namespace plugin::udf {

namespace {

using create_api_func = plugin_api* (*) ();

}  // namespace

viewer_loader::~viewer_loader() { unload_all(); }

bool viewer_loader::load(std::string_view so_path) {
    last_error_message_.clear();

    fs::path path(so_path);

    if(! fs::exists(path)) {
        set_error("Shared library not found: " + std::string(so_path));
        return false;
    }

    if(! fs::is_regular_file(path)) {
        set_error("Path is not a regular file: " + std::string(so_path));
        return false;
    }

    if(! path.has_extension() || path.extension() != ".so") {
        set_error("File is not a .so library: " + std::string(so_path));
        return false;
    }

    dlerror();
    void* handle = dlopen(path.c_str(), RTLD_LAZY | RTLD_LOCAL);
    const char* err = dlerror();

    if(handle == nullptr || err != nullptr) {
        set_error(err != nullptr ? err : "dlopen failed");
        return false;
    }

    if(! create_view_api_from_handle(handle, path.string())) {
        dlclose(handle);
        return false;
    }

    return true;
}

bool viewer_loader::create_view_api_from_handle(void* handle, std::string const& full_path) {
    if(handle == nullptr) {
        set_error("Invalid handle (nullptr): " + full_path);
        return false;
    }

    dlerror();
    void* sym = dlsym(handle, "create_plugin_api");
    const char* err = dlerror();

    if(sym == nullptr || err != nullptr) {
        set_error("Symbol 'create_plugin_api' not found: " + full_path);
        return false;
    }

    auto* api_func = reinterpret_cast<create_api_func>(sym);  // NOLINT(cppcoreguidelines-pro-type-reinterpret-cast)

    std::unique_ptr<plugin_api> api(api_func());
    if(! api) {
        set_error("Failed to initialize plugin API: " + full_path);
        return false;
    }

    plugins_.emplace_back(api.release());
    handles_.push_back(handle_entry{handle, full_path});
    return true;
}

std::vector<std::shared_ptr<plugin_api>> const& viewer_loader::plugins() const noexcept { return plugins_; }

std::string_view viewer_loader::last_error_message() const noexcept { return last_error_message_; }

void viewer_loader::set_error(std::string message) noexcept { last_error_message_ = std::move(message); }

void viewer_loader::unload_all() noexcept {
    plugins_.clear();

    for(auto& entry: handles_) {
        if(entry.handle_ != nullptr) {
            dlclose(entry.handle_);
            entry.handle_ = nullptr;
        }
    }

    handles_.clear();
}

}  // namespace plugin::udf