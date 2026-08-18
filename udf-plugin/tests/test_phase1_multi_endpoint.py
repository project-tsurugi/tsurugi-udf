from __future__ import annotations

import pytest

from tsurugi_udf.builder.cli.args import CliArgs
from tsurugi_udf.builder.core.write_ini import (
    _format_secure,
    _resolve_tsurugi_endpoints,
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
            "--tsurugi-endpoint",
            "dns:///tsurugi0:40012|dns:///tsurugi1:40012",
        ]
    )
    assert args.grpc_endpoint == "dns:///udf0:50051|dns:///udf1:50051"
    assert args.secure == "false|true"
    assert args.tsurugi_endpoint == "dns:///tsurugi0:40012|dns:///tsurugi1:40012"


def test_legacy_endpoint_is_copied_to_new_setting() -> None:
    new_endpoint, legacy_endpoint = _resolve_tsurugi_endpoints(
        grpc_server_endpoint="dns:///tsurugi:40012",
        tsurugi_endpoint=None,
    )
    assert new_endpoint == "dns:///tsurugi:40012"
    assert legacy_endpoint == "dns:///tsurugi:40012"


def test_new_multi_endpoint_uses_first_value_for_legacy_setting() -> None:
    new_endpoint, legacy_endpoint = _resolve_tsurugi_endpoints(
        grpc_server_endpoint=None,
        tsurugi_endpoint="dns:///tsurugi0:40012|dns:///tsurugi1:40012",
    )
    assert new_endpoint == "dns:///tsurugi0:40012|dns:///tsurugi1:40012"
    assert legacy_endpoint == "dns:///tsurugi0:40012"


def test_explicit_legacy_and_new_endpoints_are_kept_separately() -> None:
    new_endpoint, legacy_endpoint = _resolve_tsurugi_endpoints(
        grpc_server_endpoint="dns:///legacy:40012",
        tsurugi_endpoint="dns:///tsurugi0:40012|dns:///tsurugi1:40012",
    )
    assert new_endpoint == "dns:///tsurugi0:40012|dns:///tsurugi1:40012"
    assert legacy_endpoint == "dns:///legacy:40012"


def test_format_secure_keeps_backward_compatible_bool_input() -> None:
    assert _format_secure(False) == "false"
    assert _format_secure(True) == "true"
    assert _format_secure("false|true") == "false|true"
