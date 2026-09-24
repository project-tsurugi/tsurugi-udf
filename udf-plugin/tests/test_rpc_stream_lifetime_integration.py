from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from test_builder_viewer_e2e import (
    CPP_DIR,
    DATA_DIR,
    GENERIC_CLIENT_CONTEXT_CPP,
    REPO_PROTO_DIR,
    UDF_PLUGIN_ROOT,
    make_runtime_env,
    pkg_config_flags,
)
from tsurugi_udf.builder.cli.main import main


RPC_STREAM_LIFETIME_CPP = CPP_DIR / "rpc_stream_lifetime.cpp"
COMMON_INCLUDE_DIR = UDF_PLUGIN_ROOT / "tsurugi_udf/common/tsurugi_udf_common/include/udf"
COMMON_SRC_DIR = UDF_PLUGIN_ROOT / "tsurugi_udf/common/tsurugi_udf_common/src/udf"


def build_rpc_stream_lifetime_checker(
    *,
    tmp_path: Path,
    build_dir: Path,
    proto_so: Path,
) -> Path:
    exe = tmp_path / "rpc_stream_lifetime"
    cmd = [
        os.environ.get("CXX", "g++"),
        "-std=c++17",
        str(RPC_STREAM_LIFETIME_CPP),
        str(GENERIC_CLIENT_CONTEXT_CPP),
        str(COMMON_SRC_DIR / "generic_record_impl.cpp"),
        str(COMMON_SRC_DIR / "error_info.cpp"),
        "-I",
        str(CPP_DIR),
        "-I",
        str(COMMON_INCLUDE_DIR),
        "-I",
        str(build_dir / "gen"),
        "-pthread",
        "-o",
        str(exe),
        "-rdynamic",
        "-ldl",
        str(proto_so),
        *pkg_config_flags("protobuf", "grpc++"),
    ]
    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, (
        "failed to build RPC stream lifetime integration checker\n"
        f"cmd: {' '.join(cmd)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    return exe


def test_server_streaming_rpc_worker_cancels_when_stream_is_destroyed(
    tmp_path: Path,
) -> None:
    proto = DATA_DIR / "udf_stream.proto"
    build_dir = tmp_path / "build"
    out_dir = tmp_path / "out"

    argv = [
        "--proto",
        str(proto),
        "-I",
        str(DATA_DIR),
        "-I",
        str(REPO_PROTO_DIR),
        "--grpc-endpoint",
        "dns:///localhost:40005",
        "--build-dir",
        str(build_dir),
        "--output-dir",
        str(out_dir),
        "--clean",
        "--debug",
    ]

    try:
        main(argv)
    except SystemExit as e:
        pytest.fail(f"builder cli failed with SystemExit({e.code})")

    plugin_so = out_dir / "libudf_stream.so"
    proto_so = out_dir / "deps" / "libudf_stream_proto.so"
    assert plugin_so.exists(), f"Plugin .so not generated: {plugin_so}"
    assert proto_so.exists(), f"Proto implementation .so not generated: {proto_so}"

    checker = build_rpc_stream_lifetime_checker(
        tmp_path=tmp_path,
        build_dir=build_dir,
        proto_so=proto_so,
    )
    env = make_runtime_env([plugin_so])

    try:
        result = subprocess.run(
            [str(checker), str(plugin_so)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
            timeout=15,
        )
    except subprocess.TimeoutExpired as e:
        pytest.fail(
            "RPC stream lifetime integration checker timed out\n"
            f"stdout:\n{e.stdout or ''}\n"
            f"stderr:\n{e.stderr or ''}"
        )

    assert result.returncode == 0, (
        "RPC stream lifetime integration checker failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
