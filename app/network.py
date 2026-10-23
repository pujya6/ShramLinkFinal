"""Small HTTP boundary: fixed provider URLs, bounded responses, no redirects."""

import json
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, *, payload=None, headers=None, timeout=6, max_bytes=2_000_000):
    body = (
        json.dumps(payload, ensure_ascii=False).encode()
        if payload is not None
        else None
    )
    request = Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "User-Agent": "ShramLink-demo/3",
            **(headers or {}),
        },
        method="POST" if body is not None else "GET",
    )
    with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError("Provider response exceeds size limit.")
        return json.loads(raw)
