#include "task_manager.h"
#include <exception>
#include <functional>
#include <iostream>
#include <vector>

void TaskManager::register_task(std::function<void()> fn) { tasks_.push_back(std::move(fn)); }

void TaskManager::run_tasks() const {
    for (size_t i = 0; i < tasks_.size(); ++i) {
        try {
            tasks_[i]();
        } catch (const std::exception& ex) {
            std::cerr << "[TaskManager] Exception in task " << i << ": " << ex.what() << std::endl;
        } catch (...) { std::cerr << "[TaskManager] Unknown exception in task " << i << std::endl; }
    }
}
void TaskManager::set_loader(std::unique_ptr<plugin::udf::plugin_loader> l) {
    loader_ = std::move(l);
}
plugin::udf::plugin_loader* TaskManager::get_loader() const { return loader_.get(); }
