#!/usr/bin/env python3
"""Audit arena — hand an LLM auditor a seeded corpus and score what it finds.

WHY THIS EXISTS
---------------
`seed_known_bugs.py` measures the DETERMINISTIC gate: inject one real historical
doc bug, run the checker battery, restore, repeat. It answers "what fraction of
real doc bugs does the checker battery catch" and the current answer is 41.7%.

Four bug classes sit at a stable 0 across two runs eleven days apart and across
a checker-list correction — `attribution_role`, `citation`, `data_source`,
`mechanism`. They are blind for a diagnosed reason: the claims name no interface
variable, and every attribution checker is var-anchored, so there is nothing to
bind (`check_bindability` sizes the class corpus-wide).

The open question is whether an LLM auditor can see what the battery cannot. To
ask it honestly you need the same thing that made the gate benchmark credible:
ground truth that already exists, controls that make a false positive
measurable, and an auditor that cannot see the answer key. That is this tool.

It is deliberately NOT an agent runner. It does two things — `prepare` an arena
and `score` an auditor's output — because the dispatch step is a human decision
(the Fable arm is opened by hand; the Opus arm may be a subagent) and baking one
mechanism in would have made the tool usable for only one of them.

WHAT THE AUDITOR MUST NOT BE ABLE TO SEE, AND HOW EACH IS CLOSED
---------------------------------------------------------------
  git history      The arena is `git archive`-extracted, NOT a worktree. There
                   is no `.git`, so `git diff`/`git log` cannot reveal the
                   injections. A worktree would have handed over the answer key
                   in one command.
  the audit layer  `audit/` and `project/` are stripped. This project documents
                   its own auditing, so the round archives, the benchmark
                   write-ups and the seeding tool itself name these exact bugs.
                   Measured before the strip existed: `audit/` held the module_80
                   citation fix diff VERBATIM and the seeding tool named the
                   module_10 LUH2->LUH3 bug in a comment. An arena built without
                   this strip is not blind, and its result is worthless.
  everything else  Stripping the directories someone thought of is the reasoning
                   that let the leak in, so `leak_scan()` then greps every
                   surviving file for the seed commit SHAs and for verbatim
                   >=40-char lines from either side of each injected hunk. A hit
                   ABORTS the build.
  file mtimes      Every file in the arena is stamped to one uniform time AFTER
                   injection, so `ls -lt` does not sort the seeded files to the
                   top.
  the key itself   The key is written to a SEPARATE root, and `prepare` refuses
                   to run if the key root is inside the arena root.
  the count        The brief never states how many defects were injected, and
                   says explicitly that some files may contain none — otherwise
                   the task degenerates into a search with a stopping rule.

CONTROLS
--------
  clean controls   The auditor is given a BOUNDED file list: seeded files plus
                   unmodified controls of comparable length. Without a bounded
                   list, "found 6 bugs" and "flags everything" are the same
                   observation, because the denominator is unknown.
  vacuity          Every injection is verified to have changed the file on disk;
                   a hunk that does not reverse-apply is reported SKIPPED, never
                   silently counted against the auditor.
  honest FP        A flag on a file with no injection is reported as
                   FLAG_NO_INJECTION, *not* as a false positive. The corpus is
                   not certified clean, so some of those may be real bugs the
                   auditor found. Calling them FPs would score the auditor down
                   for being right. They need triage; the tool says so.

PATH HYGIENE (this repo is PUBLIC)
----------------------------------
Agents echo their environment into their output: R59 leaked 8 local absolute
paths into this public repo that way, every one traceable to a path put INTO the
prompt. The brief therefore uses an `<ARENA>` token rather than a literal path,
and — because a convention that depends on an agent's discipline is not a
control — `score` mechanically scrubs absolute paths out of every artifact it
writes. The scrubber is asserted in `--self-test`.

Usage:
  python3 audit/tools/prepare_audit_arena.py prepare --dry-run
  python3 audit/tools/prepare_audit_arena.py prepare --arena-root DIR --key-root DIR
  python3 audit/tools/prepare_audit_arena.py score --key KEY.json --findings F.json
  python3 audit/tools/prepare_audit_arena.py --self-test
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_known_bugs import SEED_COMMITS, split_hunks  # noqa: E402

AGENT_DIR = Path(__file__).resolve().parents[2]
MAGPIE_DIR = AGENT_DIR.parent

# The four classes the deterministic battery has never scored on. Anything else
# in SEED_COMMITS is already covered by seed_known_bugs.py and would dilute this
# measurement with bugs we know a checker catches.
BLIND_CLASSES = ("attribution_role", "citation", "data_source", "mechanism")

# Measured 2026-07-31: nitrogen-term density in the blind-class seed files.
# module_58.md carries 15 hits (13 x N2O); every other blind-class file carries
# 0 or 1. This workspace's Fable tier bails on nitrogen content, so module_58 is
# excluded BY DEFAULT and run last, on its own, as a deliberate calibration
# probe on where the threshold sits (Mike's call, per the plan). Re-include with
#   --include-file modules/module_58.md
DEFAULT_EXCLUDED_FILES = ("modules/module_58.md",)

DOC_PREFIXES = ("modules/", "core_docs/", "cross_module/")
UNIFORM_MTIME = 1_600_000_000  # 2020-09-13, well before any of this work

# The project's own meta-layer. Not MAgPIE documentation — documentation of how
# MAgPIE's documentation gets audited, which is where every answer key lives.
META_DIRS = ("audit", "project")

# Terms this workspace's Fable tier bails on. The seeded files were chosen to
# avoid them, but CONTROLS are chosen automatically and the first version of the
# picker optimised length alone — it selected `module_50` (nr_soil_budget) and
# `module_55` (awms), which would have failed the Fable arm on the control files
# while every seeded file ran fine. Controls are held to the same bar as seeds
# so that ONE arena serves both the Fable and the Opus arm; a per-tier arena
# would make the two results incomparable, which is the question being asked.
AVOID_RE = re.compile(
    r"nitrogen|nitrous|N2O|N₂O|NH3|NH₃|ammonia|nitrate|nitrif|denitrif"
    r"|fertilis|fertiliz|manure|\bnr_|\bvm_nr|urea", re.I)

# Shortest hunk line worth searching for. Below ~40 chars a generic prose line
# is things like "| Variable | Module |" and every table in the corpus matches.
LEAK_MIN_LEN = 40

# ...but a SHORT line carrying a file:line CITATION is a complete answer on its
# own — `(lp_nlp_apr17/solve.gms:16, 174)` is 33 characters and says everything.
# Measured across all 12 seed commits (2026-07-31): 303 hunk lines are >=40
# chars, 12 fall in 18-39 without a citation, and ZERO fall in 18-39 WITH one.
# So this rule is currently INERT — it buys nothing on today's corpus and is
# kept as a prospective guard, not as a fix to an observed miss.
#
# A wider version of this rule was tried and dropped the same day: allowing any
# MAgPIE identifier admitted 3 tokens, one of which was
# `| **M30** (croparea) | \`vm_area\` | |` — a bare table row, i.e. exactly the
# noise the 40-char floor exists to exclude. A citation is an answer; an
# identifier in a table is not.
LEAK_MIN_LEN_SPECIFIC = 18
SPECIFIC_RE = re.compile(r"\.gms:\d")

# Absolute-path shapes that must never reach a tracked artifact.
ABS_PATH_RE = re.compile(
    r"(?:/Users/[^\s\"'`,;:)\]]+"
    r"|/home/[^\s\"'`,;:)\]]+"
    r"|/p/projects/[^\s\"'`,;:)\]]+"
    r"|/private/(?:tmp|var)/[^\s\"'`,;:)\]]+"
    r"|/(?:tmp|var)/[^\s\"'`,;:)\]]+)")

FINDING_RE = re.compile(
    r"((?:modules|core_docs|cross_module)/[A-Za-z0-9._/-]+\.md):(\d+)")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def git(args, cwd=AGENT_DIR):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def scrub(text: str, extra: dict[str, str] | None = None) -> str:
    """Replace known roots with tokens, then redact any surviving absolute path.

    Two layers on purpose: the token pass keeps the artifact READABLE (you can
    still tell arena paths from key paths), and the regex pass is the backstop
    for paths the tool never knew about — an agent's own scratch dir, a HOME it
    printed, a temp file it made.
    """
    for literal, token in sorted((extra or {}).items(), key=lambda kv: -len(kv[0])):
        if literal:
            text = text.replace(literal, token)
    return ABS_PATH_RE.sub("<REDACTED_PATH>", text)


def changed_ranges(before: str, after: str) -> list[tuple[int, int]]:
    """Line ranges (1-based, inclusive) in AFTER that differ from BEFORE.

    Computed from a real diff rather than from the @@ header: with --recount and
    several hunks landing in one file the header offsets drift, and an
    attribution window anchored on a drifted line silently scores catches as
    misses. This is the same class of error that made a first pass of the
    2026-07-31 benchmark report 4-5 unattributable catches when the true number
    was 2.
    """
    a, b = before.splitlines(), after.splitlines()
    out: list[tuple[int, int]] = []
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":                 # deleted from AFTER: point at the seam
            out.append((max(1, j1), max(1, j1)))
        else:
            out.append((j1 + 1, max(j1 + 1, j2)))
    return out


def collect_hunks(classes, excluded, included):
    """Every candidate hunk for the requested classes, before applicability."""
    excl = {e for e in excluded if e not in set(included)}
    cands = []
    for commit, desc, klass in SEED_COMMITS:
        if klass not in classes:
            continue
        files = [f for f in git(["show", "--name-only", "--format=", commit]).stdout.split()
                 if f.endswith(".md") and f.startswith(DOC_PREFIXES)]
        for rel in files:
            diff = git(["show", commit, "--", rel]).stdout
            for hi, hunk in enumerate(split_hunks(diff)):
                cands.append({"commit": commit, "file": rel, "hunk": hi,
                              "desc": desc, "class": klass, "diff": hunk,
                              "excluded": rel in excl})
    return cands


def build_gams_mirror(root: Path) -> int:
    """Lean read-only mirror of the GAMS ground truth: *.gms + config + core.

    A copy, not a symlink: a symlink would let an auditor with Write access edit
    the real model source. Measured 2026-07-31 the full `modules/` tree is 488M
    (almost all of it input data the checkers never read), while the 606 *.gms
    files total 3.0M — every GAMS-side read in `scripts/` globs *.gms, plus
    `config/default.cfg`. So the lean mirror is faithful, not a shortcut.
    """
    n = 0
    for p in (MAGPIE_DIR / "modules").rglob("*.gms"):
        dst = root / p.relative_to(MAGPIE_DIR)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        n += 1
    for sub in ("config", "core"):
        src = MAGPIE_DIR / sub
        if src.is_dir():
            shutil.copytree(src, root / sub, dirs_exist_ok=True)
    if (MAGPIE_DIR / "main.gms").is_file():
        shutil.copy2(MAGPIE_DIR / "main.gms", root / "main.gms")
    return n


def leak_tokens(injected: list[dict], hunks_by_key: dict[str, str]) -> dict[str, str]:
    """Strings whose presence anywhere else in the arena would give the game away.

    Both sides of each hunk are collected, not just the injected side. The
    REMOVED side is the correct text: if it survives elsewhere in the corpus the
    auditor can find the defect by internal contradiction without ever opening
    the GAMS source — which is a different capability than the one being
    measured, and would be scored as though it were the same one.
    """
    toks: dict[str, str] = {}
    for i in injected:
        sha = i["commit"]
        toks[sha] = f"seed commit {sha}"
        full = git(["rev-parse", sha]).stdout.strip()
        if len(full) == 40:
            toks[full] = f"seed commit {sha} (full sha)"
        for ln in hunks_by_key.get(f"{i['file']}#{i['hunk']}", "").splitlines():
            if ln[:1] in "+-" and ln[:3] not in ("+++", "---"):
                body = ln[1:].strip()
                if len(body) >= LEAK_MIN_LEN or (
                        len(body) >= LEAK_MIN_LEN_SPECIFIC and SPECIFIC_RE.search(body)):
                    toks[body] = f"hunk text from {i['file']}#{i['hunk']}"
    return toks


def leak_scan(corpus: Path, seeded: set[str], toks: dict[str, str]) -> list[tuple[str, str]]:
    """Every file outside the seeded set that contains an answer token."""
    hits: list[tuple[str, str]] = []
    for p in sorted(corpus.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(corpus))
        if rel in seeded:
            continue
        try:
            text = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for tok, why in toks.items():
            if tok in text:
                hits.append((rel, why))
                break
    return hits


def normalize_mtimes(root: Path) -> None:
    for p in root.rglob("*"):
        try:
            os.utime(p, (UNIFORM_MTIME, UNIFORM_MTIME))
        except OSError:
            pass
    os.utime(root, (UNIFORM_MTIME, UNIFORM_MTIME))


def avoid_hits(text: str) -> int:
    return len(AVOID_RE.findall(text))


def pick_controls(corpus: Path, seeded: set[str], n: int, max_avoid: int | None) -> list[str]:
    """Clean docs of comparable length and comparable term profile.

    Comparable length matters: a flag rate is per-file only if the files offer
    similar surface area to flag. Nearest-by-line-count to the seeded median,
    ties broken by path, so a re-run reproduces the same arena.

    `max_avoid` is None to disable the term filter.
    """
    if n <= 0:
        return []
    seeded_lens = sorted(len((corpus / f).read_text().splitlines())
                         for f in seeded if (corpus / f).is_file())
    if not seeded_lens:
        return []
    median = seeded_lens[len(seeded_lens) // 2]
    cands = []
    for pref in DOC_PREFIXES:
        for p in sorted((corpus / pref).rglob("*.md")):
            rel = str(p.relative_to(corpus))
            if rel in seeded:
                continue
            text = p.read_text()
            if max_avoid is not None and avoid_hits(text) > max_avoid:
                continue
            cands.append((abs(len(text.splitlines()) - median), rel))
    cands.sort()
    return sorted(rel for _d, rel in cands[:n])


BRIEF = """\
# Documentation audit — brief

