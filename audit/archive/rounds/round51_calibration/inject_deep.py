#!/usr/bin/env python3
"""Follow-up #1: find-rate on DEEP-Layer-2 SINGLE-STATEMENT claims.

B-prime showed the residual is single-statement deep-Layer-2 claims (no
redundancy backstop, no mechanical check). Here we inject 3 internally-CONSISTENT
single-statement reversals (one wrong claim each, no self-contradiction shortcut)
across the hardest classes B/C/D, and measure whether the full-doc auditor finds
them. Copies in /tmp/r51_deep/; repo docs untouched. Truth verified @ea383032d.
"""
import os, shutil, json

REPO = "/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent"
OUT = "/tmp/r51_deep"
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)

INJ = {
  # class B - causal/data-flow direction (this is the one B-prime already MISSED; re-include)
  "carbon_balance": ("cross_module/carbon_balance_conservation.md", [
      ('All populated slices flow to Module 52 and Module 56',
       'All populated slices flow to Module 52, which then forwards them to Module 56'),
    ],
    "soilc carbon stated as serial M52 -> M56 hand-off (class B causal-direction)",
    "M52 & M56 are PARALLEL readers of vm_carbon_stock; M56 reads it directly (q56_emis_pricing_co2), not via M52."),

  # class C - producer/owner attribution (single statement)
  "Data_Flow": ("core_docs/Data_Flow.md", [
      ('Populated by: Module 52 (owner; modules/52_carbon/normal_dec17/declarations.gms:9',
       'Populated by: Module 32 (owner; modules/32_forestry/dynamic_may24/declarations.gms:9'),
    ],
    "pm_carbon_density_secdforest_ac stated as owned/populated by Module 32 (class C producer)",
    "pm_carbon_density_secdforest_ac is DECLARED in Module 52 (normal_dec17/declarations.gms:9); M32 does not declare it."),

  # class D - default-state caveat (single statement)
  "Module_Dependencies": ("core_docs/Module_Dependencies.md", [
      ('`vm_landdiff` is additionally consumed only by the non-default `lp_nlp_apr17` realization',
       '`vm_landdiff` is additionally consumed by the default `nlp_apr17` realization'),
    ],
    "vm_landdiff stated as consumed by the DEFAULT nlp_apr17 (class D default-state)",
    "Default optimization is nlp_apr17 (config); vm_landdiff is consumed ONLY by the non-default lp_nlp_apr17 (solve.gms)."),
}

key = {"phase": "followup-1 deep-Layer-2 single-statement find-rate", "docs": {}}
for did, (rel, repl, bug, truth) in INJ.items():
    text = open(os.path.join(REPO, rel)).read()
    for find, rep in repl:
        assert text.count(find) == 1, f"{did}: find-string not unique: {find[:60]!r}"
        text = text.replace(find, rep)
    base = os.path.basename(rel)
    ddir = os.path.join(OUT, did); os.makedirs(ddir)
    open(os.path.join(ddir, base), "w").write(text)
    key["docs"][did] = {"doc_file": base, "injected_bug": bug, "code_truth": truth}
    print(f"  {did}: '{bug}'")

shutil.copy(os.path.join(REPO, "audit/flywheel_rubric.md"), os.path.join(OUT, "rubric.md"))
json.dump(key, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "deep_key.json"), "w"), indent=1)
print(f"\nWrote {len(INJ)} deep injected docs to {OUT}; key -> deep_key.json")
