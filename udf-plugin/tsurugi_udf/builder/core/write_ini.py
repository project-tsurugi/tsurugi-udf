from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple
from google.protobuf.descriptor_pb2 import FileDescriptorSet

from .analyze_rpcs import collect_rpc_so_report


def _split_endpoint(endpoint: str) -> Tuple[str, int]:
    if ":" not in endpoint:
        raise ValueError(f"endpoint has no port: {endpoint}")
    prefix, port_s = endpoint.rsplit(":", 1)
    return prefix, int(port_s)


def write_ini_files_for_rpc_libs(
    fds: FileDescriptorSet,
    *,
    lib_dir: Path,
    ini_dir: Path,
    endpoint: str,
    transport: str,
    secure: bool = False,
    enabled: bool = True,
) -> Dict[str, Path]:
    report = collect_rpc_so_report(fds)

    ini_dir.mkdir(parents=True, exist_ok=True)

    ep_prefix, base_port = _split_endpoint(endpoint)

    out: Dict[str, Path] = {}
    for i, so_file in enumerate(sorted(report.keys())):
        so_path = lib_dir / so_file
        ini_path = ini_dir / Path(so_file).with_suffix(".ini").name

        if not so_path.exists():
            print(f"WARNING: missing paired .so for ini: {so_path}")
            continue

        port = base_port + i
        ep = f"{ep_prefix}:{port}"

        ini_text = "\n".join(
            [
                "[udf]",
                f"enabled={'true' if enabled else 'false'}",
                f"endpoint={ep}",
                f"secure={'true' if secure else 'false'}",
                f"transport={transport}",
                "",
            ]
        )
        ini_path.write_text(ini_text, encoding="utf-8")
        out[so_file] = ini_path

    return out
