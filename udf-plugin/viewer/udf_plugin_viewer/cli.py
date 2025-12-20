# udf_plugin_viewer/cli.py
# Copyright 2018-2025 Project Tsurugi.

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

