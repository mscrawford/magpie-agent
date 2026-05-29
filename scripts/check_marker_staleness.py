#!/usr/bin/env python3
"""check_marker_staleness.py - ADVISORY: flag <!--count:KEY-->VALUE<!--/count-->
markers that have drifted from canonical values, WITHOUT rewriting any file.

Why advisory + read-only: the markers live in AGENT.md (and command/helper docs).
AGENT.md deploys to ../AGENT.md + ../CLAUDE.md (validate_consistency.sh Check 10), so
auto-refreshing AGENT.md would force a redeploy into the parent MAgPIE repo. This check
only SURFACES drift. Remediate when convenient with:
    python3 scripts/refresh_aggregate_counts.py                  # all files (rewrites AGENT.md -> redeploy)
    python3 scripts/refresh_aggregate_counts.py --exclude-agent-md   # non-deployed docs only (parent-safe)

Scope: only the STABLE keys derived from audit/validation_rounds.json cumulative_stats
+ metadata.schema_version + the validate_consistency.sh print_section count. The volatile
live counts (gams_*_verified) and the ~-rounded word/line totals are intentionally NOT
checked - they re-derive on every refresh and would flap.

Exit 0 always (advisory). `--self-test` runs an in-memory positive control and exits.
"""
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
VALIDATION_JSON = AGENT_DIR / "audit" / "validation_rounds.json"
VALIDATE_SH = SCRIPT_DIR / "validate_consistency.sh"

# Reuse the marker format + target-file list from the refresh tool (single source of truth).
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from refresh_aggregate_counts import MARKER_RE, TARGET_FILES
except Exception:  # pragma: no cover - fallback keeps the check runnable in isolation
    MARKER_RE = re.compile(r"<!--count:([a-z_]+)-->(.*?)<!--/count-->", re.DOTALL)
    TARGET_FILES = [AGENT_DIR / "AGENT.md"]

# Only these keys are checked: stable, deterministically derived, and meaningful to a
# reader (rounds/bugs/checks/schema). Volatile keys (gams_*_verified, total_doc_words,
# total_doc_lines) are deliberately excluded.
STABLE_KEYS = {
    "total_rounds", "total_docs_validated", "module_docs_validated",
    "non_module_docs_validated", "total_bugs_found", "total_bugs_fixed",
    "validator_sub_checks", "validator_checks", "validator_main_checks",
    "validation_schema_version", "latest_round_id", "last_validation_date",
}


def stable_canonical():
    """Compute canonical values for the STABLE keys only (cheap: no live checkers)."""
    counts = {}
    if VALIDATION_JSON.is_file():
        d = json.loads(VALIDATION_JSON.read_text())
        st = d.get("cumulative_stats", {})
        for k in ("total_rounds", "total_docs_validated", "module_docs_validated",
                  "non_module_docs_validated", "total_bugs_found", "total_bugs_fixed",
                  "validator_sub_checks", "last_validation_date"):
            if k in st:
                counts[k] = str(st[k])
        rounds = d.get("rounds", [])
        if rounds:
            counts["latest_round_id"] = str(rounds[-1].get("round", "?"))
            if "date" in rounds[-1]:
                counts["last_validation_date"] = rounds[-1]["date"]
        sv = d.get("metadata", {}).get("schema_version")
        if sv:
            counts["validation_schema_version"] = str(sv)
    if VALIDATE_SH.is_file():
        n = len(re.findall(r'print_section\s+"\d+/\d+"', VALIDATE_SH.read_text()))
        counts["validator_checks"] = str(n)
        counts["validator_main_checks"] = str(n)
    return counts


def find_stale(canonical, target_files):
    """Return [(relpath, key, found, expected), ...] for drifted STABLE markers."""
    stale = []
    for path in target_files:
        if not path.is_file():
            continue
        for m in MARKER_RE.finditer(path.read_text()):
            key, val = m.group(1), m.group(2)
            if key not in STABLE_KEYS or key not in canonical:
                continue
            if val != canonical[key]:
                try:
                    rel = str(path.relative_to(AGENT_DIR))
                except ValueError:
                    rel = str(path)
                stale.append((rel, key, val, canonical[key]))
    return stale


def _self_test():
    import tempfile
    failures = []
    canonical = {"total_rounds": "27", "total_bugs_found": "508"}
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "d.md"
        p.write_text(
            "rounds <!--count:total_rounds-->1<!--/count--> and "
            "<!--count:total_bugs_found-->508<!--/count--> bugs and "
            "<!--count:total_doc_words-->~9,000<!--/count-->\n")
        keys = {s[1] for s in find_stale(canonical, [p])}
        if "total_rounds" not in keys:
            failures.append("did not flag stale total_rounds (1 vs 27)")
        if "total_bugs_found" in keys:
            failures.append("wrongly flagged a matching marker (total_bugs_found)")
        if "total_doc_words" in keys:
            failures.append("should skip non-stable key total_doc_words")
    if failures:
        print("SELF-TEST FAILED:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        return 1
    print("SELF-TEST OK - flags drifted stable markers; skips matching + non-stable keys.",
          file=sys.stderr)
    return 0


def main():
    if "--self-test" in sys.argv:
        return _self_test()
    canonical = stable_canonical()
    stale = find_stale(canonical, TARGET_FILES)
    if not stale:
        print("Aggregate-count markers (stable keys): all current.")
        return 0
    print(f"ADVISORY: {len(stale)} stale aggregate-count marker(s) vs cumulative_stats:")
    for rel, key, found, exp in stale:
        print(f"  {rel}: {key} = {found} (canonical {exp})")
    print("Remediate when convenient (advisory; does not block the gate):")
    print("  python3 scripts/refresh_aggregate_counts.py              # all (rewrites AGENT.md -> redeploy)")
    print("  python3 scripts/refresh_aggregate_counts.py --exclude-agent-md   # non-deployed docs only (parent-safe)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
