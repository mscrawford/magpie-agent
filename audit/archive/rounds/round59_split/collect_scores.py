#!/usr/bin/env python3
"""R59 score collector.

Extracts the trailing machine-readable JSON block from each audits/{ID}.md and
reports PER-ARM statistics.

BINDING (PLAN.md §0.2): Arm A and Arm B scores are NEVER pooled into one mean.
Arm A measures "did R58's fixes hold" (its docs were rewritten hours before the
probe); Arm B measures capability on never-depth-audited hubs. A pooled mean
would be meaningless and would repeat the 9.52 error. This script therefore has
no code path that averages the two arms together.

doc_quality_mean (rubric §4): mean over questions EXCLUDING those whose bugs are
exclusively `answerer_confabulation`. Questions with any doc_error /
doc_error_answerer_beat_it stay IN. Zero-bug questions stay IN.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDITS = HERE / "audits"

ARM_A = ["A1", "A2", "A3", "A4", "A5"]
ARM_B = ["B1", "B2", "B3", "B4", "B5"]
ANCHORS = ["G1", "G3"]


def load(pid):
    f = AUDITS / f"{pid}.md"
    if not f.exists():
        return None
    txt = f.read_text()
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", txt, re.S)
    if not blocks:
        return {"id": pid, "_error": "no json block"}
    try:
        return json.loads(blocks[-1])
    except json.JSONDecodeError as e:
        return {"id": pid, "_error": f"unparseable json: {e}"}


def arm_stats(label, ids, data):
    rows = [data[i] for i in ids if data.get(i) and "_error" not in data[i]]
    missing = [i for i in ids if not data.get(i)]
    broken = [i for i in ids if data.get(i) and "_error" in data[i]]
    if not rows:
        return {"label": label, "n": 0, "missing": missing, "broken": broken}

    scores = [r.get("score", 0) for r in rows]
    raw_mean = sum(scores) / len(scores)

    # doc_quality subset: drop questions whose bugs are ALL answerer_confabulation
    keep = []
    for r in rows:
        bugs = r.get("bugs", []) or []
        causes = {b.get("root_cause") for b in bugs}
        if bugs and causes <= {"answerer_confabulation"}:
            continue
        keep.append(r)
    dq = sum(r.get("score", 0) for r in keep) / len(keep) if keep else None

    return {
        "label": label,
        "n": len(rows),
        "raw_mean": round(raw_mean, 3),
        "doc_quality_mean": round(dq, 3) if dq is not None else None,
        "n_doc_quality": len(keep),
        "critical": sum(r.get("critical", 0) for r in rows),
        "major": sum(r.get("major", 0) for r in rows),
        "minor": sum(r.get("minor", 0) for r in rows),
        "informational": sum(r.get("informational", 0) for r in rows),
        "n_latent": sum(len(r.get("doc_errors_latent", []) or []) for r in rows),
        "scores": {r["id"]: r.get("score") for r in rows},
        "missing": missing,
        "broken": broken,
    }


def main():
    ids = ARM_A + ARM_B + ANCHORS
    data = {i: load(i) for i in ids}

    out = {
        "arm_A_fix_verification": arm_stats("Arm A (fix-verification)", ARM_A, data),
        "arm_B_cold_hubs": arm_stats("Arm B (central, never-depth-audited)", ARM_B, data),
        "regression_anchors": arm_stats("Regression anchors", ANCHORS, data),
        "_pooling": "REFUSED BY DESIGN (PLAN.md §0.2) - arms measure different things",
    }

    # anchors also carry drift
    out["regression_anchors"]["drift"] = {
        i: data[i].get("drift_observed")
        for i in ANCHORS
        if data.get(i) and "_error" not in data[i]
    }

    # every bug + latent, flattened, for the fix phase
    fixables = []
    for i in ids:
        r = data.get(i)
        if not r or "_error" in r:
            continue
        for b in (r.get("bugs") or []):
            if b.get("root_cause") in ("doc_error", "doc_error_answerer_beat_it"):
                fixables.append({"probe": i, "kind": "bug", **b})
        for b in (r.get("doc_errors_latent") or []):
            fixables.append({"probe": i, "kind": "latent", **b})
    out["fixables_doc_errors"] = fixables
    out["n_fixables"] = len(fixables)

    print(json.dumps(out, indent=1))
    done = [i for i in ids if data.get(i) and "_error" not in data[i]]
    print(f"\n# collected {len(done)}/12: {' '.join(sorted(done))}", file=sys.stderr)


if __name__ == "__main__":
    main()
