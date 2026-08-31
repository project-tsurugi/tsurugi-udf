from __future__ import annotations

from google.protobuf.descriptor_pb2 import FileDescriptorSet
import pytest

from tsurugi_udf.builder.cli.args import CliArgs
from tsurugi_udf.builder.core.write_ini import (
    _format_secure,
    write_ini_files_for_rpc_libs,
)


def test_secure_legacy_flag_is_kept() -> None:
    args = CliArgs.from_cli(["--proto", "sample.proto", "--secure"])
    assert args.secure == "true"


def test_secure_default_is_false() -> None:
    args = CliArgs.from_cli(["--proto", "sample.proto"])
    assert args.secure == "false"


def test_secure_accepts_pipe_separated_values() -> None:
    args = CliArgs.from_cli(["--proto", "sample.proto", "--secure", "false|true|false"])
    assert args.secure == "false|true|false"


def test_secure_rejects_invalid_value() -> None:
    with pytest.raises(SystemExit):
        CliArgs.from_cli(["--proto", "sample.proto", "--secure", "false|invalid|true"])


def test_multi_endpoint_options_are_preserved() -> None:
    args = CliArgs.from_cli(
        [
            "--proto",
            "sample.proto",
            "--grpc-endpoint",
            "dns:///udf0:50051|dns:///udf1:50051",
            "--secure",
            "false|true",
            "--grpc-server-endpoint",
            "dns:///tsurugi0:40012|dns:///tsurugi1:40012",
        ]
    )
    assert args.grpc_endpoint == "dns:///udf0:50051|dns:///udf1:50051"
    assert args.secure == "false|true"
    assert (
        args.grpc_server_endpoint
        == "dns:///tsurugi0:40012|dns:///tsurugi1:40012"
    )


def test_removed_tsurugi_endpoint_option_is_rejected() -> None:
    with pytest.raises(SystemExit):
        CliArgs.from_cli(
            [
                "--proto",
                "sample.proto",
                "--tsurugi-endpoint",
                "dns:///tsurugi0:40012|dns:///tsurugi1:40012",
            ]
        )


def test_grpc_server_multi_endpoint_is_written_as_is(tmp_path, monkeypatch) -> None:
    lib_dir = tmp_path / "lib"
    ini_dir = tmp_path / "ini"
    lib_dir.mkdir()
    so_name = "libsample.so"
    (lib_dir / so_name).touch()

    monkeypatch.setattr(
        "tsurugi_udf.builder.core.write_ini.collect_rpc_so_report",
        lambda _: {so_name: object()},
    )

    outputs = write_ini_files_for_rpc_libs(
        FileDescriptorSet(),
        lib_dir=lib_dir,
        ini_dir=ini_dir,
        endpoint="dns:///udf0:50051|dns:///udf1:50051",
        grpc_server_endpoint="dns:///tsurugi0:40012|dns:///tsurugi1:40012",
        transport="stream",
        secure="false|true",
    )
    ini_text = outputs[so_name].read_text(encoding="utf-8")

    assert "endpoint=dns:///udf0:50051|dns:///udf1:50051" in ini_text
    assert "secure=false|true" in ini_text
    assert (
        "[grpc_server]\n"
        "endpoint=dns:///tsurugi0:40012|dns:///tsurugi1:40012"
        in ini_text
    )
    assert "tsurugi_endpoint=" not in ini_text


def test_format_secure_keeps_backward_compatible_bool_input() -> None:
    assert _format_secure(False) == "false"
    assert _format_secure(True) == "true"
    assert _format_secure("false|true") == "false|true"
