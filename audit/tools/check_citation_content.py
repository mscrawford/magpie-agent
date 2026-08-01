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
from check_answer_identifiers import RE_GAMS_IDENT, split_batch  # noqa: E402

# Files we are willing to resolve a citation against.
ALLOWED_PREFIXES = ("modules/", "core/", "config/")

# `modules/x/y.gms:12`, `:12-14`, `:12,17`; also config/default.cfg:811
RE_CITATION = re.compile(
    r"\b((?:modules|core|config)/[A-Za-z0-9_./-]+\.(?:gms|cfg)):(\d+(?:\s*[-,]\s*\d+)*)"
)

# Tokens that can be "the thing cited": GAMS identifiers, realization-ish names,
# and config keys. Deliberately broader than RE_GAMS_IDENT.
RE_CLAIMED = re.compile(
    r"`([A-Za-z][A-Za-z0-9_$.]{2,})`"          # backticked token
    r"|\b((?:vm|pm|fm|sm|im|om|xm|q\d{2}|v\d{2}|p\d{2}|s\d{2}|c\d{2}|i\d{2}|f\d{2}|o\d{2}|x\d{2})_[a-z][A-Za-z0-9_]*)\b"
)

NEAR_WINDOW = 3          # +/- lines counted as "off by small"
LOOKBEHIND = 240         # chars before the citation searched for claimed identifiers


# An equation definition: `q30_prod(j2,kcr) ..` — occurs exactly once per file,
# which is what makes it usable as a STRUCTURAL anchor.
RE_EQN_DEF = re.compile(r"^\s*(q\d{2}_[A-Za-z0-9_]+)\s*(\([^)]*\))?\s*\.\.")


class Files:
    """Line-indexed reader for citable files, with a cache."""

    def __init__(self, root: Path):
        self.root = root
        self._cache: dict[str, list[str] | None] = {}
        self._spans: dict[str, dict[str, tuple[int, int]]] = {}

    def lines(self, rel: str) -> list[str] | None:
        if rel not in self._cache:
            if not rel.startswith(ALLOWED_PREFIXES) or ".." in rel:
                self._cache[rel] = None
            else:
                p = self.root / rel
                try:
                    self._cache[rel] = p.read_text(errors="ignore").splitlines()
                except OSError:
                    self._cache[rel] = None
        return self._cache[rel]

    def equation_spans(self, rel: str) -> dict[str, tuple[int, int]]:
        """{equation name: (first line, terminator line)} for one file.

        A doc legitimately cites a BODY line of an equation while naming the
        equation for context -- `q30_prod` is defined at :14 but its body is :15.
        A proximity threshold cannot tell that apart from a citation that drifted
        onto a neighbouring equation; the span boundary can, categorically.
        Only equation names get this treatment: they are defined exactly once per
        file. Recurring symbols (vm_/pm_) have no unique anchor and stay on the
        plain proximity check.
        """
        if rel in self._spans:
            return self._spans[rel]
        out: dict[str, tuple[int, int]] = {}
        lines = self.lines(rel) or []
        for i, ln in enumerate(lines, start=1):
            m = RE_EQN_DEF.match(ln)
            if not m:
                continue
            end = i
            for j in range(i, min(len(lines), i + 80)):
                end = j + 1
                if ";" in lines[j]:
                    break
            out[m.group(1)] = (i, end)
        self._spans[rel] = out
        return out


def _claimed_identifiers(text: str, cite_start: int) -> list[str]:
    """Identifiers appearing shortly BEFORE the citation — what it is cited for."""
    left = text[max(0, cite_start - LOOKBEHIND): cite_start]
    # Stop at a hard sentence boundary so we do not reach into a previous claim.
    for sep in ("\n\n", ". ", "; "):
        i = left.rfind(sep)
        if i != -1:
            left = left[i + len(sep):]
    out: list[str] = []
    for m in RE_CLAIMED.finditer(left):
        tok = m.group(1) or m.group(2)
        if tok and tok not in out:
            out.append(tok)
    return out


def _parse_lines(spec: str) -> list[int]:
    nums = [int(x) for x in re.findall(r"\d+", spec)]
    if "-" in spec and len(nums) == 2:
        lo, hi = sorted(nums)
        if hi - lo <= 60:
            return list(range(lo, hi + 1))
    return nums


def check_text(text: str, files: Files) -> list[dict]:
    findings: list[dict] = []
    for m in RE_CITATION.finditer(text):
        rel, spec = m.group(1), m.group(2)
        lines = files.lines(rel)
        if lines is None:
            continue                      # unresolvable path: another checker's job
        cited = _parse_lines(spec)
        if not cited:
            continue
        claimed = _claimed_identifiers(text, m.start())
        if not claimed:
            continue                      # nothing asserted next to it; nothing to verify

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
    ("unresolvable path is not this checker's finding",
     "`vm_prod` is at `modules/99_invented/default/equations.gms:12`."),
]


def selftest(files: Files) -> int:
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

    files = Files(Path(a.root).resolve())
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
