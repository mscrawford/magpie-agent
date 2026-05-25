#!/usr/bin/env python3
"""check_units.py — flag prose unit claims that disagree with declarations.gms.

Motivating bug: R24 Q1-B3 (Major, doc_error). `module_56.md:152,158,627,675`
stated "USD17MER per Tg" for `im_pollutant_prices` and `f56_pollutant_prices`;
the canonical declaration in `modules/56_ghg_policy/price_aug22/declarations.gms`
says "USD17MER per Mg" — a 6-orders-of-magnitude drift. The pattern is generic
(Tg vs Mg, mio vs '000, tC vs tCO2-eq) and not caught by the existing checkers
(which verify name/equation/realization existence but not unit prose).

Strategy:

1. Build a canonical {identifier -> unit_string} map by scanning
   `../modules/*/*/*.gms` (declarations.gms is the canonical home but units
   also appear in equations.gms / preloop.gms inline comments).
2. Build a doc-side {identifier -> [(file:line, claimed_unit)]} map by
   scanning `modules/module_XX.md` for backtick-quoted identifiers followed
   within ~5 lines by a unit string. We only flag claims where the unit is
   EXPLICITLY stated near the identifier — generic prose without a unit is
   not a finding.
3. Compare claims to canonical. Flag mismatches.

Output: advisory by default (does NOT fail the validator suite). Each finding
includes the doc location, claimed unit, canonical unit, and the source
declaration. Reviewer triages — the unit catalog has some legitimate
realization-specific variation, and "USD17MER per Mg" vs "USD17MER per Mg N"
is not actually a contradiction.

Usage:
    python3 scripts/check_units.py            # full check
    python3 scripts/check_units.py --summary  # one-line summary only
    python3 scripts/check_units.py --json     # JSON output for piping
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_DIR = AGENT_DIR.parent
MODULES_GMS = MAGPIE_DIR / "modules"
MODULE_DOCS = AGENT_DIR / "modules"

# Patterns

# An identifier we care about: vm_*, pm_*, im_*, vN_*, pN_*, sN_*, fN_*, iN_*,
# cN_*, sm_*, cm_*, pcm_*, qN_* (equations also have units sometimes).
IDENT_RE = re.compile(
    r"\b((?:vm|pm|im|sm|cm|pcm|ov|oq|f|i|v|p|s|c|q)\d*_[a-z][\w]*)\b"
)

# Declaration-line identifier (must be at start of token, after whitespace).
# Captures: identifier, optional dim parens, description, last-paren unit.
DECL_LINE_RE = re.compile(
    r"^\s*((?:vm|pm|im|sm|cm|pcm|ov|oq|f|i|v|p|s|c|q)\d*_[a-z][\w]*)"
    r"\s*(?:\([^)]*\))?\s+"  # optional dimension tuple
    r".+?"  # description (non-greedy)
    r"\s*\(([^()]+)\)\s*$"  # last parenthetical = unit
)

# Heuristic: a "unit" parenthetical looks unit-y. We use this to discard
# parens that aren't units (e.g., GAMS macro args, descriptive prose).
#
# Strategy: match a high-confidence unit pattern via regex with word boundaries
# (avoids "Mg" matching inside "MAgPIE", "g" matching inside "ago", etc.).
#
# Plain-string accepted units: "1", "share", "binary", "fraction", "ratio", "index"
# Regex-matched unit tokens: USD/EUR currency codes, mass with prefix (Tg/Mg/kg
# at word boundary), tDM/tC/tCO2 mass-of-element, GtC/EJ/GJ/MJ/PJ energy,
# kcal/Mcal calorie, "mio" (always with the abbreviation dot in code, but
# prose sometimes drops it), "per" connecting words.
UNIT_PLAIN_OK = {"1", "share", "binary", "fraction", "ratio", "index"}
UNIT_REGEX = re.compile(
    r"\b(?:"
    r"USD\d*[A-Z]*|"           # USD17MER, USD05MER, USD
    r"EUR\d*[A-Z]*|"           # EUR05PPP
    r"[GtkMP]?[Tt][gG]\b|"     # Tg, Mg, kg, MTg (mass)
    r"t[DCNP]M?\b|"            # tDM, tC, tN, tP, tCM (mass of element)
    r"tCO2(?:-eq)?|"           # tCO2, tCO2-eq
    r"GtC|"                    # gigaton carbon
    r"[GMEP]J\b|"              # gigajoule, megajoule, etc.
    r"[Mk]?cal\b|"             # kcal, Mcal
    r"mio\.?|"                 # mio. (with or without dot)
    r"\bha\b|"                 # ha (word-bounded)
    r"\byr\b|"                 # yr (word-bounded)
    r"\bper\s+|"               # "per" connector (a strong unit signal)
    r"%|"
    r"binary|share|fraction"
    r")",
    re.IGNORECASE,
)


def looks_like_unit(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    if s.lower() in UNIT_PLAIN_OK:
        return True
    # Reject obvious-prose patterns even if a regex matches by accident.
    # If the claim is mostly capitalized words with no slashes / digits /
    # unit-y characters, it's prose.
    if " " in s and not any(c.isdigit() or c in "/.%" for c in s):
        # E.g., "MAgPIE optimization" — multi-word with no unit-shape.
        # But "Tg N" / "kg N" must pass; check those before rejecting.
        if not re.search(r"\b(Tg|Mg|kg|tC|tN|GJ|kcal|Mcal|tDM|ha|yr|per)\b", s):
            return False
    return bool(UNIT_REGEX.search(s))


# Doc-side unit-claim pattern: an identifier in backticks, followed within
# the same line by a unit-shaped backticked string OR an explicit "unit:"
# / "units:" / "(unit:" phrasing. Tight pattern to keep FP rate low.
# Examples it catches:
#   `im_pollutant_prices` ... USD17MER per Tg
#   `vm_carbon_stock` (units: tC per ha)
# Examples it skips:
#   "im_pollutant_prices is a parameter declared in M56" (no unit nearby)
DOC_INLINE_UNIT_RE = re.compile(
    r"`([a-z_]+\d*_[a-z][\w]*)`[^\n`]*?"
    r"(?:\(|units?:|in\s+)\s*([\w./%\-\s]+?)(?:\)|[\.,]|$)"
)


def collect_canonical_units() -> dict[str, list[tuple[str, str, str]]]:
    """Return {identifier -> [(unit, file_path, line_no)]} from .gms files."""
    canonical: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    if not MODULES_GMS.is_dir():
        return canonical
    # Walk declarations.gms first; equations.gms / postsolve.gms / preloop.gms
    # also have inline-comment units but declarations is canonical.
    for gms in MODULES_GMS.rglob("declarations.gms"):
        try:
            text = gms.read_text(errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = DECL_LINE_RE.match(line)
            if not m:
                continue
            ident, unit = m.group(1), m.group(2).strip()
            if not looks_like_unit(unit):
                continue
            rel = gms.relative_to(MAGPIE_DIR)
            canonical[ident].append((unit, str(rel), str(i)))
    return canonical


def collect_doc_claims() -> dict[str, list[tuple[str, int, str]]]:
    """Return {identifier -> [(file_path, line_no, claimed_unit)]} from docs."""
    claims: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    if not MODULE_DOCS.is_dir():
        return claims
    for md in MODULE_DOCS.glob("module_*.md"):
        # Skip _notes files — notes are user-feedback, not canonical claims.
        if md.name.endswith("_notes.md"):
            continue
        try:
            text = md.read_text(errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in DOC_INLINE_UNIT_RE.finditer(line):
                ident, claim = m.group(1), m.group(2).strip()
                # Reject claims that are not unit-y (false positives where the
                # post-identifier text is just descriptive prose).
                if not looks_like_unit(claim):
                    continue
                # Reject very long captures (likely sentence fragments).
                if len(claim) > 50:
                    continue
                rel = md.relative_to(AGENT_DIR)
                claims[ident].append((str(rel), i, claim))
    return claims


def normalize_unit(s: str) -> str:
    """Normalize a unit string for comparison (whitespace, case, common syns)."""
    s = s.strip().lower()
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    # Common synonym normalizations (don't be too aggressive — we WANT to flag
    # Tg vs Mg, but NOT "USD17 MER" vs "USD17MER")
    s = s.replace("usd17 mer", "usd17mer").replace("usd05 mer", "usd05mer")
    # Slash vs "per" — tDM/ha == tDM per ha; mio USD/yr == mio. usd per yr
    s = re.sub(r"\s*/\s*", " per ", s)
    # "Mt" == "mio. t" (megaton = million tons abbreviation)
    s = s.replace("mt dm", "mio. tdm").replace("mt c", "mio. tc")
    # Drop trailing dot variations: "mio." vs "mio"
    s = s.replace("mio.", "mio").replace("mio ", "mio. ")
    # Strip trailing punctuation that snuck in
    s = re.sub(r"[.,;)]+$", "", s)
    return s


def compare(canonical, claims) -> list[dict]:
    """Compare doc claims to canonical units. Return mismatch findings."""
    findings = []
    for ident, claim_list in claims.items():
        canon_units = canonical.get(ident)
        if not canon_units:
            # No canonical — skip (we don't flag unverifiable claims here;
            # check_doc_var_existence handles missing identifiers).
            continue
        # Build set of normalized canonical units (one identifier may have
        # the same unit in multiple realizations — that's fine).
        canon_normalized = {normalize_unit(u) for u, _, _ in canon_units}
        for doc_path, doc_line, claim in claim_list:
            norm_claim = normalize_unit(claim)
            # Exact match (one of the canonical forms)
            if norm_claim in canon_normalized:
                continue
            # Substring match (canonical is "USD17MER per Mg"; claim is just
            # "Mg") — likely benign abbreviation.
            if any(norm_claim in cu or cu in norm_claim for cu in canon_normalized):
                continue
            # Real mismatch
            findings.append({
                "identifier": ident,
                "doc_location": f"{doc_path}:{doc_line}",
                "claimed_unit": claim,
                "canonical_units": sorted(canon_normalized),
                "canonical_sources": [f"{p}:{ln}" for _, p, ln in canon_units[:3]],
            })
    return findings


def main() -> int:
    summary_only = "--summary" in sys.argv
    json_out = "--json" in sys.argv

    canonical = collect_canonical_units()
    claims = collect_doc_claims()
    findings = compare(canonical, claims)

    n_canonical = sum(len(v) for v in canonical.values())
    n_idents_with_units = len(canonical)
    n_claims = sum(len(v) for v in claims.values())

    if json_out:
        json.dump({
            "summary": {
                "identifiers_with_canonical_units": n_idents_with_units,
                "total_canonical_unit_records": n_canonical,
                "doc_unit_claims_scanned": n_claims,
                "mismatches_found": len(findings),
            },
            "findings": findings,
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if summary_only:
        print(f"check_units: {n_idents_with_units} identifiers have canonical units in "
              f".gms declarations; {n_claims} doc unit claims scanned; "
              f"{len(findings)} mismatch(es) found (advisory).")
        return 0

    print(f"check_units: canonical {n_idents_with_units} identifiers with units "
          f"({n_canonical} records); doc claims scanned: {n_claims}")
    print(f"Mismatches: {len(findings)} (advisory)")
    if findings:
        print()
        for f in findings:
            print(f"  {f['doc_location']}: `{f['identifier']}` claims "
                  f"'{f['claimed_unit']}' but canonical is "
                  f"{f['canonical_units']} (sources: {f['canonical_sources'][0]})")
    return 0  # advisory, never fails


if __name__ == "__main__":
    sys.exit(main())
