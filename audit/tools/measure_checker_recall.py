#!/usr/bin/env python3
"""Measure RECALL of the citation checker by mutating real, correct citations.

Why this exists
---------------
The 2026-08-01 precision census raised `check_citation_content` precision by
fixing four extraction defects. Every one of those fixes REDUCED the finding
count, and nothing in that pass measured the other direction. A checker tuned
only against false positives converges on the empty set, which scores 100%
precision and is useless.

So: how many real defects does it MISS?

Method, and why this shape
--------------------------
Seeds are **mutations of citations that already exist and are already correct**,
in their own real prose context -- not synthetic sentences. That matters more
than it sounds: if the seeds were hand-written they would inherit the shapes I
already had in mind, which are exactly the shapes the checker's own positive
controls cover. Mutating the live corpus makes the seed distribution match the
real one by construction.

  1. find citations the checker currently does NOT flag, where the claimed
     identifier verifiably sits on the cited line;
  2. shift the line number by a controlled delta;
  3. VERIFY the mutant is a genuine defect -- the identifier must not appear at
     the new line, and no equation/set span may legitimately cover it. A mutant
     that is still correct is discarded, not counted as a miss;
  4. re-run the checker on that one doc and ask whether THAT citation is flagged.

Recall is reported per delta bucket, because the checker's classes are defined by
offset size and a single pooled number would hide the shape.

Harness control
---------------
`--delta 0` runs the whole pipeline with no mutation and must detect ~nothing. A
recall harness that flags unmutated text is measuring itself, not the checker.

Usage
-----
  python3 measure_checker_recall.py --root <magpie-root> --docs '<agent>/modules/*.md'
  python3 measure_checker_recall.py --root . --docs '...' --deltas 1,2,3,10,40 --n 40
"""

from __future__ import annotations

import argparse
import glob as globmod
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_citation_content import (  # noqa: E402
    LOOKBEHIND, RE_CLAIMED, _claimed_identifiers, _parse_lines, check_text,
)
from magpie_corpus import (  # noqa: E402
    RE_CITATION, Tree, is_filename, is_glob_stem,
)


def find_correct_citations(text: str, tree: Tree) -> list[dict]:
    """Single-line citations where a claimed identifier really is on that line."""
    flagged = {(f["path"], f["cited"]) for f in check_text(text, tree)}
    out: list[dict] = []
    for m in RE_CITATION.finditer(text):
        rel, spec = m.group(1), m.group(2)
        if not re.fullmatch(r"\d+", spec):
            continue                       # ranges have no single line to shift
        if (rel, spec) in flagged:
            continue                       # already a finding; not a clean base
        lines = tree.lines(rel)
        if lines is None:
            continue
        line = int(spec)
        if not (1 <= line <= len(lines)):
            continue
        claimed, _ = _claimed_identifiers(text, m.start(), tree.dir_names, rel)
        if not claimed:
            continue
        hit = [t for t in claimed if t in lines[line - 1]]
        if not hit:
            continue                       # correct for a reason we cannot pin down
        out.append({"pos": m.start(), "path": rel, "line": line,
                    "claimed": claimed, "anchor": hit})
    return out


def is_genuine_defect(tree: Tree, base: dict, new_line: int) -> bool:
    """Would a reader at `new_line` fail to find what the citation is cited for?"""
    lines = tree.lines(base["path"]) or []
    if not (1 <= new_line <= len(lines)):
        return True                        # past EOF is certainly wrong
    # Still correct if any claimed identifier appears at the new line...
    if any(t in lines[new_line - 1] for t in base["claimed"]):
        return False
    # ...or if a structural anchor legitimately covers it.
    spans = {**tree.equation_spans(base["path"]), **tree.set_spans(base["path"])}
    return not any(
        t in spans and spans[t][0] <= new_line <= spans[t][1] for t in base["claimed"]
    )


def mutate(text: str, base: dict, new_line: int) -> str:
    old = f"{base['path']}:{base['line']}"
    pos = base["pos"]
    if not text.startswith(old, pos):
        return text
    return text[:pos] + f"{base['path']}:{new_line}" + text[pos + len(old):]


