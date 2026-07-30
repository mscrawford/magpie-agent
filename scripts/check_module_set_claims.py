#!/usr/bin/env python3
"""check_module_set_claims.py — Check 41, ADVISORY.

Closes the `attribution_set` blind spot: EXHAUSTIVE module-set claims that name
NO interface variable, and so could not be bound by any existing checker.

WHY THIS EXISTS
--------------------------------------------------------------------------
The seeded-bug benchmark (`audit/seeded_bug_benchmark_2026-07-20.md`) measured
the deterministic gate at 30.4% detection on real historical doc bugs, and
`attribution_set` was its LARGEST blind spot at **0 of 5**. The mechanism was
diagnosed, not guessed. The module_59 R58 Critical reads:

    **Provides to**: Module 52 (carbon stocks for topsoil component)
    **Depends on**: Modules 10 (land), 30 (croparea), 29 (cropland).

Zero interface variables. Every attribution checker (31/32/33/34/35/36) is
VAR-ANCHORED — it keys the doc-vs-code diff on a backticked identifier — so
there was nothing to bind and nothing to verify. Check 37 (bindability) already
sizes the class (570 of 960 attribution lines, 59%, are unbindable) but by
design only flags the SHAPE; it never resolves the claim.

This check resolves it: a bare module list is diffed against the union of the
subject module's interface relationships, derived from the role map.

DEFINITION-ROBUSTNESS — why this is safe while the ruling is OPEN
--------------------------------------------------------------------------
`audit/interface_role_definitions.md` records that "Provides To" has three
defensible readings, and the choice is REOPENED (D2 was adopted, then found to
lose the contributor -> declarer edge). A checker that picked one would emit
findings the eventual ruling could invalidate — the exact failure the R55/R56
arc exists to prevent.

So this check only reports defects that hold under EVERY definition:

    D1 flow  = writers(v) -> readers(v)
    D2 owner = owner(v)   -> readers(v)
    D3 union = writers(v) u {owner(v)} -> readers(v)

    OMISSION  module is in D1 AND D2 (so in D3 too) yet the doc omits it
              -> missing under every definition
    PHANTOM   module is in NEITHER D1 NOR D2 NOR D3 (i.e. not in D3)
              -> present under no definition

The band between the two (in D3 but not in D1&D2) is exactly what the ruling
decides, and is deliberately NOT reported. Whatever Mike rules, no finding here
changes.

KNOWN LIMITS — stated, not hidden
--------------------------------------------------------------------------
1. SET-BASED PROVISION is invisible. The role map covers vm_/pm_/im_/pcm_/fm_
   variables, not GAMS SETS. Module 28 (age class) provides the `ac` set to
   32/29 without any shared interface var, so those read as phantoms. This is
   why PHANTOM findings are reported at lower confidence than OMISSIONs.
2. OWNER-LESS VARS — ✅ FIXED 2026-07-31, no longer a limit. Previously 13 of
   144 referenced interface vars had no recorded owner, because they are
   declared as `table`/`parameter` in a realization's `input.gms` rather than
   in `declarations.gms` (e.g. `fm_carbon_density` -> 52_carbon/*/input.gms,
   `pm_climate_class` -> 45_climate/*/input.gms). They were absent from D2, so
   a real dependency through one of them could not reach the D1&D2 lower bound
   and surfaced here as a PHANTOM. `build_producer_map` in
   check_consumer_attribution.py now scans both declaration sites (positive
   controls in its --self-test cover the `table` and `parameter` spellings).
   MEASURED EFFECT on this check: PHANTOM findings 12 claims / 18 modules ->
   8 claims / 10 modules; OMISSION coverage 33 -> 37 modules. The whole
   module_45.md:448 row (4-of-4 phantom, all four explained by
   `pm_climate_class` having no owner) disappeared. Owner-less is now 5, and
   all 5 are correct: `fm_croprea` is a typo appearing only in GAMS comments
   and is never declared, and 4 `sm_` scalars live in core/calculations.gms
   rather than in any module.
3. REALIZATION-BLIND. The role map unions all realizations, so a read that only
   exists in a NON-default realization still counts. That is a scope
   difference, not a false positive, but it explains findings a
   default-realization reading would not produce.
4. HEDGED claims ("primarily", "among others") are explicitly non-exhaustive,
   so OMISSION is suppressed on them; PHANTOM still applies.

Usage:
  python3 scripts/check_module_set_claims.py [--summary-only] [--self-test]
Exit: 0 always (ADVISORY). 2 on checker error / failed self-test.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_DIR / "scripts"))

import check_attribution_omissions as cao  # noqa: E402
import check_bindability as cb  # noqa: E402

CHECK_NAME = "check_module_set_claims"

# An EXHAUSTIVE set claim: a bolded field label whose value IS the whole set.
# "**Depends on**: Modules 10, 29, 30" claims completeness; a partial bullet
# ("- Module 31 (Pasture): pasture carbon") does not, and only an exhaustive
# claim can be checked for OMISSION.
SET_LABEL_RE = re.compile(
    r"^\s*[-*]?\s*\*\*\s*(Provides\s+to|Depends\s+on|Receives\s+from|"
    r"Feeds\s+into|Downstream|Upstream)\s*\*\*", re.I)
OUT_LABELS = {"provides to", "feeds into", "downstream"}


# ---------------------------------------------------------------------------
# Ground truth
# ---------------------------------------------------------------------------

def role_payload() -> dict:
    """The code-derived role map, in the SAME shape `--dump-rolemap` emits.

    NOTE the two key formats this normalises: build_producer_map returns a
    module DIRECTORY name ("10_land") while the role map keys by NUMBER ("10").
    Comparing them uniformly silently yields an empty owner set for every
    module, which reads as "every claimed module is a phantom".
    """
    role, _ = cao.build_role_map()
    producers = cao.build_producer_map()
    out = {}
    for var, rolemap in role.items():
        owner = producers.get(var) or None
        out[var] = {
            "owner": owner.split("_", 1)[0] if owner else None,
            "writers": {m for m, r in rolemap.items() if "POPULATE" in r},
            "readers": {m for m, r in rolemap.items() if "READ" in r},
        }
    return out


def build_defs(role: dict):
    """role -> (out, inn), each {defname: {modnum: set(modnum)}}."""
    out = {k: defaultdict(set) for k in ("D1", "D2", "D3")}
    inn = {k: defaultdict(set) for k in ("D1", "D2", "D3")}
    for _var, r in role.items():
        owner, writers, readers = r["owner"], r["writers"], r["readers"]
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


# ---------------------------------------------------------------------------
# Claim collection — production finder + ONE narrowing filter
# ---------------------------------------------------------------------------

def collect_claims(text: str, rel_path: str, subj: str,
                   allow: set | None = None) -> list[dict]:
    """Exhaustive set claims in one doc.

    The FINDER is `check_bindability.scan_doc` — the production locator for
    attribution-context lines that name >=1 module and bind NO interface var,
    with its fence / negation / historical / allowlist filter layer. Only the
    exhaustiveness test is added here. Re-implementing the finder minus those
    filters is a known failure mode (see feedback_probe_is_unverified_code).
    """
    found, _bindable, _unb, _sup = cb.scan_doc(text, rel_path, allow or set())
    lines = text.splitlines()
    claims = []
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
            "file": rel_path, "line": f["line"], "subj": subj, "label": label,
            "dir": "out" if label in OUT_LABELS else "in",
            "claimed": claimed, "hedged": f["hedged"], "row": f["row"],
        })
    return claims


def diff_claim(claim: dict, out: dict, inn: dict) -> tuple[list, list]:
    """(phantoms, omissions) that hold under EVERY definition."""
    side = out if claim["dir"] == "out" else inn
    upper = side["D3"][claim["subj"]]
    lower = side["D1"][claim["subj"]] & side["D2"][claim["subj"]]
    phantoms = sorted(claim["claimed"] - upper)
    # A hedged claim is explicitly a SUBSET -> omission is not a defect.
    omissions = [] if claim["hedged"] else sorted(lower - claim["claimed"])
    return phantoms, omissions


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _iter_docs():
    for md in sorted((AGENT_DIR / "modules").glob("module_[0-9][0-9].md")):
        yield md, f"modules/{md.name}", md.stem.split("_")[1]


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        return self_test()
    summary_only = "--summary-only" in args

    try:
        role = role_payload()
    except Exception as exc:  # noqa: BLE001
        print(f"{CHECK_NAME}: ERROR building role map: {exc}", file=sys.stderr)
        return 2
    if not role:
        print(f"{CHECK_NAME}: ERROR role map is empty", file=sys.stderr)
        return 2
    out, inn = build_defs(role)
    allow = cb.load_allowlist()

    n_claims = n_om = n_ph = 0
    om_mods = ph_mods = 0
    rows = []
    for md, rel, subj in _iter_docs():
        for c in collect_claims(md.read_text(), rel, subj, allow):
            n_claims += 1
            ph, om = diff_claim(c, out, inn)
            if om:
                n_om += 1
                om_mods += len(om)
            if ph:
                n_ph += 1
                ph_mods += len(ph)
            if ph or om:
                rows.append((c, ph, om))

    if not summary_only:
        for c, ph, om in rows:
            print(f"{c['file']}:{c['line']}: [{c['label']}] "
                  f"claims {sorted(c['claimed'])}")
            if om:
                print(f"    OMISSION (in every definition, not claimed): {om}")
            if ph:
                print(f"    PHANTOM  (in no definition; see limit 1, sets): {ph}")
            print(f"    | {c['row'][:120]}")

    print(f"{CHECK_NAME}: ADVISORY: {n_om} claim(s) with an OMISSION "
          f"({om_mods} module(s)), {n_ph} with a PHANTOM ({ph_mods} module(s)), "
          f"among {n_claims} exhaustive module-set claim(s)")
    return 0


# ---------------------------------------------------------------------------
# Self-test — SYNTHESIZED KNOWN BUGS, built before the corpus run
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Positive + negative controls on a synthetic role map.

    Per the standing rule, a validator needs a synthesized POSITIVE test
    matching the bug class BEFORE the corpus run: "0 findings on the corpus" is
    otherwise ambiguous between "corpus clean" and "validator broken".
    """
    fails = []

    def check(name, got, want):
        if got != want:
            fails.append(f"{name}: got {got!r}, want {want!r}")

    # Synthetic map. M07 owns+writes v1 which M05 reads   -> 07 in D1&D2 of 05.
    # M08 only WRITES v2 (owned by M05) which M05 reads    -> 08 in D1\D2 (band).
    # M06 only OWNS v3 (written by M09) which M05 reads    -> 06 in D2\D1 (band).
    # M04 is unrelated to M05 entirely                     -> phantom if claimed.
    role = {
        "vm_a": {"owner": "07", "writers": {"07"}, "readers": {"05"}},
        "vm_b": {"owner": "05", "writers": {"08"}, "readers": {"05"}},
        "vm_c": {"owner": "06", "writers": {"09"}, "readers": {"05"}},
    }
    out, inn = build_defs(role)

    check("D1 in(05)", inn["D1"]["05"], {"07", "08", "09"})
    check("D2 in(05)", inn["D2"]["05"], {"07", "06"})
    check("D3 in(05)", inn["D3"]["05"], {"07", "08", "09", "06"})
    check("lower bound in(05)", inn["D1"]["05"] & inn["D2"]["05"], {"07"})

    def one(text, subj="05"):
        cs = collect_claims(text, "modules/module_TEST.md", subj)
        return cs

    # POSITIVE 1 — the exact module_59 pre-fix shape must parse and diff.
    doc = ("## Dependency Chains\n"
           "- **Depends on**: Modules 04 (unrelated), 08 (writer)\n")
    cs = one(doc)
    check("positive1 parsed", len(cs), 1)
    if cs:
        ph, om = diff_claim(cs[0], out, inn)
        # 04 is in no definition -> phantom. 07 is in every one -> omission.
        check("positive1 phantom", ph, ["04"])
        check("positive1 omission", om, ["07"])

    # POSITIVE 2 — direction. "Provides to" reads the OUT side, not the IN side.
    doc_out = ("## Dependency Chains\n"
               "- **Provides to**: Module 04 (unrelated)\n")
    cs = one(doc_out, subj="07")
    check("positive2 parsed", len(cs), 1)
    if cs:
        ph, om = diff_claim(cs[0], out, inn)
        check("positive2 dir", cs[0]["dir"], "out")
        check("positive2 phantom", ph, ["04"])   # 07 -> 05 only
        check("positive2 omission", om, ["05"])

    # NEGATIVE 1 — a CORRECT claim must be silent. Vacuity control: if this
    # fired, every finding above would be noise rather than signal.
    cs = one("## Dependency Chains\n- **Depends on**: Module 07 (owner+writer)\n")
    if cs:
        ph, om = diff_claim(cs[0], out, inn)
        check("negative1 phantom", ph, [])
        check("negative1 omission", om, [])
    else:
        fails.append("negative1: correct claim was not even parsed")

    # NEGATIVE 2 — the AMBIGUOUS BAND must stay silent while the ruling is open.
    # 08 (D1 only) and 06 (D2 only) are neither omission nor phantom.
    cs = one("## Dependency Chains\n"
             "- **Depends on**: Modules 06, 07, 08, 09\n")
    if cs:
        ph, om = diff_claim(cs[0], out, inn)
        check("negative2 band-phantom", ph, [])
        check("negative2 band-omission", om, [])

    # NEGATIVE 3 — a partial bullet is NOT an exhaustive claim.
    cs = one("## Dependency Chains\n- Module 04 (Pasture): pasture carbon\n")
    check("negative3 partial-not-exhaustive", len(cs), 0)

    # NEGATIVE 4 — a HEDGED claim suppresses omission but keeps phantom.
    # NB the fixture uses the "Module NN" form: `_mod_nums` does not read a
    # single number out of "Modules 04, among others", so the first draft of
    # this case failed on the FIXTURE, not the checker.
    cs = one("## Dependency Chains\n"
             "- **Depends on**: primarily Module 04 (among others)\n")
    if cs:
        ph, om = diff_claim(cs[0], out, inn)
        check("negative4 hedged-omission-suppressed", om, [])
        check("negative4 hedged-phantom-kept", ph, ["04"])
    else:
        fails.append("negative4: hedged claim was not parsed")

    if fails:
        print(f"{CHECK_NAME} SELF-TEST: FAIL")
        for f in fails:
            print(f"  - {f}")
        return 2
    print(f"{CHECK_NAME} SELF-TEST: PASS "
          f"(2 positive, 4 negative incl. ambiguous-band + vacuity controls)")
    # Sentinel required by scripts/selftest_validator.sh: exit 0 alone would be
    # minted by a script that silently ignores --self-test and does a corpus run.
    print(f"SELFTEST_OK {CHECK_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
