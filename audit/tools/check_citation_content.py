#!/usr/bin/env python3
"""Verify that a cited `file:line` actually CONTAINS the identifier it is cited for.

Why this predicate
------------------
Reading the 261 findings the hardened regrade produced, one family dominates: a
citation that points at a real file but the wrong place in it. Off-by-one
(`input.gms:23` when the symbol is at `:24`), a line that turns out to be a
comment rather than the assignment, a line past the end of the file, or an
identifier that is not in that file at all. All four are decidable without
judgment, and one predicate settles them:

    does the cited line (or line range) contain the identifier being claimed?

Graded, because the classes differ in severity:

  citation_identifier_absent  - the identifier is nowhere in the cited file  (major)
  citation_line_wrong         - it is in the file, but far from the cited line (moderate)
  citation_off_by_small       - it is within +/-3 lines of the citation        (minor)
  citation_out_of_range       - the cited line is past the end of the file     (major)

Precision rule that matters: a sentence often names several identifiers around one
citation. A finding is emitted ONLY IF **none** of the nearby claimed identifiers
resolves at the cited location. That makes a flag mean "this citation supports
nothing it is next to", not "one of several tokens did not match".

Scope: decides placement, not truth. A correctly-placed citation can still support
a false claim, and this says nothing about that.

Extraction, the existence oracle and the shared guards live in `magpie_corpus`
(2026-08-01 consolidation). Note one guard deliberately NOT taken from there:
`is_identifier_prefix`. This checker matches a claimed identifier as a SUBSTRING
of the cited line, so a stem (`vm_peatland`) already resolves against its full
name (`vm_peatland_cost`); excluding stems would only cost recall.

Usage
-----
  python3 check_citation_content.py --selftest
  python3 check_citation_content.py --batch <file.md> --root <magpie-root> [--json out]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magpie_corpus import (  # noqa: E402
    GAMS_PREFIX_ALT,
    RE_CITATION,
    Tree,
    is_filename,
    is_glob_stem,
    is_negated_claim,
    split_batch,
)

# Tokens that can be "the thing cited": GAMS identifiers, realization-ish names,
# and config keys. Deliberately broader than RE_GAMS_IDENT -- but the GAMS half
# is BUILT from the shared prefix alternation rather than re-spelled, which is
# the divergence this consolidation removed.
RE_CLAIMED = re.compile(
    r"`([A-Za-z][A-Za-z0-9_$.]{2,})`"                       # backticked token
    rf"|\b((?:{GAMS_PREFIX_ALT})_[a-z][A-Za-z0-9_]*)\b"     # bare GAMS identifier
)

NEAR_WINDOW = 3          # +/- lines counted as "off by small"
LOOKBEHIND = 240         # chars before the citation searched for claimed identifiers


def _claimed_identifiers(text: str, cite_start: int, dir_names: set[str] | None = None
                         ) -> tuple[list[str], str]:
    """Identifiers appearing shortly BEFORE the citation -- what it is cited for.

    Returns (identifiers, clause) so the caller can also test the clause for
    negation without re-deriving the sentence boundary.
    """
    left = text[max(0, cite_start - LOOKBEHIND): cite_start]
    # Stop at a hard sentence boundary so we do not reach into a previous claim.
    for sep in ("\n\n", ". ", "; "):
        i = left.rfind(sep)
        if i != -1:
            left = left[i + len(sep):]
    out: list[str] = []
    for m in RE_CLAIMED.finditer(left):
        tok = m.group(1) or m.group(2)
        if not tok or tok in out:
            continue
        # A realization / module directory name is a LOCATION, not file content,
        # so it can never appear inside the cited file's text. Treating these as
        # claimed identifiers produced 7 of 7 false positives in the 2026-08-01
        # stratified precision sample.
        if dir_names and tok in dir_names:
            continue
        # ...and neither is a FILE name. A file essentially never contains its own
        # basename, so admitting `presolve.gms` guarantees a spurious
        # "identifier absent from the cited file".
        if is_filename(tok):
            continue
        # `s57_maxmac_*` is a GLOB the doc wrote; the regex sees the stem
        # `s57_maxmac_`. A trailing underscore is never a real identifier, and
        # the family it globs usually lives in a different file from the cited
        # effect.
        if is_glob_stem(tok):
            continue
        out.append(tok)
    return out, left


def _parse_lines(spec: str) -> list[int]:
    nums = [int(x) for x in re.findall(r"\d+", spec)]
    if "-" in spec and len(nums) == 2:
        lo, hi = sorted(nums)
        if hi - lo <= 60:
            return list(range(lo, hi + 1))
    return nums


def check_text(text: str, files: Tree) -> list[dict]:
    findings: list[dict] = []
    for m in RE_CITATION.finditer(text):
        rel, spec = m.group(1), m.group(2)
        lines = files.lines(rel)
        if lines is None:
            continue                      # unresolvable path: another checker's job
        cited = _parse_lines(spec)
        if not cited:
            continue
        claimed, clause = _claimed_identifiers(text, m.start(), files.dir_names)
        if not claimed:
            continue                      # nothing asserted next to it; nothing to verify
        # The clause may be DENYING that the identifier is there -- "no
        # `s15_secondsolve` switch exists (`.../input.gms:12`)". An identifier
        # absent from the cited file is then the answer being RIGHT, not a
        # mis-citation. Guard ported from the fabrication checker, where the same
        # class was 3 of 7 false positives. Anchored per token: see
        # `is_negated_claim` for why a clause-wide cue test is wrong here.
        if is_negated_claim(clause, claimed):
            continue

        n = len(lines)
        over = [c for c in cited if c > n]
        if over:
            findings.append({
                "kind": "citation_out_of_range", "path": rel,
                "cited": spec, "detail": f"file has {n} lines",
                "claimed": claimed[:4],
            })
            continue

        # Does ANY claimed identifier land on ANY cited line?
        def on(ls: list[int]) -> bool:
            return any(
                tok in lines[i - 1]
                for i in ls if 1 <= i <= n
                for tok in claimed
            )

        if on(cited):
            continue                      # citation supports something next to it

        # STRUCTURAL anchor before the proximity fallback: if a claimed equation
        # name owns a span in this file and the cited line sits INSIDE it, the
        # citation is correct (a body line cited under the equation's name).
        spans = files.equation_spans(rel)
        if any(
            tok in spans and spans[tok][0] <= c <= spans[tok][1]
            for tok in claimed for c in cited
        ):
            continue

        near = [i for c in cited for i in range(c - NEAR_WINDOW, c + NEAR_WINDOW + 1)
                if 1 <= i <= n]
        if on(near):
            actual = sorted({i for i in near for tok in claimed if tok in lines[i - 1]})
            findings.append({
                "kind": "citation_off_by_small", "path": rel, "cited": spec,
                "detail": f"found at {actual}", "claimed": claimed[:4],
            })
            continue

        elsewhere = sorted({i for i in range(1, n + 1)
                            for tok in claimed if tok in lines[i - 1]})
        if elsewhere:
            findings.append({
                "kind": "citation_line_wrong", "path": rel, "cited": spec,
                "detail": f"found instead at {elsewhere[:6]}", "claimed": claimed[:4],
            })
        else:
            findings.append({
                "kind": "citation_identifier_absent", "path": rel, "cited": spec,
                "detail": "none of the claimed identifiers appears anywhere in this file",
                "claimed": claimed[:4],
            })
    return findings


CERTAIN = {"citation_identifier_absent", "citation_line_wrong", "citation_out_of_range"}

# --------------------------------------------------------------------------
# Self-test. Every control's ground truth was read out of the tree by hand
# before being written here (2026-08-01).
# --------------------------------------------------------------------------

POSITIVES = [
    ("off-by-one: s30_betr_target is at :24, not :23",
     "`s30_betr_target = 0` (`modules/30_croparea/simple_apr24/input.gms:23`)",
     "citation_off_by_small"),
    ("identifier absent from the cited file",
     "`vm_totallyfakevariable` is defined at `modules/30_croparea/simple_apr24/equations.gms:15`.",
     "citation_identifier_absent"),
    ("right file, far-wrong line",
     "The production identity `vm_prod` sits at `modules/30_croparea/simple_apr24/equations.gms:1`.",
     "citation_line_wrong"),
    ("cited line past end of file",
     "`q29_fallow_min` is at `modules/29_cropland/detail_apr24/equations.gms:346`.",
     "citation_out_of_range"),
    # Structural-anchor control, OUT-of-span direction. Without this the span
    # suppression could silently become a no-op that still passes its happy path.
    ("equation name cited OUTSIDE its span is still flagged",
     "the equation `q30_prod` is at `modules/30_croparea/simple_apr24/equations.gms:1`.",
     "citation_line_wrong"),
    # Negation-guard boundary: the guard must not swallow an ORDINARY mis-citation
    # merely because the sentence contains the word "not". Without this control the
    # ported guard could silently become a recall hole.
    ("a sentence with an unrelated 'not' is still checked",
     "`vm_totallyfakevariable` is not optional and is defined at "
     "`modules/30_croparea/simple_apr24/equations.gms:15`.",
     "citation_identifier_absent"),
]

NEGATIVES = [
    ("correct citation (vm_prod_reg at :18)",
     "residue biomass scales with `vm_prod_reg` (`modules/18_residues/flexreg_apr16/equations.gms:18`)"),
    ("correct citation (vm_prod at :15)",
     "`vm_prod` is set by the production identity (`modules/30_croparea/simple_apr24/equations.gms:15`)"),
    ("correct citation (q30_prod at :14)",
     "the equation `q30_prod` (`modules/30_croparea/simple_apr24/equations.gms:14`)"),
    ("range citation containing the symbol",
     "`vm_prod` appears in `modules/30_croparea/simple_apr24/equations.gms:14-16`."),
    ("multi-identifier sentence: one matches, so no finding",
     "`vm_area` and `vm_yld` and `vm_prod` all appear at "
     "`modules/30_croparea/simple_apr24/equations.gms:15`."),
    ("no identifier claimed next to the citation",
     "See `modules/30_croparea/simple_apr24/equations.gms:15` for details."),
    # Structural-anchor control, IN-span direction: q30_prod is DEFINED at :14,
    # but citing its body line :15 under the equation's name is legitimate and
    # must not be flagged. This is the FP class a +/-N threshold cannot separate.
    ("equation name cited at its BODY line, inside the span",
     "the equation `q30_prod` (`modules/30_croparea/simple_apr24/equations.gms:15`)"),
    ("REGRESSION: glob stem is not a claimed identifier",
     "`s57_maxmac_*` causes a 1/(1-mitigation) blowup "
     "(`modules/57_maccs/on_aug22/equations.gms:38,48`)."),
    ("unresolvable path is not this checker's finding",
     "`vm_prod` is at `modules/99_invented/default/equations.gms:12`."),
    # Ported negation guard: asserting a symbol is ABSENT, with a citation to the
    # file checked, is the answer being right.
    ("REGRESSION: negated claim about an absent symbol",
     "There is no such thing as `vm_totallyfakevariable` in "
     "`modules/30_croparea/simple_apr24/equations.gms:15`."),
    # Both from adjudicating the 2026-08-01 consolidation diff, verbatim in shape.
    ("REGRESSION: a filename is not a claimed identifier",
     "the withdrawal variable is directly fixed every timestep in `presolve.gms` "
     "(`modules/42_water_demand/all_sectors_aug13/presolve.gms:38-54`):"),
    ("REGRESSION: elided identifier inside a denial",
     "There is no `q42_...` equation for these three sectors (Module 42 has exactly two "
     "equations total, both for agriculture/costs - "
     "`modules/42_water_demand/all_sectors_aug13/declarations.gms:21-24`)."),
]


def selftest(files: Tree) -> int:
    bad = 0
    print("== POSITIVE controls ==")
    for name, text, kind in POSITIVES:
        got = check_text(text, files)
        hit = any(f["kind"] == kind for f in got)
        print(f"  [{'PASS' if hit else 'FAIL'}] {name}  (expect {kind})")
        if not hit:
            bad += 1
            print(f"        got: {got}")
    print("== NEGATIVE controls (must be clean) ==")
    for name, text in NEGATIVES:
        got = check_text(text, files)
        ok = not got
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            bad += 1
            print(f"        false positives: {got}")
    print(f"\nself-test: {bad} failure(s)")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--batch")
    ap.add_argument("--json")
    a = ap.parse_args()

    files = Tree(Path(a.root).resolve())
    if a.selftest:
        return 1 if selftest(files) else 0
    if not a.batch:
        ap.error("need --batch or --selftest")

    answers = split_batch(Path(a.batch))
    res = {lab: check_text(txt, files) for lab, txt in sorted(answers.items())}
    tot = sum(len(v) for v in res.values())
    certain = sum(1 for v in res.values() for f in v if f["kind"] in CERTAIN)
    print(f"{tot} citation findings over {sum(1 for v in res.values() if v)}/{len(answers)} answers "
          f"({certain} in the mechanically-certain classes)")
    for lab, fs in sorted(res.items()):
        for f in fs:
            print(f"  {lab}  {f['kind']:<28} {f['path']}:{f['cited']}  {f['detail']}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
