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
#include <string>
#include <string_view>
#include <vector>
namespace plugin::udf {
enum class function_kind_type {
    Unary,
    ClientStreaming,
    ServerStreaming,
    BidirectionalStreaming,
};

enum class type_kind_type {
    FLOAT8,
    FLOAT4,
    INT8,
    UINT8,
    INT4,
    FIXED8,
    FIXED4,
    BOOL,
    STRING,
    GROUP,
    MESSAGE,
    BYTES,
    UINT4,
    ENUM,
    SINT4,
    SINT8,
    SFIXED8,
    SFIXED4,
};

std::string to_string(function_kind_type kind);
std::string to_string(type_kind_type kind);

class column_descriptor {
  public:
    using index_type             = std::size_t;
    virtual ~column_descriptor() = default;

    virtual index_type index() const noexcept             = 0;
    virtual std::string_view column_name() const noexcept = 0;
    virtual type_kind_type type_kind() const noexcept     = 0;
};

class record_descriptor {
  public:
    virtual ~record_descriptor()                                            = default;
    virtual std::string_view record_name() const noexcept                   = 0;
    virtual const std::vector<column_descriptor*>& columns() const noexcept = 0;
};

class function_descriptor {
  public:
    using index_type               = std::size_t;
    virtual ~function_descriptor() = default;

    virtual index_type function_index() const noexcept              = 0;
    virtual std::string_view function_name() const noexcept         = 0;
    virtual function_kind_type function_kind() const noexcept       = 0;
    virtual const record_descriptor& input_record() const noexcept  = 0;
    virtual const record_descriptor& output_record() const noexcept = 0;
};

class service_descriptor {
  public:
    using index_type                                                            = std::size_t;
    virtual ~service_descriptor()                                               = default;
    virtual index_type service_index() const noexcept                           = 0;
    virtual std::string_view service_name() const noexcept                      = 0;
    virtual const std::vector<function_descriptor*>& functions() const noexcept = 0;
};

class package_descriptor {
  public:
    virtual ~package_descriptor()                                             = default;
    virtual std::string_view package_name() const noexcept                    = 0;
    virtual const std::vector<service_descriptor*>& services() const noexcept = 0;
};

class plugin_api {
  public:
    virtual ~plugin_api()                                                     = default;
    virtual const std::vector<package_descriptor*>& packages() const noexcept = 0;
};

extern "C" plugin_api* create_plugin_api();
} // namespace plugin::udf
