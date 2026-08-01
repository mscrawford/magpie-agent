#!/usr/bin/env python3
"""Flag a doc that describes a NON-DEFAULT realization without saying so.

Why this one
------------
The hardened regrade measured where propagation actually concentrates. The worst
trap in the corpus (T5) scores 25% on outright falsehoods but **75%** once
"true, but of a realization it never flags as non-default" is counted -- the
largest narrow/wide gap anywhere in the run. `AGENT.md` Step 1c already instructs
"ALWAYS LEAD WITH THE DEFAULT REALIZATION" in prose, and the measurement says
prose does not work.

The predicate is fully mechanical: realizations enumerate from the module tree,
defaults come from `config/default.cfg` (all 46 modules resolve, and every default
names a directory that exists -- both asserted by `magpie_corpus --selftest`).

Suppression is STRUCTURAL, not a distance window: a reference is excused when the
markdown section CONTAINING it establishes the default -- by naming the module's
default realization, or by using default/non-default language. A doc that opens a
section with "the default is X" and then discusses Y throughout is correct, and no
choice of +/-N characters captures that. (Same lesson as the citation checker's
equation-span anchor.)

Scope: flags an unflagged non-default reference. It does not decide whether the
surrounding claim is true of that realization.

Extraction and the existence oracle live in `magpie_corpus` (2026-08-01
consolidation). The default-establishing LANGUAGE below stays here: it is this
predicate's judgment, not shared extraction.

Usage
-----
  python3 check_default_realization.py --selftest
  python3 check_default_realization.py --docs 'magpie-agent/modules/*.md' --root .
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magpie_corpus import (  # noqa: E402
    RE_DATED_REALIZATION,
    RE_REAL_PATH,
    Tree,
)

RE_HEADING = re.compile(r"^#{1,6}\s", re.MULTILINE)

# Language that establishes the default/non-default distinction.
#
# `default` is NOT matched when it is immediately followed by `/` -- module 73's
# realization is literally named `default`, so `73_timber/default/equations.gms`
# would otherwise read as default-establishing language and excuse the reference.
RE_QUALIFIER = re.compile(
    r"(?i)\b(default(?!/)|non-default|not the default|alternative realization|"
    r"alternative realisation|if you (?:run|use)|when configured|realization comparison)\b"
)

# How close the module's default NAME must sit to default-establishing language
# for the pair to count as "this section says which realization is configured".
ESTABLISH_WINDOW = 120

# An explicit flag immediately before the reference itself.
RE_EXPLICIT_FLAG = re.compile(
    r"(?i)(non-default|not the default|alternative realis[az]ation|rather than the default)"
)


def _sections(text: str) -> list[tuple[int, int]]:
    """(start, end) offsets of markdown sections; whole doc if it has no headings."""
    starts = [m.start() for m in RE_HEADING.finditer(text)]
    if not starts:
        return [(0, len(text))]
    if starts[0] != 0:
        starts = [0] + starts
    return [(s, starts[i + 1] if i + 1 < len(starts) else len(text))
            for i, s in enumerate(starts)]


def check_text(text: str, d: Tree) -> list[dict]:
    secs = _sections(text)

    def section_of(pos: int) -> str:
        for s, e in secs:
            if s <= pos < e:
                return text[s:e]
        return text

    seen: set[tuple[str, str]] = set()
    out: list[dict] = []

    # Candidates: path-form references, plus bare dated realization names whose
    # owning module is unambiguous.
    cands: list[tuple[int, str, str]] = [
        (m.start(), m.group(1), m.group(2)) for m in RE_REAL_PATH.finditer(text)
    ]
    for m in RE_DATED_REALIZATION.finditer(text):
        name = m.group(1)
        mod = d.unique_owner.get(name)
        if mod:
            cands.append((m.start(), mod, name))
    cands.sort()

    for pos, mod, real in cands:
        if not d.is_realization_of(mod, real):
            continue
        dflt = d.default_of(mod)
        if dflt is None or real == dflt:
            continue
        if (mod, real) in seen:
            continue
        sec = section_of(pos)

        # Suppression requires the section to ESTABLISH which realization is
        # configured -- not merely to mention the default's name somewhere.
        #
        # Measured 2026-08-01: answers that list `flexreg_apr16` and
        # `flexcluster_jul23` side by side, never saying which is configured, were
        # being excused by a bare name test. That was 3 of the 5 recall misses.
        # So the default NAME must co-occur with default-establishing LANGUAGE.
        #
        # The name matches on IDENTIFIER boundaries, not as a substring: module
        # 80's default `nlp_apr17` is a substring of the non-default
        # `lp_nlp_apr17`, so a plain containment test excuses exactly the
        # reference this checker exists to catch. (`magpie_corpus --selftest`
        # asserts that hazard is still live in the tree.)
        name_re = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(dflt)}(?![A-Za-z0-9_])")
        establishes = any(
            name_re.search(sec[max(0, q.start() - ESTABLISH_WINDOW): q.end() + ESTABLISH_WINDOW])
            for q in RE_QUALIFIER.finditer(sec)
        )
        # ...or the reference itself is explicitly flagged as non-default.
        flagged = bool(RE_EXPLICIT_FLAG.search(text[max(0, pos - 160): pos + 160]))
        if establishes or flagged:
            continue
        seen.add((mod, real))
        out.append({
            "kind": "nondefault_realization_unflagged",
            "module": mod, "cited_realization": real, "default": dflt,
            "line": text.count("\n", 0, pos) + 1,
            "context": text[max(0, pos - 90): pos + 90].replace("\n", " ").strip()[:200],
        })
    return out


# --------------------------------------------------------------------------
# Self-test. Ground truth read from the tree: 18_residues default is
# flexreg_apr16, flexcluster_jul23 is the alternative; 80_optimization default
# is nlp_apr17, lp_nlp_apr17 is not.
# --------------------------------------------------------------------------

POSITIVES = [
    ("non-default realization cited bare",
     "## Consumers\n\nModule 18 reads cell-level `vm_prod` at "
     "`modules/18_residues/flexcluster_jul23/equations.gms:18`.\n"),
    ("non-default M80 realization cited bare",
     "## Solver\n\nThe second solve is controlled at "
     "`modules/80_optimization/lp_nlp_apr17/solve.gms:66`.\n"),
    # Both realizations NAMED but neither declared configured -- 3 of the 5
    # recall misses measured on 2026-08-01 had exactly this shape.
    ("both realizations named, neither established as the default",
     "## Consumers\n\nModule 18 has two realizations, `flexreg_apr16` and "
     "`flexcluster_jul23`. The latter reads cell-level `vm_prod` at "
     "`modules/18_residues/flexcluster_jul23/equations.gms:18`.\n"),
    # `default` as a PATH SEGMENT (module 73's realization is named `default`)
    # must not read as default-establishing language.
    ("the word 'default' inside a path does not establish anything",
     "## Consumers\n\nTimber cost is at `modules/73_timber/default/equations.gms:26`, "
     "and residues at `modules/18_residues/flexcluster_jul23/equations.gms:18`.\n"),
]

NEGATIVES = [
    ("the DEFAULT realization is never flagged",
     "## Consumers\n\nModule 18 reads `vm_prod_reg` at "
     "`modules/18_residues/flexreg_apr16/equations.gms:18`.\n"),
    ("section names the default explicitly",
     "## Consumers\n\nThe default realization is `flexreg_apr16`, which reads regional "
     "production. The alternative `modules/18_residues/flexcluster_jul23/equations.gms:18` "
     "reads cell-level `vm_prod`.\n"),
    ("section uses non-default language",
     "## Consumers\n\nIn the non-default configuration, "
     "`modules/18_residues/flexcluster_jul23/equations.gms:18` reads cell-level `vm_prod`.\n"),
    ("a non-realization subdirectory is not a realization",
     "## Inputs\n\nSee `modules/18_residues/input/` for the source files.\n"),
    ("qualifier in the SAME section but a later paragraph still suppresses",
     "## Consumers\n\n`modules/18_residues/flexcluster_jul23/equations.gms:18` reads "
     "cell-level `vm_prod`.\n\nNote this is not the default realization.\n"),
]


def selftest(d: Tree) -> int:
    bad = 0
    print("== POSITIVE controls (must flag) ==")
    for name, text in POSITIVES:
        got = check_text(text, d)
        print(f"  [{'PASS' if got else 'FAIL'}] {name}")
        if not got:
            bad += 1
    print("== NEGATIVE controls (must be clean) ==")
    for name, text in NEGATIVES:
        got = check_text(text, d)
        print(f"  [{'PASS' if not got else 'FAIL'}] {name}")
        if got:
            bad += 1
            print(f"        false positives: {got}")
    print(f"\nself-test: {bad} failure(s)")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--docs", action="append", help="glob of docs to scan (repeatable)")
    ap.add_argument("--json")
    a = ap.parse_args()

    d = Tree(Path(a.root).resolve())
    print(f"defaults resolved for {len(d.defaults_by_module)}/{len(d.module_dirs)} modules",
          file=sys.stderr)
    if a.selftest:
        return 1 if selftest(d) else 0
    if not a.docs:
        ap.error("need --docs or --selftest")

    files = sorted({f for g in a.docs for f in globmod.glob(g)})
    res = {}
    for f in files:
        fs = check_text(Path(f).read_text(errors="ignore"), d)
        if fs:
            res[f] = fs
    n = sum(len(v) for v in res.values())
    print(f"{n} unflagged non-default realization references over {len(res)}/{len(files)} docs")
    for f, fs in sorted(res.items()):
        for x in fs:
            print(f"  {f}:{x['line']}  {x['module']}  cites {x['cited_realization']} "
                  f"(default {x['default']})")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
