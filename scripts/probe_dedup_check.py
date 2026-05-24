#!/usr/bin/env python3
"""Check a flywheel round-design doc against the probe-candidate dedup ledger.

Usage:
    python3 scripts/probe_dedup_check.py <round_design.md> [--round N]
    python3 scripts/probe_dedup_check.py < round_design.md [--round N]

Stderr-warn on any probe in the round design that names a ledger-tracked
GAMS module, variable, equation, parameter, or realization. Calibration
anchors (G1, G2) are exempt — their repetition IS the test.

Ported from magpie-preproc-agent (2026-05-13 origin); adapted for the
magpie-agent's GAMS domain. The preproc version matched madrat tokens
(calc*/read*/full*); this version matches MAgPIE naming conventions
(vm_*/pm_*/v<N>_*/p<N>_*/s<N>_*/q<N>_*/module_XX/realization_<month><year>).

USAGE CONTEXT: invoked during round-design step in every flywheel round
(per audit/flywheel_rubric.md §5 "Round composition"). The round
design doc typically lives at `~/.claude/plans/magpie-agent-rounds/round_N_design.md`
(outside the agent tree, to prevent probe contamination).

Exit code 0 always (warn-only signal; designer judges and may override
by explicitly classifying the question as a `regression_anchor`).
"""
import argparse
import json
import re
import sys
from pathlib import Path

LEDGER = Path(__file__).parent.parent / "audit" / "probe_dedup_ledger.json"

# Match MAgPIE GAMS tokens that appear in the ledger.
# - Modules: module_14, module_52, module_14_yields
# - Variables/params: vm_land, pm_interest, s42_pumping, c56_pollutant_prices,
#                     v35_hvarea, p32_max_aff_area_glo, sm_fix_SSP2, im_growing_stock,
#                     pcm_AEI, pm_carbon_density_ac
# - Equations: q14_yield_crop, q10_land_area
# - Realizations: managementcalib_aug19, fbask_jul23, sticky_feb18, cellpool_aug16,
#                 nlp_ipopt, all_sectors_aug13
GAMS_NAME_RE = re.compile(
    r"`?\b("
    r"module_\d{2}(?:_[a-z_]+)?"
    r"|(?:vm|pm|im|fm|pcm|sm|v\d+|p\d+|f\d+|i\d+|s\d+|c\d+)_[a-zA-Z][\w]*"
    r"|q\d+_[a-zA-Z][\w]*"
    r"|[a-z][a-z_]{2,}_(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{2}"
    r"|nlp_ipopt|all_sectors_aug13|managementcalib_aug19"
    r")\b`?"
)
# Question block header — adjust to your round-design markdown convention.
# Defaults: ## Q1, ### Q1, or **Q1:** style.
Q_HEADER_RE = re.compile(r"^(?:#{1,4}\s*|\*\*)\s*Q(\d+)", re.IGNORECASE)


def load_off_limits(current_round):
    """Return the set of GAMS names off-limits at this round.

    Calibration-exempt entries are NOT off-limits.
    Numeric retirement_eligible_after > current_round → off-limits.
    Numeric retirement_eligible_after <= current_round → rotated back in.
    """
    if not LEDGER.exists():
        print(
            f"WARN — ledger not found at {LEDGER}; no filtering applied.",
            file=sys.stderr,
        )
        return set(), {}
    data = json.loads(LEDGER.read_text())
    off_limits = set()
    metadata = {}
    for entry in data.get("off_limits", []):
        ret = entry.get("retirement_eligible_after")
        name = entry["name"]
        if ret == "calibration-exempt":
            continue
        if isinstance(ret, int) and ret <= current_round:
            continue
        off_limits.add(name)
        metadata[name] = entry
    return off_limits, metadata


def scan(text, off_limits, metadata):
    """Walk markdown, tracking current Q, find ledger-tracked names."""
    hits = []
    current_q = None
    for line in text.splitlines():
        m = Q_HEADER_RE.match(line.strip())
        if m:
            current_q = m.group(1)
            continue
        for name_match in GAMS_NAME_RE.finditer(line):
            name = name_match.group(1)
            if name in off_limits:
                snippet = line.strip()[:120]
                source = metadata.get(name, {}).get("source_files", [""])
                source_short = source[0][:60] if source else ""
                hits.append((current_q, name, snippet, source_short))
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("input", nargs="?", help="Round design markdown (or stdin)")
    ap.add_argument(
        "--round", type=int, default=99,
        help="Current round number (controls rotation; default 99 = all off-limits)",
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="Just verify the script and ledger load correctly")
    args = ap.parse_args()

    off_limits, metadata = load_off_limits(args.round)

    if args.dry_run:
        print(f"OK — ledger loaded; {len(off_limits)} off-limits names at round {args.round}.")
        print(f"Sample: {sorted(off_limits)[:5]}")
        sys.exit(0)

    if args.input:
        text = Path(args.input).read_text()
    else:
        text = sys.stdin.read()

    hits = scan(text, off_limits, metadata)

    if not hits:
        print(
            f"OK — no ledger-tracked names in probes (round {args.round}).",
            file=sys.stderr,
        )
        sys.exit(0)

    print(
        f"WARN — {len(hits)} probe(s) name ledger-tracked items at round {args.round}:",
        file=sys.stderr,
    )
    for q, name, snippet, source in hits:
        qlabel = f"Q{q}" if q else "?"
        print(f"  {qlabel}: `{name}` ({source}) — {snippet}", file=sys.stderr)
    print(
        "\nOptions:",
        file=sys.stderr,
    )
    print(
        "  (a) rotate to a fresh probe candidate (consult audit/flywheel_rubric.md §6 for archetypes)",
        file=sys.stderr,
    )
    print(
        "  (b) classify the question as `regression_anchor` in round_N_design.md and document",
        file=sys.stderr,
    )
    print(
        "      the recognition signal being tested. See flywheel_rubric.md §5 + §8.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
