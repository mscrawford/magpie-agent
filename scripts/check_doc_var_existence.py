#!/usr/bin/env python3
"""Check 21 — verify GAMS-identifier-shaped tokens in cross-cutting docs exist.

Closes R3 Cluster 2 (fabricated identifiers in backticked prose) for the
NON-module docs that Check 14 (check_gams_variables.py) does not scan:

  cross_module/*.md   (system-level docs: conservation laws, safety guide, etc.)
  core_docs/*.md      (architecture: Module_Dependencies, Data_Flow, etc.)

R3 surfaced `pm_timber_yield` in core_docs/Module_Dependencies.md:230 as a
fabricated identifier that Check 14 missed because that file is outside its
scope. This check fills that gap.

Logic reuses check_gams_variables.py:
  - same DOC_VAR_RE for extracting candidate identifiers
  - same build_gams_index() for the canonical set of real GAMS identifiers
  - same allowlist + filter logic (PER_DOC_ALLOW_RE, template suffixes, wildcards)

Module docs (modules/module_*.md) are explicitly NOT scanned — Check 14 owns
that scope. Scanning them here would be redundant.

Usage: python3 check_doc_var_existence.py [--summary-only] [--self-test]
Exit: 0 always (advisory; mismatches surface via output text)
       --self-test: exits 1 on assertion failure (positive control)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Reuse from sibling Check 14 — single source of truth for regex + index logic.
from check_gams_variables import (  # noqa: E402
    DOC_VAR_RE,
    MAGPIE_DIR,
    build_gams_index,
    collect_per_doc_allow,
    filter_doc_vars,
)

AGENT_DIR = SCRIPT_DIR.parent
SCAN_DIRS = [
    AGENT_DIR / "cross_module",
    AGENT_DIR / "core_docs",
    AGENT_DIR / "agent" / "helpers",
    AGENT_DIR / "agent" / "commands",
    AGENT_DIR / "reference",  # R5 2026-05-24: closed FN gap — 19 fabricated identifiers found in reference/ during R5 audit
]


def self_test() -> int:
    """Positive-control self-test on a synthetic fixture (no real tree touched).

    Exercises the core check loop directly so that a vacuous-green path (0 refs
    scanned) is distinguishable from a genuine clean run.  Addresses R8-I2 /
    R7-deferred: the main success string "All identifier references verified"
    was printed regardless of whether any identifiers were actually scanned.

    Assertions:
      1. POSITIVE CONTROL — a doc referencing `vm_fabricated_xyz` (absent from
         the fixture GAMS index) must be flagged as a mismatch.
      2. CLEAN CONTROL — a doc referencing only `vm_real` (present in the
         fixture GAMS index) must pass, AND the ref count must be > 0 (proving
         the scan was non-vacuous).
    """
    ok = True

    # Tiny fixture GAMS index — stands in for build_gams_index() on the real tree.
    fixture_gams_index: set[str] = {"vm_real"}

    # --- Assertion 1: positive control ---
    # A cross-cutting doc that mentions a fabricated identifier must be flagged.
    doc_bad = "The `vm_fabricated_xyz` variable is critical for land conservation."
    doc_vars_bad = set(DOC_VAR_RE.findall(doc_bad))
    per_doc_allow_bad = collect_per_doc_allow(doc_bad)
    filtered_bad = filter_doc_vars(doc_bad, doc_vars_bad, per_doc_allow_bad)
    mismatches_bad = [v for v in filtered_bad if v not in fixture_gams_index]
    if mismatches_bad != ["vm_fabricated_xyz"]:
        print(f"  check_doc_var_existence SELF-TEST FAIL [1-positive]: "
              f"expected ['vm_fabricated_xyz'] flagged, got {mismatches_bad}")
        ok = False
    else:
        print("  check_doc_var_existence SELF-TEST [1-positive]: PASS "
              "(vm_fabricated_xyz correctly flagged)")

    # --- Assertion 2: clean control — must pass AND ref count must be > 0 ---
    # A doc referencing only a real identifier must produce 0 mismatches on a
    # NON-empty scan (distinguishes genuine clean from vacuous 0-ref scan).
    doc_good = "The `vm_real` variable tracks land use across modules."
    doc_vars_good = set(DOC_VAR_RE.findall(doc_good))
    per_doc_allow_good = collect_per_doc_allow(doc_good)
    filtered_good = filter_doc_vars(doc_good, doc_vars_good, per_doc_allow_good)
    ref_count = len(filtered_good)
    mismatches_good = [v for v in filtered_good if v not in fixture_gams_index]
    if ref_count == 0:
        print("  check_doc_var_existence SELF-TEST FAIL [2-clean]: "
              "ref count is 0 — scan was vacuous (vm_real not extracted from doc fixture)")
        ok = False
    elif mismatches_good:
        print(f"  check_doc_var_existence SELF-TEST FAIL [2-clean]: "
              f"vm_real wrongly flagged as mismatch: {mismatches_good}")
        ok = False
    else:
        print(f"  check_doc_var_existence SELF-TEST [2-clean]: PASS "
              f"(verified {ref_count} ref(s), 0 mismatches — non-vacuous)")

    print(f"check_doc_var_existence self-test: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()

    summary_only = "--summary-only" in sys.argv

    if not (MAGPIE_DIR / "main.gms").is_file() or not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS codebase not found at {MAGPIE_DIR} - skipping cross-doc verification")
        return 0

    gams_index = build_gams_index()

    print("Cross-cutting doc identifier existence check")
    print("=============================================")
    print(f"GAMS codebase variables: {len(gams_index)}")
    print(f"Scopes scanned: {', '.join(p.name for p in SCAN_DIRS)}")

    total_refs = 0
    total_mismatches = 0
    docs_checked = 0
    mismatches: list[tuple[str, str]] = []

    for scan_dir in SCAN_DIRS:
        if not scan_dir.is_dir():
            continue
        for doc in sorted(scan_dir.glob("*.md")):
            docs_checked += 1
            text = doc.read_text(encoding="utf-8", errors="ignore")
            doc_vars = set(DOC_VAR_RE.findall(text))
            per_doc_allow = collect_per_doc_allow(text)
            filtered = filter_doc_vars(text, doc_vars, per_doc_allow)
            total_refs += len(filtered)
            for var in filtered:
                if var not in gams_index:
                    rel = doc.relative_to(AGENT_DIR)
                    mismatches.append((str(rel), var))
                    total_mismatches += 1

    print(f"Doc identifier references: {total_refs} (across {docs_checked} docs)")
    print()

    if total_mismatches == 0:
        print("✅ All identifier references verified against GAMS code")
    else:
        print(f"⚠️  Found {total_mismatches} identifier(s) in cross-cutting docs not in GAMS code:")
        print()
        if summary_only:
            from collections import Counter

            counts = Counter(d for d, _ in mismatches)
            for doc, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                print(f"  {doc}: {n} mismatches")
        else:
            for doc, var in sorted(mismatches):
                print(f"  {doc}: {var}")

    if total_refs > 0:
        ok = total_refs - total_mismatches
        accuracy = ok * 100 // total_refs
        print()
        print(f"Accuracy: {accuracy}% ({ok}/{total_refs} verified)")

    # Advisory: always exit 0. Mismatches surface in output.
    return 0


if __name__ == "__main__":
    sys.exit(main())
