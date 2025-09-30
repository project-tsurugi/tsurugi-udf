#!/usr/bin/env python3
# Copyright 2018-2025 Project Tsurugi.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
from jinja2 import Environment, FileSystemLoader
from google.protobuf import descriptor_pb2


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "py")))

from dataclasses import asdict
from common.descriptors import (
    ColumnDescriptor,
    ScalarDescriptor,
    NestedDescriptor,
    OneofDescriptor,
    RecordDescriptor,
    FunctionDescriptor,
    ServiceDescriptor,
    PackageDescriptor,
    TYPE_KIND_MAP,
    FIELD_TYPE_MAP,
)


def fetch_add_name(type_kind: str) -> str:
    return TYPE_KIND_MAP.get(type_kind, "/* no fetch, unknown type */")


def field_type_to_kind(field) -> str:
    """Protobuf field type番号 -> internal type名"""
    return FIELD_TYPE_MAP.get(field.type, f"TYPE_{field.type}")


def parse_package_descriptor(
    desc_set: descriptor_pb2.FileDescriptorSet,
) -> List[PackageDescriptor]:
    packages = []
    service_counter = 0
    function_counter = 0

    message_type_map = {}

    def register_message(pkg: str, msg, parent_prefix: str = ""):
        if parent_prefix:
            fqname = f"{parent_prefix}.{msg.name}"
        else:
            fqname = f".{pkg}.{msg.name}" if pkg else f".{msg.name}"
        message_type_map[fqname] = msg
        for nested in msg.nested_type:
            register_message(pkg, nested, fqname)

    for file_proto in desc_set.file:
        pkg = file_proto.package
        for msg in file_proto.message_type:
            register_message(pkg, msg)

    def resolve_record_type(type_name):
        descriptor = message_type_map.get(type_name)
        if not descriptor:
            return RecordDescriptor(
                columns=[
                    ColumnDescriptor(
                        index=0, column_name="unknown", type_kind="UNKNOWN"
                    )
                ],
                record_name=type_name.lstrip("."),
            )
        columns: list[ColumnDescriptor] = []
        for idx, field in enumerate(descriptor.field):
            kind = field_type_to_kind(field)
            nested = None
            # 11: MESSAGE
            if kind == FIELD_TYPE_MAP[11]:
                nested_type_name = field.type_name
                nested = resolve_record_type(nested_type_name)
                field_desc = NestedDescriptor(
                    index=idx,
                    column_name=field.name,
                    type_kind=kind,
                    nested_record=nested,
                )
            else:
                field_desc = ScalarDescriptor(
                    index=idx,
                    column_name=field.name,
                    type_kind=kind,
                    nested_record=None,
                )
            columns.append(field_desc)
        return RecordDescriptor(columns=columns, record_name=type_name.lstrip("."))

    for file_proto in desc_set.file:
        pkg = file_proto.package
        services = []
        for service_proto in file_proto.service:
            functions = []
            for idx, method in enumerate(service_proto.method):
                kind = "Unary"
                if method.client_streaming and method.server_streaming:
                    kind = "BidirectionalStreaming"
                elif method.client_streaming:
                    kind = "ClientStreaming"
                elif method.server_streaming:
                    kind = "ServerStreaming"
                func = FunctionDescriptor(
                    function_index=function_counter,
                    function_name=method.name,
                    function_kind=kind,
                    input_record=resolve_record_type(method.input_type),
                    output_record=resolve_record_type(method.output_type),
                )
                functions.append(func)
                function_counter += 1

            service = ServiceDescriptor(
                service_index=service_counter,
                service_name=service_proto.name,
                functions=functions,
            )
            services.append(service)
            service_counter += 1
        if services:
            package = PackageDescriptor(
                package_name=pkg,
                services=services,
            )
            packages.append(package)
    return packages


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate C++ and gRPC code from .proto file"
    )

    parser.add_argument(
        "--proto_file",
        nargs="+",
        default=[
            "proto/sample.proto",
            "proto/complex_types.proto",
            "proto/primitive_types.proto",
        ],
        help="Path(s) to main .proto file(s) (default: sample + complex_types + primitive_types)",
    )
    parser.add_argument(
        "--out",
        default="out",
        help="Output directory for generated files (default: out)",
    )
    parser.add_argument(
        "--descriptor_set_out",
        default=None,
        help="Path to write descriptor.pb (default: <out>/descriptor.pb)",
    )

    return parser.parse_args()


def dump_packages_json(packages: List[PackageDescriptor], output_path: str):
    with open(output_path, "w") as f:
        json.dump([asdict(pkg) for pkg in packages], f, indent=2)


def load_descriptor(path: str) -> descriptor_pb2.FileDescriptorSet:
    with open(path, "rb") as f:
        data = f.read()
    desc_set = descriptor_pb2.FileDescriptorSet()
    desc_set.ParseFromString(data)
    return desc_set


def generate_cpp_from_template(
    packages: List[PackageDescriptor],
    template_dir: str,
    template_file: str,
    output_cpp_path: str,
    proto_base_name: str,
):
    env = Environment(
        loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True
    )
    env.globals["fetch_add_name"] = fetch_add_name
    template = env.get_template(template_file)
    rendered = template.render(
        packages=[asdict(pkg) for pkg in packages], proto_base_name=proto_base_name
    )

    with open(output_cpp_path, "w") as f:
        f.write(rendered)

    print(f"[OK] Generated C++ file from template: {output_cpp_path}")


if __name__ == "__main__":
    args = parse_args()
    out_dir = args.out
    descriptor_path = args.descriptor_set_out or f"{out_dir}/descriptor.pb"
    desc_set = load_descriptor(descriptor_path)
    packages = parse_package_descriptor(desc_set)
    dump_packages_json(packages, f"{out_dir}/service_descriptors.json")
    proto_base_name = Path(parse_args().proto_file[0]).stem
    templates = {
        "plugin_api_impl.cpp.j2": "plugin_api_impl.cpp",
        "rpc_client.cpp.j2": "rpc_client.cpp",
        "rpc_client.h.j2": "rpc_client.h",
        "rpc_client_factory.cpp.j2": "rpc_client_factory.cpp",
    }
    template_dir = "templates"
    for template_file, output_file in templates.items():
        output_path = f"{out_dir}/{output_file}"
        generate_cpp_from_template(
            packages, template_dir, template_file, output_path, proto_base_name
        )
