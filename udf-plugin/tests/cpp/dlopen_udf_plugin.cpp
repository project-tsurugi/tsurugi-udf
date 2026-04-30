#include <dlfcn.h>
#include <iostream>

int main(int argc, char** argv) {
    if(argc < 2) {
        std::cerr << "usage: dlopen_udf_plugin <so...>\n";
        return 1;
    }

    int result = 0;

    for(int i = 1; i < argc; ++i) {
        char const* path = argv[i];

        std::cerr << "checking dlopen: " << path << "\n";

        dlerror();
        void* handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
        if(handle == nullptr) {
            char const* error = dlerror();
            std::cerr << "dlopen failed: " << (error != nullptr ? error : "(unknown)") << "\n";
            result = 1;
            continue;
        }

        std::cerr << "dlopen succeeded: " << path << "\n";
        dlclose(handle);
    }

    return result;
}
