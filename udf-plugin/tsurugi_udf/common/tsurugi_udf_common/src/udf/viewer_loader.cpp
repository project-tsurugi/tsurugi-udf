#include "viewer_loader.h"

#include <dlfcn.h>
#include <filesystem>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "enum_types.h"
#include "error_info.h"

namespace fs = std::filesystem;

namespace plugin::udf {

namespace {

using create_api_func = plugin_api* (*) ();

}  // namespace

viewer_loader::~viewer_loader() { unload_all(); }

std::vector<load_result> viewer_loader::load(std::string_view so_path) {
    std::vector<load_result> results{};

    fs::path path(so_path);

    if(! fs::exists(path)) {
        results.emplace_back(load_status::path_not_found, std::string(so_path), "Shared library not found");
        return results;
    }

    if(! fs::is_regular_file(path)) {
        results.emplace_back(load_status::path_not_found, std::string(so_path), "Path is not a regular file");
        return results;
    }

    if(! path.has_extension() || path.extension() != ".so") {
        results.emplace_back(load_status::no_ini_and_so_files, std::string(so_path), "File is not a .so library");
        return results;
    }

    dlerror();
    void* handle = dlopen(path.c_str(), RTLD_LAZY | RTLD_LOCAL);
    const char* err = dlerror();

    if(handle == nullptr || err != nullptr) {
        results.emplace_back(load_status::dlopen_failed, path.string(), err != nullptr ? err : "dlopen failed");
        return results;
    }

    auto result = create_view_api_from_handle(handle, path.string());
    if(result.status() != load_status::ok) { dlclose(handle); }

    results.push_back(std::move(result));
    return results;
}

load_result viewer_loader::create_view_api_from_handle(void* handle, std::string const& full_path) {
    if(handle == nullptr) {
        return {
            load_status::dlopen_failed,
            full_path,
            "Invalid handle (nullptr)",
        };
    }

    dlerror();
    void* sym = dlsym(handle, "create_plugin_api");
    const char* err = dlerror();

    if(sym == nullptr || err != nullptr) {
        return {
            load_status::api_symbol_missing,
            full_path,
            "Symbol 'create_plugin_api' not found",
        };
    }

    auto* api_func = reinterpret_cast<create_api_func>(sym);  // NOLINT(cppcoreguidelines-pro-type-reinterpret-cast)

    std::unique_ptr<plugin_api> api(api_func());
    if(! api) {
        return {
            load_status::api_init_failed,
            full_path,
            "Failed to initialize plugin API",
        };
    }

    plugins_.emplace_back(api.release());
    handles_.push_back(handle_entry{
        .handle_ = handle,
        .path_ = full_path,
    });

    return {
        load_status::ok,
        full_path,
        "Loaded successfully",
    };
}

std::vector<std::shared_ptr<plugin_api>> const& viewer_loader::plugins() const noexcept { return plugins_; }

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
