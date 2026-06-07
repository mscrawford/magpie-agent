#!/usr/bin/env python3
"""Check 15: GAMS equation name verification.

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


def build_equation_index(modules_root=None) -> set[str]:
    """Scan all .gms files under modules_root and return the set of equation names.

    modules_root overrides ``../modules`` (used only by --self-test; real-tree
    behaviour is unchanged when None).
    """
    index: set[str] = set()
    root = modules_root if modules_root is not None else (MAGPIE_DIR / "modules")
    if not root.is_dir():
        return index
    for path in root.rglob("*.gms"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        index.update(GAMS_EQ_RE.findall(text))
    return index


def find_doc_eq_mismatches(gams_eqns, docs_dir):
    """Return (mismatches, unique_total) for equation refs in docs_dir/module_*.md.

    A doc ref absent from gams_eqns and not in ALLOWLIST is a mismatch
    (list of (doc_name, equation) tuples). Factored out of main() so --self-test
    can drive it on a synthetic fixture.
    """
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
    return mismatches, len(unique_refs)


def self_test() -> int:
    """Positive + clean controls on a synthetic temp tree (real tree untouched).

    Synthesize the known bug FIRST, then assert the check flags it:
      Positive: a fake .gms defines q99_real; module_99.md cites q99_fake
                (absent from source) -> q99_fake must be flagged, q99_real not.
      Clean:    module_99.md cites only q99_real -> nothing flagged.
    Exits 0 (prints SELFTEST_OK) iff both hold; 1 otherwise.
    """
    import shutil
    import tempfile

    ok = True
    tmp = Path(tempfile.mkdtemp(prefix="check15_selftest_"))
    try:
        mdir = tmp / "modules" / "99_testmod" / "default"
        mdir.mkdir(parents=True)
        (mdir / "equations.gms").write_text(
            "q99_real(i) .. v99_x(i) =e= v99_y(i);\n", encoding="utf-8"
        )
        gams_eqns = build_equation_index(tmp / "modules")
        if "q99_real" not in gams_eqns:
            print(f"  SELF-TEST FAIL: fixture index missed q99_real: {sorted(gams_eqns)}")
            ok = False

        docs = tmp / "docs"
        docs.mkdir()
        doc = docs / "module_99.md"

        doc.write_text("Equation `q99_fake` does X; see also `q99_real`.\n", encoding="utf-8")
        mm, total = find_doc_eq_mismatches(gams_eqns, docs)
        names = {eq for _doc, eq in mm}
        if "q99_fake" in names and "q99_real" not in names:
            print(f"  SELF-TEST PASS [positive]: q99_fake flagged ({len(mm)} mismatch, {total} refs)")
        else:
            print(f"  SELF-TEST FAIL [positive]: expected only q99_fake flagged; got {sorted(names)}")
            ok = False

        doc.write_text("Only the real equation `q99_real` is cited here.\n", encoding="utf-8")
        mm_clean, _ = find_doc_eq_mismatches(gams_eqns, docs)
        if not mm_clean:
            print("  SELF-TEST PASS [clean]: doc citing only q99_real not flagged")
        else:
            print(f"  SELF-TEST FAIL [clean]: clean doc wrongly flagged: {mm_clean}")
            ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("check_gams_equations self-test: PASS")
        print("SELFTEST_OK check_gams_equations")
        return 0
    print("check_gams_equations self-test: FAIL")
    return 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()

    summary_only = "--summary-only" in sys.argv

    if not (MAGPIE_DIR / "main.gms").is_file() or not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS codebase not found at {MAGPIE_DIR} - skipping equation verification")
        return 0

    gams_eqns = build_equation_index()

    docs_dir = AGENT_DIR / "modules"
    if not docs_dir.is_dir():
        print("⚠️  Module docs dir not found - nothing to check")
        return 0

    mismatches, unique_total = find_doc_eq_mismatches(gams_eqns, docs_dir)
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
