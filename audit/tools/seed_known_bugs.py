#!/usr/bin/env python3
"""Seeded-bug detection benchmark — how many REAL past doc bugs would the gate catch today?

WHY THIS EXISTS
---------------
Every quality number this project reports is self-play: the agent answers, the
agent scores. `validation_rounds.json`'s means and the 9.52 corpus figure both
measure "few bugs found at that depth/FNR", not "few bugs exist" — and R54/R55
showed 9-month-old Criticals surviving repeated green passes. A checker battery
that reports 0 findings is indistinguishable from a battery that cannot see.

This harness answers the missing question directly: take bugs that were REAL,
put them back, and count how many the gate catches.

METHOD — reverse-apply, not replay
----------------------------------
The obvious approach (check out the pre-fix doc and run the checkers) confounds
DETECTION with CODE DRIFT: an old doc is judged against today's GAMS source, so
a "miss" may just mean the code moved. Instead each fix commit is split into
individual hunks and one hunk at a time is REVERSE-applied to TODAY's doc. The
injected text is the exact wrong claim that existed historically, sitting in an
otherwise-current corpus, judged against current code. Drift is eliminated by
construction and every finding is attributable to one hunk.

This follows [[feedback_historical_replay_positive_control]]: a REAL pre-fix
artifact discriminates broken-vs-fixed on real data in a way a synthetic
fixture cannot, so a "0" here is informative rather than vacuous.

CONTROLS (a benchmark without these is theatre)
----------------------------------------------
  baseline  clean corpus is measured first; only findings NOT in the baseline
            count as a detection, so pre-existing advisory noise cannot inflate
            the rate.
  positive  at least one seeded bug MUST be caught. If none is, the plumbing is
            broken and the run ABORTS rather than reporting a clean 0%.
  vacuity   each injection is verified to have actually changed the file on
            disk; a hunk that fails to reverse-apply is reported as SKIPPED,
            never silently counted as a miss.

Usage:
  python3 audit/tools/seed_known_bugs.py [--limit N] [--json OUT] [--verbose]
Exit: 0 on a completed run (even with misses — misses are the POINT), 2 on a
      broken harness (no positive control, unusable baseline).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[2]
MAGPIE_DIR = AGENT_DIR.parent

# Checkers to run per injection. Doc-vs-code checks that could plausibly bind a
# doc claim. Kept small so a run stays minutes, not hours.
CHECKERS = [
    "check_attribution_omissions",
    "check_dependent_counts",
    "check_consumer_attribution",
    "check_attribution_prose",
    "check_attribution_tables",
    "check_role_attribution",
    "check_dependent_direction",
    "check_fenced_identifiers",
    "check_doc_var_existence",
    "check_gams_variables",
]

# Curated REAL doc-bug fixes. Each entry is a commit whose diff to modules/*.md
# reverted a genuine, verified bug. `klass` records what the bug WAS, so misses
# can be grouped into a blind-spot map rather than a bare percentage.
SEED_COMMITS = [
    ("2b74f9e", "module_59 dependency set (Critical, R58)", "attribution_set"),
    ("60b2c62", "module_52 stockType (Critical latent, R59)", "set_membership"),
    ("0812d19", "module_70 2 Criticals + 9th interface output", "attribution_set"),
    ("48c789f", "module_11/29 5 confirmed Criticals", "attribution_set"),
    ("581e26d", "R55 depth-audit findings M10/M52/M56/M58", "attribution_read"),
    ("658f56e", "2 cross-module phantoms (M59, M73)", "attribution_phantom"),
    ("228b26c", "module_59 remaining Major/Minor", "mixed"),
    ("ee14508", "R58 diagram phantoms", "diagram_phantom"),
    ("b6afd58", "M29 inverted fallow + M32 populate-vs-consume", "mechanism"),
    ("2f52a70", "module_10 land-init source LUH2 -> LUH3", "data_source"),
    ("ec119a9", "2 MANDATE-18 vein bugs", "attribution_role"),
    ("3620958", "3 module_80 mis-citations", "citation"),
]

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@", re.M)


def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def git(args, cwd=AGENT_DIR):
    return run(["git", *args], cwd=cwd)


def split_hunks(diff_text: str) -> list[str]:
    """Split a single-file diff into one-hunk diffs, each with the file header."""
    lines = diff_text.splitlines(keepends=True)
    header, i = [], 0
    while i < len(lines) and not lines[i].startswith("@@"):
        header.append(lines[i])
        i += 1
    if i >= len(lines):
        return []
    hunks, cur = [], []
    for line in lines[i:]:
        if line.startswith("@@"):
            if cur:
                hunks.append("".join(header + cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        hunks.append("".join(header + cur))
    return hunks


def findings(worktree: Path, env: dict) -> dict[str, set[str]]:
    """Run every checker in `worktree`; return check -> set of finding lines.

    Only lines that look like a per-file finding are kept (they carry a doc
    path), so summary/among counters do not register as detections.
    """
    out: dict[str, set[str]] = {}
    for chk in CHECKERS:
        script = worktree / "scripts" / f"{chk}.py"
        if not script.is_file():
            continue
        r = run([sys.executable, str(script)], env=env)
        lines = set()
        for ln in (r.stdout + r.stderr).splitlines():
            s = ln.strip()
            if not s or "SUMMARY" in s or "coverage" in s.lower():
                continue
            if ".md" in s and ("modules/" in s or "core_docs/" in s or "cross_module/" in s):
                lines.add(s)
        out[chk] = lines
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="max hunks to test")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    env = {"MAGPIE_DIR": str(MAGPIE_DIR), "PATH": "/usr/bin:/bin:/usr/local/bin",
           "HOME": str(Path.home())}

    tmp = Path(tempfile.mkdtemp(prefix="seedbugs_"))
    wt = tmp / "wt"
    print(f"seed_known_bugs: preparing scratch corpus (worktree at HEAD)", file=sys.stderr)
    r = git(["worktree", "add", "--detach", str(wt), "HEAD"])
    if r.returncode != 0:
        print(f"FATAL: could not create worktree: {r.stderr[:300]}", file=sys.stderr)
        return 2

    try:
        print("seed_known_bugs: measuring CLEAN baseline ...", file=sys.stderr)
        base = findings(wt, env)
        base_total = sum(len(v) for v in base.values())
        print(f"  baseline: {base_total} finding-lines across {len(base)} checkers",
              file=sys.stderr)

        results, tested = [], 0
        for commit, desc, klass in SEED_COMMITS:
            files = [f for f in git(["show", "--name-only", "--format=", commit]
                                    ).stdout.split() if f.endswith(".md")
                     and (f.startswith("modules/") or f.startswith("core_docs/")
                          or f.startswith("cross_module/"))]
            for rel in files:
                diff = git(["show", commit, "--", rel]).stdout
                for hi, hunk in enumerate(split_hunks(diff)):
                    if args.limit and tested >= args.limit:
                        break
                    target = wt / rel
                    if not target.is_file():
                        continue
                    before = target.read_text()
                    # Reverse-apply this hunk => re-inject the historical bug.
                    ap_r = subprocess.run(
                        ["git", "apply", "-R", "--recount"], cwd=str(wt),
                        input=hunk, capture_output=True, text=True)
                    if ap_r.returncode != 0:
                        results.append({"commit": commit, "file": rel, "hunk": hi,
                                        "desc": desc, "class": klass,
                                        "status": "SKIPPED_NOT_APPLICABLE"})
                        continue
                    after = target.read_text()
                    if after == before:                       # vacuity control
                        results.append({"commit": commit, "file": rel, "hunk": hi,
                                        "desc": desc, "class": klass,
                                        "status": "SKIPPED_NO_CHANGE"})
                        continue
                    tested += 1
                    now = findings(wt, env)
                    caught_by = sorted(c for c in now if (now[c] - base.get(c, set())))
                    new_lines = sorted(
                        ln for c in now for ln in (now[c] - base.get(c, set())))
                    results.append({
                        "commit": commit, "file": rel, "hunk": hi, "desc": desc,
                        "class": klass,
                        "status": "CAUGHT" if caught_by else "MISSED",
                        "caught_by": caught_by,
                        "new_findings": new_lines[:4],
                    })
                    if args.verbose:
                        mark = "OK " if caught_by else "MISS"
                        print(f"  [{mark}] {rel} h{hi} <- {commit} "
                              f"{'/'.join(caught_by) if caught_by else ''}", file=sys.stderr)
                    target.write_text(before)                  # restore
    finally:
        git(["worktree", "remove", "--force", str(wt)])
        shutil.rmtree(tmp, ignore_errors=True)

    tested_r = [r for r in results if r["status"] in ("CAUGHT", "MISSED")]
    caught = [r for r in tested_r if r["status"] == "CAUGHT"]
    skipped = [r for r in results if r["status"].startswith("SKIPPED")]

    print("\n=== SEEDED-BUG DETECTION ===")
    print(f"injected & measured : {len(tested_r)}")
    print(f"caught              : {len(caught)}")
    print(f"missed              : {len(tested_r) - len(caught)}")
    print(f"skipped (not applicable to today's text): {len(skipped)}")
    if tested_r:
        print(f"DETECTION RATE      : {100*len(caught)/len(tested_r):.1f}% "
              f"({len(caught)}/{len(tested_r)})")

    by_class: dict[str, list[int]] = {}
    for r in tested_r:
        b = by_class.setdefault(r["class"], [0, 0])
        b[1] += 1
        if r["status"] == "CAUGHT":
            b[0] += 1
    print("\nBY BUG CLASS (caught/total):")
    for k, (c, t) in sorted(by_class.items(), key=lambda kv: -kv[1][1]):
        print(f"  {k:22s} {c:3d}/{t:<3d}  {'BLIND SPOT' if c == 0 else ''}")

    fired: dict[str, int] = {}
    for r in caught:
        for c in r["caught_by"]:
            fired[c] = fired.get(c, 0) + 1
    print("\nWHICH CHECKER FIRED:")
    for c, n in sorted(fired.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {c}")
    for c in CHECKERS:
        if c not in fired:
            print(f"    0  {c}   <- never fired on any seeded bug")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(
            {"results": results, "baseline_findings": base_total}, indent=2))
        print(f"\ndetail -> {args.json_out}")

    # POSITIVE CONTROL — a benchmark that catches nothing is broken, not clean.
    if tested_r and not caught:
        print("\nFATAL: positive control FAILED — no seeded bug was detected at all. "
              "Treat this as broken plumbing, NOT as a 0% detection rate.",
              file=sys.stderr)
        return 2
    if not tested_r:
        print("\nFATAL: no hunk could be injected; nothing was measured.", file=sys.stderr)
        return 2
    print("\nSEEDBUGS_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
