from pathlib import Path

import pytest

from tsurugi_udf.builder.cli.main import main


DATA_DIR = Path(__file__).parent / "data"
REPO_ROOT = Path(__file__).resolve().parents[2]
TSURUGI_PROTO_DIR = REPO_ROOT / "proto"


@pytest.mark.parametrize(
    "proto_name,include_repo_proto",
    [
        ("minimal.proto", False),
        ("udf_stream.proto", False),
        ("optional.proto", True),
        ("oneof.proto", True),
    ],
)
def test_builder_cli_generates_outputs(
    tmp_path: Path,
    proto_name: str,
    include_repo_proto: bool,
) -> None:
    proto = DATA_DIR / proto_name
    assert proto.exists(), f"Proto file not found: {proto}"

    include_dirs = [DATA_DIR]
    if include_repo_proto:
        tsurugi_types_proto = (
            TSURUGI_PROTO_DIR / "tsurugidb" / "udf" / "tsurugi_types.proto"
        )
        assert (
            tsurugi_types_proto.exists()
        ), f"Tsurugi types proto not found: {tsurugi_types_proto}"
        include_dirs.append(TSURUGI_PROTO_DIR)

    build_dir = tmp_path / "build"
    out_dir = tmp_path / "out"
    argv = [
        "--proto",
        str(proto),
        "--build-dir",
        str(build_dir),
        "--output-dir",
        str(out_dir),
    ]
    for include_dir in include_dirs:
        argv += ["-I", str(include_dir)]

    try:
        main(argv)
    except SystemExit as e:
        pytest.fail(f"builder cli failed with SystemExit({e.code})")

    plugin_so = out_dir / f"lib{proto.stem}.so"
    proto_so = out_dir / "deps" / f"lib{proto.stem}_proto.so"
    ini_file = out_dir / f"lib{proto.stem}.ini"
    desc_file = out_dir / f"{proto.stem}.desc.pb"

    root_so_files = sorted(out_dir.glob("lib*.so"))
    deps_so_files = sorted((out_dir / "deps").glob("lib*.so"))
    ini_files = sorted(out_dir.glob("*.ini"))
    desc_files = sorted(out_dir.glob("*.desc.pb"))

    print(f"[{proto_name}] argv: {argv}")
    print(f"[{proto_name}] plugin so: {plugin_so}")
    print(f"[{proto_name}] proto so: {proto_so}")
    print(f"[{proto_name}] ini file: {ini_file}")
    print(f"[{proto_name}] desc file: {desc_file}")
    print(f"[{proto_name}] root so files: {root_so_files}")
    print(f"[{proto_name}] deps so files: {deps_so_files}")
    print(f"[{proto_name}] ini files: {ini_files}")
    print(f"[{proto_name}] desc files: {desc_files}")

    assert plugin_so.exists(), f"Plugin .so not generated: {plugin_so}"
    assert proto_so.exists(), f"Proto .so not generated: {proto_so}"
    assert ini_file.exists(), f".ini file not generated: {ini_file}"
    assert desc_file.exists(), f".desc.pb file not generated: {desc_file}"

    assert root_so_files, f"No root .so file generated in {out_dir}"
    assert deps_so_files, f"No deps .so file generated in {out_dir / 'deps'}"
    assert ini_files, f"No .ini file generated in {out_dir}"
    assert desc_files, f"No .desc.pb file generated in {out_dir}"

    assert plugin_so in root_so_files
    assert proto_so in deps_so_files
    assert proto_so not in root_so_files
