#!/usr/bin/env python3
"""Check 14: GAMS variable name verification.

Validates GAMS variable names cited in AI documentation against the actual
GAMS codebase. Single-pass index build + O(1) set lookup replaces the bash
version's nested per-variable grep loop (was ~47s of total validator time).

Usage: python3 check_gams_variables.py [--summary-only] [--module N]
Exit:
  0 if all references verified (or GAMS code absent)
  1 if mismatches found
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_DIR = AGENT_DIR.parent

DOCS_DIR = AGENT_DIR / "modules"

# Interface / numbered / scalar GAMS identifier regexes.
GAMS_INTERFACE_RE = re.compile(
    r"\b(?:vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_|sm_|cm_)[a-zA-Z0-9_]+[a-zA-Z0-9]"
)
GAMS_NUMBERED_RE = re.compile(
    # R3 (2026-05-23): extended to cover module-numbered ic\d+_, oq\d+_, ov\d+_
    # prefixes (e.g., ic42_pumping_cost, ov56_*) which were previously
    # uncheckable due to single-char [vpfisc] class.
    # 2026-05-24: pc\d+_ added — carry-over from previous timestep (e.g.
    # pc35_secdforest_natural). Surfaced on PR #876.
    r"\b(?:ic\d+_|oq\d+_|ov\d+_|pc\d+_|[vpfisc]\d+_)[a-zA-Z0-9_]+[a-zA-Z0-9]"
)
GAMS_CORE_SCALAR_RE = re.compile(r"\bs_[a-zA-Z0-9_]+[a-zA-Z0-9]")

DOC_VAR_RE = re.compile(
    r"`((?:vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_|sm_|cm_"
    r"|ic\d+_|oq\d+_|ov\d+_|pc\d+_"
    r"|v\d+_|p\d+_|f\d+_|i\d+_|s\d+_|c\d+_|s_)[a-zA-Z0-9_]+[a-zA-Z0-9])"
)

# Per-doc allowlist via magic comment, e.g.
#   <!-- check-gams-vars: allow im_gdp_pc_ppp, vm_foo -->
PER_DOC_ALLOW_RE = re.compile(
    r"<!--\s*check-gams-vars:\s*allow\s+([^>]+?)\s*-->"
)
# I4 (2026-05-24): loose pattern that catches typo variants (underscore
# instead of dash, missing colon, missing space, etc.). When this matches but
# the strict regex does not, the marker is silently failing — emit a WARNing.
PER_DOC_ALLOW_LOOSE_RE = re.compile(
    r"<!--[^>]*?\bcheck[-_]?gams[-_]?vars\b[^>]*?\ballow\b[^>]*?-->",
    re.IGNORECASE,
)

# Template-style placeholder: var_<type>, var_{type}, var_%type%, var_$type
TEMPLATE_SUFFIX_CHARS = "<{%$"

ALLOWLIST = {"vm_prod_calibrated", "vm_prod_initial"}


def iter_files(path: Path):
    """Yield all files under a path (or the path itself if a single file)."""
    if path.is_file():
        yield path
        return
    if not path.is_dir():
        return
    # Use os.walk to avoid loading the entire glob list eagerly.
    for root, _dirs, files in os.walk(path):
        for name in files:
            yield Path(root) / name


def read_text_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# File extensions worth scanning for GAMS identifiers.
# .gms/.cfg/.inc are the obvious carriers; .R is included because some helper
# scripts reference variable names too. Skips binary inputs (.gdx, .mz) and
# data tables (.csv, .cs2-cs4) which never define new identifiers.
SCANNABLE_EXTS = {".gms", ".cfg", ".inc", ".R", ".r"}


def file_is_scannable(path: Path) -> bool:
    return path.suffix in SCANNABLE_EXTS or path.name in {"main.gms", "default.cfg"}


def build_gams_index() -> set[str]:
    """Scan GAMS sources once; return set of variable names.

    Single-pass per file: each file's text is read once and all three regexes
    are applied to it. Skips binary/data files via SCANNABLE_EXTS.
    """
    index: set[str] = set()

    interface_sources = [
        (MAGPIE_DIR / "modules", True, True, True),   # iface + numbered + core_scalar
        (MAGPIE_DIR / "core", True, False, True),     # iface + core_scalar
        (MAGPIE_DIR / "main.gms", True, False, False),
        (MAGPIE_DIR / "config" / "default.cfg", True, False, False),
    ]

    for root, want_iface, want_numbered, want_core_scalar in interface_sources:
        for f in iter_files(root):
            if not file_is_scannable(f):
                continue
            text = read_text_or_empty(f)
            if not text:
                continue
            if want_iface:
                index.update(GAMS_INTERFACE_RE.findall(text))
            if want_numbered:
                index.update(GAMS_NUMBERED_RE.findall(text))
            if want_core_scalar:
                index.update(GAMS_CORE_SCALAR_RE.findall(text))
    return index


def filter_doc_vars(text: str, doc_vars: set[str], per_doc_allow: set[str]) -> list[str]:
    """Apply allowlist / placeholder / wildcard / template skip logic.

    Returns the names that should still be checked against the GAMS index.
    """
    out = []
    for var in sorted(doc_vars):
        if var in ALLOWLIST or var in per_doc_allow:
            continue
        if "_X_" in var or "_type_" in var:
            continue
        # Wildcard context: literal substring match (`var*`, `var_*`, var_\*).
        if f"{var}*" in text or f"{var}_*" in text:
            continue
        # Template-style placeholder: var followed by `_<…>`, `_{…}`, etc.
        # (e.g., `f57_maccs_<type>` makes `f57_maccs` a stem, not a real var).
        if any(f"{var}_{ch}" in text for ch in TEMPLATE_SUFFIX_CHARS):
            continue
        out.append(var)
    return out


def collect_per_doc_allow(text: str) -> set[str]:
    """Return per-doc allowlisted names from `<!-- check-gams-vars: allow ... -->` markers."""
    out: set[str] = set()
    for m in PER_DOC_ALLOW_RE.finditer(text):
        for name in m.group(1).split(","):
            name = name.strip()
            if name:
                out.add(name)
    return out


def find_typo_allow_markers(text: str) -> list[str]:
    """Return loose-match marker strings that fail the strict allow regex.

    I4 (2026-05-24): catches typo variants of the per-doc allowlist marker
    that silently fail the strict regex. Returns the raw marker substring
    so callers can show it in WARNings.
    """
    typos = []
    for lm in PER_DOC_ALLOW_LOOSE_RE.finditer(text):
        raw = lm.group(0)
        if not PER_DOC_ALLOW_RE.search(raw):
            typos.append(raw)
    return typos


def self_test() -> int:
    """Positive-control self-test using a self-contained temp fixture.

    Asserts:
      1. A doc citing a fabricated variable (``vm_NOTREAL``) that is absent from
         the GAMS declarations IS flagged as a mismatch.
      2. A doc citing a declared variable (``vm_real``) is NOT flagged.
      3. An EMPTY GAMS index + empty doc produces 0 doc vars — the check is
         vacuously green, which is the known silent-failure mode.  We surface
         this explicitly (does NOT cause a FAIL — but is printed as a WARNING so
         callers can see it; addressed by ensuring the fixture above is non-empty).

    The test builds its index by applying the same regexes used by
    build_gams_index() to a synthetic in-memory GAMS text — so a regression that
    breaks the regex-based detection would also break the self-test.
    """
    import tempfile

    ok = True
    print("check_gams_variables self-test")
    print("------------------------------")

    # --- Build a synthetic GAMS index from fixture text (same regex path as
    #     build_gams_index, no real tree required).
    fixture_gams_text = (
        "Variables\n"
        "  vm_real(j,i)  'a real declared variable'\n"
        ";\n"
        "Positive Variables vm_real;\n"
    )
    gams_index: set[str] = set()
    gams_index.update(GAMS_INTERFACE_RE.findall(fixture_gams_text))
    gams_index.update(GAMS_NUMBERED_RE.findall(fixture_gams_text))
    gams_index.update(GAMS_CORE_SCALAR_RE.findall(fixture_gams_text))

    if "vm_real" not in gams_index:
        print("  SELF-TEST FAIL: fixture GAMS text did not index vm_real")
        ok = False
    else:
        print("  [index build] vm_real indexed from fixture: OK")

    # --- Positive-control: doc cites vm_NOTREAL (fabricated) — must be flagged.
    doc_flag_text = (
        "## Section\n"
        "The variable `vm_NOTREAL` is used here.\n"
    )
    per_doc_allow_flag = collect_per_doc_allow(doc_flag_text)
    doc_vars_flag = set(DOC_VAR_RE.findall(doc_flag_text))
    filtered_flag = filter_doc_vars(doc_flag_text, doc_vars_flag, per_doc_allow_flag)
    mismatches_flag = [v for v in filtered_flag if v not in gams_index]

    if "vm_NOTREAL" not in mismatches_flag:
        print("  SELF-TEST FAIL [positive-control]: vm_NOTREAL was NOT flagged — "
              "fabricated variable escaped detection")
        ok = False
    else:
        print("  [positive-control] vm_NOTREAL flagged as nonexistent: OK")

    # --- Clean control: doc cites vm_real (declared) — must NOT be flagged.
    doc_clean_text = (
        "## Section\n"
        "The variable `vm_real` handles this.\n"
    )
    per_doc_allow_clean = collect_per_doc_allow(doc_clean_text)
    doc_vars_clean = set(DOC_VAR_RE.findall(doc_clean_text))
    filtered_clean = filter_doc_vars(doc_clean_text, doc_vars_clean, per_doc_allow_clean)
    mismatches_clean = [v for v in filtered_clean if v not in gams_index]

    if mismatches_clean:
        print(f"  SELF-TEST FAIL [clean-control]: vm_real was wrongly flagged: "
              f"{mismatches_clean}")
        ok = False
    else:
        print("  [clean-control] vm_real not flagged (correctly passes): OK")

    # --- Vacuous-green check: empty GAMS index + empty doc → 0 vars checked.
    #     This is the known silent-failure mode (R8 finding I2 / R7-deferred):
    #     the check returns 0 on empty input, giving a confident green that proves
    #     nothing.  We surface it explicitly.  This does NOT fail the self-test
    #     (it is expected behaviour of the current code), but the print makes it
    #     visible so a future hardening pass can decide to exit non-zero on 0 vars.
    empty_gams_index: set[str] = set()
    empty_doc_text = ""
    empty_doc_vars = set(DOC_VAR_RE.findall(empty_doc_text))
    empty_filtered = filter_doc_vars(empty_doc_text, empty_doc_vars, set())
    empty_mismatches = [v for v in empty_filtered if v not in empty_gams_index]
    empty_total_vars = len(empty_filtered)
    if empty_total_vars == 0 and len(empty_mismatches) == 0:
        print("  [vacuous-green WARNING] empty GAMS index + empty doc → 0 vars "
              "checked, 0 mismatches — check would report confident green that "
              "proves nothing. (Not a FAIL; surfaced for awareness.)")
    else:
        print(f"  [vacuous-green] unexpected: vars={empty_total_vars}, "
              f"mismatches={len(empty_mismatches)}")

    print()
    print(f"SELF-TEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()

    summary_only = "--summary-only" in sys.argv
    target_module = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--module" and i + 1 < len(args):
            target_module = args[i + 1]

    if not (MAGPIE_DIR / "main.gms").is_file() or not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS codebase not found at {MAGPIE_DIR} - skipping variable verification")
        return 0

    gams_index = build_gams_index()

    print("GAMS Variable Name Verification")
    print("================================")
    print(f"GAMS codebase variables: {len(gams_index)}")

    total_doc_vars = 0
    total_mismatches = 0
    modules_checked = 0
    per_doc_mismatches: list[tuple[str, str]] = []
    typo_markers: list[tuple[str, str]] = []  # (doc.name, raw_marker)

    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        m = re.match(r"^module_(\d+)\.md$", doc.name)
        if not m:
            continue
        if target_module and m.group(1) != target_module:
            continue
        modules_checked += 1
        text = doc.read_text(encoding="utf-8", errors="ignore")
        doc_vars = set(DOC_VAR_RE.findall(text))
        per_doc_allow = collect_per_doc_allow(text)
        for typo in find_typo_allow_markers(text):
            typo_markers.append((doc.name, typo))
        filtered = filter_doc_vars(text, doc_vars, per_doc_allow)
        total_doc_vars += len(filtered)
        for var in filtered:
            if var not in gams_index:
                per_doc_mismatches.append((doc.name, var))
                total_mismatches += 1

    print(f"AI doc variable references: {total_doc_vars} (across {modules_checked} modules)")
    print()

    if typo_markers:
        print(f"⚠️  Found {len(typo_markers)} likely typo'd allowlist marker(s) (silently failing):")
        for doc, raw in sorted(set(typo_markers)):
            preview = raw if len(raw) < 100 else raw[:97] + "..."
            print(f"  {doc}: {preview}")
            print(f"    → expected format: <!-- check-gams-vars: allow NAME[,NAME...] -->")
        print()

    if total_mismatches == 0:
        print("✅ All variable references verified against GAMS code")
    else:
        print(f"❌ Found {total_mismatches} variable(s) in docs not found in GAMS code:")
        print()
        if summary_only:
            counts = Counter(d for d, _ in per_doc_mismatches)
            for doc, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                print(f"  {doc}: {n} mismatches")
        else:
            for doc, var in sorted(per_doc_mismatches):
                print(f"  {doc}: {var}")

    if total_doc_vars > 0:
        accuracy = (total_doc_vars - total_mismatches) * 100 // total_doc_vars
        print()
        print(f"Accuracy: {accuracy}% ({total_doc_vars - total_mismatches}/{total_doc_vars} verified)")

    if total_mismatches > 0:
        print()
        print("Common error patterns:")
        print("  - Wrong prefix: vm_ vs v{N}_, pm_ vs p{N}_, fm_ vs f{N}_, pm_ vs s{N}_")
        print("  - Suffix truncation: missing _ac, _iso, _reg suffixes")
        print("  - Invented names: plausible but non-existent variables (especially in advisory text)")
        print("  - Conceptual pseudo-code: annotate with '(conceptual, not actual GAMS)'")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
