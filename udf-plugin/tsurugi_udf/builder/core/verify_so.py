from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Set

from .log import debug, warn, error


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
        warn("verify: warnings detected:")
        for w in warnings:
            warn(f"  - {w}")

    if errors:
        error("verify: errors detected:")
        for e in errors:
            error(f"  - {e}")
        raise SystemExit(2)

    debug("verify: OK (DT_NEEDED / RUNPATH look consistent)")


def proto_libfile_for_proto(proto_name: str) -> str:
    return f"lib{Path(proto_name).stem}_proto.so"


def verify_split_shared_libs(
    *,
    plugin_outputs: Dict[str, Path],
    proto_outputs: Dict[str, Path],
    import_graph: Dict[str, Set[str]],
    require_origin_rpath: bool = True,
    forbid_path_needed: bool = True,
) -> None:
    errors: list[str] = []
    warnings: list[str] = []

    for proto, so_path in sorted(proto_outputs.items()):
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
        expected = {proto_outputs[d].name for d in deps if d in proto_outputs}

        missing = sorted(expected - n)
        if missing:
            errors.append(
                f"{so_path.name}: missing DT_NEEDED for proto deps: {missing}"
            )

    for proto, so_path in sorted(plugin_outputs.items()):
        n = needed_libs(so_path)
        rp = runpath_rpath(so_path)

        if require_origin_rpath and "$ORIGIN" not in rp:
            warnings.append(
                f"{so_path.name}: missing $ORIGIN in RUNPATH/RPATH (got: {rp!r})"
            )

        if proto not in proto_outputs:
            errors.append(
                f"{so_path.name}: missing proto output for plugin body: {proto}"
            )
        else:
            expected = proto_outputs[proto].name
            if expected not in n:
                errors.append(
                    f"{so_path.name}: missing DT_NEEDED for proto body: {expected}"
                )

        if forbid_path_needed:
            bad = sorted([x for x in n if "/" in x])
            if bad:
                errors.append(f"{so_path.name}: DT_NEEDED contains path entries: {bad}")

    if warnings:
        warn("verify: warnings detected:")
        for w in warnings:
            warn(f" - {w}")

    if errors:
        error("verify: errors detected:")
        for e in errors:
            error(f" - {e}")
        raise SystemExit(2)

    debug("verify split: OK (DT_NEEDED / RUNPATH look consistent)")
