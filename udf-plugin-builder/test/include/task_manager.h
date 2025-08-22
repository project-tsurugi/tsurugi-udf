#pragma once
#include "udf/plugin_loader.h"
#include <functional>
#include <memory>
#include <vector>
class TaskManager {
  public:
    void register_task(std::function<void()> fn);
    void run_tasks() const;
    void set_loader(std::unique_ptr<plugin::udf::plugin_loader> l);
    plugin::udf::plugin_loader* get_loader() const;
    void set_functions();

  private:
    std::vector<std::function<void()>> tasks_;
    std::unique_ptr<plugin::udf::plugin_loader> loader_;
};
