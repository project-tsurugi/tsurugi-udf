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
#include "generic_record.h"
#include <optional>
#include <variant>
#include <vector>

namespace plugin::udf {

using value_type = std::optional<std::variant<bool, std::int32_t, std::int64_t, std::uint32_t,
    std::uint64_t, std::string, double, float>>;

class generic_record_impl : public generic_record {
  public:
    void reset() override;
    void add_bool(bool value) override;
    void add_bool_null() override;
    void add_int4(std::int32_t value) override;
    void add_int4_null() override;
    void add_int8(std::int64_t value) override;
    void add_int8_null() override;
    void add_uint4(std::uint32_t value) override;
    void add_uint4_null() override;
    void add_uint8(std::uint64_t value) override;
    void add_uint8_null() override;
    void add_float(float value) override;
    void add_float_null() override;
    void add_double(double value) override;
    void add_double_null() override;
    void add_string(std::string value) override;
    void add_string_null() override;
    std::unique_ptr<generic_record_cursor> cursor() const override;

  private:
    std::vector<value_type> values_;
};

class generic_record_cursor_impl : public generic_record_cursor {
  public:
    explicit generic_record_cursor_impl(const std::vector<value_type>& values);
    std::optional<bool> fetch_bool() override;
    std::optional<std::int32_t> fetch_int4() override;
    std::optional<std::int64_t> fetch_int8() override;
    std::optional<std::uint32_t> fetch_uint4() override;
    std::optional<std::uint64_t> fetch_uint8() override;
    std::optional<float> fetch_float() override;
    std::optional<double> fetch_double() override;
    std::optional<std::string> fetch_string() override;
    bool has_next() override;

  private:
    const std::vector<value_type>& values_;
    std::size_t index_ = 0;
};

} // namespace plugin::udf
