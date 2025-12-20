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
#include <iostream>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

#include "udf_loader.h"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;
using namespace plugin::udf;
using namespace pybind11::literals;

std::string type_kind_to_string(plugin::udf::type_kind kind) {
    switch(kind) {
        case plugin::udf::type_kind::float8: return "float8";
        case plugin::udf::type_kind::float4: return "float4";
        case plugin::udf::type_kind::int8: return "int8";
        case plugin::udf::type_kind::uint8: return "uint8";
        case plugin::udf::type_kind::int4: return "int4";
        case plugin::udf::type_kind::fixed8: return "fixed8";
        case plugin::udf::type_kind::fixed4: return "fixed4";
        case plugin::udf::type_kind::boolean: return "boolean";
        case plugin::udf::type_kind::string: return "string";
        case plugin::udf::type_kind::group: return "group";
        case plugin::udf::type_kind::message: return "message";
        case plugin::udf::type_kind::bytes: return "bytes";
        case plugin::udf::type_kind::uint4: return "uint4";
        case plugin::udf::type_kind::grpc_enum: return "grpc_enum";
        case plugin::udf::type_kind::sint4: return "sint4";
        case plugin::udf::type_kind::sint8: return "sint8";
        case plugin::udf::type_kind::sfixed8: return "sfixed8";
        case plugin::udf::type_kind::sfixed4: return "sfixed4";
        default: return "UNKNOWN";
    }
}
std::string function_kind_to_string(plugin::udf::function_kind kind) {
    switch(kind) {
        case plugin::udf::function_kind::unary: return "unary";
        case plugin::udf::function_kind::client_streaming: return "client_streaming";
        case plugin::udf::function_kind::server_streaming: return "server_streaming";
        case plugin::udf::function_kind::bidirectional_streaming: return "bidirectional_streaming";
        default: return "unknown_function_kind";
    }
}
py::dict record_to_dict(const record_descriptor& record);

py::dict column_to_dict(const column_descriptor* col) {
    py::dict d;
    d["index"] = col->index();
    d["column_name"] = std::string(col->column_name());
    d["type_kind"] = type_kind_to_string(col->type_kind());

    // oneof_index
    if(col->has_oneof()) {
        d["oneof_index"] = py::cast(col->oneof_index().value());
    } else {
        d["oneof_index"] = py::none();
    }

    // oneof_name
    if(col->has_oneof()) {
        d["oneof_name"] = py::cast(std::string(col->oneof_name().value()));
    } else {
        d["oneof_name"] = py::none();
    }

    if(auto nested = col->nested()) {
        d["nested_record"] = record_to_dict(*nested);
    } else {
        d["nested_record"] = py::none();
    }

    return d;
}

py::dict record_to_dict(const record_descriptor& record) {
    py::list cols;
    for(auto* col: record.columns()) { cols.append(column_to_dict(col)); }
    return py::dict("record_name"_a = std::string(record.record_name()), "columns"_a = cols);
}

py::dict function_to_dict(const function_descriptor* fn) {
    return py::dict(
        "function_index"_a = fn->function_index(),
        "function_name"_a = std::string(fn->function_name()),
        "function_kind"_a = function_kind_to_string(fn->function_kind()),
        "input_record"_a = record_to_dict(fn->input_record()),
        "output_record"_a = record_to_dict(fn->output_record())
    );
}

py::list functions_to_list(const std::vector<function_descriptor*>& fns) {
    py::list result;
    for(auto* fn: fns) { result.append(function_to_dict(fn)); }
    return result;
}

py::dict service_to_dict(const service_descriptor* svc) {
    return py::dict(
        "service_index"_a = svc->service_index(),
        "service_name"_a = std::string(svc->service_name()),
        "functions"_a = functions_to_list(svc->functions())
    );
}

py::list services_to_list(const std::vector<service_descriptor*>& svcs) {
    py::list result;
    for(auto* svc: svcs) {
        if(! svc) {
            std::cerr << "Warning: null service_descriptor pointer encountered" << std::endl;
            continue;
        }
        result.append(service_to_dict(svc));
    }
    return result;
}

py::dict package_to_dict(const package_descriptor* pkg) {
    py::dict version_dict;
    version_dict["major"] = pkg->version().major();
    version_dict["minor"] = pkg->version().minor();
    version_dict["patch"] = pkg->version().patch();

    return py::dict(
        "package_name"_a = std::string(pkg->package_name()),
        "services"_a = services_to_list(pkg->services()),
        "file_name"_a = std::string(pkg->file_name()),
        "version"_a = version_dict
    );
}

py::list package_to_list(const std::vector<plugin_api*>& apis) {
    py::list result;
    for(const auto* api: apis) {
        for(const auto* pkg: api->packages()) { result.append(package_to_dict(pkg)); }
    }
    return result;
}

PYBIND11_MODULE(udf_plugin, m) {
    m.doc() = "UDF Plugin Loader (with nested record support)";
    m.def("load_plugin", [](const std::string& path) {
        udf_loader loader;

        auto results = loader.view_load(path);
        for(const auto& result: results) {
            std::cerr << "[gRPC] " << result.status()
                      << " file: " << result.file()
                      << " detail: " << result.detail()
                      << std::endl;
        }

        auto plugins = loader.get_plugins();
        std::vector<plugin_api*> apis;
        apis.reserve(plugins.size());
        for(const auto& plugin: plugins) {
            apis.push_back(std::get<0>(plugin).get());
        }

        return package_to_list(apis);
    });
}
