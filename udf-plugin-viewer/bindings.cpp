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
#include "udf/udf_loader.h"
#include <iostream>
#include <memory>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <tuple>
#include <vector>

namespace py = pybind11;
using namespace plugin::udf;
using namespace pybind11::literals;

std::string type_kind_to_string(plugin::udf::type_kind_type kind) {
    switch (kind) {
        case plugin::udf::type_kind_type::FLOAT8: return "FLOAT8";
        case plugin::udf::type_kind_type::FLOAT4: return "FLOAT4";
        case plugin::udf::type_kind_type::INT8: return "INT8";
        case plugin::udf::type_kind_type::UINT8: return "UINT8";
        case plugin::udf::type_kind_type::INT4: return "INT4";
        case plugin::udf::type_kind_type::FIXED8: return "FIXED8";
        case plugin::udf::type_kind_type::FIXED4: return "FIXED4";
        case plugin::udf::type_kind_type::BOOL: return "BOOL";
        case plugin::udf::type_kind_type::STRING: return "STRING";
        case plugin::udf::type_kind_type::GROUP: return "GROUP";
        case plugin::udf::type_kind_type::MESSAGE: return "MESSAGE";
        case plugin::udf::type_kind_type::BYTES: return "BYTES";
        case plugin::udf::type_kind_type::UINT4: return "UINT4";
        case plugin::udf::type_kind_type::ENUM: return "ENUM";
        case plugin::udf::type_kind_type::SINT4: return "SINT4";
        case plugin::udf::type_kind_type::SINT8: return "SINT8";
        case plugin::udf::type_kind_type::SFIXED8: return "SFIXED8";
        case plugin::udf::type_kind_type::SFIXED4: return "SFIXED4";
        default: return "UNKNOWN";
    }
}
py::dict record_to_dict(const record_descriptor& record);

py::dict column_to_dict(const column_descriptor* col) {
    py::dict d("index"_a = col->index(), "column_name"_a = std::string(col->column_name()),
        "type_kind"_a = type_kind_to_string(col->type_kind()));

    if (auto nested = col->nested()) {
        d["nested_record"] = record_to_dict(*nested);
    } else {
        d["nested_record"] = py::none();
    }
    return d;
}

py::dict record_to_dict(const record_descriptor& record) {
    py::list cols;
    for (auto* col : record.columns()) {
        cols.append(column_to_dict(col));
    }
    return py::dict("record_name"_a = std::string(record.record_name()), "columns"_a = cols);
}

py::dict function_to_dict(const function_descriptor* fn) {
    return py::dict("function_index"_a = fn->function_index(),
        "function_name"_a              = std::string(fn->function_name()),
        "function_kind"_a              = static_cast<int>(fn->function_kind()),
        "input_record"_a               = record_to_dict(fn->input_record()),
        "output_record"_a              = record_to_dict(fn->output_record()));
}

py::list functions_to_list(const std::vector<function_descriptor*>& fns) {
    py::list result;
    for (auto* fn : fns) {
        result.append(function_to_dict(fn));
    }
    return result;
}

py::dict service_to_dict(const service_descriptor* svc) {
    return py::dict("service_index"_a = svc->service_index(),
        "service_name"_a              = std::string(svc->service_name()),
        "functions"_a                 = functions_to_list(svc->functions()));
}

py::list services_to_list(const std::vector<service_descriptor*>& svcs) {
    py::list result;
    for (auto* svc : svcs) {
        if (!svc) {
            std::cerr << "Warning: null service_descriptor pointer encountered" << std::endl;
            continue;
        }
        result.append(service_to_dict(svc));
    }
    return result;
}

py::dict package_to_dict(const package_descriptor* pkg) {
    return py::dict("package_name"_a = std::string(pkg->package_name()),
        "services"_a                 = services_to_list(pkg->services()));
}

py::list package_to_list(const std::vector<plugin_api*>& apis) {
    py::list result;
    for (const auto* api : apis) {
        for (const auto* pkg : api->packages()) {
            result.append(package_to_dict(pkg));
        }
    }
    return result;
}

PYBIND11_MODULE(udf_plugin, m) {
    m.doc() = "UDF Plugin Loader (with nested record support)";
    m.def("load_plugin", [](const std::string& path) {
        static std::unique_ptr<udf_loader> loader = std::make_unique<udf_loader>();
        loader->load(path);
        auto plugins = loader->get_plugins();
        std::vector<plugin_api*> apis;
        for (const auto& plugin : plugins) {
            apis.push_back(std::get<0>(plugin));
        }
        return package_to_list(apis);
    });
}