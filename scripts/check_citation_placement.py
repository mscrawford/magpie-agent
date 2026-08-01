#!/usr/bin/env python3
"""Gate/benchmark wrapper: does a cited `file:line` contain what it is cited for?

The predicate lives in `audit/tools/check_citation_content.py`, which takes
`--root` and `--docs`. This wrapper exists so the checker can be invoked the way
`scripts/check_*.py` checkers are -- no arguments, paths resolved from the tree it
is sitting in -- which is what `audit/tools/seed_known_bugs.py` requires to
include it in the seeded-bug benchmark.

Without this, the two 2026-08-01 citation-drift seed commits would have been
scored as MISSES by a battery that simply never ran the checker able to see them:
a blind spot that is an artifact of the harness, and flattering in the wrong
direction. `seed_known_bugs.py` has a vacuity guard for a checker absent from the
worktree; it has none for a checker that was never listed.

The GAMS root comes from `MAGPIE_DIR` when set (the benchmark runs the docs from a
scratch worktree while the GAMS tree stays at its real location), otherwise from
the parent of the agent directory.

Output is one line per finding, with DOC-RELATIVE paths.
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_DIR / "audit" / "tools"))

from check_citation_content import ACTIONABLE, CERTAIN, check_text  # noqa: E402
from magpie_corpus import Tree  # noqa: E402


def main() -> int:
    root = Path(os.environ.get("MAGPIE_DIR") or AGENT_DIR.parent)
    if not (root / "modules").is_dir():
        # A missing GAMS tree must not read as "no findings". Same rule as the
        # session-startup guard: an ERROR is not a WARNING.
        print(f"ERROR: no modules/ under {root} - cannot resolve citations", file=sys.stderr)
        return 2

    tree = Tree(root)
    docs = sorted(
        {f for sub in ("modules", "cross_module", "core_docs")
         for f in glob.glob(str(AGENT_DIR / sub / "*.md"))}
    )
    total = actionable = certain = 0
    for f in docs:
        rel = str(Path(f).relative_to(AGENT_DIR))
        for x in check_text(Path(f).read_text(errors="ignore"), tree):
            total += 1
            actionable += x["kind"] in ACTIONABLE
            certain += x["kind"] in CERTAIN
            print(f"  {rel}  {x['kind']:<28} {x['path']}:{x['cited']}  {x['detail']}")
    print(f"SUMMARY docs={len(docs)} findings={total} certain={certain} "
          f"actionable={actionable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
