#!/usr/bin/env python3
"""refresh_aggregate_counts.py - update aggregate-count placeholders in docs.

Aggregate counts (e.g., "21 semantic-validation rounds", "445 bugs") live in
many AI-doc source files and drift on every flywheel round. This script reads
canonical values and updates HTML-comment-marked placeholders.

Marker format (round-tripable; markdown renders only the inner text):
    <!--count:KEY-->TEXT<!--/count-->

Example markers in source:
    Identified across <!--count:total_rounds-->21<!--/count--> rounds
    (<!--count:total_bugs_found-->445<!--/count--> bugs catalogued).

Canonical sources:
- audit/validation_rounds.json.cumulative_stats (rounds, bugs, dates)
- live validator output (variable/equation/citation/realization counts) by
  re-running the relevant checkers
- validate_consistency.sh (number of print_section calls = validator_checks)

Usage:
    python3 scripts/refresh_aggregate_counts.py            # update files
    python3 scripts/refresh_aggregate_counts.py --dry-run  # print diffs only
    python3 scripts/refresh_aggregate_counts.py --list     # show known keys
    python3 scripts/refresh_aggregate_counts.py --exclude-agent-md  # skip AGENT.md
                                                          # (refresh only non-deployed
                                                          #  docs; avoids forcing a
                                                          #  parent ../AGENT.md+CLAUDE.md
                                                          #  redeploy mid-work)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent

VALIDATION_JSON = AGENT_DIR / "audit" / "validation_rounds.json"
VALIDATE_SH = SCRIPT_DIR / "validate_consistency.sh"
BUG_TAXONOMY_MD = AGENT_DIR / "core_docs" / "Bug_Taxonomy.md"

# Files known to host aggregate-count markers. Add new files here as markers
# spread; absence of markers in a listed file is harmless.
TARGET_FILES = [
    AGENT_DIR / "AGENT.md",
    AGENT_DIR / "README.md",                                              # R6 E2
    AGENT_DIR / "agent" / "commands" / "validate-semantic.md",
    AGENT_DIR / "agent" / "commands" / "validate.md",
    AGENT_DIR / "agent" / "commands" / "validate-module.md",
    AGENT_DIR / "agent" / "commands" / "pipeline-audit.md",
    AGENT_DIR / "agent" / "commands" / "bootstrap.md",                    # R6 E2
    AGENT_DIR / "agent" / "commands" / "guide.md",                        # R6 E2
    AGENT_DIR / "agent" / "helpers" / "verifiers.md",
    AGENT_DIR / "agent" / "helpers" / "maintenance_protocol.md",
    AGENT_DIR / "agent" / "helpers" / "realization_selection.md",         # R6 E2
    AGENT_DIR / "agent" / "helpers" / "README.md",                        # R6 E2
    AGENT_DIR / "core_docs" / "Response_Guidelines.md",
    AGENT_DIR / "cross_module" / "circular_dependency_resolution.md",     # R6 E2
]

MARKER_RE = re.compile(r"<!--count:([a-z_]+)-->(.*?)<!--/count-->", re.DOTALL)


def load_canonical_counts() -> dict[str, str]:
    """Build the dict of canonical {key: str_value} for all known counts."""
    counts: dict[str, str] = {}

    # 1. validation_rounds.json -> cumulative_stats
    if VALIDATION_JSON.is_file():
        with VALIDATION_JSON.open() as f:
            data = json.load(f)
        stats = data.get("cumulative_stats", {})
        for key in (
            "total_rounds",
            "total_docs_validated",
            "module_docs_validated",
            "non_module_docs_validated",
            "total_bugs_found",
            "total_bugs_fixed",
            "validator_sub_checks",
            "last_validation_date",
        ):
            if key in stats:
                counts[key] = str(stats[key])
        # Latest round date string from the rounds list (most accurate)
        rounds = data.get("rounds", [])
        if rounds:
            counts["latest_round_id"] = str(rounds[-1].get("round", counts.get("total_rounds", "?")))
            if "date" in rounds[-1]:
                counts["last_validation_date"] = rounds[-1]["date"]

    # 2. validator_checks: count print_section calls in validate_consistency.sh
    if VALIDATE_SH.is_file():
        text = VALIDATE_SH.read_text()
        n = len(re.findall(r'print_section\s+"\d+/\d+"', text))
        counts["validator_checks"] = str(n)
        # Alias for clarity: distinguish main numbered checks from sub-checks
        counts["validator_main_checks"] = str(n)

    # 3. bug_taxonomy_patterns: count "### Pattern" headings in Bug_Taxonomy.md
    if BUG_TAXONOMY_MD.is_file():
        text = BUG_TAXONOMY_MD.read_text()
        n = len(re.findall(r'^### Pattern', text, re.MULTILINE))
        counts["bug_taxonomy_patterns"] = str(n)

    # 4. Live counts via the per-check scripts (run them in --summary-only where
    # supported; parse stdout). Wrapped in try/except so a broken script does
    # not corrupt the whole refresh run.
    counts.update(run_live_counts())

    # 5. R6 E1 — file-system-derived counts that don't need a separate check script.

    # Slash command count
    cmd_dir = AGENT_DIR / "agent" / "commands"
    if cmd_dir.is_dir():
        counts["n_commands"] = str(len(list(cmd_dir.glob("*.md"))))

    # Helper count (excluding README.md)
    helper_dir = AGENT_DIR / "agent" / "helpers"
    if helper_dir.is_dir():
        helpers = [p for p in helper_dir.glob("*.md") if p.name != "README.md"]
        counts["n_helpers"] = str(len(helpers))

    # Number of modules with multiple realizations (drives Step 1c trigger list)
    # MAgPIE source is at ../modules/ relative to AGENT_DIR
    modules_dir = AGENT_DIR.parent / "modules"
    if modules_dir.is_dir():
        n_multi = 0
        for m in sorted(modules_dir.iterdir()):
            if not m.is_dir() or not m.name[0].isdigit():
                continue
            realizations = [r for r in m.iterdir() if r.is_dir() and r.name != "include"]
            if len(realizations) > 1:
                n_multi += 1
        counts["n_modules_multi_realization"] = str(n_multi)

    # validation_rounds.json schema version
    if VALIDATION_JSON.is_file():
        with VALIDATION_JSON.open() as f:
            data = json.load(f)
        sv = data.get("metadata", {}).get("schema_version")
        if sv:
            counts["validation_schema_version"] = str(sv)

    # Aggregate doc word/line totals (excluding archive/cache)
    DOC_DIRS = [
        AGENT_DIR / "modules",
        AGENT_DIR / "core_docs",
        AGENT_DIR / "cross_module",
        AGENT_DIR / "reference",
        AGENT_DIR / "agent",
    ]
    total_words = 0
    total_lines = 0
    for d in DOC_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*.md"):
            if "archive" in p.parts:
                continue
            try:
                text = p.read_text()
            except Exception:
                continue
            total_words += len(text.split())
            total_lines += text.count("\n")
    # Round to nearest 1000 for stability — small edits shouldn't flap the marker
    counts["total_doc_words"] = f"~{round(total_words, -3):,}"
    counts["total_doc_lines"] = f"~{round(total_lines, -3):,}"

    # Number of pipeline-audit rounds run (for /pipeline-audit context)
    PIPELINE_JSON = AGENT_DIR / "audit" / "pipeline_audit_rounds.json"
    if PIPELINE_JSON.is_file():
        with PIPELINE_JSON.open() as f:
            data = json.load(f)
        counts["n_pipeline_audit_rounds"] = str(len(data.get("rounds", [])))

    return counts


def parse_int(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def run_live_counts() -> dict[str, str]:
    """Run the variable/equation/realization/citation checkers and harvest counts."""
    out: dict[str, str] = {}

    def run(cmd: list[str]) -> str:
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=120
            ).stdout
        except Exception:
            return ""

    # GAMS variables (Python script)
    out_text = run(["python3", str(SCRIPT_DIR / "check_gams_variables.py")])
    n = parse_int(out_text, r"\((\d+)/\d+ verified\)")
    if n:
        out["gams_variables_verified"] = n

    # GAMS equations
    out_text = run(["python3", str(SCRIPT_DIR / "check_gams_equations.py"), "--summary-only"])
    n = parse_int(out_text, r"\((\d+)/\d+ unique equations\)")
    if n:
        out["gams_equations_verified"] = n

    # GAMS realizations (module-scoped .py: output is "(61/127 references; module-scoped check)")
    out_text = run(["python3", str(SCRIPT_DIR / "check_gams_realizations.py"), "--summary-only"])
    n = parse_int(out_text, r"(\d+)/\d+ references")
    if n:
        out["gams_realizations_verified"] = n

    # File:line citations
    out_text = run(["bash", str(SCRIPT_DIR / "check_gams_citations.sh")])
    n = parse_int(out_text, r"(\d+)/\d+ valid")
    if n:
        out["file_line_citations_verified"] = n

    return out


def apply_markers(text: str, counts: dict[str, str]) -> tuple[str, list[tuple[str, str, str]]]:
    """Replace marker contents in `text` with current values.

    Returns (new_text, changes) where changes is [(key, old, new), ...].
    """
    changes: list[tuple[str, str, str]] = []

    def sub(m: re.Match) -> str:
        key = m.group(1)
        old = m.group(2)
        if key not in counts:
            return m.group(0)  # unknown key - leave alone (will be flagged)
        new = counts[key]
        if old != new:
            changes.append((key, old, new))
        return f"<!--count:{key}-->{new}<!--/count-->"

    return MARKER_RE.sub(sub, text), changes


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    show_list = "--list" in sys.argv
    exclude_agent = "--exclude-agent-md" in sys.argv

    counts = load_canonical_counts()

    if show_list:
        print("Known aggregate-count keys (current canonical values):")
        for k in sorted(counts):
            print(f"  {k:35s} = {counts[k]}")
        return 0

    total_files = 0
    total_changes = 0
    unknown_keys: set[str] = set()

    files = TARGET_FILES
    if exclude_agent:
        files = [p for p in TARGET_FILES if p.name != "AGENT.md"]
        print("(--exclude-agent-md: skipping AGENT.md to avoid a parent redeploy)")
    for path in files:
        if not path.is_file():
            continue
        original = path.read_text()
        updated, changes = apply_markers(original, counts)

        # Track any markers whose key is not in counts (so user knows to update)
        for m in MARKER_RE.finditer(original):
            if m.group(1) not in counts:
                unknown_keys.add(m.group(1))

        if changes:
            total_files += 1
            total_changes += len(changes)
            rel = path.relative_to(AGENT_DIR)
            print(f"\n{rel}: {len(changes)} update(s)")
            for key, old, new in changes:
                print(f"  {key}: '{old}' -> '{new}'")
            if not dry_run:
                path.write_text(updated)

    if total_changes == 0:
        print("All aggregate-count markers are already up to date.")
    else:
        verb = "would update" if dry_run else "updated"
        print(f"\n{verb} {total_changes} marker(s) across {total_files} file(s).")

    if unknown_keys:
        print(f"\nWarning: {len(unknown_keys)} marker key(s) not in canonical sources:")
        for k in sorted(unknown_keys):
            print(f"  - {k}")
        print("Add them to load_canonical_counts() or remove the markers.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
