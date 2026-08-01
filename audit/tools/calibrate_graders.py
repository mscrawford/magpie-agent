#!/usr/bin/env python3
"""Calibrate the Phase 1A grading layer against a NON-LLM ground truth.

The Phase 1A propagation numbers rested on a single Opus grader per trap, and a
blind 3-way re-adjudication later overturned 11 of 21 of its verdicts. That
established the grader was unreliable but did NOT quantify it, because the
adjudicators are themselves LLMs -- comparing them to each other measures
agreement, not accuracy.

This script supplies the missing anchor. `check_answer_identifiers.py` decides one
subclass of falsehood MECHANICALLY (an answer that names a module directory,
realization, path or identifier that does not exist). On that subclass the truth
is not a judgment call, so a grader that scores such an answer CORRECT is
committing a measurable false negative.

What this reports is therefore a FLOOR on grader error, over the fabrication
subclass only -- not an overall FNR. Answers can be false in ways the mechanical
check cannot see; those are counted in neither the numerator nor the denominator.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_answer_identifiers import (  # noqa: E402
    FABRICATION_KINDS,
    Corpus,
    check_answer,
)

# Grader outcomes that assert the answer did NOT carry a falsehood to the user.
CLEAN_VERDICTS = {"CORRECT", "NOT_ELICITED", "ABSTAINED"}


def load_grader_verdicts(data_dir: Path) -> dict[tuple, dict]:
    """{(rep, trap, cell): verdict} across every rep file on disk."""
    out: dict[tuple, dict] = {}
    for f in sorted(data_dir.glob("arena_1a_rep*_grader.json")):
        d = json.loads(f.read_text())
        rep = d["rep"]
        for res in d.get("results", []):
            for cell, v in (res.get("scored") or {}).items():
                out[(rep, res["trap"], cell)] = v
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True, help="extracted answers JSON")
    ap.add_argument("--root", default=".", help="magpie root")
    ap.add_argument("--data", default="magpie-agent/audit/data")
    ap.add_argument("--json", help="write the joined table here")
    a = ap.parse_args()

    corpus = Corpus(Path(a.root).resolve())
    rows = json.loads(Path(a.answers).read_text())
    rows = [r for r in rows if r.get("trap") and r.get("cell") and r.get("answer")]
    verdicts = load_grader_verdicts(Path(a.data))

    joined = []
    for r in rows:
        findings = check_answer(r["answer"], corpus)
        fabs = [f for f in findings if f["kind"] in FABRICATION_KINDS]
        v = verdicts.get((r["rep"], r["trap"], r["cell"]))
        joined.append({
            "rep": r["rep"], "trap": r["trap"], "cell": r["cell"], "arm": r["arm"],
            "phrasing": r["phrasing"],
            "fabrications": [{"kind": f["kind"], "token": f["token"]} for f in fabs],
            "citation_imprecise": [
                f["token"] for f in findings if f["kind"] == "citation_imprecise"
            ],
            "grader_outcome": (v or {}).get("outcome"),
            "context": [f["context"] for f in fabs],
        })

    n = len(joined)
    with_fab = [j for j in joined if j["fabrications"]]
    graded = [j for j in with_fab if j["grader_outcome"]]
    missed = [j for j in graded if j["grader_outcome"] in CLEAN_VERDICTS]

    print(f"answers analysed                     : {n}")
    print(f"answers with >=1 FABRICATED identifier: {len(with_fab)}")
    print(f"  ...of which the grader also scored  : {len(graded)}")
    print(f"  ...scored CLEAN despite fabrication : {len(missed)}  <-- measured false negatives")
    if graded:
        print(f"  floor on grader FNR (fabrication subclass): "
              f"{len(missed)}/{len(graded)} = {100*len(missed)/len(graded):.0f}%")

    print("\n-- every answer containing a mechanically certain fabrication --")
    for j in sorted(with_fab, key=lambda x: (x["rep"], x["trap"], x["cell"])):
        toks = ", ".join(f"{f['kind']}={f['token']}" for f in j["fabrications"])
        flag = "MISS" if j["grader_outcome"] in CLEAN_VERDICTS else "    "
        print(f"  {flag} rep{j['rep']} {j['trap']} {j['cell']} ({j['arm']:<7}) "
              f"grader={str(j['grader_outcome']):<12} {toks}")

    if a.json:
        Path(a.json).write_text(json.dumps(joined, indent=1))
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
