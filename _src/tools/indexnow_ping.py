"""Send all Travel Finds sitemap URLs to IndexNow (Bing/Yandex/Seznam).

The key is public and lives both in the source tree and at
https://nonamemac-cyber.github.io/travel-finds/<key>.txt after deployment.
Set DRY_RUN=1 to print the payload without network calls.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = (ROOT / "site" / "indexnow-key.txt").read_text(encoding="utf-8").strip()
SITEMAP = ROOT.parent / "sitemap.xml"
HOST = "nonamemac-cyber.github.io"
SITE_PATH = "/travel-finds"
PREFIX = f"https://{HOST}{SITE_PATH}/"
KEY_URL = PREFIX + KEY + ".txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
USER_AGENT = "travel-finds-indexnow/1.0"


def sitemap_urls() -> list[str]:
    text = SITEMAP.read_text(encoding="utf-8")
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)
    return list(dict.fromkeys(url for url in urls if url.startswith(PREFIX)))


def url_ready(url: str, timeout: float = 20.0) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= int(getattr(response, "status", 0) or 0) < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_ready(url: str, attempts: int = 24, delay: float = 10.0) -> bool:
    for attempt in range(attempts):
        if url_ready(url):
            return True
        if attempt + 1 < attempts:
            print(f"waiting for {url} ({attempt + 1}/{attempts})")
            time.sleep(delay)
    return False


def main() -> int:
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", KEY):
        print("invalid IndexNow key")
        return 2
    urls = sitemap_urls()
    if not urls:
        print(f"no URLs under {PREFIX}")
        return 1
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_URL,
        "urlList": urls,
    }
    if os.environ.get("DRY_RUN") == "1":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if not wait_ready(KEY_URL):
        print(f"key file not reachable: {KEY_URL}")
        return 1
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = int(getattr(response, "status", 0) or 0)
            response.read(300)
    except urllib.error.HTTPError as error:
        print(f"IndexNow HTTP {error.code}: {error.read(300).decode('utf-8', 'replace')}")
        return 1
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print(f"IndexNow unavailable: {type(error).__name__}: {error}")
        return 1
    print(f"IndexNow HTTP {status} | urls: {len(urls)}")
    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(main())
