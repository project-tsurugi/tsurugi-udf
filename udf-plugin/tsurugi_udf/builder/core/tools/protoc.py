from pathlib import Path
import re
import subprocess

from ..errors import CommandFailedError


def _parse_protoc_version(version_text: str) -> tuple[int, int, int]:
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?$", version_text.strip())
    if not m:
        raise RuntimeError(f"failed to parse protoc version: {version_text!r}")
    major = int(m.group(1))
    minor = int(m.group(2))
    patch = int(m.group(3) or 0)
    return major, minor, patch


def _get_protoc_version(protoc: str = "protoc") -> tuple[int, int, int]:
    r = subprocess.run(
        [protoc, "--version"],
        text=True,
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        raise CommandFailedError(
            cmd=[protoc, "--version"],
            returncode=r.returncode,
            stderr=r.stderr,
        )
    return _parse_protoc_version(r.stdout)


def _proto3_optional_extra_args(protoc: str = "protoc") -> list[str]:
    try:
        major, minor, patch = _get_protoc_version(protoc)
    except Exception as e:
        raise CommandFailedError(
            cmd=[protoc, "--version"],
            returncode=-1,
            stderr=str(e),
        ) from e

    if major < 3 or (major == 3 and minor < 12):
        raise CommandFailedError(
            cmd=[protoc, "--version"],
            returncode=0,
            stderr=f"protoc {major}.{minor}.{patch} does not support proto3 optional",
        )

    if major == 3 and minor < 15:
        return ["--experimental_allow_proto3_optional"]
    return []


def build_protoc_cmd(
    *, includes, proto_files, desc_out: Path, gen_dir: Path, grpc_plugin_path: Path
) -> list[str]:
    protoc = "protoc"
    cmd = [protoc]

    for inc in includes:
        cmd.append(f"-I{inc}")

    cmd += _proto3_optional_extra_args(protoc)

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
