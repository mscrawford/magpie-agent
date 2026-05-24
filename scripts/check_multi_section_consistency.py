#!/usr/bin/env python3
"""Check 23 — verify within-doc consistency of variable dimensions.

Closes R4 Lens 1 finding (M14 pcm_tau stragglers): when a doc updates a
variable's dimensions in one section after a rename but leaves stale signatures
in other sections, this check flags the divergence.

Scans each `modules/module_*.md` for backticked variable references with
parenthesized dimensions (e.g. `pcm_tau(j,"crop")`). Code blocks are stripped
first — they may legitimately quote verbatim GAMS source from non-default
realizations or unfixed files. For each variable, all distinct normalized
dimension signatures in prose text are compared. >1 distinct signature → flag.

Normalization (applied before comparing signatures, to suppress false positives
from legitimate variation):
  - whitespace within dim list is collapsed
  - quote variant unified (`"crop"` and `'crop'` → `"crop"`)
  - set aliases collapsed: j/j2/j3/j4 → j; i/i2/i3/i4 → i; h/h2/h3/h4 → h;
    cell/cell2 → cell; supreg/supreg2 → supreg
  - quoted literals normalized to `<lit>` placeholder (so `("crop")` and
    `("pasture")` are treated as same shape, but `("crop")` vs `(kcr)` still
    differ — set-name vs literal is meaningful)

This catches the M14 pcm_tau pattern where the SET NAME changed (h→j) on
rename but stragglers used the wrong set. It does NOT flag legitimate
variation like `vm_prod(j,k)` vs `vm_prod(j,kcr)` (here k is a parent set
of kcr — still flagged but at lower confidence).

Usage: python3 check_multi_section_consistency.py [--verbose]
Exit: 0 always (advisory)
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"


def load_allowlist() -> set[tuple[str, str]]:
    """Return set of (file, key) tuples allowlisted for this checker."""
    if not ALLOWLIST_PATH.exists():
        return set()
    with ALLOWLIST_PATH.open() as f:
        data = json.load(f)
    return {
        (entry["file"], entry["key"])
        for entry in data.get("allowlist", [])
        if entry.get("check") == "check_multi_section_consistency"
    }

# Backticked GAMS-style variable with dimensions:
#   `vm_land(j,land)`
#   `pcm_tau(j2, "crop")`
# Allows the same prefixes as DOC_VAR_RE in check_gams_variables.py.
VAR_WITH_DIMS_RE = re.compile(
    r"`((?:vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_|sm_|cm_"
    r"|v\d+_|p\d+_|f\d+_|i\d+_|s\d+_|c\d+_|ic\d+_|oq\d+_|ov\d+_)"
    r"[a-zA-Z0-9_]+[a-zA-Z0-9])\s*\(([^)]+)\)`"
)

CODE_FENCE_RE = re.compile(r"^\s*```")


# Set-alias map: j, j2, j3, j4 → j (and similar for i, h, cell, supreg).
# These aliases are interchangeable in GAMS index contexts; the choice is
# usually about avoiding name collisions in nested sums, not a semantic
# distinction. Comparing without normalization would false-positive.
_ALIAS_RE = re.compile(r"\b(j|i|h|cell|supreg|t)\d+\b")


def normalize_dims(dims: str) -> str:
    """Collapse whitespace, unify quotes, collapse set aliases, mask literals.

    Steps:
      1. Whitespace removed
      2. Quotes unified to `"`
      3. Aliases collapsed: `j2` → `j`, `i2` → `i`, etc.
      4. Quoted literals replaced with `<lit>` placeholder so multiple distinct
         literal values for the same slot don't fragment the signature
    """
    s = dims.replace("'", '"')
    s = re.sub(r"\s+", "", s)
    s = _ALIAS_RE.sub(r"\1", s)
    s = re.sub(r'"[^"]*"', "<lit>", s)
    return s


def strip_code_blocks(text: str) -> str:
    """Replace lines inside ``` fences with blank lines to preserve lineno."""
    out_lines = []
    in_block = False
    for line in text.splitlines():
        if CODE_FENCE_RE.match(line):
            in_block = not in_block
            out_lines.append("")  # also drop the fence line itself
            continue
        out_lines.append("" if in_block else line)
    return "\n".join(out_lines)


def check_doc(doc_path: Path) -> list[tuple[str, str, dict[str, list[int]]]]:
    """Return findings: (doc_name, var_name, {dim_sig: [linenos]}).

    Only emits when a var has >1 distinct normalized dim signature outside
    code blocks.
    """
    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    stripped = strip_code_blocks(text)

    # var_name → dim_sig → [linenos]
    sigs: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for m in VAR_WITH_DIMS_RE.finditer(stripped):
        var = m.group(1)
        dims = m.group(2)
        sig = normalize_dims(dims)
        lineno = stripped.count("\n", 0, m.start()) + 1
        sigs[var][sig].append(lineno)

    findings = []
    for var, dim_map in sigs.items():
        if len(dim_map) > 1:
            findings.append((doc_path.name, var, dict(dim_map)))
    return findings


def classify_findings(
    all_findings: list[tuple[str, str, dict[str, list[int]]]],
) -> tuple[list, list]:
    """Split into (arity_mismatches, signature_variants).

    Arity mismatches are higher-confidence drift signals (literally a different
    number of dimensions). Signature variants are same-arity differences and
    are usually legitimate context variation (subset vs parent set, literal
    vs set placeholder).

    Convention-suppression: signatures containing `...` (ellipsis abbreviation),
    `t-1`/`t+1` (pedagogical time annotations), or only literals like `(<lit>)`
    are docs-only conventions, NOT real arity changes. These are excluded from
    arity-mismatch consideration.
    """
    def is_convention(sig: str) -> bool:
        if "..." in sig:
            return True
        if "t-1" in sig or "t+1" in sig or "ct-1" in sig:
            return True
        # Pure-literal signatures like (<lit>) are partial-reference shorthand
        if re.fullmatch(r"\(<lit>(?:,<lit>)*\)", sig):
            return True
        return False

    arity_findings = []
    sig_findings = []
    for doc_name, var, dim_map in all_findings:
        non_convention_sigs = {s: l for s, l in dim_map.items() if not is_convention(s)}
        # If after dropping conventions, only one signature remains → not a real conflict
        if len(non_convention_sigs) <= 1:
            continue
        arities = {sig.count(",") + 1 for sig in non_convention_sigs}
        if len(arities) > 1:
            arity_findings.append((doc_name, var, non_convention_sigs))
        else:
            sig_findings.append((doc_name, var, non_convention_sigs))
    return arity_findings, sig_findings


def main() -> int:
    args = sys.argv[1:]
    verbose = "--verbose" in args
    summary_only = "--summary-only" in args

    if not DOCS_DIR.is_dir():
        print(f"⚠️  Module docs dir not found at {DOCS_DIR} - skipping consistency check")
        return 0

    print("Multi-section dimension consistency check")
    print("==========================================")

    allowlist = load_allowlist()
    docs_scanned = 0
    all_findings: list[tuple[str, str, dict[str, list[int]]]] = []
    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        if doc.name.endswith("_notes.md"):
            continue
        docs_scanned += 1
        all_findings.extend(check_doc(doc))

    arity_findings, sig_findings = classify_findings(all_findings)

    # Filter allowlisted entries (apply to arity findings — the actionable tier).
    allowlisted_count = 0
    if allowlist:
        filtered_arity = []
        for doc_name, var, dim_map in arity_findings:
            rel = f"modules/{doc_name}"
            if (rel, var) in allowlist:
                allowlisted_count += 1
                continue
            filtered_arity.append((doc_name, var, dim_map))
        arity_findings = filtered_arity

    print(f"Module docs scanned: {docs_scanned}")
    print(f"Arity mismatches (likely drift): {len(arity_findings)}")
    print(f"Signature variants (same arity, different set/literal — usually OK): {len(sig_findings)}")
    if allowlisted_count:
        print(f"Allowlisted (suppressed via audit/advisory_allowlist.json): {allowlisted_count}")
    print()

    if not all_findings:
        print("✅ All variable dimensions consistent within each module doc")
        return 0

    if not arity_findings and not sig_findings:
        print("✅ All variable dimensions consistent (after applying allowlist)")
        return 0

    if arity_findings:
        print(f"⚠️  {len(arity_findings)} arity mismatch(es) — these are likely drift:")
        print()
        for doc_name, var, dim_map in sorted(arity_findings):
            print(f"  {doc_name}: `{var}` has {len(dim_map)} distinct arities:")
            for sig, linenos in sorted(dim_map.items(), key=lambda kv: -len(kv[1])):
                lines_str = ", ".join(str(l) for l in linenos[:5])
                if len(linenos) > 5:
                    lines_str += f", +{len(linenos) - 5} more"
                print(f"    ({sig})  lines: {lines_str}")
        print()

    if sig_findings and not summary_only:
        print(f"ℹ️  {len(sig_findings)} signature variant(s) — usually legitimate context variation:")
        if verbose:
            for doc_name, var, dim_map in sorted(sig_findings):
                print(f"  {doc_name}: `{var}` has {len(dim_map)} distinct signatures:")
                for sig, linenos in sorted(dim_map.items(), key=lambda kv: -len(kv[1])):
                    lines_str = ", ".join(str(l) for l in linenos[:5])
                    if len(linenos) > 5:
                        lines_str += f", +{len(linenos) - 5} more"
                    print(f"    ({sig})  lines: {lines_str}")
        else:
            print("  (re-run with --verbose to list; usually subset/literal/alias variants)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