You are auditing the AI documentation of the MAgPIE land-use model against the
model's actual GAMS source code.

## Where things are

- Corpus root (your working directory): `<ARENA>`
- Documentation to audit: the files listed below, paths relative to the corpus root.
- GAMS ground truth: `../modules/` relative to the corpus root — the real model
  source (`../modules/NN_name/<realization>/*.gms`), plus `../config/default.cfg`.

**Report every path relative to the corpus root** (e.g. `modules/module_40.md`,
`../modules/40_transport/gtap_nov12/equations.gms:14`). Do not write absolute
paths into your output.

## Your task

For each listed file, find claims that CONTRADICT the GAMS source. In scope:

- a claim about which module provides, writes, or reads an interface variable
- a citation that points at the wrong file, the wrong realization, or a file
  that does not exist
- a claim about where a piece of input data comes from
- a claim that the model MECHANISTICALLY models something when the code applies
  a fixed rate, a historical parameter, or an exogenous input — and the reverse

Out of scope: typos, formatting, style, missing content, anything you cannot
check against the code.

Some of these files may contain no defects at all. Do not assume each file has
one, and do not stop when you have found a few — audit every listed file.

## Files

{filelist}

## Output format

Write JSON, and nothing else:

```json
{{"findings": [
  {{"file": "modules/module_XX.md",
   "line": 123,
   "claim": "the exact text you believe is wrong",
   "why_wrong": "what the code actually says",
   "evidence": "../modules/NN_name/real/file.gms:45",
   "severity": "Critical|Major|Minor"}}
]}}
```

