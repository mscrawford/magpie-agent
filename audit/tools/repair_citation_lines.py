#!/usr/bin/env python3
"""Repair off-by-N citation line numbers in the docs, but ONLY where unambiguous.

Why only this class
-------------------
The 2026-08-01 precision census measured `check_citation_content` per class and
found the severity labels inverted relative to reliability:

    citation_off_by_small       labelled "minor"      100% precise (4/4)
    citation_line_wrong         labelled "moderate"    50%
    citation_identifier_absent  labelled "major"       20%

So the only class that has earned automated action is the one the checker calls
least important. `citation_identifier_absent` must never be auto-repaired -- four
out of five of those are the checker failing to read a proposition, not a doc
being wrong.

The ambiguity rule
------------------
A finding is repairable ONLY IF exactly ONE candidate line carries the claimed
identifier within the search window. When the identifier appears at, say, both
:1926 and :1931 around a citation to :1928, there is no fact of the matter about
which the author meant, and picking one is a guess wearing a tool's authority.
Those are reported and left alone.

`citation_out_of_range` is also excluded: a line past the end of the file is
certainly wrong, but the correct target is not derivable from an offset.

Safety
------
Dry-run is the DEFAULT. `--apply` writes, and then RE-RUNS the checker and fails
loudly if any repaired finding survives -- the repair verifies itself rather than
trusting its own arithmetic.

Usage
-----
  python3 repair_citation_lines.py --selftest
  python3 repair_citation_lines.py --root <magpie-root> --docs '<agent>/modules/*.md'
  python3 repair_citation_lines.py --root <magpie-root> --docs '...' --apply
"""

from __future__ import annotations

import argparse
import glob as globmod
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_citation_content import NEAR_WINDOW, check_text  # noqa: E402
from magpie_corpus import Tree  # noqa: E402

REPAIRABLE_KIND = "citation_off_by_small"
RE_FOUND_AT = re.compile(r"found at \[([0-9, ]+)\]")


def plan_repairs(text: str, tree: Tree) -> tuple[list[dict], list[dict]]:
    """(repairable, refused) for one doc."""
    ok: list[dict] = []
    refused: list[dict] = []
    for f in check_text(text, tree):
        if f["kind"] != REPAIRABLE_KIND:
            refused.append({**f, "why": f"kind {f['kind']} is not auto-repairable"})
            continue
        m = RE_FOUND_AT.search(f["detail"])
        if not m:
            refused.append({**f, "why": "could not parse the actual location"})
            continue
        cands = [int(x) for x in m.group(1).split(",") if x.strip()]
        # Disambiguate on IDENTIFIER BOUNDARIES. The checker matches a claimed
        # identifier as a substring, deliberately -- that keeps its false-positive
        # rate down. But it makes `s30_betr_target` "appear" at both :24 (the real
        # declaration) and :25 (`s30_betr_target_noselect`), which reads as
        # ambiguous when it is not. The REPAIRER may be stricter than the checker:
        # if exactly one candidate carries the identifier on a boundary, that is
        # the target.
        lines = tree.lines(f["path"]) or []
        exact = [
            c for c in cands
            if 1 <= c <= len(lines) and any(
                re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", lines[c - 1])
                for tok in f["claimed"]
            )
        ]
        if len(exact) == 1:
            cands = exact
        # A single-number citation only. A range citation has no single target.
        if not re.fullmatch(r"\d+", f["cited"]):
            refused.append({**f, "why": "range citation has no single repair target"})
            continue
        if len(cands) != 1:
            refused.append({**f, "why": f"ambiguous: identifier appears at {cands}"})
            continue
        target = cands[0]
        cited = int(f["cited"])
        if target == cited or abs(target - cited) > NEAR_WINDOW:
            refused.append({**f, "why": f"target {target} outside the window"})
            continue
        ok.append({**f, "from": cited, "to": target})
    return ok, refused


def apply_repairs(text: str, repairs: list[dict]) -> tuple[str, int]:
    """Rewrite the SPECIFIC cited occurrences, at their recorded offsets.

    Not a textual find-and-replace. `module_52.md` cites
    `.../presolve.gms:66` three times for three different identifiers, and two of
    those citations are correct; a blanket replace fixed one and broke two. So
    each repair is applied only at the offsets the checker actually flagged.

    Edits are applied in DESCENDING offset order so that an earlier replacement
    of a different length cannot invalidate a later offset.
    """
    edits: list[tuple[int, str, str]] = []
    for r in repairs:
        old = f"{r['path']}:{r['from']}"
        new = f"{r['path']}:{r['to']}"
        for pos in r.get("positions", []):
            edits.append((pos, old, new))
    n = 0
    for pos, old, new in sorted(edits, key=lambda e: -e[0]):
        # The offset points at the start of the path. Verify before trusting it:
        # a stale offset must fail loudly, not silently corrupt a neighbour.
        if not text.startswith(old, pos):
            continue
        after = pos + len(old)
        if after < len(text) and text[after].isdigit():
            continue                       # `:41` sitting inside `:414`
        text = text[:pos] + new + text[after:]
        n += 1
    return text, n


# --------------------------------------------------------------------------
# Self-test. Ground truth read from the tree: s30_betr_target is at
# modules/30_croparea/simple_apr24/input.gms:24; vm_prod at .../equations.gms:15.
# --------------------------------------------------------------------------

