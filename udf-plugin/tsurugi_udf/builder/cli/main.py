from pathlib import Path
import sys
import shutil
import importlib.util

from .args import CliArgs
from .validate import validate_includes, validate_proto_files
from ..core.compile_gen import build_objects_parallel
from ..core.paths import BuildPaths
from ..core.fs import ensure_dirs, move_outputs
from ..core.tools.grpc_plugin import find_grpc_cpp_plugin
from ..core.tools import protoc
from ..core.errors import ToolNotFoundError, CommandFailedError
from ..core.descriptor import load_fds, build_import_graph
from ..core.gen_tpl import render_tpl_for_rpc_protos
from ..core.log import info, debug, error
from ..core.compile_tpl import compile_tpl_objects_parallel
from ..core.compile_common import compile_common_objects, archive_common_static
from ..core.link_shared import build_shared_libs_layered_parallel
from ..core.verify_so import verify_shared_libs
from ..core.analyze_rpcs import dump_rpc_so_report
from ..core.write_ini import write_ini_files_for_rpc_libs


def mkdir(p: Path) -> None:
    p.mkdir(exist_ok=True)


def main(argv: list[str] | None = None) -> None:
    args = CliArgs.from_cli(argv)
    for line in args.to_info_lines():
        info(line)
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir / "templates"
    spec = importlib.util.find_spec("tsurugi_udf")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("Cannot locate tsurugi_udf package directory")

    pkg_dir = Path(next(iter(spec.submodule_search_locations))).resolve()
    tsurugi_udf_common_dir = pkg_dir / "common" / "tsurugi_udf_common"
    templates_dir = pkg_dir / "builder" / "templates"
    includes = validate_includes(list(args.include))
    proto_files = validate_proto_files([Path(p) for p in args.proto_files])

    build_dir = Path(args.build_dir)
    if build_dir.exists():
        info(f"build dir exists: {build_dir}")
        if args.clean:
            info(f"--clean specified, removing build dir: {build_dir}")
            shutil.rmtree(build_dir)
            info(f"creating: {build_dir}")
        else:
            info(f"--clean not specified, overwriting build dir: {build_dir}")
    else:
        info(f"build dir does not exist, creating: {build_dir}")
    paths = BuildPaths.from_build_dir(build_dir)
    ensure_dirs(paths)
    desc_pb = paths.OUT / "all.desc.pb"
    try:
        grpc_plugin = find_grpc_cpp_plugin(args.grpc_plugin)
        cmd = protoc.build_protoc_cmd(
            includes=includes,
            proto_files=proto_files,
            desc_out=desc_pb,
            gen_dir=paths.GEN,
            grpc_plugin_path=grpc_plugin,
        )
        debug(" ".join(map(str, cmd)))
        protoc.run(cmd)
        fds = load_fds(desc_pb)
        graph = build_import_graph(fds)
        templates_dir = Path(__file__).resolve().parents[1] / "templates"
        # from importlib.resources import files
        # from pathlib import Path
        # templates_dir = Path(files("tsurugi_udf.builder").joinpath("templates"))
        render_tpl_for_rpc_protos(
            fds=fds,
            templates_dir=templates_dir,
            tpl_dir=paths.TPL,
        )
        tpl_subdirs = [str(p) for p in sorted(paths.TPL.glob("*")) if p.is_dir()]
        gen_subdirs = [str(p) for p in paths.GEN.rglob("*") if p.is_dir()]
        tpl_include_dirs = [
            *tpl_subdirs,
            str(tsurugi_udf_common_dir / "include" / "udf"),
            str(paths.GEN),
            *gen_subdirs,
            *[str(p) for p in includes],
        ]
        tpl_objs, tpl_objs_by_stem = compile_tpl_objects_parallel(
            tpl_dir=paths.TPL,
            obj_dir=paths.OBJ,
            include_dirs=tpl_include_dirs,
            jobs=None,
        )
        info(f"compiled tpl objects: {len(tpl_objs)}")
        if args.debug:
            for stem, objs in sorted(tpl_objs_by_stem.items()):
                debug(f"tpl stem '{stem}': {len(objs)} objs")
        for stem in sorted(tpl_objs_by_stem.keys()):
            out_dir = paths.OBJ / "tpl" / stem
            info(f"compiled tpl objects for proto '{stem}' -> {out_dir}")

            names = sorted(p.name for p in tpl_objs_by_stem[stem])
            for n in names:
                info(f"  - {n}")
        common_srcs = [
            tsurugi_udf_common_dir / "src" / "udf" / "descriptor_impl.cpp",
            tsurugi_udf_common_dir / "src" / "udf" / "error_info.cpp",
            tsurugi_udf_common_dir / "src" / "udf" / "generic_record_impl.cpp",
        ]

        common_include_dirs = [
            str(tsurugi_udf_common_dir / "include" / "udf"),
            str(paths.GEN),
            *[str(p) for p in includes],
        ]

        common_obj_dir = paths.OBJ / "common" / "obj"
        common_objs = compile_common_objects(
            sources=common_srcs,
            obj_dir=common_obj_dir,
            include_dirs=common_include_dirs,
        )

        info(f"compiled common objects: {len(common_objs)} -> {common_obj_dir}")
        for o in common_objs:
            info(f"  - {o.name}")
        common_a = archive_common_static(
            objs=common_objs,
            out_dir=paths.OBJ / "common" / "lib",
        )
        info(f"archived common static: {common_a}")

        gen_include_dirs = [
            str(paths.GEN),
            *[str(p) for p in includes],
            str(tsurugi_udf_common_dir / "include" / "udf"),
        ]
        gen_objs = build_objects_parallel(
            gen_dir=paths.GEN,
            obj_dir=paths.OBJ / "gen",
            include_dirs=gen_include_dirs,
            jobs=None,
        )
        if gen_objs:
            info(f"compiled generated sources -> objects ({len(gen_objs)} files)")
            for obj in gen_objs:
                rel = obj.relative_to(paths.OBJ / "gen")
                src = (paths.GEN / rel).with_suffix(".cc")
                info(f"  - {src} -> {obj}")
        else:
            info("no generated sources to compile")
        target_protos = set(graph.keys())
        exclude_protos: set[str] = set()

        lib_dir = paths.LIB if hasattr(paths, "LIB") else (build_dir / "lib")
        lib_dir.mkdir(parents=True, exist_ok=True)

        outputs = build_shared_libs_layered_parallel(
            import_graph=graph,
            target_protos=target_protos,
            obj_dir=paths.OBJ / "gen",
            lib_dir=lib_dir,
            exclude_protos=exclude_protos,
            jobs=None,
            tpl_objs_by_stem=tpl_objs_by_stem,
            common_static=common_a,
        )

        info(f"linked shared libs: {len(outputs)}")
        for pn in sorted(outputs.keys()):
            info(f"  - {pn} -> {outputs[pn]}")

        verify_shared_libs(
            outputs=outputs,
            import_graph=graph,
            require_origin_rpath=True,
            forbid_path_needed=True,
        )

        dump_rpc_so_report(fds)

        ini_dir = paths.INI if hasattr(paths, "INI") else (build_dir / "ini")
        ini_dir.mkdir(parents=True, exist_ok=True)

        ini_outputs = write_ini_files_for_rpc_libs(
            fds,
            lib_dir=lib_dir,
            ini_dir=ini_dir,
            endpoint=args.grpc_endpoint,
            transport=args.grpc_transport,
            secure=args.secure,
            enabled=not args.disable,
        )
        info(f"wrote ini files: {len(ini_outputs)} -> {ini_dir}")
        for so, ini in sorted(ini_outputs.items()):
            info(f"  - {so} -> {ini.name}")
        output_dir = Path(args.output_dir).resolve()
        move_outputs(
            src_lib_dir=lib_dir,
            src_ini_dir=ini_dir,
            dst_root=output_dir,
        )
        info(f"moved output files to: {output_dir}")
    except ToolNotFoundError as e:
        error(f"{e}", file=sys.stderr)
        raise SystemExit(2)
    except CommandFailedError as e:
        if e.stderr:
            error(e.stderr, file=sys.stderr, end="")
        raise SystemExit(e.returncode)
    return


if __name__ == "__main__":
    main(sys.argv[1:])
