#!/usr/bin/env python3
"""Publish a Tieji IPA into this repo and update latest.json + SHA256SUMS."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RAW_BASE = "https://raw.githubusercontent.com/yuanyeye0210-debug/tieji-releases/main"
SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(root: Path) -> dict:
    path = root / "latest.json"
    if not path.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "updated_at": utc_now(),
            "channels": {
                "ios": {
                    "latest": None,
                    "previous": None,
                    "mandatory": False,
                    "min_supported_version": "1.4.0",
                    "releases": [],
                }
            },
        }
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(root: Path, data: dict) -> None:
    data["schema_version"] = SCHEMA_VERSION
    data["updated_at"] = utc_now()
    (root / "latest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_sha256sums(root: Path, manifest: dict) -> None:
    lines = []
    channels = manifest.get("channels") or {}
    for channel in channels.values():
        for rel in channel.get("releases") or []:
            digest = rel.get("sha256")
            name = rel.get("file")
            if digest and name:
                lines.append(f"{digest}  {name}")
    # stable unique, keep last occurrence (newest write)
    seen = {}
    for line in lines:
        digest, _, name = line.partition("  ")
        seen[name] = digest
    text = "".join(f"{digest}  {name}\n" for name, digest in sorted(seen.items()))
    (root / "SHA256SUMS").write_text(text, encoding="utf-8")


def expected_url(filename: str) -> str:
    return f"{RAW_BASE}/{filename}"


def publish(root: Path, version: str, ipa: Path, changelog: str | None) -> dict:
    if not ipa.is_file():
        raise SystemExit(f"IPA not found: {ipa}")
    dest_name = f"Tieji-v{version}.ipa"
    dest = root / dest_name
    if ipa.resolve() != dest.resolve():
        shutil.copyfile(ipa, dest)
    digest = sha256_of(dest)
    size = dest.stat().st_size
    url = expected_url(dest_name)
    entry = {
        "version": version,
        "file": dest_name,
        "size": size,
        "sha256": digest,
        "download_url": url,
        "published_at": utc_now(),
    }
    if changelog:
        entry["changelog"] = changelog

    manifest = load_manifest(root)
    channels = manifest.setdefault("channels", {})
    ios = channels.setdefault("ios", {
        "latest": None, "previous": None, "mandatory": False,
        "min_supported_version": "1.4.0", "releases": [],
    })
    releases = [r for r in (ios.get("releases") or []) if r.get("version") != version]
    # replace same version in place (rebuild), keep others
    releases.insert(0, entry)
    prev = ios.get("latest")
    if prev and prev != version:
        ios["previous"] = prev
    ios["latest"] = version
    ios["releases"] = releases
    write_manifest(root, manifest)
    write_sha256sums(root, manifest)
    return entry


def cmd_publish(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if args.channel and args.channel != "ios":
        raise SystemExit(f"tieji-releases only has an ios channel, got {args.channel}")
    entry = publish(root, args.version, Path(args.ipa), args.changelog)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest = load_manifest(root)
    ios = (manifest.get("channels") or {}).get("ios") or {}
    latest = ios.get("latest")
    if not latest:
        print("no latest version yet")
        return 0
    releases = ios.get("releases") or []
    row = next((r for r in releases if r.get("version") == latest), None)
    if not row:
        raise SystemExit(f"latest {latest} missing from releases")
    path = root / row["file"]
    if not path.is_file():
        raise SystemExit(f"missing file {path}")
    digest = sha256_of(path)
    if digest != row.get("sha256"):
        raise SystemExit(f"sha256 mismatch for {path.name}")
    if path.stat().st_size != row.get("size"):
        raise SystemExit(f"size mismatch for {path.name}")
    print(f"ok {row['file']} {digest} {row['download_url']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("publish")
    p.add_argument("--channel", default="ios")
    p.add_argument("--version", required=True)
    p.add_argument("--ipa", required=True)
    p.add_argument("--changelog")
    p.set_defaults(func=cmd_publish)
    v = sub.add_parser("verify")
    v.set_defaults(func=cmd_verify)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
