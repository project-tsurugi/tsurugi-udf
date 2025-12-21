import tempfile
from udf_plugin_builder import build_with_cmake
from pathlib import Path


def test_types_build():
    with tempfile.TemporaryDirectory() as tmp_dir:
        build_with_cmake.run(
            [
                "--name",
                "types_test",
                "--proto-file",
                "tests/proto/read_tsurugi_types.proto",
                "../../proto/tsurugidb/udf/tsurugi_types.proto",
                "--proto-path",
                "tests",
                "../../proto",
            ]
        )
        for fname in [
            "libtypes_test.so",
            "libtypes_test.ini",
        ]:
            p = Path(fname)
            if p.exists():
                p.unlink()
