#!/usr/bin/env python3
"""Save HTML, a cover, and optional inline images to WeChat drafts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


API_ROOT = "https://api.weixin.qq.com"


class WeChatError(RuntimeError):
    pass


def request_json(request: urllib.request.Request, stage: str) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise WeChatError(f"{stage} HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise WeChatError(f"{stage} network error: {exc.reason}") from exc

    try:
        result = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise WeChatError(f"{stage} returned invalid JSON") from exc

    if result.get("errcode") not in (None, 0):
        raise WeChatError(
            f"{stage} failed: errcode={result.get('errcode')}, "
            f"errmsg={result.get('errmsg', 'unknown')}"
        )
    return result


def get_access_token(app_id: str, app_secret: str) -> str:
    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
        }
    )
    request = urllib.request.Request(f"{API_ROOT}/cgi-bin/token?{query}")
    result = request_json(request, "get_access_token")
    token = result.get("access_token")
    if not token:
        raise WeChatError("get_access_token returned no access_token")
    return token


def upload_cover(access_token: str, cover_path: Path) -> str:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(cover_path.name)[0] or "application/octet-stream"
    file_bytes = cover_path.read_bytes()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                'Content-Disposition: form-data; name="media"; '
                f'filename="{cover_path.name}"\r\n'
            ).encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    url = (
        f"{API_ROOT}/cgi-bin/material/add_material?"
        + urllib.parse.urlencode({"access_token": access_token, "type": "thumb"})
    )
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    result = request_json(request, "upload_cover")
    media_id = result.get("media_id")
    if not media_id:
        raise WeChatError("upload_cover returned no media_id")
    return media_id


def upload_body_image(access_token: str, image_path: Path) -> str:
    """Upload an inline article image and return WeChat's stable image URL."""
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                'Content-Disposition: form-data; name="media"; '
                f'filename="{image_path.name}"\r\n'
            ).encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            image_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    url = f"{API_ROOT}/cgi-bin/media/uploadimg?" + urllib.parse.urlencode(
        {"access_token": access_token}
    )
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    result = request_json(request, f"upload_body_image:{image_path.name}")
    image_url = result.get("url")
    if not image_url:
        raise WeChatError(f"upload_body_image returned no url: {image_path.name}")
    return image_url


def clean_article_html(html: str) -> str:
    # The API already has a separate title field; avoid a duplicated title in the body.
    return re.sub(r"\s*<h1\b[^>]*>.*?</h1>\s*", "", html, count=1, flags=re.I | re.S)


