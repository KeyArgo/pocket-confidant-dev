#!/usr/bin/env python3
"""Pocket Confidant — version + build-number manager.

Single source of truth: VERSION at the repo root.

VERSION file format (one line, semver-ish):
    MAJOR.MINOR.PATCH                    clean release (matches tag exactly)
    MAJOR.MINOR.PATCH-dev                pre-release work, no tag yet
    MAJOR.MINOR.PATCH-buildNNN           post-release, NNN commits since tag

Detection logic (idempotent — safe to run any number of times):

  read VERSION  -> 0.2.0-dev
  parse: major.minor.patch = 0.2.0, suffix = -dev
  look for tag v0.2.0
    - no tag  -> state = prerelease
                 target = "0.2.0-dev"   (preserve user-supplied suffix or default to -dev)
    - tag exists:
        - 0 commits since tag  -> state = released-clean
                                  target = "0.2.0"
        - N commits since tag  -> state = released-with-build
                                  target = "0.2.0-build{N:03d}"

  if VERSION != target: rewrite VERSION, rewrite metadata.json
  else:                no-op (safe to run pre-commit, doesn't dirty the tree)

To bump the release version (0.2.0 -> 0.3.0):
    # manual:
    echo "0.3.0-dev" > VERSION
    # or, after tagging v0.2.0 and committing all post-release work:
    python scripts/bump_version.py --set 0.3.0-dev

Usage:
    python scripts/bump_version.py            # compute + write if changed
    python scripts/bump_version.py --print    # show computed version, don't write
    python scripts/bump_version.py --set X.Y.Z[-suffix]   # force-set release
    python scripts/bump_version.py --stage    # also `git add VERSION metadata.json`
    python scripts/bump_version.py --json     # emit metadata.json contents to stdout

Why git-derived: build number = `git rev-list vX.Y.Z..HEAD --count`. No counter
file, no drift, naturally resets on the next release tag.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "VERSION"
METADATA_FILE = REPO_ROOT / "metadata.json"

# Accept: 0.2.0 | 0.2.0-dev | 0.2.0-build001 | v0.2.0 | v0.2.0-dev
SEMVER_RE = re.compile(
    r"^v?"
    r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<suffix>[A-Za-z0-9.\-]+))?"
    r"\s*$"
)


# --------------------------------------------------------------------------- #
# git helpers
# --------------------------------------------------------------------------- #
def _run(args: list[str]) -> Tuple[int, str, str]:
    p = subprocess.run(
        args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def is_git_repo() -> bool:
    rc, _, _ = _run(["git", "rev-parse", "--git-dir"])
    return rc == 0


def tag_exists(tag: str) -> bool:
    rc, out, _ = _run(["git", "tag", "-l", tag])
    return rc == 0 and out == tag


def commits_since_tag(tag: str) -> int:
    """Count commits reachable from HEAD but not from tag. 0 if tag missing."""
    if not tag_exists(tag):
        return 0
    rc, out, _ = _run(["git", "rev-list", f"{tag}..HEAD", "--count"])
    if rc != 0:
        return 0
    try:
        return int(out)
    except ValueError:
        return 0


def current_commit() -> str:
    rc, out, _ = _run(["git", "rev-parse", "--short", "HEAD"])
    return out if rc == 0 else "unknown"


def current_branch() -> str:
    rc, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return out if rc == 0 else "unknown"


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #
def parse_version(raw: str) -> Tuple[int, int, int, Optional[str]]:
    """Return (major, minor, patch, suffix-or-None). Raises ValueError on bad input."""
    m = SEMVER_RE.match(raw.strip())
    if not m:
        raise ValueError(f"VERSION is not valid semver: {raw!r}")
    return (
        int(m["major"]),
        int(m["minor"]),
        int(m["patch"]),
        m["suffix"],
    )


def clean(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


# --------------------------------------------------------------------------- #
# compute target version
# --------------------------------------------------------------------------- #
def compute(raw_version: str) -> dict:
    """Return the target state: target string + metadata dict."""
    major, minor, patch, suffix = parse_version(raw_version)
    base = clean(major, minor, patch)
    tag = f"v{base}"

    info = {
        "base": base,
        "tag": tag,
        "state": "unknown",
        "build": None,
        "target": raw_version.strip(),
        "commits_since_tag": 0,
        "tag_exists": False,
    }

    if not is_git_repo():
        # No git: just trust whatever's in VERSION, mark as prerelease by default
        info["state"] = "no-git"
        info["target"] = raw_version.strip() or f"{base}-dev"
        return info

    if not tag_exists(tag):
        # No release tag yet — pre-release work
        info["state"] = "prerelease"
        # Preserve the user's suffix if they wrote one (e.g. -dev, -rc1, -alpha);
        # otherwise default to -dev so the state is always explicit.
        if suffix:
            info["target"] = f"{base}-{suffix}"
        else:
            info["target"] = f"{base}-dev"
        return info

    info["tag_exists"] = True
    n = commits_since_tag(tag)
    info["commits_since_tag"] = n

    if n == 0:
        info["state"] = "released-clean"
        info["target"] = base
    else:
        info["state"] = "released-with-build"
        info["build"] = n
        info["target"] = f"{base}-build{n:03d}"

    return info


# --------------------------------------------------------------------------- #
# write
# --------------------------------------------------------------------------- #
def write_version(target: str) -> bool:
    """Write VERSION if different. Return True if changed."""
    current = ""
    if VERSION_FILE.exists():
        current = VERSION_FILE.read_text().strip()
    if current == target:
        return False
    VERSION_FILE.write_text(target + "\n")
    return True


def write_metadata(info: dict) -> None:
    payload = {
        "version": info["target"],
        "base": info["base"],
        "tag": info["tag"],
        "tag_exists": info.get("tag_exists", False),
        "state": info["state"],
        "build": info.get("build"),
        "commits_since_tag": info.get("commits_since_tag", 0),
        "commit": current_commit(),
        "branch": current_branch(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    METADATA_FILE.write_text(json.dumps(payload, indent=2) + "\n")


def git_stage() -> None:
    rc, _, err = _run(["git", "add", str(VERSION_FILE), str(METADATA_FILE)])
    if rc != 0:
        print(f"warning: git add failed: {err}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--print", action="store_true", help="print computed version, do not write")
    p.add_argument("--json", action="store_true", help="emit metadata.json contents to stdout")
    p.add_argument("--stage", action="store_true", help="git add VERSION + metadata.json after writing")
    p.add_argument("--set", metavar="VERSION", help="force-set VERSION (e.g. 0.3.0-dev), then compute")
    p.add_argument("--quiet", "-q", action="store_true", help="suppress human-readable output")
    args = p.parse_args()

    if not VERSION_FILE.exists():
        VERSION_FILE.write_text("0.0.0-dev\n")
        if not args.quiet:
            print(f"created {VERSION_FILE.relative_to(REPO_ROOT)} with 0.0.0-dev", file=sys.stderr)

    raw = VERSION_FILE.read_text().strip()

    if args.set:
        # Force-set the release line, then re-run detection against it
        # Validates the user input is well-formed first
        try:
            parse_version(args.set)
        except ValueError as e:
            print(f"error: --set value invalid: {e}", file=sys.stderr)
            return 2
        raw = args.set
        if raw != VERSION_FILE.read_text().strip():
            VERSION_FILE.write_text(raw + "\n")

    info = compute(raw)

    if args.json:
        # Augment with commit/branch/timestamp so consumers see the full picture
        info["commit"] = current_commit()
        info["branch"] = current_branch()
        info["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(json.dumps(info, indent=2))
        return 0

    if args.print:
        print(info["target"])
        return 0

    changed = write_version(info["target"])
    write_metadata(info)
    if args.stage and changed:
        git_stage()

    if not args.quiet:
        state_emoji = {
            "prerelease": "🧪",
            "released-clean": "✅",
            "released-with-build": "🔧",
            "no-git": "❓",
        }.get(info["state"], "•")
        commit = current_commit()
        msg = f"{state_emoji} {info['target']}  ({info['state']}, {commit}"
        if info["state"] == "released-with-build":
            msg += f", {info['commits_since_tag']} commits since {info['tag']}"
        elif info["state"] == "prerelease":
            msg += f", waiting for tag {info['tag']}"
        msg += ")"
        print(msg)
        if changed:
            print(f"   wrote {VERSION_FILE.relative_to(REPO_ROOT)} + {METADATA_FILE.relative_to(REPO_ROOT)}")
        else:
            print(f"   no change (already at {info['target']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
