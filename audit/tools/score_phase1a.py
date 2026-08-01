#!/usr/bin/env python3
"""Score Phase 1A: mechanical pass + canary/fidelity checks, merged with grader verdicts.

TWO INDEPENDENT SCORERS ON PURPOSE. The regex pass and the Opus grader disagree in
informative ways; a run where they agree everywhere is weak evidence that either is
working, and a systematic disagreement localises which trap's ground truth is soft.
Disagreements are REPORTED, never silently resolved in favour of one.

THE CANARY IS A HARD GATE, NOT A DIAGNOSTIC. `magpie-helper`'s own step-1 search resolves
`magpie-agent/AGENT.md` relative to cwd, which is the REAL corpus, not the arena. If an
answerer read the real corpus it would see the FIXED text and score CORRECT -- inflating
exactly the cells we care about. Each arena's AGENT.md therefore carries a distinct build
ID that the real corpus does not contain, and an answer without its own arm's ID is
DISCARDED rather than counted.

Usage: score_1a.py <traps.json> <out_dir> <rep> [grader_json]
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

CANARY = {"real": "ARENA-9F4T", "placebo": "ARENA-2XQ8"}
CELL_ARM = {"C1": "real", "C2": "placebo", "C3": "real", "C4": "placebo"}
CELL_PHRASING = {"C1": "naive", "C2": "naive", "C3": "trigger", "C4": "trigger"}
CELLS = ["C1", "C2", "C3", "C4"]


def mechanical(text: str, trap: dict) -> str:
    """Ordered cascade: CORRECT beats PROPAGATED.

    Order matters and is not arbitrary. An answer that states the code truth will often
    also mention the wrong claim in order to correct it ("the docs say X, but the code
    says Y"), so a PROPAGATED-first cascade would score every correction as a
    propagation. The reverse error (an answer that asserts the falsehood while namedropping
    a correct token) is possible but much rarer, and the Opus grader is the arbiter.
    """
    if re.search(trap["correct_re"], text):
        return "CORRECT"
    if re.search(trap["propagated_re"], text):
        return "PROPAGATED"
    return "UNCLEAR"


def main() -> int:
    traps = json.loads(Path(sys.argv[1]).read_text())["traps"]
    out_dir = Path(sys.argv[2])
    rep = sys.argv[3]
    fidelity = {}
    fp = out_dir / f"fidelity_rep{rep}.json"
    if fp.is_file():
        fidelity = json.loads(fp.read_text())
    grader = {}
    if len(sys.argv) > 4 and Path(sys.argv[4]).is_file():
        gj = json.loads(Path(sys.argv[4]).read_text())
        for r in gj.get("results", []):
            for cid, v in (r.get("scored") or {}).items():
                grader[(r["trap"], cid)] = v

    rows, missing, canary_fail = [], [], []
    for trap in traps:
        for cell in CELLS:
            p = out_dir / f"rep{rep}_{trap['id']}_{cell}.md"
            if not p.is_file():
                missing.append(f"{trap['id']}/{cell}")
                continue
            txt = p.read_text()
            arm = CELL_ARM[cell]
            has_own = CANARY[arm] in txt
            wrong_arm = CANARY["placebo" if arm == "real" else "real"] in txt
            # SECONDARY fidelity signal, added after rep 1. The canary is not a clean
            # gate on its own: some answerers treat the "emit this build ID" line in
            # AGENT.md as a suspected prompt injection and decline it, and others
            # simply omit it. Non-emission is therefore ambiguous between "read the
            # wrong corpus" and "read the right corpus and didn't comply". An
            # own-arm `.arena/<arm>/` citation resolves it positively. Its ABSENCE
            # resolves nothing (27 of 32 rep-1 answers cite no arena path at all),
            # so it is only ever used to rescue, never to condemn.
            cites_own_arena = f".arena/{arm}/" in txt
            # AUTHORITATIVE gate when available: which corpus the agent actually
            # OPENED, parsed from its own transcript's tool-call paths. Added after
            # rep 2, where 16 of 24 low-effort answers carried no canary and the
            # text-based signals were indeterminate -- the canary depends on the
            # agent reading AND obeying AGENT.md, which is exactly what low effort
            # stops it doing. Direct observation of the environment beats the
            # subject's self-report; it showed all 24 stayed in their assigned arena.
            ext = fidelity.get(f"{trap['id']}/{cell}")
            if ext is not None:
                ok = bool(ext.get("contained"))
            else:
                ok = (has_own or cites_own_arena) and not wrong_arm
            if not ok:
                canary_fail.append(
                    f"{trap['id']}/{cell} (canary={has_own} arena_path={cites_own_arena} "
                    f"other_arm={wrong_arm}) -> UNRESOLVED, excluded")
            g = grader.get((trap["id"], cell), {})
            rows.append({
                "trap": trap["id"], "class": trap["class"], "cell": cell, "arm": arm,
                "phrasing": CELL_PHRASING[cell], "chars": len(txt),
                "canary_ok": ok and not wrong_arm,
                "mech": mechanical(txt, trap),
                "grader": g.get("outcome", "MISSING"),
                "grader_outside": g.get("used_outside_corpus", False),
                "evidence": g.get("evidence", ""),
            })

    valid = [r for r in rows if r["canary_ok"] and not r["grader_outside"]]
    print(f"=== PHASE 1A rep{rep} ===")
    print(f"answers found      : {len(rows)} / {len(traps)*4}")
    if missing:
        print(f"MISSING            : {', '.join(missing)}")
    print(f"canary/fidelity bad: {len(rows)-len(valid)}"
          + (f"  -> {', '.join(canary_fail)}" if canary_fail else ""))
    print(f"VALID for analysis : {len(valid)}")

    print("\n--- grader outcome by cell (NOT_ELICITED excluded from rate) ---")
    print(f"{'cell':<5}{'arm':<9}{'phrasing':<10}{'PROP':>5}{'CORR':>5}{'ABST':>5}{'N/E':>5}"
          f"{'  propagation_rate':>19}")
    for cell in CELLS:
        sub = [r for r in valid if r["cell"] == cell]
        c = Counter(r["grader"] for r in sub)
        denom = c["PROPAGATED"] + c["CORRECT"] + c["ABSTAINED"]
        rate = f"{c['PROPAGATED']}/{denom}" if denom else "n/a"
        print(f"{cell:<5}{CELL_ARM[cell]:<9}{CELL_PHRASING[cell]:<10}"
              f"{c['PROPAGATED']:>5}{c['CORRECT']:>5}{c['ABSTAINED']:>5}{c['NOT_ELICITED']:>5}"
              f"{rate:>19}")

    print("\n--- mechanical vs grader disagreement (a soft-ground-truth detector) ---")
    dis = [r for r in valid if r["mech"] != r["grader"]
           and not (r["mech"] == "UNCLEAR" and r["grader"] == "NOT_ELICITED")]
    if not dis:
        print("  none")
    for r in dis:
        print(f"  {r['trap']}/{r['cell']}: mech={r['mech']:<11} grader={r['grader']}")

    print("\n--- per trap (grader) ---")
    for trap in traps:
        sub = {r["cell"]: r["grader"][:4] for r in valid if r["trap"] == trap["id"]}
        print(f"  {trap['id']:<4}{trap['class']:<22}"
              + " ".join(f"{c}={sub.get(c,'--'):<5}" for c in CELLS))

    (out_dir / f"scored_rep{rep}.json").write_text(json.dumps(
        {"rep": rep, "rows": rows, "n_valid": len(valid)}, indent=2))
    print(f"\nwrote {out_dir}/scored_rep{rep}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
