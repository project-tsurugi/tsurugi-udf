#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build UDF plugin with CMake (control proto files from Python)"
    )

    parser.add_argument(
        "--proto-file",
        nargs="+",
        default=[
            "proto/sample.proto",
            "proto/complex_types.proto",
            "proto/primitive_types.proto",
        ],
        help="Path(s) to main .proto file(s)",
    )
    parser.add_argument(
        "--proto-path",
        default=None,
        help="Directory containing .proto files (default: automatically inferred from the first .proto file).",
    )
    parser.add_argument(
        "--build-dir", default="tmp", help="Temporary directory for generated files"
    )
    parser.add_argument(
        "--name",
        default="plugin_api",
        help="Base name used for the generated plugin library (.so) and configuration file (.ini). (default: plugin_api)",
    )
    parser.add_argument(
        "--grpc-endpoint", default="localhost:50051", help="gRPC server endpoint"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Path to write the generated ini file.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    build_dir = Path.cwd() / args.build_dir
    out_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    if args.output_dir:
        if not out_dir.exists():
            raise FileNotFoundError(f"--output-dir '{out_dir}' does not exist.")
        if not out_dir.is_dir():
            raise NotADirectoryError(f"--output-dir '{out_dir}' is not a directory.")
    build_dir_full = build_dir

    if build_dir_full.exists():
        shutil.rmtree(build_dir_full)
    build_dir_full.mkdir(parents=True)

    proto_files = [str(Path(p).resolve()) for p in args.proto_file]
    proto_files_str = ";".join(proto_files)
    if args.proto_path:
        proto_path = os.path.abspath(args.proto_path)
    else:
        proto_path = str(Path(proto_files[0]).parent.resolve())

    print(f"[INFO] Building with CMake in {build_dir_full}")
    print(f"[INFO] Using proto files: {args.proto_file}")
    print(f"[INFO] Proto path: {proto_path}")
    print(f"[INFO] gRPC endpoint: {args.grpc_endpoint}")
    # CMake configure
    cmake_cmd = [
        "cmake",
        "-B",
        str(build_dir_full),
        "-S",
        str(script_dir / "cmake"),
        f"-DPROTO_PATH={proto_path}",
        f"-DPROTO_FILES={proto_files_str}",
        f"-DNAME={args.name}",
        f"-DBUILD_DIR={build_dir}",
        f"-DGRPC_ENDPOINT={args.grpc_endpoint}",
    ]
    print(f"[CMD] {' '.join(cmake_cmd)}")
    subprocess.check_call(cmake_cmd)

    build_cmd = ["cmake", "--build", str(build_dir_full), "--", "-j"]
    print(f"[INFO] Building: {' '.join(build_cmd)}")
    subprocess.check_call(build_cmd)

    lib_name = f"lib{args.name}.so"
    ini_name = f"lib{args.name}.ini"

    shutil.copy(build_dir_full / lib_name, out_dir / lib_name)
    shutil.copy(build_dir_full / ini_name, out_dir / ini_name)

    shutil.rmtree(build_dir)

    print(f"[INFO] Finished. Files created in {out_dir}: {lib_name}, {ini_name}")


if __name__ == "__main__":
    main()
