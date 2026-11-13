"""Fetch official article social images for the dated AI news issue."""

from __future__ import annotations

import html
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


SOURCES = [
    ("openai", "https://openai.com/index/model-misalignment-reporting-framework/"),
    ("microsoft", "https://blogs.microsoft.com/blog/2026/09/17/what-weve-learned-from-microsofts-own-ai-transformation/"),
    ("google", "https://blog.google/innovation-and-ai/technology/ai/google-un-data-commons-platform/"),
    ("aws", "https://aws.amazon.com/blogs/machine-learning/reduce-time-to-hire-for-quality-candidates-with-ai-powered-amazon-connect-talent/"),
    ("nvidia", "https://blogs.nvidia.com/blog/vera-rubin-nvl72-mlperf-inference/"),
]


class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.meta = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "meta" and d.get("property") in {"og:image", "og:image:url"}:
            self.meta.append(d.get("content", ""))
        if tag == "img" and d.get("src"):
            self.images.append((d.get("src"), d.get("alt", "")))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(), response.headers.get("Content-Type", "")


def main():
    for key, page in SOURCES:
        try:
            raw, _ = fetch(page)
        except Exception as exc:
            print(f"{key}: page download failed: {type(exc).__name__}: {exc}", flush=True)
            continue
        parser = ImageParser()
        parser.feed(raw.decode("utf-8", "replace"))
        choices = parser.meta + [url for url, _ in parser.images]
        print(f"{key}: {page}")
        for c in choices[:7]:
            print("  candidate:", urllib.parse.urljoin(page, html.unescape(c)))
        if not choices:
            continue
        url = urllib.parse.urljoin(page, html.unescape(choices[0]))
        try:
            data, mime = fetch(url)
        except Exception as exc:
            print(f"  image download failed: {type(exc).__name__}: {exc}", flush=True)
            continue
        if data.startswith(b"\xff\xd8\xff"):
            ext = ".jpg"
        elif data.startswith(b"\x89PNG"):
            ext = ".png"
        elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            ext = ".webp"
        else:
            print("  unsupported:", mime, data[:12])
            continue
        dest = Path("output/ai-news/2026-09-18") / f"{key}{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print("  saved:", dest, len(data), mime)


if __name__ == "__main__":
    main()
