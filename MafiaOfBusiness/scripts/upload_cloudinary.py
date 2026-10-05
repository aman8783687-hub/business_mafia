#!/usr/bin/env python3
"""Upload a finalized Business Mafia episode to Cloudinary and expose a
direct-download link valid for ~24 hours.

Public + auto-delete model (operator chose this):
  - upload is public (resource_type=video, folder `business-mafia/`),
    tagged `mafia-of-business` + `expires-24h`, with `context` carrying
    `expires_at` (UTC ISO) so the cleanup workflow knows what to delete.
  - the download link is the secure_url with `fl_attachment` forced, so a
    click downloads instead of streaming.
  - `.github/workflows/cleanup-cloudinary.yml` runs hourly and destroys
    anything in `business-mafia/` older than 24h.

Auth via env (never commit): CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY,
CLOUDINARY_API_SECRET. Reads .env via env_loader (local) without
overriding real env (GitHub secrets win).

Usage:
    python3 scripts/upload_cloudinary.py <episode-slug>
    python3 scripts/upload_cloudinary.py <episode-slug> --video path/to.mp4
    python3 scripts/upload_cloudinary.py cleanup [--max-age-hours 24] [--dry-run]

Upload writes <output>/<slug>/cloudinary.json and, when running in GitHub
Actions, appends a download link to $GITHUB_STEP_SUMMARY and sets
$GITHUB_OUTPUT (video_url, download_url, public_id).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import env_loader  # noqa: E402

WORKSPACE = SCRIPTS_DIR.parent
OUTPUT_ROOT = WORKSPACE / "output"
FOLDER = "business-mafia"
TAG = "mafia-of-business"
EXPIRES_TAG = "expires-24h"
PUBLIC_EXPIRY_HOURS = 24


def _creds() -> tuple[str, str, str]:
    return (
        env_loader.get("CLOUDINARY_CLOUD_NAME"),
        env_loader.get("CLOUDINARY_API_KEY"),
        env_loader.get("CLOUDINARY_API_SECRET"),
    )


def _sign(params: dict[str, str], secret: str) -> str:
    payload = "&".join(f"{k}={params[k]}" for k in sorted(params)) + secret
    return hashlib.sha1(payload.encode()).hexdigest()


def find_video(slug: str) -> tuple[Path, Path]:
    """Return (video_path, out_dir) for a finalized episode."""
    out_dir = OUTPUT_ROOT / slug
    candidates = sorted(out_dir.glob("mafia-of-business-*.mp4"))
    if candidates:
        return candidates[0], out_dir
    # Fallback: any mp4 in the output dir.
    candidates = sorted(out_dir.glob("*.mp4"))
    if candidates:
        return candidates[0], out_dir
    raise RuntimeError(f"no .mp4 found in {out_dir} (run finalize first)")


def upload_video(video: Path, slug: str, expiry_hours: int = PUBLIC_EXPIRY_HOURS) -> dict:
    cloud, key, secret = _creds()
    timestamp = int(time.time())
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=expiry_hours)).isoformat()
    public_id = f"{FOLDER}/{slug}"
    params = {
        "timestamp": str(timestamp),
        "public_id": public_id,
        "folder": FOLDER,
        "resource_type": "video",
        "type": "upload",
        "tags": f"{TAG},{EXPIRES_TAG}",
        "context": f"slug={slug}|expires_at={expires_at}",
    }
    # Cloudinary signs every param except file/cloud_name/api_key/resource_type/type.
    sign_params = {k: v for k, v in params.items() if k not in ("resource_type", "type")}
    files = {"file": (video.name, open(video, "rb"), "video/mp4")}
    data = {**sign_params, "api_key": key, "signature": _sign(sign_params, secret)}
    try:
        resp = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud}/video/upload",
            data=data, files=files, timeout=600,
        )
        resp.raise_for_status()
    finally:
        files["file"][1].close()
    body = resp.json()
    secure_url: str = body["secure_url"]
    # Force download on click: insert fl_attachment transformation.
    download_url = secure_url.replace("/video/upload/", "/video/upload/fl_attachment/")
    return {
        "slug": slug,
        "public_id": body.get("public_id", public_id),
        "video_url": secure_url,
        "download_url": download_url,
        "bytes": body.get("bytes"),
        "duration": body.get("duration"),
        "expires_at": expires_at,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }


def _github_output(result: dict) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if out_path:
        with open(out_path, "a") as fh:
            fh.write(f"video_url={result['video_url']}\n")
            fh.write(f"download_url={result['download_url']}\n")
            fh.write(f"public_id={result['public_id']}\n")
            fh.write(f"slug={result['slug']}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        size_mb = f"{result['bytes'] / 1e6:.1f} MB" if result.get("bytes") else "?"
        with open(summary, "a") as fh:
            fh.write(
                f"## 📥 Business Mafia: {result['slug']}\n\n"
                f"**[⬇️ Download video]({result['download_url']})** ({size_mb}) — "
                f"link valid ~24h, expires {result['expires_at'][:16]} UTC.\n\n"
                f"Preview: {result['video_url']}\n"
            )


def cmd_upload(slug: str, video_arg: str | None) -> int:
    video, out_dir = (Path(video_arg), OUTPUT_ROOT / slug) if video_arg else find_video(slug)
    if not video.exists():
        print(f"video not found: {video}", file=sys.stderr)
        return 1
    print(f"Uploading {video} ({video.stat().st_size / 1e6:.1f} MB) to Cloudinary...")
    result = upload_video(video, slug)
    (out_dir / "cloudinary.json").write_text(json.dumps(result, indent=2))
    print(f"video_url:    {result['video_url']}")
    print(f"download_url: {result['download_url']}  (click = direct download, ~24h)")
    print(f"expires_at:   {result['expires_at']}")
    _github_output(result)
    return 0


def cmd_cleanup(max_age_hours: float, dry_run: bool) -> int:
    """Delete public uploads in FOLDER older than max_age_hours (Admin API)."""
    cloud, key, secret = _creds()
    auth = (key, secret)
    # List video resources under our folder (paginated, newest first).
    url = f"https://api.cloudinary.com/v1_1/{cloud}/resources/video"
    params: dict = {"type": "upload", "prefix": FOLDER + "/", "max_results": 100}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    deleted, kept, checked = [], [], 0
    next_cursor = None
    while True:
        q = dict(params)
        if next_cursor:
            q["next_cursor"] = next_cursor
        resp = requests.get(url, auth=auth, params=q, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        for res in body.get("resources", []):
            checked += 1
            created = datetime.fromisoformat(res["created_at"].replace("Z", "+00:00"))
            pid = res["public_id"]
            if created < cutoff:
                if dry_run:
                    print(f"[dry-run] would delete {pid} (created {res['created_at']})")
                    deleted.append(pid)
                    continue
                timestamp = int(time.time())
                sig_params = {"public_id": pid, "timestamp": str(timestamp), "invalidate": "true"}
                data = {**sig_params, "api_key": key,
                        "signature": _sign(sig_params, secret)}
                d = requests.post(
                    f"https://api.cloudinary.com/v1_1/{cloud}/video/destroy",
                    data=data, timeout=120)
                d.raise_for_status()
                print(f"deleted {pid} (created {res['created_at']})")
                deleted.append(pid)
            else:
                kept.append(pid)
        next_cursor = body.get("next_cursor")
        if not next_cursor:
            break
    print(f"checked={checked} deleted={len(deleted)} kept={len(kept)} (cutoff {cutoff.isoformat()})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="Episode slug (output/<slug>/) or 'cleanup'")
    ap.add_argument("--video", help="Explicit .mp4 path (default: output/<slug>/*.mp4)")
    ap.add_argument("--max-age-hours", type=float, default=24)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.slug == "cleanup":
        return cmd_cleanup(args.max_age_hours, args.dry_run)
    if not args.slug:
        ap.print_usage(sys.stderr)
        return 1
    return cmd_upload(args.slug, args.video)


if __name__ == "__main__":
    sys.exit(main())
