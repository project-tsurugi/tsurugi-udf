from pathlib import Path
import subprocess
from ..errors import CommandFailedError


def build_protoc_cmd(
    *, includes, proto_files, desc_out: Path, gen_dir: Path, grpc_plugin_path: Path
) -> list[str]:
    cmd = ["protoc"]
    for inc in includes:
        cmd.append(f"-I{inc}")
    cmd += [
        "--include_imports",
        f"--descriptor_set_out={desc_out}",
        f"--cpp_out={gen_dir}",
        f"--grpc_out={gen_dir}",
        f"--plugin=protoc-gen-grpc={grpc_plugin_path}",
    ]
    cmd += [str(p) for p in proto_files]
    return cmd


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, text=True, capture_output=True)
    if r.returncode != 0:
        raise CommandFailedError(cmd=cmd, returncode=r.returncode, stderr=r.stderr)
