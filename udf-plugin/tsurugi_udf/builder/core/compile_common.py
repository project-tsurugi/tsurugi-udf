from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path


def _pkg_config_cflags() -> list[str]:
    try:
        r = subprocess.run(
            ["pkg-config", "--cflags", "protobuf", "grpc++"],
            check=True,
            text=True,
            capture_output=True,
        )
        out = r.stdout.strip()
        return shlex.split(out) if out else []
    except Exception:
        return []


def compile_common_objects(
    *,
    sources: list[Path],
    obj_dir: Path,
    include_dirs: list[str],
    cxx: str | None = None,
) -> list[Path]:
    cxx = cxx or os.environ.get("CXX", "g++")

    extra = shlex.split(os.environ.get("CXXFLAGS", ""))
    extra += _pkg_config_cflags()

    objs: list[Path] = []
    for src in sources:
        if not src.exists():
            raise FileNotFoundError(f"common source not found: {src}")

        obj = (obj_dir / src.name).with_suffix(".o")
        obj.parent.mkdir(parents=True, exist_ok=True)

        cmd = [cxx, "-fPIC", "-c", str(src), "-o", str(obj)]
        for inc in include_dirs:
            cmd.append(f"-I{inc}")
        cmd += extra

        r = subprocess.run(cmd, text=True, capture_output=True)
        if r.returncode != 0:
            msg = ["compile common failed:", "  " + " ".join(map(str, cmd))]
            if r.stdout:
                msg.append(r.stdout)
            if r.stderr:
                msg.append(r.stderr)
            raise RuntimeError("\n".join(msg))

        objs.append(obj)

    return objs


def archive_common_static(
    *,
    objs: list[Path],
    out_dir: Path,
    name: str = "libtsurugi_udf_common.a",
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name

    if out.exists():
        out.unlink()

    cmd = ["ar", "rcs", str(out), *map(str, objs)]
    subprocess.run(cmd, check=True)
    return out
