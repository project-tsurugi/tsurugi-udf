from __future__ import annotations

import concurrent.futures
import os
import shlex
import subprocess
from pathlib import Path


def find_generated_cc(gen_dir: Path) -> list[Path]:
    cc: list[Path] = []
    for p in gen_dir.rglob("*.cc"):
        if p.name.endswith(".pb.cc") or p.name.endswith(".grpc.pb.cc"):
            cc.append(p)
    return sorted(cc)


def obj_path_for(cc: Path, gen_dir: Path, obj_dir: Path) -> Path:
    rel = cc.relative_to(gen_dir)
    return (obj_dir / rel).with_suffix(".o")


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
    *,
    gen_dir: Path,
    obj_dir: Path,
    include_dirs: list[str],
    jobs: int | None = None,
    cxx: str | None = None,
) -> list[Path]:
    cxx = cxx or os.environ.get("CXX", "g++")

    extra = shlex.split(os.environ.get("CXXFLAGS", ""))
    extra += _pkg_config_cflags()

    cc_files = find_generated_cc(gen_dir)
    if not cc_files:
        print(f"no generated .cc files found under: {gen_dir}")
        return []

    objs = [obj_path_for(cc, gen_dir, obj_dir) for cc in cc_files]

    max_workers = jobs or (os.cpu_count() or 4)
    print(f"# compiling {len(cc_files)} files -> {obj_dir} (jobs={max_workers})")

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
