/*
 * Copyright 2018-2026 Project Tsurugi.
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

#include <memory>
#include <string>
#include <string_view>
#include <vector>

#include "plugin_api.h"

namespace plugin::udf {

class viewer_loader {
public:

    viewer_loader() = default;
    ~viewer_loader();

    viewer_loader(viewer_loader const&) = delete;
    viewer_loader& operator=(viewer_loader const&) = delete;
    viewer_loader(viewer_loader&&) = delete;
    viewer_loader& operator=(viewer_loader&&) = delete;

    [[nodiscard]] bool load(std::string_view so_path);

    [[nodiscard]] std::vector<std::shared_ptr<plugin_api>> const& plugins() const noexcept;
    [[nodiscard]] std::string_view last_error_message() const noexcept;

    void unload_all() noexcept;

private:

    [[nodiscard]] bool create_view_api_from_handle(void* handle, std::string const& full_path);

    void set_error(std::string message) noexcept;

    struct handle_entry {
        void* handle_{nullptr};
        std::string path_{};
    };

    std::vector<handle_entry> handles_{};
    std::vector<std::shared_ptr<plugin_api>> plugins_{};
    std::string last_error_message_{};
};

}  // namespace plugin::udf