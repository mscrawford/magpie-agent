#!/usr/bin/env python3
"""Mechanical updater (component 5b of S2, the PR-integration pipeline).

Reads a 5a impact-report JSON (from `pr_doc_impact.py --output ...`) and applies
all "mechanical"-tier changes. Currently that's exclusively `line_shift` entries
— citations whose cited line number needs to follow the GAMS diff.

Confidence tiers higher than mechanical (semantic, manual) are left to 5c or to
manual review. 5b never commits and never pushes; it leaves a dirty tree for the
operator to inspect with `git diff` before deciding.

After the bare-cite migration (commit e982a76), 5b can apply line shifts
uniformly across all docs — no special-case logic for cross-module bare cites.

Usage:
  pr_mechanical_update.py --input REPORT.json [--apply] [--verbose]

Without --apply, runs in dry-run mode and prints what would change.

The post-apply validator run reports pass/fail; non-zero exit if the validator
finds new errors after the rewrites (would indicate the line shifts broke
something).

Range citations are supported: `path:START-END` updates both endpoints. The
end is shifted using the same cumulative-hunk logic, then capped at the new
file's EOF.

EOF safety: if the rewritten start is past the new file's EOF (typically
because the original cite was already stale, pointing past OLD EOF), the
rewrite is skipped and logged as `skipped-eof`.

Testing caveat: when testing against an OLD PR commit (e.g., re-running on
PR #876's c7731e234), the validator runs against the CURRENT working tree,
which may have additional drift since the test commit. EOF errors in this
case reflect that drift, not 5b bugs. In production, 5b runs immediately
after a PR merges and the working tree matches the PR head.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent


def shift_old_to_new(hunks: list[dict], old_line: int) -> int:
    """Project an OLD-file line to its NEW-file line via cumulative hunk deltas.

    Mirrors 5a's `from_line <= cited_line` summation. For lines inside a
    replacement hunk, this is approximate (treats them as if before any hunks
    that don't include them); 5a's anchor convention deliberately avoids
    naming such lines.
    """
    return old_line + sum(h["delta"] for h in hunks if h["from_line"] <= old_line)


def collect_actions(report: dict) -> dict[str, list[dict]]:
    """Walk the report; return per-doc list of shift entries to apply.

    Each entry carries the parent change's `hunks` and `new_file_line_count`
    so the rewriter can update range endpoints and enforce EOF bounds.
    """
    by_doc: dict[str, list[dict]] = defaultdict(list)
    for change in report.get("changes", []):
        if change.get("type") != "line_shift":
            continue
        in_file = change["in_file"]
        hunks = change.get("hunks", [])
        new_eof = change.get("new_file_line_count")
        for ad in change.get("affected_docs", []):
            if ad.get("confidence") != "mechanical":
                continue
            doc_rel = ad["doc"]
            for s in ad.get("shifts", []):
                by_doc[doc_rel].append({
                    "in_file": in_file,
                    "hunks": hunks,
                    "new_eof": new_eof,
                    "doc_line": s["doc_line"],
                    "cited_line": s["cited_line"],
                    "suggested_line": s["suggested_line"],
                })
    return by_doc


def rewrite_doc(
    doc_rel: str,
    shifts: list[dict],
    apply: bool,
    verbose: bool,
) -> list[dict]:
    """Apply shifts to a single doc. Returns list of action records (one per matched cite).

    A cite is matched in two flavors:
      1. Full path: `<in_file>:<cited_line>` — preferred.
      2. Bare basename: `<file>.gms:<cited_line>` — fallback, only valid in the
         module's own doc per the 5a contract (post-migration; we trust 5a to
         only emit bare shifts where this is safe).

    The regex requires a word boundary after cited_line so we don't substitute
    `:12` inside `:123`. Range syntax (`:45-52`) is preserved — only the start
    is rewritten. Range-end staleness is a known follow-up (see plan).
    """
    doc_path = AGENT_DIR / doc_rel
    if not doc_path.is_file():
        if verbose:
            print(f"WARN: doc not found: {doc_rel}", file=sys.stderr)
        return []

    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    has_trailing_nl = text.endswith("\n")
    lines = text.splitlines()

    # Process per-doc-line so multiple shifts on the same line are batched.
    by_doc_line: dict[int, list[dict]] = defaultdict(list)
    for s in shifts:
        by_doc_line[s["doc_line"]].append(s)

    actions: list[dict] = []
    for line_no, line_shifts in sorted(by_doc_line.items()):
        if line_no > len(lines):
            if verbose:
                print(f"WARN: {doc_rel}:{line_no} beyond EOF (len={len(lines)})",
                      file=sys.stderr)
            continue
        line = lines[line_no - 1]
        for s in line_shifts:
            in_file = s["in_file"]
            cited = s["cited_line"]
            suggested = s["suggested_line"]
            hunks = s["hunks"]
            new_eof = s.get("new_eof")
            file_basename = Path(in_file).stem  # e.g. "preloop"

            # EOF safety: if suggested start is past the new file's EOF, the
            # original cite was stale (pointed past OLD EOF) and the shift
            # cannot reliably project it. Skip with a warning.
            if new_eof is not None and suggested > new_eof:
                if verbose:
                    print(f"  SKIP {doc_rel}:{line_no} {in_file}:{cited} -> :{suggested} "
                          f"(past EOF, file has {new_eof} lines; pre-existing stale cite)",
                          file=sys.stderr)
                actions.append({
                    "doc": doc_rel, "doc_line": line_no,
                    "old_cite": f"{in_file}:{cited}",
                    "new_cite": None,
                    "kind": "skipped-eof",
                })
                continue

            # Build regexes that handle both single-line and range citations.
            # Range: <path>:<start>-<end> — update both endpoints.
            # Single: <path>:<start> not followed by `-<digit>`.
            #
            # Use a single regex with optional range capture so we update in
            # one substitution per form.
            def make_rewriter(path_prefix: str):
                pattern = re.compile(
                    re.escape(path_prefix)
                    + r":(?P<start>\d+)(?:-(?P<end>\d+))?\b"
                )
                # Pre-condition: only match when start == cited
                def repl(m: re.Match) -> str:
                    if int(m.group("start")) != cited:
                        return m.group(0)
                    end = m.group("end")
                    new_start = str(suggested)
                    if end is not None:
                        end_old = int(end)
                        end_new = shift_old_to_new(hunks, end_old)
                        if new_eof is not None and end_new > new_eof:
                            end_new = new_eof
                        return f"{path_prefix}:{new_start}-{end_new}"
                    return f"{path_prefix}:{new_start}"
                return pattern, repl

            # Try full path first.
            full_pat, full_repl = make_rewriter(in_file)
            new_line, n = full_pat.subn(full_repl, line)
            if n > 0 and new_line != line:
                actions.append({
                    "doc": doc_rel, "doc_line": line_no,
                    "old_cite": f"{in_file}:{cited}",
                    "new_cite": f"{in_file}:{suggested}",
                    "kind": "full-path",
                })
                line = new_line
                continue

            # Bare-basename fallback. The negative lookbehind prevents matching
            # within a full path (already handled above).
            bare_pat = re.compile(
                r"(?<!/)" + re.escape(file_basename)
                + r"\.gms:(?P<start>\d+)(?:-(?P<end>\d+))?\b"
            )
            def bare_repl(m: re.Match) -> str:
                if int(m.group("start")) != cited:
                    return m.group(0)
                end = m.group("end")
                new_start = str(suggested)
                if end is not None:
                    end_old = int(end)
                    end_new = shift_old_to_new(hunks, end_old)
                    if new_eof is not None and end_new > new_eof:
                        end_new = new_eof
                    return f"{file_basename}.gms:{new_start}-{end_new}"
                return f"{file_basename}.gms:{new_start}"

            new_line, n = bare_pat.subn(bare_repl, line)
            if n > 0 and new_line != line:
                actions.append({
                    "doc": doc_rel, "doc_line": line_no,
                    "old_cite": f"{file_basename}.gms:{cited}",
                    "new_cite": f"{file_basename}.gms:{suggested}",
                    "kind": "bare",
                })
                line = new_line
                continue

            if verbose:
                print(f"  NO MATCH {doc_rel}:{line_no} for {in_file}:{cited}",
                      file=sys.stderr)

        lines[line_no - 1] = line

    if apply and actions:
        out = "\n".join(lines)
        if has_trailing_nl:
            out += "\n"
        doc_path.write_text(out, encoding="utf-8")
    return actions


def run_validator() -> tuple[int, str]:
    """Run validate_consistency.sh and return (exit_code, stdout)."""
    result = subprocess.run(
        ["bash", str(SCRIPT_DIR / "validate_consistency.sh")],
        capture_output=True, text=True, cwd=AGENT_DIR,
    )
    return result.returncode, result.stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="5a JSON report")
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--skip-validator", action="store_true",
                    help="Skip the post-apply validator run (debug only)")
    args = ap.parse_args()

    try:
        report = json.loads(Path(args.input).read_text())
    except Exception as e:
        print(f"Failed to read report: {e}", file=sys.stderr)
        return 1

    by_doc = collect_actions(report)
    if not by_doc:
        print("No mechanical updates to apply.")
        return 0

    all_actions: list[dict] = []
    for doc_rel in sorted(by_doc):
        all_actions.extend(rewrite_doc(doc_rel, by_doc[doc_rel], args.apply, args.verbose))

    # Per-doc summary
    by_doc_acts: dict[str, list[dict]] = defaultdict(list)
    for a in all_actions:
        by_doc_acts[a["doc"]].append(a)

    print(f"=== Mechanical updates ({len(all_actions)} cites across {len(by_doc_acts)} docs) ===")
    for doc, acts in sorted(by_doc_acts.items()):
        print(f"\n{doc}: {len(acts)} updates")
        for a in acts[:5]:
            print(f"  line {a['doc_line']}: {a['old_cite']} -> {a['new_cite']}")
        if len(acts) > 5:
            print(f"  ... and {len(acts) - 5} more")

    # Coverage: shifts attempted vs matched
    attempted = sum(len(s) for s in by_doc.values())
    matched = len(all_actions)
    print(f"\nCoverage: {matched}/{attempted} shifts matched and applied"
          f"{' (dry-run; nothing written)' if not args.apply else ''}")

    if args.apply and not args.skip_validator:
        print("\nRunning validator...")
        rc, out = run_validator()
        for line in out.splitlines():
            if any(tag in line for tag in ("Total checks:", "✓ Passed:", "⚠️", "❌")):
                # Strip ANSI color codes for readability
                clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
                print(f"  {clean}")
        if rc != 0:
            print("\n❌ Validator reported errors after rewrite. Inspect with `git diff`.")
            return 1
        print("\n✅ Validator clean. Inspect with `git diff` before committing.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
