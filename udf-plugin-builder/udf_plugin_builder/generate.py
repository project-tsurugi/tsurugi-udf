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
import shutil
import sys
import subprocess
import os
import json
from tsurugi_udf_common import descriptors
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
from jinja2 import Environment, FileSystemLoader
from google.protobuf import descriptor_pb2


from dataclasses import asdict

ColumnDescriptor = descriptors.ColumnDescriptor
RecordDescriptor = descriptors.RecordDescriptor
FunctionDescriptor = descriptors.FunctionDescriptor
ServiceDescriptor = descriptors.ServiceDescriptor
PackageDescriptor = descriptors.PackageDescriptor
TYPE_KIND_MAP = descriptors.TYPE_KIND_MAP
FIELD_TYPE_MAP = descriptors.FIELD_TYPE_MAP
Version = descriptors.Version

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")


def fetch_add_name(type_kind: str) -> str:
    return TYPE_KIND_MAP.get(type_kind, "/* no fetch, unknown type */")


def field_type_to_kind(field) -> str:
    """Protobuf field type番号 -> internal type名"""
    return FIELD_TYPE_MAP.get(field.type, f"TYPE_{field.type}")


def find_grpc_cpp_plugin():
    plugin = shutil.which("grpc_cpp_plugin")
    if plugin is None:
        print("[ERROR] grpc_cpp_plugin not found in PATH.")
        sys.exit(1)
    return plugin


def run_protoc(proto_files, proto_path, tmp_dir, descriptor_set_out=None):
    plugin_path = find_grpc_cpp_plugin()
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    if descriptor_set_out is None:
        descriptor_set_out = tmp_dir / "descriptor.pb"

    protoc_cmd = [
        "protoc",
        f"-I{proto_path}",
        f"--cpp_out={tmp_dir}",
        f"--grpc_out={tmp_dir}",
        f"--plugin=protoc-gen-grpc={plugin_path}",
        f"--descriptor_set_out={descriptor_set_out}",
        "--include_imports",
    ]
    protoc_cmd.extend(proto_files)

    print("[INFO] Running protoc:", " ".join(str(x) for x in protoc_cmd))
    subprocess.check_call(protoc_cmd)
    return descriptor_set_out


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
            if field.HasField("oneof_index"):
                oneof_idx = field.oneof_index
                oneof_name = (
                    descriptor.oneof_decl[oneof_idx].name
                    if oneof_idx is not None
                    else None
                )
            else:
                oneof_idx = None
                oneof_name = None
            # 11: MESSAGE
            if kind == FIELD_TYPE_MAP[11]:  # MESSAGE
                nested_type_name = field.type_name
                nested = resolve_record_type(nested_type_name)
            field_desc = ColumnDescriptor(
                index=idx,
                column_name=field.name,
                type_kind=kind,
                nested_record=nested,
                oneof_index=oneof_idx,
                oneof_name=oneof_name,
            )
            columns.append(field_desc)
        return RecordDescriptor(columns=columns, record_name=type_name.lstrip("."))

    for file_proto in desc_set.file:
        pkg = file_proto.package
        services = []
        for service_proto in file_proto.service:
            functions = []
            for idx, method in enumerate(service_proto.method):
                kind = "unary"
                if method.client_streaming and method.server_streaming:
                    kind = "bidirectional_streaming"
                elif method.client_streaming:
                    kind = "client_streaming"
                elif method.server_streaming:
                    kind = "server_streaming"
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
                file_name=file_proto.name,
                version=Version(1, 0, 0),
            )
            packages.append(package)
    return packages


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate C++ and gRPC code from .proto file"
    )

    parser.add_argument(
        "--proto-file",
        nargs="+",
        default=[
            "proto/sample.proto",
            "proto/complex_types.proto",
            "proto/primitive_types.proto",
        ],
        help="Path(s) to main .proto file(s) (default: sample + complex_types + primitive_types)",
    )
    parser.add_argument(
        "--proto_path",
        default="proto",
        help="Directory containing .proto files (default: proto)",
    )
    parser.add_argument(
        "--tmp",
        default="tmp",
        help="Temporary directory for generated files (default: tmp)",
    )
    parser.add_argument(
        "--descriptor_set_out",
        default=None,
        help="Path to write descriptor.pb (default: <tmp>/descriptor.pb)",
    )
    parser.add_argument(
        "--plugin_api_name",
        default="plugin_api",
        help="Name of the generated plugin API library (used to name the ini: lib<name>.ini).",
    )
    parser.add_argument(
        "--grpc-endpoint",
        default="localhost:50051",
        help="gRPC server URL to write into the ini (default: localhost:50051).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Path to write the generated ini file.",
    )

    return parser.parse_args()


def dump_packages_json(packages: List[PackageDescriptor], tmp_path: str):
    with open(tmp_path, "w") as f:
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
    def camelcase(s: str) -> str:
        parts = s.split("_")
        return "".join(p.capitalize() for p in parts if p)

    env = Environment(
        loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True
    )
    env.globals["fetch_add_name"] = fetch_add_name
    env.filters["camelcase"] = camelcase
    template = env.get_template(template_file)
    rendered = template.render(
        packages=[asdict(pkg) for pkg in packages], proto_base_name=proto_base_name
    )

    with open(output_cpp_path, "w") as f:
        f.write(rendered)

    print(f"[OK] Generated C++ file from template: {output_cpp_path}")


def generate_ini_file(plugin_name: str, grpc_endpoint: str, out_dir: str):
    """Generate .ini file for plugin"""
    ini_path = Path(out_dir) / f"lib{plugin_name}.ini"
    ini_path.parent.mkdir(parents=True, exist_ok=True)

    with open(ini_path, "w") as f:
        f.write("[udf]\n")
        f.write(f"enabled=true\n")
        f.write(f"endpoint={grpc_endpoint}\n")
        f.write("secure=false\n")

    print(f"[OK] Generated ini file: {ini_path}")
    return ini_path


def main():
    args = parse_args()
    tmp_dir = args.tmp
    descriptor_path = run_protoc(args.proto_file, args.proto_path, tmp_dir)
    descriptor_path = args.descriptor_set_out or f"{tmp_dir}/descriptor.pb"
    desc_set = load_descriptor(descriptor_path)
    packages = parse_package_descriptor(desc_set)
    dump_packages_json(packages, f"{tmp_dir}/service_descriptors.json")
    proto_base_name = Path(parse_args().proto_file[0]).stem
    templates = {
        "plugin_api_impl.cpp.j2": "plugin_api_impl.cpp",
        "rpc_client.cpp.j2": "rpc_client.cpp",
        "rpc_client.h.j2": "rpc_client.h",
        "rpc_client_factory.cpp.j2": "rpc_client_factory.cpp",
    }
    for template_file, output_file in templates.items():
        output_path = f"{tmp_dir}/{output_file}"
        generate_cpp_from_template(
            packages, TEMPLATES_DIR, template_file, output_path, proto_base_name
        )
    generate_ini_file(args.plugin_api_name, args.grpc_endpoint, args.out or ".")


if __name__ == "__main__":
    main()
