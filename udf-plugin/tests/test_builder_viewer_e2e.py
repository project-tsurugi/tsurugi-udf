from pathlib import Path

import pytest

from tsurugi_udf.builder.cli.main import main


DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "proto_name",
    [
        "minimal.proto",
        "udf_stream.proto",
    ],
)
def test_builder_cli_generates_outputs(tmp_path: Path, proto_name: str) -> None:
    proto = DATA_DIR / proto_name
    assert proto.exists(), f"Proto file not found: {proto}"

    build_dir = tmp_path / "build"
    out_dir = tmp_path / "out"

    argv = [
        "--proto",
        str(proto),
        "--build-dir",
        str(build_dir),
        "--output-dir",
        str(out_dir),
        "-I",
        str(DATA_DIR),
    ]

    try:
        main(argv)
    except SystemExit as e:
        pytest.fail(f"builder cli failed with SystemExit({e.code})")

    so_files = sorted(out_dir.glob("lib*.so"))
    ini_files = sorted(out_dir.glob("*.ini"))
    desc_files = sorted(out_dir.glob("*.desc.pb"))

    print(f"[{proto_name}] so  files: {so_files}")
    print(f"[{proto_name}] ini files: {ini_files}")
    print(f"[{proto_name}] desc files: {desc_files}")

    assert so_files, f"No .so file generated in {out_dir}"
    assert ini_files, f"No .ini file generated in {out_dir}"
    assert desc_files, f"No .desc.pb file generated in {out_dir}"
