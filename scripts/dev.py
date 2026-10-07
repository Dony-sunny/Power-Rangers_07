"""Start missing demo services and preserve healthy services already running."""

import json
import os
import sys
import time
import shutil
import socket
import subprocess
import signal
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def running_service(kind, port):
    """Reuse only a healthy Jalayatra service, not any process on the port."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass
    except OSError:
        return False

    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            timeout = min(3, max(0.1, deadline - time.monotonic()))
            if kind == "backend":
                with urllib.request.urlopen(
                    base + "/api/health", timeout=timeout
                ) as response:
                    health = json.loads(response.read(2_000_000))
                timeout = min(3, max(0.1, deadline - time.monotonic()))
                with urllib.request.urlopen(
                    base + "/openapi.json", timeout=timeout
                ) as response:
                    schema = json.loads(response.read(2_000_000))
                healthy = (
                    health.get("status") == "ok"
                    and schema.get("info", {}).get("title") == "Jalayatra AI"
                )
            else:
                with urllib.request.urlopen(base + "/", timeout=timeout) as response:
                    page = response.read(128_000).decode("utf-8")
                healthy = "<title>Jalayatra AI" in page
            if healthy:
                return True
            break  # An unrelated application responded; retrying will not fix it.
        except (OSError, ValueError, AttributeError):
            # Uvicorn's reloader keeps the socket while replacing its worker.
            # Give the application a bounded chance to answer before reporting
            # an occupied, unresponsive port.
            time.sleep(min(0.25, max(0, deadline - time.monotonic())))
    raise RuntimeError(
        f"Port {port} is occupied, but a healthy Jalayatra {kind} could not be verified. "
        "Stop the service using that port in its terminal, then run this launcher again."
    )


def stop_children(children):
    """Only terminate processes created by this launcher."""
    for child in children:
        if child.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                os.killpg(child.pid, signal.SIGTERM)
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()


def main():
    children = []
    try:
        # Check both ports before launching either service; do not leave a partial
        # startup behind when the other port belongs to an unrelated application.
        backend_running = running_service("backend", 8000)
        frontend_running = running_service("frontend", 5173)
        for kind, port, running in [
            ("Backend", 8000, backend_running),
            ("Frontend", 5173, frontend_running),
        ]:
            if running:
                print(
                    f"{kind} already running at http://127.0.0.1:{port}; reusing it.",
                    flush=True,
                )

        if backend_running and frontend_running:
            print("API docs: http://127.0.0.1:8000/docs", flush=True)
            return 0

        python = ROOT / (
            ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
        )
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if (not backend_running and not python.exists()) or (
            not frontend_running
            and (not npm or not (ROOT / "frontend/node_modules").exists())
        ):
            raise RuntimeError(
                "Run scripts/setup.ps1 on Windows or scripts/setup.sh on Linux first."
            )

        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        if not backend_running:
            children.append(
                subprocess.Popen(
                    [
                        str(python),
                        "-m",
                        "uvicorn",
                        "backend.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        "8000",
                        "--reload",
                    ],
                    cwd=ROOT,
                    creationflags=flags,
                    start_new_session=os.name != "nt",
                )
            )
        if not frontend_running:
            children.append(
                subprocess.Popen(
                    [npm, "run", "dev", "--", "--port", "5173", "--strictPort"],
                    cwd=ROOT / "frontend",
                    creationflags=flags,
                    shell=os.name == "nt",
                    start_new_session=os.name != "nt",
                )
            )
        print(
            "Jalayatra AI: http://127.0.0.1:5173\nAPI docs: http://127.0.0.1:8000/docs\n"
            "Ctrl+C stops services started by this launcher; reused services keep running.",
            flush=True,
        )
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        raise RuntimeError("A service stopped; inspect its error above.")
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError) as error:
        print(f"Startup error: {error}", file=sys.stderr, flush=True)
        return 1
    finally:
        stop_children(children)


if __name__ == "__main__":
    sys.exit(main())
