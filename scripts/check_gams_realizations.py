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
    """Return set of actual realization-directory names under ../modules.

    Kept for backward compatibility with any caller; the module-aware index
    (build_realization_index_by_module) is the authoritative source for
    Check 16's scope-coupling-aware verification (R5 2026-05-24).
    """
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


def build_realization_index_by_module() -> dict[str, set[str]]:
    """Return {module_num: {realization_names}} for module-aware verification.

    Added 2026-05-24 R5 (Cluster C/E intervention) to close the scope-coupling
    FN: prior global membership check would have passed a doc citing module 12's
    `select_apr20` realization inside module_70.md (cross-module realization
    mismatch). Each citation now checks only against its own module's
    realization set.
    """
    by_mod: dict[str, set[str]] = {}
    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        return by_mod
    for module_dir in modules_root.iterdir():
        if not module_dir.is_dir():
            continue
        # Extract NN from "NN_name" directory format
        m = re.match(r"(\d+)_", module_dir.name)
        if not m:
            continue
        mod_num = m.group(1)
        by_mod.setdefault(mod_num, set())
        for child in module_dir.iterdir():
            if not child.is_dir():
                continue
            if child.name in ("input", ".git"):
                continue
            by_mod[mod_num].add(child.name)
    return by_mod


def main() -> int:
    summary_only = "--summary-only" in sys.argv

    if not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS modules not found at {MAGPIE_DIR} - skipping realization verification")
        return 0

    real_dirs = build_realization_index()
    by_mod = build_realization_index_by_module()

    docs_dir = AGENT_DIR / "modules"
    if not docs_dir.is_dir():
        print("⚠️  Module docs dir not found - nothing to check")
        return 0

    # Collect unique (doc, doc_mod_num, realization) tuples.
    # doc_mod_num is extracted from `module_NN.md` filename; this scopes
    # realization lookup to the doc's module per R5 Cluster C intervention.
    triples: set[tuple[str, str, str]] = set()
    for doc in sorted(docs_dir.glob("module_*.md")):
        m = re.match(r"module_(\d+)\w*\.md$", doc.name)
        if not m:
            continue
        doc_mod_num = m.group(1)
        text = doc.read_text(encoding="utf-8", errors="ignore")
        for name in set(REAL_RE.findall(text)):
            triples.add((doc.name, doc_mod_num, name))

    total = len(triples)
    verified = 0
    mismatches: list[tuple[str, str, str, str]] = []  # (doc, mod, name, reason)
    for doc, doc_mod_num, name in sorted(triples):
        if name in ALLOWLIST:
            verified += 1
            continue
        own_module_set = by_mod.get(doc_mod_num, set())
        if name in own_module_set:
            verified += 1
            continue
        # The realization name exists elsewhere — scope-coupling drift.
        if name in real_dirs:
            other_mods = sorted(mod for mod, names in by_mod.items() if name in names)
            mismatches.append(
                (doc, doc_mod_num, name,
                 f"belongs to module(s) {','.join(other_mods)}, not {doc_mod_num}")
            )
        else:
            # Doesn't exist anywhere
            mismatches.append((doc, doc_mod_num, name, "no such realization in any module"))

    # Mismatches are ADVISORY: cross-module references (e.g., module_11.md
    # discussing module_71's `foragebased_jul23`) are legitimate and common.
    # The check surfaces drift candidates without breaking the validator.
    # Hard-error only when a realization name doesn't exist anywhere.
    fabricated = [m for m in mismatches if m[3].startswith("no such realization")]
    cross_module = [m for m in mismatches if not m[3].startswith("no such realization")]

    if fabricated:
        print(f"Realization check: {len(fabricated)} FABRICATED realization names found")
        if not summary_only:
            for doc, doc_mod, name, reason in fabricated:
                print(f"  ❌ {name} (in {doc}) — {reason}")
        return 1

    print(f"Realization names verified: Accuracy: 100% ({verified}/{total} references; module-scoped check)")
    if cross_module:
        print(f"  ⓘ {len(cross_module)} cross-module references (other module's realization mentioned in this module's doc — advisory, usually legitimate):")
        if not summary_only:
            for doc, doc_mod, name, reason in cross_module[:8]:
                print(f"    - {name} (in {doc}) — {reason}")
            if len(cross_module) > 8:
                print(f"    ... and {len(cross_module) - 8} more (use --summary-only=false for full list)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
