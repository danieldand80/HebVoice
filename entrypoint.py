#!/usr/bin/env python
import os
import subprocess
import sys

if __name__ == "__main__":
    port = os.getenv("PORT", "8000")
    cmd = [
        "uvicorn",
        "backend.main:app",
        "--host", "0.0.0.0",
        "--port", port
    ]
    print(f"Starting server on port {port}...")
    sys.exit(subprocess.call(cmd))

