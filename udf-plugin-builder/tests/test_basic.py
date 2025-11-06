import tempfile
from udf_plugin_builder import build_with_cmake

def test_help_command():
    with tempfile.TemporaryDirectory() as tmp_dir:
        build_with_cmake.main()
        assert True  # if no exception, test passes

