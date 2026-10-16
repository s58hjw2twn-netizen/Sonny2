"""Run optional Playwright checks against a temporary loopback-only demo server.

Requires Node, Playwright and Chromium already installed. Does not download tools.
"""
import os
import argparse
import tempfile
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', action='store_true', help='Check the authenticated local pilot with disposable sample accounts')
    args = parser.parse_args()
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    temp = tempfile.TemporaryDirectory(prefix='sonny-one-browser-')
    env = dict(os.environ)
    target = ['sonny_one.web_app:app']
    if args.pilot:
        sys.path.insert(0, str(ROOT))
        from sonny_one.pilot_store import PilotStore
        db_path = str(Path(temp.name) / 'pilot.db')
        store = PilotStore(db_path)
        for username in ('alice-demo', 'bob-demo'):
            store.create_user(username, 'public-browser-test-password')
        env.update(SONNY_ONE_DB=db_path, SONNY_ONE_ORIGIN=base,
                   SONNY_ONE_AUTH_SECRET='public-browser-test-key-only-not-a-real-secret')
        target = ['sonny_one.pilot_app:create_app', '--factory']
    server = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', *target,
         '--host', '127.0.0.1', '--port', str(port), '--no-proxy-headers'], cwd=ROOT, env=env,
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
            ['node', 'tests/browser_sonny_one_pilot.cjs' if args.pilot else 'tests/browser_sonny_one.cjs'], cwd=ROOT,
            env={**os.environ, 'SONNY_DEMO_URL': base}, timeout=180).returncode
    finally:
        server.terminate()
        server.wait(timeout=10)
        temp.cleanup()


if __name__ == '__main__':
    sys.exit(main())
