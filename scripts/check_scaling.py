#!/usr/bin/env python3
"""check_scaling.py — flag doc GAMS .scale-value claims that disagree with scaling.gms.

Motivating bug class (R33-R37 doc sweep): docs repeatedly wrote a GAMS scaling
value as "10eN" (e.g. 10e4, 10e5) where the code is "1eN" (1e4, 1e5) — a 10x
magnitude error. It recurred in module_11/20/40/41/43/73 and is not caught by the
existing checkers (which verify names/equations/realizations/citations, not the
numeric value of a .scale assignment).

Strategy (mirrors check_units.py):
1. Canonical {identifier -> [(value_float, raw, file, line)]} from
   modules/*/*/scaling.gms lines `VAR.scale(...) = VALUE;` — ATOMIC numeric /
   scientific-notation values only; complex expressions (`1e3 * 100`) are skipped
   (conservative). Column-0 '*' comment lines are skipped (GAMS comment rule).
2. Doc claims {identifier -> [(file, line, raw, value_float)]} from
   modules/module_XX.md: on any line that mentions scaling, pair each
   scientific-notation token with its nearest preceding interface identifier.
3. Compare NUMERICALLY: flag a claim whose value matches NO canonical value for
   that identifier within 5% (so "10e4" vs canonical "1e4" -> flagged; "1e4" vs
   "1.0e4" -> ok; a value matching any realization's canonical -> ok).

Advisory by default (never fails the suite). --summary / --json / --self-test.

Usage:
    python3 scripts/check_scaling.py            # full check
    python3 scripts/check_scaling.py --summary  # one-line summary
    python3 scripts/check_scaling.py --json      # JSON for piping
    python3 scripts/check_scaling.py --self-test # synthetic known-bug test (exits 1 on failure)
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_DIR = AGENT_DIR.parent
MODULES_GMS = MAGPIE_DIR / "modules"
MODULE_DOCS = AGENT_DIR / "modules"

# Interface identifier (vm_/pm_/im_/vN_/.../fN_/iN_/qN_ etc.)
IDENT = r"(?:vm|pm|im|sm|cm|pcm|ov|oq|v|p|s|c|q|f|i)\d*_[a-z][\w]*"

# Canonical GAMS scaling line: VAR.scale(dims) = VALUE ;
CANON_RE = re.compile(rf"^\s*({IDENT})\.scale\s*(?:\([^)]*\))?\s*=\s*([^;]+);")
# Atomic numeric / scientific value (NOT an expression).
NUM_ATOMIC_RE = re.compile(r"^\s*(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*$")
# Scientific / power token to extract from doc prose (plain ints are ignored on
# purpose — "scaling.gms:8" must not read as a scale value of 8).
DOC_NUM = r"\d+(?:\.\d+)?[eE][+-]?\d+|\d+\s*\^\s*\d+"

# Doc claim: an identifier (optionally `.scale(dims)`/backticked), then within a
# few words a scaling connector (=, :, "scaled by", "scale factor of"...), then a
# scientific value. The bounded gap + required connector keep each identifier
# attached to ITS OWN value — so "variable scaled by 1e4 (10^4); the q43_water
# constraint is scaled by 1e2" does NOT mis-attribute the 1e4 to q43_water
# ("variable" is not an identifier token, so its 1e4 is correctly left unpaired).
DOC_CLAIM_RE = re.compile(
    rf"`?({IDENT})`?(?:\.scale)?(?:\([^)]*\))?[^\n]{{0,25}}?"
    rf"(?:=|:|scaled\s+by|scale(?:d)?(?:\s+factor)?(?:\s+of)?)\s*"
    rf"`?({DOC_NUM})`?",
    re.IGNORECASE,
)


def to_float(raw: str):
    raw = raw.strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*\^\s*(\d+)$", raw)  # 10^4 form
    if m:
        try:
            return float(m.group(1)) ** float(m.group(2))
        except Exception:
            return None
    try:
        return float(raw)
    except Exception:
        return None


def claims_in_line(line: str):
    """Extract (ident, raw, value_float) where an identifier is connected to a
    scientific value by a scaling connector, on a line that mentions scaling."""
    if "scal" not in line.lower():
        return []
    out = []
    for m in DOC_CLAIM_RE.finditer(line):
        ident, raw = m.group(1), m.group(2)
        f = to_float(raw)
        if f is None or f == 0:
            continue
        out.append((ident, raw, f))
    return out


def collect_canonical():
    canon = defaultdict(list)
    if not MODULES_GMS.is_dir():
        return canon
    for gms in MODULES_GMS.rglob("scaling.gms"):
        try:
            text = gms.read_text(errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if line.startswith("*"):  # column-0 GAMS comment / disabled line
                continue
            m = CANON_RE.match(line)
            if not m:
                continue
            val_raw = m.group(2).strip()
            if not NUM_ATOMIC_RE.match(val_raw):  # skip expressions
                continue
            f = to_float(val_raw)
            if f is None:
                continue
            rel = gms.relative_to(MAGPIE_DIR)
            canon[m.group(1)].append((f, val_raw, str(rel), str(i)))
    return canon


def collect_doc_claims():
    claims = defaultdict(list)
    if not MODULE_DOCS.is_dir():
        return claims
    for md in MODULE_DOCS.glob("module_*.md"):
        if md.name.endswith("_notes.md"):
            continue
        try:
            text = md.read_text(errors="ignore")
        except Exception:
            continue
        rel = md.relative_to(AGENT_DIR)
        for i, line in enumerate(text.splitlines(), 1):
            for ident, raw, f in claims_in_line(line):
                claims[ident].append((str(rel), i, raw, f))
    return claims


def close(a: float, b: float, tol: float = 0.05) -> bool:
    if a == 0 or b == 0:
        return a == b
    return abs(math.log10(a / b)) < math.log10(1 + tol)


def compare(canon, claims):
    findings = []
    for ident, cl in claims.items():
        cvals = canon.get(ident)
        if not cvals:  # no canonical .scale for this ident -> can't verify here
            continue
        for doc_path, line, raw, f in cl:
            if any(close(f, cf) for cf, _, _, _ in cvals):
                continue
            findings.append({
                "identifier": ident,
                "doc_location": f"{doc_path}:{line}",
                "claimed_value": raw,
                "canonical_values": sorted({cr for _, cr, _, _ in cvals}),
                "canonical_sources": [f"{p}:{ln}" for _, _, p, ln in cvals[:3]],
            })
    return findings


def self_test() -> int:
    ok = True
    # (1) extraction: a known-bad line yields (vm_cost_timber, 10e4)
    line = "Section 10: `vm_cost_timber.scale(i)` is scaled by 10e4 in scaling.gms:8"
    got = claims_in_line(line)
    if not any(g[0] == "vm_cost_timber" and g[1].lower() == "10e4" for g in got):
        print(f"  SELF-TEST FAIL: extraction did not yield (vm_cost_timber, 10e4): {got}")
        ok = False
    # plain ints (line numbers) must NOT be treated as scale values
    if any(g[1] in ("8", "10") for g in got):
        print(f"  SELF-TEST FAIL: a plain int was read as a scale value: {got}")
        ok = False
    # (2) numeric compare: 10e4 flagged vs canonical 1e4; 1e4 not flagged
    canon = {"vm_x": [(to_float("1e4"), "1e4", "fake/scaling.gms", "8")]}
    bad = compare(canon, {"vm_x": [("module_x.md", 1, "10e4", to_float("10e4"))]})
    good = compare(canon, {"vm_x": [("module_x.md", 2, "1e4", to_float("1e4"))]})
    if len(bad) != 1:
        print(f"  SELF-TEST FAIL: 10e4-vs-1e4 not flagged ({len(bad)})")
        ok = False
    if len(good) != 0:
        print(f"  SELF-TEST FAIL: 1e4-vs-1e4 wrongly flagged ({len(good)})")
        ok = False
    print("check_scaling self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        rc = self_test()
        if rc == 0:
            print("SELFTEST_OK check_scaling")
        return rc
    summary = "--summary" in sys.argv
    js = "--json" in sys.argv

    canon = collect_canonical()
    claims = collect_doc_claims()
    findings = compare(canon, claims)
    n_canon = sum(len(v) for v in canon.values())
    n_claims = sum(len(v) for v in claims.values())

    if js:
        json.dump({
            "summary": {
                "canonical_scale_identifiers": len(canon),
                "canonical_records": n_canon,
                "doc_scale_claims_scanned": n_claims,
                "mismatches_found": len(findings),
            },
            "findings": findings,
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if summary:
        print(f"check_scaling: {len(canon)} idents with canonical .scale; "
              f"{n_claims} doc scale claims scanned; {len(findings)} mismatch(es) (advisory).")
        return 0

    print(f"check_scaling: canonical {len(canon)} idents ({n_canon} records); "
          f"doc scale claims scanned: {n_claims}")
    print(f"Mismatches: {len(findings)} (advisory)")
    if findings:
        print()
        for f in findings:
            src = f["canonical_sources"][0] if f["canonical_sources"] else "?"
            print(f"  {f['doc_location']}: `{f['identifier']}` claims "
                  f"'{f['claimed_value']}' but canonical is {f['canonical_values']} "
                  f"(source: {src})")
    return 0  # advisory, never fails


if __name__ == "__main__":
    sys.exit(main())
