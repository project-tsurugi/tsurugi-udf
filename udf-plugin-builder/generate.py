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
import subprocess
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
    RecordDescriptor,
    FunctionDescriptor,
    ServiceDescriptor,
    PackageDescriptor,
)


def fetch_add_name(type_kind: str) -> str:
    mapping = {
        "FLOAT8": "double",
        "FLOAT4": "float",
        "INT8": "int8",
        "UINT8": "uint8",
        "INT4": "int4",
        "FIXED8": "int8",
        "FIXED4": "int4",
        "BOOL": "bool",
        "STRING": "string",
        "BYTES": "string",
        "ENUM": "string",
        "GROUP": "/* no fetch, GROUP type */",
        "MESSAGE": "/* no fetch, MESSAGE type */",
        "UINT4": "uint4",
        "SINT4": "int4",
        "SINT8": "int8",
        "SFIXED8": "int8",
        "SFIXED4": "int4",
    }
    return mapping.get(type_kind, "/* no fetch, unknown type */")


def parse_package_descriptor(
    desc_set: descriptor_pb2.FileDescriptorSet,
) -> List[PackageDescriptor]:
    packages = []
    service_counter = 0
    function_counter = 0

    message_type_map = {}
    for file_proto in desc_set.file:
        pkg = file_proto.package
        for msg in file_proto.message_type:
            fqname = f".{pkg}.{msg.name}" if pkg else f".{msg.name}"
            message_type_map[fqname] = msg

    # @see https://github.com/protocolbuffers/protobuf/blob/main/src/google/protobuf/descriptor.proto#L243
    def field_type_to_kind(field):
        type_map = {
            1: "FLOAT8",
            2: "FLOAT4",
            3: "INT8",
            4: "UINT8",
            5: "INT4",
            6: "FIXED8",
            7: "FIXED4",
            8: "BOOL",
            9: "STRING",
            10: "GROUP",
            11: "MESSAGE",
            12: "BYTES",
            13: "UINT4",
            14: "ENUM",
            15: "SFIXED4",
            16: "SFIXED8",
            17: "SINT4",
            18: "SINT8",
        }
        return type_map.get(field.type, f"TYPE_{field.type}")

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
        columns = []
        for idx, field in enumerate(descriptor.field):
            kind = field_type_to_kind(field)
            nested = None
            if kind == "MESSAGE":
                nested_type_name = field.type_name
                nested = resolve_record_type(nested_type_name)
            columns.append(
                ColumnDescriptor(
                    index=idx,
                    column_name=field.name,
                    type_kind=kind,
                    nested_record=nested,
                )
            )
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
        "--proto_path",
        nargs="+",
        default=["proto"],
        help="Directory(ies) containing .proto files (default: proto)",
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


def generate_file() -> str:
    args = parse_args()

    out_dir = args.out
    descriptor_path = args.descriptor_set_out or f"{out_dir}/descriptor.pb"

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    import shutil

    grpc_plugin = shutil.which("grpc_cpp_plugin")
    if not grpc_plugin:
        print("Error: grpc_cpp_plugin not found in PATH")
        sys.exit(1)

    proto_files = [Path(p) for p in args.proto_file]
    for p in proto_files:
        if not p.exists():
            print(f"Error: proto file not found: {p}")
            sys.exit(1)
    proto_files_str = [str(p) for p in proto_files]

    proto_path_flags = [f"-I{p}" for p in args.proto_path]

    cmd = [
        "protoc",
        *proto_path_flags,
        f"--cpp_out={out_dir}",
        f"--grpc_out={out_dir}",
        f"--plugin=protoc-gen-grpc={grpc_plugin}",
        f"--descriptor_set_out={descriptor_path}",
        "--include_imports",
        *proto_files_str,
    ]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"[OK] Generated C++ and gRPC files in: {out_dir}")
    return descriptor_path


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
    descriptor_path = generate_file()
    desc_set = load_descriptor(descriptor_path)
    packages = parse_package_descriptor(desc_set)
    dump_packages_json(packages, "out/service_descriptors.json")
    out_dir = "out"
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
