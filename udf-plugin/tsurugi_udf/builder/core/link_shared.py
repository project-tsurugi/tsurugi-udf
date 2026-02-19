from __future__ import annotations

import concurrent.futures
import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Set, List, Tuple


def _pkg_config_libs() -> list[str]:
    try:
        r = subprocess.run(
            ["pkg-config", "--libs", "protobuf", "grpc++"],
            check=True,
            text=True,
            capture_output=True,
        )
        out = r.stdout.strip()
        return shlex.split(out) if out else []
    except Exception:
        return []


def _dedup_keep_order(xs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def topo_layers(graph: Dict[str, Set[str]]) -> List[List[str]]:
    nodes = set(graph.keys())
    users: Dict[str, Set[str]] = {}
    indeg: Dict[str, int] = {n: 0 for n in nodes}

    for n, deps in graph.items():
        indeg[n] = len(deps)
        for d in deps:
            users.setdefault(d, set()).add(n)

    layer: list[str] = sorted([n for n in nodes if indeg[n] == 0])
    layers: List[List[str]] = []
    processed = 0

    while layer:
        layers.append(layer)
        next_nodes: list[str] = []
        for n in layer:
            processed += 1
            for u in users.get(n, ()):
                indeg[u] -= 1
                if indeg[u] == 0:
                    next_nodes.append(u)
        layer = sorted(next_nodes)

    if processed != len(nodes):
        remaining = sorted([n for n in nodes if indeg[n] > 0])
        raise RuntimeError(f"cycle detected in lib dependency graph: {remaining}")

    return layers


def resolve_lib_names(proto_names: list[str]) -> Dict[str, str]:
    by_stem: Dict[str, list[str]] = {}
    for pn in proto_names:
        by_stem.setdefault(Path(pn).stem, []).append(pn)

    mapping: Dict[str, str] = {}
    for stem, items in by_stem.items():
        if len(items) == 1:
            mapping[items[0]] = f"lib{stem}.so"
        else:
            for pn in items:
                safe = pn.replace("/", "__").replace(".proto", "")
                mapping[pn] = f"lib{safe}.so"
    return mapping


def build_lib_dep_graph(
    import_graph: Dict[str, Set[str]],
    *,
    include_protos: Set[str],
    exclude_protos: Set[str] | None = None,
) -> Dict[str, Set[str]]:
    exclude_protos = exclude_protos or set()

    targets = {p for p in include_protos if p not in exclude_protos}
    out: Dict[str, Set[str]] = {}
    for p in targets:
        deps = import_graph.get(p, set())
        out[p] = {d for d in deps if d in targets}
    return out


def obj_paths_for_proto(proto_name: str, obj_dir: Path) -> list[Path]:
    base = obj_dir / Path(proto_name).with_suffix("")
    candidates = [
        Path(str(base) + ".pb.o"),
        Path(str(base) + ".grpc.pb.o"),
    ]
    return [p for p in candidates if p.exists()]


def link_one_shared(
    *,
    proto_name: str,
    out_lib_path: Path,
    obj_dir: Path,
    lib_dir: Path,
    deps: list[str],
    proto_to_libfile: Dict[str, str],
    extra_ldflags: list[str],
    cxx: str,
    extra_objs: list[Path] | None = None,
    common_static: Path | None = None,
) -> None:
    objs = obj_paths_for_proto(proto_name, obj_dir)
    if not objs:
        raise RuntimeError(
            f"no object files found for proto: {proto_name} (expected under {obj_dir})"
        )
    if extra_objs:
        objs = objs + [p for p in extra_objs if p.exists()]

    lib_dir.mkdir(parents=True, exist_ok=True)
    out_lib_path.parent.mkdir(parents=True, exist_ok=True)

    dep_lib_args: list[str] = []
    for d in deps:
        libfile = proto_to_libfile[d]
        dep_lib_args.append(f"-l:{libfile}")

    rpath_flag = "-Wl,-rpath,$ORIGIN"

    cmd = [cxx, "-shared", "-o", str(out_lib_path)]
    cmd += [str(o) for o in objs]
    if common_static is not None:
        common_static = Path(common_static)
        if not common_static.exists():
            raise RuntimeError(f"common static archive not found: {common_static}")
        cmd += [str(common_static)]

    cmd += [f"-L{lib_dir}"]
    cmd += dep_lib_args
    cmd += [rpath_flag]
    cmd += extra_ldflags

    r = subprocess.run(cmd, text=True, capture_output=True)
    if r.returncode != 0:
        msg = ["link failed:", "  " + " ".join(map(str, cmd))]
        if r.stdout:
            msg.append(r.stdout)
        if r.stderr:
            msg.append(r.stderr)
        raise RuntimeError("\n".join(msg))


def build_shared_libs_layered_parallel(
    *,
    import_graph: Dict[str, Set[str]],
    target_protos: Set[str],
    obj_dir: Path,
    lib_dir: Path,
    exclude_protos: Set[str] | None = None,
    jobs: int | None = None,
    tpl_objs_by_stem: dict[str, list[Path]] | None = None,
    common_static: Path | None = None,
) -> Dict[str, Path]:
    exclude_protos = exclude_protos or set()

    lib_dep_graph = build_lib_dep_graph(
        import_graph,
        include_protos=target_protos,
        exclude_protos=exclude_protos,
    )
    layers = topo_layers(lib_dep_graph)

    proto_list = sorted(lib_dep_graph.keys())
    proto_to_libfile = resolve_lib_names(proto_list)

    cxx = os.environ.get("CXX", "g++")
    extra = shlex.split(os.environ.get("LDFLAGS", ""))
    extra += _pkg_config_libs()
    extra = _dedup_keep_order(extra)

    max_workers = jobs or (os.cpu_count() or 4)
    outputs: Dict[str, Path] = {}

    for i, layer in enumerate(layers):
        print(f"# link layer[{i}] ({len(layer)} libs)")

        def _job(pn: str) -> Tuple[str, Path]:
            out = lib_dir / proto_to_libfile[pn]
            deps = sorted(lib_dep_graph.get(pn, ()))
            stem = Path(pn).stem
            extra_objs = (tpl_objs_by_stem or {}).get(stem, [])
            link_one_shared(
                proto_name=pn,
                out_lib_path=out,
                obj_dir=obj_dir,
                lib_dir=lib_dir,
                deps=deps,
                proto_to_libfile=proto_to_libfile,
                extra_ldflags=extra,
                cxx=cxx,
                extra_objs=extra_objs,
                common_static=common_static,
            )
            return pn, out

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = [ex.submit(_job, pn) for pn in layer]
            for f in concurrent.futures.as_completed(futs):
                pn, out = f.result()
                outputs[pn] = out

    return outputs
