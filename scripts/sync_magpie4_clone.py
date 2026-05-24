#!/usr/bin/env python3
"""Clone magpie4 R package source at the renv.lock-pinned commit.

magpie4 is the R post-processing package consuming fulldata.gdx. The
magpie-agent answers questions about it by reading SHA-pinned source on
demand, NOT by curating function-level docs (309 exports, treadmill trap).

This script keeps a local SHA-aligned clone of magpie4 at
.cache/sources/magpie4/ matched to whatever the parent MAgPIE renv.lock
pins, and records the pin in project/version_pins.json so the agent can
verify freshness before answering.

Usage:
  python3 scripts/sync_magpie4_clone.py             # clone/update to pinned SHA
  python3 scripts/sync_magpie4_clone.py --check     # SHA alignment only, no changes
  python3 scripts/sync_magpie4_clone.py --renv-lock PATH  # explicit renv.lock
  python3 scripts/sync_magpie4_clone.py --allow-head-fallback  # accept HEAD if SHA+tag both unavailable (default: refuse)

Idempotent: re-running while already at the pinned SHA is a no-op.

Exit codes (per R5 audit Cluster L hardening, 2026-05-24):
  0 — aligned (pinned SHA matches local HEAD, or sync completed at the SHA)
  1 — misaligned (local cache exists but HEAD does not match pin)
  2 — not cloned (no local cache yet; only --check)
  3 — silent HEAD-fallback refused (SHA and tag both unavailable on GitHub
      and --allow-head-fallback not set). Callers can decide whether to
      retry, escalate, or accept the downgrade via the flag.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = "magpie4"
REPO_URL = f"https://github.com/pik-piam/{PACKAGE}.git"


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def current_sha(repo_dir, full=False):
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha if full else sha[:10]


def resolve_renv_lock(agent_dir, explicit_path):
    """Locate renv.lock. Order: --renv-lock arg, then standard MAgPIE locations."""
    if explicit_path:
        p = Path(explicit_path).resolve()
        if not p.exists():
            sys.exit(f"--renv-lock: file not found at {p}")
        return p

    candidates = [
        agent_dir / ".." / "input" / "renv.lock",
        agent_dir / ".." / "renv.lock",
    ]
    for c in candidates:
        resolved = c.resolve()
        if resolved.exists():
            return resolved

    checked = "\n  ".join(str(c.resolve()) for c in candidates)
    sys.exit(
        f"No renv.lock found. Checked:\n  {checked}\n\n"
        f"Re-pair this agent with a magpie/ working tree containing input/renv.lock."
    )


def load_magpie4_record(lock_path):
    with open(lock_path) as f:
        data = json.load(f)
    rec = data.get("Packages", {}).get(PACKAGE)
    if not rec:
        sys.exit(f"{PACKAGE} not found in {lock_path}")
    return rec


def write_version_pins(agent_dir, version, sha, source_dir, lock_path, resolution):
    """Write project/version_pins.json snapshot. Single-package shape."""
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lock_bytes = Path(lock_path).read_bytes() if Path(lock_path).is_file() else b""
    lock_hash = hashlib.sha256(lock_bytes).hexdigest() if lock_bytes else ""
    pins = {
        "schema_version": 1,
        "captured_at": captured_at,
        "lock_file": str(lock_path),
        "lock_file_sha256": lock_hash,
        "packages": {
            PACKAGE: {
                "version": version,
                "sha": sha,
                "source_dir": source_dir,
                "resolution": resolution,
            },
        },
        "_documentation": {
            "purpose": "Records the SHA-pinned magpie4 clone state. Agent reads this to verify freshness before answering magpie4 questions.",
            "consumers": [
                "agent/helpers/magpie4_reference.md (auto-loaded helper)",
            ],
            "lifecycle": "Refreshed by scripts/sync_magpie4_clone.py. Gitignored — regenerate locally.",
            "resolution_values": {
                "sha": "Checked out at the exact RemoteSha from renv.lock.",
                "tag": "RemoteSha unavailable on GitHub; fell back to v<version> tag.",
                "head": "Both SHA and tag unavailable; using HEAD of default branch (version may not match).",
            },
        },
    }
    pins_file = agent_dir / "project" / "version_pins.json"
    pins_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pins_file, "w") as f:
        json.dump(pins, f, indent=2)
    return pins_file


def checkout_pinned(dest, sha, version, allow_head_fallback=False):
    """Try SHA → tag → HEAD (if allowed). Return resolution string used or None if HEAD fallback refused."""
    try:
        run(["git", "-C", str(dest), "checkout", "--quiet", sha])
        return "sha"
    except subprocess.CalledProcessError:
        pass

    try:
        run(["git", "-C", str(dest), "fetch", "--tags", "--quiet", "origin"])
        run(["git", "-C", str(dest), "checkout", "--quiet", f"v{version}"])
        print(f"  WARNING: SHA {sha[:10]} not found on GitHub; checked out v{version} tag.")
        return "tag"
    except subprocess.CalledProcessError:
        pass

    if not allow_head_fallback:
        print(f"  ERROR: SHA {sha[:10]} and v{version} tag both unavailable on GitHub. "
              f"Refusing to silently downgrade to HEAD. Pass --allow-head-fallback "
              f"to accept the downgrade explicitly (version_pins.json will record "
              f"resolution='head'). Exit code 3.")
        return None

    head_sha = current_sha(dest) or "unknown"
    print(f"  WARNING: SHA {sha[:10]} and v{version} tag unavailable; using HEAD ({head_sha}). "
          f"Version may NOT match renv.lock pin.")
    return "head"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="Verify SHA alignment only; no clone/checkout.")
    parser.add_argument("--renv-lock", metavar="PATH",
                        help="Explicit path to renv.lock (overrides candidate search).")
    parser.add_argument("--allow-head-fallback", action="store_true",
                        help="Accept HEAD fallback if SHA and version tag are both "
                             "unavailable on GitHub (default: refuse with exit 3).")
    args = parser.parse_args()

    agent_dir = Path(__file__).resolve().parent.parent
    cache_dir = agent_dir / ".cache" / "sources"
    dest = cache_dir / PACKAGE

    lock_path = resolve_renv_lock(agent_dir, args.renv_lock)
    rec = load_magpie4_record(lock_path)
    version = rec["Version"]
    sha = rec.get("RemoteSha", "")
    if not sha:
        sys.exit(f"{PACKAGE} entry in {lock_path} has no RemoteSha. Cannot pin.")

    print(f"[sync_magpie4_clone] renv.lock: {lock_path}")
    print(f"[sync_magpie4_clone] pinned: {PACKAGE} v{version} @ {sha[:10]}")

    if args.check:
        live = current_sha(dest)
        if not live:
            print(f"  Not cloned. Run without --check to clone. Exit code 2.")
            sys.exit(2)
        aligned = sha.startswith(live) or live.startswith(sha[:10])
        print(f"  local HEAD: {live} {'✓ aligned' if aligned else '✗ MISMATCH'}")
        sys.exit(0 if aligned else 1)

    # Already at the pinned SHA? No-op.
    if (dest / ".git").exists():
        live = current_sha(dest)
        if live and sha.startswith(live):
            print(f"  {PACKAGE} v{version} already at {sha[:10]} — no-op.")
            # Refresh version_pins.json to keep captured_at current.
            pins_file = write_version_pins(
                agent_dir, version, sha, str(dest), str(lock_path), "sha"
            )
            print(f"  version_pins.json refreshed: {pins_file}")
            return
        print(f"  {PACKAGE} v{version}: fetching to checkout {sha[:10]}...")
        try:
            run(["git", "-C", str(dest), "fetch", "--quiet", "origin"])
        except subprocess.CalledProcessError as e:
            print(f"  WARNING: fetch failed: {e.stderr.strip()}")
    else:
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Cloning {REPO_URL} → {dest}...")
        try:
            run([
                "git", "clone",
                "--filter=blob:none", "--no-checkout", "--quiet",
                REPO_URL, str(dest),
            ])
        except subprocess.CalledProcessError as e:
            sys.exit(f"ERROR cloning {PACKAGE}: {e.stderr.strip()}")

    resolution = checkout_pinned(dest, sha, version, allow_head_fallback=args.allow_head_fallback)
    if resolution is None:
        # HEAD-fallback was refused. Do NOT write version_pins.json (caller
        # would otherwise consume a downgraded pin without realizing).
        sys.exit(3)

    final_sha = current_sha(dest)
    print(f"  {PACKAGE} v{version} cached at {dest} (HEAD: {final_sha}, resolution: {resolution})")

    pins_file = write_version_pins(
        agent_dir, version, sha, str(dest), str(lock_path), resolution
    )
    print(f"  version_pins.json: {pins_file}")


if __name__ == "__main__":
    main()
