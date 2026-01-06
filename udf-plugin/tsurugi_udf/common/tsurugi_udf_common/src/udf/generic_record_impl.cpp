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

#include "generic_record_impl.h"

#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <variant>
#include <vector>
#include <chrono>
#include <queue>


#include "error_info.h"
namespace plugin::udf {
std::optional<error_info>& generic_record_impl::error() noexcept { return err_; }
std::optional<error_info> const& generic_record_impl::error() const noexcept { return err_; }
void generic_record_impl::reset() {
    values_.clear();
    err_ = std::nullopt;
}
void generic_record_impl::set_error(error_info const& status) {
    err_ = error_info(status.code(), std::string(status.message()));
}

void generic_record_impl::add_bool(bool v) { values_.emplace_back(v); }
void generic_record_impl::add_bool_null() { values_.emplace_back(std::monostate{}); }

void generic_record_impl::add_int4(std::int32_t v) { values_.emplace_back(v); }
void generic_record_impl::add_int4_null() { values_.emplace_back(std::monostate{}); }

void generic_record_impl::add_int8(std::int64_t v) { values_.emplace_back(v); }
void generic_record_impl::add_int8_null() { values_.emplace_back(std::monostate{}); }

void generic_record_impl::add_uint4(std::uint32_t v) { values_.emplace_back(v); }
void generic_record_impl::add_uint4_null() { values_.emplace_back(std::monostate{}); }

void generic_record_impl::add_uint8(std::uint64_t v) { values_.emplace_back(v); }
void generic_record_impl::add_uint8_null() { values_.emplace_back(std::monostate{}); }

void generic_record_impl::add_float(float v) { values_.emplace_back(v); }
void generic_record_impl::add_float_null() { values_.emplace_back(std::monostate{}); }

void generic_record_impl::add_double(double v) { values_.emplace_back(v); }
void generic_record_impl::add_double_null() { values_.emplace_back(std::monostate{}); }

void generic_record_impl::add_string(std::string v) { values_.emplace_back(std::move(v)); }
void generic_record_impl::add_string_null() { values_.emplace_back(std::monostate{}); }

std::unique_ptr<generic_record_cursor> generic_record_impl::cursor() const {
    return std::make_unique<generic_record_cursor_impl>(values_);
}

generic_record_cursor_impl::generic_record_cursor_impl(std::vector<value_type> const& values) : values_(values) {}

bool generic_record_cursor_impl::has_next() { return index_ < values_.size(); }

namespace {
template<typename T>
std::optional<T> fetch_value_as(value_type const& v) {
    if(std::holds_alternative<std::monostate>(v)) { return std::nullopt; }
    if(auto p = std::get_if<T>(&v)) { return *p; }
    return std::nullopt;
}
}  // anonymous namespace
std::optional<bool> generic_record_cursor_impl::fetch_bool() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<bool>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

std::optional<std::int32_t> generic_record_cursor_impl::fetch_int4() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<std::int32_t>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

std::optional<std::int64_t> generic_record_cursor_impl::fetch_int8() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<std::int64_t>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

std::optional<std::uint32_t> generic_record_cursor_impl::fetch_uint4() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<std::uint32_t>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

std::optional<std::uint64_t> generic_record_cursor_impl::fetch_uint8() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<std::uint64_t>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

std::optional<float> generic_record_cursor_impl::fetch_float() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<float>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

std::optional<double> generic_record_cursor_impl::fetch_double() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<double>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

std::optional<std::string> generic_record_cursor_impl::fetch_string() {
    if(! has_next()) { return std::nullopt; }
    auto value = fetch_value_as<std::string>(values_[index_]);
    if(value) { ++index_; }
    return value;
}

generic_record_stream_impl::generic_record_stream_impl() = default;
generic_record_stream_impl::~generic_record_stream_impl() { close(); }

generic_record_stream_impl::generic_record_stream_impl(generic_record_stream_impl&& other) noexcept {
    {
        std::lock_guard lk(other.mutex_);
        queue_ = std::move(other.queue_);
        closed_ = other.closed_;
        eos_ = other.eos_;
        
        // Leave moved-from object in a well-defined closed state
        other.closed_ = true;
        other.eos_ = true;
    }
    // Notify any threads waiting on the moved-from object
    other.cv_.notify_all();
}

generic_record_stream_impl& generic_record_stream_impl::operator=(generic_record_stream_impl&& other) noexcept {
    if(this == &other) return *this;
    {
        std::scoped_lock lk(mutex_, other.mutex_);
        queue_ = std::move(other.queue_);
        closed_ = other.closed_;
        eos_ = other.eos_;
        
        // Leave moved-from object in a well-defined closed state
        other.closed_ = true;
        other.eos_ = true;
    }
    // Notify any threads waiting on the moved-from object
    other.cv_.notify_all();
    
    return *this;
}

generic_record_stream::status_type generic_record_stream_impl::try_next(generic_record& record) {
    std::lock_guard lk(mutex_);

    if(! queue_.empty()) {
        auto rec = std::move(queue_.front());
        queue_.pop();

        auto& impl = static_cast<generic_record_impl&>(record);
        impl = std::move(rec);

        return impl.error() ? status_type::error : status_type::ok;
    }

    if(eos_) { return status_type::end_of_stream; }

    return status_type::not_ready;
}

generic_record_stream::status_type
generic_record_stream_impl::next(generic_record& record, std::optional<std::chrono::milliseconds> timeout) {

    std::unique_lock lk(mutex_);

    auto pred = [&] { return ! queue_.empty() || eos_ || closed_; };

    if(timeout) {
        if(! cv_.wait_for(lk, *timeout, pred)) { return status_type::not_ready; }
    } else {
        cv_.wait(lk, pred);
    }

    if(! queue_.empty()) {
        auto rec = std::move(queue_.front());
        queue_.pop();

        auto& impl = static_cast<generic_record_impl&>(record);
        impl = std::move(rec);

        return impl.error() ? status_type::error : status_type::ok;
    }

    return status_type::end_of_stream;
}

void generic_record_stream_impl::push(generic_record_impl record) {
    {
        std::lock_guard lk(mutex_);
        if(closed_ || eos_) return;
        queue_.push(std::move(record));
    }
    cv_.notify_one();
}

void generic_record_stream_impl::end_of_stream() {
    {
        std::lock_guard lk(mutex_);
        eos_ = true;
    }
    cv_.notify_all();
}

void generic_record_stream_impl::close() {
    {
        std::lock_guard lk(mutex_);
        closed_ = true;
        eos_ = true;
        std::queue<generic_record_impl> empty;
        queue_.swap(empty);
    }
    cv_.notify_all();
}

}  // namespace plugin::udf
