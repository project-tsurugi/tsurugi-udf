from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from .paths import BuildPaths
from .log import debug
import shutil


def ensure_dirs(paths: BuildPaths) -> None:
    paths.build_dir.mkdir(parents=True, exist_ok=True)

    dirs = [
        paths.OUT,
        paths.GEN,
        paths.OBJ,
        paths.TPL,
        paths.LIB,
        paths.INI,
        paths.CMN,
    ]

    with ThreadPoolExecutor() as ex:
        futures = [ex.submit(d.mkdir, exist_ok=True) for d in dirs]
        for f in as_completed(futures):
            f.result()


def move_outputs(
    *,
    src_lib_dir: Path,
    src_ini_dir: Path,
    dst_root: Path,
    src_deps_lib_dir: Path | None = None,
) -> None:
    dst_root = dst_root.resolve()
    dst_root.mkdir(parents=True, exist_ok=True)

    if src_lib_dir.exists():
        for p in src_lib_dir.iterdir():
            if p.is_file() and p.suffix == ".so":
                dst = dst_root / p.name
                debug(f"move {p} -> {dst}")
                shutil.move(str(p), dst)

    if src_ini_dir.exists():
        for p in src_ini_dir.iterdir():
            if p.is_file() and p.suffix == ".ini":
                dst = dst_root / p.name
                debug(f"move {p} -> {dst}")
                shutil.move(str(p), dst)

    if src_deps_lib_dir and src_deps_lib_dir.exists():
        dst_deps = dst_root / "deps"
        dst_deps.mkdir(parents=True, exist_ok=True)
        for p in src_deps_lib_dir.iterdir():
            if p.is_file() and p.suffix == ".so":
                dst = dst_deps / p.name
                debug(f"move {p} -> {dst}")
                shutil.move(str(p), dst)
