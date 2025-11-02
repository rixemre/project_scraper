from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from typing import Dict, Any
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://bannerlord.fandom.com/api.php"
HEADERS = {
    "User-Agent": "BannerlordScraper/1.0 (+educational use; contact: example@example.com)"
}

def _cache_path(params: Dict[str, Any]) -> Path:
    """Create a stable cache filename for the given params."""
    key = hashlib.md5(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()
    return RAW / f"{key}.json"

def get_json(params: Dict[str, Any], sleep: float = 0.6) -> Dict[str, Any]:
    """
    Call MediaWiki API with caching. Returns JSON dict.
    Adds format=json automatically. Respects simple rate limit with sleep.
    """
    params = dict(params)
    params.setdefault("format", "json")

    pth = _cache_path(params)
    if pth.exists():
        return json.loads(pth.read_text(encoding="utf-8"))

    # polite delay
    if sleep:
        time.sleep(sleep)

    r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    pth.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data

def get_page_html(title: str) -> str:
    """
    Fetch page HTML using action=parse.
    Returns raw HTML string of the page body.
    """
    data = get_json({
        "action": "parse",
        "page": title,
        "prop": "text",
        "redirects": True
    })
    return data["parse"]["text"]["*"]
