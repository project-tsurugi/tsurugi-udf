#pragma once

#include <chrono>
#include <optional>
#include <string_view>

#include <grpcpp/client_context.h>

namespace plugin::udf {

class generic_client_context {
public:

    generic_client_context() = default;
    ~generic_client_context() = default;

    generic_client_context(generic_client_context const&) = delete;
    generic_client_context& operator=(generic_client_context const&) = delete;
    generic_client_context(generic_client_context&&) = delete;
    generic_client_context& operator=(generic_client_context&&) = delete;

    [[nodiscard]] grpc::ClientContext& grpc_context() noexcept;
    [[nodiscard]] grpc::ClientContext const& grpc_context() const noexcept;

    [[nodiscard]] std::optional<std::chrono::milliseconds> timeout() const noexcept;
    void timeout(std::optional<std::chrono::milliseconds> value) noexcept;

    [[nodiscard]] bool is_debug_enabled() const noexcept;
    void debug_enabled(bool value) noexcept;

    void log_debug(std::string_view message) const;

private:

    void apply_timeout() noexcept;

    grpc::ClientContext grpc_context_{};
    std::optional<std::chrono::milliseconds> timeout_{};
    bool debug_enabled_{false};
};

}  // namespace plugin::udf
