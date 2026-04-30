#include "generic_client_context.h"

#include <chrono>
#include <iostream>

namespace plugin::udf {

grpc::ClientContext& generic_client_context::grpc_context() noexcept { return grpc_context_; }

grpc::ClientContext const& generic_client_context::grpc_context() const noexcept { return grpc_context_; }

std::optional<std::chrono::milliseconds> generic_client_context::timeout() const noexcept { return timeout_; }

void generic_client_context::timeout(std::optional<std::chrono::milliseconds> value) noexcept {
    timeout_ = value;
    apply_timeout();
}

bool generic_client_context::is_debug_enabled() const noexcept { return debug_enabled_; }

void generic_client_context::debug_enabled(bool value) noexcept { debug_enabled_ = value; }

void generic_client_context::log_debug(std::string_view message) const {
    if(! debug_enabled_) { return; }
    std::cerr << "[udf] " << message << '\n';
}

void generic_client_context::apply_timeout() noexcept {
    if(! timeout_) { return; }
    grpc_context_.set_deadline(std::chrono::system_clock::now() + *timeout_);
}

}  // namespace plugin::udf
