#!/usr/bin/env python3
"""check_dependent_counts.py — mechanized checker for STALE DEPENDENT-COUNT claims.

Targets the `set_membership` bug class identified in the R55 depth audit as the
2nd-worst residual class (15.9 findings / 100 claims): a doc says "N modules"
(depend on / are provided to / consume / are affected by a var or the whole
module) and N has drifted out of sync with the code. The anchor bug: module_10.md
carried a stale "15 modules" claim at TEN sites when the true value was 18.

WHAT THIS CHECKS
--------------------------------------------------------------------------
Every `modules/module_NN.md` is scanned for lines matching one of a small set
of DEPENDENT-COUNT claim shapes (see PATTERN_SPECS below), each of which
asserts "N modules [are dependents / consume / read / are affected]" — i.e.
the DOWNSTREAM direction only (this checker does NOT evaluate "DEPENDS ON (N
modules)" / "Consumes from: N modules" style UPSTREAM claims — see LIMITS).

For each claim, an integer N is captured together with the claim's LINE. The
line is then classified NAMED vs whole-module (NAMED resolution is UNIFORM
and var-FIRST across every trigger — see the note on "downstream_bare" below):

  NAMED = the distinct backticked cross-module interface vars (vm_/pm_/im_/
          pcm_/fm_) found on the claim line (via
          `check_attribution_omissions._cross_vars_backticked`), for every
          trigger — EXCEPT the "N modules depend on TARGET" construct, whose
          own regex captures TARGET directly (with optional backticks)
          because this phrasing conventionally names the variable in plain
          prose, unbackticked (see module_10.md:870, a designated validation
          fixture: "10 modules depend on vm_land" — `vm_land` is NOT
          backticked there, and the claim is 10/10 correct today; see LIMITS
          for why this is a deliberate, narrow exception).

TRUTH (role-map-derived; the same ground truth check_attribution_omissions
uses, built by `build_role_map()` over `<MAGPIE_DIR>/modules/**/*.gms`):

  - If NAMED is non-empty (a per-var claim):
      truth = | union over v in NAMED of {modules that READ v} |
              minus {v's declarer, for each v in NAMED}
              minus {the doc's own module}
  - If NAMED is empty (a whole-module claim):
      truth = | union over ALL vars whose declarer is the doc's own module of
                {modules that READ v} |
              minus {the doc's own module}

A claim whose N != truth is a MISMATCH (stale dependent-count). A claim whose
var(s) are not present in the role map (never seen in any *.gms) — or whose
"var-scoped-only" trigger (used by / consumers of / provides interface to
... via) finds NO backticked var on its own line — is UNBOUND / AMBIGUOUS and
is SKIPPED (counted, not guessed; precision over recall). A "whole-module"
trigger with no backticked var but a PLAIN (unbackticked) var mention
somewhere on the line is ALSO skipped rather than resolved whole-module — see
`_has_stray_plain_var` (a real corpus case: module_51.md:471 names
`vm_emissions_reg` in plain prose, unbackticked, but that var is declared by
Module 56, not the doc's own Module 51 — falling back to "vars Module 51
declares" would silently compare the claim to the wrong variable's readers).

PATTERN SCOPE (DOWNSTREAM ONLY — see LIMITS for what is deliberately NOT seen)
--------------------------------------------------------------------------
  "whole"-CAPABLE triggers (whole-module ONLY as a fallback — if the line
  ALSO backtick-names a var, that var's per-var truth wins instead; this is
  not optional: module_30.md:23 pairs a `downstream_bare` trigger with a
  backticked `vm_area(j,kcr,w)` on the same line, and treating it as
  whole-module produces a false 7-vs-9 mismatch):
    "PROVIDES TO (N modules)"            -> provides_to_paren
    "**Provides to**: N modules (...)"   -> provides_to_colon
    "Provides interface to: N modules"   -> provides_iface_bare (no "via ...")
    "affect **N other/downstream modules**" -> affect
    "N downstream modules"               -> downstream_bare
    "N modules depend on it/this/them"   -> depend_on (generic-pronoun target)

  "var"-ONLY triggers (require a backticked cross-iface var on the SAME line;
  if none is found the claim is SKIPPED as ambiguous — whole-module is never
  a credible fallback for these, since the phrasing inherently names a
  specific referent):
    "... used by N modules"              -> used_by
    "consumers? of `V` ... (N modules"   -> consumers_of
    "Provides interface to: N modules via `V1`, `V2`, ..." -> provides_iface_via

  auto-classified (the ONE construct whose var target is captured directly,
  backticked or not — see the docstring intro):
    "N modules depend(s) on TARGET"      -> depend_on
      TARGET matches a cross-iface var shape (backticked or not) -> var-scoped
      TARGET is a generic pronoun (it/this/them)                 -> whole-module
      anything else (e.g. "Module", a different module's name)   -> SKIPPED
      (ambiguous — likely refers to a specific OTHER module, out of scope for
      this doc-centric truth formula)

LIMITS (what this checker CANNOT see — read before trusting a "0 findings")
--------------------------------------------------------------------------
  1. UPSTREAM claims are entirely out of scope: "DEPENDS ON (N modules)",
     "Consumes from: N modules", "Receives from: N modules" are never matched
     — evaluating them would need the POPULATE-direction analogue of this
     truth formula, which this checker does not implement.
  2. A bare "(N modules)" with NO trigger phrase on the line is deliberately
     NOT matched — the only "(N modules)" shape recognized is anchored to a
     "provides to" trigger. A fully generic "(N modules)" pattern would also
     fire on "DEPENDS ON (2 modules)" headers (an upstream claim -- wrong
     direction) and was rejected for that reason.
  3. A "whole"-capable trigger with NO var mention at all anywhere on the
     line (backticked or plain) resolves whole-module using the vars the
     DOC'S OWN module declares. If the true subject is a variable declared by
     a DIFFERENT module and that variable is named nowhere on the line at all
     (not even in plain prose) — e.g. only implied by surrounding paragraph
     context — this checker has no way to detect that and will silently
     compute the wrong (whole-module) truth. The plain-mention case IS caught
     (`_has_stray_plain_var` -> skip, see module_51.md:471); only a fully
     UNNAMED wrong-module claim is invisible to it.
  4. A var-scoped trigger ("used by" / "consumers of" / "... via") whose
     variable is named only on an ADJACENT line (e.g. a numbered var heading
     on line N, the count on line N+1, no backtick repetition) fires the
     trigger but finds NAMED empty on its own line, so it is SKIPPED as
     ambiguous rather than guessed whole-module (module_10.md:176 is exactly
     this shape: "(used by 10 modules)" with `vm_land` named only on the
     PRECEDING numbered-list line). This is real coverage loss, but it
     surfaces in the printed skip count — check `--verbose` output before
     assuming a clean run covered every claim in a doc.
  5. Only `modules/module_NN.md` is scanned (not `cross_module/*.md`, not
     `core_docs/*.md`) — matching the task scope this checker was built for.
  6. The role map is WHOLE-VARIABLE (same caveat as check_attribution_omissions):
     a doc's count may legitimately be scoped to one SLICE of a shared
     interface var; this checker cannot see slices and will over-count
     readers for a slice-scoped claim. Adjudicate by hand and allowlist.
  7. Fenced code blocks are skipped outright. Hedged claims (imported HEDGE_RE:
     "primary/key/e.g./etc/such as/..." PLUS a local approximate-quantifier
     set: "roughly/approximately/about/around/~/at least/up to/...") are also
     skipped, but the hedge search is WINDOWED to ~20 chars around the
     claim's own match span, not the whole line — a whole-line search would
     let an unrelated "~" or hedge word elsewhere in a long paragraph (e.g.
     "~292 lines of code" earlier in the same bullet as a correct, precise
     "18 modules depend on it", module_10.md:778) wrongly suppress a claim
     that is not itself hedged.

Ground truth: `<MAGPIE_DIR>/modules`. Point MAGPIE_DIR at a pinned develop
worktree for an authoritative run (see magpie_agent_sync_against_develop):
    MAGPIE_DIR=/path/to/develop-worktree python3 check_dependent_counts.py

Usage:
  python3 check_dependent_counts.py [--summary-only] [--verbose]
  python3 check_dependent_counts.py --self-test   # hermetic positive control

Exit: 0 always in scan mode (advisory). --self-test returns 0/1.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_gams_variables import MAGPIE_DIR  # noqa: E402
from check_consumer_attribution import (  # noqa: E402
    build_producer_map,
    strip_dims,
    is_interface_var,
)
from check_attribution_omissions import (  # noqa: E402
    build_role_map,
    _cross_vars_backticked,
    _cross_vars,
    _debacktick,
    _mod_nums,
    HEDGE_RE,
    FENCE_RE,
    CROSS_IFACE_RE,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"
CHECK_NAME = "check_dependent_counts"


def load_allowlist() -> set[tuple[str, str]]:
    """{(file, key)} suppressed known FPs. key = "<lineno>:<pattern>".

    NOTE the real file keys its rows under "allowlist"; accept "entries" too
    (mirrors the sibling checkers' defensive read so a schema rename cannot
    silently empty the suppression list).
    """
    if not ALLOWLIST_PATH.exists():
        return set()
    try:
        data = json.loads(ALLOWLIST_PATH.read_text())
    except (ValueError, OSError):
        return set()
    rows = data if isinstance(data, list) else (data.get("allowlist") or data.get("entries") or [])
    return {(e.get("file", ""), e.get("key", "")) for e in rows if e.get("check") == CHECK_NAME}


# ---------------------------------------------------------------------------
# Count-claim hedge words. Distinct from the imported HEDGE_RE (which guards
# PARTIAL-LIST hedges — "primary", "e.g.", "such as" — the omission checker's
# concern). A dependent-COUNT claim has its own hedge class: approximate
# quantifiers, where the doc is explicitly NOT claiming a precise N.
# ---------------------------------------------------------------------------
COUNT_HEDGE_RE = re.compile(
    r"\b(?:roughly|approximately|approx\.?|about|around|circa|nearly|almost|"
    r"over|under|at\s+least|up\s+to|more\s+than|fewer\s+than|less\s+than)\b|~",
    re.IGNORECASE)


# ---------------------------------------------------------------------------
# Count-claim trigger patterns. Each fires on a de-facto DOWNSTREAM claim
# only (see module docstring LIMITS for what is deliberately excluded).
# ---------------------------------------------------------------------------
PROVIDES_IFACE_VIA_RE = re.compile(
    r"provides?\s+interface\s+to\**\s*:?\s*\**\s*(\d+)\s+modules?\b\s*via\b",
    re.IGNORECASE)
PROVIDES_IFACE_BARE_RE = re.compile(
    r"provides?\s+interface\s+to\**\s*:?\s*\**\s*(\d+)\s+modules?\b",
    re.IGNORECASE)
PROVIDES_TO_PAREN_RE = re.compile(
    r"provides?\s+to\b\s*\(\s*(\d+)\s+modules?\b", re.IGNORECASE)
PROVIDES_TO_COLON_RE = re.compile(
    r"provides?\s+to\**\s*:\s*\**\s*(\d+)\s+modules?\b", re.IGNORECASE)
# "N modules depend(s) on TARGET" — TARGET captured directly (optional
# backticks via a matched-pair group + backreference). See module docstring.
DEPEND_ON_RE = re.compile(
    r"(\d+)\s+modules?\s+depend(?:s)?\s+on\s+(`?)([A-Za-z][A-Za-z0-9_]*)\2",
    re.IGNORECASE)
AFFECT_RE = re.compile(
    r"affects?\s*\**\s*(\d+)\s*\**\s*(?:other\s+|downstream\s+)?modules?\b",
    re.IGNORECASE)
DOWNSTREAM_BARE_RE = re.compile(r"\b(\d+)\s+downstream\s+modules?\b", re.IGNORECASE)
USED_BY_RE = re.compile(r"used\s+by\s+(\d+)\s+modules?\b", re.IGNORECASE)
# ".{0,80}?" keeps the "consumers of ... (N modules" binding on ONE claim
# (a var-anchored header like "**Direct consumers of `vm_land`** (10 modules
# ...)") without letting the non-greedy gap run away across a whole paragraph.
CONSUMERS_OF_RE = re.compile(
    r"consumers?\s+of\b.{0,80}?\(\s*(\d+)\s+modules?\b", re.IGNORECASE)

# (name, regex, category) — category in {"whole", "var", "depend"}.
# Order matters: more specific triggers first so a shared substring (e.g.
# "provides interface to: N modules via ..." vs the bare form) is claimed by
# the more specific pattern first; span-tracking in extract_claims prevents
# a lower-priority pattern from double-claiming the same text.
PATTERN_SPECS = [
    ("provides_iface_via", PROVIDES_IFACE_VIA_RE, "var"),
    ("provides_iface_bare", PROVIDES_IFACE_BARE_RE, "whole"),
    ("provides_to_paren", PROVIDES_TO_PAREN_RE, "whole"),
    ("provides_to_colon", PROVIDES_TO_COLON_RE, "whole"),
    ("depend_on", DEPEND_ON_RE, "depend"),
    ("affect", AFFECT_RE, "whole"),
    ("downstream_bare", DOWNSTREAM_BARE_RE, "whole"),
    ("used_by", USED_BY_RE, "var"),
    ("consumers_of", CONSUMERS_OF_RE, "var"),
]


def _spans_free(span: tuple[int, int], claimed: list[tuple[int, int]]) -> bool:
    s, e = span
    return not any(s < e2 and s2 < e for s2, e2 in claimed)


# Window (chars) around a claim's own match span searched for a hedge word.
# Local, NOT whole-line: a whole-line hedge search lets an UNRELATED "~" or
# "roughly" elsewhere in a long paragraph (e.g. "~292 lines of code" earlier
# in the same bullet as a correct, precise "18 modules depend on it") wrongly
# suppress a claim that is not itself hedged. 20 chars before comfortably
# covers every lead-in hedge word ("approximately ", "roughly ", "e.g. ",
# "primary " before a "consumers of" trigger, ...) while excluding a stray
# tilde/hedge word two dozen characters away (verified against module_10.md:778).
HEDGE_WINDOW_BEFORE = 20
HEDGE_WINDOW_AFTER = 10


def _claim_is_hedged(line: str, span: tuple[int, int]) -> bool:
    """True if a hedge word governs this claim (checked in a window around
    its own match span, never the whole line — see HEDGE_WINDOW_* above).

    HEDGE_RE (imported; the omission checker's PARTIAL-LIST hedge set —
    "primary/key/including/other(s)/...") is checked ONLY in the surrounding
    CONTEXT (before/after the match), never inside it: this checker's OWN
    AFFECT_RE vocabulary literally contains "other" ("affect N **other**
    modules" is one of the valid, non-hedged claim shapes this checker is
    built to catch — module_10.md:14). Checking HEDGE_RE against the match's
    own interior would flag every such claim as hedged via HEDGE_RE's
    `others?` alternative — a real false-negative confirmed against the live
    corpus (module_10.md:14, "affect **18 other modules**", correct today).
    COUNT_HEDGE_RE (approximate quantifiers: roughly/about/~/...) shares no
    vocabulary with any trigger pattern here, so it is safe to check across
    the FULL window including the match interior (catches e.g. "affect
    roughly 18 modules").
    """
    s, e = span
    before = line[max(0, s - HEDGE_WINDOW_BEFORE):s]
    after = line[e:min(len(line), e + HEDGE_WINDOW_AFTER)]
    interior = line[s:e]
    if COUNT_HEDGE_RE.search(before + interior + after):
        return True
    return bool(HEDGE_RE.search(before) or HEDGE_RE.search(after))


# A cross-iface var token OUTSIDE backticks (plain prose mention). Used only
# as an AMBIGUITY guard for "whole"-category triggers — see _has_stray_plain_var.
_PLAIN_IFACE_TOKEN_RE = re.compile(r"\b(?:vm|pm|im|pcm|fm)_[a-zA-Z0-9_]+[a-zA-Z0-9]")


def _has_stray_plain_var(line: str) -> bool:
    """True if a cross-iface var is named in PLAIN TEXT (no backticks) anywhere
    on the line. Backticked spans are blanked first so a var already counted
    in NAMED is not double-detected here.

    Guards a real corpus false-positive (module_51.md:471): "Provides
    emissions (via vm_emissions_reg) to 2 downstream modules: 56 and 57" names
    `vm_emissions_reg` in plain prose, unbackticked. `vm_emissions_reg` is
    declared by Module 56, NOT Module 51 — so falling back to "whole-module
    truth = vars doc_own (51) declares" is comparing the claim to the WRONG
    variable's readers entirely (truth came out 0, not a meaningful number).
    When a plain var mention like this is present, the claim is ambiguous
    (unlike the "N modules depend on TARGET" construct, this checker has no
    principled way to resolve which module the plain-text var belongs to) —
    skip rather than compute a misleading whole-module number.
    """
    stripped = re.sub(r"`[^`]*`", " ", line)
    for m in _PLAIN_IFACE_TOKEN_RE.finditer(stripped):
        base = strip_dims(m.group())
        if is_interface_var(base):
            return True
    return False


def extract_claims(line: str) -> list[dict]:
    """Return raw count-claims on one line (pre fence filtering).

    Each claim: {count, scope, named, pattern, span[, skip_reason]}.
    scope in {"whole", "var", "skip"} — "skip" = ambiguous/hedged, ok to count
    as unevaluated but never guessed. Hedge detection is done HERE, per-claim,
    in a window around the claim's own match span (see _claim_is_hedged) —
    NOT once for the whole line — so an unrelated hedge word elsewhere in a
    long line cannot suppress an otherwise-clean, precisely-stated claim.

    NAMED resolution is UNIFORM and var-first for every category except
    "depend" (which has its own target-capture logic): if the line backtick-
    names one or more cross-iface vars, USE THEM (per-var truth), regardless
    of which trigger phrase matched — this is not optional flavor, it is
    required for correctness (module_30.md:23: "consumed by 7 downstream
    modules" — a `downstream_bare` trigger — sits on the SAME line as a
    backticked `vm_area(j,kcr,w)`; treating this as a whole-module claim
    instead of a per-var one produces a false 7-vs-9 mismatch). Only when NO
    backticked var is found does a "whole"-category trigger fall back to
    the whole-module truth — and even then, only if the line ALSO has no
    PLAIN (unbackticked) var mention (see _has_stray_plain_var); a "var"-
    category trigger (used_by / consumers_of / provides_iface_via) with no
    backticked var is always skipped as ambiguous (these triggers are
    inherently about a specific referent — "whole-module" is never a
    credible fallback for them).
    """
    claims: list[dict] = []
    claimed: list[tuple[int, int]] = []
    for name, rx, category in PATTERN_SPECS:
        for m in rx.finditer(line):
            span = m.span()
            if not _spans_free(span, claimed):
                continue
            claimed.append(span)
            count = int(m.group(1))
            if _claim_is_hedged(line, span):
                claims.append({"count": count, "scope": "skip", "named": [], "pattern": name,
                                "span": span, "skip_reason": "hedged (approximate/partial-list qualifier)"})
                continue

            if category == "depend":
                # Resolved via THIS trigger's own captured target — deliberately
                # NOT routed through the uniform NAMED-first check below: a
                # depend-on claim's scope is whatever follows "depend(s) on",
                # regardless of any OTHER backticked var that happens to sit
                # elsewhere on the same line.
                target_raw = m.group(3)
                base = strip_dims(target_raw)
                if CROSS_IFACE_RE.match(base) and is_interface_var(base):
                    claims.append({"count": count, "scope": "var", "named": [base], "pattern": name, "span": span})
                elif target_raw.lower() in ("it", "this", "them"):
                    claims.append({"count": count, "scope": "whole", "named": [], "pattern": name, "span": span})
                else:
                    claims.append({"count": count, "scope": "skip", "named": [], "pattern": name, "span": span,
                                    "skip_reason": f"ambiguous depend-on target {target_raw!r}"})
                continue

            named = _cross_vars_backticked(line)
            if named:
                claims.append({"count": count, "scope": "var", "named": named, "pattern": name, "span": span})
            elif category == "whole":
                if _has_stray_plain_var(line):
                    claims.append({"count": count, "scope": "skip", "named": [], "pattern": name, "span": span,
                                    "skip_reason": "line names a var in plain (unbackticked) text; cannot "
                                                    "confirm it belongs to the doc's own module"})
                else:
                    claims.append({"count": count, "scope": "whole", "named": [], "pattern": name, "span": span})
            else:  # category == "var"
                claims.append({"count": count, "scope": "skip", "named": [], "pattern": name, "span": span,
                                "skip_reason": "var-scoped trigger but no backticked var on the line"})
    return claims


# ---------------------------------------------------------------------------
# TRUTH — role-map-derived dependent count
# ---------------------------------------------------------------------------

def build_declared_by(producers: dict[str, str]) -> dict[str, list[str]]:
    """modnum -> [vars it declares] (inverse of build_producer_map())."""
    out: dict[str, list[str]] = {}
    for var, decl_dir in producers.items():
        if not decl_dir or "_" not in decl_dir:
            continue
        num = decl_dir.split("_", 1)[0]
        if num.isdigit():
            out.setdefault(num, []).append(var)
    return out


def compute_truth(named: list[str], role: dict, producers: dict[str, str],
                   doc_own: str | None, declared_by: dict[str, list[str]]
                   ) -> tuple[int, set[str]] | None:
    """Return (truth_count, truth_module_set) or None if truth is unknowable.

    named non-empty  -> per-var truth (union of READers over `named`, minus
                         each var's declarer, minus doc_own).
    named empty      -> whole-module truth (union of READers over every var
                         doc_own declares, minus doc_own). None if doc_own is
                         unknown or declares no var present in the role map.
    """
    if named:
        read_union: set[str] = set()
        declarers: set[str] = set()
        for v in named:
            base = strip_dims(v)
            if base not in role:
                return None  # unbound — cannot confirm truth, do not guess
            read_union |= {m for m, roles in role[base].items() if "READ" in roles}
            d = producers.get(base, "")
            if d and "_" in d:
                declarers.add(d.split("_", 1)[0])
        exclude = declarers | ({doc_own} if doc_own else set())
        truth_set = read_union - exclude
        return len(truth_set), truth_set

    if not doc_own:
        return None
    own_vars = declared_by.get(doc_own, [])
    if not own_vars:
        return None
    read_union = set()
    for v in own_vars:
        read_union |= {m for m, roles in role.get(v, {}).items() if "READ" in roles}
    truth_set = read_union - {doc_own}
    return len(truth_set), truth_set


# ---------------------------------------------------------------------------
# DOC SCAN
# ---------------------------------------------------------------------------

def scan_doc(text: str, rel_path: str, role, producers, declared_by,
             allow: set | None = None) -> tuple[list[dict], int, int, int]:
    """Return (mismatches, n_claims_found, n_evaluated, n_skipped) for one doc.

    mismatches: [{lineno, pattern, scope, named, claimed, truth, truth_set, row}]
    """
    allow = allow or set()
    fname = Path(rel_path).name
    mod_m = re.search(r"module_(\d{1,2})", fname)
    doc_own = f"{int(mod_m.group(1)):02d}" if mod_m else None

    mismatches: list[dict] = []
    n_found = n_eval = n_skipped = 0
    in_fence = False

    for lineno, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        raw = extract_claims(line)
        if not raw:
            continue
        for c in raw:
            n_found += 1
            # Hedging is already resolved per-claim inside extract_claims (a
            # windowed check around the claim's own span — see _claim_is_hedged).
            if c["scope"] == "skip":
                n_skipped += 1
                continue
            truth = compute_truth(c["named"], role, producers, doc_own, declared_by)
            if truth is None:
                n_skipped += 1
                continue
            n_eval += 1
            truth_count, truth_set = truth
            if c["count"] == truth_count:
                continue
            key = f"{lineno}:{c['pattern']}"
            if (rel_path, key) in allow or (fname, key) in allow:
                continue
            mismatches.append({
                "file": rel_path, "line": lineno, "pattern": c["pattern"],
                "scope": c["scope"], "named": c["named"], "claimed": c["count"],
                "truth": truth_count, "truth_set": sorted(truth_set, key=int),
                "row": line.strip()[:160],
            })
    return mismatches, n_found, n_eval, n_skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    summary_only = "--summary-only" in args
    verbose = "--verbose" in args

    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        print(f"{CHECK_NAME}: WARNING GAMS modules not found at {MAGPIE_DIR} - skipping.")
        return 0

    role, _realiz = build_role_map()
    producers = build_producer_map()
    declared_by = build_declared_by(producers)
    allow = load_allowlist()

    all_mismatches: list[dict] = []
    total_found = total_eval = total_skipped = 0
    n_docs = 0

    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        if doc.name.endswith("_notes.md"):
            continue
        n_docs += 1
        rel = str(doc.relative_to(AGENT_DIR))
        text = doc.read_text(encoding="utf-8", errors="ignore")
        mism, nf, ne, ns = scan_doc(text, rel, role, producers, declared_by, allow)
        all_mismatches.extend(mism)
        total_found += nf
        total_eval += ne
        total_skipped += ns

    # Coverage denominator ALWAYS printed — a "0 findings" over few evaluated
    # claims is BLIND, not clean.
    print(f"{CHECK_NAME}: coverage = {total_found} dependent-count claim(s) found across "
          f"{n_docs} docs; {total_eval} bound + evaluated against the role-map truth, "
          f"{total_skipped} skipped (hedged / ambiguous / var not in role map).")
    print(f"{CHECK_NAME}: role map = {len(role)} interface vars; "
          f"{len(declared_by)} modules with a declared-var index.")

    if total_eval == 0:
        print(f"\n{CHECK_NAME}: 0 claims evaluated — this run proves NOTHING about doc "
              f"accuracy (BLIND, not clean). Check MAGPIE_DIR and pattern coverage.")
    elif all_mismatches:
        print(f"\n{CHECK_NAME}: {len(all_mismatches)} MISMATCH(es) (stale dependent count):")
        rows = all_mismatches if not summary_only else all_mismatches[:30]
        for f in rows:
            named = f"`{'`, `'.join(f['named'])}`" if f["named"] else "(whole-module)"
            print(f"  {f['file']}:{f['line']}  [{f['pattern']}] {named} claims "
                  f"{f['claimed']} modules but role-map truth is {f['truth']} "
                  f"(modules: {','.join(f['truth_set'])}). Line: {f['row']}")
        if summary_only and len(all_mismatches) > 30:
            print(f"  ... and {len(all_mismatches) - 30} more")
    else:
        print(f"\n{CHECK_NAME}: 0 mismatches within {total_eval} evaluated claim(s).")

    if verbose:
        print(f"\n{CHECK_NAME}: NOTE — {total_skipped} claim(s) skipped this run "
              f"(precision over recall: an unresolvable claim is never guessed).")

    print(f"\n{CHECK_NAME}: NOTE this checker sees DOWNSTREAM count claims only "
          f"(provides-to / consumers-of / used-by / depend-on / affect / downstream) — "
          f"see the module docstring LIMITS for upstream (\"DEPENDS ON\") and adjacent-line "
          f"forms it structurally cannot bind. Confirm against develop before any doc edit.")
    print(f"{CHECK_NAME}: SUMMARY mismatches={len(all_mismatches)} evaluated={total_eval} "
          f"skipped={total_skipped} coverage_claims={total_found} docs={n_docs}")
    return 0


# ---------------------------------------------------------------------------
# Hermetic self-test (fixture-first positive control)
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Positive + negative controls with INJECTED role/producer maps — hermetic,
    no repo required. Mirrors the real R55 bug shape: a stale whole-module
    count ("15 modules" claimed, 18 true) plus a per-var wrong count, guarded
    against hedges, fenced code, and non-module counts.
    """
    ok = True

    # Small, hand-countable fixture (deliberately NOT module_10's real numbers,
    # to keep the arithmetic independently checkable at a glance):
    #   vm_alpha declared by M10, READ by {20,30,40}          -> 3 readers
    #   vm_beta  declared by M10, READ by {30,50}              -> 2 readers
    #   pm_gamma declared by M10, READ by {60}                 -> 1 reader
    # whole-module truth (doc_own=10) = |{20,30,40,50,60}| = 5
    role = {
        "vm_alpha": {"10": {"POPULATE"}, "20": {"READ"}, "30": {"READ"}, "40": {"READ"}},
        "vm_beta": {"10": {"POPULATE"}, "30": {"READ"}, "50": {"READ"}},
        "pm_gamma": {"10": {"POPULATE"}, "60": {"READ"}},
    }
    producers = {"vm_alpha": "10_land", "vm_beta": "10_land", "pm_gamma": "10_land"}
    declared_by = build_declared_by(producers)

    def run(text: str, fname: str = "modules/module_10.md"):
        return scan_doc(text, fname, role, producers, declared_by)

    cases = []

    # POSITIVE 1 — the R55 shape: whole-module claim understates the true count.
    cases.append((
        "pos-whole-stale",
        "#### **PROVIDES TO (3 modules)** - stale, should be 5\n",
        1,  # expect 1 mismatch
    ))
    # POSITIVE 2 — per-var claim with the wrong count.
    cases.append((
        "pos-var-wrong",
        "5 modules depend on `vm_alpha`\n",  # true = 3
        1,
    ))
    # NEGATIVE 1 — correct whole-module count.
    cases.append((
        "neg-whole-correct",
        "#### **PROVIDES TO (5 modules)**:\n",
        0,
    ))
    # NEGATIVE 2 — correct per-var count.
    cases.append((
        "neg-var-correct",
        "3 modules depend on `vm_alpha`\n",
        0,
    ))
    # NEGATIVE 3 — approximate-count hedge ("roughly").
    cases.append((
        "neg-hedge-roughly",
        "roughly 15 modules depend on `vm_alpha`\n",
        0,
    ))
    # NEGATIVE 4 — partial-list hedge ("e.g.") via the imported HEDGE_RE.
    cases.append((
        "neg-hedge-eg",
        "e.g. 15 modules depend on `vm_alpha`\n",
        0,
    ))
    # NEGATIVE 5 — fenced code block.
    cases.append((
        "neg-fence",
        "```\n#### **PROVIDES TO (15 modules)**\n```\n",
        0,
    ))
    # NEGATIVE 6 — a count that is NOT about modules (var-count table cell, pool count).
    cases.append((
        "neg-not-module-count",
        "| **59_som** | pcm_land, vm_land (4) | Soil carbon tracking |\n"
        "MAgPIE distinguishes **7 land pools** in this section.\n",
        0,
    ))
    # NEGATIVE 7 — the module_10.md:870 shape: plain (unbackticked) var target
    # after "depend on" must be recognized as NAMED via the depend_on capture,
    # not fall through to a wrong whole-module truth.
    cases.append((
        "neg-depend-on-plain-var",
        "Review dependency list (3 modules depend on vm_alpha; 5 depend on Module 10 overall)\n",
        0,  # "3 modules depend on vm_alpha" -> var-scoped truth=3, correct.
    ))
    # NEGATIVE 8 — used-by trigger with NO backticked var on the line -> must be
    # SKIPPED (ambiguous), never guessed whole (this is the module_10.md:176 shape).
    cases.append((
        "neg-used-by-no-var-ambiguous",
        "**Most shared variable in MAgPIE** (used by 3 modules)\n",  # would be a
        # false mismatch (3 != 5) if wrongly treated as whole-module; must be
        # SKIPPED instead, so 0 mismatches.
        0,
    ))
    # NEGATIVE 9 — unknown variable (not in the injected role map) -> unbound,
    # skipped, never guessed.
    cases.append((
        "neg-unknown-var-unbound",
        "99 modules depend on `vm_nonexistent`\n",
        0,
    ))

    for label, text, expect_n in cases:
        mism, nf, ne, ns = run(text)
        got_n = len(mism)
        if got_n == expect_n:
            print(f"  SELF-TEST PASS [{label}] (found={nf} eval={ne} skipped={ns} mismatches={got_n})")
        else:
            ok = False
            print(f"  SELF-TEST FAIL [{label}]: expected {expect_n} mismatch(es), got {got_n}: {mism}")

    # REGRESSION — module_10.md:778 shape: an UNRELATED tilde/hedge word
    # elsewhere in a long line ("~292 lines of code") must NOT suppress a
    # correct, precisely-stated claim later in the same line ("18 modules
    # depend on it"). This must be EVALUATED (not skipped) and clean.
    regress_text = "- Only ~292 lines of code, but **5 modules depend on it**\n"
    mism, nf, ne, ns = run(regress_text)
    if ne < 1 or mism:
        ok = False
        print(f"  SELF-TEST FAIL [neg-unrelated-tilde-not-hedge]: expected eval>=1 and 0 "
              f"mismatches (a distant '~' must not hedge-suppress this claim), "
              f"got eval={ne} mismatches={mism}")
    else:
        print(f"  SELF-TEST PASS [neg-unrelated-tilde-not-hedge] (eval={ne} mismatches=0)")

    # REGRESSION — module_10.md:14 shape: "affect N **other** modules" must
    # NOT be treated as hedged just because HEDGE_RE's `others?` alternative
    # matches the word "other" that is structurally part of AFFECT_RE's own
    # match (see _claim_is_hedged docstring). Must be evaluated and clean.
    other_text = "**Impact**: Changes to this module affect **5 other modules** - testing must be comprehensive\n"
    mism, nf, ne, ns = run(other_text)
    if ne < 1 or mism:
        ok = False
        print(f"  SELF-TEST FAIL [neg-affect-other-not-hedge]: expected eval>=1 and 0 "
              f"mismatches ('other' inside the trigger's own match must not self-hedge), "
              f"got eval={ne} mismatches={mism}")
    else:
        print(f"  SELF-TEST PASS [neg-affect-other-not-hedge] (eval={ne} mismatches=0)")

    # REGRESSION — module_30.md:23 shape: a "whole"-capable trigger
    # (downstream_bare) sharing a line with a backticked var must resolve to
    # the VAR's truth, not the whole-module truth. vm_alpha's true reader
    # count is 3 (20,30,40); a whole-module claim would wrongly compare
    # against 5. Claiming 3 here must be CLEAN, proving the per-var path won.
    paired_text = "Provides the interface variable `vm_alpha` that is consumed by 3 downstream modules.\n"
    mism, nf, ne, ns = run(paired_text)
    if ne < 1 or mism:
        ok = False
        print(f"  SELF-TEST FAIL [neg-downstream-bare-with-backticked-var]: expected eval>=1 "
              f"and 0 mismatches (must bind to vm_alpha's truth=3, not whole-module truth=5), "
              f"got eval={ne} mismatches={mism}")
    else:
        print(f"  SELF-TEST PASS [neg-downstream-bare-with-backticked-var] (eval={ne} mismatches=0)")
    # Same shape, WRONG count (5, the whole-module number) — must be flagged
    # as a mismatch against vm_alpha's true 3, proving it did NOT silently
    # accept the whole-module truth as an alternative correct answer.
    paired_wrong_text = "Provides the interface variable `vm_alpha` that is consumed by 5 downstream modules.\n"
    mism, nf, ne, ns = run(paired_wrong_text)
    if len(mism) != 1 or mism[0]["truth"] != 3:
        ok = False
        print(f"  SELF-TEST FAIL [pos-downstream-bare-with-backticked-var-wrong]: expected 1 "
              f"mismatch with truth=3, got {mism}")
    else:
        print(f"  SELF-TEST PASS [pos-downstream-bare-with-backticked-var-wrong] (truth=3 confirmed)")

    # REGRESSION — module_51.md:471 shape: a "whole"-capable trigger with NO
    # backticked var but a PLAIN (unbackticked) var mention elsewhere on the
    # line must be SKIPPED as ambiguous, never resolved whole-module (the
    # plain var may belong to a DIFFERENT module — see _has_stray_plain_var).
    stray_text = "Provides emissions (via vm_alpha) to 2 downstream modules: 20 and 30.\n"
    mism, nf, ne, ns = run(stray_text)
    if nf < 1 or ns < 1 or mism:
        ok = False
        print(f"  SELF-TEST FAIL [neg-stray-plain-var-ambiguous]: expected found>=1, "
              f"skipped>=1, 0 mismatches (a plain var mention must skip, not guess "
              f"whole-module), got found={nf} skipped={ns} mismatches={mism}")
    else:
        print(f"  SELF-TEST PASS [neg-stray-plain-var-ambiguous] (found={nf} skipped={ns})")

    # Extra assertion: the used-by-no-var case must be SKIPPED, not silently
    # dropped as "no claim found" — otherwise the 0-mismatch result above could
    # be hiding a coverage bug rather than a correct skip.
    _, nf, ne, ns = run("**Most shared variable in MAgPIE** (used by 3 modules)\n")
    if nf < 1 or ns < 1:
        ok = False
        print(f"  SELF-TEST FAIL [used-by-no-var-must-be-counted-as-skip]: "
              f"found={nf} skipped={ns} (expected found>=1 and skipped>=1)")
    else:
        print("  SELF-TEST PASS [used-by-no-var-must-be-counted-as-skip]")

    # Extra assertion: the 4 named-var case (module_10.md:838 shape) resolves
    # to the UNION of all four vars' readers, minus the shared declarer.
    multi_text = "**Provides interface to**: 5 modules via `vm_alpha`, `vm_beta`, `pm_gamma`\n"
    mism, nf, ne, ns = run(multi_text)
    # union READ({vm_alpha,vm_beta,pm_gamma}) = {20,30,40,50,60} minus {10} = 5
    if mism:
        ok = False
        print(f"  SELF-TEST FAIL [multi-var-union]: expected clean (truth=5), got {mism}")
    else:
        print("  SELF-TEST PASS [multi-var-union]")
    wrong_multi_text = "**Provides interface to**: 4 modules via `vm_alpha`, `vm_beta`, `pm_gamma`\n"
    mism, nf, ne, ns = run(wrong_multi_text)
    if len(mism) != 1 or mism[0]["truth"] != 5:
        ok = False
        print(f"  SELF-TEST FAIL [multi-var-union-wrong]: expected 1 mismatch truth=5, got {mism}")
    else:
        print("  SELF-TEST PASS [multi-var-union-wrong]")

    if ok:
        print(f"{CHECK_NAME} self-test: PASS")
        print(f"SELFTEST_OK {CHECK_NAME}")
        return 0
    print(f"{CHECK_NAME} self-test: FAIL")
    return 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(main())
