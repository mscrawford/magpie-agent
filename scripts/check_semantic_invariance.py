#!/usr/bin/env python3
"""P0 regularization gate — semantic invariance of a doc rewrite (BEFORE vs AFTER).

The P0 pilot (audit/regularization_p0_plan.md) lets Sonnet agents regularize doc
FORM: reflow, headings, badges, citation format, and migrating existing prose
attribution into "Provides To" / "Receives From" table rows so that
check_attribution_tables can read it.

The safety mechanism is NOT a second LLM (shared priors, correlated failure
modes). It is this deterministic gate:

    Form may move. Meaning may not.

Four invariants, compared as MULTISETS between the before-text and after-text:

  (a) GAMS identifiers   -- vm_/pm_/im_/pcm_/fm_/sm_/cm_/v14_/q70_/s32_/... tokens
  (b) numeric literals   -- every number outside a citation
  (c) code-fence bodies  -- verbatim, ordered
  (d) citations          -- FILE.gms:LINE, compared CANONICALLY (see below)

Any difference in (a)-(c) is a REJECT. A regularizer that "helpfully" corrects a
variable name, drops a claim, edits a number, or rewrites a code block trips this
gate. That is precisely the failure mode the pilot exists to detect (H.7).

Citations get the one sanctioned relaxation, matching the rule Check 25 already
encodes: a BARE cite (`declarations.gms:9`) may be upgraded to a FULL path
(`modules/13_tc/exo/declarations.gms:9`) iff the resolved path EXISTS on disk and
the basename and line-spec are unchanged. Upgrading to a non-existent path, or
changing a line number, is a REJECT. Citations are masked before (a)/(b) are
extracted, so a path's own digits ("13_tc") cannot perturb the numeral multiset.

Usage:
  python3 check_semantic_invariance.py --self-test
  python3 check_semantic_invariance.py --before OLD.md --after NEW.md
  python3 check_semantic_invariance.py --git-diff <ref> <path> [<path> ...]

Exit:
  0  invariance holds (diff may be accepted)
  1  violation -> REJECT the diff
  2  usage error
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_ROOT = AGENT_DIR.parent

CHECK_NAME = "check_semantic_invariance"

# (a) Interface / module-scoped GAMS identifiers. Superset of the shapes used by
# check_fenced_identifiers.py, plus equations (q70_) and any other [letter][NN]_
# form MAgPIE uses. Deliberately shape-based, not existence-based: this gate asks
# "did the token set change?", not "is the token real?".
IDENT_RE = re.compile(
    r"\b((?:vm_|pm_|fm_|im_|pcm_|sm_|cm_|ic\d+_|oq\d+_|ov\d+_|pc\d+_"
    r"|[vpfiscqxo]\d+_)[a-zA-Z][a-zA-Z0-9_]*)"
)

# (d) A .gms citation, optionally full-path, with a line or line-range.
CITE_RE = re.compile(
    r"(?P<path>(?:[\w./-]*/)?)(?P<base>\w+\.gms)(?::(?P<lines>\d+(?:-\d+)?))?"
)

# (c) Fenced code blocks. Group 1 = body.
FENCE_RE = re.compile(r"^```[^\n]*\n(.*?)^```", re.M | re.S)

# (b) Numeric literals: integers and decimals, not glued to a word character.
# The trailing guard is (?!\w), NOT (?![\w.]): a number ending a sentence
# ("Module 10.") must still be seen. The lookbehind already prevents starting
# mid-decimal, and \d+(?:\.\d+)? is greedy, so "1.5" is captured whole.
NUM_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?!\w)")

# A per-module doc's OWN module number is structurally implicit: under
# modules/module_13.md, "Module 13 provides `vm_tau` to Module 14" migrates
# faithfully to a "Provides To" row of "| Module 14 | `vm_tau` |". Requiring the
# self-reference count to survive would reject every legitimate migration -- the
# pilot's central operation -- and make criterion 1 uninterpretable (a style miss
# would read as a meaning change). So the OWN number is compared by PRESENCE, and
# a count decrease is reported as INFO. Every OTHER module number stays a hard
# multiset invariant, so "Module 10 -> Module 11" is still a REJECT.
OWN_MODNUM_RE = re.compile(r"module_(\d{2})\.md$")


# A citation path that is a PEDAGOGICAL PLACEHOLDER, not a claim about a real
# file: `modules/NN_xxx/realization/file.gms:123`, `<module>/...`, `modules/*/...`.
# These cannot and should not resolve on disk. Found by the real-world control on
# commit e982a76, where the bare-cite migration rewrote exactly such examples.
PLACEHOLDER_CITE_RE = re.compile(
    r"NN_|_xxx|/xxx|<|>|\*|\?|\bN+_|/realization/|/REAL/|\bfile\.gms", re.I
)

# --------------------------------------------------------------------------- #
# Invariants (e)-(g), added after the P0 pilot (audit/regularization_p0_result.md).
# All four errors that pilot let through shared ONE mechanism: the (a)-(d)
# invariants are token-IDENTITY based, so anything that is not a prefixed
# identifier, a numeral, a fence body, or a citation was invisible. These three
# close the mechanizable part of that gap. Each is validated in the self-test
# against the REAL pilot error it would have caught, not against a fixture.
# --------------------------------------------------------------------------- #

# (e) DOMAIN SIGNATURES. Pilot error 2: `pm_yields_semi_calib(j,kve,w)` became
# `pm_yields_semi_calib`, so the declared dimensionality vanished doc-wide (kve
# includes pasture, so the doc came to imply a crop-only parameter). Set names
# inside the parens are not identifiers, so (a) saw nothing. We compare the
# multiset of (identifier, domain) PAIRS; a bare mention pairs with "".
IDENT_DOMAIN_RE = re.compile(IDENT_RE.pattern + r"(\([^()\n]{0,120}?\))?")

# (f) HEDGES AND QUANTIFIERS. Pilot error 1: "is read by **many modules** (18,
# 20, 53, 55, 50)" lost the hedge when the five examples became table rows, so a
# deliberately non-exhaustive list read as the complete consumer set -- while the
# real reader count is eight. Hedges are ordinary words: no identifier, no
# numeral, so (a)/(b) saw nothing.
HEDGE_RE = re.compile(
    r"\b(many|several|some|various|numerous|multiple|most|often|typically"
    r"|usually|generally|primarily|mainly|mostly|largely|including|includes"
    r"|such as|among others|e\.g\.|etc\.|at least|roughly|approximately"
    r"|about|indirectly|transitive|transitively|partially|effectively)\b",
    re.I,
)

# (g) BARE-PROSE ENTITY TOKENS. Pilot error 3: a net-new realization qualifier
# (`flexreg_apr16`) asserted a scope the original never claimed. Module-directory
# tokens behave the same way: "22_land_conservation" yields zero identifiers and
# zero numerals (NUM_RE's (?!\w) guard rejects "22_"), so an entire migrated
# Module column was unchecked claim surface. Both are matched from GROUND TRUTH
# (the real directory names on disk), never guessed.
MODDIR_RE = re.compile(r"(?<![\w/.])(\d{1,2}_[a-z][a-z0-9_]*)")


def realization_names() -> set[str]:
    """Realization directory names under ../modules/, from disk.

    Only names containing a digit or an underscore are tracked: bare words like
    `static`, `default`, `exo` and `simple` are real realization directories but
    also ordinary English, and matching those in prose would be a false-positive
    factory.
    """
    out: set[str] = set()
    mod_root = MAGPIE_ROOT / "modules"
    if not mod_root.is_dir():
        return out
    for mod in mod_root.iterdir():
        if not mod.is_dir():
            continue
        for real in mod.iterdir():
            n = real.name
            if real.is_dir() and n != "input" and ("_" in n or any(c.isdigit() for c in n)):
                out.add(n)
    return out


_REALIZATIONS: set[str] | None = None


def _realizations() -> set[str]:
    global _REALIZATIONS
    if _REALIZATIONS is None:
        _REALIZATIONS = realization_names()
    return _REALIZATIONS


def extract_fences(text: str) -> tuple[list[str], str]:
    """Return (ordered fence bodies, text with fences removed).

    Fence bodies are CITATION-NORMALISED before being compared: a bare cite
    inside a fence may be upgraded to a full path just as in prose (the same
    Check 25 rule). Everything else in a fence stays verbatim-immutable, so an
    edited operator (=e= -> =g=) or a changed line number is still a REJECT.
    """
    bodies = [CITE_RE.sub(canon_cite, m.group(1)) for m in FENCE_RE.finditer(text)]
    return bodies, FENCE_RE.sub("\n", text)


def canon_cite(m: re.Match) -> str:
    """Canonical form of a citation: 'basename:lines' (path dropped)."""
    lines = m.group("lines") or ""
    return f"{m.group('base')}:{lines}" if lines else m.group("base")


def extract_cites(text: str) -> tuple[list[tuple[str, str]], str]:
    """Return ([(canonical, full_match)], text with citations masked out).

    Masking prevents a citation path's own digits (modules/13_tc/...) and any
    .gms basename from leaking into the numeral / identifier multisets.
    """
    found: list[tuple[str, str]] = []

    def _mask(m: re.Match) -> str:
        found.append((canon_cite(m), m.group(0)))
        return " \x00CITE\x00 "

    return found, CITE_RE.sub(_mask, text)


def cite_path_ok(full: str) -> bool:
    """True if a full-path cite resolves on disk (bare cites are always ok).

    A bare cite has no '/' and needs no resolution. A full-path cite must point at
    a real file, resolved from the MAgPIE root (docs cite 'modules/NN_x/r/f.gms').
    """
    path_part = full.split(":")[0]
    if "/" not in path_part:
        return True
    if PLACEHOLDER_CITE_RE.search(path_part):
        return True  # pedagogical example, not a claim about a real file
    return (MAGPIE_ROOT / path_part).is_file()


def profile(text: str) -> dict:
    """Extract the four invariant profiles from a doc."""
    fences, rest = extract_fences(text)
    cites, masked = extract_cites(rest)
    # Raw cites from the ORIGINAL fenced text too, so a full path introduced
    # inside a code fence is still disk-checked (extract_fences normalises fence
    # bodies to canonical form, which would otherwise hide the path).
    fence_raw = [m.group(0)
                 for b in FENCE_RE.findall(text)
                 for m in CITE_RE.finditer(b)]
    reals = _realizations()
    return {
        "fences": fences,
        "idents": Counter(IDENT_RE.findall(masked)),
        "nums": Counter(NUM_RE.findall(masked)),
        "cites": Counter(c for c, _ in cites),
        "cite_raw": [full for _, full in cites] + fence_raw,
        # (e) (identifier, domain) pairs -- a bare mention pairs with "".
        "domains": Counter(
            (m.group(1), m.group(2) or "") for m in IDENT_DOMAIN_RE.finditer(masked)
        ),
        # (f) hedge / quantifier words, lowercased.
        "hedges": Counter(h.lower() for h in HEDGE_RE.findall(masked)),
        # (g) module-directory and realization tokens appearing in PROSE.
        "entities": Counter(MODDIR_RE.findall(masked))
        + Counter(w for w in re.findall(r"[\w.]+", masked) if w in reals),
    }


def _counter_delta(before: Counter, after: Counter) -> list[str]:
    """Human-readable +added / -removed lines for a multiset difference."""
    out = []
    for tok, n in sorted((after - before).items()):
        out.append(f"    + {tok}" + (f" (x{n})" if n > 1 else ""))
    for tok, n in sorted((before - after).items()):
        out.append(f"    - {tok}" + (f" (x{n})" if n > 1 else ""))
    return out


def compare(before_text: str, after_text: str, label: str = "",
            info: list[str] | None = None,
            review: list[str] | None = None) -> list[str]:
    """Return a list of violation strings. Empty list == invariance holds.

    `label` is the doc path; it enables the own-module-number carve-out.
    `info`, if given, collects non-fatal observations for the report.
    `review`, if given, collects REVIEWED-ADDITIONS items: not fatal, but never
    silent -- they must be signed off, and they block under --strict.
    """
    b, a = profile(before_text), profile(after_text)
    v: list[str] = []
    info = info if info is not None else []
    review = review if review is not None else []

    if b["idents"] != a["idents"]:
        v.append("IDENTIFIERS changed:")
        v.extend(_counter_delta(b["idents"], a["idents"]))

    b_nums, a_nums = b["nums"], a["nums"]
    own = OWN_MODNUM_RE.search(label or "")
    if own:
        tok = str(int(own.group(1)))  # "13" from module_13.md
        b_n, a_n = b_nums.get(tok, 0), a_nums.get(tok, 0)
        if b_n != a_n:
            if a_n > b_n:
                v.append(
                    f"NUMERALS: own module number {tok!r} count ROSE "
                    f"{b_n} -> {a_n} (new self-claims are not a form change)"
                )
            elif a_n == 0 and b_n > 0:
                v.append(
                    f"NUMERALS: own module number {tok!r} vanished entirely "
                    f"({b_n} -> 0); presence must be preserved"
                )
            else:
                info.append(
                    f"own module number {tok!r} self-reference count "
                    f"{b_n} -> {a_n} (allowed: implicit in per-module doc context)"
                )
            b_nums, a_nums = Counter(b_nums), Counter(a_nums)
            b_nums.pop(tok, None)
            a_nums.pop(tok, None)

    if b_nums != a_nums:
        v.append("NUMERALS changed:")
        v.extend(_counter_delta(b_nums, a_nums))

    if b["fences"] != a["fences"]:
        if len(b["fences"]) != len(a["fences"]):
            v.append(
                f"CODE FENCES changed: {len(b['fences'])} before, "
                f"{len(a['fences'])} after"
            )
        else:
            for i, (fb, fa) in enumerate(zip(b["fences"], a["fences"])):
                if fb != fa:
                    v.append(f"CODE FENCE #{i + 1} body edited:")
                    v.append(f"    - {fb.strip()[:120]!r}")
                    v.append(f"    + {fa.strip()[:120]!r}")

    # (e) Domain signatures. Report only pairs whose DOMAIN changed for an
    # identifier that is otherwise present, so this does not restate an
    # identifier-count change already reported above.
    if b["domains"] != a["domains"] and b["idents"] == a["idents"]:
        lost = [f"{i}{d}" for (i, d), n in (b["domains"] - a["domains"]).items() if d]
        gained = [f"{i}{d}" for (i, d), n in (a["domains"] - b["domains"]).items() if d]
        if lost or gained:
            v.append("DOMAIN SIGNATURES changed:")
            v.extend(f"    - {x}" for x in sorted(lost))
            v.extend(f"    + {x}" for x in sorted(gained))

    # (f) Hedges / quantifiers.
    if b["hedges"] != a["hedges"]:
        v.append("HEDGES/QUANTIFIERS changed (a dropped hedge flattens a claim):")
        v.extend(_counter_delta(b["hedges"], a["hedges"]))

    # (g) Module-directory / realization tokens in prose. Split by direction,
    # per H.7 ("if the gate is too strict, relax to a reviewed-additions mode --
    # do not weaken the invariants"). A REMOVAL drops a claim and is fatal. An
    # ADDITION is usually a legitimate migration artefact (a Module column
    # gaining `22_land_conservation` where the prose said "Module 22"), but pilot
    # error 3 was an addition, so additions are never silent: they are surfaced
    # for sign-off and block under --strict.
    ent_removed = b["entities"] - a["entities"]
    ent_added = a["entities"] - b["entities"]
    if ent_removed:
        v.append("MODULE-DIR / REALIZATION tokens REMOVED (claim dropped):")
        v.extend(f"    - {t}" + (f" (x{n})" if n > 1 else "")
                 for t, n in sorted(ent_removed.items()))
    if ent_added:
        review.append("MODULE-DIR / REALIZATION tokens ADDED (verify each is correct):")
        review.extend(f"    + {t}" + (f" (x{n})" if n > 1 else "")
                      for t, n in sorted(ent_added.items()))

    # Citations: canonical multiset must match (bare -> full is form, not meaning).
    if b["cites"] != a["cites"]:
        v.append("CITATIONS changed (canonical basename:line form):")
        v.extend(_counter_delta(b["cites"], a["cites"]))

    # ...but any full path introduced must actually resolve on disk.
    new_paths = [p for p in a["cite_raw"] if p not in b["cite_raw"]]
    for p in new_paths:
        if not cite_path_ok(p):
            v.append(f"CITATION path does not resolve on disk: {p}")

    return [f"{label}: {s}" if label and not s.startswith("    ") else s for s in v]


# --------------------------------------------------------------------------- #
# Self-test: synthesize the known bugs FIRST, then assert the gate catches them.
# --------------------------------------------------------------------------- #

_BEFORE = """\
# Module 13 (tc)

