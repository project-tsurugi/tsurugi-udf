#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import sys
from google.protobuf import descriptor_pb2
from typing import List
from jinja2 import Environment, FileSystemLoader
from dataclasses import asdict
from tsurugi_udf_common import descriptors
import tsurugi_udf_common

tsurugi_udf_common_dir = os.path.dirname(tsurugi_udf_common.__file__)

ColumnDescriptor = descriptors.ColumnDescriptor
RecordDescriptor = descriptors.RecordDescriptor
FunctionDescriptor = descriptors.FunctionDescriptor
ServiceDescriptor = descriptors.ServiceDescriptor
PackageDescriptor = descriptors.PackageDescriptor
TYPE_KIND_MAP = descriptors.TYPE_KIND_MAP
FIELD_TYPE_MAP = descriptors.FIELD_TYPE_MAP
Version = descriptors.Version
from udf_plugin_builder.tsurugi_keywords import (
    TSURUGI_RESERVED_KEYWORDS,
    TSURUGI_TYPES_KEYWORDS,
    TEMPLATE,
)


def get_build_type() -> str:
    """Return normalized build type: 'Debug' or 'Release'. Default is 'Release'."""
    val = os.environ.get("BUILD_TYPE", "").strip().lower()
    if val == "debug":
        return "Debug"
    else:
        # empty or anything else -> Release
        return "Release"


BUILD_TYPE = get_build_type()

DEBUG = BUILD_TYPE == "Debug"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CMAKE_DIR = Path(SCRIPT_DIR) / "cmake"
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")


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


def handle_value_error(e: ValueError):
    if DEBUG:
        raise e
    else:
        print(f"\033[91m[ERROR]\033[0m {e}", file=sys.stderr)
        os._exit(1)


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


def generate_cpp_from_template(
    packages: List[PackageDescriptor],
    template_dir: str,
    template_file: str,
    output_cpp_path: str,
    proto_base_name: str,
) -> str:
    def camelcase(s: str) -> str:
        parts = s.split("_")
        return "".join(p.capitalize() for p in parts if p)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["fetch_add_name"] = fetch_add_name
    env.filters["camelcase"] = camelcase

    template = env.get_template(template_file)
    rendered = template.render(
        packages=[asdict(pkg) for pkg in packages],
        proto_base_name=proto_base_name,
    )

    output_path = Path(output_cpp_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered)
    return str(output_path)


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


def field_type_to_kind(field) -> str:
    """Protobuf field type番号 -> internal type名"""
    return FIELD_TYPE_MAP.get(field.type, f"TYPE_{field.type}")


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Build UDF plugin with CMake (control proto files from Python)"
    )

    parser.add_argument(
        "--proto-file",
        nargs="+",
        required=True,
        help="Path(s) to main .proto file(s)",
    )
    parser.add_argument(
        "--proto-path",
        nargs="+",
        default=None,
        help="Directory containing .proto files (default: automatically inferred from the first .proto file).",
    )
    parser.add_argument(
        "--build-dir", default="tmp", help="Temporary directory for generated files"
    )
    parser.add_argument(
        "--name",
        required=False,
        help="Base name used for the generated plugin library (.so) and configuration file (.ini).",
    )
    parser.add_argument(
        "--grpc-endpoint", default="dns:///localhost:50051", help="gRPC server endpoint"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Path to write the generated ini file.",
    )

    return parser.parse_args(args)


def find_grpc_cpp_plugin():
    plugin = shutil.which("grpc_cpp_plugin")
    if not plugin:
        raise RuntimeError("grpc_cpp_plugin not found in PATH")
    return plugin


def run_protoc(proto_files, proto_paths, build_dir):
    plugin_path = find_grpc_cpp_plugin()
    build_dir.mkdir(parents=True, exist_ok=True)

    before = {p.resolve() for p in build_dir.rglob("*") if p.is_file()}

    descriptor_out = build_dir / "descriptor.pb"
    include_args = [f"-I{p}" for p in proto_paths]

    protoc_cmd = [
        "protoc",
        *include_args,
        f"--cpp_out={build_dir}",
        f"--grpc_out={build_dir}",
        f"--plugin=protoc-gen-grpc={plugin_path}",
        f"--descriptor_set_out={descriptor_out}",
        "--include_imports",
        *proto_files,
    ]

    print("[CMD]", " ".join(protoc_cmd))
    subprocess.check_call(protoc_cmd)

    after = {p.resolve() for p in build_dir.rglob("*") if p.is_file()}

    generated_files = sorted(after - before)

    return {
        "descriptor": descriptor_out.resolve(),
        "generated_files": generated_files,
    }


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


def dump_packages_json(packages: List[PackageDescriptor], build_path: str):
    with open(build_path, "w") as f:
        json.dump([asdict(pkg) for pkg in packages], f, indent=2)


def write_sources_cmake(created_files, build_dir):
    srcs = []
    hdrs = []

    for f in created_files:
        f = Path(f)
        if f.suffix in (".cc", ".cpp", ".cxx"):
            srcs.append(f)
        elif f.suffix in (".h", ".hpp"):
            hdrs.append(f)

    sources_cmake = build_dir / "generated_sources.cmake"
    with open(sources_cmake, "w") as fp:
        fp.write("# Auto-generated by udf-plugin-builder\n")
        fp.write("set(GENERATED_SRCS\n")
        for s in srcs:
            fp.write(f'  "{s}"\n')
        fp.write(")\n\n")

        fp.write("set(GENERATED_HDRS\n")
        for h in hdrs:
            fp.write(f'  "{h}"\n')
        fp.write(")\n")

    return sources_cmake


