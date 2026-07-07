#!/usr/bin/env python3
"""ruff 기반 린트. `pip install -r requirements-dev.txt` 필요."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ["packages", "apps/api-server/api_server", "apps/worker/worker_jobs", "scripts"]

if __name__ == "__main__":
    try:
        r = subprocess.run([sys.executable, "-m", "ruff", "check", *TARGETS], cwd=ROOT)
    except FileNotFoundError:
        print("[lint] ruff가 설치되어 있지 않습니다. `pip install -r requirements-dev.txt` 후 다시 실행하세요.")
        sys.exit(1)
    sys.exit(r.returncode)
