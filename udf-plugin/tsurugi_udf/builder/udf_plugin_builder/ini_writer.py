#!/usr/bin/env python3
from pathlib import Path
from .utils import log_ok


def generate_ini_file(
    plugin_name: str, grpc_endpoint: str, grpc_transport: str, out_dir: str
):
    """Generate .ini file for plugin"""
    ini_path = Path(out_dir) / f"lib{plugin_name}.ini"
    ini_path.parent.mkdir(parents=True, exist_ok=True)

    with open(ini_path, "w") as f:
        f.write("[udf]\n")
        f.write(f"enabled=true\n")
        f.write(f"endpoint={grpc_endpoint}\n")
        f.write("secure=false\n")
        f.write(f"transport={grpc_transport}\n")

    log_ok(f"Generated ini file: {ini_path}")
    return ini_path
