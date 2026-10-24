"""Read-only GitHub REST transport for development evidence verification.

Only fixed GitHub API URLs under the configured repository are permitted.
No credentials, writes, shell commands, or arbitrary URL fetching.
"""
from __future__ import annotations

import json
import re
from urllib.request import Request, urlopen

_REPO = "s58hjw2twn-netizen/Sonny2"
_BASE = "https://api.github.com/repos/" + _REPO
_COMMIT = re.compile(r"^/commits/[0-9a-f]{40}$")
_RUN = re.compile(r"^/actions/runs/[1-9][0-9]{0,19}$")


def github_readonly_json(url: str, *, timeout: int = 10) -> dict:
    if type(url) is not str or not url.startswith(_BASE + "/"):
        raise ValueError("GitHub URL is outside allowed repository")
    suffix = url[len(_BASE):]
    if not (_COMMIT.fullmatch(suffix) or _RUN.fullmatch(suffix)):
        raise ValueError("GitHub endpoint is not allowlisted")
    if type(timeout) is not int or not 1 <= timeout <= 20:
        raise ValueError("invalid timeout")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sonny-ONE-Research-Receipt-Reader",
    }, method="GET")
    # GitHub redirects are not expected for these API endpoints. The default
    # opener may follow redirects; never trust redirected response origins.
    from urllib.parse import urlsplit
    with urlopen(request, timeout=timeout) as response:
        if urlsplit(response.geturl()).netloc != "api.github.com":
            raise ValueError("redirected outside GitHub API")
        raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("GitHub response exceeds size limit")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("GitHub response must be an object")
    return value
