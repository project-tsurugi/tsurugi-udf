from __future__ import annotations

import concurrent.futures
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


def _compile_one(
    *, cxx: str, src: Path, obj: Path, include_dirs: list[str], extra_cflags: list[str]
) -> None:
    obj.parent.mkdir(parents=True, exist_ok=True)

    cmd = [cxx, "-fPIC", "-c", str(src), "-o", str(obj)]
    for inc in include_dirs:
        cmd.append(f"-I{inc}")
    cmd += extra_cflags

    r = subprocess.run(cmd, text=True, capture_output=True)
    if r.returncode != 0:
        msg = ["compile failed:", "  " + " ".join(map(str, cmd))]
        if r.stdout:
            msg.append(r.stdout)
        if r.stderr:
            msg.append(r.stderr)
        raise RuntimeError("\n".join(msg))


def compile_tpl_objects_parallel(
    *,
    tpl_dir: Path,
    obj_dir: Path,
    include_dirs: list[str],
    jobs: int | None = None,
    cxx: str | None = None,
) -> tuple[list[Path], dict[str, list[Path]]]:
    cxx = cxx or os.environ.get("CXX", "g++")
    extra = shlex.split(os.environ.get("CXXFLAGS", ""))
    extra += _pkg_config_cflags()

    cpp_files = sorted(tpl_dir.rglob("*.cpp"))
    if not cpp_files:
        print(f"# no tpl cpp files under: {tpl_dir}")
        return [], {}

    def _obj_for(src: Path) -> Path:
        rel = src.relative_to(tpl_dir)
        return (obj_dir / "tpl" / rel).with_suffix(".o")

    objs = [_obj_for(s) for s in cpp_files]

    max_workers = jobs or (os.cpu_count() or 4)
    print(
        f"# compiling tpl {len(cpp_files)} files -> {obj_dir / 'tpl'} (jobs={max_workers})"
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [
            ex.submit(
                _compile_one,
                cxx=cxx,
                src=src,
                obj=obj,
                include_dirs=include_dirs,
                extra_cflags=extra,
            )
            for src, obj in zip(cpp_files, objs)
        ]
        for f in concurrent.futures.as_completed(futs):
            f.result()

    by_stem: dict[str, list[Path]] = {}
    for o in objs:
        rel = o.relative_to(obj_dir / "tpl")
        stem = rel.parts[0]
        by_stem.setdefault(stem, []).append(o)

    return objs, by_stem
