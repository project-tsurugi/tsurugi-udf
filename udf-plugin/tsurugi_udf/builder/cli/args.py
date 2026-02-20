from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class CliArgs:
    proto_files: list[str]
    build_dir: str = "tmp"
    grpc_plugin: str | None = None
    include: list[str] = field(default_factory=list)
    grpc_endpoint: str = "dns:///localhost:50051"
    grpc_transport: str = "stream"
    output_dir: str | None = None
    debug: bool = False
    clean: bool = False
    secure: bool = False
    disable: bool = False

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(description="protoc wrapper")

        p.add_argument(
            "--proto",
            dest="proto_files",
            nargs="+",
            required=True,
            help=".proto files (space separated list)",
        )
        p.add_argument(
            "--build-dir",
            default="tmp",
            help="Temporary directory for generated files",
        )
        p.add_argument(
            "--grpc-plugin",
            default=None,
            help="Path to grpc_cpp_plugin (default: auto-detect, fallback /usr/bin/grpc_cpp_plugin)",
        )
        p.add_argument(
            "-I",
            "--include",
            action="append",
            default=[],
            help="proto include path (can be specified multiple times)",
        )
        p.add_argument(
            "--grpc-endpoint",
            default="dns:///localhost:50051",
            help="gRPC server endpoint",
        )
        p.add_argument(
            "--grpc-transport",
            default="stream",
            help="gRPC server transport",
        )
        p.add_argument(
            "--output-dir",
            default=".",
            help="Directory to write final generated files (default: current directory)",
        )
        p.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug output",
        )
        p.add_argument(
            "--clean",
            action="store_true",
            help="Remove build directory before building",
        )
        p.add_argument(
            "--secure",
            action="store_true",
            help="Enable secure gRPC connection",
        )
        p.add_argument(
            "--disable",
            action="store_true",
            help="Disable generated UDF (enabled=false in ini)",
        )
        return p

    @classmethod
    def from_cli(cls, argv: Sequence[str] | None = None) -> "CliArgs":
        ns = cls.build_parser().parse_args(argv)
        return cls(
            proto_files=list(ns.proto_files),
            build_dir=ns.build_dir,
            grpc_plugin=ns.grpc_plugin,
            include=list(ns.include),
            grpc_endpoint=ns.grpc_endpoint,
            grpc_transport=ns.grpc_transport,
            output_dir=ns.output_dir,
            debug=bool(ns.debug),
            clean=bool(ns.clean),
            secure=ns.secure,
            disable=ns.disable,
        )

    def __str__(self) -> str:
        return (
            f"proto_files={self.proto_files}, "
            f"build_dir={self.build_dir}, "
            f"grpc_endpoint={self.grpc_endpoint}, "
            f"grpc_transport={self.grpc_transport}, "
            f"output_dir={self.output_dir}"
        )

    def dump(self) -> list[str]:
        return [
            f"proto_files      : {self.proto_files}",
            f"build_dir        : {self.build_dir}",
            f"grpc_plugin      : {self.grpc_plugin}",
            f"include          : {self.include}",
            f"grpc_endpoint    : {self.grpc_endpoint}",
            f"grpc_transport   : {self.grpc_transport}",
            f"output_dir       : {self.output_dir}",
            f"debug            : {self.debug}",
            f"secure           : {self.secure}",
            f"disable          : {self.disable}",
        ]

    def to_info_lines(self) -> list[str]:
        return [
            f"proto files     :",
            *[f"  - {p}" for p in self.proto_files],
            f"build dir       : {self.build_dir}",
            f"grpc plugin     : {self.grpc_plugin}",
            f"include         : {self.include}",
            f"grpc endpoint   : {self.grpc_endpoint}",
            f"grpc transport  : {self.grpc_transport}",
            f"output dir      : {self.output_dir}",
            f"debug           : {self.debug}",
            f"secure          : {self.secure}",
            f"disable         : {self.disable}",
        ]
