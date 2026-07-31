#!/usr/bin/env python3
"""compute_module_centrality.py — the persisted source for the §1.2 centrality numbers.

WHY THIS EXISTS
--------------------------------------------------------------------------
`audit/interface_role_definitions.md` records the 2026-07-31 ruling: the module
centrality table reports TWO columns, `Owns` and `Reaches`, and the single
`Total` (with its `Total = ProvidesTo + DependsOn` identity) is retired.

The numbers for that ruling were first computed in a throwaway heredoc. Item R6
of the reliability program — the anti-9.52 rule — says any quality figure that
will be CITED must have a persisted artifact, or it is an anecdote. These
figures are cited by `core_docs/Module_Dependencies.md` and
`cross_module/modification_safety_guide.md`, so the computation lives here.

DEFINITIONS (they are `build_defs()` in check_module_set_claims.py; this module
imports them rather than restating them, so there is exactly one implementation)

    Owns       = D2 out = owner(v)              -> readers(v)
    Reaches    = D3 out = writers(v) u {owner(v)} -> readers(v)
    DependsOn2 = D2 in  = the reverse of Owns
    DependsOn3 = D3 in  = the reverse of Reaches

`Owns` is also exactly what the GATE computes as whole-module truth: see
`check_dependent_counts.compute_truth()` with an empty `named` list — the union
of READers over every var the module DECLARES, minus itself. So a prose claim
"provides to N modules" is checked against `Owns`, and writing `Reaches` into
such a line would redden the gate. `Reaches` belongs in the table, which the
claim scanner does not read, and in prose only when named as blast radius.

THE ANCHOR
--------------------------------------------------------------------------
`modules/module_10.md:793` enumerates M10's downstream modules BY NUMBER, hand
-derived long before any of this machinery existed. `--self-test` asserts set
equality against it — not merely the count of 18, which two different sets could
both satisfy. If the role map regresses, this fails loudly.

USAGE
    python3 audit/tools/compute_module_centrality.py --self-test
    python3 audit/tools/compute_module_centrality.py --table      # the 1.2 rows
    python3 audit/tools/compute_module_centrality.py --all        # all 46, csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import check_module_set_claims as cms  # noqa: E402

# §1.2's rows are RANKED BY REACHES, and the ranking is computed here rather
# than hand-maintained. Membership changed on 2026-07-31: the old list was the
# top 10 by `Total = ProvidesTo + DependsOn`, and the ruling retires `Total`, so
# the selection rule went with it. Under Reaches the old list was wrong in both
# directions — it omitted 31_past, which ranks FIRST at 21, and 34_urban at 16;
# and it seated 11_costs at rank 1 with a reach of 1, purely on its 27 inbound
# edges. 11_costs is now a footnote (see M11_FOOTNOTE) rather than a row.
#
# Roles are the only hand-maintained field, because no code artifact carries a
# module's purpose in prose.
ROLE_LABELS = {
    "31": "Pasture area and production",
    "10": "Core land allocation",
    "35": "Natural vegetation",
    "32": "Forestry plantations",
    "30": "Cropland allocation",
    "34": "Urban land",
    "29": "Cropland management",
    "09": "Socioeconomic drivers",
    "17": "Production hub",
    "18": "Crop residues",
    "38": "Factor costs",
    "20": "Commodity processing",
    "11": "Cost aggregator (the model's sink)",
}

# Show the top TOP_N by Reaches, but never cut a tie at the boundary: a "top 10"
# that silently drops two of three modules tied at the cutoff misreports coverage.
TOP_N = 10

M11_FOOTNOTE = "11"

# modules/module_10.md:793 — "Provides to: 18 modules (11, 13, 14, 22, 29, 30,
# 31, 32, 34, 35, 39, 44, 50, 56, 58, 59, 71, 80)". Independently derived.
#
# CAVEAT, and it is the reason the M31 anchor below exists: M10 is a GAP-ZERO
# module (Owns == Reaches == 18), so this anchor is BLIND to the D2-vs-D3
# distinction the ruling turns on. Swapping `owns` to read D3 leaves it green.
# Measured, not assumed: that mutation was run and survived. It validates the
# role map; it does not validate the choice of definition.
M10_ANCHOR = {"11", "13", "14", "22", "29", "30", "31", "32", "34", "35",
              "39", "44", "50", "56", "58", "59", "71", "80"}

# M31 is the DECIDING case of the ruling and the maximally discriminating one
# (gap +20). Owns is independently anchored in the GAMS source, not in this
# computation: `../modules/31_past/*/declarations.gms` declares exactly ONE
# interface variable, `vm_cost_prod_past`, and 11_costs is its only reader.
M31_OWNS_ANCHOR = {"11"}
M31_REACHES_MIN = 20  # regression floor, pinned from this computation (21)


def centrality() -> dict[str, dict[str, set[str]]]:
    """{modnum: {owns, reaches, depends_on_2, depends_on_3}} as module-number sets."""
    out, inn = cms.build_defs(cms.role_payload())
    mods = set(out["D3"]) | set(inn["D3"]) | set(out["D2"]) | set(inn["D2"])
    return {
        m: {
            "owns": set(out["D2"].get(m, set())),
            "reaches": set(out["D3"].get(m, set())),
            "depends_on_2": set(inn["D2"].get(m, set())),
            "depends_on_3": set(inn["D3"].get(m, set())),
        }
        for m in sorted(mods)
    }


def self_test() -> int:
    """Anchor the computation before anything downstream trusts it."""
    failures = 0
    c = centrality()

    got = c.get("10", {}).get("owns", set())
    if got == M10_ANCHOR:
        print(f"  SELF-TEST PASS [m10-owns-set-anchor] ({len(got)} modules, exact set match)")
    else:
        failures += 1
        print(f"  SELF-TEST FAIL [m10-owns-set-anchor]: modules/module_10.md:793 enumerates "
              f"{sorted(M10_ANCHOR)}, computed {sorted(got)} "
              f"(missing {sorted(M10_ANCHOR - got)}, extra {sorted(got - M10_ANCHOR)})")

    # The DISCRIMINATING assertion. M10 alone cannot tell D2 from D3, so without
    # this a computation that silently collapsed the two definitions would pass
    # every other check here. M31 owns one variable and reaches 21 modules.
    m31 = c.get("31", {})
    if m31.get("owns") == M31_OWNS_ANCHOR and len(m31.get("reaches", ())) >= M31_REACHES_MIN:
        print(f"  SELF-TEST PASS [m31-owns-vs-reaches-discriminates] "
              f"(owns={sorted(m31['owns'])}, reaches={len(m31['reaches'])})")
    else:
        failures += 1
        print(f"  SELF-TEST FAIL [m31-owns-vs-reaches-discriminates]: M31 declares only "
              f"`vm_cost_prod_past`, so Owns must be {sorted(M31_OWNS_ANCHOR)} and Reaches "
              f">= {M31_REACHES_MIN}; computed owns={sorted(m31.get('owns', ()))} "
              f"reaches={len(m31.get('reaches', ()))}")

    # The two definitions must not collapse into each other: at least one module
    # must have a STRICTLY larger Reaches than Owns, or the gap column is a
    # column of zeros and the whole two-column ruling is moot.
    gapped = [m for m, r in c.items() if len(r["reaches"]) > len(r["owns"])]
    if gapped:
        print(f"  SELF-TEST PASS [definitions-do-not-collapse] ({len(gapped)} modules with gap > 0)")
    else:
        failures += 1
        print("  SELF-TEST FAIL [definitions-do-not-collapse]: Owns == Reaches for every "
              "module — D2 and D3 have collapsed, so the table's gap column is meaningless")

    # Owns is a SUBSET of Reaches by construction (D3 = writers u {owner}).
    # A violation means build_defs changed shape under us.
    bad = [m for m, r in c.items() if not r["owns"] <= r["reaches"]]
    if bad:
        failures += 1
        print(f"  SELF-TEST FAIL [owns-subset-of-reaches]: violated for {bad}")
    else:
        print(f"  SELF-TEST PASS [owns-subset-of-reaches] ({len(c)} modules)")

    # A module never provides to itself under either definition.
    self_edges = [m for m, r in c.items() if m in r["owns"] | r["reaches"]]
    if self_edges:
        failures += 1
        print(f"  SELF-TEST FAIL [no-self-edges]: {self_edges}")
    else:
        print(f"  SELF-TEST PASS [no-self-edges]")

    # Guard against a vacuous scan reading as a clean result.
    if len(c) < 40:
        failures += 1
        print(f"  SELF-TEST FAIL [non-vacuous]: only {len(c)} modules in the map, expected ~46")
    else:
        print(f"  SELF-TEST PASS [non-vacuous] ({len(c)} modules)")

    if failures:
        print(f"SELFTEST_FAIL compute_module_centrality ({failures} failed)")
        return 1
    print("SELFTEST_OK compute_module_centrality")
    return 0


def ranked() -> list[tuple[int, str, int, int, int]]:
    """[(rank, modnum, owns, reaches, depends_on)] by Reaches, ties included."""
    c = centrality()
    rows = sorted(
        ((m, len(r["owns"]), len(r["reaches"]), len(r["depends_on_3"]))
         for m, r in c.items()),
        key=lambda t: (-t[2], -t[1], t[0]),
    )
    cutoff = rows[TOP_N - 1][2] if len(rows) >= TOP_N else 0
    kept = [t for t in rows if t[2] >= cutoff]
    return [(i, m, o, rc, d) for i, (m, o, rc, d) in enumerate(kept, 1)]


def module_dir(num: str) -> str:
    for d in sorted((MAGPIE_MODULES).iterdir()) if MAGPIE_MODULES.is_dir() else []:
        if d.is_dir() and d.name.startswith(f"{num}_"):
            return d.name
    return num


MAGPIE_MODULES = REPO.parent / "modules"


def print_table() -> int:
    rows = ranked()
    print(f"| Rank | Module | Owns | Reaches | gap | Depends On | Primary Role |")
    print(f"|-----:|--------|-----:|--------:|----:|-----------:|--------------|")
    for rank, num, owns, reaches, dep in rows:
        gap = reaches - owns
        role = ROLE_LABELS.get(num, "")
        print(f"| {rank} | **{module_dir(num)}** | {owns} | {reaches} | "
              f"{'+' + str(gap) if gap else '0'} | {dep} | {role} |")
    if len(rows) > TOP_N:
        tied = [f"M{m}" for _, m, _, rc, _ in rows if rc == rows[TOP_N - 1][3]]
        print(f"\n(rows past {TOP_N} are the tie at Reaches "
              f"{rows[TOP_N - 1][3]}: {', '.join(tied)} — shown rather than cut)")
    c = centrality()
    f = c[M11_FOOTNOTE]
    print(f"\nfootnote: {module_dir(M11_FOOTNOTE)} owns {len(f['owns'])} / reaches "
          f"{len(f['reaches'])} but DEPENDS ON {len(f['depends_on_3'])}")
    return 0


def print_all() -> int:
    c = centrality()
    print("module,owns,reaches,gap,depends_on_d2,depends_on_d3")
    for m, r in sorted(c.items()):
        print(f"{m},{len(r['owns'])},{len(r['reaches'])},"
              f"{len(r['reaches']) - len(r['owns'])},"
              f"{len(r['depends_on_2'])},{len(r['depends_on_3'])}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="anchor against module_10.md:793")
    ap.add_argument("--table", action="store_true", help="emit the section 1.2 rows as markdown")
    ap.add_argument("--all", action="store_true", help="emit all modules as csv")
    ap.add_argument("--members", metavar="MOD", help="enumerate the module sets for one module")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.members:
        r = centrality().get(args.members)
        if not r:
            print(f"no such module in the role map: {args.members}")
            return 1
        for k in ("owns", "reaches", "depends_on_2", "depends_on_3"):
            print(f"{k:14s} ({len(r[k]):2d}): {', '.join(sorted(r[k]))}")
        return 0
    if args.all:
        return print_all()
    return print_table()


if __name__ == "__main__":
    raise SystemExit(main())
