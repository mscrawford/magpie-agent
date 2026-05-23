#!/usr/bin/env python3
"""Check 14 (Python rewrite of check_gams_variables.sh).

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

# Same regexes as the bash version (kept in lockstep with check_gams_variables.sh).
GAMS_INTERFACE_RE = re.compile(
    r"\b(?:vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_|sm_|cm_)[a-zA-Z0-9_]+[a-zA-Z0-9]"
)
GAMS_NUMBERED_RE = re.compile(
    # R3 (2026-05-23): extended to cover module-numbered ic\d+_, oq\d+_, ov\d+_
    # prefixes (e.g., ic42_pumping_cost, ov56_*) which were previously
    # uncheckable due to single-char [vpfisc] class.
    r"\b(?:ic\d+_|oq\d+_|ov\d+_|[vpfisc]\d+_)[a-zA-Z0-9_]+[a-zA-Z0-9]"
)
GAMS_CORE_SCALAR_RE = re.compile(r"\bs_[a-zA-Z0-9_]+[a-zA-Z0-9]")

DOC_VAR_RE = re.compile(
    r"`((?:vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_|sm_|cm_"
    r"|ic\d+_|oq\d+_|ov\d+_"
    r"|v\d+_|p\d+_|f\d+_|i\d+_|s\d+_|c\d+_|s_)[a-zA-Z0-9_]+[a-zA-Z0-9])"
)

# Per-doc allowlist via magic comment, e.g.
#   <!-- check-gams-vars: allow im_gdp_pc_ppp, vm_foo -->
PER_DOC_ALLOW_RE = re.compile(
    r"<!--\s*check-gams-vars:\s*allow\s+([^>]+?)\s*-->"
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


def main() -> int:
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
        filtered = filter_doc_vars(text, doc_vars, per_doc_allow)
        total_doc_vars += len(filtered)
        for var in filtered:
            if var not in gams_index:
                per_doc_mismatches.append((doc.name, var))
                total_mismatches += 1

    print(f"AI doc variable references: {total_doc_vars} (across {modules_checked} modules)")
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
