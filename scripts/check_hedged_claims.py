#!/usr/bin/env python3
"""check_hedged_claims.py - ADVISORY: flag hedged-as-fact claims in load-bearing context.

Motivation: module_40.md carried "**Usage in Module 11** (inferred from standard MAgPIE
cost structure): `sum(j2, vm_cost_transp(j2,k))`" - an explicitly INFERRED (and wrong)
formula later cited as fact. ~200 hedge markers exist across the module docs, but only the
subset sitting ON A LINE WITH A BACKTICKED INTERFACE IDENTIFIER are load-bearing: there the
hedge qualifies a concrete vm_*/pm_*/q*_ claim a reader may act on. This check flags those
(targets the ~40-50 load-bearing ones, not the ~200 narrative hedges).

Advisory only (exit 0): a hedge near an identifier is sometimes legitimate honest marking;
the goal is to surface them for verify-or-de-hedge, not to block the gate. Opt out:
  - whole-doc: a line `<!-- check-hedged: allow -->`
  - per-line:  append `<!-- check-hedged -->` to the line

`--self-test` runs an in-memory positive control and exits.
"""
import glob
import re
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent

HEDGE_RE = re.compile(
    r'\b(inferred|assumed|presumably)\b',
    re.IGNORECASE)
# Interface identifier appearing INSIDE an inline-code span (the load-bearing surface).
# Start narrow: vm_/pm_/im_/fm_/pcm_/sm_ interface vars + q<N>_ equations. The id may sit
# mid-expression (e.g. `sum(j2, vm_cost_transp(j2,k))`), so we scan inside backtick spans
# rather than requiring the id to be backtick-adjacent.
# R7: hedge set narrowed to high-signal words (inferred/assumed/presumably) -- the broad set
# Widening the id set to module-internal vars (v<N>_/p<N>_/s<N>_/c<N>_) raises it to ~30;
# kept narrow by default for precision - cross-module interface hedges do the most harm
# (the M40 "inferred sum(j2, vm_cost_transp)" bug was exactly this). Widen if more coverage
# is wanted; this check is advisory either way.
CODE_SPAN_RE = re.compile(r'`[^`]+`')
ID_TOKEN_RE = re.compile(r'\b(?:vm|pm|im|fm|pcm|sm)_[a-zA-Z]\w*|\bq\d+_[a-zA-Z]\w*')
WHOLE_ALLOW = "<!-- check-hedged: allow -->"
LINE_ALLOW = "<!-- check-hedged -->"


def _has_backticked_id(line):
    return any(ID_TOKEN_RE.search(span) for span in CODE_SPAN_RE.findall(line))


def scan_text(text):
    """Return [(lineno, hedge, line)] for load-bearing hedged claims."""
    hits = []
    in_fence = False
    whole_allow = any(l.strip() == WHOLE_ALLOW for l in text.splitlines())
    if whole_allow:
        return hits
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or LINE_ALLOW in line or "\U0001F534" in line:  # 🔴 = honestly-inferred badge
            continue
        hm = HEDGE_RE.search(line)
        if hm and _has_backticked_id(line):
            hits.append((i, hm.group(0), line.strip()[:110]))
    return hits


def _self_test():
    failures = []
    pos = ("**Usage in Module 11** (inferred from standard MAgPIE cost structure): "
           "`sum(j2, vm_cost_transp(j2,k))`\n")
    if not scan_text(pos):
        failures.append("did not flag the M40 'inferred ... `vm_cost_transp`' line")
    if scan_text("Module 40 is likely the most-used transport module in practice.\n"):
        failures.append("wrongly flagged a hedge with no interface identifier")
    if scan_text("```\n# assumed `vm_cost_transp` default 0\n```\n"):
        failures.append("wrongly flagged a hedge inside a code fence")
    if scan_text("The `vm_cost_transp` value is assumed 0 here. <!-- check-hedged -->\n"):
        failures.append("did not honor the per-line allow opt-out")
    if scan_text("<!-- check-hedged: allow -->\nAll `vm_x` assumed; this doc is illustrative.\n"):
        failures.append("did not honor the whole-doc allow opt-out")
    if failures:
        print("SELF-TEST FAILED:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        return 1
    print("SELF-TEST OK - flags hedge+identifier lines; skips no-id / code-fence / allow-marked.",
          file=sys.stderr)
    return 0


def main():
    if "--self-test" in sys.argv:
        rc = _self_test()
        if rc == 0:
            print("SELFTEST_OK check_hedged_claims")
        return rc
    files = [f for f in sorted(glob.glob(str(AGENT_DIR / "modules" / "module_*.md")))
             if "_notes.md" not in f]
    out, total = [], 0
    for f in files:
        for ln, hedge, line in scan_text(Path(f).read_text()):
            out.append(f"  {Path(f).name}:{ln}  [{hedge}]  {line}")
            total += 1
    if total == 0:
        print("Hedged-as-fact (load-bearing): none found.")
        return 0
    print(f"ADVISORY: {total} hedged-as-fact claim(s) on a line with a backticked interface "
          f"identifier (a hedge qualifying a concrete vm_*/pm_*/q*_ claim; verify-or-de-hedge):")
    for line in out:
        print(line)
    print("Opt out: whole-doc line `<!-- check-hedged: allow -->`, or per-line `<!-- check-hedged -->`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
