from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from google.protobuf.descriptor_pb2 import FileDescriptorSet


def default_so_name_for_proto(proto_name: str) -> str:
    return f"lib{Path(proto_name).stem}.so"


def _check_so_name_collisions(
    fds: FileDescriptorSet,
    *,
    so_name_for_proto=default_so_name_for_proto,
) -> None:
    m: Dict[str, List[str]] = {}
    for fd in fds.file:
        so = so_name_for_proto(fd.name)
        m.setdefault(so, []).append(fd.name)

    collisions = {so: ps for so, ps in m.items() if len(ps) > 1}
    if collisions:
        lines = ["so name collision detected (forbidden):"]
        for so, ps in sorted(collisions.items()):
            lines.append(f"  {so}:")
            for p in sorted(ps):
                lines.append(f"    - {p}")
        raise SystemExit("\n".join(lines))


def collect_rpc_so_report(
    fds: FileDescriptorSet,
    *,
    so_name_for_proto=default_so_name_for_proto,
) -> Dict[str, dict]:
    out: Dict[str, dict] = {}

    for fd in fds.file:
        if not fd.service:
            continue

        so = so_name_for_proto(fd.name)
        pkg = fd.package or ""
        services: Dict[str, List[str]] = {}
        rpcs: List[str] = []

        for svc in fd.service:
            methods = [m.name for m in svc.method]
            services[svc.name] = methods
            for m in svc.method:
                fq = f"{pkg + '.' if pkg else ''}{svc.name}/{m.name}"
                rpcs.append(fq)

        out[so] = {
            "proto": fd.name,
            "package": pkg,
            "services": services,
            "rpcs": rpcs,
        }

    return out


def print_rpc_so_report(report: Dict[str, dict]) -> None:
    print("\n# === RPC-bearing .so report (from all.desc.pb) ===")
    if not report:
        print("# (no services/rpcs found)")
        return

    for so in sorted(report.keys()):
        info = report[so]
        print(f"\n{so}")
        print(f"  proto: {info['proto']}")
        if info["package"]:
            print(f"  package: {info['package']}")
        for svc, methods in info["services"].items():
            print(f"  service: {svc}")
            for m in methods:
                print(f"    - {m}")


def dump_rpc_so_report(
    fds: FileDescriptorSet,
    *,
    so_name_for_proto=default_so_name_for_proto,
    check_collisions: bool = True,
) -> None:
    if check_collisions:
        _check_so_name_collisions(fds, so_name_for_proto=so_name_for_proto)

    report = collect_rpc_so_report(fds, so_name_for_proto=so_name_for_proto)
    print_rpc_so_report(report)
