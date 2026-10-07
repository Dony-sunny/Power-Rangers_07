"""Launcher regression checks without opening ports or starting child processes."""

import io
import json
import os
import runpy
import shutil
import socket
import subprocess
import time
import urllib.request
from contextlib import nullcontext
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def launcher(monkeypatch):
    started = []
    stopped = []
    occupied = {8000, 5173}
    unrelated = set()

    def connect(address, timeout=None):
        if address[1] not in occupied:
            raise ConnectionRefusedError()
        return nullcontext()

    def read_url(url, timeout=None):
        port = 8000 if ":8000/" in url else 5173
        if port in unrelated:
            return io.BytesIO(b'{"status":"ok","info":{"title":"Another app"}}')
        if url.endswith("/api/health"):
            return io.BytesIO(json.dumps({"status": "ok"}).encode())
        if url.endswith("/openapi.json"):
            return io.BytesIO(
                json.dumps({"info": {"title": "Jalayatra AI"}}).encode()
            )
        return io.BytesIO(
            b"<html><title>Jalayatra AI \xc2\xb7 Freight workspace</title></html>"
        )

    class Child:
        def __init__(self, command, **kwargs):
            self.pid = 20000 + len(started)
            started.append((self.pid, command))

        def poll(self):
            return None

        def wait(self, timeout=None):
            return 0

        def kill(self):
            stopped.append(self.pid)

    def interrupt(_):
        raise KeyboardInterrupt()

    original_exists = Path.exists

    def exists(path):
        if path.name in {"python", "python.exe", "node_modules"}:
            return True
        return original_exists(path)

    monkeypatch.setattr(socket, "create_connection", connect)
    monkeypatch.setattr(urllib.request, "urlopen", read_url)
    monkeypatch.setattr(shutil, "which", lambda _: "npm.cmd")
    monkeypatch.setattr(subprocess, "Popen", Child)
    monkeypatch.setattr(
        subprocess, "run", lambda command, **kwargs: stopped.append(command)
    )
    if hasattr(os, "killpg"):
        monkeypatch.setattr(os, "killpg", lambda pid, _: stopped.append(pid))
    monkeypatch.setattr(time, "sleep", interrupt)
    monkeypatch.setattr(Path, "exists", exists)

    def run():
        try:
            runpy.run_path(str(ROOT / "scripts/dev.py"), run_name="__main__")
        except SystemExit as result:
            return result.code
        return 0

    return run, started, stopped, occupied, unrelated


def test_existing_services_are_reused_without_duplicate_processes(launcher, capsys):
    run, started, stopped, _, _ = launcher
    assert run() == 0
    assert started == []
    assert stopped == []
    output = capsys.readouterr().out
    assert "already running" in output.lower()
    assert "8000" in output and "5173" in output


def test_unrelated_backend_blocks_startup_before_launching_children(launcher, capsys):
    run, started, _, _, unrelated = launcher
    unrelated.add(8000)
    assert run() == 1
    assert started == []
    assert "8000" in capsys.readouterr().err


def test_unrelated_frontend_does_not_leave_a_new_backend_running(launcher, capsys):
    run, started, _, occupied, unrelated = launcher
    occupied.remove(8000)
    unrelated.add(5173)
    assert run() == 1
    assert started == []
    assert "5173" in capsys.readouterr().err


def test_existing_frontend_is_preserved_when_new_backend_is_stopped(launcher):
    run, started, stopped, occupied, _ = launcher
    occupied.remove(8000)
    assert run() == 0
    assert len(started) == 1
    pid, command = started[0]
    assert "uvicorn" in command
    if os.name == "nt":
        assert any(isinstance(item, list) and str(pid) in item for item in stopped)
    else:
        assert stopped == [pid]


def test_reloading_backend_is_reused_after_health_recovers(launcher, monkeypatch):
    run, started, _, _, _ = launcher
    ready_response = urllib.request.urlopen
    health_attempts = []

    def recovering_response(url, timeout=None):
        if url.endswith("/api/health"):
            health_attempts.append(url)
            if len(health_attempts) == 1:
                raise TimeoutError("Application reload in progress")
        return ready_response(url, timeout=timeout)

    monkeypatch.setattr(urllib.request, "urlopen", recovering_response)
    monkeypatch.setattr(time, "sleep", lambda _: None)
    assert run() == 0
    assert started == []
    assert len(health_attempts) == 2