def coverage(corpus: dict[str, str], tree: Tree) -> dict[str, int]:
    """How many citations the checker actually EVALUATES, and why it skips the rest.

    Recall measured on the evaluated subset is not recall over the corpus. The
    checker declines any citation with no claimed identifier next to it -- and
    that exit is silent, so without this the skipped population is invisible and
    a high recall number reads as broader than it is.
    """
    c = defaultdict(int)
    for txt in corpus.values():
        for m in RE_CITATION.finditer(txt):
            c["citations_total"] += 1
            rel = m.group(1)
            if tree.lines(rel) is None:
                c["skipped_unresolvable_path"] += 1
                continue
            claimed, _ = _claimed_identifiers(txt, m.start(), tree.dir_names, rel)
            if not claimed:
                c["skipped_no_claimed_identifier"] += 1
                continue
            c["evaluated"] += 1
            if re.fullmatch(r"\d+", m.group(2)):
                c["evaluated_single_line"] += 1
            else:
                c["evaluated_range_or_list"] += 1
    return dict(c)


RE_BOLD_LABEL = re.compile(r"\*\*[^*]{2,40}\*\*\s*[:(]?\s*$")


def classify_skipped(corpus: dict[str, str], tree: Tree) -> dict[str, int]:
    """Why the checker declines 56% of citations, and how much is recoverable.

    The skipped population is the largest known gap. Widening the lookbehind is
    the obvious fix and also the exact move that caused the bullet-inheritance
    false positives, so this measures BEFORE anything changes:

      recoverable_and_correct  a wider window yields an identifier, and it IS at
                               the cited line -> extending only adds confirmations
      recoverable_would_flag   a wider window yields an identifier NOT at the cited
                               line -> extending manufactures findings that would
                               each need adjudication. This is the risky bucket.
      bold_label_only          "**Usage Location**: `path`" -- the subject lives in
                               a heading, not in any window
      nothing_nearby           no identifier-like token at all
    """
    c = defaultdict(int)
    for txt in corpus.values():
        for m in RE_CITATION.finditer(txt):
            rel = m.group(1)
            lines = tree.lines(rel)
            if lines is None:
                continue
            claimed, clause = _claimed_identifiers(txt, m.start(), tree.dir_names, rel)
            if claimed:
                continue
            c["skipped"] += 1
            # What a window that ignored clause boundaries would have found.
            wide_ctx = txt[max(0, m.start() - LOOKBEHIND): m.start()]
            wide = [t for t in RE_CLAIMED.findall(wide_ctx)]
            toks = [(a or b) for a, b in wide]
            toks = [t for t in toks if t and not is_filename(t) and not is_glob_stem(t)
                    and (rel.startswith("config/") or t not in tree.dir_names)]
            if not toks:
                c["bold_label_only" if RE_BOLD_LABEL.search(clause.rstrip())
                  else "nothing_nearby"] += 1
                continue
            cited = _parse_lines(m.group(2))
            on_line = any(t in lines[i - 1] for i in cited
                          if 1 <= i <= len(lines) for t in toks)
            c["recoverable_and_correct" if on_line else "recoverable_would_flag"] += 1
    return dict(c)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--docs", action="append", required=True)
    ap.add_argument("--classify-skipped", action="store_true",
                    help="report the composition of the skipped population and exit")
    ap.add_argument("--deltas", default="1,2,3,5,15,50,99999",
                    help="line offsets to seed; 99999 forces past-EOF")
    ap.add_argument("--n", type=int, default=40, help="seeds per delta")
    ap.add_argument("--seed", type=int, default=20260801)
    a = ap.parse_args()

    tree = Tree(Path(a.root).resolve())
    files = sorted({f for g in a.docs for f in globmod.glob(g)})
    corpus = {f: Path(f).read_text(errors="ignore") for f in files}

    cov = coverage(corpus, tree)
    tot = cov.get("citations_total", 0)
    print("\n=== COVERAGE: what fraction of citations the checker EVALUATES ===")
    for k in ("citations_total", "evaluated", "evaluated_single_line",
              "evaluated_range_or_list", "skipped_no_claimed_identifier",
              "skipped_unresolvable_path"):
        v = cov.get(k, 0)
        pct = f"{v / tot:5.1%}" if tot else "  n/a"
        print(f"  {k:<32} {v:>5}  {pct}")
    print("  NOTE: recall below is measured ON THE EVALUATED SUBSET. Multiply by the")
    print("        evaluated fraction for effective corpus coverage.")

    if a.classify_skipped:
        cls = classify_skipped(corpus, tree)
        tot_s = cls.get("skipped", 0)
        print("\n=== COMPOSITION of the SKIPPED population ===")
        for k in ("skipped", "recoverable_and_correct", "recoverable_would_flag",
                  "bold_label_only", "nothing_nearby"):
            v = cls.get(k, 0)
            pct = f"{v / tot_s:5.1%}" if tot_s else "  n/a"
            print(f"  {k:<28} {v:>5}  {pct}")
        return 0

    bases: list[tuple[str, dict]] = []
    for f, txt in corpus.items():
        for b in find_correct_citations(txt, tree):
            bases.append((f, b))
    print(f"{len(bases)} correct single-line citations available as seed bases "
          f"across {len(files)} docs", file=sys.stderr)
    if not bases:
        print("no seed bases -- cannot measure recall", file=sys.stderr)
        return 1

    rng = random.Random(a.seed)
    deltas = [int(x) for x in a.deltas.split(",")]
    results: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    missed: list[str] = []

    for d in deltas:
        pool = bases[:]
        rng.shuffle(pool)
        taken = 0
        for f, b in pool:
            if taken >= a.n:
                break
            new_line = b["line"] + d
            if new_line == b["line"]:
                # delta 0: the harness control. Run it unmutated.
                new_line = b["line"]
            elif not is_genuine_defect(tree, b, new_line):
                results[d]["discarded_still_correct"] += 1
                continue
            mutated = mutate(corpus[f], b, new_line)
            if d != 0 and mutated == corpus[f]:
                results[d]["discarded_unmutated"] += 1
                continue
            found = {(x["path"], x["cited"]) for x in check_text(mutated, tree)}
            hit = (b["path"], str(new_line)) in found
            results[d]["seeded"] += 1
            results[d]["caught" if hit else "missed"] += 1
            if not hit and len(missed) < 12:
                missed.append(f"delta {d:+6d}  {Path(f).name}  {b['path']}:{b['line']}"
                              f"->{new_line}  claimed={b['claimed'][:3]}")
            taken += 1

    print(f"\n{'delta':>8}  {'seeded':>7} {'caught':>7} {'missed':>7}  {'recall':>7}   discarded")
    for d in deltas:
        r = results[d]
        s, c = r["seeded"], r["caught"]
        rec = f"{c / s:.0%}" if s else "n/a"
        disc = r["discarded_still_correct"] + r["discarded_unmutated"]
        if d == 0:
            # The control INVERTS: catching an unmutated citation would mean the
            # harness flags correct text, so 0 caught is the PASS.
            verdict = "PASS" if c == 0 else "FAIL"
            print(f"{d:>8}  {s:>7} {c:>7} {r['missed']:>7}  {'--':>7}   {disc}"
                  f"  <- HARNESS CONTROL: {verdict} (0 caught is correct)")
            continue
        print(f"{d:>8}  {s:>7} {c:>7} {r['missed']:>7}  {rec:>7}   {disc}")

    tot_s = sum(results[d]["seeded"] for d in deltas if d != 0)
    tot_c = sum(results[d]["caught"] for d in deltas if d != 0)
    if tot_s:
        print(f"\npooled recall (excluding the delta-0 control): {tot_c}/{tot_s} = "
              f"{tot_c / tot_s:.0%}")
    if missed:
        print("\nsample of MISSED seeds (what the checker does not see):")
        for m in missed:
            print("   " + m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
