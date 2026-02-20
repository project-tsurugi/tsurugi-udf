import os, shutil
from pathlib import Path
from ..errors import ToolNotFoundError


def find_grpc_cpp_plugin(cli_value: str | None = None) -> Path:
    candidates: list[str] = []
    if cli_value:
        candidates.append(cli_value)

    env_val = os.environ.get("GRPC_CPP_PLUGIN") or os.environ.get("PROTOC_GEN_GRPC")
    if env_val:
        candidates.append(env_val)

    which_val = shutil.which("grpc_cpp_plugin")
    if which_val:
        candidates.append(which_val)

    candidates += ["/usr/bin/grpc_cpp_plugin", "/usr/local/bin/grpc_cpp_plugin"]

    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        p = Path(c)
        if p.exists() and p.is_file() and os.access(p, os.X_OK):
            return p

    raise ToolNotFoundError(
        "grpc_cpp_plugin not found (use --grpc-plugin or set GRPC_CPP_PLUGIN)"
    )