def add_draft(
    access_token: str,
    title: str,
    digest: str,
    content: str,
    thumb_media_id: str,
    source_url: str,
) -> str:
    payload = {
        "articles": [
            {
                "title": title,
                "author": "",
                "digest": digest,
                "content": content,
                "content_source_url": source_url,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }
    url = f"{API_ROOT}/cgi-bin/draft/add?" + urllib.parse.urlencode(
        {"access_token": access_token}
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    result = request_json(request, "add_draft")
    media_id = result.get("media_id")
    if not media_id:
        raise WeChatError("add_draft returned no media_id")
    return media_id


def update_draft(
    access_token: str,
    draft_media_id: str,
    title: str,
    digest: str,
    content: str,
    thumb_media_id: str,
    source_url: str,
) -> str:
    payload = {
        "media_id": draft_media_id,
        "index": 0,
        "articles": {
            "title": title,
            "author": "",
            "digest": digest,
            "content": content,
            "content_source_url": source_url,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        },
    }
    url = f"{API_ROOT}/cgi-bin/draft/update?" + urllib.parse.urlencode(
        {"access_token": access_token}
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    request_json(request, "update_draft")
    return draft_media_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--cover", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--source-url", default="")
    parser.add_argument(
        "--draft-media-id",
        default="",
        help="Update article index 0 in an existing draft instead of creating a new draft.",
    )
    parser.add_argument(
        "--body-image",
        action="append",
        default=[],
        metavar="PLACEHOLDER=PATH",
        help="Upload an inline image and replace PLACEHOLDER in HTML; repeat as needed.",
    )
    return parser.parse_args()


def parse_body_images(values: list[str]) -> list[tuple[str, Path]]:
    parsed: list[tuple[str, Path]] = []
    seen: set[str] = set()
    seen_hashes: dict[str, Path] = {}
    supported_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    for value in values:
        if "=" not in value:
            raise WeChatError(f"invalid --body-image value: {value}")
        placeholder, raw_path = value.split("=", 1)
        placeholder = placeholder.strip()
        image_path = Path(raw_path.strip())
        if not placeholder or not raw_path.strip():
            raise WeChatError(f"invalid --body-image value: {value}")
        if placeholder in seen:
            raise WeChatError(f"duplicate body image placeholder: {placeholder}")
        if not image_path.is_file():
            raise WeChatError(f"body image file not found: {image_path}")
        if image_path.suffix.lower() not in supported_extensions:
            raise WeChatError(
                f"unsupported body image format: {image_path.suffix or '(none)'}; "
                "convert to JPG, PNG, or GIF before upload"
            )
        image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if image_hash in seen_hashes:
            raise WeChatError(
                "duplicate body image content: "
                f"{image_path} matches {seen_hashes[image_hash]}"
            )
        seen.add(placeholder)
        seen_hashes[image_hash] = image_path
        parsed.append((placeholder, image_path))
    return parsed


def load_env_file(path: Path) -> None:
    if not path.is_file():
        raise WeChatError(f"credential file not found: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip()


def main() -> int:
    args = parse_args()
    try:
        if args.env_file:
            load_env_file(args.env_file)
    except WeChatError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    app_id = os.environ.get("WECHAT_APP_ID")
    app_secret = os.environ.get("WECHAT_APP_SECRET")
    if not app_id or not app_secret:
        print("[FAIL] Missing WECHAT_APP_ID or WECHAT_APP_SECRET", file=sys.stderr)
        return 2
    if not args.html.is_file() or not args.cover.is_file():
        print("[FAIL] Article HTML or cover file does not exist", file=sys.stderr)
        return 2

    content = clean_article_html(args.html.read_text(encoding="utf-8"))
    try:
        body_images = parse_body_images(args.body_image)
        for placeholder, _ in body_images:
            count = content.count(placeholder)
            if count != 1:
                raise WeChatError(
                    f"body image placeholder must occur exactly once: {placeholder} "
                    f"(found {count})"
                )
    except WeChatError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    try:
        total_steps = 3 + len(body_images)
        step = 1
        print(f"[{step}/{total_steps}] Getting access token...")
        access_token = get_access_token(app_id, app_secret)
        print("[OK] Access token acquired")

        step += 1
        print(f"[{step}/{total_steps}] Uploading cover...")
        thumb_media_id = upload_cover(access_token, args.cover)
        print(f"[OK] Cover uploaded: media_id={thumb_media_id}")

        for placeholder, image_path in body_images:
            step += 1
            print(f"[{step}/{total_steps}] Uploading body image: {image_path.name}...")
            image_url = upload_body_image(access_token, image_path)
            image_tag = (
                '<img src="'
                + html.escape(image_url, quote=True)
                + '" alt="" style="display:block;width:100%;height:auto;margin:0 auto;" />'
            )
            content = content.replace(placeholder, image_tag)
            print(f"[OK] Body image uploaded: {image_path.name}")

        remaining_placeholders = re.findall(r"\{\{BODY_IMAGE_\d{2}\}\}", content)
        if remaining_placeholders:
            raise WeChatError(
                "unreplaced body image placeholders: "
                + ", ".join(sorted(set(remaining_placeholders)))
            )
        content_without_images = re.sub(r"<img\b[^>]*>", "", content, flags=re.I)
        if "mmbiz.qpic.cn" in content_without_images:
            raise WeChatError("bare WeChat image URL found outside an <img> tag")

        step += 1
        if args.draft_media_id:
            print(f"[{step}/{total_steps}] Updating draft...")
            draft_media_id = update_draft(
                access_token,
                args.draft_media_id,
                args.title,
                args.digest,
                content,
                thumb_media_id,
                args.source_url,
            )
            print(f"[OK] Draft updated: media_id={draft_media_id}")
        else:
            print(f"[{step}/{total_steps}] Creating draft...")
            draft_media_id = add_draft(
                access_token,
                args.title,
                args.digest,
                content,
                thumb_media_id,
                args.source_url,
            )
            print(f"[OK] Draft created: media_id={draft_media_id}")
        return 0
    except WeChatError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
