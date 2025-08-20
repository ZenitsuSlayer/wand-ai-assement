from __future__ import annotations
from typing import Any, Dict, Optional
import httpx

class HttpGet:
    name = "http.get"

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    async def run(self, url: str, headers: Optional[Dict[str, str]] = None, **_: Any) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "")
            if "application/json" in ctype:
                return {"status_code": resp.status_code, "json": resp.json(), "headers": dict(resp.headers)}
            return {"status_code": resp.status_code, "text": resp.text, "headers": dict(resp.headers)}
