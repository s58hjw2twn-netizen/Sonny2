"""Read-only OAuth provider preflight. No credentials or tokens are required."""
import json
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from sonny.mcp_provider_metadata import validate_provider


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("OAuth metadata redirects are forbidden")


def fetch_provider_metadata(metadata_url, expected_issuer):
    """Fetch bounded HTTPS metadata and verify issuer and required capabilities."""
    expected = urlsplit(expected_issuer)
    parsed = urlsplit(metadata_url)
    if (not isinstance(metadata_url, str) or parsed.scheme != "https"
            or not parsed.hostname or parsed.username or parsed.password
            or parsed.fragment or parsed.query or parsed.hostname != expected.hostname
            or parsed.port != expected.port):
        raise ValueError("Metadata URL must be HTTPS on the exact issuer host and port")
    request = Request(metadata_url, headers={"Accept": "application/json"})
    with build_opener(_NoRedirect()).open(request, timeout=5) as response:
        if response.status != 200:
            raise ValueError("Provider metadata request failed")
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("Provider metadata exceeds size limit")
    metadata = json.loads(raw)
    return validate_provider(metadata, expected_issuer)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        raise SystemExit("Usage: python -m sonny.mcp_provider_preflight ISSUER METADATA_URL")
    try:
        result = fetch_provider_metadata(args[1], args[0])
    except Exception:
        raise SystemExit("OAuth provider preflight failed; verify trusted issuer and metadata")
    print("OAuth provider preflight passed for issuer:", result["issuer"])


if __name__ == "__main__":
    main()