Module 13 provides `vm_tau` to Module 14 and receives `pm_land_start` from
Module 10. The calibration runs over 140 iterations.

See declarations.gms:9 for the declaration.

```gams
q13_tech_cost(i2) .. vm_tech_cost(i2) =e= sum(kcr, p13_cost(i2,kcr));
```
"""


def self_test() -> int:
    """Positive controls (must REJECT) + clean controls (must ACCEPT).

    Per the project rule for new validators: build the positive test matching the
    bug class BEFORE trusting any clean result. "0 violations" is otherwise
    ambiguous between "the rewrite was safe" and "the gate is broken".
    """
    cases: list[tuple[str, str, bool]] = []  # (name, after_text, expect_reject)

    # --- POSITIVE: the ways a regularizer silently changes meaning ------------
    cases.append((
        "identifier swapped (vm_tau -> vm_tau_hist)",
        _BEFORE.replace("`vm_tau`", "`vm_tau_hist`"), True,
    ))
    cases.append((
        "identifier dropped (claim omitted during rewrite)",
        _BEFORE.replace(" and receives `pm_land_start` from\nModule 10", ""), True,
    ))
    cases.append((
        "numeral edited (140 -> 141 iterations)",
        _BEFORE.replace("140 iterations", "141 iterations"), True,
    ))
    cases.append((
        "code fence body edited (=e= -> =g=)",
        _BEFORE.replace("=e= sum(kcr", "=g= sum(kcr"), True,
    ))
    cases.append((
        "code fence deleted",
        FENCE_RE.sub("", _BEFORE), True,
    ))
    cases.append((
        "citation line number changed (:9 -> :19)",
        _BEFORE.replace("declarations.gms:9", "declarations.gms:19"), True,
    ))
    cases.append((
        "citation upgraded to a NON-EXISTENT path",
        _BEFORE.replace(
            "declarations.gms:9",
            "modules/13_tc/no_such_realization/declarations.gms:9"), True,
    ))
    cases.append((
        "module number changed in prose (Module 10 -> Module 11)",
        _BEFORE.replace("from\nModule 10", "from\nModule 11"), True,
    ))

    # --- CLEAN: the ways Pass A is *supposed* to change a doc -----------------
    cases.append((
        "pure reflow + heading/badge change",
        _BEFORE.replace(
            "# Module 13 (tc)",
            "# Module 13 — Technological Change (`tc`)\n\n**Status**: 🟢 Verified"
        ).replace("to Module 14 and receives", "to Module 14\nand receives"), False,
    ))
    cases.append((
        "prose attribution migrated into a table (the pilot's whole point)",
        """\
