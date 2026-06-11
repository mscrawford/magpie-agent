#!/usr/bin/env python3
"""Item 3: tighter find-rate on internally-CONSISTENT single-statement direction
injections, split class B (serial/causal direction) vs class C (producer
reversal). Tests the hypothesis that B (needs non-local serial-vs-parallel
inference) is the blind spot while C (one declarations.gms grep) is catchable.

Each injection is ONE reversed statement, fully self-consistent (all parts of
that statement flipped, no un-edited sibling). Copies in /tmp/r51_deep2/; repo
docs untouched. Truths verified @ea383032d this session (Phase 0 + the 3-agent
direction audit)."""
import os, shutil, json

REPO = "/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent"
OUT = "/tmp/r51_deep2"
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)

# doc_id: (relpath, [(find,replace)], klass, injected_bug, code_truth)
INJ = {
  "dataflow_chain": ("core_docs/Data_Flow.md", [
      ("- Flow: Module 14 → 30 → 17", "- Flow: Module 17 → 30 → 14")],
    "B", "production serial chain reversed to 17 -> 30 -> 14",
    "M14 produces vm_yld -> M30 produces vm_prod (reads vm_yld) -> M17 aggregates vm_prod_reg. Flow is 14->30->17, not reversed."),

  "modsafety_chain": ("cross_module/modification_safety_guide.md", [
      ("Module 30 (Croparea) → vm_prod(j,k) → Module 17 → vm_prod_reg(i,kall) → Module 21 (Trade)",
       "Module 21 (Trade) → vm_prod_reg(i,kall) → Module 17 → vm_prod(j,k) → Module 30 (Croparea)")],
    "B", "production->trade chain reversed to trade->production",
    "M30 produces vm_prod, M17 aggregates to vm_prod_reg, M21 consumes vm_prod_reg. Flow is 30->17->21, not reversed."),

  "circular_costchain": ("cross_module/circular_dependency_resolution.md", [
      ("Prices → Emission costs → Total costs (one direction)",
       "Total costs → Emission costs → Prices (one direction)")],
    "B", "cost causal chain reversed",
    "q56 emission pricing produces v56_emis_pricing -> vm_emission_costs -> enters q11 total cost. Direction is prices->emission costs->total costs."),

  "dataflow_producer": ("core_docs/Data_Flow.md", [
      ("Populated by: Module 52 (owner; modules/52_carbon/normal_dec17/declarations.gms:9, set in modules/52_carbon/normal_dec17/preloop.gms:71)",
       "Populated by: Module 32 (owner; modules/32_forestry/dynamic_may24/declarations.gms:9, set in modules/32_forestry/dynamic_may24/preloop.gms:71)")],
    "C", "pm_carbon_density_secdforest_ac owner reversed to M32 (fully consistent this time)",
    "pm_carbon_density_secdforest_ac is DECLARED+populated in Module 52 (normal_dec17/declarations.gms:9, preloop.gms:71); M32 does not own it."),

  "moddep_forestry": ("core_docs/Module_Dependencies.md", [
      ("`pm_demand_forestry` (73 → 32): Timber demand",
       "`pm_demand_forestry` (32 → 73): Timber demand")],
    "C", "pm_demand_forestry direction reversed to 32 -> 73",
    "pm_demand_forestry is declared in M73 (timber), read by M32 (forestry). Direction is 73->32, not 32->73."),
}

key = {"phase": "item3 tighter class-B-vs-C find-rate", "docs": {}}
for did, (rel, repl, klass, bug, truth) in INJ.items():
    text = open(os.path.join(REPO, rel)).read()
    for find, rep in repl:
        assert text.count(find) == 1, f"{did}: find-string not unique ({text.count(find)}x): {find[:60]!r}"
        text = text.replace(find, rep)
    base = os.path.basename(rel)
    ddir = os.path.join(OUT, did); os.makedirs(ddir)
    open(os.path.join(ddir, base), "w").write(text)
    key["docs"][did] = {"doc_file": base, "klass": klass, "injected_bug": bug, "code_truth": truth}
    print(f"  [{klass}] {did}: {bug}")

shutil.copy(os.path.join(REPO, "audit/flywheel_rubric.md"), os.path.join(OUT, "rubric.md"))
json.dump(key, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "deep2_key.json"), "w"), indent=1)
nb = sum(1 for d in INJ.values() if d[2] == "B"); nc = sum(1 for d in INJ.values() if d[2] == "C")
print(f"\nWrote {len(INJ)} injected docs ({nb} class-B, {nc} class-C) to {OUT}; key -> deep2_key.json")
