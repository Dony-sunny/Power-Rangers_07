"""Start both local demo services; terminate children when this process exits."""

import os
import sys
import time
import shutil
import subprocess
import signal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
python = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
if not python.exists() or not npm or not (ROOT / "frontend/node_modules").exists():
    sys.exit("Run scripts/setup.ps1 on Windows or scripts/setup.sh on Linux first.")
children = []
try:
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
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
            ],
            cwd=ROOT,
            creationflags=flags,
            start_new_session=os.name != "nt",
        )
    )
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
        "Jalayatra AI: http://127.0.0.1:5173\nAPI docs: http://127.0.0.1:8000/docs\nCtrl+C stops both services.",
        flush=True,
    )
    while all(child.poll() is None for child in children):
        time.sleep(0.5)
    raise RuntimeError(
        "A service stopped; inspect the error above. Check whether ports 8000/5173 are already in use."
    )
except KeyboardInterrupt:
    pass
finally:
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