# Module 13 (tc)

### Provides To

| Module | Variable |
|---|---|
| Module 14 | `vm_tau` |

### Receives From

| Module | Variable |
|---|---|
| Module 10 | `pm_land_start` |

The calibration runs over 140 iterations.

See declarations.gms:9 for the declaration.

```gams
q13_tech_cost(i2) .. vm_tech_cost(i2) =e= sum(kcr, p13_cost(i2,kcr));
```
""", False,
    ))
    cases.append((
        "bare cite upgraded to a REAL full path (Check 25 rule)",
        _BEFORE.replace(
            "declarations.gms:9", "modules/13_tc/exo/declarations.gms:9"), False,
    ))

    # --- POSITIVE: the own-module-number carve-out must not become a hole -----
    cases.append((
        "own module number vanishes entirely (13 dropped from doc)",
        _BEFORE.replace("# Module 13 (tc)", "# Technological Change (tc)")
               .replace("Module 13 provides", "This module provides"), True,
    ))
    # Injects ONLY the numeral 13 -- no new identifier, no other numeral -- so
    # the own-number ROSE arm is the only thing that can catch it. (An earlier
    # fixture also added `vm_tau` and passed via the IDENTIFIERS arm instead,
    # leaving the carve-out's own guard untested.)
    cases.append((
        "own module number count ROSE (new self-claim invented)",
        _BEFORE.replace(
            "The calibration runs",
            "Module 13 also drives that scaling. The calibration runs"), True,
    ))

    # --- Fence-internal citations (found by the real-world control, e982a76) --
    # The bare-cite migration rewrote cites INSIDE code fences. A verbatim fence
    # invariant rejects that legitimate form change, so fence bodies are
    # citation-normalised -- but only that. These four cases pin the boundary.
    fb = (
        "# Module 13 (tc)\n\n"
        "```gams\n"
        "* see declarations.gms:9\n"
        "q13_tech_cost(i2) .. vm_tech_cost(i2) =e= 140;\n"
        "```\n"
    )
    cases.append((
        "fence-internal bare cite -> REAL full path", fb,
        fb.replace("declarations.gms:9", "modules/13_tc/exo/declarations.gms:9"),
        False,
    ))
    cases.append((
        "fence-internal placeholder cite (NN_xxx) introduced", fb,
        fb.replace("declarations.gms:9",
                   "modules/NN_xxx/realization/declarations.gms:9"), False,
    ))
    cases.append((
        "fence-internal cite LINE changed (:9 -> :19)", fb,
        fb.replace("declarations.gms:9", "declarations.gms:19"), True,
    ))
    cases.append((
        "fence-internal cite -> NON-EXISTENT real-looking path", fb,
        fb.replace("declarations.gms:9",
                   "modules/13_tc/no_such_real/declarations.gms:9"), True,
    ))
    cases.append((
        "fence body still immutable around a cite (=e= -> =g=)", fb,
        fb.replace("=e= 140", "=g= 140"), True,
    ))

    # --- Invariants (e)-(g), each pinned to the REAL P0 pilot error it closes --
    # Not fixtures: these are the actual before/after texts from the four errors
    # recorded in audit/regularization_p0_result.md (the R56 discipline -- a new
    # check is validated against a real historical bug, not a synthetic one).
    dom_b = "**pm_yields_semi_calib(j,kve,w)** - 1995 calibrated yields (tDM/ha/yr)\n"
    dom_a = "**Tertiary Output:** 1995 calibrated yields (tDM/ha/yr)\n\n" \
            "| M 17 | `pm_yields_semi_calib` | sole consumer |\n"
    cases.append((
        "PILOT ERROR 2: domain signature (j,kve,w) stripped doc-wide",
        dom_b, dom_a, True,
    ))

    hedge_b = ("Shared input table `fm_attributes` is read by many modules "
               "(18_residues, 20_processing) for conversion.\n")
    hedge_a = ("| Module | Variable |\n|---|---|\n"
               "| 18_residues | `fm_attributes` |\n| 20_processing | `fm_attributes` |\n")
    cases.append((
        "PILOT ERROR 1: hedge 'many' dropped, list reads as exhaustive",
        hedge_b, hedge_a, True,
    ))

    real_b = "Module 17 is the sole consumer of `pm_yields_semi_calib`.\n"
    real_a = ("Module 17 is the sole consumer of `pm_yields_semi_calib` "
              "(Production realization `flexreg_apr16`).\n")
    cases.append((
        "PILOT ERROR 3: net-new realization qualifier (addition -> review, not reject)",
        real_b, real_a, False,   # an ADDITION: surfaced for sign-off, not fatal
    ))
    cases.append((
        "module-dir token REMOVED (claim dropped) is fatal",
        "Handled by `22_land_conservation` during presolve.\n",
        "Handled during presolve.\n", True,
    ))

    ok = True
    print(f"{CHECK_NAME} self-test")
    print("=" * 60)
    for case in cases:
        if len(case) == 4:
            name, before, after, expect_reject = case
        else:
            name, after, expect_reject = case
            before = _BEFORE
        notes: list[str] = []
        violations = compare(before, after, label="modules/module_13.md", info=notes)
        rejected = bool(violations)
        kind = "positive" if expect_reject else "clean"
        if rejected == expect_reject:
            detail = violations[0] if violations else (
                f"no violations; INFO: {notes[0]}" if notes else "no violations")
            print(f"  PASS [{kind}] {name}")
            print(f"         -> {detail}")
        else:
            ok = False
            if expect_reject:
                print(f"  FAIL [{kind}] {name}")
                print("         -> gate did NOT catch a planted meaning change")
            else:
                print(f"  FAIL [{kind}] {name}")
                for line in violations:
                    print(f"         {line}")

    # The reviewed-additions split must actually route: an added realization
    # token is NOT a violation but MUST appear in the review list (never silent).
    rev: list[str] = []
    viol = compare(real_b, real_a, label="modules/module_14.md", review=rev)
    if not viol and any("flexreg_apr16" in r for r in rev):
        print("  PASS [review] added realization token routed to review, not silence")
    else:
        ok = False
        print(f"  FAIL [review] addition mis-routed: violations={viol} review={rev}")

    # Guard the disk-resolution arm itself: the "real full path" clean case is
    # only meaningful if that file actually exists in this checkout.
    probe = MAGPIE_ROOT / "modules/13_tc/exo/declarations.gms"
    if not probe.is_file():
        ok = False
        print(f"  FAIL [meta] self-test fixture path missing: {probe}")
    else:
        print(f"  PASS [meta] fixture path resolves: modules/13_tc/exo/declarations.gms")

    print("=" * 60)
    if ok:
        print(f"{CHECK_NAME} self-test: PASS ({len(cases)} cases)")
        # The count travels on the sentinel so selftest_validator.sh can ratchet
        # it (audit/selftest_assertion_counts.json). This check prints a SUMMARY
        # rather than one line per case, so the harness cannot derive it.
        print(f"SELFTEST_OK {CHECK_NAME} {len(cases)}")
        return 0
    print(f"{CHECK_NAME} self-test: FAIL")
    return 1


def _git_show(ref: str, path: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(AGENT_DIR), "show", f"{ref}:{path}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"ERROR: cannot read {path} at {ref}: {r.stderr.strip()}")
        sys.exit(2)
    return r.stdout


def main() -> int:
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()

    pairs: list[tuple[str, str, str]] = []  # (label, before, after)

    if "--git-diff" in argv:
        i = argv.index("--git-diff")
        rest = argv[i + 1:]
        if len(rest) < 2:
            print("usage: --git-diff <ref> <path> [<path> ...]")
            return 2
        ref, paths = rest[0], rest[1:]
        for p in paths:
            after_path = AGENT_DIR / p
            if not after_path.is_file():
                print(f"ERROR: missing working-tree file: {p}")
                return 2
            pairs.append((p, _git_show(ref, p),
                          after_path.read_text(encoding="utf-8")))
    elif "--before" in argv and "--after" in argv:
        b = Path(argv[argv.index("--before") + 1])
        a = Path(argv[argv.index("--after") + 1])
        pairs.append((a.name, b.read_text(encoding="utf-8"),
                      a.read_text(encoding="utf-8")))
    else:
        print(__doc__)
        return 2

    strict = "--strict" in argv
    print("Semantic-invariance gate (P0 regularization)")
    print("=" * 60)
    total = 0
    total_review = 0
    for label, before, after in pairs:
        notes: list[str] = []
        reviews: list[str] = []
        violations = compare(before, after, label=label, info=notes, review=reviews)
        p = profile(before)
        cov = (f"{len(p['idents'])} idents / {sum(p['nums'].values())} numerals / "
               f"{len(p['fences'])} fences / {sum(p['cites'].values())} cites")
        if violations:
            total += len(violations)
            print(f"\n❌ REJECT  {label}   [{cov}]")
            for line in violations:
                print(f"  {line}")
        elif reviews:
            total_review += 1
            print(f"\n⚠️  REVIEW  {label}   [{cov}] invariant, but new claim surface:")
            for line in reviews:
                print(f"  {line}")
        else:
            print(f"✅ ACCEPT  {label}   [{cov}] invariant")
        for line in notes:
            print(f"     INFO: {line}")
        if violations and reviews:
            for line in reviews:
                print(f"  (also, pending review) {line}")

    print()
    print("=" * 60)
    if total:
        print(f"{CHECK_NAME}: {total} violation(s) -> REJECT the diff.")
        print("Form may move; meaning may not. Revert the doc and re-run Pass A.")
        return 1
    if total_review:
        print(f"{CHECK_NAME}: 0 violations, but {total_review} doc(s) introduced new "
              f"claim surface needing sign-off.")
        if strict:
            print("--strict: treating reviewed additions as blocking.")
            return 1
        print("Verify each ADDED token against the code, then accept.")
        return 0
    print(f"{CHECK_NAME}: 0 violations across {len(pairs)} doc(s) -> invariance holds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
