#!/usr/bin/env python3
"""check_dependent_direction.py — SERIAL HAND-OFF claims vs slice-resolved code truth.

Check 36 (advisory). Mechanizes (part of) the `data_flow_direction` bug class
that R55's depth audit found NOT cheaply mechanizable by a plain role-map diff
(6.38 findings per 100 claims; residual_density_per_100_claims in
audit/validation_rounds.json round 55) — because both of its surviving Majors
were SLICE-disjointness bugs (module_52.md:443, module_56.md:66: "module 52
feeds module 56's carbon pricing via vm_emissions_reg" — false; the two
modules read/write PROVABLY DISJOINT slices of the same shared variable, per
`core/sets.gms:314` emis_oneoff vs `:320` emis_annual). Now that
`scripts/gams_slices.py` (slice-index resolution) and
`check_attribution_omissions.build_slice_role_map()` (per-occurrence raw
argument tuples) exist, this class becomes mechanical too.

WHAT THIS CATCHES
  A doc claims a SERIAL hand-off of one interface var between two named
  modules — "Module A provides `V` to Module B", "B receives `V` from A",
  "X flows A -> B", or (the two REAL corpus shapes) a var-block "Consumers"
  field under a module-owned var heading, or a self-contained
  "- **V(dims)**: ... from the emission modules (A, B, C)" bullet. Each such
  claim names a PRODUCER (writes V) and a CONSUMER (reads V). This checker
  tests whether the producer's CODE write-slice(s) and the consumer's CODE
  read-slice(s) of V could plausibly overlap (`gams_slices.slices_intersect`).

  Flags ONLY when EVERY (write-slice, read-slice) pair resolves to
  `slices_intersect(...) is False` (provably disjoint) AND NO pair resolves to
  True (a genuine overlap exists somewhere, e.g. a `.l`-postsolve reporting
  dump over the bare declared sets — this is exactly what rescues the doc's
  OTHER, legitimate emis_annual producers 51/53/58 from a false flag: verified
  live against MAGPIE_DIR that producers 51/53/58 all show >=1 intersecting
  pair against module 56's reads, while producer 52 shows zero). A `None`
  (unresolved — alias, macro, dynamic/mapping set) pair alone never flags and
  never rescues; it just means "insufficient evidence," consistent with
  gams_slices's own binding precision rule (a wrong DISJOINT verdict is the
  harmful direction, never a missed one).

DOC-SIDE PARSING (reuses check_attribution_omissions's scaffold; does NOT
reimplement it)
  Imports `_debacktick`, `_mod_nums`, `_cross_vars_backticked`, `_cross_vars`,
  `NEGATION_RE`, `HISTORICAL_RE`, `FENCE_RE`, `HEDGE_RE`, `_VARBLOCK_HEAD_RE`,
  `_MD_HEAD_RE`, `_FIELD_READ_RE`, `_FIELD_POP_RE`, and `build_slice_role_map`
  directly from check_attribution_omissions.py. What's genuinely NEW here
  (not a reimplementation of anything upstream) is the HAND-OFF trigger
  vocabulary itself (HANDOFF_TO_RE / HANDOFF_FROM_RE / ARROW_RE) — this is a
  different question from Check 34/35's "is the consumer LIST complete"
  (omission/count), so it needs its own triggers. Two doc-side gaps had to be
  closed for this to work on the REAL corpus text (found empirically, not
  assumed):
    1. `_mod_nums` alone does not parse "the emission modules (51 N2O, 52
       LULUCF CO2, ...)" — a bare-number-plus-label enumeration inside a
       parenthetical, with NO "Module" keyword per item. Added
       `_bare_paren_modnums` (bold-marker-stripped before digit matching — a
       raw `**52 LULUCF CO2**` segment's leading `**` blocks a naive
       `\s*\d` match otherwise).
    2. `check_attribution_omissions`'s var-block scope tracking
       (`_VARBLOCK_HEAD_RE`) only recognizes a STANDALONE var heading
       ("**1. VAR** (citation)") followed by SEPARATE "- **Field**:" bullets.
       module_56.md's real shape is a SELF-CONTAINED bullet
       ("- **VAR(dims)**: description...") with the var AND its attribution
       prose on one line. Added `_BULLET_BOLD_RE` to catch this shape without
       touching the imported scope-tracking logic.

COVERAGE (ALWAYS printed — "0 findings" over few claims is BLIND, not clean)
  hand-off claims found (raw doc lines bound to a var+direction+module set),
  vs. pairs bound (producer x consumer pairs with slice data on BOTH sides —
  actually comparable) vs. pairs skipped (one or both sides have zero code-side
  occurrences of the var at all — a DIFFERENT bug class, existence not
  direction; out of scope here, left to Check 34).

Ground truth: `<MAGPIE_DIR>/modules`. Point MAGPIE_DIR at a pinned develop
worktree for an authoritative run:
    MAGPIE_DIR=/path/to/develop-worktree python3 check_dependent_direction.py

Usage:
  python3 check_dependent_direction.py [--verbose]
  python3 check_dependent_direction.py --self-test

Exit: 0 always in scan mode (advisory). --self-test returns 0/1, prints
`SELFTEST_OK check_dependent_direction`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_gams_variables import MAGPIE_DIR  # noqa: E402  (honours MAGPIE_DIR env override)
from check_attribution_omissions import (  # noqa: E402
    _debacktick,
    _mod_nums,
    _cross_vars_backticked,
    _cross_vars,
    NEGATION_RE,
    HISTORICAL_RE,
    FENCE_RE,
    HEDGE_RE,
    _VARBLOCK_HEAD_RE,
    _MD_HEAD_RE,
    _FIELD_READ_RE,
    _FIELD_POP_RE,
    build_slice_role_map,
)
from gams_slices import (  # noqa: E402
    build_set_index,
    resolve_index,
    slices_intersect,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
CROSS_DIR = AGENT_DIR / "cross_module"
ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"
CHECK_NAME = "check_dependent_direction"


def load_allowlist() -> set[tuple[str, str]]:
    """{(file, "<producer>:<consumer>:<var>")} suppressed known FPs (allowlist
    loader pattern mirrored from check_attribution_omissions.load_allowlist)."""
    if not ALLOWLIST_PATH.exists():
        return set()
    try:
        data = json.loads(ALLOWLIST_PATH.read_text())
    except (ValueError, OSError):
        return set()
    rows = data if isinstance(data, list) else (data.get("allowlist") or data.get("entries") or [])
    return {(e.get("file", ""), e.get("key", "")) for e in rows if e.get("check") == CHECK_NAME}


# ---------------------------------------------------------------------------
# DOC SIDE — hand-off trigger vocabulary (NEW; not in check_attribution_omissions)
# ---------------------------------------------------------------------------

# "TO" direction: doc_own (a POPULATOR of the scoped var, per code) hands the
# var off TO named recipient module(s). Field-label form ("**Consumers**:",
# the module_52.md:443 real shape) plus explicit prose.
HANDOFF_TO_RE = re.compile(
    r"\*\*consumers?\*\*\s*:|\bconsumers?\s+of\b|\bconsumed\s+by\b|"
    r"\b(?:provides?|supplies?|sends?)\b[^.\n]{0,80}?\bto\b|"
    r"\bfeeds?\s+(?:into|to)\b|\bpassed\s+to\b|\bsent\s+to\b",
    re.IGNORECASE)

# "FROM" direction: doc_own (a READER of the scoped var, per code) receives the
# var FROM named producer module(s). Prose form ("from the emission modules
# (...)", the module_56.md:66 real shape) plus explicit "receives/consumes from".
HANDOFF_FROM_RE = re.compile(
    r"\*\*(?:receives?\s+from|populated\s+by|produced\s+by|written\s+by)\*\*\s*:|"
    r"\breceives?\b[^.\n]{0,80}?\bfrom\b|\bconsumes?\b[^.\n]{0,80}?\bfrom\b|"
    r"\bfrom\s+the\b[^.\n]{0,40}?\bmodules?\b|\bsourced\s+from\b",
    re.IGNORECASE)

# Arrow form: "Module A -> Module B" / "Module A → Module B" — explicit,
# doc_own-INDEPENDENT (both ends named directly; order is the arrow itself, no
# heuristic needed).
ARROW_RE = re.compile(
    r"(?<![\w])(?:Module\s*|M)(\d{1,2})(?![\w])\s*(?:->|-->|=>|→)\s*"
    r"(?<![\w])(?:Module\s*|M)(\d{1,2})(?![\w])", re.IGNORECASE)
# 2026-07-19: the `M70 → M14` short form was previously unreadable (the pattern
# required the literal word "Module" on BOTH ends), leaving 7 genuine bindable
# hand-off claims in module_70.md unbound -- in the very bug class this check
# exists for (data_flow_direction, source of both R55 Majors). Same reader-dialect
# gap as the `**NN** (Name)` one in check_attribution_tables; see
# audit/reader_blind_spots.md.
#
# Deliberately NOT widened to the `NN_name` form (`56_ghg_policy → 32_forestry`):
# the only corpus instances are var-less topology chains, so they carry no claim
# this check can bind, and admitting them would add surface area for zero gain.
# Negations and historical refs are already filtered downstream by NEGATION_RE /
# HISTORICAL_RE, which is what keeps this widening precision-safe.

# A bullet whose OWN bold span is the var itself (module_56.md's real shape):
# "- **vm_emissions_reg(i,emis_annual,pollutants)**: Actual regional emissions
# from the emission modules (...)". Distinguished from a FIELD-label bullet
# ("- **Consumers**: ...") by requiring the bold content to resolve to exactly
# one cross-module var via `_cross_vars` (a field label never does).
_BULLET_BOLD_RE = re.compile(r"^\s*[-*]\s*\*\*([^*]+)\*\*\s*:")

# A bare-number-plus-label enumeration inside a "modules (...)" parenthetical
# — e.g. "the emission modules (51 N2O, 52 LULUCF CO2, 53 CH4, 58 peatland)".
# `_mod_nums` (imported) does NOT catch this shape: it requires either the
# literal word "Module" before each number, or a "NN_lowercase" identifier —
# neither is present here (bare "51 N2O"). This is a genuinely NEW extraction,
# not a reimplementation of `_mod_nums` (it targets a DIFFERENT doc idiom).
_BARE_PAREN_MODLIST_RE = re.compile(r"\bmodules?\s*\(([^)]+)\)", re.IGNORECASE)


def _bare_paren_modnums(fragment: str) -> set[str]:
    nums: set[str] = set()
    for pm in _BARE_PAREN_MODLIST_RE.finditer(fragment):
        # Strip markdown bold/italic markers FIRST: a raw segment like
        # " **52 LULUCF CO2**" starts with "**", which blocks a leading-digit
        # match otherwise (verified against the real module_56.md:66 text).
        inner = pm.group(1).replace("*", "")
        inner = re.sub(r"\band\b", ",", inner, flags=re.IGNORECASE)
        for seg in inner.split(","):
            m = re.match(r"\s*(\d{1,2})\b", seg)
            if m:
                nums.add(f"{int(m.group(1)):02d}")
    return nums


def _line_vars(line: str) -> list[str]:
    """Cross-iface var bases mentioned in backticks OR (fallback) a bold span
    on this line. Mirrors the bold-fallback already used by
    check_attribution_omissions.parse_doc_varblock_triples for the same
    reason: real headings often bold the var instead of backticking it."""
    out = list(_cross_vars_backticked(line))
    if not out:
        for bold in re.findall(r"\*\*([^*]+)\*\*", line):
            for v in _cross_vars(bold):
                if v not in out:
                    out.append(v)
    return out


def _bind_field_claim(line: str, deb: str, var: str, doc_own: str, lineno: int) -> dict | None:
    """Bind ONE line/field's hand-off claim, given the var already in scope.

    Returns None if: both/neither TO+FROM trigger matched (ambiguous), or no
    OTHER module is named (nothing to compare doc_own against).
    """
    to_m = HANDOFF_TO_RE.search(deb)
    from_m = HANDOFF_FROM_RE.search(deb)
    if not (to_m or from_m) or (to_m and from_m):
        return None
    named = (_mod_nums(deb) | _bare_paren_modnums(deb)) - {doc_own}
    if not named:
        return None
    hedged = bool(HEDGE_RE.search(deb))
    row = line.strip()[:160]
    if to_m:
        return {"lineno": lineno, "var": var, "producers": {doc_own}, "consumers": named,
                "row": row, "source": "to-field", "hedged": hedged}
    return {"lineno": lineno, "var": var, "producers": named, "consumers": {doc_own},
            "row": row, "source": "from-field", "hedged": hedged}


def parse_handoff_claims(text: str, doc_own: str | None) -> list[dict]:
    """Return hand-off claims: {lineno, var, producers:set, consumers:set,
    row, source, hedged}. `source` in {"arrow","to-field","from-field"}.
    """
    claims: list[dict] = []
    lines = text.splitlines()
    in_fence = False
    scope_var: str | None = None
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if HISTORICAL_RE.search(line):
            continue

        deb = _debacktick(line)
        negated = bool(NEGATION_RE.search(deb))

        # Arrow form — explicit, doc_own-independent. Checked on every
        # non-fenced/non-historical line regardless of var-scope state.
        if not negated:
            for am in ARROW_RE.finditer(line):
                a, b = f"{int(am.group(1)):02d}", f"{int(am.group(2)):02d}"
                if a == b:
                    continue
                vh = _line_vars(line) or ([scope_var] if scope_var else [])
                if len(vh) == 1:
                    claims.append({
                        "lineno": i + 1, "var": vh[0], "producers": {a}, "consumers": {b},
                        "row": line.strip()[:160], "source": "arrow",
                        "hedged": bool(HEDGE_RE.search(deb)),
                    })

        if _MD_HEAD_RE.match(line):
            scope_var = None
            continue

        # Self-contained bullet: "- **VAR(dims)**: description..." (the
        # module_56.md:66 real shape — var + attribution prose on one line, no
        # separate heading). Tried BEFORE the heading-scope path; mutually
        # exclusive with it by construction (this requires a leading "-"/"*"
        # bullet marker, which _VARBLOCK_HEAD_RE explicitly excludes).
        bm = _BULLET_BOLD_RE.match(line)
        if bm:
            found = set(_cross_vars(bm.group(1)))
            if len(found) == 1:
                var = next(iter(found))
                scope_var = var
                if doc_own and not negated:
                    c = _bind_field_claim(line, deb, var, doc_own, i + 1)
                    if c:
                        claims.append(c)
                continue

        # Heading-scope form: a bolded, NON-bulleted heading names ONE var and
        # OPENS a scope; subsequent "- **Field**:" bullets (module_52.md:443's
        # real shape) inherit it. Reuses the SAME scope-open test as
        # check_attribution_omissions.parse_doc_varblock_triples (imported
        # regexes), not reimplemented.
        is_field = bool(_FIELD_READ_RE.match(line) or _FIELD_POP_RE.match(line))
        if _VARBLOCK_HEAD_RE.match(line) and not is_field:
            found = set()
            for bold in re.findall(r"\*\*([^*]+)\*\*", line):
                found |= set(_cross_vars(bold))
            inline_var = next(iter(found)) if len(found) == 1 else None
            scope_var = inline_var
            if inline_var and doc_own and not negated:
                c = _bind_field_claim(line, deb, inline_var, doc_own, i + 1)
                if c:
                    claims.append(c)
            continue

        if not scope_var or doc_own is None or negated:
            continue
        if not (is_field):
            continue
        c = _bind_field_claim(line, deb, scope_var, doc_own, i + 1)
        if c:
            claims.append(c)
    return claims


# ---------------------------------------------------------------------------
# CODE SIDE — slice-verdict aggregation
# ---------------------------------------------------------------------------

def _evaluate_pair(write_slices: list, read_slices: list, set_index: dict):
    """Return ('intersect'|'disjoint'|'ambiguous'|'heterogeneous-producer',
    sample_write, sample_read).

    PRODUCER-HOMOGENEITY GATE (precision fix, found empirically -- see below):
    a "disjoint hand-off" verdict presupposes ONE identifiable "the slice the
    producer writes." When the producer instead populates the var via SEVERAL
    DIFFERENT literal argument tuples (a shared parameter written per-pool /
    per-land-type in separate statements, e.g. `pm_carbon_density_secdforest_ac`:
    M52 writes `(t_all,j,ac,"vegc")` AND `(t_all,j,ac,"litc")` in separate
    lines), there is no single slice to test — an arbitrary occurrence pairing
    (e.g. the "litc" write vs a consumer's "vegc" read) can be genuinely
    disjoint on ONE dimension while a DIFFERENT, matching occurrence (the
    "vegc" write) exists but can't be proven to intersect (commonly because an
    UNRELATED dimension never resolves symmetrically -- e.g. `t` (a dynamic,
    runtime-populated current-period subset) vs `t_all` (the full static year
    set) are never both resolved, so even the genuinely-matching "vegc" vs
    "vegc" pair returns None, not True). Verified against the real corpus: this
    exact shape produced a false "disjoint" on module_52.md's OWN correct
    `pm_carbon_density_secdforest_ac`/`fm_carbon_density` consumer claims
    before this gate was added (M14/29/30/31/32 genuinely DO consume what M52
    writes). Gated OFF (treated as 'heterogeneous-producer', never flagged)
    whenever the producer's DISTINCT write-tuples number != 1.

    'intersect' takes priority over 'disjoint' when the gate passes (a single
    True anywhere rescues the whole comparison — a real connection exists via
    SOME occurrence, e.g. a `.l`-postsolve reporting dump over the bare
    declared sets). Only 'disjoint' (>=1 False pair, zero True pairs, single
    producer slice) is ever flagged. 'ambiguous' (no True, no False — every
    pair unresolved) is never flagged either: insufficient evidence, not proof.
    """
    if len({tuple(w) for w in write_slices}) != 1:
        return "heterogeneous-producer", None, None
    any_true = False
    disjoint_sample = None
    for w in write_slices:
        wr = tuple(resolve_index(tok, set_index) for tok in w)
        for r in read_slices:
            rr = tuple(resolve_index(tok, set_index) for tok in r)
            v = slices_intersect(wr, rr)
            if v is True:
                any_true = True
            elif v is False and disjoint_sample is None:
                disjoint_sample = (w, r)
    if any_true:
        return "intersect", None, None
    if disjoint_sample is not None:
        return "disjoint", disjoint_sample[0], disjoint_sample[1]
    return "ambiguous", None, None


def scan_doc(text: str, rel_path: str, slice_role: dict, set_index: dict,
             allow: set | None = None) -> tuple[list[dict], dict]:
    """Return (findings, stats) for one doc. stats = {claims_found, pairs_bound,
    pairs_skipped} — a doc line naming several producers/consumers yields
    several PAIRS from one claim (e.g. "from the emission modules (51,52,53,58)"
    yields 4 pairs against doc_own).
    """
    allow = allow or set()
    fname = os.path.basename(rel_path)
    mod_m = re.search(r"module_(\d{1,2})", fname)
    doc_own = f"{int(mod_m.group(1)):02d}" if mod_m else None

    claims = parse_handoff_claims(text, doc_own)
    findings: list[dict] = []
    stats = {"claims_found": 0, "pairs_bound": 0, "pairs_skipped": 0}

    for c in claims:
        if c["hedged"]:
            continue
        stats["claims_found"] += 1
        var = c["var"]
        for p in sorted(c["producers"]):
            for m in sorted(c["consumers"]):
                if p == m:
                    continue
                write_slices = slice_role.get(var, {}).get(p, {}).get("POPULATE", [])
                read_slices = slice_role.get(var, {}).get(m, {}).get("READ", [])
                if not write_slices or not read_slices:
                    stats["pairs_skipped"] += 1
                    continue
                verdict, sw, sr = _evaluate_pair(write_slices, read_slices, set_index)
                if verdict == "heterogeneous-producer":
                    # Producer writes >1 distinct slice -- no single "the
                    # write-slice" to test against (see _evaluate_pair
                    # docstring). Insufficient data, not evidence either way.
                    stats["pairs_skipped"] += 1
                    continue
                stats["pairs_bound"] += 1
                if verdict != "disjoint":
                    continue
                key = f"{p}:{m}:{var}"
                if (rel_path, key) in allow or (fname, key) in allow:
                    continue
                findings.append({
                    "file": rel_path, "line": c["lineno"], "var": var,
                    "producer": p, "consumer": m, "row": c["row"], "source": c["source"],
                    "sample_write": sw, "sample_read": sr,
                })
    return findings, stats


# ---------------------------------------------------------------------------
# Output / CLI
# ---------------------------------------------------------------------------

def _iter_docs():
    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        if not doc.name.endswith("_notes.md"):
            yield doc
    if CROSS_DIR.is_dir():
        yield from sorted(CROSS_DIR.glob("*.md"))


def main() -> int:
    args = sys.argv[1:]
    verbose = "--verbose" in args
    if "--self-test" in args:
        return self_test()

    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        print(f"{CHECK_NAME}: WARNING GAMS modules not found at {MAGPIE_DIR} - skipping.")
        return 0

    slice_role = build_slice_role_map()
    set_index = build_set_index()
    allow = load_allowlist()

    all_findings: list[dict] = []
    totals = {"claims_found": 0, "pairs_bound": 0, "pairs_skipped": 0}
    n_docs = 0
    docs_with_claims = 0
    for doc in _iter_docs():
        n_docs += 1
        rel = str(doc.relative_to(AGENT_DIR))
        text = doc.read_text(encoding="utf-8", errors="ignore")
        findings, stats = scan_doc(text, rel, slice_role, set_index, allow)
        if stats["claims_found"]:
            docs_with_claims += 1
        for k in totals:
            totals[k] += stats[k]
        all_findings.extend(findings)

    # Coverage denominator ALWAYS printed (a "0" over few claims is BLIND, per
    # the mandate — not "corpus clean").
    print(f"{CHECK_NAME}: coverage = {totals['claims_found']} hand-off claims found "
          f"across {docs_with_claims}/{n_docs} docs; "
          f"{totals['pairs_bound']} producer/consumer pair(s) slice-comparable "
          f"(both sides have code-side slice data), "
          f"{totals['pairs_skipped']} skipped (one/both sides have ZERO code-side "
          f"occurrences of the var -- an existence gap, not a direction claim; "
          f"out of scope here, see Check 34).")

    if all_findings:
        print(f"\n{CHECK_NAME}: {len(all_findings)} PARALLEL-NOT-SERIAL finding(s) "
              f"(doc claims a hand-off; producer's write-slice and consumer's "
              f"read-slice are provably disjoint on EVERY occurrence pair):")
        for f in all_findings:
            print(f"  {f['file']}:{f['line']}  `{f['var']}` claims M{f['producer']} -> "
                  f"M{f['consumer']} ({f['source']}), but M{f['producer']} writes "
                  f"{f['sample_write']} and M{f['consumer']} reads {f['sample_read']} "
                  f"(disjoint). Line: {f['row']}")
    else:
        print(f"\n{CHECK_NAME}: 0 findings within covered claims "
              f"(NOT a corpus-clean claim unless coverage above is non-trivial — see "
              f"the mandatory coverage line).")

    print(f"\n{CHECK_NAME}: NOTE advisory + precision-first: flags ONLY when every "
          f"occurrence-pair is provably disjoint and none intersects; a single "
          f"intersecting occurrence (e.g. a postsolve reporting dump over the bare "
          f"declared sets) rescues the claim. Confirm against develop + adversarial "
          f"refute before any doc edit.")
    # Machine-greppable summary line (for a future validate_consistency.sh Check 36).
    print(f"{CHECK_NAME}: SUMMARY findings={len(all_findings)} "
          f"claims_found={totals['claims_found']} pairs_bound={totals['pairs_bound']} "
          f"pairs_skipped={totals['pairs_skipped']}")
    return 0


# ---------------------------------------------------------------------------
# Hermetic self-test (fixture-first positive control)
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Positive + negative controls with INJECTED slice_role / set_index (no
    repo needed). Mirrors the REAL M52/M56 case (verified live against
    MAGPIE_DIR=/private/tmp/magpie_develop_ro before this fixture was written —
    see check_attribution_omissions.py's own self-test for the identical
    slice-role shape, reused here for the SAME real variable/modules).
    """
    ok = True

    def check(label, got, expect):
        nonlocal ok
        if got == expect:
            print(f"  SELF-TEST PASS [{label}]")
        else:
            ok = False
            print(f"  SELF-TEST FAIL [{label}]: expected {expect!r}, got {got!r}")

    set_index = {
        "emis_oneoff": frozenset({"co2_c"}),
        "emis_annual": frozenset({"ch4", "n2o_n_direct"}),
        "pollutants_maccs57": frozenset({"ch4", "n2o_n_direct"}),
    }
    # MANDATORY CONTROL 1 (positive): producer's write and consumer's read are
    # provably disjoint on the only pair -> must flag.
    slice_role_disjoint = {
        "vm_emissions_reg": {
            "52": {"POPULATE": [("i2", "emis_oneoff", '"co2_c"')]},
            "56": {"READ": [("i2", "emis_annual", "pollutants_maccs57")]},
        },
    }
    # MANDATORY CONTROL 2 (negative): an INTERSECTING pair (same slice) -> must
    # NOT flag, even though the claim shape is otherwise identical.
    slice_role_intersect = {
        "vm_emissions_reg": {
            "52": {"POPULATE": [("i2", "emis_oneoff", '"co2_c"')]},
            "56": {"READ": [("i2", "emis_oneoff", '"co2_c"')]},
        },
    }
    # MANDATORY CONTROL 3 (negative, CRITICAL): an UNRESOLVED dimension on the
    # only pair -> ambiguous, never treated as disjoint -> must NOT flag.
    slice_role_unresolved = {
        "vm_emissions_reg": {
            "52": {"POPULATE": [("i2", "emis_oneoff", '"co2_c"')]},
            "56": {"READ": [("i2", "emis_oneoff", "totally_unknown_token")]},
        },
    }

    to_field_doc = (
        "**1. vm_emissions_reg** (Module 56 declarations.gms)\n"
        "- **Dimensions**: `(i,emis_source,pollutants)`\n"
        "- **Consumers**: Module 56 (GHG Policy) for carbon pricing.\n"
    )

    findings, stats = scan_doc(to_field_doc, "modules/module_52.md", slice_role_disjoint, set_index)
    check("MANDATORY positive: disjoint hand-off -> flagged",
          {(f["producer"], f["consumer"]) for f in findings}, {("52", "56")})
    check("  coverage counted (claims_found=1, pairs_bound=1, pairs_skipped=0)",
          (stats["claims_found"], stats["pairs_bound"], stats["pairs_skipped"]), (1, 1, 0))

    findings2, _ = scan_doc(to_field_doc, "modules/module_52.md", slice_role_intersect, set_index)
    check("MANDATORY negative: intersecting slices -> NOT flagged", findings2, [])

    findings3, _ = scan_doc(to_field_doc, "modules/module_52.md", slice_role_unresolved, set_index)
    check("MANDATORY negative (critical): unresolved dimension -> NOT flagged (never a false disjoint)",
          findings3, [])

    # NEGATIVE — negation clause kills the claim entirely (correct statement of
    # absence, not a hand-off assertion).
    negated_doc = (
        "**1. vm_emissions_reg** (Module 56 declarations.gms)\n"
        "- **Consumers**: Module 56 does NOT consume this slice for pricing.\n"
    )
    findings4, _ = scan_doc(negated_doc, "modules/module_52.md", slice_role_disjoint, set_index)
    check("NEGATIVE: negated clause -> NOT flagged", findings4, [])

    # NEGATIVE — hedge suppresses (partial-list framing, not a firm claim).
    hedge_doc = (
        "**1. vm_emissions_reg** (Module 56 declarations.gms)\n"
        "- **Consumers**: primarily Module 56, among others.\n"
    )
    findings5, _ = scan_doc(hedge_doc, "modules/module_52.md", slice_role_disjoint, set_index)
    check("NEGATIVE: hedged claim -> NOT flagged", findings5, [])

    # NEGATIVE — fenced code example skipped entirely.
    fenced_doc = (
        "```\n"
        "**1. vm_emissions_reg** (Module 56 declarations.gms)\n"
        "- **Consumers**: Module 56\n"
        "```\n"
    )
    findings6, _ = scan_doc(fenced_doc, "modules/module_52.md", slice_role_disjoint, set_index)
    check("NEGATIVE: fenced code -> NOT flagged", findings6, [])

    # POSITIVE — the module_56.md:66 REAL shape: self-contained bullet
    # ("- **VAR(dims)**: ... from the emission modules (A, B, C)"), bare
    # bold-wrapped module-number enumeration, doc_own=56 is the READER.
    from_field_doc = (
        "**Components:**\n\n"
        "- **v56_emis_pricing(i,emis_annual,pollutants)**: Emissions used for pricing (Tg/yr)\n"
        "- **vm_emissions_reg(i,emis_annual,pollutants)**: Actual regional emissions from "
        "the emission modules (51 N2O, **52 LULUCF CO2**, 53 CH4, 58 peatland) (Tg/yr)\n"
    )
    slice_role_56 = {
        "vm_emissions_reg": {
            "51": {"POPULATE": [("i2", "emis_annual", "n_pollutants_direct")]},
            "52": {"POPULATE": [("i2", "emis_oneoff", '"co2_c"')]},
            "53": {"POPULATE": [("i2", "emis_annual", '"ch4"')]},
            "58": {"POPULATE": [("i2", "emis_annual", "poll58")]},
            "56": {"READ": [("i2", "emis_annual", "pollutants")]},
        },
    }
    set_index_56 = {
        "emis_oneoff": frozenset({"co2_c"}),
        "emis_annual": frozenset({"man_crop", "inorg_fert", "ch4", "n2o_n_direct", "peatland"}),
        "n_pollutants_direct": frozenset({"n2o_n_direct"}),
        "poll58": frozenset({"co2_c", "ch4", "n2o_n_direct"}),
        "pollutants": frozenset({"co2_c", "ch4", "n2o_n_direct", "nh3_n"}),
    }
    findings7, stats7 = scan_doc(from_field_doc, "modules/module_56.md", slice_role_56, set_index_56)
    check("POSITIVE (real module_56.md:66 shape): only M52 flagged, 51/53/58 rescued by overlap",
          {(f["producer"], f["consumer"]) for f in findings7}, {("52", "56")})
    check("  coverage counted (claims_found=1, pairs_bound=4)",
          (stats7["claims_found"], stats7["pairs_bound"]), (1, 4))

    # POSITIVE — arrow form, doc_own-independent.
    arrow_doc = "`vm_emissions_reg` flows Module 52 -> Module 56 for pricing.\n"
    findings8, _ = scan_doc(arrow_doc, "modules/module_99.md", slice_role_disjoint, set_index)
    check("POSITIVE: arrow form flags the named pair regardless of doc_own",
          {(f["producer"], f["consumer"]) for f in findings8}, {("52", "56")})

    # NEGATIVE — coverage-skip: a var with NO code-side slice data at all must
    # be SKIPPED, not silently treated as disjoint.
    no_data_doc = (
        "**1. vm_unknown_var** (Module 56 declarations.gms)\n"
        "- **Consumers**: Module 56\n"
    )
    findings9, stats9 = scan_doc(no_data_doc, "modules/module_52.md", slice_role_disjoint, set_index)
    check("NEGATIVE: no code-side slice data -> skipped, not flagged", findings9, [])
    check("  coverage counted as skipped (pairs_skipped=1, pairs_bound=0)",
          (stats9["pairs_bound"], stats9["pairs_skipped"]), (0, 1))

    # NEGATIVE (critical, found on the REAL corpus, not synthesized in advance):
    # a HETEROGENEOUS producer -- writes the var via >1 DISTINCT literal slice
    # (e.g. separate "vegc"/"litc" pool statements, the real
    # pm_carbon_density_secdforest_ac / fm_carbon_density shape) -- must be
    # SKIPPED, never flagged, even though ONE of its slices (litc) is genuinely
    # disjoint from the consumer's read (vegc): the OTHER slice (vegc) is the
    # one that actually matches, so picking either single pairing to "prove
    # disjoint" would be a false positive. This is the false positive this
    # checker actually produced on module_52.md before the producer-homogeneity
    # gate was added to _evaluate_pair.
    slice_role_heterogeneous = {
        "vm_test_multi_pool": {
            "52": {"POPULATE": [("t_all", "j", "ac", '"vegc"'), ("t_all", "j", "ac", '"litc"')]},
            "14": {"READ": [("t", "j", "ac", '"vegc"')]},
        },
    }
    set_index_hetero = {}  # ac/j/t/t_all all deliberately unresolved (mirrors the real case)
    hetero_doc = (
        "**1. vm_test_multi_pool** (Module 52 declarations.gms)\n"
        "- **Consumers**: Module 14 (im_growing_stock computation)\n"
    )
    findings10, stats10 = scan_doc(hetero_doc, "modules/module_52.md", slice_role_heterogeneous,
                                    set_index_hetero)
    check("NEGATIVE (critical, real-corpus-derived): heterogeneous producer slice -> "
          "NOT flagged despite one occurrence being disjoint", findings10, [])
    check("  coverage counted as skipped, not bound (pairs_skipped=1, pairs_bound=0)",
          (stats10["pairs_bound"], stats10["pairs_skipped"]), (0, 1))

    if ok:
        print(f"{CHECK_NAME} self-test: PASS")
        print(f"SELFTEST_OK {CHECK_NAME}")
        return 0
    print(f"{CHECK_NAME} self-test: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
