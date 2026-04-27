from __future__ import annotations

import concurrent.futures
import os
import subprocess
from pathlib import Path
from .toolchain import get_cxx, get_cxxflags
from .log import debug, debug_list


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
    *, tpl_dir: Path, obj_dir: Path, include_dirs: list[str], jobs: int | None = None
) -> tuple[list[Path], dict[str, list[Path]]]:
    cxx = get_cxx()
    extra = get_cxxflags()

    cpp_files = sorted(tpl_dir.rglob("*.cpp"))
    if not cpp_files:
        debug(f"no template .cpp files under: {tpl_dir}")
        return [], {}

    def _obj_for(src: Path) -> Path:
        rel = src.relative_to(tpl_dir)
        return (obj_dir / "tpl" / rel).with_suffix(".o")

    objs = [_obj_for(s) for s in cpp_files]

    max_workers = jobs or (os.cpu_count() or 4)
    out_dir = obj_dir / "tpl"

    debug(
        f"compiling templates: {len(cpp_files)} files -> {out_dir} (jobs={max_workers})"
    )
    debug_list("tpl cpp files", (str(p) for p in cpp_files))

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
        rel = o.relative_to(out_dir)
        stem = rel.parts[0]
        by_stem.setdefault(stem, []).append(o)

    return objs, by_stem
