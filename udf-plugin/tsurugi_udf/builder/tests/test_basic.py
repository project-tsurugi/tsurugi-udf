import tempfile
from udf_plugin_builder import build_with_cmake
from pathlib import Path


def test_basic_build():
    with tempfile.TemporaryDirectory() as tmp_dir:
        build_with_cmake.run(
            [
                "--name",
                "plugin_api_test",
                "--proto-file",
                "tests/proto/sample.proto",
            ]
        )
        for fname in [
            "libplugin_api_test.so",
            "libplugin_api_test.ini",
        ]:
            p = Path(fname)
            if p.exists():
                p.unlink()
