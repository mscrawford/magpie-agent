#!/usr/bin/env python3
"""check_bindability.py — Check 37, ADVISORY coverage/to-do checker.

*** THIS CHECK PRODUCES A COVERAGE / TO-DO LIST, NOT A DEFECT LIST. ***
A finding here means "this attribution-shaped claim cannot be MECHANICALLY
verified" — it NEVER means "this claim is wrong". Read every finding as
"needs a var name so a future run of Checks 34/36 can check it", not as a bug.

WHY THIS EXISTS
--------------------------------------------------------------------------
The mechanical attribution layer (Checks 31/32/33/34/35/36 — check_role_
attribution.py, check_attribution_tables.py, check_attribution_prose.py,
check_attribution_omissions.py, check_dependent_counts.py, check_dependent_
direction.py) can only verify a claim that NAMES its interface variable as a
backticked identifier — the diff against code truth (build_role_map /
build_consumer_map / build_producer_map) is keyed on that identifier. R55
measured `attribution_populate` at 10.71 findings per 100 claims, and
follow-up analysis showed its actual instances are UNBINDABLE, not
un-mechanized:
  - modules/module_52.md:711-718 (the real fixture this check's self-test
    mirrors): "**6. Land Modules** (provide carbon stocks to Module 56): -
    Module 31 (Pasture): Pasture carbon stocks" — prose, no `vm_carbon_stock`
    (or any other) identifier anywhere in the claim.
  - a bare file citation ("populated in `postsolve.gms:9`") is a FILE
    reference, not a module-attribution list — nothing for a role-map diff
    to bind to either.
A role-map diff has nothing to bind to in either shape. Pretending to check
these would either (a) silently skip them (a false "clean" signal) or (b) try
to guess a var and risk a FABRICATED citation. Instead, this check FLAGS the
shape itself: attribution-context content that names >=1 module but ZERO
backticked cross-module interface vars in scope. That is the blind spot,
surfaced honestly.

WHAT COUNTS AS "IN SCOPE" (per the task's exact bindability test)
--------------------------------------------------------------------------
A line is a BINDABILITY CANDIDATE when:
  (a) it sits in an ATTRIBUTION CONTEXT — a hard SECTION header (`SECTION_KW_
      RE` armed at a `HEADER_RE` line, exactly as check_attribution_prose.
      scan_doc does), OR an inline TRIGGER verb on the line itself (`TRIGGER_
      RE`, plus a var-BLOCK FIELD LABEL — "**Consumers**:" / "**Populated
      by**:" — which is an attribution row by construction even though it
      never carries a trigger VERB), OR it is a bullet continuing a "soft
      anchor" (a non-header line ending in ':' that itself qualified as
      attribution context — the exact shape of the module_52.md fixture,
      where the heading is bolded prose, not a markdown/HEADER_RE section);
  (b) it names >=1 module ("Module NN" / "NN_name" / a "Modules N, M, and P"
      list — all three forms handled by ONE reused function, `_mod_nums`);
  (c) it is not a negation ("Module 38 is NOT a consumer of...") or
      historical/changelog aside (both correctly describe an ABSENCE or a
      past state, not a live unbound claim).
A candidate is BINDABLE iff a backticked cross-module interface var
(vm_/pm_/im_/pcm_/fm_) is IN SCOPE: on the line itself, OR — if the line
sits under a bolded var-heading block ("**1b. pm_carbon_density_..._uncalib**
(declarations.gms:10)" followed by field bullets) — the var named by that
heading. Zero in-scope vars = UNBINDABLE = a to-do item.

REUSE, DO NOT REIMPLEMENT
--------------------------------------------------------------------------
Every regex/function below is imported, not recreated, from the two modules
that already solved this sub-problem:
  check_attribution_prose.py    — HEADER_RE, SECTION_KW_RE, TRIGGER_RE (the
                                   section-arm / inline-trigger state machine
                                   this check's "hard" half mirrors exactly).
  check_attribution_omissions.py — _debacktick, _mod_nums, _cross_vars_
                                   backticked, _cross_vars (claim-detection
                                   primitives); NEGATION_RE, HISTORICAL_RE,
                                   FENCE_RE, HEDGE_RE, LIST_CONT_RE (FP
                                   guards + list-continuation matcher);
                                   _MD_HEAD_RE, _VARBLOCK_HEAD_RE, _FIELD_
                                   READ_RE, _FIELD_POP_RE (the var-BLOCK
                                   scoping state machine from parse_doc_
                                   varblock_triples, byte-for-byte the same
                                   open/close rule — reused, not reimplemented,
                                   so the two checks can never disagree about
                                   which var a "Consumers:" bullet inherits).
  check_gams_variables.py       — MAGPIE_DIR (printed for transparency only;
                                   this check is PURE DOC-PROSE — it never
                                   reads GAMS code, so MAGPIE_DIR does not
                                   gate anything here).
HEDGE_RE is deliberately used as METADATA, not a suppressor: in check_
attribution_omissions.py a hedge ("primary/key/e.g./etc") legitimately
suppresses an OMISSION finding, because a hedge disproves the COMPLETENESS
a real omission needs. A bindability finding asserts no such completeness —
"no var is named" stays true whether the prose hedges or not — so a hedged
claim is still flagged, just tagged `[hedged]` so a maintainer can
deprioritize it in the to-do list.

DESIGN — precision-first on CLAIM DETECTION, tolerant on the finding itself
--------------------------------------------------------------------------
The claim-detection primitives (`_mod_nums`, negation/historical/fence
guards) are the same precision-first primitives the sibling mechanical
checks rely on, so this check is no noisier at deciding "is this an
attribution claim" than they are. But because the OUTPUT here is an advisory
to-do list rather than a pass/fail defect count, a modest false-positive rate
on the FLAGGING side (e.g. a transitional sentence like "Module 52 **provides
to** these modules:" gets flagged too, alongside the real per-module bullets)
is explicitly tolerated rather than chased — see "HONEST LIMITS" below.

HONEST LIMITS
--------------------------------------------------------------------------
  THE RATIO IS AN UPPER BOUND, NOT A MEASUREMENT. Do not quote it as "N% of
  attribution is unverifiable". Claim-DETECTION is deliberately loose (the output
  is a to-do list, so a modest FP rate is tolerated), and the residual FP classes
  are known and unfixed:
    - non-claim prose that happens to carry a trigger verb + a module number, e.g.
      "**Core Function**: Module 10 is the central land ..." (module_10.md:10),
      "**Rank**: 2nd most depended-upon module (after 09_drivers)" (:277);
    - illustrative notes, e.g. "*These are made-up numbers for illustration ...
      Modules 70 ...*" (module_53.md:155).
  These inflate UNBINDABLE. The number is therefore a ceiling on the blind spot
  and a prioritised to-do list -- useful for "where can the mechanical layer not
  see", useless as a statistic.

  BINDABLE is aligned with what Check 34 ACTUALLY binds: a backticked var in
  scope (line or enclosing var-block heading) OR, for a markdown TABLE ROW, a
  bare-text var in the cell (Check 34's `_cross_vars_backticked(col2) or
  _cross_vars(col2)` fallback). An earlier backticked-only definition reported
  the PROVIDES-TO table rows as blind when Check 34 sees them fine -- a 5.6-point
  over-report. "Bindable" must track real coverage, not a stricter proxy.
- Trigger vocabulary is TRIGGER_RE (check_attribution_prose's inline-verb
  list) + the two var-BLOCK field labels, NOT the (differently-shaped)
  READ_TRIGGER_RE / POP_TRIGGER_RE prose vocabulary used internally by
  check_attribution_omissions.py (e.g. "consumers of `V`"). A line like
  "**Direct consumers of `vm_land`**: Module 29" is therefore sometimes
  simply never EXAMINED by this check (no recognized trigger) rather than
  examined-and-found-bindable — harmless for THIS check's purpose (it always
  already carries a backticked var, so it was never going to be a finding),
  but means the "examined" denominator is not a strict superset of what
  Check 34's own triple-parser sees.
- "Soft anchor" list continuation (a bolded, colon-terminated line that is
  not a markdown/HEADER_RE section but reads like one, e.g. "**6. Land
  Modules** (provide carbon stocks to Module 56):") arms a following bullet
  list until a blank line, a fence, or a non-bullet line. It does not cap the
  lookahead by line count (a real markdown header or blank line reliably
  ends the block in every corpus instance seen); a pathological doc with no
  such boundary for many lines would over-propagate. Not observed in the
  corpus.
- No macro/alias/slice resolution of any kind — this check does not read
  GAMS code at all, so it cannot know whether an "unbindable" claim is even
  TRUE. It only reports "no identifier here to check against code".
- A modest false-positive rate (transitional sentences, section-title
  echoes) is expected and NOT tuned away — see DESIGN above. This trades
  some noise for a denominator that is never silently gamed to look clean.

Ground truth for the DOC side is this repo's `modules/` + `cross_module/`.
This check never reads `<MAGPIE_DIR>/modules` (GAMS code) — there is no code
truth to diff against here, only a coverage question ("was a var named at
all?").

Usage:
  python3 check_bindability.py [--summary-only] [--verbose]
  python3 check_bindability.py --self-test    # hermetic positive/negative fixtures

Exit: 0 always in scan mode (advisory). --self-test returns 0/1.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_gams_variables import MAGPIE_DIR  # noqa: E402
from check_attribution_prose import (  # noqa: E402
    HEADER_RE,
    SECTION_KW_RE,
    TRIGGER_RE,
)
from check_attribution_omissions import (  # noqa: E402
    _cross_vars,
    _cross_vars_backticked,
    _debacktick,
    _mod_nums,
    _FIELD_POP_RE,
    _FIELD_READ_RE,
    _MD_HEAD_RE,
    _VARBLOCK_HEAD_RE,
    FENCE_RE,
    HEDGE_RE,
    HISTORICAL_RE,
    LIST_CONT_RE,
    NEGATION_RE,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
CROSS_DIR = AGENT_DIR / "cross_module"
ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"
CHECK_NAME = "check_bindability"

_BOLD_SPAN_RE = re.compile(r"\*\*([^*]+)\*\*")


def load_allowlist() -> set[tuple[str, str]]:
    """{(file, "L<lineno>")} suppressed known noise (see audit/advisory_allowlist.json).

    Mirrors the load_allowlist() PATTERN used by the sibling advisory checkers
    (check_attribution_omissions.py / check_attribution_prose.py) — same file,
    same schema, filtered by THIS check's own CHECK_NAME (the sibling
    functions are hardcoded to their own module's CHECK_NAME, so they cannot
    be imported and reused directly here). A bindability finding has no
    var/module pair to key on (that IS the finding — no var was named), so
    entries are keyed by line number instead: {"key": "L712"}.
    """
    if not ALLOWLIST_PATH.exists():
        return set()
    try:
        data = json.loads(ALLOWLIST_PATH.read_text())
    except (ValueError, OSError):
        return set()
    rows = data if isinstance(data, list) else (data.get("allowlist") or data.get("entries") or [])
    return {(e.get("file", ""), e.get("key", "")) for e in rows if e.get("check") == CHECK_NAME}


def _iter_docs():
    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        if not doc.name.endswith("_notes.md"):
            yield doc
    if CROSS_DIR.is_dir():
        yield from sorted(CROSS_DIR.glob("*.md"))


def scan_doc(text: str, rel_path: str, allow: set | None = None) -> tuple[list[dict], int, int, int]:
    """Return (findings, bindable_count, unbindable_count, suppressed_count).

    findings: unbindable, non-allowlisted attribution-context lines — the
    to-do list. Each: {file, line, modules, hedged, row}.
    bindable_count: attribution-context lines that named >=1 module AND had
    >=1 cross-module interface var in scope — already covered by Checks
    34/36, not this check's business.
    unbindable_count == len(findings) (kept separate from suppressed so the
    denominator stays honest — see load_allowlist docstring).
    """
    allow = allow or set()
    lines = text.splitlines()
    in_fence = False
    in_section = False
    list_armed = False
    scope_var: str | None = None
    findings: list[dict] = []
    bindable = 0
    unbindable = 0
    suppressed = 0

    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            list_armed = False
            continue
        if in_fence:
            continue

        # --- var-BLOCK scope tracking — UNCHANGED logic from parse_doc_varblock_
        # triples (check_attribution_omissions.py): a bolded var heading OPENS a
        # scope; a markdown header or any other bolded (non-field) heading CLOSES
        # it. Reused so the two checks can never disagree about which var a
        # "Consumers:"/"Populated by:" bullet inherits. ---
        if _MD_HEAD_RE.match(line):
            scope_var = None
        elif _VARBLOCK_HEAD_RE.match(line) and not (_FIELD_READ_RE.match(line) or _FIELD_POP_RE.match(line)):
            found: set[str] = set()
            for bold in _BOLD_SPAN_RE.findall(line):
                found |= _cross_vars(bold)
            scope_var = next(iter(found)) if len(found) == 1 else None

        # --- hard SECTION arm/disarm — mirrors check_attribution_prose.scan_doc
        # exactly: a HEADER_RE line (re)sets in_section from SECTION_KW_RE and is
        # never itself an attribution row. ---
        if HEADER_RE.match(line):
            in_section = bool(SECTION_KW_RE.search(line))
            list_armed = False
            continue

        stripped = line.strip()
        if not stripped:
            list_armed = False
            continue

        if HISTORICAL_RE.search(line):
            list_armed = False
            continue

        deb = _debacktick(line)

        # Trigger = an inline verb (TRIGGER_RE) OR a var-BLOCK field label
        # ("**Consumers**:" / "**Populated by**:") — the latter names no var of
        # its own by construction but is unambiguously an attribution row (it IS
        # the field parse_doc_varblock_triples binds to scope_var).
        has_trigger = bool(TRIGGER_RE.search(line) or _FIELD_READ_RE.match(line) or _FIELD_POP_RE.match(line))
        # "Soft anchor" continuation: a bullet under a PRIOR line that ended in
        # ':' and already qualified as attribution context, even though that
        # prior line was not a HEADER_RE section (the real module_52.md shape —
        # a bolded pseudo-heading, not a markdown/bold-only header line).
        in_list_cont = list_armed and bool(LIST_CONT_RE.match(line))
        candidate_ctx = in_section or has_trigger or in_list_cont
        ends_colon = line.rstrip().endswith(":")

        if candidate_ctx and not NEGATION_RE.search(deb):
            mods = _mod_nums(deb)
            if mods:
                scoped = set(_cross_vars_backticked(line))
                # A markdown TABLE ROW is bound by Check 34 through its bare-text
                # fallback (`_cross_vars_backticked(col2) or _cross_vars(col2)`), so an
                # UNBACKTICKED var in a table cell IS mechanically visible. Requiring
                # backticks here would report as "blind" exactly what Check 34 already
                # sees -- e.g. module_10.md:300-302, the PROVIDES-TO rows
                # (`| **59_som** | pcm_land, pm_land_start, vm_land ... |`). "Bindable"
                # must mean what the mechanical layer ACTUALLY binds, not a stricter
                # proxy, or the blind-spot ratio is systematically over-reported.
                if stripped.startswith("|"):
                    scoped |= _cross_vars(line)
                if scope_var:
                    scoped.add(scope_var)
                if scoped:
                    bindable += 1
                else:
                    key = f"L{i + 1}"
                    if (rel_path, key) in allow:
                        suppressed += 1
                    else:
                        unbindable += 1
                        findings.append({
                            "file": rel_path, "line": i + 1,
                            "modules": sorted(mods),
                            "hedged": bool(HEDGE_RE.search(deb)),
                            "row": stripped[:160],
                        })

        list_armed = (candidate_ctx and ends_colon) or in_list_cont

    return findings, bindable, unbindable, suppressed


# ---------------------------------------------------------------------------
# Output / CLI
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    summary_only = "--summary-only" in args
    verbose = "--verbose" in args

    allow = load_allowlist()
    all_findings: list[dict] = []
    total_bindable = 0
    total_unbindable = 0
    total_suppressed = 0
    n_docs = 0
    docs_examined = 0

    for doc in _iter_docs():
        n_docs += 1
        rel = str(doc.relative_to(AGENT_DIR))
        text = doc.read_text(encoding="utf-8", errors="ignore")
        findings, bindable, unbindable, suppressed = scan_doc(text, rel, allow)
        if bindable or unbindable or suppressed:
            docs_examined += 1
        total_bindable += bindable
        total_unbindable += unbindable
        total_suppressed += suppressed
        all_findings.extend(findings)

    examined = total_bindable + total_unbindable  # suppressed excluded — see load_allowlist
    ratio_str = f"{(total_unbindable / examined):.1%}" if examined else "N/A (0 examined — BLIND, not clean)"

    print(f"{CHECK_NAME}: ADVISORY coverage/to-do checker (Check 37). A finding here means "
          f"'this attribution claim cannot be MECHANICALLY bound to code' — NEVER 'this claim "
          f"is wrong'. It is a to-do list for Checks 34/36, not a defect list.")
    print(f"{CHECK_NAME}: doc ground truth = {AGENT_DIR} (this check parses DOC PROSE only; "
          f"it never reads GAMS code — MAGPIE_DIR={MAGPIE_DIR} is printed for consistency with "
          f"the other checks, but nothing here is gated on it).")
    print(f"{CHECK_NAME}: coverage = {examined} attribution-context lines examined across "
          f"{docs_examined}/{n_docs} docs -> {total_bindable} BINDABLE (named a var; already "
          f"covered by Checks 34/36) / {total_unbindable} UNBINDABLE "
          f"(blind-spot ratio (UPPER BOUND, see limits) = {ratio_str} of examined lines).")
    if total_suppressed:
        print(f"{CHECK_NAME}: {total_suppressed} finding(s) allowlist-suppressed "
              f"(audit/advisory_allowlist.json, check={CHECK_NAME}).")

    if all_findings:
        by_doc: dict[str, list[dict]] = defaultdict(list)
        for f in all_findings:
            by_doc[f["file"]].append(f)
        print(f"\n{CHECK_NAME}: {len(all_findings)} unbindable attribution claim(s) across "
              f"{len(by_doc)} doc(s) — to-do list, grouped by doc:")
        for doc_name in sorted(by_doc, key=lambda d: (-len(by_doc[d]), d)):
            rows = by_doc[doc_name]
            print(f"  {doc_name}: {len(rows)} unbindable")
            if not summary_only:
                for f in rows:
                    tag = " [hedged]" if f["hedged"] else ""
                    mods = ",".join(f"M{m}" for m in f["modules"])
                    print(f"    {doc_name}:{f['line']}{tag} names {mods} but no backticked "
                          f"cross-module interface var is in scope. Line: {f['row']}")
    else:
        print(f"\n{CHECK_NAME}: 0 unbindable claims within {examined} examined lines "
              f"(NOT a corpus-clean claim if examined==0 — see coverage above).")

    if verbose:
        print(f"\n({CHECK_NAME}: trigger vocabulary = check_attribution_prose.TRIGGER_RE + "
              f"var-block field labels (**Consumers**:/**Populated by**:); does not include "
              f"check_attribution_omissions' own READ_TRIGGER_RE/POP_TRIGGER_RE prose forms "
              f"— see module docstring HONEST LIMITS.)")

    print(f"\n{CHECK_NAME}: NOTE this is a coverage-gap report, not a bug report. Every "
          f"UNBINDABLE line is a candidate for a future doc edit that NAMES the interface var "
          f"so Checks 34/36 can verify it mechanically — never treat a finding here as 'this is "
          f"wrong'. Precision-first on claim detection; a modest false-positive rate on "
          f"borderline/transitional lines is expected and NOT tuned away (see module docstring).")
    print(f"{CHECK_NAME}: SUMMARY examined={examined} bindable={total_bindable} "
          f"unbindable={total_unbindable} suppressed={total_suppressed} docs={n_docs}")
    return 0


# ---------------------------------------------------------------------------
# Hermetic self-test (fixture-first positive control)
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Fixture-first, hermetic positive + negative controls (no repo/code needed).

    The headline positive control (`pos-real-r55-shape`) reproduces the EXACT
    shape of the real R55 `attribution_populate` Major that motivated this
    check: modules/module_52.md:711-718, a bolded pseudo-heading ("**6. Land
    Modules** (provide carbon stocks to Module 56):") that is NOT a markdown/
    HEADER_RE section, followed by a bullet list naming modules with no
    backticked identifier anywhere in the claim.
    """
    ok = True

    def run(text: str, fname: str = "modules/module_TEST.md"):
        return scan_doc(text, fname, set())

    cases = []

    # POSITIVE — the real R55 shape. Must flag the bullet (no var anywhere).
    cases.append((
        "pos-real-r55-shape",
        "**6. Land Modules** (provide carbon stocks to Module 56):\n"
        "- Module 30 (Cropland): Cropland carbon stocks\n",
        {"must_flag_lines": {2}},
    ))

    # NEGATIVE — var-BLOCK heading supplies the var; the field bullet under it
    # carries no var of its own but is BINDABLE via the heading (parse_doc_
    # varblock_triples scoping, reused unchanged).
    cases.append((
        "neg-varblock-bindable",
        "**1b. pm_carbon_density_secdforest_ac_uncalib** (declarations.gms:10)\n"
        "- **Consumers**: Module 32, Module 29\n",
        {"must_not_flag_lines": {2}},
    ))

    # NEGATIVE — inline backticked var on the SAME line as the module list.
    cases.append((
        "neg-inline-backtick-bindable",
        "**Direct consumers of `vm_land`**: Module 29\n",
        {"must_not_flag_lines": {1}},
    ))

    # NEGATIVE — negation: a correct statement of absence, not an unbound claim.
    cases.append((
        "neg-negation",
        "- Module 40 (Transport) does NOT provide carbon stocks to Module 56.\n",
        {"must_not_flag_lines": {1}},
    ))

    # NEGATIVE — historical/changelog wording.
    cases.append((
        "neg-historical",
        "Previously, Module 40 provided carbon stocks to Module 56 (corrected R54).\n",
        {"must_not_flag_lines": {1}},
    ))

    # NEGATIVE — fenced code must be skipped entirely.
    cases.append((
        "neg-fenced-code",
        "```\n- Module 40 provides carbon stocks to Module 56\n```\n",
        {"must_not_flag_lines": {2}},
    ))

    # NEGATIVE — prose names a module but carries no attribution trigger and
    # sits in no attribution section -> not a claim at all -> not examined.
    cases.append((
        "neg-no-trigger-no-section",
        "Module 40 is discussed in the introduction; nothing about attribution here.\n",
        {"must_not_flag_lines": {1}},
    ))

    # BONUS — HEDGE_RE is METADATA here, never a suppressor (unlike in check_
    # attribution_omissions, where a hedge disproves the completeness an
    # OMISSION needs). A hedged claim still names no var, so it still belongs
    # on the to-do list, just tagged lower-priority.
    cases.append((
        "pos-hedge-is-metadata-not-suppression",
        "Module 31 (e.g.) reads carbon stock summaries destined for Module 56, among others.\n",
        {"must_flag_lines": {1}, "must_be_hedged_lines": {1}},
    ))

    for label, text, expect in cases:
        findings, _bindable, _unbindable, _suppressed = run(text)
        flagged_lines = {f["line"] for f in findings}
        must_flag = expect.get("must_flag_lines", set())
        must_not = expect.get("must_not_flag_lines", set())
        must_hedge = expect.get("must_be_hedged_lines", set())
        missing = must_flag - flagged_lines
        wrong = must_not & flagged_lines
        hedge_ok = all(any(f["line"] == ln and f["hedged"] for f in findings) for ln in must_hedge)
        if not missing and not wrong and hedge_ok:
            print(f"  SELF-TEST PASS [{label}]")
        else:
            ok = False
            print(f"  SELF-TEST FAIL [{label}]: missing={sorted(missing)} wrong={sorted(wrong)} "
                  f"hedge_ok={hedge_ok} (flagged={sorted(flagged_lines)})")

    # Coverage-counter sanity: the headline positive fixture must examine >=1 line
    # (guards against a vacuously-green run where a regex regression silently
    # examines nothing — see memory feedback_validator_coverage_denominator).
    _findings, bindable, unbindable, _supp = run(
        "**6. Land Modules** (provide carbon stocks to Module 56):\n"
        "- Module 30 (Cropland): Cropland carbon stocks\n")
    if (bindable + unbindable) < 1:
        ok = False
        print("  SELF-TEST FAIL [coverage-counter]: headline fixture examined 0 lines")
    else:
        print("  SELF-TEST PASS [coverage-counter]")

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
