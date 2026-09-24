from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


TESTS_DIR = Path(__file__).resolve().parent
UDF_PLUGIN_ROOT = TESTS_DIR.parent
INCLUDE_DIR = UDF_PLUGIN_ROOT / "tsurugi_udf/common/tsurugi_udf_common/include/udf"
SRC_DIR = UDF_PLUGIN_ROOT / "tsurugi_udf/common/tsurugi_udf_common/src/udf"


def pkg_config_flags(*packages: str) -> list[str]:
    try:
        result = subprocess.run(
            ["pkg-config", "--cflags", "--libs", *packages],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("pkg-config is required to build the C++ stream test.")

    if result.returncode != 0:
        pytest.fail(
            "pkg-config failed while preparing C++ stream test\n"
            f"packages: {packages}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout.split()


def test_stream_close_callback_runs_once_and_waits_for_worker(tmp_path: Path) -> None:
    source = tmp_path / "stream_close_callback.cpp"
    source.write_text(
        r'''
#include "generic_record_impl.h"

#include <atomic>
#include <chrono>
#include <future>
#include <thread>

int main() {
    plugin::udf::generic_record_stream_impl stream;
    auto state = stream.shared_state();
    if(!state) { return 1; }

    std::atomic<int> close_count{0};
    std::promise<void> close_started;
    state->set_on_close([&close_count, &close_started] {
        close_count.fetch_add(1);
        close_started.set_value();
    });

    std::promise<void> worker_started;
    std::promise<void> allow_worker_finish;
    auto allow_worker_finish_future = allow_worker_finish.get_future();
    state->set_worker(std::thread(
        [&worker_started, allow_worker_finish_future = std::move(allow_worker_finish_future)]() mutable {
            worker_started.set_value();
            allow_worker_finish_future.wait();
        }
    ));
    if(worker_started.get_future().wait_for(std::chrono::seconds{1}) != std::future_status::ready) { return 2; }

    std::promise<void> close_returned;
    auto close_returned_future = close_returned.get_future();
    std::thread closer([&stream, &close_returned] {
        stream.close();
        close_returned.set_value();
    });

    if(close_started.get_future().wait_for(std::chrono::seconds{1}) != std::future_status::ready) {
        allow_worker_finish.set_value();
        closer.join();
        return 3;
    }
    if(close_returned_future.wait_for(std::chrono::milliseconds{0}) == std::future_status::ready) {
        allow_worker_finish.set_value();
        closer.join();
        return 4;
    }

    allow_worker_finish.set_value();
    if(close_returned_future.wait_for(std::chrono::seconds{1}) != std::future_status::ready) {
        closer.join();
        return 5;
    }
    closer.join();
    stream.close();

    if(close_count.load() != 1) { return 6; }

    plugin::udf::generic_record_impl record;
    auto status = stream.next(record, std::chrono::milliseconds{0});
    if(status != plugin::udf::generic_record_stream::status_type::end_of_stream) { return 7; }

    return 0;
}
''',
        encoding="utf-8",
    )

    exe = tmp_path / "stream_close_callback"
    cmd = [
        os.environ.get("CXX", "g++"),
        "-std=c++17",
        str(source),
        str(SRC_DIR / "generic_record_impl.cpp"),
        str(SRC_DIR / "error_info.cpp"),
        "-I",
        str(INCLUDE_DIR),
        "-pthread",
        "-o",
        str(exe),
        *pkg_config_flags("grpc++"),
    ]
    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, (
        "failed to build C++ stream test\n"
        f"cmd: {' '.join(cmd)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    result = subprocess.run(
        [str(exe)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=5,
    )
    assert result.returncode == 0, (
        "C++ stream close callback test failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
