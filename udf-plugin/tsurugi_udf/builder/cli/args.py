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
    auto_deps: bool = True
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
            "--auto-deps",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Automatically include imported .proto files (default: enabled). "
            "Use --no-auto-deps to disable and treat unlisted imports as error.",
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
            auto_deps=bool(ns.auto_deps),
            secure=ns.secure,
            disable=ns.disable,
        )

    def to_debug_summary(self) -> str:
        return (
            "args: "
            f"protos={len(self.proto_files)}, "
            f"includes={len(self.include)}, "
            f"build_dir={self.build_dir}, "
            f"transport={self.grpc_transport}, "
            f"secure={'true' if self.secure else 'false'}, "
            f"auto_deps={'true' if self.auto_deps else 'false'}, "
            f"clean={'true' if self.clean else 'false'}, "
            f"out={self.output_dir}"
        )

    def to_debug_detail_lines(self) -> list[str]:
        lines = ["args.protos:"]
        lines += [f"  - {p}" for p in self.proto_files]
        if self.include:
            lines.append("args.includes:")
            lines += [f"  - {p}" for p in self.include]
        return lines
