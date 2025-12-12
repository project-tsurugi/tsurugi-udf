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
import os
import sys
import json
from pathlib import Path

from udf_plugin_viewer.descriptors import (
    PackageDescriptor,
    ServiceDescriptor,
    FunctionDescriptor,
    RecordDescriptor,
    ColumnDescriptor,
)
from . import udf_plugin


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <path_to_plugin.so>")
        sys.exit(1)

    path = Path(sys.argv[1]).resolve()
    so_files = []
    if path.is_dir():
        for p in path.iterdir():
            if p.is_file() and p.suffix == ".so":
                so_files.append(str(p.resolve()))
        if not so_files:
            print(f"No .so files found in directory: {path}")
            sys.exit(1)
    elif path.is_file():
        so_files.append(str(path.resolve()))
    else:
        print(f"Error: {path} is neither file nor directory")
        sys.exit(1)
    all_packages = []
    for so in sorted(so_files):
        packages = udf_plugin.load_plugin(so)
        all_packages.extend(packages)
    json_output = json.dumps(all_packages, indent=2)
    print(json_output)
