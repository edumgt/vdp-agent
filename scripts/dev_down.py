#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

compose = Path(__file__).resolve().parent.parent / "infra" / "docker" / "docker-compose.yml"
r = subprocess.run(["docker", "compose", "-f", str(compose), "down"])
sys.exit(r.returncode)