`line` must be the line in the documentation file where the wrong claim sits.
If you are confident a file is clean, say nothing about it.
"""


# --------------------------------------------------------------------------
# prepare
# --------------------------------------------------------------------------
def cmd_prepare(args) -> int:
    classes = tuple(c.strip() for c in args.classes.split(",") if c.strip())
    included = tuple(args.include_file or ())
    excluded = tuple(args.exclude_file) if args.exclude_file else DEFAULT_EXCLUDED_FILES

    cands = collect_hunks(classes, excluded, included)
    if args.only_hunk:
        want = set(args.only_hunk)
        cands = [c for c in cands
                 if f"{c['file']}#{c['hunk']}" in want or c["file"] in want]
        for c in cands:
            c["excluded"] = False

    live = [c for c in cands if not c["excluded"]]
    held = [c for c in cands if c["excluded"]]

    print("=== ARENA PLAN ===")
    print(f"classes   : {','.join(classes)}")
    print(f"candidates: {len(cands)}  ({len(live)} to inject, {len(held)} held back)")
    for c in cands:
        mark = "HELD " if c["excluded"] else "     "
        print(f"  {mark}{c['file']}#{c['hunk']:<2d} [{c['class']}] {c['commit']} {c['desc']}")
    if held:
        print("\n  HELD files are excluded by default and must be run separately;")
        print("  --include-file <path> overrides.")
    if args.dry_run:
        print("\n(dry run — nothing built)")
        return 0
    if not live:
        print("\nFATAL: no hunk selected; nothing to build.", file=sys.stderr)
        return 2

    arena_root = Path(args.arena_root).resolve() if args.arena_root else \
        Path(tempfile.mkdtemp(prefix="arena_"))
    key_root = Path(args.key_root).resolve() if args.key_root else \
        Path(tempfile.mkdtemp(prefix="arenakey_"))
    # The key must not be reachable from the arena. An auditor with Bash can
    # walk upward, so nesting is refused rather than warned about.
    if key_root == arena_root or arena_root in key_root.parents or key_root in arena_root.parents:
        print("FATAL: key root and arena root must not be nested — the auditor "
              "would be able to read the answer key.", file=sys.stderr)
        return 2

    fake_magpie = arena_root / "magpie"
    corpus = fake_magpie / "magpie-agent"
    corpus.mkdir(parents=True, exist_ok=True)

    # git archive, NOT a worktree: no .git means no `git diff` shortcut to the key.
    # Binary pipe (text=False) — a tar stream round-tripped through str corrupts.
    tar = subprocess.run(["git", "archive", "--format=tar", "HEAD"],
                         cwd=AGENT_DIR, capture_output=True)
    if tar.returncode != 0:
        print(f"FATAL: git archive failed: {tar.stderr[:300]!r}", file=sys.stderr)
        return 2
    ar = subprocess.run(["tar", "-x", "-C", str(corpus)],
                        input=tar.stdout, capture_output=True)
    if ar.returncode != 0:
        print(f"FATAL: tar extract failed: {ar.stderr[:300]!r}", file=sys.stderr)
        return 2
    n_gms = build_gams_mirror(fake_magpie)

    stripped = []
    if not args.keep_meta:
        for d in META_DIRS:
            if (corpus / d).is_dir():
                shutil.rmtree(corpus / d)
                stripped.append(d + "/")

    injected, skipped, hunks_by_key = [], [], {}
    for c in live:
        target = corpus / c["file"]
        if not target.is_file():
            skipped.append({**{k: c[k] for k in ("commit", "file", "hunk", "class")},
                            "why": "file absent from today's corpus"})
            continue
        before = target.read_text()
        r = subprocess.run(["git", "apply", "-R", "--recount", "--unsafe-paths",
                            "--directory=.", "-"],
                           cwd=str(corpus), input=c["diff"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            # No .git in the arena, so `git apply` runs in --no-index style; if
            # it still refuses, the hunk genuinely does not fit today's text.
            skipped.append({**{k: c[k] for k in ("commit", "file", "hunk", "class")},
                            "why": f"hunk no longer applies ({r.stderr.strip()[:120]})"})
            continue
        after = target.read_text()
        if after == before:                                   # vacuity control
            skipped.append({**{k: c[k] for k in ("commit", "file", "hunk", "class")},
                            "why": "reverse-apply produced no change"})
            continue
        injected.append({"commit": c["commit"], "file": c["file"], "hunk": c["hunk"],
                         "class": c["class"], "desc": c["desc"],
                         "ranges": changed_ranges(before, after)})
        hunks_by_key[f"{c['file']}#{c['hunk']}"] = c["diff"]

    if not injected:
        print("FATAL: nothing was injected; the arena would measure nothing.", file=sys.stderr)
        shutil.rmtree(arena_root, ignore_errors=True)
        return 2

    seeded_files = {i["file"] for i in injected}

    # BLINDNESS CONTROL — after this point the arena either is blind or is not
    # built. An arena that leaks its own key produces a number that reads like a
    # measurement and is not one, so this aborts rather than warns.
    leaks = leak_scan(corpus, seeded_files, leak_tokens(injected, hunks_by_key))
    if leaks and not args.allow_leaks:
        print(f"\nFATAL: arena is NOT BLIND — {len(leaks)} file(s) contain the answer:",
              file=sys.stderr)
        for rel, why in leaks[:20]:
            print(f"  {rel}   <- {why}", file=sys.stderr)
        if len(leaks) > 20:
            print(f"  ... and {len(leaks) - 20} more", file=sys.stderr)
        print("Strip these from the arena or drop the affected hunk. Refusing to "
              "build an arena whose result would be meaningless.", file=sys.stderr)
        shutil.rmtree(arena_root, ignore_errors=True)
        return 2

    max_avoid = None if args.no_avoid else args.max_avoid_hits
    controls = pick_controls(corpus, seeded_files, args.controls, max_avoid)
    filelist = sorted(seeded_files | set(controls))
    density = {f: avoid_hits((corpus / f).read_text()) for f in filelist}

    normalize_mtimes(arena_root)

    brief = BRIEF.format(filelist="\n".join(f"- `{f}`" for f in filelist))
    key = {
        "arena_root": str(arena_root),
        "corpus": str(corpus),
        "classes": list(classes),
        "injected": injected,
        "skipped": skipped,
        "controls": controls,
        "filelist": filelist,
        "gms_files_mirrored": n_gms,
        "stripped_dirs": stripped,
        "leaks_found": [{"file": f, "why": w} for f, w in leaks],
        "avoid_term_hits": density,
        "avoid_max_allowed": max_avoid,
    }
    (key_root / "ANSWER_KEY.json").write_text(json.dumps(key, indent=2))
    (key_root / "auditor_brief.md").write_text(brief)

    print("\n=== ARENA BUILT ===")
    print(f"injected : {len(injected)}")
    for i in injected:
        rng = ",".join(f"{a}-{b}" for a, b in i["ranges"])
        print(f"  + {i['file']}#{i['hunk']} [{i['class']}] lines {rng}")
    if skipped:
        print(f"skipped  : {len(skipped)}")
        for s in skipped:
            print(f"  - {s['file']}#{s['hunk']} [{s['class']}] {s['why']}")
    print(f"controls : {len(controls)} clean file(s)")
    print(f"presented: {len(filelist)} file(s) total, seeded and clean shuffled by path")
    print(f"gams src : {n_gms} .gms files mirrored + config/ + core/")
    print(f"stripped : {', '.join(stripped) if stripped else '(nothing — --keep-meta)'}")
    print(f"blindness: leak scan clean ({len(leaks)} hits)" if not leaks
          else f"blindness: {len(leaks)} LEAK(S) TOLERATED via --allow-leaks")
    worst = sorted(density.items(), key=lambda kv: -kv[1])[:3]
    worst_str = ", ".join("%s=%d" % (Path(f).name, n) for f, n in worst)
    print(f"avoid-terms: max {max(density.values()) if density else 0} hits in any "
          f"presented file (cap {max_avoid}) — worst: {worst_str}")
    print(f"\narena  -> {arena_root}")
    print(f"key    -> {key_root}/ANSWER_KEY.json")
    print(f"brief  -> {key_root}/auditor_brief.md")
    print("\nPoint the auditor at the corpus and give it the brief with <ARENA>")
    print("replaced by the corpus path. Then:")
    print("  prepare_audit_arena.py score --key <KEY>/ANSWER_KEY.json --findings <out>")
    return 0


# --------------------------------------------------------------------------
# score
# --------------------------------------------------------------------------
def parse_findings(text: str) -> tuple[list[dict], str]:
    """Accept the JSON schema, or fall back to regex over prose.

    The fallback is loud on purpose: a prose scrape recovers file:line and
    nothing else, so a finding that names the right line for the wrong reason
    scores as a catch. That is a real inflation risk and the caller is told.
    """
    t = text.strip()
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            fs = obj.get("findings", obj if isinstance(obj, list) else [])
            if isinstance(fs, list) and all(isinstance(f, dict) for f in fs):
                return fs, "json"
        except json.JSONDecodeError:
            pass
    out, seen = [], set()
    for path, line in FINDING_RE.findall(text):
        k = (path, int(line))
        if k not in seen:
            seen.add(k)
            out.append({"file": path, "line": int(line), "claim": "", "why_wrong": ""})
    return out, "regex-fallback"


def score_findings(key: dict, found: list[dict], window: int) -> dict:
    injected = key["injected"]
    controls = set(key.get("controls", []))
    presented = set(key.get("filelist", []))

    hits = {f"{i['file']}#{i['hunk']}": [] for i in injected}
    per_finding = []
    for f in found:
        rel = str(f.get("file", "")).lstrip("./")
        ln = f.get("line")
        ln = int(ln) if isinstance(ln, (int, str)) and str(ln).isdigit() else None
        matched = None
        for i in injected:
            if i["file"] != rel:
                continue
            if ln is None:
                matched = (f"{i['file']}#{i['hunk']}", "file-only")
                break
            if any(a - window <= ln <= b + window for a, b in i["ranges"]):
                matched = (f"{i['file']}#{i['hunk']}", "line")
                break
            matched = (f"{i['file']}#{i['hunk']}", "file-only")
        if matched:
            hits[matched[0]].append({"strength": matched[1], **f})
            verdict = f"HIT:{matched[1]}"
        elif rel in controls:
            verdict = "FLAG_NO_INJECTION"
        elif rel in presented:
            verdict = "FLAG_NO_INJECTION"
        else:
            verdict = "OFF_LIST"
        per_finding.append({"file": rel, "line": ln, "verdict": verdict,
                            "claim": str(f.get("claim", ""))[:200]})

    # A file-only match is weak evidence: right file, wrong place. Counted
    # separately so the headline cannot be inflated by proximity alone — the
    # same distinction that took the gate benchmark's 20 catches down to an
    # 18-catch attribution-verified floor.
    caught_line = [k for k, v in hits.items() if any(h["strength"] == "line" for h in v)]
    caught_file = [k for k, v in hits.items()
                   if k not in caught_line and v]
    missed = [k for k, v in hits.items() if not v]

    by_class: dict[str, list[int]] = {}
    for i in injected:
        k = f"{i['file']}#{i['hunk']}"
        b = by_class.setdefault(i["class"], [0, 0])
        b[1] += 1
        if k in caught_line:
            b[0] += 1

    return {
        "n_injected": len(injected),
        "caught_line": sorted(caught_line),
        "caught_file_only": sorted(caught_file),
        "missed": sorted(missed),
        "by_class": by_class,
        "flags_without_injection": [p for p in per_finding
                                    if p["verdict"] == "FLAG_NO_INJECTION"],
        "off_list": [p for p in per_finding if p["verdict"] == "OFF_LIST"],
        "per_finding": per_finding,
    }


def cmd_score(args) -> int:
    key = json.loads(Path(args.key).read_text())
    raw = Path(args.findings).read_text()
    found, mode = parse_findings(raw)
    res = score_findings(key, found, args.window)
    res["parse_mode"] = mode
    res["n_findings_reported"] = len(found)

    n = res["n_injected"]
    print("=== AUDITOR SCORE ===")
    if mode == "regex-fallback":
        print("!! findings parsed by REGEX FALLBACK — file:line only, no reasoning was")
        print("!! checked, so a right-line/wrong-reason finding scores as a catch.")
        print("!! Treat the rate as an UPPER BOUND and triage by hand.")
    print(f"injected            : {n}")
    print(f"reported by auditor : {len(found)}")
    print(f"caught (line match) : {len(res['caught_line'])}")
    print(f"caught (file only)  : {len(res['caught_file_only'])}   <- weak, needs triage")
    print(f"missed              : {len(res['missed'])}")
    if n:
        print(f"DETECTION RATE      : {100*len(res['caught_line'])/n:.1f}% "
              f"({len(res['caught_line'])}/{n}) by line match")
    print("\nBY BUG CLASS (caught/total):")
    for k, (c, t) in sorted(res["by_class"].items(), key=lambda kv: -kv[1][1]):
        print(f"  {k:22s} {c:3d}/{t:<3d}  {'BLIND' if c == 0 else ''}")
    print(f"\nflags on files with NO injection: {len(res['flags_without_injection'])}")
    print("  These are NOT automatically false positives. The corpus is not certified")
    print("  clean, so some may be real bugs the auditor found. Triage before scoring.")
    for p in res["flags_without_injection"][:10]:
        print(f"    {p['file']}:{p['line']}  {p['claim'][:80]}")
    if res["off_list"]:
        print(f"\nflags on files NOT in the presented list: {len(res['off_list'])}")

    if args.out:
        payload = scrub(json.dumps(res, indent=2),
                        {key.get("corpus", ""): "<ARENA>",
                         key.get("arena_root", ""): "<ARENA_ROOT>"})
        Path(args.out).write_text(payload)
        print(f"\nscored -> {args.out}  (absolute paths scrubbed)")
    return 0


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------
def self_test() -> int:
    """Synthesized positive controls, built BEFORE the tool met real data.

    A scorer that classifies nothing still prints a plausible 0%, so each
    classification branch gets a fixture that must land in it.
    """
    n_ok = n_fail = 0

    def check(label, cond):
        nonlocal n_ok, n_fail
        if cond:
            n_ok += 1
        else:
            n_fail += 1
            print(f"  FAIL: {label}")

    # --- changed_ranges: the attribution anchor ---
    before = "a\nb\nc\nd\ne\n"
    check("changed_ranges finds a single replaced line",
          changed_ranges(before, "a\nb\nX\nd\ne\n") == [(3, 3)])
    check("changed_ranges finds an insertion",
          changed_ranges(before, "a\nb\nX\nY\nc\nd\ne\n") == [(3, 4)])
    check("changed_ranges is empty on identical text",
          changed_ranges(before, before) == [])

    # --- scrubber: the R59 guard ---
    # The fixtures use the repo's own placeholder conventions (`/Users/you`,
    # `/private/tmp/<scratch>`) because Check 40 scans this file too, and a
    # literal local path here would be exactly the defect it exists to catch.
    # Placeholders still exercise the regex — ABS_PATH_RE stops at whitespace,
    # not at angle brackets. Do not "fix" these back to concrete paths.
    leaked = "see /Users/you/work/repo/file.md and /private/tmp/<scratch>/arena"
    s = scrub(leaked)
    check("scrubber removes a /Users path", "/Users/you" not in s)
    check("scrubber removes a /private/tmp path", "/private/tmp/<scratch>" not in s)
    check("scrubber keeps repo-relative paths intact",
          "modules/module_10.md" in scrub("modules/module_10.md:5"))
    check("scrubber token pass beats the regex pass",
          scrub("/tmp/a/b/corpus/x", {"/tmp/a/b/corpus": "<ARENA>"}) == "<ARENA>/x")

    # --- finding parser ---
    fs, mode = parse_findings('{"findings":[{"file":"modules/module_40.md","line":11}]}')
    check("parser reads the JSON schema", mode == "json" and len(fs) == 1)
    fs2, mode2 = parse_findings("I think modules/module_40.md:11 is wrong, and so is\n"
                                "modules/module_40.md:11 again.")
    check("parser falls back to regex and de-duplicates",
          mode2 == "regex-fallback" and len(fs2) == 1)

    # --- scorer: one fixture per classification branch ---
    key = {"injected": [{"file": "modules/module_40.md", "hunk": 0,
                         "class": "attribution_role", "ranges": [(10, 12)]},
                        {"file": "modules/module_10.md", "hunk": 0,
                         "class": "data_source", "ranges": [(50, 50)]}],
           "controls": ["modules/module_99.md"],
           "filelist": ["modules/module_10.md", "modules/module_40.md",
                        "modules/module_99.md"]}
    res = score_findings(key, [
        {"file": "modules/module_40.md", "line": 11},    # inside the range -> line hit
        {"file": "modules/module_10.md", "line": 400},   # right file, far away -> file-only
        {"file": "modules/module_99.md", "line": 5},     # control -> flag, no injection
        {"file": "core_docs/Data_Flow.md", "line": 7},   # not presented -> off list
    ], window=5)
    check("scorer counts an in-range finding as a line hit",
          res["caught_line"] == ["modules/module_40.md#0"])
    check("scorer counts a far finding in a seeded file as file-only, not a catch",
          res["caught_file_only"] == ["modules/module_10.md#0"])
    check("scorer does not let a file-only match inflate the rate",
          "modules/module_10.md#0" not in res["caught_line"])
    check("scorer flags a control-file finding as FLAG_NO_INJECTION",
          len(res["flags_without_injection"]) == 1
          and res["flags_without_injection"][0]["file"] == "modules/module_99.md")
    check("scorer routes an unlisted file to OFF_LIST", len(res["off_list"]) == 1)
    check("scorer reports the blind class as 0 caught",
          res["by_class"]["data_source"] == [0, 1])
    check("scorer reports the seen class as 1 caught",
          res["by_class"]["attribution_role"] == [1, 1])

    # --- a scorer that catches nothing must not look clean ---
    res0 = score_findings(key, [], window=5)
    check("no findings at all yields 0 caught and 2 missed",
          res0["caught_line"] == [] and len(res0["missed"]) == 2)

    # --- leak scanner: a PLANTED leak must be caught ---
    # Written as a positive control because the failure mode is silence: a
    # scanner that matches nothing reports a clean arena, which is exactly what
    # a genuinely clean arena reports.
    with tempfile.TemporaryDirectory() as td:
        c = Path(td)
        (c / "modules").mkdir(parents=True)
        (c / "audit").mkdir(parents=True)
        long_line = "the M40 transport cost table attributes vm_prod to the wrong module"
        (c / "modules" / "module_40.md").write_text(f"x\n{long_line}\ny\n")
        (c / "audit" / "round_archive.md").write_text(f"we fixed it: {long_line}\n")
        (c / "modules" / "module_11.md").write_text("nothing incriminating here\n")
        toks = {long_line: "hunk text from modules/module_40.md#0"}
        hits = leak_scan(c, {"modules/module_40.md"}, toks)
        check("leak scan finds a planted answer in a non-seeded file",
              [h[0] for h in hits] == ["audit/round_archive.md"])
        check("leak scan exempts the seeded file from its own token",
              "modules/module_40.md" not in [h[0] for h in hits])
        check("leak scan does not flag an innocent file",
              "modules/module_11.md" not in [h[0] for h in hits])
        check("leak scan is clean when the leak is removed",
              leak_scan(c, {"modules/module_40.md", "audit/round_archive.md"}, toks) == [])

    # A short citation-bearing line is a complete answer; a short table row is not.
    short_answer = "see (lp_nlp_apr17/solve.gms:16, 174)"
    toks_short = leak_tokens(
        [{"commit": "3620958", "file": "modules/module_80.md", "hunk": 0}],
        {"modules/module_80.md#0": f"--- a/x\n+++ b/x\n@@ -1 +1 @@\n+{short_answer}\n"})
    check("a short but identifier-bearing hunk line is still a leak token",
          short_answer in toks_short)
    table_row = "| **M30** (croparea) | `vm_area` | |"   # a real 18-39 char hunk line
    check("a short table row is NOT a leak token even though it names a variable",
          table_row not in leak_tokens(
              [{"commit": "3620958", "file": "modules/module_80.md", "hunk": 0}],
              {"modules/module_80.md#0": f"--- a/x\n+++ b/x\n@@ -1 +1 @@\n+{table_row}\n"}))
    check("the specific-line floor is well below the generic one",
          LEAK_MIN_LEN_SPECIFIC < LEAK_MIN_LEN and LEAK_MIN_LEN >= 40)

    # --- control selection must hold controls to the seeds' term bar ---
    with tempfile.TemporaryDirectory() as td:
        c = Path(td)
        for pref in DOC_PREFIXES:
            (c / pref).mkdir(parents=True, exist_ok=True)
        body = "\n".join(f"line {i}" for i in range(60))
        (c / "modules" / "module_40.md").write_text(body)               # the seed
        (c / "modules" / "module_12.md").write_text(body)               # clean control
        (c / "modules" / "module_50.md").write_text(
            body + "\nnitrogen and N2O and fertiliser\n")               # loaded control
        picked = pick_controls(c, {"modules/module_40.md"}, 2, 0)
        check("control picker rejects a nitrogen-loaded doc",
              "modules/module_50.md" not in picked)
        check("control picker still returns a clean doc of comparable length",
              "modules/module_12.md" in picked)
        check("control picker accepts the loaded doc when the filter is disabled",
              "modules/module_50.md" in pick_controls(c, {"modules/module_40.md"}, 2, None))
    check("avoid regex counts the terms Fable bails on",
          avoid_hits("nitrogen N2O fertiliser manure") == 4 and avoid_hits("land carbon") == 0)
    check("the meta layer that holds the answer key is stripped by default",
          set(META_DIRS) == {"audit", "project"})

    # --- selection honours the class filter and the default exclusion ---
    check("module_58 is excluded by default", "modules/module_58.md" in DEFAULT_EXCLUDED_FILES)
    check("the blind-class list is exactly the four unscored classes",
          set(BLIND_CLASSES) == {"attribution_role", "citation", "data_source", "mechanism"})
    check("every blind class exists in the seed corpus",
          set(BLIND_CLASSES) <= {k for _c, _d, k in SEED_COMMITS})

    if n_fail:
        print(f"SELFTEST_FAIL prepare_audit_arena {n_fail} of {n_ok + n_fail} assertions failed")
        return 1
    print(f"SELFTEST_OK prepare_audit_arena {n_ok}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("prepare", help="build a seeded arena + sealed answer key")
    p.add_argument("--classes", default=",".join(BLIND_CLASSES))
    p.add_argument("--exclude-file", action="append")
    p.add_argument("--include-file", action="append")
    p.add_argument("--only-hunk", action="append",
                   help="repeatable; 'modules/module_58.md' or 'modules/module_80.md#1'")
    p.add_argument("--controls", type=int, default=6)
    p.add_argument("--max-avoid-hits", type=int, default=0,
                   help="max nitrogen-term hits allowed in a CONTROL file (default 0)")
    p.add_argument("--no-avoid", action="store_true",
                   help="disable the term filter on control selection")
    p.add_argument("--arena-root")
    p.add_argument("--key-root")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-meta", action="store_true",
                   help="do NOT strip audit/ and project/ (debugging only — they "
                        "contain the answer key and the build will then abort)")
    p.add_argument("--allow-leaks", action="store_true",
                   help="build even if the blindness scan finds the answer in the "
                        "corpus. The resulting number is not a measurement.")

    s = sub.add_parser("score", help="score an auditor's findings against the key")
    s.add_argument("--key", required=True)
    s.add_argument("--findings", required=True)
    s.add_argument("--window", type=int, default=5)
    s.add_argument("--out")

    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.cmd == "prepare":
        return cmd_prepare(args)
    if args.cmd == "score":
        return cmd_score(args)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
