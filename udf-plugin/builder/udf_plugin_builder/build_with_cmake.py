#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List
from jinja2 import Environment, FileSystemLoader
from dataclasses import asdict
import tsurugi_udf_common
from tsurugi_udf_common import descriptors
from .ini_writer import generate_ini_file
from .utils import (
    log_always,
    log_info,
    log_ok,
    log_error,
    fetch_add_name,
    check_forbidden_function_names,
    find_grpc_cpp_plugin,
    load_descriptor,
    parse_package_descriptor,
    dump_packages_json,
)

tsurugi_udf_common_dir = os.path.dirname(tsurugi_udf_common.__file__)

PackageDescriptor = descriptors.PackageDescriptor
from udf_plugin_builder.tsurugi_keywords import (
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

    log_info("[CMD]", " ".join(protoc_cmd))
    try:
        subprocess.check_call(protoc_cmd)
    except subprocess.CalledProcessError as e:
        log_error(f"protoc failed with return code {e.returncode}")
        log_error(f"Command: {' '.join(protoc_cmd)}")
        sys.exit(1)

    after = {p.resolve() for p in build_dir.rglob("*") if p.is_file()}

    generated_files = sorted(after - before)

    return {
        "descriptor": descriptor_out.resolve(),
        "generated_files": generated_files,
    }


def write_sources_cmake(created_files, build_dir):
    srcs = []
    hdrs = []
    include_dirs = set()

    build_dir = Path(build_dir).resolve()

    for f in created_files:
        f = Path(f).resolve()

        if f.suffix in (".cc", ".cpp", ".cxx"):
            srcs.append(f)
        elif f.suffix in (".h", ".hpp"):
            hdrs.append(f)

        try:
            rel = f.relative_to(build_dir)
        except ValueError:
            include_dirs.add(str(f.parent))
            continue

        if len(rel.parts) > 1:
            include_dirs.add(str(build_dir / rel.parts[0]))
        else:
            include_dirs.add(str(build_dir))

    include_dirs.add(str(build_dir))

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
        fp.write(")\n\n")

        fp.write("set(GENERATED_INCLUDE_DIRS\n")
        for d in sorted(include_dirs):
            fp.write(f'  "{d}"\n')
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
    out_dir_resolved = out_dir.resolve() if args.output_dir else None

    counter = 0
    while True:
        if counter == 0:
            build_dir_full = build_dir_base
        else:
            build_dir_full = build_dir_base.parent / f"{build_dir_base.name}_{counter}"

        if out_dir_resolved and build_dir_full == out_dir_resolved:
            counter += 1
            continue
        if build_dir_full.exists():
            counter += 1
            continue

        break
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
    log_always(f"[INFO] Building in {build_dir_full}")
    log_always(f"[INFO] Output directory: {out_dir}")
    log_always(f"[INFO] Plugin name: {name}")
    log_always(f"[INFO] gRPC endpoint: {args.grpc_endpoint}")
    log_always(f"[INFO] Proto path: {proto_paths}")
    log_always(f"[INFO] Using proto files: {args.proto_file}")

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
    log_info("[FILE]", result["descriptor"])
    for f in result["generated_files"]:
        log_info("[FILE]", f)
        created_files.append(f)
    desc_set = load_descriptor(result["descriptor"])
    packages = parse_package_descriptor(desc_set)
    check_forbidden_function_names(packages)
    dump_packages_json(packages, f"{build_dir_full}/service_descriptors.json")
    proto_base_name = Path(args.proto_file[0]).stem
    log_info(f"[INFO] Generating C++ files from templates...", "")
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
        log_info("[FILE]", generated_path)

    descriptor_impl_cpp = os.path.join(
        tsurugi_udf_common_dir, "src", "udf", "descriptor_impl.cpp"
    )
    created_files.append(descriptor_impl_cpp)

    sources_cmake = write_sources_cmake(created_files, build_dir_full)
    log_info("[INFO] Wrote", sources_cmake)

    cmake_cmd = [
        "cmake",
        "-S",
        str(CMAKE_DIR),
        "-B",
        str(build_dir_full),
        f"-DBUILD_DIR={build_dir_full}",
        f"-DNAME={name}",
        f"-DOUTPUT_DIR={out_dir}",
        f"-DTSURUGI_UDF_COMMON_DIR={tsurugi_udf_common_dir}",
        f"-DCMAKE_BUILD_TYPE={BUILD_TYPE}",
    ]

    if not DEBUG:
        cmake_cmd.append("--log-level=WARNING")

    subprocess.check_call(cmake_cmd)

    build_cmd = ["cmake", "--build", str(build_dir_full), "--", "-j"]

    if not DEBUG:
        build_cmd.append("-s")

    subprocess.check_call(build_cmd)

    so_file = out_dir / f"lib{name}.so"
    if not so_file.exists():
        raise FileNotFoundError(f"{so_file} not found!")
    log_ok(f"Generated so file: {so_file}")
    log_info(f"[INFO] Generating ini file...")
    generate_ini_file(name, args.grpc_endpoint, out_dir)
    if build_dir_full.exists():
        try:
            shutil.rmtree(build_dir_full)
            log_info(f"[INFO] Deleted build directory: {build_dir_full}")
        except Exception as e:
            log_always(f"[WARN] Failed to delete build directory {build_dir_full}: {e}")


def main():
    run(sys.argv[1:])


if __name__ == "__main__":
    main()
