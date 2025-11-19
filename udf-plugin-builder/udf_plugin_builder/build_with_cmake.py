#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
from pathlib import Path
import sys


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
        "--grpc-endpoint", default="localhost:50051", help="gRPC server endpoint"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Path to write the generated ini file.",
    )

    return parser.parse_args(args)


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
    build_dir_full = build_dir.resolve()
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
        f"-DNAME={name}",
        f"-DBUILD_DIR={build_dir}",
        f"-DGRPC_ENDPOINT={args.grpc_endpoint}",
    ]
    print(f"[CMD] {' '.join(cmake_cmd)}")
    subprocess.check_call(cmake_cmd)

    build_cmd = ["cmake", "--build", str(build_dir_full), "--", "-j"]
    print(f"[INFO] Building: {' '.join(build_cmd)}")
    subprocess.check_call(build_cmd)

    lib_name = f"lib{name}.so"
    ini_name = f"lib{name}.ini"

    shutil.copy(build_dir_full / lib_name, out_dir / lib_name)
    shutil.copy(build_dir_full / ini_name, out_dir / ini_name)

    shutil.rmtree(build_dir)

    print(f"[INFO] Finished. Files created in {out_dir}: {lib_name}, {ini_name}")


def main():
    run(sys.argv[1:])


if __name__ == "__main__":
    main()
