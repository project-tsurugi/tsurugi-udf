from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tsurugi_udf.builder.cli.main import main

TESTS_DIR = Path(__file__).resolve().parent
DATA_DIR = TESTS_DIR / "data"
CPP_DIR = TESTS_DIR / "cpp"

DLOPEN_CPP = CPP_DIR / "dlopen_udf_plugin.cpp"
GENERIC_CLIENT_CONTEXT_CPP = CPP_DIR / "generic_client_context.cpp"
GENERIC_CLIENT_CONTEXT_H = CPP_DIR / "generic_client_context.h"

# udf-plugin/
UDF_PLUGIN_ROOT = TESTS_DIR.parent
# tsurugi-udf/
REPO_ROOT = UDF_PLUGIN_ROOT.parent
REPO_PROTO_DIR = REPO_ROOT / "proto"


def pkg_config_flags(*packages: str) -> list[str]:
    result = subprocess.run(
        ["pkg-config", "--cflags", "--libs", *packages],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            "pkg-config failed while preparing dlopen checker\n"
            f"packages: {packages}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout.split()


def build_dlopen_checker(tmp_path: Path) -> Path:
    assert DLOPEN_CPP.exists(), f"dlopen checker source not found: {DLOPEN_CPP}"
    assert GENERIC_CLIENT_CONTEXT_CPP.exists(), (
        f"test host generic_client_context.cpp not found: {GENERIC_CLIENT_CONTEXT_CPP}"
    )
    assert GENERIC_CLIENT_CONTEXT_H.exists(), (
        f"test host generic_client_context.h not found: {GENERIC_CLIENT_CONTEXT_H}"
    )

    exe = tmp_path / "dlopen_udf_plugin"

    # Generated plugin entry .so files intentionally expect host-side
    # plugin::udf::generic_client_context symbols.
    #
    # This checker acts as a small host executable:
    #   - links a test-local, jogasaki-free generic_client_context
    #   - exports executable symbols with -rdynamic
    #   - loads generated plugin entry .so files with RTLD_NOW | RTLD_LOCAL
    cmd = [
        "g++",
        "-std=c++17",
        str(DLOPEN_CPP),
        str(GENERIC_CLIENT_CONTEXT_CPP),
        "-I",
        str(CPP_DIR),
        "-o",
        str(exe),
        "-rdynamic",
        "-ldl",
        *pkg_config_flags("protobuf", "grpc++"),
        "-lglog",
    ]

    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, (
        "failed to build dlopen checker\n"
        f"cmd: {' '.join(cmd)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    return exe


def assert_plugins_dlopenable(tmp_path: Path, plugin_sos: list[Path]) -> None:
    # Only plugin entry .so files are direct dlopen targets.
    # deps/lib*_proto.so are implementation dependencies and are verified by
    # file-existence checks, not by direct dlopen here.
    assert plugin_sos, "no plugin entry .so files were passed to dlopen checker"
    assert all(path.parent.name != "deps" for path in plugin_sos)
    assert all(not path.name.endswith("_proto.so") for path in plugin_sos)

    checker = build_dlopen_checker(tmp_path)

    out_dirs = sorted({path.parent for path in plugin_sos})
    ld_paths: list[str] = []
    for out_dir in out_dirs:
        ld_paths.append(str(out_dir))
        ld_paths.append(str(out_dir / "deps"))

    env = dict(os.environ)
    old_ld_library_path = env.get("LD_LIBRARY_PATH")
    env["LD_LIBRARY_PATH"] = ":".join(
        ld_paths + ([old_ld_library_path] if old_ld_library_path else [])
    )

    cmd = [str(checker), *[str(path) for path in plugin_sos]]
    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )

    assert result.returncode == 0, (
        "generated plugin entry .so cannot be loaded by host-style C++ dlopen checker\n"
        f"cmd: {' '.join(cmd)}\n"
        f"plugins:\n"
        + "\n".join(f"  {p}" for p in plugin_sos)
        + "\n"
        f"LD_LIBRARY_PATH={env['LD_LIBRARY_PATH']}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def assert_standard_outputs(
    *,
    proto_name: str,
    out_dir: Path,
    plugin_so: Path,
    proto_so: Path,
    ini_file: Path,
    desc_file: Path,
) -> None:
    root_so_files = sorted(out_dir.glob("lib*.so"))
    deps_so_files = sorted((out_dir / "deps").glob("lib*.so"))
    ini_files = sorted(out_dir.glob("*.ini"))
    desc_files = sorted(out_dir.glob("*.desc.pb"))

    print(f"[{proto_name}] root so files: {root_so_files}")
    print(f"[{proto_name}] deps so files: {deps_so_files}")
    print(f"[{proto_name}] ini files: {ini_files}")
    print(f"[{proto_name}] desc files: {desc_files}")

    assert plugin_so.exists(), f"Plugin .so not generated: {plugin_so}"
    assert proto_so.exists(), f"Proto implementation .so not generated: {proto_so}"
    assert ini_file.exists(), f".ini file not generated: {ini_file}"
    assert desc_file.exists(), f".desc.pb file not generated: {desc_file}"

    assert root_so_files == [plugin_so]
    assert ini_files == [ini_file]
    assert desc_files == [desc_file]

    # deps contains proto implementation .so files for the input proto and
    # may also contain imported proto implementation .so files such as
    # libtsurugi_types_proto.so.
    assert proto_so in deps_so_files
    assert all(file.name.endswith("_proto.so") for file in deps_so_files)
    assert "_proto" not in plugin_so.name


@pytest.mark.parametrize(
    "proto_name",
    [
        "minimal.proto",
        "udf_stream.proto",
        "optional.proto",
        "oneof.proto",
    ],
)
def test_builder_cli_generates_outputs(tmp_path: Path, proto_name: str) -> None:
    proto = DATA_DIR / proto_name
    assert proto.exists(), f"Proto file not found: {proto}"

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

    print(f"[{proto_name}] argv: {argv}")

    try:
        main(argv)
    except SystemExit as e:
        pytest.fail(f"builder cli failed with SystemExit({e.code})")

    plugin_so = out_dir / f"lib{proto.stem}.so"
    proto_so = out_dir / "deps" / f"lib{proto.stem}_proto.so"
    ini_file = out_dir / f"lib{proto.stem}.ini"
    desc_file = out_dir / f"{proto.stem}.desc.pb"

    assert_standard_outputs(
        proto_name=proto_name,
        out_dir=out_dir,
        plugin_so=plugin_so,
        proto_so=proto_so,
        ini_file=ini_file,
        desc_file=desc_file,
    )

    assert_plugins_dlopenable(tmp_path, [plugin_so])


def test_builder_cli_generates_outputs_for_multi_imported_service(tmp_path: Path) -> None:
    proto = DATA_DIR / "multi_c.proto"
    imported_proto = DATA_DIR / "multi_common_service.proto"

    assert proto.exists(), f"Proto file not found: {proto}"
    assert imported_proto.exists(), f"Imported proto file not found: {imported_proto}"

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

    print(f"[multi_c.proto] argv: {argv}")

    try:
        main(argv)
    except SystemExit as e:
        pytest.fail(f"builder cli failed with SystemExit({e.code})")

    expected_root_so_files = sorted(
        [
            out_dir / "libmulti_c.so",
            out_dir / "libmulti_common_service.so",
        ]
    )
    expected_ini_files = sorted(
        [
            out_dir / "libmulti_c.ini",
            out_dir / "libmulti_common_service.ini",
        ]
    )
    expected_desc_files = [out_dir / "multi_c.desc.pb"]
    expected_deps_files = sorted(
        [
            out_dir / "deps" / "libmulti_c_proto.so",
            out_dir / "deps" / "libmulti_common_service_proto.so",
        ]
    )

    root_so_files = sorted(out_dir.glob("lib*.so"))
    deps_so_files = sorted((out_dir / "deps").glob("lib*.so"))
    ini_files = sorted(out_dir.glob("*.ini"))
    desc_files = sorted(out_dir.glob("*.desc.pb"))

    print(f"[multi_c.proto] root so files: {root_so_files}")
    print(f"[multi_c.proto] deps so files: {deps_so_files}")
    print(f"[multi_c.proto] ini files: {ini_files}")
    print(f"[multi_c.proto] desc files: {desc_files}")

    for expected_file in (
        expected_root_so_files
        + expected_ini_files
        + expected_desc_files
        + expected_deps_files
    ):
        assert expected_file.exists(), f"Expected generated file not found: {expected_file}"

    assert root_so_files == expected_root_so_files
    assert deps_so_files == expected_deps_files
    assert ini_files == expected_ini_files
    assert desc_files == expected_desc_files

    assert all("_proto" not in file.name for file in root_so_files)
    assert all(file.name.endswith("_proto.so") for file in deps_so_files)

    assert_plugins_dlopenable(tmp_path, expected_root_so_files)
