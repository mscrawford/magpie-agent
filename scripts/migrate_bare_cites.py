#!/usr/bin/env python3
"""Migrate bare-basename .gms citations to full-path form in non-module docs.

A bare cite like `equations.gms:20` in cross-module / helper / reference docs is
ambiguous (which module's equations.gms?). This script infers the module from
paragraph context, looks up the module's default realization from
config/default.cfg, and rewrites the citation as
`modules/NN_name/REAL/equations.gms:20`.

Scope: non-module docs (cross_module/, core_docs/, reference/, agent/helpers/,
AGENT.md, README.md). Module docs (modules/module_NN.md and _notes.md) are
exempt — their context is unambiguous.

Algorithm:
  1. For each bare cite, scan ±8 lines for a module mention (Module NN, M14,
     modules/14_*). Take the closest mention.
  2. Look up default realization via config/default.cfg.
  3. Verify the resulting path resolves to a real file.
  4. Rewrite.

Usage:
  migrate_bare_cites.py                    # dry-run
  migrate_bare_cites.py --apply            # write changes
  migrate_bare_cites.py --doc PATH         # limit to a single doc
  migrate_bare_cites.py --verbose          # print every skip reason
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_default_realizations import (  # noqa: E402
    get_module_name_to_number,
    get_default_realizations,
)

AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_DIR = AGENT_DIR.parent

# Bare-basename cite: file.gms:N NOT preceded by `modules/...` or `core/`
BARE_RE = re.compile(r"(?<!\w)(?<![./])(?P<file>\w+)\.gms:(?P<line>\d+)")

# Module mention in context.
# Branches (in priority order at match time, but we just take the closest):
#   "Module 14" / "module 14" / "M14"
#   "modules/14_yields"
#   bare directory name "14_yields" / "10_land" (used in table cells)
MODULE_MENTION_RE = re.compile(
    r"\b(?:Module|module|M)[\s_]?0?(\d{2})\b"
    r"|modules/(\d+)_"
    r"|\b(\d{2})_[a-z][a-z_]*\b"
)

# Var-prefix module hint within the SAME line as the citation: a numbered
# identifier like `s15_exo_diet`, `q52_emis`, `c15_EAT_scen`. Note that `vm_`/
# `pm_`/`im_`/`pcm_` and similar do NOT include the module number, so they
# don't disambiguate.
VAR_PREFIX_SAME_LINE_RE = re.compile(
    r"\b(?:v|p|f|i|s|c|q|ic|ov|oq|pc)(\d{2})_[A-Za-z]",
    re.IGNORECASE,
)

SCOPE_PATTERNS = [
    "cross_module/*.md", "core_docs/*.md", "reference/*.md",
    "agent/helpers/*.md", "AGENT.md", "README.md",
]


def build_default_realization_map() -> dict[str, str]:
    """module_number_str -> default_realization_dir."""
    name_to_num = get_module_name_to_number()
    defaults = get_default_realizations()
    num_to_realization: dict[str, str] = {}
    for switch_name, realization in defaults.items():
        if switch_name in name_to_num:
            num_to_realization[name_to_num[switch_name]] = realization
    return num_to_realization


def build_num_to_dir_map() -> dict[str, str]:
    """module_number_str -> 'NN_name' directory name."""
    name_to_num = get_module_name_to_number()
    out: dict[str, str] = {}
    for name, num in name_to_num.items():
        out[num] = f"{num}_{name}"
    return out


def candidate_modules_for_cite(
    text_lines: list[str],
    cite_lineno: int,
    search_back: int = 15,
    search_forward: int = 5,
) -> list[str]:
    """Return module-number candidates ordered by proximity to the cite.

    Sources (combined into a single ordered list, deduped):
      1. MODULE_MENTION_RE within ±N lines of the cite (wider window catches
         cases where the only hint is a section header or following paragraph).
      2. Var-prefix `<letter><NN>_` on the SAME line as the cite (case-
         insensitive — `c15_EAT_scen` counts as a hint).

    Caller iterates the list, picking the first candidate whose constructed
    full path resolves to a real file (self-correcting against wrong proximity
    matches).
    """
    start = max(0, cite_lineno - search_back - 1)
    end = min(len(text_lines), cite_lineno + search_forward)
    block_lines = text_lines[start:end]
    block = "\n".join(block_lines)

    # Compute cite character offset within the block (start of cite_lineno)
    cite_offset_in_block = sum(
        len(line) + 1 for line in text_lines[start : cite_lineno - 1]
    )

    scored: list[tuple[int, str]] = []
    for m in MODULE_MENTION_RE.finditer(block):
        proximity = abs(m.start() - cite_offset_in_block)
        mod = m.group(1) or m.group(2) or m.group(3)
        if mod:
            scored.append((proximity, mod))

    # Same-line var-prefix as a secondary signal (always proximity 0)
    same_line = text_lines[cite_lineno - 1]
    for m in VAR_PREFIX_SAME_LINE_RE.finditer(same_line):
        scored.append((0, m.group(1)))

    scored.sort()
    seen: set[str] = set()
    out: list[str] = []
    for _, mod in scored:
        if mod not in seen:
            out.append(mod)
            seen.add(mod)
    return out


def construct_full_path(
    module_num: str,
    gms_basename: str,
    real_map: dict[str, str],
    dir_map: dict[str, str],
) -> str | None:
    """Return modules/NN_name/REAL/file.gms if it exists on disk; else None."""
    realization = real_map.get(module_num)
    module_dir = dir_map.get(module_num)
    if not realization or not module_dir:
        return None
    full = f"modules/{module_dir}/{realization}/{gms_basename}.gms"
    if not (MAGPIE_DIR / full).is_file():
        return None
    return full


def collect_replacements(
    doc_path: Path,
    real_map: dict[str, str],
    dir_map: dict[str, str],
    verbose: bool,
) -> tuple[list[tuple], dict[str, int]]:
    """Return list of (line_no, start_in_line, end_in_line, old, new) and a stats dict."""
    rel = str(doc_path.relative_to(AGENT_DIR))
    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    replacements = []
    stats = {"converted": 0, "skipped_no_module": 0, "skipped_no_path": 0}
    for i, line in enumerate(lines, 1):
        for m in BARE_RE.finditer(line):
            before_in_line = line[: m.start()]
            if "modules/" in before_in_line[-40:] or "core/" in before_in_line[-10:]:
                continue
            cite_str = m.group(0)
            gms_basename = m.group("file")
            cited_line = m.group("line")
            candidates = candidate_modules_for_cite(lines, i)
            if not candidates:
                stats["skipped_no_module"] += 1
                if verbose:
                    print(f"  SKIP no-module: {rel}:{i} {cite_str}")
                continue
            # Try each candidate in proximity order; keep the first whose path resolves.
            full_path = None
            tried = []
            for cand in candidates:
                tried.append(cand)
                p = construct_full_path(cand, gms_basename, real_map, dir_map)
                if p:
                    full_path = p
                    break
            if not full_path:
                stats["skipped_no_path"] += 1
                if verbose:
                    print(f"  SKIP no-path: {rel}:{i} {cite_str} "
                          f"(tried modules {tried}, {gms_basename}.gms missing in all)")
                continue
            new_cite = f"{full_path}:{cited_line}"
            replacements.append((i, m.start(), m.end(), cite_str, new_cite))
            stats["converted"] += 1
    return replacements, stats


def apply_replacements(doc_path: Path, replacements: list[tuple]) -> None:
    """Write replacements back to doc_path."""
    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    has_trailing_nl = text.endswith("\n")
    lines = text.splitlines()
    by_line: dict[int, list[tuple]] = defaultdict(list)
    for r in replacements:
        by_line[r[0]].append(r)
    for line_no, repls in by_line.items():
        # Process rightmost first so earlier offsets stay valid.
        repls.sort(key=lambda r: -r[1])
        line = lines[line_no - 1]
        for _, start, end, _, new_text in repls:
            line = line[:start] + new_text + line[end:]
        lines[line_no - 1] = line
    out = "\n".join(lines)
    if has_trailing_nl:
        out += "\n"
    doc_path.write_text(out, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    ap.add_argument("--doc", help="Limit to a single doc (relative to AGENT_DIR)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    real_map = build_default_realization_map()
    dir_map = build_num_to_dir_map()

    if not real_map or not dir_map:
        print(f"⚠️  config/default.cfg or modules/ unavailable at {MAGPIE_DIR}", file=sys.stderr)
        return 1

    docs_to_process: list[Path] = []
    if args.doc:
        docs_to_process = [AGENT_DIR / args.doc]
    else:
        for pat in SCOPE_PATTERNS:
            docs_to_process.extend(sorted(AGENT_DIR.glob(pat)))

    grand_stats = {"converted": 0, "skipped_no_module": 0, "skipped_no_path": 0}
    per_doc_summary: list[tuple[str, int, int, int]] = []

    for doc_path in docs_to_process:
        if not doc_path.is_file():
            continue
        replacements, stats = collect_replacements(doc_path, real_map, dir_map, args.verbose)
        if not replacements and not any(stats.values()):
            continue
        rel = str(doc_path.relative_to(AGENT_DIR))
        per_doc_summary.append((rel, stats["converted"],
                                stats["skipped_no_module"], stats["skipped_no_path"]))
        for k in grand_stats:
            grand_stats[k] += stats[k]
        if replacements and args.apply:
            apply_replacements(doc_path, replacements)
        elif replacements and not args.verbose:
            print(f"\n{rel}: {len(replacements)} proposed conversions")
            for r in replacements[:6]:
                print(f"  line {r[0]}: {r[3]}  ->  {r[4]}")
            if len(replacements) > 6:
                print(f"  ... and {len(replacements) - 6} more")

    print()
    print("=== Summary ===")
    print(f"{'Doc':55s} {'conv':>5} {'no_mod':>7} {'no_path':>8}")
    for rel, conv, no_mod, no_path in per_doc_summary:
        print(f"  {rel:53s} {conv:>5} {no_mod:>7} {no_path:>8}")
    print(f"  {'TOTAL':53s} {grand_stats['converted']:>5} "
          f"{grand_stats['skipped_no_module']:>7} {grand_stats['skipped_no_path']:>8}")
    print()
    if not args.apply:
        print("Dry-run. Re-run with --apply to write changes.")
    else:
        print("Changes written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
