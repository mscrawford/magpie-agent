#!/usr/bin/env python3
"""MEASUREMENT PROBE (throwaway) — how would a module-set checker behave?

Answers, with numbers rather than assertion:
  1. How many EXHAUSTIVE set claims ("**Depends on**: Modules 10, 29, 30")
     exist in the corpus? That is the `attribution_set` shape, 0/5 in the
     seeded-bug benchmark.
  2. Under D1 / D2 / D3, how many phantoms and omissions would each produce?
  3. What survives as DEFINITION-ROBUST while the Provides-To ruling is open?

ARCHITECTURE — per [[feedback_probe_is_unverified_code]] rule 1, the FINDER is
the production one. `check_bindability.scan_doc` already locates attribution-
context lines that name >=1 module and bind NO interface var, with its fence /
negation / historical / hedge / allowlist filter layer applied. Re-implementing
that regex minus the filters is failure mode 1 in that memory (17 phantoms vs
the real checker's 0). This probe only adds ONE thing on top: a narrowing test
for whether the line is an EXHAUSTIVE set claim rather than a partial mention.

Not a checker. Prints a table; changes nothing.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AGENT_DIR / "scripts"))

import check_attribution_omissions as cao  # noqa: E402
import check_bindability as cb  # noqa: E402

# The ONE thing not already in production: an EXHAUSTIVE set claim, i.e. a
# bolded field label whose value IS the whole set. "**Depends on**: Modules 10,
# 29, 30" claims completeness; "- Module 31 (Pasture): pasture carbon" does not.
# Only exhaustive claims can be checked for OMISSION.
SET_LABEL_RE = re.compile(
    r"^\s*[-*]?\s*\*\*\s*(Provides\s+to|Depends\s+on|Receives\s+from|"
    r"Feeds\s+into|Downstream|Upstream)\s*\*\*", re.I)
OUT_LABELS = {"provides to", "feeds into", "downstream"}


def build_defs(role):
    """owner/writers/readers -> per-module D1, D2, D3 (out, in) sets."""
    out = {k: defaultdict(set) for k in ("D1", "D2", "D3")}
    inn = {k: defaultdict(set) for k in ("D1", "D2", "D3")}
    for _var, r in role.items():
        owner = r["declared_in"]
        writers, readers = r["populated_by"], r["read_by"]
        srcs = {"D1": set(writers),
                "D2": {owner} if owner else set(),
                "D3": set(writers) | ({owner} if owner else set())}
        for rd in readers:
            for k, ss in srcs.items():
                for s in ss:
                    if s != rd:
                        out[k][s].add(rd)
                        inn[k][rd].add(s)
    return out, inn


def norm_role():
    """Ground truth via the PRODUCTION dump, not a reimplementation.

    `build_role_map()` returns {var: {modnum: {"READ","POPULATE"}}} — a DIFFERENT
    shape from the `--dump-rolemap` JSON. Reading `declared_in`/`populated_by`
    off it silently yields empty sets, which reads as "every claimed module is a
    phantom" (118 of them, first run of this probe). Call the real CLI instead;
    `declared_in` in particular comes from build_producer_map(), not the role map.
    """
    import json
    import subprocess
    r = subprocess.run([sys.executable, str(AGENT_DIR / "scripts" /
                        "check_attribution_omissions.py"), "--dump-rolemap"],
                       cwd=str(AGENT_DIR), capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise SystemExit(f"FATAL: --dump-rolemap failed: {r.stderr[:300]}")
    raw = json.loads(r.stdout)
    # TRAP: the dump MIXES key types in one object. `declared_in` is a module
    # DIRECTORY NAME ("10_land"); `populated_by`/`read_by` are 2-digit NUMBERS
    # ("10"). Comparing them uniformly silently yields owner-set = 0 for every
    # module (caught here only by the M32 D2=6 cross-check). Normalise to number.
    def _num(x):
        return x.split("_", 1)[0] if x else None
    return {v: {"declared_in": _num(d["declared_in"]),
                "populated_by": set(d["populated_by"]),
                "read_by": set(d["read_by"])} for v, d in raw.items()}


def collect_claims():
    """Exhaustive set claims, found via the PRODUCTION finder + one filter."""
    allow = cb.load_allowlist()
    claims = []
    for md in sorted((AGENT_DIR / "modules").glob("module_[0-9][0-9].md")):
        rel = f"modules/{md.name}"
        text = md.read_text()
        lines = text.splitlines()
        found, _bindable, _unb, _sup = cb.scan_doc(text, rel, allow)
        subj = md.stem.split("_")[1]
        for f in found:
            line = lines[f["line"] - 1]
            m = SET_LABEL_RE.match(line)
            if not m:
                continue
            label = re.sub(r"\s+", " ", m.group(1)).strip().lower()
            claimed = set(f["modules"]) - {subj}
            if not claimed:
                continue
            claims.append({
                "file": rel, "line": f["line"], "subj": subj, "label": label,
                "dir": "out" if label in OUT_LABELS else "in",
                "claimed": claimed, "hedged": f["hedged"],
                "text": f["row"],
            })
    return claims


def controls(claims, role, out, inn) -> bool:
    """POSITIVE + NEGATIVE control. A probe's 'clean' is unlicensed without both."""
    ok = True
    # GROUND-TRUTH control — the one that would have caught the shape bug that
    # made run 1 report 118 phantoms. An EMPTY truth set makes every claimed
    # module look like a phantom, and the failure is silent.
    vl = role.get("vm_land", {})
    if not vl.get("read_by") or not vl.get("populated_by"):
        print(f"CONTROL FAIL (ground truth): vm_land readers={sorted(vl.get('read_by', []))} "
              f"writers={sorted(vl.get('populated_by', []))} — role map did not load")
        ok = False
    else:
        print(f"control+ : vm_land writers={len(vl['populated_by'])} "
              f"readers={len(vl['read_by'])} (role map non-empty)")
    # CROSS-CHECK against an INDEPENDENT record: audit/interface_role_definitions.md
    # states M32 provides-to counts D1=16, D2=6, D3=17. If my derivation cannot
    # reproduce a number computed in a separate session, one of us is wrong.
    got = tuple(len(out[k]["32"]) for k in ("D1", "D2", "D3"))
    if got == (16, 6, 17):
        print(f"control+ : M32 provides-to D1/D2/D3 = {got} matches the "
              f"independently-recorded 16/6/17")
    else:
        print(f"CONTROL FAIL (cross-check): M32 D1/D2/D3 = {got}, "
              f"definitions doc records (16, 6, 17)")
        ok = False
    if len({tuple(sorted(out[k]["32"])) for k in ("D1", "D2", "D3")}) == 1:
        print("CONTROL FAIL: D1/D2/D3 identical for M32 — definitions collapsed")
        ok = False
    # POSITIVE: the finder must locate real set claims in the live corpus.
    if not claims:
        print("CONTROL FAIL (positive): finder returned ZERO set claims.")
        ok = False
    else:
        print(f"control+ : finder located {len(claims)} set claims (non-vacuous)")
    # POSITIVE 2: the exact pre-fix module_59 shape must classify correctly.
    probe = ("**Depends on**: Modules 10 (land), 30 (croparea), 29 (cropland).")
    m = SET_LABEL_RE.match(probe)
    nums = cao._mod_nums(cao._debacktick(probe))
    if not m or nums != {"10", "29", "30"}:
        print(f"CONTROL FAIL (positive2): module_59 pre-fix shape -> "
              f"match={bool(m)} nums={sorted(nums)}")
        ok = False
    else:
        print("control+ : module_59 pre-fix line parses as in/{10,29,30}")
    # NEGATIVE: a partial mention must NOT be read as an exhaustive claim.
    part = "- Module 31 (Pasture): Pasture carbon stocks"
    if SET_LABEL_RE.match(part):
        print("CONTROL FAIL (negative): partial mention read as exhaustive")
        ok = False
    else:
        print("control- : partial bullet correctly NOT an exhaustive claim")
    # CROSS-CHECK: direction from the label vs the production direction picker.
    # POLARITY: the picker answers "do the LISTED modules read or populate the
    # var?". "**Provides to**: Module 11" -> the listed module READs -> that is
    # my "out". So picker READ <-> out, picker POPULATE <-> in. Getting this
    # backwards (first version did) makes every correct line look like a
    # disagreement — 15 of 15, which is what tipped it off.
    dis, cmp_n = 0, 0
    for c in claims:
        deb = cao._debacktick(c["text"])
        rt, pt = cao.READ_TRIGGER_RE.search(deb), cao.POP_TRIGGER_RE.search(deb)
        d = cao._pick_direction(rt, pt, cao._first_module_pos(deb))
        if d == "UNKNOWN":
            continue  # "Depends on"/"Receives from" carry no trigger verb
        cmp_n += 1
        if (d == "READ") != (c["dir"] == "out"):
            dis += 1
    if dis:
        print(f"CONTROL FAIL (cross-check): {dis}/{cmp_n} direction disagreements")
        ok = False
    else:
        print(f"control+ : direction agrees with the production picker on "
              f"{cmp_n}/{cmp_n} comparable claims")
    return ok


