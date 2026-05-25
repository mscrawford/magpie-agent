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
import datetime
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


def collect_probe_names_from_round(round_data):
    """Extract names that should enter the dedup ledger from a round entry.

    Rules (R25 follow-up implementation of validate-semantic.md Step 5c):
      - Skip regression-anchor questions (archetype=='regression_anchor' OR
        id matches *-G\\d). Their repetition is the test.
      - From each remaining question's modules_tested list:
          - int N      -> 'module_{N:02d}'  (canonical short form)
          - string s   -> slug of s (e.g. 'magpie4 helper' -> 'magpie4_helper')
      - Return de-duplicated set.
    """
    names = set()
    for q in round_data.get("questions", []):
        if q.get("archetype") == "regression_anchor":
            continue
        if re.match(r".*-G\d+$", q.get("id", "")):
            continue
        for m in q.get("modules_tested", []) or []:
            if isinstance(m, int):
                names.add(f"module_{m:02d}")
            elif isinstance(m, str):
                slug = re.sub(r"\W+", "_", m.strip().lower()).strip("_")
                if slug:
                    names.add(slug)
    return names


def append_round_to_ledger(round_num, names, ledger_path):
    """Append new probe names to the ledger and advance existing entries.

    For each name:
      - if in calibration_exempt -> skip
      - if absent from off_limits -> new entry, retirement_eligible_after = round_num + 3
      - if present with numeric retirement_eligible_after < round_num + 3 -> advance
      - if present with 'calibration-exempt' -> skip
      - if present with retirement_eligible_after >= round_num + 3 -> no-op

    Returns (added: list[str], updated: list[tuple[str, int, int]]).
    """
    if not ledger_path.exists():
        print(f"WARN — ledger missing at {ledger_path}; cannot append.", file=sys.stderr)
        return [], []
    d = json.loads(ledger_path.read_text())
    name_to_idx = {e["name"]: i for i, e in enumerate(d["off_limits"])}
    # calibration_exempt entries are like "module_14 (G1 anchor)" — take leading slug
    exempt = set()
    for label in d.get("calibration_exempt", []):
        slug = label.split(" ", 1)[0].strip()
        if slug:
            exempt.add(slug)

    added: list[str] = []
    updated: list[tuple[str, int, int]] = []
    today = datetime.date.today().isoformat()
    retire_after = round_num + 3

    for name in sorted(names):
        if name in exempt:
            continue
        if name in name_to_idx:
            entry = d["off_limits"][name_to_idx[name]]
            cur = entry.get("retirement_eligible_after")
            if cur == "calibration-exempt":
                continue
            if isinstance(cur, int) and cur < retire_after:
                entry["retirement_eligible_after"] = retire_after
                sf = entry.get("source_files", [])
                sf.append(f"R{round_num} (auto-appended)")
                entry["source_files"] = sf
                updated.append((name, cur, retire_after))
        else:
            entry = {
                "name": name,
                "type": "module" if name.startswith("module_") else "resource",
                "named_in": ["round_result"],
                "source_files": [f"R{round_num} (auto-appended)"],
                "first_named_at": today,
                "first_named_round": round_num,
                "retirement_eligible_after": retire_after,
            }
            d["off_limits"].append(entry)
            added.append(name)

    d["captured_at"] = today
    ledger_path.write_text(json.dumps(d, indent=2) + "\n")
    return added, updated


def auto_detect_next_round():
    """Read validation_rounds.json to find the next round number.

    Returns the next round number to design (latest + 1), or 0 if no rounds
    exist or the file can't be read. 0 keeps everything off-limits, which is
    the safe default — running the check on a stale "round 99" was the R5
    Cluster E bug (returned 0 off-limits because every numeric retirement
    value satisfied retirement_eligible_after <= 99).
    """
    val_path = Path(__file__).parent.parent / "audit" / "validation_rounds.json"
    if not val_path.exists():
        return 0
    try:
        data = json.loads(val_path.read_text())
        rounds = data.get("rounds", [])
        if rounds:
            return max(r.get("round", 0) for r in rounds) + 1
    except (json.JSONDecodeError, OSError):
        pass
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("input", nargs="?", help="Round design markdown (or stdin)")
    ap.add_argument(
        "--round", type=int, default=None,
        help="Round number being designed (controls which names have "
             "rotated back in). Default: auto-detect from "
             "audit/validation_rounds.json (latest + 1); falls back to 0 "
             "(all off-limits) if unavailable. R5 2026-05-24 fix replaces "
             "the prior broken default of 99 which rotated everything in.",
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="Just verify the script and ledger load correctly")
    ap.add_argument(
        "--append-from-round", type=int, metavar="N", default=None,
        help="Append probe names from round N (in validation_rounds.json) to "
             "the off-limits ledger. Sets retirement_eligible_after = N + 3 "
             "for new entries; advances existing entries' retirement_eligible_after "
             "if currently < N + 3. Skips calibration-exempt entries and regression-"
             "anchor questions (their repetition is the test). Default: pass an "
             "explicit N. Implements validate-semantic.md Step 5c (was previously "
             "warn-only).",
    )
    args = ap.parse_args()

    # --append-from-round runs without input/stdin; do that path first
    if args.append_from_round is not None:
        val_path = Path(__file__).parent.parent / "audit" / "validation_rounds.json"
        if not val_path.exists():
            print(f"ERROR — validation_rounds.json missing at {val_path}", file=sys.stderr)
            sys.exit(1)
        data = json.loads(val_path.read_text())
        target_round = next(
            (r for r in data.get("rounds", []) if r.get("round") == args.append_from_round),
            None,
        )
        if target_round is None:
            print(
                f"ERROR — round {args.append_from_round} not in validation_rounds.json",
                file=sys.stderr,
            )
            sys.exit(1)
        names = collect_probe_names_from_round(target_round)
        if not names:
            print(
                f"OK — round {args.append_from_round} has no non-regression probe names to append.",
                file=sys.stderr,
            )
            sys.exit(0)
        added, updated = append_round_to_ledger(args.append_from_round, names, LEDGER)
        print(
            f"R{args.append_from_round} ledger update: {len(added)} added, {len(updated)} retire-after advanced.",
            file=sys.stderr,
        )
        if added:
            print(f"  Added: {added}", file=sys.stderr)
        if updated:
            for n, old, new in updated:
                print(f"  Advanced: {n} {old} -> {new}", file=sys.stderr)
        sys.exit(0)

    if args.round is None:
        args.round = auto_detect_next_round()

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
