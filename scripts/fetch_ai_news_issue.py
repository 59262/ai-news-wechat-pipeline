"""Fetch official images for one dated AI news issue."""
from __future__ import annotations
import argparse, html, mimetypes, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path
import shutil

SOURCES = [
    ("openai", "https://openai.com/index/gpt-6-for-everyone/", ""),
    ("anthropic", "https://www.anthropic.com/claude-haiku-5-5", ""),
    ("microsoft", "https://news.microsoft.com/source/emea/2026/10/building-windows-for-hybrid-intelligence/", ""),
    ("nvidia", "https://nvidianews.nvidia.com/news/nvidia-commits-1-billion-to-advance-genomics-drug-discovery-and-healthcare", ""),
    ("aws", "https://aws.amazon.com/blogs/machine-learning/pay-per-inference-for-ai-agents-how-blockrun-and-incarna-use-amazon-bedrock-agentcore-payments/", ""),
]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.images=[]; self.meta=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag == 'meta' and d.get('property') in {'og:image','og:image:url','twitter:image'} and d.get('content'): self.meta.append(d['content'])
        if tag == 'img' and d.get('src'): self.images.append(d['src'])

def get(url):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r: return r.read(), r.headers.get('Content-Type','')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('date'); ns=ap.parse_args(); out=Path('output/ai-news')/ns.date; out.mkdir(parents=True, exist_ok=True)
    chosen=[]
    for key,page,fallback in SOURCES:
        candidates=[]
        try:
            raw,_=get(page); p=Parser(); p.feed(raw.decode('utf-8','replace')); candidates=p.meta+p.images
        except Exception as exc: print(key,'page failed',type(exc).__name__,exc)
        if fallback: candidates.insert(0,fallback)
        saved=False
        for rawurl in candidates[:12]:
            url=urllib.parse.urljoin(page, html.unescape(rawurl))
            try:
                data,mime=get(url)
                if data.startswith(b'\xff\xd8\xff'): ext='.jpg'
                elif data.startswith(b'\x89PNG'): ext='.png'
                elif data.startswith(b'RIFF') and data[8:12]==b'WEBP': ext='.webp'
                else: continue
                path=out/(key+ext); path.write_bytes(data); print(key,path,len(data),url); chosen.append((key,str(path),url)); saved=True; break
            except Exception: continue
        if not saved: print(key,'no compatible image')
    # Official related visuals for pages that block direct crawling.
    fallback_files = {
        "openai": Path("output/ai-news/2026-09-14-ai-daily-01-openai.png"),
        "microsoft": Path("output/ai-news/2026-09-18/microsoft-related.jpg"),
    }
    for key, src in fallback_files.items():
        if not any(k == key for k,_,_ in chosen) and src.is_file():
            dest = out / (key + src.suffix); shutil.copyfile(src, dest); chosen.append((key, str(dest), "local official related visual")); print(key, dest, "copied related official visual")
    # Use first downloaded image as a cover if no explicit cover was found.
    if chosen:
        src=Path(chosen[0][1]); cover=out/('cover'+src.suffix); cover.write_bytes(src.read_bytes()); print('cover',cover)

if __name__=='__main__': main()
