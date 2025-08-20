from __future__ import annotations
from typing import Any, Dict, List

class JsonPick:
    """
    Simple jq-like extractor:
      - supports dot.notation keys
      - supports list indexes like items[0].name
    """
    name = "json.pick"

    def __init__(self) -> None:
        ...

    def _get_path(self, data: Any, path: str) -> Any:
        cur = data
        parts = path.split(".") if path else []
        for part in parts:
            if "[" in part and part.endswith("]"):
                key, idx = part[:-1].split("[")
                if key:
                    cur = cur.get(key)
                cur = cur[int(idx)]
            else:
                if isinstance(cur, list):
                    cur = cur[int(part)]
                else:
                    cur = cur.get(part)
        return cur

    async def run(self, data: Any, paths: List[str]) -> Dict[str, Any]:
        out = {}
        for p in paths:
            out[p] = self._get_path(data, p)
        return {"picked": out}
