#!/usr/bin/env python3
"""Check 24 — flag references to historically-renamed identifiers.

Reads `feedback/renames.json` and greps for each `old` name in non-exempt
docs. Catches the class where an identifier was renamed in MAgPIE but a doc
author wrote new content still referencing the old name (e.g., M14 pcm_tau
h→j rename: stragglers in §7.2/§16.2 escaped R3 review).

Differs from Check 14 (check_gams_variables.py): Check 14 verifies the doc's
identifier EXISTS in current code. This check verifies the doc isn't using
an identifier that USED TO exist but has since been renamed. Both are needed
because Check 14 misses "old name still references an existing variable
under a slightly different prefix" cases.

Usage: python3 check_renames.py [--summary-only]
Exit: 0 always (advisory; mismatches surface via output text)
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
RENAMES_PATH = AGENT_DIR / "feedback" / "renames.json"

# Where to scan. Exclude archives and the renames file itself.
SCAN_DIRS = [
    AGENT_DIR / "modules",
    AGENT_DIR / "core_docs",
    AGENT_DIR / "cross_module",
    AGENT_DIR / "agent",
    AGENT_DIR / "reference",
]
ALWAYS_EXEMPT = [
    "feedback/*",
    "*/.git/*",
    "reference/archive/*",
    "scripts/__pycache__/*",
]


def load_renames() -> list[dict]:
    if not RENAMES_PATH.is_file():
        return []
    data = json.loads(RENAMES_PATH.read_text(encoding="utf-8"))
    return data.get("renames", [])


def is_exempt(rel_path: str, exempt_patterns: list[str]) -> bool:
    for pat in exempt_patterns:
        if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(rel_path, f"*{pat}*"):
            return True
        # Substring match for directory globs like "feedback/"
        if pat.endswith("/") and pat.rstrip("/") in rel_path.split(os.sep):
            return True
    return False


def main() -> int:
    args = sys.argv[1:]
    summary_only = "--summary-only" in args

    renames = load_renames()
    if not renames:
        print("⚠️  No renames defined in feedback/renames.json — skipping")
        return 0

    print("Historical-rename reference check")
    print("==================================")
    print(f"Renames tracked: {len(renames)}")

    # Pre-compile patterns
    # Per agent/commands/sync.md convention, `*name*` (italicized) is the doc
    # convention for "historical reference, not current identifier" — exclude
    # these from the flag. Also exclude allowlist marker lines (markers MUST
    # mention old names to suppress Check 14 flags).
    compiled = []
    for r in renames:
        old = r["old"]
        # Word-boundary anchored; the literal is treated as a regex-safe string
        pattern = re.compile(r"\b" + re.escape(old) + r"\b")
        compiled.append((pattern, r))

    ITALIC_HISTORICAL_RE = re.compile(r"\*([A-Za-z_][A-Za-z0-9_]*)\*")
    ALLOWLIST_LINE_RE = re.compile(r"check-gams-vars:\s*allow")

    total_hits = 0
    per_rename: dict[str, list[tuple[str, int]]] = {}

    for scan_dir in SCAN_DIRS:
        if not scan_dir.is_dir():
            continue
        for root, dirs, files in os.walk(scan_dir):
            # Skip archive dirs
            dirs[:] = [d for d in dirs if d not in ("archive", "__pycache__", ".git")]
            for name in files:
                if not name.endswith((".md", ".sh", ".py")):
                    continue
                path = Path(root) / name
                rel = str(path.relative_to(AGENT_DIR))
                if is_exempt(rel, ALWAYS_EXEMPT):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for pattern, rename in compiled:
                    if is_exempt(rel, rename.get("exempt_paths", [])):
                        continue
                    for m in pattern.finditer(text):
                        # Skip italicized historical references: `*old_name*`
                        # (the doc convention for "no longer current identifier").
                        if m.start() > 0 and text[m.start() - 1] == "*":
                            end = m.end()
                            if end < len(text) and text[end] == "*":
                                continue
                        # Skip allowlist marker lines: they MUST name old names
                        # to suppress Check 14 flags.
                        line_start = text.rfind("\n", 0, m.start()) + 1
                        line_end = text.find("\n", m.end())
                        if line_end == -1:
                            line_end = len(text)
                        line = text[line_start:line_end]
                        if ALLOWLIST_LINE_RE.search(line):
                            continue
                        lineno = text.count("\n", 0, m.start()) + 1
                        per_rename.setdefault(rename["old"], []).append((rel, lineno))
                        total_hits += 1

    if total_hits == 0:
        print("✅ No references to historically-renamed identifiers found")
        return 0

    print(f"⚠️  Found {total_hits} reference(s) to historically-renamed identifiers:")
    print()
    for rename in renames:
        hits = per_rename.get(rename["old"], [])
        if not hits:
            continue
        new = rename["new"]
        since = rename.get("since", "?")
        reason = rename.get("reason", "")
        print(f"  `{rename['old']}` → `{new}` (since {since})")
        if reason and not summary_only:
            print(f"    Reason: {reason}")
        if summary_only:
            print(f"    Hits: {len(hits)}")
        else:
            for rel, lineno in hits[:5]:
                print(f"    {rel}:{lineno}")
            if len(hits) > 5:
                print(f"    +{len(hits) - 5} more")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
