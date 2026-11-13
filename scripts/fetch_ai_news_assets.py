#!/usr/bin/env python3
"""Download one representative official image for each item in a sources JSON file."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


class ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta" and values.get("content"):
            key = values.get("property") or values.get("name")
            if key in {"og:image", "og:image:url", "twitter:image", "twitter:image:src"}:
                self.candidates.append(values["content"] or "")
        if tag == "img":
            for key in ("src", "data-src", "data-original"):
                if values.get(key):
                    self.candidates.append(values[key] or "")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
            "Accept": "text/html,image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        return response.read()


def image_from_page(page_url: str) -> tuple[bytes, str, str]:
    parser = ImageParser()
    parser.feed(fetch(page_url).decode("utf-8", "replace"))
    seen: set[str] = set()
    for candidate in parser.candidates:
        image_url = urllib.parse.urljoin(page_url, html.unescape(candidate))
        if not image_url.startswith(("http://", "https://")) or image_url in seen:
            continue
        seen.add(image_url)
        try:
            data = fetch(image_url)
            if data.startswith(b"\xff\xd8\xff"):
                return data, ".jpg", image_url
            if data.startswith(b"\x89PNG"):
                return data, ".png", image_url
            if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
                return data, ".webp", image_url
        except Exception:
            continue
    raise RuntimeError(f"No suitable image found: {page_url}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", type=Path)
    args = parser.parse_args()
    out_dir = args.sources.parent
    sources = json.loads(args.sources.read_text(encoding="utf-8"))
    downloaded: list[dict[str, str]] = []
    for index, source in enumerate(sources, 1):
        data, ext, image_url = image_from_page(source["url"])
        path = out_dir / f"{index:02d}-{source['key']}{ext}"
        path.write_bytes(data)
        downloaded.append({"key": source["key"], "path": str(path), "image_url": image_url})
        print(f"{source['key']}: {path} ({len(data)} bytes)")
    historical_cover_hashes: set[str] = set()
    history_root = out_dir.parent
    for old_cover in history_root.glob("*/cover.*"):
        if old_cover.parent == out_dir:
            continue
        historical_cover_hashes.add(hashlib.sha256(old_cover.read_bytes()).hexdigest())
    cover_source = Path(downloaded[0]["path"])
    for candidate in downloaded:
        candidate_path = Path(candidate["path"])
        digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        if digest not in historical_cover_hashes:
            cover_source = candidate_path
            break
    cover_path = out_dir / ("cover" + cover_source.suffix)
    cover_path.write_bytes(cover_source.read_bytes())
    print(f"cover source: {cover_source}")
    (out_dir / "image-sources.json").write_text(
        json.dumps(downloaded, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"cover: {cover_path}")


if __name__ == "__main__":
    main()
