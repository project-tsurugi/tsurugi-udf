import tempfile
from udf_plugin_builder import build_with_cmake
from pathlib import Path


def test_basic_build2():
    with tempfile.TemporaryDirectory() as tmp_dir:
        build_with_cmake.run(
            [
                "--name",
                "plugin_api_test2",
                "--proto-file",
                "tests/proto/sample.proto",
                "--proto-path",
                "tests",
            ]
        )
        for fname in [
            "libplugin_api_test2.so",
            "libplugin_api_test2.ini",
        ]:
            p = Path(fname)
            if p.exists():
                p.unlink()
