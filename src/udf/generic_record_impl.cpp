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

#include "udf/generic_record_impl.h"
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <variant>
#include <vector>
namespace plugin::udf {

void generic_record_impl::reset() { values_.clear(); }

void generic_record_impl::add_bool(bool v) { values_.emplace_back(v); }

void generic_record_impl::add_bool_null() { values_.emplace_back(std::nullopt); }

void generic_record_impl::add_int4(std::int32_t v) { values_.emplace_back(v); }

void generic_record_impl::add_int4_null() { values_.emplace_back(std::nullopt); }

void generic_record_impl::add_int8(std::int64_t v) { values_.emplace_back(v); }

void generic_record_impl::add_int8_null() { values_.emplace_back(std::nullopt); }

void generic_record_impl::add_uint4(std::uint32_t v) { values_.emplace_back(v); }

void generic_record_impl::add_uint4_null() { values_.emplace_back(std::nullopt); }

void generic_record_impl::add_uint8(std::uint64_t v) { values_.emplace_back(v); }

void generic_record_impl::add_uint8_null() { values_.emplace_back(std::nullopt); }

void generic_record_impl::add_float(float v) { values_.emplace_back(v); }

void generic_record_impl::add_float_null() { values_.emplace_back(std::nullopt); }

void generic_record_impl::add_double(double v) { values_.emplace_back(v); }

void generic_record_impl::add_double_null() { values_.emplace_back(std::nullopt); }

void generic_record_impl::add_string(std::string value) { values_.emplace_back(std::move(value)); }

void generic_record_impl::add_string_null() { values_.emplace_back(std::nullopt); }

std::unique_ptr<generic_record_cursor> generic_record_impl::cursor() const {
    return std::make_unique<generic_record_cursor_impl>(values_);
}

generic_record_cursor_impl::generic_record_cursor_impl(const std::vector<value_type>& values)
    : values_(values) {}

bool generic_record_cursor_impl::has_next() { return index_ < values_.size(); }

std::optional<bool> generic_record_cursor_impl::fetch_bool() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<bool>(&*opt)) return *p;
    return std::nullopt;
}

std::optional<std::int32_t> generic_record_cursor_impl::fetch_int4() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<std::int32_t>(&*opt)) return *p;
    return std::nullopt;
}

std::optional<std::int64_t> generic_record_cursor_impl::fetch_int8() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<std::int64_t>(&*opt)) return *p;
    return std::nullopt;
}

std::optional<std::uint32_t> generic_record_cursor_impl::fetch_uint4() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<std::uint32_t>(&*opt)) return *p;
    return std::nullopt;
}

std::optional<std::uint64_t> generic_record_cursor_impl::fetch_uint8() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<std::uint64_t>(&*opt)) return *p;
    return std::nullopt;
}

std::optional<std::string> generic_record_cursor_impl::fetch_string() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<std::string>(&*opt)) return *p;
    return std::nullopt;
}

std::optional<float> generic_record_cursor_impl::fetch_float() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<float>(&*opt)) return *p;
    return std::nullopt;
}

std::optional<double> generic_record_cursor_impl::fetch_double() {
    if (!has_next()) return std::nullopt;
    const auto& opt = values_[index_++];
    if (!opt) return std::nullopt;
    if (auto p = std::get_if<double>(&*opt)) return *p;
    return std::nullopt;
}

} // namespace plugin::udf
