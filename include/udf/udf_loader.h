/*
 * Copyright 2018-2025 Project Tsurugi.
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
#pragma once
#include "generic_client_factory.h"
#include "plugin_api.h"
#include "plugin_loader.h"
#include <string_view>
#include <vector>

namespace plugin::udf {
class udf_loader : public plugin_loader {
  public:
    void load(std::string_view dir_path) override;
    void unload_all() override;
    const std::vector<plugin_api*>& apis() const noexcept override;
    ~udf_loader() override;
    generic_client_factory* get_factory() const noexcept override;

  private:
    std::vector<void*> handles_;
    std::vector<plugin_api*> apis_;
    void create_api_from_handle(void* handle);
    generic_client_factory* factory_ = nullptr;
};
} // namespace plugin::udf
