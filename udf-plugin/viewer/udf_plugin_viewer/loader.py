from pathlib import Path
from typing import List, Union

from . import udf_plugin


class PluginLoadError(RuntimeError):
    pass


def _collect_so_files(path: Path) -> List[Path]:
    if path.is_dir():
        so_files = sorted(p for p in path.iterdir() if p.is_file() and p.suffix == ".so")
        if not so_files:
            raise PluginLoadError(f"No .so files found in directory: {path}")
        return so_files

    if path.is_file():
        return [path]

    raise PluginLoadError(f"Path is neither file nor directory: {path}")


def load_plugins(path: Union[str, Path]) -> list:
    """
    Load UDF plugin shared libraries and return package descriptors.

    :param path: path to .so file or directory containing .so files
    :return: list of package dictionaries
    """
    base = Path(path).expanduser().resolve()
    so_files = _collect_so_files(base)

    all_packages = []
    for so in so_files:
        packages = udf_plugin.load_plugin(str(so))
        all_packages.extend(packages)

    return all_packages

