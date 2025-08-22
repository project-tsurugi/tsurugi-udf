#pragma once
#include "task_manager.h"
#include "udf/generic_client.h"
#include <grpcpp/grpcpp.h>
using namespace plugin::udf;
void register_rpc_tasks(TaskManager& manager, generic_client& client);
