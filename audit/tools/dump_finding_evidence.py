#!/usr/bin/env python3
"""Dump the evidence needed to adjudicate each checker finding, one block per finding.

Why a tool rather than 70 ad-hoc greps
--------------------------------------
Precision is the gate on every rate this project quotes, and the standing rule is
that a quoted figure must have a persisted, re-runnable artifact behind it -- a
number computed in a throwaway shell is an anecdote. Adjudicating 70 findings by
hand, one grep at a time, is also exactly the regime where "plausible but wrong"
creeps in: by finding 40 the reader is pattern-matching, not reading.

So this extracts the same evidence for every finding, in the same shape, and the
human verdict is recorded against a stable finding id. Re-running it after a
checker change shows which findings moved.

It renders NO verdict. It only assembles: the citing sentence, the cited lines as
they actually are on disk, and where the claimed identifiers really occur.

Usage
-----
  python3 dump_finding_evidence.py --root <magpie-root> --batch <batch.md> \
      --citations <cite.json> [--defaults <dflt.json>] [--out evidence.txt]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magpie_corpus import Tree, split_batch  # noqa: E402

CONTEXT_CHARS = 320


def _citing_context(answer: str, path: str, spec: str) -> str:
    """The sentence in the answer that carries this citation."""
    needle = f"{path}:{spec}"
    i = answer.find(needle)
    if i == -1:
        i = answer.find(path)
    if i == -1:
        return "<citation not located in answer text>"
    lo = max(0, i - CONTEXT_CHARS)
    hi = min(len(answer), i + len(needle) + 80)
    return "..." + answer[lo:hi].replace("\n", " ").strip() + "..."


def _parse_lines(spec: str) -> list[int]:
    import re
    nums = [int(x) for x in re.findall(r"\d+", spec)]
    if "-" in spec and len(nums) == 2:
        lo, hi = sorted(nums)
        if hi - lo <= 60:
            return list(range(lo, hi + 1))
    return nums


def dump_citations(res: dict, answers: dict, tree: Tree, out) -> int:
    n = 0
    for label in sorted(res):
        for f in res[label]:
            n += 1
            fid = f"CIT-{n:03d}"
            path, spec = f["path"], f["cited"]
            claimed = f.get("claimed", [])
            lines = tree.lines(path) or []
            cited = _parse_lines(spec)

            print(f"\n{'=' * 78}", file=out)
            print(f"{fid}  [{f['kind']}]  {label}", file=out)
            print(f"  cited      : {path}:{spec}", file=out)
            print(f"  claimed    : {claimed}", file=out)
            print(f"  checker say: {f['detail']}", file=out)
            print(f"  in answer  : {_citing_context(answers.get(label, ''), path, spec)}", file=out)
            print(f"  --- cited lines as they are on disk ({len(lines)} total) ---", file=out)
            shown = [c for c in cited if 1 <= c <= len(lines)]
            for c in shown[:12]:
                print(f"    {c:>5}| {lines[c - 1].rstrip()[:110]}", file=out)
            if not shown:
                print("    <cited line(s) past end of file>", file=out)
            print("  --- where each claimed identifier ACTUALLY occurs ---", file=out)
            for tok in claimed:
                hits = [i for i, ln in enumerate(lines, 1) if tok in ln]
                if hits:
                    print(f"    {tok:<28} lines {hits[:10]}"
                          f"{' ...' if len(hits) > 10 else ''}", file=out)
                    for h in hits[:2]:
                        print(f"        {h:>5}| {lines[h - 1].rstrip()[:100]}", file=out)
                else:
                    print(f"    {tok:<28} ABSENT from this file", file=out)
    return n


def dump_defaults(res: dict, tree: Tree, out) -> int:
    n = 0
    for doc in sorted(res):
        for f in res[doc]:
            n += 1
            fid = f"DEF-{n:03d}"
            mod, real, dflt = f["module"], f["cited_realization"], f["default"]
            print(f"\n{'=' * 78}", file=out)
            print(f"{fid}  [{f['kind']}]  {Path(doc).name}:{f['line']}", file=out)
            print(f"  module     : {mod}", file=out)
            print(f"  cites      : {real}", file=out)
            print(f"  default is : {dflt}", file=out)
            print(f"  all reals  : {sorted(tree.realizations_by_module.get(mod, []))}", file=out)
            print(f"  context    : ...{f['context']}...", file=out)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--batch")
    ap.add_argument("--citations")
    ap.add_argument("--defaults")
    ap.add_argument("--out")
    a = ap.parse_args()

    tree = Tree(Path(a.root).resolve())
    answers = split_batch(Path(a.batch)) if a.batch else {}
    out = open(a.out, "w") if a.out else sys.stdout
    nc = nd = 0
    if a.citations:
        print("#" * 78, file=out)
        print("# CITATION FINDINGS", file=out)
        print("#" * 78, file=out)
        nc = dump_citations(json.load(open(a.citations)), answers, tree, out)
    if a.defaults:
        print("\n" + "#" * 78, file=out)
        print("# NON-DEFAULT REALIZATION FINDINGS", file=out)
        print("#" * 78, file=out)
        nd = dump_defaults(json.load(open(a.defaults)), tree, out)
    if a.out:
        out.close()
    print(f"dumped {nc} citation + {nd} default-realization findings", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
