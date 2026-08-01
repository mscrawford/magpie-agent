#!/usr/bin/env python3
"""A bare `file.gms:N` in a passage about a NON-DEFAULT realization.

The defect
----------
In a module doc, a bare basename citation reads as the module's DEFAULT
realization -- that is the convention `AGENT.md` Step 1c establishes, and module
docs reinforce it by declaring the default up front. So when a passage discusses a
non-default realization and cites bare, a reader who follows the convention opens
the wrong file and finds different code at that line.

It is not "ambiguous". It is **actively misleading**, and it points the reader at
the realization they are most likely to be running.

    **magpie.solprint** = 0 (normal), = 1 (if infeasible) (solve.gms:16, 174)

`solve.gms:16` is `magpie.optfile = s80_optfile;` in the default `nlp_apr17` and
`magpie.solprint = 0 ;` in `lp_nlp_apr17`, which is the realization that passage
is actually about. Commit 3620958 fixed exactly this by qualifying the path.

Why the existing checkers miss it
---------------------------------
`check_no_bare_cites` exempts `modules/module_NN.md` on the rationale that
"context is the module itself". That holds for a single-realization module and
fails for the 23 of 46 that have more than one: the module is not enough context,
the realization is. `check_citation_content` never sees it either -- its
`RE_CITATION` only matches paths rooted at `modules|core|config`, so a bare
basename is not missed, it is never matched.

Two predicates that were tried and REJECTED, recorded so they are not retried
-----------------------------------------------------------------------------
1. "Flag every bare cite in a multi-realization module doc" -> 1739 hits. Useless.
2. "...only where the line differs across realizations, unless the enclosing
   section names the default" -> 547 differing, 5 residual, and it scored **0 on
   the seeded bug**. The suppression inherits ancestor sections, and module docs
   declare the default in their preamble, so every section in the document is
   suppressed. Worse, that declaration is precisely what makes a bare cite mean
   the default -- the thing that makes the defect harmful was being used to
   excuse it.

The predicate below inverts that: the doc-level default convention is ASSUMED,
and the flag fires when the local passage contradicts it.

Boundary matching is load-bearing: the default `nlp_apr17` is a substring of the
non-default `lp_nlp_apr17`, so a containment test would read a passage about
`lp_nlp_apr17` as naming the default and suppress the very case this exists for.

Usage
-----
  python3 check_misleading_bare_cite.py --selftest
  python3 check_misleading_bare_cite.py --root <magpie-root> --docs '<agent>/modules/*.md'
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magpie_corpus import Tree  # noqa: E402

RE_BARE = re.compile(r"(?<!\w)(?<![./])(?P<file>\w+\.gms):(?P<line>\d+)")
RE_MODULE_DOC = re.compile(r"module_(\d{2})")

# Chars before the citation searched for a realization name. The passage's
# subject, not the document's.
#
# BACKWARD ONLY, deliberately. A first version also looked 80 chars ahead and
# picked up (a) the heading of the NEXT section, and (b) a contrast clause that
# follows the cite -- "Capital costs (`equations.gms:64-66`); in
# `fbask_jan16_sticky`: investment-based ...", where the bare cite belongs to the
# default and the non-default is named only to contrast with it. A passage's
# subject is established BEFORE its citation, never after. 2 of 7 false positives
# in the 2026-08-01 adjudication of all 19 findings.
WINDOW = 300


def _bounded(name: str) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")


def module_of(doc_name: str, tree: Tree) -> str | None:
    m = RE_MODULE_DOC.search(doc_name)
    if not m:
        return None
    return next((d for d in tree.realizations_by_module if d.startswith(m.group(1) + "_")), None)


def _line(tree: Tree, mod: str, real: str, fname: str, n: int) -> str | None:
    lines = tree.lines(f"modules/{mod}/{real}/{fname}")
    if lines is None or not (1 <= n <= len(lines)):
        return None
    return lines[n - 1].strip()


def check_text(text: str, mod: str, tree: Tree) -> list[dict]:
    dflt = tree.default_of(mod)
    others = sorted(r for r in tree.realizations_by_module.get(mod, ()) if r != dflt)
    if not dflt or not others:
        return []
    dflt_re = _bounded(dflt)
    out: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for m in RE_BARE.finditer(text):
        fname, n = m.group("file"), int(m.group("line"))
        if (fname, n) in seen:
            continue
        ctx = text[max(0, m.start() - WINDOW): m.start()]
        named = [r for r in others if _bounded(r).search(ctx)]
        if not named:
            continue                       # passage is not about a non-default one
        if dflt_re.search(ctx):
            continue                       # passage names the default too; not misleading
        dv = _line(tree, mod, dflt, fname, n)
        for r in named:
            rv = _line(tree, mod, r, fname, n)
            if rv is None or rv == dv:
                continue                   # same content, or absent there: harmless
            seen.add((fname, n))
            out.append({
                "kind": "misleading_bare_cite",
                "cite": f"{fname}:{n}", "passage_realization": r, "default": dflt,
                "line": text.count("\n", 0, m.start()) + 1,
                "in_passage_realization": (rv or "")[:70],
                "in_default": (dv if dv is not None else "<line absent>")[:70],
            })
            break
    return out


# --------------------------------------------------------------------------
# Self-test. Ground truth read from the tree 2026-08-01: module 80's default is
# nlp_apr17; solve.gms:16 is `magpie.optfile = s80_optfile;` there and
# `magpie.solprint  = 0 ;` in lp_nlp_apr17.
# --------------------------------------------------------------------------

POSITIVES = [
    # The shape of the real bug fixed by commit 3620958.
    ("bare cite in a passage about a non-default realization",
     "## Solver\n\nIn the `lp_nlp_apr17` realization the print flag is set "
     "(solve.gms:16).\n", "80_optimization"),
    # This ALSO proves the boundary matching: `nlp_apr17` is a substring of
    # `lp_nlp_apr17`, and a containment test would have read the default as named
    # here and suppressed both of these.
    #
    # Written first as a NEGATIVE control and moved here after it "failed":
    # solve.gms:174 exists ONLY in lp_nlp_apr17, so a reader following the default
    # convention opens nlp_apr17/solve.gms and finds no line 174 at all. Being
    # absent from the default is not an excuse, it is the defect.
    ("cite valid only in the non-default realization (default has no such line)",
     "Only `lp_nlp_apr17` is discussed here (solve.gms:174).\n", "80_optimization"),
]

NEGATIVES = [
    ("qualified path is not a bare cite",
     "In `lp_nlp_apr17` the flag is set "
     "(`modules/80_optimization/lp_nlp_apr17/solve.gms:16`).\n", "80_optimization"),
    ("passage names the DEFAULT, so a bare cite reads correctly",
     "In the `nlp_apr17` realization the optfile is chosen (solve.gms:16).\n",
     "80_optimization"),
    ("passage names no realization at all",
     "The solver options are configured early (solve.gms:16).\n", "80_optimization"),
    # REGRESSION: the non-default is named only to CONTRAST, after the cite. The
    # bare cite belongs to the default and is correct. Backward-only window.
    ("a non-default named AFTER the cite does not claim it",
     "- `q70_cost_prod_liv_capital`: Capital costs (equations.gms:64-66); in "
     "`fbask_jan16_sticky`: investment-based capital costs.\n", "70_livestock"),
    ("identical content across realizations is harmless",
     "In `lp_nlp_apr17` see (realization.gms:1).\n", "80_optimization"),
]


def selftest(tree: Tree) -> int:
    bad = 0
    print("== POSITIVE controls (must flag) ==")
    for name, text, mod in POSITIVES:
        got = check_text(text, mod, tree)
        print(f"  [{'PASS' if got else 'FAIL'}] {name}")
        if not got:
            bad += 1
    print("== NEGATIVE controls (must be clean) ==")
    for name, text, mod in NEGATIVES:
        got = check_text(text, mod, tree)
        ok = not got
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            bad += 1
            print(f"        false positives: {got}")
    # The substring hazard must actually be LIVE in the tree, or the control above
    # passes vacuously.
    live = ("nlp_apr17" in tree.realizations_by_module.get("80_optimization", set())
            and "lp_nlp_apr17" in tree.realizations_by_module.get("80_optimization", set()))
    print(f"  [{'PASS' if live else 'FAIL'}] substring hazard is live in the tree "
          f"(nlp_apr17 vs lp_nlp_apr17)")
    if not live:
        bad += 1
    print(f"\nself-test: {bad} failure(s)")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--docs", action="append")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()

    tree = Tree(Path(a.root).resolve())
    if a.selftest:
        return 1 if selftest(tree) else 0
    if not a.docs:
        ap.error("need --docs or --selftest")

    files = sorted({f for g in a.docs for f in globmod.glob(g)})
    res: dict[str, list[dict]] = {}
    multi = 0
    for f in files:
        mod = module_of(Path(f).name, tree)
        if not mod or len(tree.realizations_by_module.get(mod, ())) < 2:
            continue
        multi += 1
        fs = check_text(Path(f).read_text(errors="ignore"), mod, tree)
        if fs:
            res[f] = fs
    n = sum(len(v) for v in res.values())
    print(f"{n} misleading bare cites over {len(res)}/{multi} multi-realization module docs")
    for f, fs in sorted(res.items()):
        for x in fs:
            print(f"  {Path(f).name}:{x['line']}  {x['cite']:<22} passage={x['passage_realization']} "
                  f"(default {x['default']})")
    print(f"SUMMARY multi_realization_docs={multi} findings={n}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
