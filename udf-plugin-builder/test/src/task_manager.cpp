#include <functional>
#include <vector>
#include <iostream>
#include <exception>
#include "task_manager.h"

void TaskManager::register_task(std::function<void()> fn) {
    tasks.push_back(std::move(fn));
}

void TaskManager::run_tasks() const {
    for (size_t i = 0; i < tasks.size(); ++i) {
        try {
            tasks[i]();
        } catch (const std::exception& ex) {
            std::cerr << "[TaskManager] Exception in task " << i
                      << ": " << ex.what() << std::endl;
        } catch (...) {
            std::cerr << "[TaskManager] Unknown exception in task " << i << std::endl;
        }
    }
}
