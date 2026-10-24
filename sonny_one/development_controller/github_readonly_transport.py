"""Read-only GitHub REST transport for development evidence verification.

Only fixed GitHub API URLs under the configured repository are permitted.
No credentials, writes, shell commands, or arbitrary URL fetching.
"""
from __future__ import annotations

import json
import re
from urllib.request import HTTPRedirectHandler, Request, build_opener

_REPO = "s58hjw2twn-netizen/Sonny2"
_BASE = "https://api.github.com/repos/" + _REPO
_COMMIT = re.compile(r"^/commits/[0-9a-f]{40}$")
_RUN = re.compile(r"^/actions/runs/[1-9][0-9]{0,19}$")
_BRANCH = "/branches/research/apl-001"


def github_readonly_json(url: str, *, timeout: int = 10) -> dict:
    if type(url) is not str or not url.startswith(_BASE + "/"):
        raise ValueError("GitHub URL is outside allowed repository")
    suffix = url[len(_BASE):]
    if not (_COMMIT.fullmatch(suffix) or _RUN.fullmatch(suffix) or suffix == _BRANCH):
        raise ValueError("GitHub endpoint is not allowlisted")
    if type(timeout) is not int or not 1 <= timeout <= 20:
        raise ValueError("invalid timeout")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sonny-ONE-Research-Receipt-Reader",
    }, method="GET")
    # Fail closed on redirects, including redirects to private networks.
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError("GitHub API redirect not allowed")

    with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
        raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("GitHub response exceeds size limit")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("GitHub response must be an object")
    return value
