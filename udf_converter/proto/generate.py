#!/usr/bin/env python3
import hashlib
import shutil
from pathlib import Path
import subprocess
import sys

SRC_PROTO = Path("tsurugi_types.proto")
OUT_DIR = Path("../udf_converter")


def main():
    if not SRC_PROTO.exists():
        print(f"ERROR: {SRC_PROTO} not found", file=sys.stderr)
        sys.exit(1)

    digest = hashlib.sha256(SRC_PROTO.read_bytes()).hexdigest()[:32]

    gen_name = f"tsurugi_types_{digest}.proto"
    gen_path = OUT_DIR / gen_name

    shutil.copy2(SRC_PROTO, gen_path)

    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        "-I",
        str(OUT_DIR),
        f"--python_out={OUT_DIR}",
        str(gen_path),
    ]

    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

    print(f"Generated: {gen_path}")


if __name__ == "__main__":
    main()
