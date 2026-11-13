"""Render the dated five-item issue as WeChat-friendly inline HTML."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path


issue_date = sys.argv[1] if len(sys.argv) > 1 else "2026-09-18"
root = Path("output/ai-news") / issue_date
source = (root / f"{issue_date}-ai-daily.md").read_text(encoding="utf-8")
body = source.split("## 编辑与质检记录", 1)[0]
out = [
    '<section style="max-width:680px;margin:0 auto;color:#263449;font-family:-apple-system,BlinkMacSystemFont,Arial,sans-serif;">',
    f'<p style="font-size:13px;color:#728096;letter-spacing:1px;margin:8px 0 24px;">AI 资讯速读 · {issue_date.replace("-", ".")}</p>',
]
for line in body.splitlines():
    line = line.strip()
    if not line or line.startswith("# ") or line.startswith("**日期：**") or line.startswith("**摘要：**") or line.startswith("**分享语：**") or line.startswith("**关键词：**") or line == "---":
        continue
    if line.startswith("## "):
        title = html.escape(line[3:])
        out.append(f'<h2 style="font-size:21px;font-weight:700;line-height:1.5;color:#17233d;border-left:4px solid #315efb;padding-left:11px;margin:32px 0 12px;">{title}</h2>')
        continue
    image = re.fullmatch(r"_配图：(.+?)。(\{\{BODY_IMAGE_\d{2}\}\})_", line)
    if image:
        out.append(f'<p style="margin:18px 0 0;">{image.group(2)}</p>')
        out.append(f'<p style="font-size:12px;line-height:1.6;color:#8b96a6;margin:5px 0 25px;">图源：{html.escape(image.group(1))}。</p>')
        continue
    if line.startswith("**你所在"):
        text = html.escape(line.strip("*"))
        out.append(f'<p style="font-size:16px;line-height:1.8;color:#315efb;border-top:1px solid #e5eaf0;padding-top:20px;margin:32px 0;">{text}</p>')
        continue
    escaped = html.escape(line)
    escaped = re.sub(r"\[官方原文\]\((https?://[^)]+)\)", lambda m: f'<a href="{html.escape(m.group(1), quote=True)}" style="color:#315efb;text-decoration:none;">官方原文</a>', escaped)
    out.append(f'<p style="font-size:16px;font-weight:400;line-height:1.85;color:#344054;margin:0 0 14px;">{escaped}</p>')
out.append("</section>")
dest = root / f"{issue_date}-ai-daily.html"
dest.write_text("\n".join(out) + "\n", encoding="utf-8")
print(dest)
