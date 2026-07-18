#!/usr/bin/env python3
"""Check 40: local absolute paths committed to a PUBLIC repo.

`mscrawford/magpie-agent` is public, so `AGENT.md` § *PUBLIC repo — secret & PII
hygiene* binds: never hard-code a local absolute path (`/Users/<you>`,
`/p/projects/...`) into docs, audit logs, or example commands — use
`<magpie-root>`, `~`, or a relative path.

Until now that rule was BOUND BUT UNENFORCED, which is why it recurred across
rounds (R58, R59) and why an earlier audit found local paths baked into
thousands of history blobs. A norm without a gate recurs forever. This is the
gate.

WHY IT KEEPS HAPPENING (the upstream cause this check backstops): subagent
prompts that paste an absolute working directory get echoed back into the
agents' own output. Prevention lives in how work is dispatched (give agents a
repo-relative brief); this check is the last line, not the fix.
See AGENT.md § *Dispatching subagents* and the memory
`feedback_recurring_hygiene_leak_fix_upstream`.

PLACEHOLDERS ARE FINE. `/Users/<you>`, `/Users/<user>`, `/home/<user>` are the
prescribed way to WRITE the rule, so anything whose user component is an
angle-bracketed placeholder is exempt by design. Only concrete user/project
names are flagged.

Usage:
    python3 scripts/check_local_paths.py            # scan tracked files
    python3 scripts/check_local_paths.py --verbose  # list every hit
    python3 scripts/check_local_paths.py --self-test # positive+negative control

Exit 0 = clean (or only allowlisted). Exit 1 = findings. Exit 2 = checker error.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent
ALLOWLIST = AGENT_DIR / "audit" / "local_path_allowlist.json"

SCAN_SUFFIXES = {".md", ".sh", ".py", ".json", ".txt", ".yml", ".yaml"}

# A concrete local path: the component after the prefix must NOT be an
# angle-bracketed placeholder. `(?!<)` is what keeps `/Users/<you>` legal.
PATTERNS = [
    ("users_home", re.compile(r"/Users/(?!<)[A-Za-z0-9._-]+")),
    ("linux_home", re.compile(r"/home/(?!<)[A-Za-z0-9._-]+")),
    ("hpc_project", re.compile(r"/p/projects/(?!<)[A-Za-z0-9._-]+")),
    ("private_tmp", re.compile(r"/private/tmp/(?!<)[A-Za-z0-9._-]+")),
]

# Generic placeholder user names that are conventions, not real identities.
PLACEHOLDER_USERS = {"user", "you", "me", "username", "USER", "yourname", "name"}

# An all-dots tail is an ellipsis, i.e. the rule text quoting ITSELF
# ("avoid /Users/..., /p/projects/..."). Documenting the rule must not trip it.
ELLIPSIS_TAIL = re.compile(r"^\.+$")


def load_allowlist() -> dict:
    if not ALLOWLIST.exists():
        return {"entries": []}
    try:
        return json.loads(ALLOWLIST.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover
        print(f"ERROR: allowlist is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "-C", str(AGENT_DIR), "ls-files"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"ERROR: could not list tracked files: {exc}", file=sys.stderr)
        sys.exit(2)
    files = []
    for rel in out.splitlines():
        p = AGENT_DIR / rel
        if p.suffix.lower() in SCAN_SUFFIXES and p.is_file():
            files.append(p)
    return files


def scan_text(text: str, rel: str) -> list[dict]:
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                token = m.group(0)
                tail = token.rsplit("/", 1)[-1]
                if tail in PLACEHOLDER_USERS or ELLIPSIS_TAIL.match(tail):
                    continue
                hits.append({
                    "file": rel, "line": lineno, "kind": kind,
                    "match": token, "text": line.strip()[:160],
                })
    return hits


def allowlisted(hit: dict, allow: dict) -> bool:
    """Exact-file or prefix-scoped exemption.

    A `path_prefix` entry MUST also pin `match`, so an exemption covers one
    known string under one directory — never "anything under this dir".
    A broad exemption would hide the next real leak, which is the whole
    failure mode this check exists to close.
    """
    for e in allow.get("entries", []):
        if e.get("file") == hit["file"]:
            if e.get("match") in (None, hit["match"]):
                return True
        prefix = e.get("path_prefix")
        if prefix and hit["file"].startswith(prefix) and e.get("match") == hit["match"]:
            return True
    return False


def self_test() -> int:
    """Positive AND negative control.

    A checker that has never been shown a known bug cannot distinguish
    'corpus clean' from 'checker broken'. This runs both directions before
    the corpus scan is allowed to mean anything.
    """
    bad = "see /Users/alice/Documents/thing and /p/projects/foo/bar\n"
    good = ("see /Users/<you>/Documents/thing and `<magpie-root>` and ~/rel\n"
            "and the rule quoting itself: avoid /Users/... or /p/projects/...\n")

    pos = scan_text(bad, "SYNTHETIC")
    if len(pos) < 2:
        print(f"SELF-TEST FAIL: positive control found {len(pos)} hits, expected >= 2")
        return 1
    neg = scan_text(good, "SYNTHETIC")
    if neg:
        print(f"SELF-TEST FAIL: negative control produced {len(neg)} false positive(s): {neg}")
        return 1

    # vacuity control: the scanner must actually be looking at the text
    if scan_text("nothing here at all\n", "SYNTHETIC"):
        print("SELF-TEST FAIL: matched a line with no paths")
        return 1

    print("SELF-TEST OK - positive (2 hits), negative (0 FPs), vacuity controls all pass.")
    print("SELFTEST_OK check_local_paths")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    allow = load_allowlist()
    files = tracked_files()
    if not files:
        print("ERROR: no tracked files matched - refusing to report 'clean'", file=sys.stderr)
        return 2

    findings, skipped = [], 0
    for p in files:
        rel = str(p.relative_to(AGENT_DIR))
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        for hit in scan_text(text, rel):
            if allowlisted(hit, allow):
                skipped += 1
            else:
                findings.append(hit)

    print(f"check_local_paths: coverage = {len(files)} tracked files scanned, "
          f"{len(findings)} finding(s), {skipped} allowlisted")
    if findings and args.verbose:
        for f in findings:
            print(f"  {f['file']}:{f['line']} [{f['kind']}] {f['match']}")
            print(f"      {f['text']}")
    elif findings:
        for f in findings[:10]:
            print(f"  {f['file']}:{f['line']} [{f['kind']}] {f['match']}")

    print(f"check_local_paths: SUMMARY findings={len(findings)} "
          f"files={len(files)} allowlisted={skipped}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