def run(args=None):
    args = parse_args(args)

    script_dir = Path(__file__).resolve().parent
    build_dir = Path.cwd() / args.build_dir
    out_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    if args.output_dir:
        if not out_dir.exists():
            raise FileNotFoundError(f"--output-dir '{out_dir}' does not exist.")
        if not out_dir.is_dir():
            raise NotADirectoryError(f"--output-dir '{out_dir}' is not a directory.")
    build_dir_base = build_dir.resolve()
    build_dir_full = build_dir_base
    counter = 1
    while build_dir_full.exists():
        build_dir_full = build_dir_base.parent / f"{build_dir_base.name}_{counter}"
        counter += 1
    build_dir_full.mkdir(parents=True)
    if build_dir_full == out_dir.resolve():
        raise RuntimeError(
            f"--build-dir '{build_dir_full}' must not be the same as --output-dir."
        )
    if hasattr(out_dir.resolve(), "is_relative_to"):
        # Python 3.9+
        if out_dir.resolve().is_relative_to(build_dir_full):
            raise RuntimeError(
                f"--output-dir '{out_dir.resolve()}' must not be inside --build-dir '{build_dir_full}'."
            )
    else:
        # Python 3.8 and below
        if build_dir_full in out_dir.resolve().parents:
            raise RuntimeError(
                f"--output-dir '{out_dir.resolve()}' must not be inside --build-dir '{build_dir_full}'."
            )
    name = ""
    if args.name:
        name = args.name
    else:
        first_proto = Path(args.proto_file[0])
        name = first_proto.stem
    if build_dir_full.exists():
        shutil.rmtree(build_dir_full)
    build_dir_full.mkdir(parents=True)

    proto_files = [str(Path(p).resolve()) for p in args.proto_file]
    proto_files_str = ";".join(proto_files)
    proto_paths = []

    if args.proto_path:
        if isinstance(args.proto_path, str):
            proto_paths = [
                os.path.abspath(p.strip()) for p in args.proto_path.split(",")
            ]
        else:
            proto_paths = [os.path.abspath(p) for p in args.proto_path]
    else:
        proto_paths = [str(Path(proto_files[0]).parent.resolve())]
    proto_paths_str = ";".join(proto_paths)
    print(f"[INFO] Building in {build_dir_full}")
    print(f"[INFO] Output directory: {out_dir}")
    print(f"[INFO] Plugin name: {name}")
    print(f"[INFO] gRPC endpoint: {args.grpc_endpoint}")
    print(f"[INFO] Proto path: {proto_paths}")
    print(f"[INFO] Using proto files: {args.proto_file}")

    build_type_env = os.environ.get("BUILD_TYPE", "").strip()
    if not build_type_env:
        build_type = "Release"
    else:
        build_type = build_type_env.capitalize()
    if build_type not in ("Debug", "Release"):
        raise RuntimeError(
            f"Invalid build type: {build_type}. Must be Debug or Release."
        )
    result = run_protoc(proto_files, proto_paths, build_dir_full)
    created_files = []
    print("[FILE]", result["descriptor"])
    for f in result["generated_files"]:
        print("[FILE]", f)
        created_files.append(f)
    desc_set = load_descriptor(result["descriptor"])
    packages = parse_package_descriptor(desc_set)
    check_forbidden_function_names(packages)
    dump_packages_json(packages, f"{build_dir_full}/service_descriptors.json")
    proto_base_name = Path(args.proto_file[0]).stem
    print(f"[INFO] Generating C++ files from templates...")
    for template_file, output_file in TEMPLATE.items():
        output_path = Path(build_dir_full) / output_file
        generated_path = generate_cpp_from_template(
            packages,
            TEMPLATES_DIR,
            template_file,
            str(output_path),
            proto_base_name,
        )
        created_files.append(generated_path)
        print("[FILE]", generated_path)

    print(f"[INFO] Generating ini file...")
    generate_ini_file(name, args.grpc_endpoint, out_dir)
    descriptor_impl_cpp = os.path.join(
        tsurugi_udf_common_dir, "src", "udf", "descriptor_impl.cpp"
    )
    created_files.append(descriptor_impl_cpp)
    sources_cmake = write_sources_cmake(created_files, build_dir_full)
    print("[INFO] Wrote", sources_cmake)

    subprocess.check_call(
        [
            "cmake",
            "-S",
            str(CMAKE_DIR),
            "-B",
            str(build_dir_full),
            f"-DBUILD_DIR={build_dir_full}",
            f"-DNAME={name}",
            f"-DOUTPUT_DIR={out_dir}",
            f"-DTSURUGI_UDF_COMMON_DIR={tsurugi_udf_common_dir}",
        ]
    )
    subprocess.check_call(["cmake", "--build", str(build_dir_full), "--", "-j"])
    so_file = out_dir / f"lib{name}.so"
    if not so_file.exists():
        raise FileNotFoundError(f"{so_file} not found!")
    print("[FILE]", so_file)
    if build_dir_full.exists():
        try:
            shutil.rmtree(build_dir_full)
            print(f"[INFO] Deleted build directory: {build_dir_full}")
        except Exception as e:
            print(f"[WARN] Failed to delete build directory {build_dir_full}: {e}")


def main():
    run(sys.argv[1:])


if __name__ == "__main__":
    main()
