from __future__ import annotations

from pathlib import Path
from typing import Dict

from google.protobuf.descriptor_pb2 import FileDescriptorSet

from .analyze_rpcs import collect_rpc_so_report
from .log import debug, warn


def _format_secure(secure: bool | str) -> str:
    if isinstance(secure, bool):
        return "true" if secure else "false"
    return secure


def write_ini_files_for_rpc_libs(
    fds: FileDescriptorSet,
    *,
    lib_dir: Path,
    ini_dir: Path,
    endpoint: str,
    grpc_server_endpoint: str | None,
    transport: str,
    secure: bool | str = False,
    enabled: bool = True,
    udf_timeout: int | None = None,
) -> Dict[str, Path]:
    report = collect_rpc_so_report(fds)

    secure_value = _format_secure(secure)
    ini_dir.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Path] = {}
    for so_file in sorted(report.keys()):
        so_path = lib_dir / so_file
        ini_path = ini_dir / Path(so_file).with_suffix(".ini").name

        if not so_path.exists():
            warn(f"missing paired .so for ini: {so_path}")
            continue
        ini_text = "\n".join(
            [
                "[udf]",
                f"enabled={'true' if enabled else 'false'}",
                f"endpoint={endpoint}",
                f"secure={secure_value}",
                f"transport={transport}",
                *([f"timeout={udf_timeout}"] if udf_timeout is not None else []),
                *(
                    [
                        "",
                        "[grpc_server]",
                        f"endpoint={grpc_server_endpoint}",
                    ]
                    if grpc_server_endpoint
                    else []
                ),
                "",
            ]
        )
        ini_path.write_text(ini_text, encoding="utf-8")
        out[so_file] = ini_path
        debug(f"wrote ini: {ini_path} (for {so_file})")

    return out
