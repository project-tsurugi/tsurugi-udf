import tempfile
from udf_plugin_builder import build_with_cmake


def test_basic_build():
    with tempfile.TemporaryDirectory() as tmp_dir:
        build_with_cmake.run(
            [
                "--name",
                "plugin_api_test",
                "--proto-file",
                "proto/sample.proto",
                "proto/complex_types.proto",
                "proto/primitive_types.proto",
            ]
        )
        assert True
