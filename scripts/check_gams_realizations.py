#!/usr/bin/env python3
"""Check 16 (Python rewrite of check_gams_realizations.sh).

Validates realization names cited in AI documentation against actual
realization subdirectories under `../modules/NN_name/`. Builds the directory
index once, then checks each doc reference via O(1) set lookup.

Usage: python3 check_gams_realizations.py [--summary-only]
Exit:
  0 if all references verified (or GAMS code absent)
  1 if mismatches found
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_DIR = AGENT_DIR.parent

# Realization-name pattern: lowercase word(s)_monthYY[YY]
# Examples: endo_apr13, sticky_feb18, pot_forest_may24
REAL_RE = re.compile(
    r"\b[a-z][a-z_]+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{2}\b"
)

# Realizations that legitimately refer to old/removed realizations in
# historical/comparative text.
ALLOWLIST = {
    "anthropometrics_jan18",
    "substitution_dec18",
    "price_jan20",
    "fbask_jan16",
}


def build_realization_index() -> set[str]:
    """Return set of actual realization-directory names under ../modules."""
    index: set[str] = set()
    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        return index
    for module_dir in modules_root.iterdir():
        if not module_dir.is_dir():
            continue
        for child in module_dir.iterdir():
            if not child.is_dir():
                continue
            if child.name in ("input", ".git"):
                continue
            index.add(child.name)
    return index


def main() -> int:
    summary_only = "--summary-only" in sys.argv

    if not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS modules not found at {MAGPIE_DIR} - skipping realization verification")
        return 0

    real_dirs = build_realization_index()

    docs_dir = AGENT_DIR / "modules"
    if not docs_dir.is_dir():
        print("⚠️  Module docs dir not found - nothing to check")
        return 0

    # Collect unique (doc, realization) pairs to mirror the bash version.
    # _notes.md files are included (bash version scanned them too).
    pairs: set[tuple[str, str]] = set()
    for doc in sorted(docs_dir.glob("module_*.md")):
        text = doc.read_text(encoding="utf-8", errors="ignore")
        for name in set(REAL_RE.findall(text)):
            pairs.add((doc.name, name))

    total = len(pairs)
    verified = 0
    mismatches: list[tuple[str, str]] = []
    for doc, name in sorted(pairs):
        if name in ALLOWLIST or name in real_dirs:
            verified += 1
            continue
        mismatches.append((doc, name))

    if mismatches:
        print(f"Realization check: {len(mismatches)} mismatches found")
        if not summary_only:
            for doc, name in mismatches:
                print(f"  ❌ {name} (in {doc})")
        return 1

    print(f"Realization names verified: Accuracy: 100% ({verified}/{total} references)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
