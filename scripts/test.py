#!/usr/bin/env python3
"""전체 패키지/앱 테스트 실행. 사전에 `pip install -r requirements.txt`가 필요합니다."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_DIRS = [
    "packages/shared/test",
    "packages/pdf_engine/test",
    "packages/accounting_engine/test",
    "packages/ml_pipeline/test",
    "packages/dart_integration/test",
    "packages/accounting_data/test",
]

if __name__ == "__main__":
    r = subprocess.run([sys.executable, "-m", "pytest", *TEST_DIRS, "-v"], cwd=ROOT)
    sys.exit(r.returncode)
