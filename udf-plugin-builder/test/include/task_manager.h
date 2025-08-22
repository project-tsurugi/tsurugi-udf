#pragma once
#include <functional>
#include <vector>

class TaskManager {
public:
    void register_task(std::function<void()> fn);
    void run_tasks() const;
private:
    std::vector<std::function<void()>> tasks;
};
