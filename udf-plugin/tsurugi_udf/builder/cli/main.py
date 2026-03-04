from __future__ import annotations

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
from ..core.descriptor import load_fds, build_import_graph, find_unlisted_imports
from ..core.gen_tpl import render_tpl_for_rpc_protos
from ..core.log import info, debug, error, debug_list, setup, warn, section
from ..core.compile_tpl import compile_tpl_objects_parallel
from ..core.compile_common import compile_common_objects, archive_common_static
from ..core.link_shared import build_shared_libs_layered_parallel
from ..core.verify_so import verify_shared_libs
from ..core.analyze_rpcs import dump_rpc_so_report
from ..core.write_ini import write_ini_files_for_rpc_libs


def main(argv: list[str] | None = None) -> None:
    args = CliArgs.from_cli(argv)
    setup(debug=args.debug)

    debug(args.to_debug_summary())
    for line in args.to_debug_detail_lines():
        debug(line)

    spec = importlib.util.find_spec("tsurugi_udf")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("Cannot locate tsurugi_udf package directory")

    pkg_dir = Path(next(iter(spec.submodule_search_locations))).resolve()
    tsurugi_udf_common_dir = pkg_dir / "common" / "tsurugi_udf_common"

    raw_includes = list(args.include) if args.include else ["."]
    includes = validate_includes(raw_includes)
    proto_files = validate_proto_files([Path(p) for p in args.proto_files])

    debug(f"pkg: tsurugi_udf={pkg_dir} common={tsurugi_udf_common_dir}")

    build_dir = Path(args.build_dir)
    paths = BuildPaths.from_build_dir(build_dir)
    desc_pb = paths.OUT / "all.desc.pb"

    outputs: dict[str, Path] | None = None
    ini_outputs: dict[str, Path] | None = None
    output_dir: Path | None = None

    try:
        with section("build dir"):
            if build_dir.exists():
                if args.clean:
                    info(f"cleaning build dir: {build_dir}")
                    shutil.rmtree(build_dir)
                else:
                    info(f"reusing build dir: {build_dir}")
            else:
                info(f"creating build dir: {build_dir}")

            ensure_dirs(paths)
            debug(
                "BuildPaths: "
                f"GEN={paths.GEN} TPL={paths.TPL} OBJ={paths.OBJ} "
                f"LIB={paths.LIB} INI={paths.INI} OUT={paths.OUT}"
            )

        with section("code generation"):
            info("generating C++/gRPC sources from .proto files...")
            grpc_plugin = find_grpc_cpp_plugin(args.grpc_plugin)
            debug(f"resolved grpc plugin: {grpc_plugin}")

            cmd = protoc.build_protoc_cmd(
                includes=includes,
                proto_files=proto_files,
                desc_out=desc_pb,
                gen_dir=paths.GEN,
                grpc_plugin_path=grpc_plugin,
            )
            debug("protoc cmd: " + " ".join(map(str, cmd)))
            protoc.run(cmd)
            debug(f"descriptor: {desc_pb}")

            fds = load_fds(desc_pb)
            graph = build_import_graph(fds)
            info(f"import graph: {len(graph)} proto(s)")
            debug_list("import graph protos", sorted(graph.keys()))

            unmappable, unlisted = find_unlisted_imports(
                fds=fds,
                includes=includes,
                proto_files=proto_files,
                exclude_well_known=True,
            )

            if unmappable:
                warn("Some specified .proto files are not under any -I include path.")
                warn("Cannot map them to import names (check your --I settings):")
                for p in unmappable:
                    warn(f"  - {p}")

            if unlisted:
                info(
                    "Imported .proto files detected that were not explicitly specified:"
                )
                for n in unlisted:
                    info(f"  - {n}")

                if args.auto_deps:
                    info(
                        "Auto-deps enabled (default): including them and retrying code generation."
                    )
                    proto_files2 = [*proto_files, *unlisted]  # Path + str 混在OK
                    cmd2 = protoc.build_protoc_cmd(
                        includes=includes,
                        proto_files=proto_files2,
                        desc_out=desc_pb,
                        gen_dir=paths.GEN,
                        grpc_plugin_path=grpc_plugin,
                    )
                    debug("protoc cmd (auto-deps): " + " ".join(map(str, cmd2)))
                    protoc.run(cmd2)

                    fds = load_fds(desc_pb)
                    graph = build_import_graph(fds)
                    info(f"import graph (after auto-deps): {len(graph)} proto(s)")
                    debug_list(
                        "import graph protos (after auto-deps)", sorted(graph.keys())
                    )
                else:
                    error(
                        "Unlisted imported .proto files found and --no-auto-deps specified."
                    )
                    error("Please explicitly add them via --proto or enable auto-deps.")
                    for n in unlisted:
                        error(f"  - {n}")
                    raise SystemExit(1)

            info("code generation completed.")

        with section("templates"):
            info("rendering RPC templates...")
            templates_dir = Path(__file__).resolve().parents[1] / "templates"
            debug(f"templates_dir: {templates_dir}")

            rendered = render_tpl_for_rpc_protos(
                fds=fds,
                templates_dir=templates_dir,
                tpl_dir=paths.TPL,
            )
            info(f"template rendering completed. ({len(rendered)} proto(s))")
            debug(f"template dir: {paths.TPL}")

            tpl_subdirs = [p for p in sorted(paths.TPL.glob("*")) if p.is_dir()]
            gen_subdirs = [p for p in sorted(paths.GEN.rglob("*")) if p.is_dir()]
            tpl_include_dirs: list[Path] = [
                *tpl_subdirs,
                tsurugi_udf_common_dir / "include" / "udf",
                paths.GEN,
                *gen_subdirs,
                *includes,
            ]

            debug_list("tpl_subdirs", tpl_subdirs)
            debug_list("gen_subdirs", gen_subdirs)
            debug_list("tpl_include_dirs", tpl_include_dirs)

        with section("compile templates"):
            tpl_objs, tpl_objs_by_stem = compile_tpl_objects_parallel(
                tpl_dir=paths.TPL,
                obj_dir=paths.OBJ,
                include_dirs=[str(p) for p in tpl_include_dirs],
                jobs=None,
            )
            info(f"compiled template sources: {len(tpl_objs)} objects")

            for stem, objs in sorted(tpl_objs_by_stem.items()):
                debug(
                    f"tpl stem '{stem}': {len(objs)} objs -> {(paths.OBJ / 'tpl' / stem)}"
                )
                for o in sorted(objs, key=lambda p: p.name):
                    debug(f"  - {o.name}")

        with section("compile runtime"):
            common_srcs = [
                tsurugi_udf_common_dir / "src" / "udf" / "descriptor_impl.cpp",
                tsurugi_udf_common_dir / "src" / "udf" / "error_info.cpp",
                tsurugi_udf_common_dir / "src" / "udf" / "generic_record_impl.cpp",
            ]
            common_include_dirs = [
                tsurugi_udf_common_dir / "include" / "udf",
                paths.GEN,
                *includes,
            ]
            debug_list("common_srcs", common_srcs)
            debug_list("common_include_dirs", common_include_dirs)

            common_obj_dir = paths.OBJ / "common" / "obj"
            common_objs = compile_common_objects(
                sources=common_srcs,
                obj_dir=common_obj_dir,
                include_dirs=[str(p) for p in common_include_dirs],
            )
            common_a = archive_common_static(
                objs=common_objs,
                out_dir=paths.OBJ / "common" / "lib",
            )
            info(f"compiled runtime library: {common_a.name}")
            debug(f"runtime static: {common_a}")

        with section("compile generated"):
            gen_include_dirs = [
                paths.GEN,
                *includes,
                tsurugi_udf_common_dir / "include" / "udf",
            ]
            debug_list("gen_include_dirs", gen_include_dirs)

            gen_objs = build_objects_parallel(
                gen_dir=paths.GEN,
                obj_dir=paths.OBJ / "gen",
                include_dirs=[str(p) for p in gen_include_dirs],
                jobs=None,
            )
            info(f"compiled generated sources: {len(gen_objs)} objects")
            for obj in gen_objs:
                rel = obj.relative_to(paths.OBJ / "gen")
                src = (paths.GEN / rel).with_suffix(".cc")
                debug(f"gen: {src} -> {obj}")

        with section("link"):
            target_protos = set(graph.keys())
            exclude_protos: set[str] = set()

            outputs = build_shared_libs_layered_parallel(
                import_graph=graph,
                target_protos=target_protos,
                obj_dir=paths.OBJ / "gen",
                lib_dir=paths.LIB,
                exclude_protos=exclude_protos,
                jobs=None,
                tpl_objs_by_stem=tpl_objs_by_stem,
                common_static=common_a,
            )
            info(f"linked shared libraries: {len(outputs)}")
            for pn in sorted(outputs.keys()):
                debug(f"so: {pn} -> {outputs[pn]}")

        with section("verify"):
            verify_shared_libs(
                outputs=outputs,
                import_graph=graph,
                require_origin_rpath=True,
                forbid_path_needed=True,
            )
            info("verification completed.")

        with section("report"):
            dump_rpc_so_report(fds)

        with section("ini"):
            ini_outputs = write_ini_files_for_rpc_libs(
                fds,
                lib_dir=paths.LIB,
                ini_dir=paths.INI,
                endpoint=args.grpc_endpoint,
                transport=args.grpc_transport,
                secure=args.secure,
                enabled=not args.disable,
            )
            info(
                "wrote ini files: "
                f"{len(ini_outputs)} (endpoint={args.grpc_endpoint}, transport={args.grpc_transport}, secure={'true' if args.secure else 'false'})"
            )

        with section("output"):
            output_dir = Path(args.output_dir).resolve()
            move_outputs(
                src_lib_dir=paths.LIB,
                src_ini_dir=paths.INI,
                dst_root=output_dir,
            )
            info(f"output directory: {output_dir}")

        info("")
        info("Build succeeded.")
        info("")

        if outputs:
            info("Generated libraries:")
            for so_path in sorted(outputs.values(), key=lambda p: p.name):
                info(f"  - {so_path.name}")

        if ini_outputs:
            info("")
            info("Generated ini files:")
            for ini_path in sorted(ini_outputs.values(), key=lambda p: p.name):
                info(f"  - {ini_path.name}")

    except ToolNotFoundError as e:
        error(f"{e}")
        raise SystemExit(2)
    except CommandFailedError as e:
        if e.stderr:
            error(e.stderr, end="")
        raise SystemExit(e.returncode)


if __name__ == "__main__":
    main(sys.argv[1:])
