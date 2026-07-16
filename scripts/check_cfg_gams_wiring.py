#!/usr/bin/env python3
"""Check 38: `cfg$gms$` scalar keys that have no GAMS counterpart (silent no-ops).

Bug class (R58, found while auditing module_70): `config/default.cfg` line 2197
declares `cfg$gms$s70_feed_subst_functional_form <- 1`, but no such scalar exists
anywhere in the GAMS tree -- the real identifier is `s70_subst_functional_form`.
A user who sets that key gets NO effect and NO warning: the sigmoid feed-substitution
fader is simply unreachable from the config surface.

WHY NOTHING ELSE CATCHES IT:
  * `check_config` validates a run's cfg against `default.cfg` itself, so a key that
    is wrong in BOTH is consistent and passes.
  * `manipulateConfig` is a regex substitution with no existence check, so writing an
    unmatched key into `full.gms` is a silent no-op rather than an error.
  * GAMS never sees the key at all, so no compile error is possible.
The failure is therefore invisible end-to-end: the only observable is that the switch
does nothing, which looks like a modelling result rather than a bug.

SCOPE: scalar/switch-shaped keys only -- `cfg$gms$s<NN>_*` and `cfg$gms$c<NN>_*`.
Realization switches (`cfg$gms$costs <- "default"`) are deliberately EXCLUDED: they
name a directory, not a GAMS identifier, and are already covered by Check 19.

DIRECTION: this check is one-way by design. It flags cfg keys with no GAMS
identifier. It does NOT flag GAMS scalars absent from cfg -- that is legitimate and
common (most module scalars are not exposed as config switches). Reporting those
would bury the real signal under ~hundreds of false positives.

PRESENCE, not wiring: a key counts as present if its exact token appears ANYWHERE in
the GAMS tree, including a comment. This is deliberately permissive -- the aim is to
catch names that exist nowhere at all (typos / renames that left cfg behind), with a
near-zero false-positive rate. A key that appears only in a comment would pass here;
that is an accepted recall gap, not an oversight.

Advisory: always exits 0. Findings surface as warnings via the validator.

Usage: python3 scripts/check_cfg_gams_wiring.py [--self-test] [--summary-only]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
# Honour the MAGPIE_DIR env override (the convention documented in
# check_gams_variables.py) so this checker can be pointed at a pinned worktree --
# and so its own self-test can drive it over a synthetic tree.
MAGPIE_DIR = (
    Path(os.environ["MAGPIE_DIR"]).resolve()
    if os.environ.get("MAGPIE_DIR")
    else AGENT_DIR.parent
)

# cfg$gms$s12_interest_lic <- 0.1   /   cfg$gms$c30_bioen_water <- "rainfed"
CFG_SCALAR_RE = re.compile(r"^\s*cfg\$gms\$([sc]\d+_[A-Za-z0-9_]+)\s*<-")
# Any scalar/switch-shaped identifier token in GAMS source.
GAMS_TOKEN_RE = re.compile(r"\b[sc]\d+_[A-Za-z0-9_]+\b")


def collect_cfg_scalar_keys(cfg_path: Path) -> list[tuple[str, int]]:
    """Return [(key_name, line_no)] for scalar-shaped cfg$gms$ keys.

    Skips commented-out lines so a disabled key is not reported as dead.
    """
    if not cfg_path.is_file():
        return []
    out = []
    for i, line in enumerate(cfg_path.read_text(errors="ignore").split("\n"), 1):
        if line.lstrip().startswith("#"):
            continue
        m = CFG_SCALAR_RE.match(line)
        if m:
            out.append((m.group(1), i))
    return out


def collect_gams_tokens(magpie_dir: Path) -> set[str]:
    """Return every scalar/switch-shaped identifier appearing in the GAMS tree."""
    tokens: set[str] = set()
    roots = [magpie_dir / "modules", magpie_dir / "core"]
    files: list[Path] = []
    for r in roots:
        if r.is_dir():
            files.extend(r.rglob("*.gms"))
    main = magpie_dir / "main.gms"
    if main.is_file():
        files.append(main)
    for p in files:
        try:
            tokens |= set(GAMS_TOKEN_RE.findall(p.read_text(errors="ignore")))
        except Exception:
            continue
    return tokens


def near_miss(key: str, tokens: set[str]) -> list[str]:
    """Best-effort 'did you mean' for a dead key, by shared module prefix + stem overlap."""
    prefix = key.split("_", 1)[0]
    stem_words = set(key.split("_")[1:])
    scored = []
    for t in tokens:
        if not t.startswith(prefix + "_"):
            continue
        tw = set(t.split("_")[1:])
        overlap = len(stem_words & tw)
        if overlap >= 2:
            scored.append((overlap, t))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [t for _, t in scored[:3]]


def find_dead_keys(keys, tokens):
    """Return [(key, line, near_misses)] for cfg keys absent from the GAMS tree."""
    return [(k, ln, near_miss(k, tokens)) for k, ln in keys if k not in tokens]


def _scan_only() -> int:
    """Internal: drive the REAL collectors over MAGPIE_DIR and emit JSON.

    Lets the self-test exercise the actual ground-truth extractors against a real
    tree on disk instead of stubbing them -- the defect R57/W0a found across the
    battery, and which this checker must not reproduce on day one.
    """
    keys = collect_cfg_scalar_keys(MAGPIE_DIR / "config" / "default.cfg")
    tokens = collect_gams_tokens(MAGPIE_DIR)
    dead = find_dead_keys(keys, tokens)
    print(json.dumps({
        "n_keys": len(keys),
        "n_tokens": len(tokens),
        "dead": [{"key": k, "line": ln, "near_miss": nm} for k, ln, nm in dead],
    }))
    return 0


def _write_fixture(root: Path) -> None:
    """Synthetic tree replicating the REAL R58 bug, plus the negative controls.

    The dead key is `s70_feed_subst_functional_form` against a wired
    `s70_subst_functional_form` -- i.e. an exact replica of the live defect at
    config/default.cfg:2197, not an invented pair. Per the project's convention,
    a positive control anchored on a real historical bug is worth more than a
    synthetic one: it proves the checker catches THE thing it was built for.
    """
    def w(rel: str, text: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    w("main.gms", "* synthetic\n")
    w("config/default.cfg",
      'cfg$gms$livestock <- "fbask_jan16"           # realization switch: must be IGNORED\n'
      "cfg$gms$s70_wired_switch <- 1                # wired: exists in GAMS\n"
      "cfg$gms$s70_feed_subst_functional_form <- 1  # DEAD: replica of the real bug\n"
      "cfg$gms$s70_subst_functional_form <- 1       # wired: the near-miss target\n"
      "# cfg$gms$s70_commented_out <- 1             # commented: must be IGNORED\n"
      'cfg$gms$c70_dead_char <- "x"                 # DEAD char-shaped switch\n')
    w("modules/70_livestock/fbask_jan16/input.gms",
      "  s70_wired_switch  Some switch (1) / 1 /\n"
      "  s70_subst_functional_form  Fader form (1) / 1 /\n")
    w("core/sets.gms", "* nothing relevant\n")


def self_test() -> int:
    """Positive control: the dead key MUST be flagged; the wired ones must NOT be.

    Drives the REAL extractors over a synthetic tree via a MAGPIE_DIR-overridden
    subprocess. Does NOT stub them.
    """
    checks: list[tuple[str, bool]] = []

    def check(name: str, cond: bool) -> None:
        checks.append((name, bool(cond)))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_fixture(root)
        env = dict(os.environ, MAGPIE_DIR=str(root))
        p = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--_scan-only"],
            capture_output=True, text=True, env=env, timeout=120,
        )
        if p.returncode != 0:
            print(f"SELF-TEST FAIL: subprocess rc={p.returncode}\n{p.stderr[:400]}", file=sys.stderr)
            return 1
        data = json.loads(p.stdout)
        dead = {d["key"] for d in data["dead"]}

        # POSITIVE control: the REAL bug's shape must be caught.
        check("flags the real-bug replica (s70_feed_subst_functional_form)",
              "s70_feed_subst_functional_form" in dead)
        check("flags a dead char-shaped key", "c70_dead_char" in dead)
        # NEGATIVE controls: these must NOT be flagged.
        check("does NOT flag a wired key", "s70_wired_switch" not in dead)
        check("does NOT flag the near-miss target (it is wired)",
              "s70_subst_functional_form" not in dead)
        check("does NOT flag a commented-out key", "s70_commented_out" not in dead)
        check("does NOT flag a realization switch (not a GAMS identifier)",
              not any(d.startswith("livestock") for d in dead))
        # Extractors actually ran (guards the vacuous-green failure mode: an empty
        # key list or empty token set would make 'no dead keys' meaningless).
        check("cfg collector is non-vacuous (4 scalar keys in the fixture)",
              data["n_keys"] == 4)
        check("gams token collector is non-vacuous", data["n_tokens"] >= 2)
        # Near-miss suggestion. NOTE: asserted for real, with no escape clause.
        # An earlier draft of this line read `... or nm.get(k) == [] or True`, which
        # passes unconditionally -- the exact vacuous-control anti-pattern this
        # checker's own class of bug is about. If the near-miss heuristic regresses,
        # this must go red.
        nm = {d["key"]: d["near_miss"] for d in data["dead"]}
        check("suggests the correct near-miss for the real-bug replica",
              nm.get("s70_feed_subst_functional_form") == ["s70_subst_functional_form"])

    failures = [n for n, c in checks if not c]
    for n, c in checks:
        print(f"  {'ok  ' if c else 'FAIL'} {n}", file=sys.stderr)
    if failures:
        print(f"SELF-TEST FAILED ({len(failures)}/{len(checks)})", file=sys.stderr)
        return 1
    print(f"SELF-TEST OK - {len(checks)} assertions: dead cfg keys flagged; wired, "
          "commented and realization switches not.", file=sys.stderr)
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--_scan-only" in args:
        return _scan_only()
    if "--self-test" in args:
        rc = self_test()
        if rc == 0:
            print("SELFTEST_OK check_cfg_gams_wiring")
        return rc

    cfg_path = MAGPIE_DIR / "config" / "default.cfg"
    if not cfg_path.is_file() or not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS codebase not found at {MAGPIE_DIR} - skipping cfg-wiring check")
        return 0

    keys = collect_cfg_scalar_keys(cfg_path)
    tokens = collect_gams_tokens(MAGPIE_DIR)
    if not keys or not tokens:
        print("  cfg wiring: nothing collected (cfg or GAMS tree empty?) — skipped")
        return 0
    dead = find_dead_keys(keys, tokens)

    summary_only = "--summary-only" in args
    if dead and not summary_only:
        print(f"  Dead cfg$gms$ keys (set them and NOTHING happens): {len(dead)}")
        for k, ln, nm in dead:
            hint = f"  → did you mean: {', '.join(nm)}" if nm else ""
            print(f"    config/default.cfg:{ln}  {k}{hint}")
    print(f"  cfg-wiring: {len(dead)} dead of {len(keys)} scalar keys checked "
          f"({len(tokens)} GAMS identifiers indexed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