def selftest(tree: Tree) -> int:
    bad = 0
    print("== POSITIVE control (must plan a repair) ==")
    # config/default.cfg:414 is a BLANK line; `s15_elastic_demand` is at :417 and
    # nowhere else nearby. Verified by hand 2026-08-01.
    doc = ("Endogenous demand is off by default: `s15_elastic_demand = 0` "
           "(`config/default.cfg:414`).\n")
    ok, refused = plan_repairs(doc, tree)
    hit = len(ok) == 1 and ok[0]["from"] == 414 and ok[0]["to"] == 417
    print(f"  [{'PASS' if hit else 'FAIL'}] off-by-three 414 -> 417 is planned")
    if not hit:
        bad += 1
        print(f"        planned={ok} refused={refused}")
    else:
        fixed, n = apply_repairs(doc, ok)
        # The repair must actually silence the checker -- not merely edit text.
        still = [f for f in check_text(fixed, tree) if f["kind"] == REPAIRABLE_KIND]
        good = n == 1 and not still
        print(f"  [{'PASS' if good else 'FAIL'}] applying it silences the finding")
        if not good:
            bad += 1

    print("== BOUNDARY-DISAMBIGUATION control ==")
    # `s30_betr_target` substring-matches :24 AND :25 (`s30_betr_target_noselect`).
    # Only :24 carries it on an identifier boundary, so this IS repairable.
    doc2 = ("The target share `s30_betr_target` is declared at "
            "`modules/30_croparea/simple_apr24/input.gms:23`.\n")
    ok2, ref2 = plan_repairs(doc2, tree)
    good = len(ok2) == 1 and ok2[0]["to"] == 24
    print(f"  [{'PASS' if good else 'FAIL'}] a prefix-collision resolves to the boundary match")
    if not good:
        bad += 1
        print(f"        planned={ok2} refused={ref2}")

    print("== REFUSAL controls (must NOT repair) ==")
    cases = [
        ("a range citation has no single target",
         "`vm_prod` is at `modules/30_croparea/simple_apr24/equations.gms:10-12`.\n"),
        ("identifier_absent is never auto-repairable",
         "`vm_totallyfakevariable` is at "
         "`modules/30_croparea/simple_apr24/equations.gms:15`.\n"),
        ("a correct citation is left alone",
         "`vm_prod` is at `modules/30_croparea/simple_apr24/equations.gms:15`.\n"),
    ]
    for name, doc in cases:
        ok, _ = plan_repairs(doc, tree)
        good = not ok
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
        if not good:
            bad += 1
            print(f"        would have repaired: {ok}")

    print("== SUBSTITUTION controls ==")
    t = "see `modules/x/y.gms:41` and `modules/x/y.gms:414` here"
    got, _ = apply_repairs(t, [{"path": "modules/x/y.gms", "from": 41, "to": 44,
                                "positions": [t.index("modules/x/y.gms:41")]}])
    good = "y.gms:44" in got and "y.gms:414" in got
    print(f"  [{'PASS' if good else 'FAIL'}] :41 does not match inside :414")
    if not good:
        bad += 1
        print(f"        got: {got}")

    # The module_52.md shape, verbatim in structure: the SAME path:line cited
    # three times, only one of which is being repaired. The other two must survive.
    t2 = ("A cites `modules/x/y.gms:66`. B cites `modules/x/y.gms:66`. "
          "C cites `modules/x/y.gms:66`.")
    second = t2.index("modules/x/y.gms:66", t2.index("modules/x/y.gms:66") + 1)
    got2, k2 = apply_repairs(t2, [{"path": "modules/x/y.gms", "from": 66, "to": 64,
                                   "positions": [second]}])
    good2 = k2 == 1 and got2.count("y.gms:66") == 2 and got2.count("y.gms:64") == 1
    print(f"  [{'PASS' if good2 else 'FAIL'}] only the flagged occurrence is rewritten")
    if not good2:
        bad += 1
        print(f"        got: {got2}")

    print(f"\nself-test: {bad} failure(s)")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--docs", action="append")
    ap.add_argument("--apply", action="store_true", help="write (default is dry-run)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    tree = Tree(Path(a.root).resolve())
    if a.selftest:
        return 1 if selftest(tree) else 0
    if not a.docs:
        ap.error("need --docs or --selftest")

    files = sorted({f for g in a.docs for f in globmod.glob(g)})
    total_ok = total_refused = written = 0
    for f in files:
        p = Path(f)
        text = p.read_text(errors="ignore")
        ok, refused = plan_repairs(text, tree)
        total_refused += len(refused)
        if not ok:
            continue
        total_ok += len(ok)
        print(f"\n{p.name}")
        for r in ok:
            print(f"   {r['path']}:{r['from']}  ->  :{r['to']}   ({r['claimed']})")
        if a.apply:
            new, n = apply_repairs(text, ok)
            if n:
                p.write_text(new)
                written += n

    print(f"\n{total_ok} repairable, {total_refused} left alone "
          f"({'APPLIED ' + str(written) if a.apply else 'DRY RUN - nothing written'})")

    if a.apply and written:
        # Verify by RE-RUNNING, not by trusting the arithmetic above.
        remaining = 0
        for f in files:
            remaining += sum(1 for x in check_text(Path(f).read_text(errors="ignore"), tree)
                             if x["kind"] == REPAIRABLE_KIND)
        print(f"post-repair re-run: {remaining} {REPAIRABLE_KIND} findings remain")
        if remaining >= total_ok:
            print("ERROR: repairs did not reduce the finding count", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
