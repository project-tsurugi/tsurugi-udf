#!/usr/bin/env python3
import os
import sys
import shutil
import json
from typing import List
from dataclasses import asdict
from tsurugi_udf_common import descriptors
from google.protobuf import descriptor_pb2

ColumnDescriptor = descriptors.ColumnDescriptor
RecordDescriptor = descriptors.RecordDescriptor
FunctionDescriptor = descriptors.FunctionDescriptor
ServiceDescriptor = descriptors.ServiceDescriptor
PackageDescriptor = descriptors.PackageDescriptor
DEBUG = os.environ.get("BUILD_TYPE", "").strip().lower() == "debug"
TYPE_KIND_MAP = descriptors.TYPE_KIND_MAP
FIELD_TYPE_MAP = descriptors.FIELD_TYPE_MAP
Version = descriptors.Version

from udf_plugin_builder.tsurugi_keywords import (
    TSURUGI_RESERVED_KEYWORDS,
    TSURUGI_TYPES_KEYWORDS,
)


def set_debug(value: bool):
    global DEBUG
    DEBUG = value


def log_always(*args, **kwargs):
    print(*args, **kwargs)


def log_info(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def log_error(*args, **kwargs):
    print("\033[91m[ERROR]\033[0m", *args, file=sys.stderr, **kwargs)


def log_ok(*args, **kwargs):
    print("\033[32m[OK]\033[0m", *args, **kwargs)


def handle_value_error(e: ValueError):
    if DEBUG:
        raise e
    else:
        print(f"\033[91m[ERROR]\033[0m {e}", file=sys.stderr)
        sys.exit(1)


def check_no_oneof(record: RecordDescriptor, fn_name: str):
    for col in record.columns:
        if col.oneof_index is not None or col.oneof_name is not None:
            e = ValueError(
                f"oneof is not allowed in output record.\n"
                f"  Function: {fn_name}\n"
                f"  Column: index={col.index}, name='{col.column_name}', "
                f"oneof_index={col.oneof_index}, oneof_name={col.oneof_name}"
            )
            handle_value_error(e)


def validate_tsurugi_type(
    file_name: str,
    service_name: str,
    function_name: str,
    record_name: str,
    position: str,
):
    if record_name in TSURUGI_TYPES_KEYWORDS:
        e = ValueError(
            f"RPC function failed.\n"
            f"Error occurred in {file_name}, service {service_name}, function {function_name}.\n"
            f"Unwrapped Tsurugi types ({record_name}) are not allowed for {position}.\n"
            f"Tsurugi types must be specified by wrapping them in a message type."
        )
        handle_value_error(e)


def fetch_add_name(type_kind: str) -> str:
    return TYPE_KIND_MAP.get(type_kind, "/* no fetch, unknown type */")


def validate_non_empty_record_recursive(
    file_name: str,
    service_name: str,
    function_name: str,
    record: RecordDescriptor,
    position: str,
):
    if len(record.columns) == 0:
        e = ValueError(
            f"RPC function failed.\n"
            f"Error occurred in {file_name}, service {service_name}, function {function_name}.\n"
            f"{position.capitalize()} record '{record.record_name}' must contain at least one column.\n"
            f"Empty message types are not allowed for {position}."
        )
        handle_value_error(e)

    for col in record.columns:
        if col.nested_record is not None:
            validate_non_empty_record_recursive(
                file_name,
                service_name,
                function_name,
                col.nested_record,
                position,
            )


def check_forbidden_function_names(packages):
    forbidden = TSURUGI_RESERVED_KEYWORDS
    for pkg in packages:
        for svc in pkg.services:
            for fn in svc.functions:
                check_no_oneof(fn.output_record, fn.function_name)
                validate_tsurugi_type(
                    pkg.file_name,
                    svc.service_name,
                    fn.function_name,
                    fn.output_record.record_name,
                    "returns",
                )
                validate_tsurugi_type(
                    pkg.file_name,
                    svc.service_name,
                    fn.function_name,
                    fn.input_record.record_name,
                    "argument",
                )
                if fn.function_name.lower() in forbidden:
                    e = ValueError(
                        f"Function name '{fn.function_name}' is forbidden because it is a reserved keyword in Tsurugi.\n"
                        f"  Service: {svc.service_name}\n"
                        f"  Package: {pkg.package_name}"
                    )
                    handle_value_error(e)
                validate_non_empty_record_recursive(
                    pkg.file_name,
                    svc.service_name,
                    fn.function_name,
                    fn.output_record,
                    "returns",
                )


def find_grpc_cpp_plugin():
    plugin = shutil.which("grpc_cpp_plugin")
    if not plugin:
        raise RuntimeError("grpc_cpp_plugin not found in PATH")
    return plugin


def load_descriptor(path: str) -> descriptor_pb2.FileDescriptorSet:
    with open(path, "rb") as f:
        data = f.read()
    desc_set = descriptor_pb2.FileDescriptorSet()
    desc_set.ParseFromString(data)
    return desc_set


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


def field_type_to_kind(field) -> str:
    """Protobuf field type番号 -> internal type名"""
    return FIELD_TYPE_MAP.get(field.type, f"TYPE_{field.type}")


def dump_packages_json(packages: List[PackageDescriptor], build_path: str):
    with open(build_path, "w") as f:
        json.dump([asdict(pkg) for pkg in packages], f, indent=2)
