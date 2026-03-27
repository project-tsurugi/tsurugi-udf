#pragma once

#include <memory>
#include <string>
#include <string_view>
#include <vector>

#include "error_info.h"
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

    [[nodiscard]] std::vector<load_result> load(std::string_view so_path);

    [[nodiscard]] std::vector<std::shared_ptr<plugin_api>> const& plugins() const noexcept;

    void unload_all() noexcept;

private:
    [[nodiscard]] load_result create_view_api_from_handle(
        void* handle,
        std::string const& full_path
    );

    struct handle_entry {
        void* handle_{nullptr};
        std::string path_{};
    };

    std::vector<handle_entry> handles_{};
    std::vector<std::shared_ptr<plugin_api>> plugins_{};
};

} // namespace plugin::udf
