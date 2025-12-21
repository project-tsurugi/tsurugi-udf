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
import argparse
import json
import sys
from pathlib import Path

from .loader import load_plugins, PluginLoadError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="udf-plugin-viewer",
        description="View metadata of Tsurugi UDF plugin (.so)",
    )
    parser.add_argument(
        "path",
        help="Path to UDF plugin .so file or directory containing .so files",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent (default: 2)",
    )

    args = parser.parse_args(argv)

    try:
        packages = load_plugins(Path(args.path))
    except PluginLoadError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    json.dump(packages, sys.stdout, indent=args.indent)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
