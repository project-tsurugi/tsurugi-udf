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

    path = sys.argv[1]
    packages = udf_plugin.load_plugin(path)
    json_output = json.dumps(packages, indent=2)
    print(json_output)
