#!/usr/bin/env python3
"""check_attribution_prose.py — advisory Check: interface-attribution PROSE vs code.

The PROSE complement to check_attribution_tables.py (which handles the markdown
"Provides To"/"Receives From" TABLES) and to check_role_attribution.py / Check 31
(which mechanizes ONLY the ADJACENT "Module NN provides `var`" / "declared in NN"
prose forms via strict regexes).

THE GAP THIS CLOSES
  Check 31's PROVIDES_RE requires the module number ADJACENT to the verb:
  `(\\d{1,2})\\s+provides`. The corpus's dominant attribution form puts a
  parenthetical LABEL between the number and the verb, e.g. (module_14.md:1240):
      - **Module 10 (Land):** Provides `fm_croparea` (historical cropland ...)
  so Check 31 never sees it. That exact line was a real R54 Critical:
  `fm_croparea` is referenced by Modules 14/17/30/59 (declared as a `table` in
  30_croparea/*/input.gms), NOT Module 10. This check catches the labeled-bullet,
  numbered-list, and "Provides `var` to Module NN" prose forms that Check 31
  deliberately scoped out as FP-prone.

WHAT IT DOES (direction-agnostic PHANTOM test)
  In every modules/module_XX.md, on each line that
    (a) sits inside an attribution SECTION (Provides To / Receives From /
        Dependencies / Interfaces / Inputs / Outputs / Up-&Downstream / ...),
        OR carries an attribution TRIGGER verb (provides / consumed by / reads /
        to Module / from Module / ...), AND
    (b) names EXACTLY ONE module (via "Module NN" or a standalone "NN_name",
        deduped by number; file-path "modules/NN_name/..." forms excluded), AND
    (c) contains >=1 backticked CROSS-MODULE interface var (vm_/pm_/im_/pcm_/fm_):
  for each (module M, var V) pair, if M references V NOWHERE in its GAMS code
  (build_consumer_map is a \\b-anchored "referenced anywhere" set, so `.l`/`.lo`
  attribute reads are included), the M<->V attribution is a PHANTOM -> flag.

  Direction-agnostic: whether the line claims "M provides V", "V provided to M",
  or "V read by M", a module that never references V in ANY *.gms cannot stand in
  ANY of those relations -> the claim is wrong regardless of direction. (Same
  reduction check_attribution_tables.py uses for Provides-To vs Receives-From.)

DESIGN (precision over recall, like Check 29/31 and the table check)
  - EXACTLY ONE module per line. Multi-module lines (dense cross-ref prose, or a
    consumer line that also cites the producer's file path) are AMBIGUOUS in their
    M<->V binding -> skipped. Lowers recall, protects precision. Deduped by number,
    so "Module 58 ... (`modules/58_peatland/...`)" counts as one module (58).
  - PHANTOM only. An OMITTED real consumer is NOT flagged (build_consumer_map
    over-lists — includes the declarer + comment mentions — so omission-flagging is
    noisy; phantom is the high-signal R54 class).
  - Backticked CROSS-module interface vars only (vm_/pm_/im_/pcm_/fm_). Numbered
    module-internal vars (v32_/p56_/…) are module-owned and off-topic for
    cross-module attribution; excluding them keeps the metric on-class.
  - Historical/changelog lines skipped (HISTORICAL_RE). Fenced ``` code skipped.
  - Advisory only: main() always returns 0. --self-test returns 0/1 (hermetic).

COVERAGE (honest-by-construction): main() ALWAYS prints how many (module,var) pairs
  were evaluated across how many docs. A "0 findings" over few pairs is BLIND, not
  clean — see memory feedback_validator_coverage_denominator.

Ground truth: the LOCAL parent checkout scanned by build_consumer_map
(<MAGPIE_DIR>/modules). For an authoritative run point MAGPIE_DIR at a develop
worktree; the working tree can lag (see memory magpie_agent_sync_against_develop).

Usage: python3 check_attribution_prose.py [--self-test] [--summary-only] [--verbose]
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_consumer_attribution import (  # noqa: E402
    build_consumer_map,
    is_interface_var,
    strip_dims,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"
CHECK_NAME = "check_attribution_prose"

# Cross-module interface var prefixes (MANDATE-18 core set + fm_ input params).
# Numbered module-internal vars (v32_/p56_/…) are deliberately excluded.
# Case-INSENSITIVE after the prefix (R57) -- see the twin definition in
# check_attribution_omissions.py. A `[a-z]` gate silently dropped vm_AEI (M41->M30).
# NOTE: this constant is DUPLICATED across the two modules; keep them in sync (the
# duplication itself is an R57 finding -- a single definition would have made this a
# one-site fix).
CROSS_IFACE_RE = re.compile(r"^(?:vm|pm|im|pcm|fm)_[a-zA-Z]")

BACKTICK_TOKEN_RE = re.compile(r"`([^`]+)`")
ID_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")

# Module reference forms.
#   "Module 10", "Module 58 (Peatland)"  -> word form
#   "10_land", "39_landconversion"       -> NN_name form, but NOT when part of a
#                                            path ("modules/58_peatland/...") — the
#                                            negative lookbehind rejects a preceding
#                                            word char or '/'.
MODULE_WORD_RE = re.compile(r"\bModule\s+(\d{1,2})\b")
MODNAME_RE = re.compile(r"(?<![\w/])(\d{1,2})_[a-z]")

# A header line (markdown heading, bold-only line, or numbered bold) — used to
# (re)evaluate section membership.
HEADER_RE = re.compile(r"^\s{0,3}(?:#{1,6}\s|\*\*[^*].*\*\*\s*:?\s*$|\d+\.\s+\*\*)")
# Attribution-section keywords. If a header matches one of these, lines under it
# are in "attribution mode" (evaluated even without an inline trigger verb).
SECTION_KW_RE = re.compile(
    r"provides?\s+to|provides?\s+yields?\s+to|receives?\s+from|dependenc|"
    r"\binterfaces?\b|\binputs?\b|\boutputs?\b|consumers?|producers?|"
    r"upstream|downstream|data\s+flow|connections?|provides?\s+.*\bto\b",
    re.IGNORECASE)

# Inline attribution trigger verbs (direction-agnostic — the phantom test does not
# care which way the relation points).
TRIGGER_RE = re.compile(
    r"\b(provides?|provided\s+by|providing|produces?|produced\s+by|populates?|"
    r"populated\s+by|declared\s+in|declares?|supplies|supplied|passes|passed|"
    r"feeds?|fed\s+(?:by|into)|sends?|sent|consumed\s+by|consumes?|reads?|"
    r"used\s+by|uses?|receives?|received\s+from|aggregat\w*|sourced\s+from|"
    r"drawn\s+from|to\s+Module|from\s+Module)\b",
    re.IGNORECASE)

# Genuine historical / changelog wording -> skip the line (the bug is being
# described, not committed). Mirrors check_role_attribution.HISTORICAL_RE + a few.
HISTORICAL_RE = re.compile(
    r"\b(corrected|previously|used to be|was declared|changelog|deprecat|"
    r"R\d+\s+audit|R\d+\s+correction|earlier (?:draft|rubric|wording|attempt)|"
    r"formerly|superseded|removed in R\d+|no longer|renamed|stale wording|"
    r"misattributed|prior wording)\b",
    re.IGNORECASE)

# Negation within a clause flips a "phantom" into a CORRECT statement of absence
# ("Module 38 is NOT a consumer of `vm_tau`", "Module 14 reads NO `vm_prod`").
# A clause carrying any of these is a statement the module does NOT relate to the
# var -> never a phantom attribution -> skip the whole clause (precision-first;
# costs recall only on the rare clause that uses a negation word incidentally).
NEGATION_RE = re.compile(r"\b(?:not|no|none|never|cannot|nor|neither)\b|n't\b",
                         re.IGNORECASE)


def load_allowlist() -> set[tuple[str, str]]:
    if not ALLOWLIST_PATH.exists():
        return set()
    try:
        data = json.loads(ALLOWLIST_PATH.read_text())
    except (ValueError, OSError):
        return set()
    out: set[tuple[str, str]] = set()
    rows = data if isinstance(data, list) else (data.get("allowlist") or data.get("entries") or [])
    for entry in rows:
        if entry.get("check") == CHECK_NAME:
            out.add((entry.get("file", ""), entry.get("key", "")))
    return out


def _mods_on_line(line: str) -> set[int]:
    """Distinct module NUMBERS referenced on the line (word form + NN_name form)."""
    nums = {int(m.group(1)) for m in MODULE_WORD_RE.finditer(line)}
    nums |= {int(m.group(1)) for m in MODNAME_RE.finditer(line)}
    return nums


def _cross_iface_vars_on_line(line: str) -> list[str]:
    """Distinct backticked cross-module interface var bases on the line."""
    out: list[str] = []
    for span in BACKTICK_TOKEN_RE.findall(line):
        for tok in ID_TOKEN_RE.findall(span):
            base = strip_dims(tok)
            if CROSS_IFACE_RE.match(base) and is_interface_var(base) and base not in out:
                out.append(base)
    return out


def scan_doc(text: str, rel_path: str, ref_map: dict[str, set[int]],
             allow: set | None = None) -> list[dict]:
    """Return phantom-attribution findings for one doc.

    ref_map: base_var -> set of module NUMBERS that reference it anywhere in code.

    A finding = a CLAUSE (line split on ';') that, in an attribution context
    (inside an attribution section OR carrying a trigger verb), names EXACTLY ONE
    module in its prose and EXACTLY ONE backticked cross-module interface var, where
    that module references that var NOWHERE in code.

    Precision guards (each removes a real FP class found on the corpus):
      - NEGATION_RE: "Module 38 is NOT a consumer of `vm_tau`" is a correct
        statement of absence, not a phantom -> skip the clause.
      - De-backticked prose for module extraction: a backticked realization/path
        name (`73_timber/default`) is NOT a "Module 73" attribution -> strip
        backtick spans before matching module numbers (vars still come FROM the
        backtick spans).
      - Clause split on ';' + EXACTLY ONE module + EXACTLY ONE var: multi-var and
        multi-clause prose (where the lone "Module NN" belongs to a different var
        or a non-var clause) is ambiguous in its binding -> skip.
    """
    allow = allow or set()
    fname = os.path.basename(rel_path)
    findings: list[dict] = []
    in_section = False
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # Track fenced code blocks (``` or ~~~). Skip their content.
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # A header line re-evaluates attribution-section membership.
        if HEADER_RE.match(line):
            in_section = bool(SECTION_KW_RE.search(line))
            # A header itself is not an attribution row.
            continue
        if HISTORICAL_RE.search(line):
            continue
        # Cheap line-level gate: an attribution line is either section-armed or
        # carries a trigger verb somewhere. (Per-clause trigger re-checked below.)
        if not (in_section or TRIGGER_RE.search(line)):
            continue
        for clause in line.split(";"):
            if NEGATION_RE.search(clause):
                continue
            vars_here = [v for v in _cross_iface_vars_on_line(clause) if v in ref_map]
            if len(vars_here) != 1:
                continue  # 0 or >1 vars -> ambiguous binding -> skip
            # Module numbers from the DE-BACKTICKED prose only (backticked spans
            # are code: file paths, realization names, var tokens — not attribution).
            prose = BACKTICK_TOKEN_RE.sub(" ", clause)
            mods = _mods_on_line(prose)
            if len(mods) != 1:
                continue  # 0 modules -> nothing to attribute; >1 -> ambiguous
            # The trigger must apply to THIS clause (a section-armed line needs none).
            if not (in_section or TRIGGER_RE.search(clause)):
                continue
            var = vars_here[0]
            mod = next(iter(mods))
            scan_doc.pairs_evaluated += 1
            if mod in ref_map[var]:
                continue  # module references the var -> attribution stands
            key = f"{mod:02d}:{var}"
            if (fname, key) in allow:
                continue
            findings.append({
                "file": rel_path, "line": lineno, "claimed_module": mod,
                "var": var, "true_refs": sorted(ref_map[var]),
                "row": stripped[:160],
            })
    return findings


scan_doc.pairs_evaluated = 0  # coverage counter; reset by callers (see main / self_test)


def _ref_map_from_consumers() -> dict[str, set[int]]:
    """build_consumer_map (var -> {"NN_name"}) normalized to var -> {NN:int}."""
    out: dict[str, set[int]] = {}
    for var, mods in build_consumer_map().items():
        nums = set()
        for m in mods:
            head = m.split("_", 1)[0]
            if head.isdigit():
                nums.add(int(head))
        out[strip_dims(var)] = nums
    return out


def _fmt(f: dict) -> str:
    return (f"{f['file']}:{f['line']}: [attribution-prose] Module {f['claimed_module']:02d} "
            f"is attributed `{f['var']}`, but code shows that var referenced only by "
            f"modules {f['true_refs']} (Module {f['claimed_module']:02d} references it "
            f"nowhere) -> likely phantom attribution. Line: {f['row']}")


def main() -> int:
    args = sys.argv[1:]
    summary_only = "--summary-only" in args
    verbose = "--verbose" in args

    allow = load_allowlist()
    ref_map = _ref_map_from_consumers()
    if not ref_map:
        print(f"{CHECK_NAME}: WARNING could not build consumer map "
              f"(parent modules/ not found) - skipping.")
        return 0

    all_findings: list[dict] = []
    scan_doc.pairs_evaluated = 0
    docs_with_pairs = 0
    n_docs = 0
    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        if doc.name.endswith("_notes.md"):
            continue
        n_docs += 1
        rel = f"modules/{doc.name}"
        before = scan_doc.pairs_evaluated
        all_findings.extend(scan_doc(doc.read_text(), rel, ref_map, allow))
        if scan_doc.pairs_evaluated > before:
            docs_with_pairs += 1

    # Coverage line ALWAYS printed: "0 findings" is meaningless without the
    # denominator. This check parses PROSE attribution lines naming exactly one
    # module; multi-module prose + table-only docs contribute 0 pairs here.
    print(f"{CHECK_NAME}: coverage = {scan_doc.pairs_evaluated} (module,var) pairs evaluated "
          f"across {docs_with_pairs}/{n_docs} module docs (single-module prose lines only).")

    if all_findings:
        print(f"{CHECK_NAME}: {len(all_findings)} advisory phantom-attribution finding(s):")
        if summary_only:
            from collections import Counter
            counts = Counter(f["file"] for f in all_findings)
            for doc, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                print(f"  {doc}: {n}")
        else:
            for f in all_findings:
                print("  " + _fmt(f))
    else:
        print(f"{CHECK_NAME}: 0 findings within covered pairs "
              f"(NOT a corpus-clean claim — see coverage above).")

    if verbose:
        print(f"\n(ref_map has {len(ref_map)} interface vars; "
              f"cross-module prefixes vm_/pm_/im_/pcm_/fm_ only.)")
    return 0


def self_test() -> int:
    """Hermetic positive + negative controls with an injected ref-map (no parent repo).

    Ground truth mirrors the real fixture: fm_croparea referenced by 14/17/30/59
    (NOT 10); vm_land_forestry only by 58; vm_yld by 14/30/31.
    """
    ref = {
        "fm_croparea": {14, 17, 30, 59},
        "vm_land_forestry": {58},
        "vm_yld": {14, 30, 31},
        "vm_cost_fore": {11, 32},
        "vm_tau": {13, 14},
        "vm_prod": {17, 18, 30, 31, 38, 40, 42, 71, 73},
        "vm_prod_reg": {16, 17, 18, 20, 21, 38, 50, 70, 71},
        "fm_aboveground_fraction": {14, 52},
        "vm_nr_som_fertilizer": {50, 59},  # the real R54-class corpus bug (M50, not M51)
    }
    ok = True

    # Each case: (label, doc_text, expected {(module, var)} that MUST be flagged,
    #             forbidden {(module, var)} that must NOT be flagged).
    # The neg-* cases below are the exact FALSE-POSITIVE classes found on the corpus
    # 2026-07-15 (negation, backticked-realization, multi-var, multi-clause) — locked
    # in as regression controls so a future edit can't reintroduce them.
    cases = [
        # POSITIVE 1 — the real R54 fixture shape (subject-first, labeled bullet).
        ("pos-fixture-subject-first",
         "- **Module 10 (Land):** Provides `fm_croparea` (historical cropland patterns)\n",
         {(10, "fm_croparea")}, set()),
        # POSITIVE 2 — object-last "Provides `var` to Module NN".
        ("pos-object-last",
         "Provides `vm_land_forestry` to Module 10 (Land) for something wrong.\n",
         {(10, "vm_land_forestry")}, set()),
        # POSITIVE 3 — the real corpus finding this run confirmed (module_59.md:221):
        # vm_nr_som_fertilizer is consumed by M50, NOT M51.
        ("pos-real-m59-nr-som",
         "- `vm_nr_som_fertilizer(j)`: Plant-available nitrogen from SOM loss "
         "(Mt N per yr) — provided to Module 51\n",
         {(51, "vm_nr_som_fertilizer")}, set()),
        # NEGATIVE 1 — correct consumer under an armed section (no inline verb).
        ("neg-correct-section-bullet",
         "#### Provides Yields To\n"
         "- **Module 30 (Croparea):** `vm_yld(j,kcr,w)` -> crop production\n",
         set(), {(30, "vm_yld")}),
        # NEGATIVE 2 — correct provider claim.
        ("neg-correct-provider",
         "- **Module 58 (Peatland):** reads `vm_land_forestry` (sole consumer)\n",
         set(), {(58, "vm_land_forestry")}),
        # NEGATIVE 3 — multi-module line -> ambiguous -> skip.
        ("neg-multi-module",
         "`fm_croparea` is consumed by Module 10 and Module 35 per the docs.\n",
         set(), {(10, "fm_croparea"), (35, "fm_croparea")}),
        # NEGATIVE 4 — historical/changelog wording -> skip.
        ("neg-historical",
         "Previously Module 10 provided `fm_croparea` (corrected R54).\n",
         set(), {(10, "fm_croparea")}),
        # NEGATIVE 5 — no trigger, no section -> incidental co-mention -> skip.
        ("neg-incidental",
         "Contrast with Module 10, where `fm_croparea` behaves differently.\n",
         set(), {(10, "fm_croparea")}),
        # NEGATIVE 6 — file-path NN_name must NOT count as a second module.
        ("neg-filepath-single-module",
         "Provides `vm_land_forestry` to Module 58 (`modules/58_peatland/v2/equations.gms:23`).\n",
         set(), {(58, "vm_land_forestry")}),
        # NEGATIVE 7 — fenced code must be skipped.
        ("neg-code-fence",
         "```\n- Module 10 provides `fm_croparea` inside a code block\n```\n",
         set(), {(10, "fm_croparea")}),
        # NEGATIVE 8 — unknown var (not in ref_map) -> skip (avoid FP).
        ("neg-unknown-var",
         "- **Module 10 (Land):** Provides `vm_totally_unknown_iface`\n",
         set(), set()),
        # NEGATIVE 9 — NEGATION: "Module 38 is NOT a consumer of `vm_tau`" is a
        # correct statement of absence, not a phantom (real corpus FP module_13:372).
        ("neg-negation-not-consumer",
         "- Module 38 (Factor Costs): NOT a direct consumer of `vm_tau`; respond transitively\n",
         set(), {(38, "vm_tau")}),
        # NEGATIVE 10 — NEGATION "reads no" (real corpus FP module_14:852).
        ("neg-negation-reads-no",
         "See §21.3 (Module 14 reads no `vm_prod`, and no path reaches Module 14).\n",
         set(), {(14, "vm_prod")}),
        # NEGATIVE 11 — MULTI-VAR clause: one module, two vars -> ambiguous binding
        # (real corpus FP module_14:1450 — vm_yld actually belongs to q14_yield_crop).
        ("neg-multivar-clause",
         "The co-solve of `vm_tau` (Module 13, endogenous) and `vm_yld` (`q14_yield_crop`)\n",
         set(), {(13, "vm_yld")}),
        # NEGATIVE 12 — BACKTICKED REALIZATION: `73_timber/default` is a realization
        # path, not a "Module 73" attribution (real corpus FP module_17:31).
        ("neg-backticked-realization",
         "Populated under the default timber realization `73_timber/default` and "
         "aggregated to `vm_prod_reg(i,\"wood\")` by q17\n",
         set(), {(73, "vm_prod_reg")}),
        # NEGATIVE 13 — MULTI-CLAUSE (';'): the lone "Module 32" is in the age-
        # distribution clause; the var is in a different clause (real corpus FP
        # module_52:263).
        ("neg-multiclause-semicolon",
         "The age distribution comes from Module 32 (forestry) plantation pools; "
         "plantation uses `fm_aboveground_fraction(\"forestry\")` at preloop.gms:96\n",
         set(), {(32, "fm_aboveground_fraction")}),
    ]

    for label, text, must_flag, must_not_flag in cases:
        scan_doc.pairs_evaluated = 0
        fnd = scan_doc(text, "module_TEST.md", ref)
        got = {(f["claimed_module"], f["var"]) for f in fnd}
        missing = must_flag - got
        wrong = must_not_flag & got
        if not missing and not wrong:
            print(f"  SELF-TEST PASS [{label}]")
        else:
            ok = False
            if missing:
                print(f"  SELF-TEST FAIL [{label}]: did not flag {sorted(missing)} (got {sorted(got)})")
            if wrong:
                print(f"  SELF-TEST FAIL [{label}]: false-positive on {sorted(wrong)}")

    # Coverage instrumentation sanity: the fixture case must evaluate >=1 pair.
    scan_doc.pairs_evaluated = 0
    scan_doc("- **Module 10 (Land):** Provides `fm_croparea`\n", "m.md", ref)
    if scan_doc.pairs_evaluated < 1:
        ok = False
        print("  SELF-TEST FAIL [coverage-counter]: fixture evaluated 0 pairs")
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
