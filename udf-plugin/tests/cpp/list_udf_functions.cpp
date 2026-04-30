#include <dlfcn.h>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

#include "plugin_api.h"

namespace {

struct loaded_plugin {
    std::string path;
    void* handle{};
};

}  // namespace

int main(int argc, char** argv) {
    if(argc < 2) {
        std::cerr << "usage: list_udf_functions <so...>\n";
        return 1;
    }

    std::vector<loaded_plugin> loaded;
    loaded.reserve(static_cast<std::size_t>(argc - 1));

    for(int i = 1; i < argc; ++i) {
        char const* path = argv[i];

        std::cerr << "loading: " << path << "\n";

        dlerror();
        void* handle = dlopen(path, RTLD_NOW | RTLD_GLOBAL);
        if(handle == nullptr) {
            char const* error = dlerror();
            std::cerr << "dlopen failed: " << (error != nullptr ? error : "(unknown)") << "\n";
            return 1;
        }

        loaded.push_back({path, handle});
    }

    using create_api_func = plugin::udf::plugin_api* (*) ();

    int result = 0;

    for(auto const& plugin: loaded) {
        dlerror();
        auto* symbol = dlsym(plugin.handle, "create_plugin_api");
        if(symbol == nullptr) {
            char const* error = dlerror();
            std::cerr << "dlsym failed: " << plugin.path << ": " << (error != nullptr ? error : "(unknown)") << "\n";
            result = 1;
            continue;
        }

        auto* create_api = reinterpret_cast<create_api_func>(symbol);
        std::unique_ptr<plugin::udf::plugin_api> api(create_api());
        if(! api) {
            std::cerr << "create_plugin_api returned nullptr: " << plugin.path << "\n";
            result = 1;
            continue;
        }

        for(auto const* pkg: api->packages()) {
            if(pkg == nullptr) { continue; }
            for(auto const* svc: pkg->services()) {
                if(svc == nullptr) { continue; }
                for(auto const* fn: svc->functions()) {
                    if(fn == nullptr) { continue; }
                    std::cout << plugin.path << '\t' << pkg->package_name() << '\t' << svc->service_name() << '\t'
                              << fn->function_name() << '\n';
                }
            }
        }
    }

    for(auto it = loaded.rbegin(); it != loaded.rend(); ++it) {
        if(it->handle != nullptr) { dlclose(it->handle); }
    }

    return result;
}
