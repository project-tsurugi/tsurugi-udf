# Copyright 2018-2025 Project Tsurugi.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pathlib import Path
from typing import List, Union

from . import _udf_plugin


class PluginLoadError(RuntimeError):
    pass


def _collect_so_files(path: Path) -> List[Path]:
    """
    Collect .so files from a given path.

    :param path: Path to a .so file or a directory containing .so files
    :return: List of .so file paths
    :raises PluginLoadError: if the path does not exist,
                             is not a file or directory,
                             or a directory contains no .so files
    """
    if not path.exists():
        raise PluginLoadError(f"Path does not exist: {path}")
    if path.is_dir():
        so_files = sorted(
            p for p in path.iterdir() if p.is_file() and p.suffix == ".so"
        )
        if not so_files:
            raise PluginLoadError(f"No .so files found in directory: {path}")
        return so_files

    if path.is_file():
        if path.suffix != ".so":
            raise PluginLoadError(f"File is not a .so file: {path}")
        return [path]

    raise PluginLoadError(f"Path is neither file nor directory: {path}")


def load_plugins(path: Union[str, Path]) -> list:
    """
    Load UDF plugin shared libraries and return package descriptors.

    This function supports loading a single `.so` file or all `.so` files
    in a directory. The returned list contains package dictionaries
    describing the loaded plugins.

    :param path: Path to a `.so` file or a directory containing `.so` files.
    :return: List of package dictionaries.
    :raises PluginLoadError: Raised in the following cases:
        - The path does not exist.
        - The path is neither a file nor a directory.
        - The file is not a `.so` file.
        - A directory contains no `.so` files.
        - The C++ binding fails to load the plugin.
    """
    base = Path(path).expanduser().resolve()
    so_files = _collect_so_files(base)

    all_packages = []
    for so in so_files:
        try:
            packages = _udf_plugin.load_plugin(str(so))
        except Exception as exc:
            raise PluginLoadError(f"Failed to load plugin '{so}': {exc}") from exc
        all_packages.extend(packages)
    return all_packages
