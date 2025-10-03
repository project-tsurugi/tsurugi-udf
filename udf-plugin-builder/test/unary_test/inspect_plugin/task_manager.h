#pragma once
#include <functional>
#include <memory>
#include <vector>

#include "generic_client.h"
#include "plugin_api.h"
#include "plugin_loader.h"

using namespace plugin::udf;
class TaskManager {
public:

    void register_task(std::function<void()> fn);
    void run_tasks() const;
    void set_loader(std::unique_ptr<plugin_loader> l);
    plugin_loader* get_loader() const;
    void set_functions();
    void register_rpc_tasks();
    void shutdown();

private:

    std::vector<std::function<void()>> tasks_;
    std::unique_ptr<plugin_loader> loader_;
    std::vector<std::tuple<std::shared_ptr<plugin_api>, std::shared_ptr<generic_client>>> plugins_;
};
