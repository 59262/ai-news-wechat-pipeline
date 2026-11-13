"""Download dated issue's official related images when article pages block fetching."""
import urllib.request
from pathlib import Path

OUT = Path("output/ai-news/2026-09-18")
URLS = {
    "openai-related.png": "https://deploymentsafety.openai.com/data/eval-sets/gpt-5-6/assets/images/internaldep.png",
    "microsoft-related.jpg": "https://blogs.microsoft.com/wp-content/uploads/2025/12/OMB-FY26Q2-Hero-e1773250045900-1024x576.jpg",
    "cover.jpg": "https://blogs.nvidia.com/wp-content/uploads/2026/09/nvidia-vera-rubin-delivers-up-to-3-7x-better-performance.jpeg",
}
OUT.mkdir(parents=True, exist_ok=True)
for name, url in URLS.items():
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
        if not (data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG")):
            raise ValueError("Image is not JPG or PNG")
        (OUT / name).write_bytes(data)
        print(name, len(data), url)
    except Exception as exc:
        print(name, "FAILED", type(exc).__name__, exc)
