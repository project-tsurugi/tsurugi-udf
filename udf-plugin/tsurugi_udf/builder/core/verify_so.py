from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Set


def _readelf_dynamic(so: Path) -> str:
    r = subprocess.run(["readelf", "-d", str(so)], text=True, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"readelf failed for {so}:\n{r.stderr}")
    return r.stdout


def needed_libs(so: Path) -> set[str]:
    out = _readelf_dynamic(so)
    libs: set[str] = set()
    for line in out.splitlines():
        if "NEEDED" in line:
            libs.add(line.split("[", 1)[1].split("]", 1)[0])
    return libs


def runpath_rpath(so: Path) -> str:
    out = _readelf_dynamic(so)
    for line in out.splitlines():
        if "(RUNPATH)" in line or "(RPATH)" in line:
            return line.split("[", 1)[1].split("]", 1)[0]
    return ""


def libfile_for_proto(proto_name: str) -> str:
    return f"lib{Path(proto_name).stem}.so"


def verify_shared_libs(
    *,
    outputs: Dict[str, Path],
    import_graph: Dict[str, Set[str]],
    require_origin_rpath: bool = True,
    forbid_path_needed: bool = True,
) -> None:
    errors: list[str] = []
    warnings: list[str] = []

    built_libfiles = {p.name for p in outputs.values()}

    for proto, so_path in sorted(outputs.items()):
        n = needed_libs(so_path)
        rp = runpath_rpath(so_path)

        if require_origin_rpath and "$ORIGIN" not in rp:
            warnings.append(
                f"{so_path.name}: missing $ORIGIN in RUNPATH/RPATH (got: {rp!r})"
            )

        if forbid_path_needed:
            bad = sorted([x for x in n if "/" in x])
            if bad:
                errors.append(f"{so_path.name}: DT_NEEDED contains path entries: {bad}")

        deps = import_graph.get(proto, set())
        expected = {
            libfile_for_proto(d) for d in deps if libfile_for_proto(d) in built_libfiles
        }

        missing = sorted(expected - n)
        if missing:
            errors.append(f"{so_path.name}: missing DT_NEEDED for deps: {missing}")

    if warnings:
        print("# VERIFY WARNINGS")
        for w in warnings:
            print("WARNING:", w)

    if errors:
        print("# VERIFY ERRORS")
        for e in errors:
            print("ERROR:", e)
        raise SystemExit(2)

    print("# VERIFY OK: DT_NEEDED / RUNPATH look consistent")
