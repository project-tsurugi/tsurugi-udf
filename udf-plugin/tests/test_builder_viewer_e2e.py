# tests/test_builder_e2e.py
import pytest
from pathlib import Path
from tsurugi_udf.builder.udf_plugin_builder.build_with_cmake import run

def test_builder_generates_so(tmp_path):
 
    proto = Path(__file__).parent / "data" / "minimal.proto"
    assert proto.exists(), f"Proto file not found: {proto}"


    build_dir = tmp_path / "build"
    out_dir = tmp_path / "out"
    build_dir.mkdir()
    out_dir.mkdir()

    try:
        run([
            "--name", "minimal_plugin",
            "--proto-file", str(proto),
            "--build-dir", str(build_dir),
            "--output-dir", str(out_dir),
        ])
    except SystemExit as e:
        pytest.fail(f"Builder run failed with SystemExit({e.code})")

    so_files = list(out_dir.glob("lib*.so"))
    print("Generated .so files:", so_files)
    assert so_files, f"No .so file generated in {out_dir}"
