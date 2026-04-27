from __future__ import annotations

import concurrent.futures
import os
import subprocess
from pathlib import Path

from .log import debug, debug_list
from .toolchain import get_cxx, get_cxxflags


def find_generated_cc(gen_dir: Path) -> list[Path]:
    cc: list[Path] = []
    for p in gen_dir.rglob("*.cc"):
        if p.name.endswith(".pb.cc") or p.name.endswith(".grpc.pb.cc"):
            cc.append(p)
    return sorted(cc)


def obj_path_for(cc: Path, gen_dir: Path, obj_dir: Path) -> Path:
    rel = cc.relative_to(gen_dir)
    return (obj_dir / rel).with_suffix(".o")


def compile_one(
    *,
    cxx: str,
    cc: Path,
    obj: Path,
    include_dirs: list[str],
    extra_cflags: list[str],
) -> None:
    obj.parent.mkdir(parents=True, exist_ok=True)

    cmd = [cxx, "-fPIC", "-c", str(cc), "-o", str(obj)]
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


def build_objects_parallel(
    *, gen_dir: Path, obj_dir: Path, include_dirs: list[str], jobs: int | None = None
) -> list[Path]:
    cxx = get_cxx()
    extra = get_cxxflags()

    cc_files = find_generated_cc(gen_dir)
    if not cc_files:
        debug(f"no generated .cc files found under: {gen_dir}")
        return []

    objs = [obj_path_for(cc, gen_dir, obj_dir) for cc in cc_files]

    max_workers = jobs or (os.cpu_count() or 4)
    debug(
        f"compiling generated sources: {len(cc_files)} files -> {obj_dir} (jobs={max_workers})"
    )

    if len(cc_files) <= 30:
        debug_list("generated .cc files", (str(p) for p in cc_files))
    else:
        debug(f"generated .cc files: {len(cc_files)} (list omitted)")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [
            ex.submit(
                compile_one,
                cxx=cxx,
                cc=cc,
                obj=obj,
                include_dirs=include_dirs,
                extra_cflags=extra,
            )
            for cc, obj in zip(cc_files, objs)
        ]
        for f in concurrent.futures.as_completed(futs):
            f.result()

    return objs
