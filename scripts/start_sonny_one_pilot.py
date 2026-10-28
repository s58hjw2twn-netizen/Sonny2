"""Start the local Sonny ONE test pilot. No public hosting or model API calls."""
import argparse
import getpass
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_or_create_config(directory):
    """Create a private local key once; never print it or replace an existing key."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / 'config.json'
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as target:
            json.dump({'signing_key': secrets.token_urlsafe(48)}, target)
    try:
        config = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(config.get('signing_key'), str) or len(config['signing_key']) < 32:
            raise ValueError('Invalid local signing configuration')
        return config
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Local configuration is invalid; it was not overwritten') from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a local port from 1024 to 65535')
    try:
        from sonny_one.pilot_store import PilotStore
        config = load_or_create_config(ROOT / 'local_state')
        store = PilotStore(ROOT / 'local_state' / 'pilot.db')
    except (ImportError, ValueError) as exc:
        parser.error(str(exc))
    with store.connect() as db:
        has_accounts = db.execute('SELECT count(*) FROM accounts').fetchone()[0] > 0
    if not has_accounts:
        print('Create one local test account. Use invented credentials and sample data.')
        username = input('Test username (default local-demo): ').strip() or 'local-demo'
        password = getpass.getpass('Password (12–128 characters): ')
        if password != getpass.getpass('Confirm password: '):
            parser.error('Passwords did not match')
        try:
            store.create_user(username, password)
        except ValueError as exc:
            parser.error(str(exc))
    base = f'http://127.0.0.1:{args.port}'
    env = {**os.environ, 'SONNY_ONE_DB': store.path, 'SONNY_ONE_ORIGIN': base,
           'SONNY_ONE_AUTH_SECRET': config['signing_key']}
    server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'sonny_one.pilot_app:create_app',
                               '--factory', '--host', '127.0.0.1', '--port', str(args.port),
                               '--no-proxy-headers'], cwd=ROOT, env=env)
    try:
        for _ in range(100):
            if server.poll() is not None:
                return server.returncode or 1
            try:
                with urllib.request.urlopen(base+'/api/status', timeout=1):
                    break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Local server did not become ready')
        print(f'Sonny ONE local test pilot: {base}\nKeep this window open. Press Ctrl+C to stop.')
        if not args.no_browser:
            webbrowser.open(base)
        return server.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    sys.exit(main())