def main() -> int:
    role = norm_role()
    out, inn = build_defs(role)
    claims = collect_claims()
    print("=== CONTROLS ===")
    if not controls(claims, role, out, inn):
        print("\nFATAL: controls failed; numbers below are NOT trustworthy.")
        return 2

    files = {c["file"] for c in claims}
    print(f"\n=== EXHAUSTIVE SET CLAIMS: {len(claims)} across {len(files)} docs ===")
    by_dir = defaultdict(int)
    for c in claims:
        by_dir[c["dir"]] += 1
    print(f"    provides-to (out): {by_dir['out']}   depends-on (in): {by_dir['in']}")

    print(f"\n{'def':5s} {'claims w/ phantom':>18s} {'claims w/ omission':>19s}"
          f" {'phantom mods':>13s} {'omitted mods':>13s}")
    for k in ("D1", "D2", "D3"):
        ph_c = om_c = ph_m = om_m = 0
        for c in claims:
            truth = (out[k] if c["dir"] == "out" else inn[k])[c["subj"]]
            ph, om = c["claimed"] - truth, truth - c["claimed"]
            if ph:
                ph_c += 1; ph_m += len(ph)
            if om:
                om_c += 1; om_m += len(om)
        print(f"{k:5s} {ph_c:18d} {om_c:19d} {ph_m:13d} {om_m:13d}")

    print("\n=== DEFINITION-ROBUST BAND (safe while the ruling is OPEN) ===")
    print("  phantom  := claimed module is in NO definition (not in D3)")
    print("  omission := module is in EVERY definition (in D1 & D2) yet unclaimed\n")
    rows, rob_ph, rob_om = [], 0, 0
    for c in claims:
        upper = (out["D3"] if c["dir"] == "out" else inn["D3"])[c["subj"]]
        lower = ((out["D1"] if c["dir"] == "out" else inn["D1"])[c["subj"]]
                 & (out["D2"] if c["dir"] == "out" else inn["D2"])[c["subj"]])
        ph, om = sorted(c["claimed"] - upper), sorted(lower - c["claimed"])
        if ph or om:
            rows.append((c, ph, om)); rob_ph += len(ph); rob_om += len(om)
    print(f"claims with a robust defect : {len(rows)} / {len(claims)}")
    print(f"  phantom modules : {rob_ph}")
    print(f"  omitted modules : {rob_om}")
    for c, ph, om in rows:
        tag = " [hedged]" if c["hedged"] else ""
        print(f"\n  {c['file']}:{c['line']} [{c['dir']}]{tag} "
              f"phantom={ph} omitted={om}")
        print(f"      {c['text'][:130]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
