#!/usr/bin/env python3
"""Check 15 (Python rewrite of check_gams_equations.sh).

Validates GAMS equation-name references (`q\\d+_*` shape) in AI documentation
against actual equation names in the GAMS codebase. Single-pass index build +
O(1) set lookup replaces the bash version's `grep -qx` per-equation loop
(was ~3.8s of total validator time).

Usage: python3 check_gams_equations.py [--summary-only]
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

GAMS_EQ_RE = re.compile(r"\bq\d+_[a-zA-Z_]+[a-zA-Z]\b")
DOC_EQ_RE = re.compile(r"`(q\d+_[a-zA-Z_]+[a-zA-Z])\b")

# Conceptual equations explicitly annotated in docs (do not exist in source).
ALLOWLIST = {"q10_deforestation", "q10_urban_source"}


def build_equation_index() -> set[str]:
    """Scan all .gms files under ../modules and return the set of equation names."""
    index: set[str] = set()
    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        return index
    for path in modules_root.rglob("*.gms"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        index.update(GAMS_EQ_RE.findall(text))
    return index


def main() -> int:
    summary_only = "--summary-only" in sys.argv

    if not (MAGPIE_DIR / "main.gms").is_file() or not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS codebase not found at {MAGPIE_DIR} - skipping equation verification")
        return 0

    gams_eqns = build_equation_index()

    docs_dir = AGENT_DIR / "modules"
    if not docs_dir.is_dir():
        print("⚠️  Module docs dir not found - nothing to check")
        return 0

    seen_per_doc: dict[str, set[str]] = {}
    for doc in sorted(docs_dir.glob("module_*.md")):
        if doc.name.endswith("_notes.md"):
            continue
        text = doc.read_text(encoding="utf-8", errors="ignore")
        seen_per_doc[doc.name] = set(DOC_EQ_RE.findall(text))

    unique_refs: set[str] = set()
    mismatches: list[tuple[str, str]] = []
    for doc, eqns in seen_per_doc.items():
        for eq in eqns:
            unique_refs.add(eq)
            if eq in ALLOWLIST:
                continue
            if eq not in gams_eqns:
                mismatches.append((doc, eq))

    unique_total = len(unique_refs)
    mismatches.sort()

    if mismatches:
        if summary_only:
            print(f"Equation check: {len(mismatches)} mismatches found")
        else:
            print(f"Equation check: {len(mismatches)} mismatches found")
            for doc, eq in mismatches:
                print(f"  ❌ {eq} (in {doc})")
        return 1

    verified = unique_total - len(mismatches)
    print(f"Equation names verified: Accuracy: 100% ({verified}/{unique_total} unique equations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
