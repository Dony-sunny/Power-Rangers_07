#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
(cd frontend && npm ci)
.venv/bin/python -m data.seed.network
.venv/bin/python scripts/make_demo_documents.py
echo 'Ready. Run: python3 scripts/dev.py'
