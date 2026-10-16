"""Run optional Playwright checks against a temporary loopback-only demo server.

Requires Node, Playwright and Chromium already installed. Does not download tools.
"""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    server = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'sonny_one.web_app:app',
         '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError('Local demo server stopped before checks')
            try:
                with urllib.request.urlopen(base + '/api/status', timeout=1):
                    break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Local demo server did not become ready')
        return subprocess.run(
            ['node', 'tests/browser_sonny_one.cjs'], cwd=ROOT,
            env={**os.environ, 'SONNY_DEMO_URL': base}, timeout=180).returncode
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == '__main__':
    sys.exit(main())
