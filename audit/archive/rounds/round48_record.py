#!/usr/bin/env python3
"""Append Round 48 to validation_rounds.json (schema v1.4). Matches file style: indent=1, ensure_ascii=True."""
import json, subprocess, os

F = os.path.join(os.path.dirname(__file__), "..", "..", "validation_rounds.json")
F = os.path.abspath(F)
d = json.load(open(F))

R48 = {
 "round": 48,
 "date": "2026-06-05",
 "type": "full",
 "answerer_model": "claude-sonnet-4-6 (Agent model:sonnet, magpie-helper)",
 "auditor_model": "claude-opus-4-8 (Agent model:opus, general-purpose)",
 "commit_before": "6d87471",
 "commit_after": None,
 "scope": "cross_module conservation docs + 2 core_docs not re-tested by R47 (post-R47 stale set). R47 (same day) re-validated the 3 worst-scoring cross_module docs; this round covers the 3 it skipped (carbon/land/water balance, last direct test R30 2026-05-29) + Data_Flow (R30) + a fresh-angle Module_Dependencies probe (R47-P4 only did vm_land) + a 2nd carbon deep-dive. 6 probes + G4 regression. User-requested.",
 "questions": [
  {"id": "R48-P1", "archetype": "conservation-law",
   "question": "When land converts between uses (forest->cropland), how is the carbon stock change computed/accounted so carbon is conserved (stock loss -> CO2 emission)? Equations, where released carbon goes, pools tracked.",
   "docs_tested": ["cross_module/carbon_balance_conservation.md"], "modules_tested": [52, 35, 32, 59],
   "score": 8, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 2, "bugs_informational": 1, "bugs_found": 3,
   "root_causes": ["doc_error", "answerer_confabulation"],
   "doc_errors_latent": [{"id": "R48-P1-DOC1", "severity": "minor", "root_cause": "doc_error", "fixed": True, "file": "cross_module/carbon_balance_conservation.md:325", "desc": "emis_land set citation core/sets.gms:332-335 truncated to 3 of 21 mappings; should be 332-354 (verified: set spans 332-354, 7 land x 3 pools). Answer inherited the truncated range from the doc."}],
   "notes": "Central eq q52_emis_co2_actual (52_carbon/normal_dec17/equations.gms:16-19) verbatim-correct; G2 producer/consumer story matches anchor (vm_carbon_stock declared M56, populated by land modules+M59, read by M52). 2 Minor citation-drift (pcm_carbon_stock decl line :34 vs :19; emis_land range). Doc semantic claims correct."},

  {"id": "R48-P2", "archetype": "quantitative-structural",
   "question": "vm_carbon_stock exact dimensions/domain, pools (vegc/litc/soilc), land types; stock = density x area; which module DECLARES vs POPULATES.",
   "docs_tested": ["cross_module/carbon_balance_conservation.md"], "modules_tested": [52, 59, 58],
   "score": 6, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 2, "bugs_informational": 0, "bugs_found": 3,
   "root_causes": ["answerer_confabulation"],
   "doc_errors_latent": [],
   "notes": "Load-bearing spine ALL correct: 4-D vm_carbon_stock(j,land,c_pools,stockType) declared M56 price_aug22/declarations.gms:34, pools {vegc,litc,soilc} (core/sets.gms:324-325), 6 populators (M29/31/32/34/35/59), M52 reads-not-writes, actualNoAcEst pricing default. The flagged 4-D claim is CORRECT, not invented. Major = answerer's oversimplified section-5 cropland-carbon formula (density x crop-area) vs q29_carbon (29_cropland/detail_apr24/equations.gms:38-42) which builds from vm_carbon_stock_croparea+fallow+treecover; honestly labeled '(simplified)'. answerer_confabulation, NOT a doc bug (doc verified correct). G2 anchor healthy."},

  {"id": "R48-P3", "archetype": "conservation-law",
   "question": "How does the land balance guarantee sum of land types = total area, no double-counting/creation? q10_land_area structure; transition constraints across timesteps.",
   "docs_tested": ["cross_module/land_balance_conservation.md"], "modules_tested": [10, 29, 30, 31, 32, 35],
   "score": 10, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 2, "bugs_found": 2,
   "root_causes": [],
   "doc_errors_latent": [],
   "notes": "ACCURATE. q10_land_area (=e=, sum(land,vm_land)=sum(land,pcm_land)) + q10_transition_to/from + .fx forbidden-transition bounds (presolve.gms:13-21) + pcm_land postsolve update all verbatim-correct with exact lines (landmatrix_dec18, the only realization, default.cfg:232). R16 set-expansion anchor NOT reproduced (kept sum(land,...) form). 2 Info (land-set member order; start.gms:8 vs :11 for pcm_land). Inherited expansion/reduction consumer lists verified CORRECT vs code (auditor's initial 'omits M32' was a grep-substring false positive, retracted)."},

  {"id": "R48-P4", "archetype": "conservation-edge-case",
   "question": "How is the water balance (demand <= available) enforced by default? Balancing equation, demand sectors, env flows, infeasibility conditions. Default realization.",
   "docs_tested": ["cross_module/water_balance_conservation.md"], "modules_tested": [42, 43, 41],
   "score": 10, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 2, "bugs_found": 2,
   "root_causes": [],
   "doc_errors_latent": [],
   "notes": "ACCURATE. Both defaults verified (M42 all_sectors_aug13 default.cfg:1319; M43 total_water_aug13 :1406). q43_water (=l=, per-cell) verbatim; wat_dem 5-sector set (agriculture/domestic/manufacturing/electricity/ecosystem, core/sets.gms:247); q42_water_demand; s42_env_flow_scenario default /2/ (LPJmL Smakhtin); groundwater buffer asymmetry (agriculture NOT buffered, 1.01 margin) all code-true. Illustrative numbers properly labeled. 2 Info (decl-line off-by-4)."},

  {"id": "R48-P5", "archetype": "provenance",
   "question": "Per Data_Flow, trace land-use-init (or yield) input from .cs2/.cs3/.mz through GAMS reading into the set/param used + first consumer; file types, params, upstream source.",
   "docs_tested": ["core_docs/Data_Flow.md"], "modules_tested": [10],
   "score": 8, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 0, "bugs_informational": 0, "bugs_found": 1,
   "root_causes": ["doc_error", "answerer_confabulation"],
   "doc_errors_latent": [{"id": "R48-P5-DOC1", "severity": "major", "root_cause": "doc_error", "fixed": True, "file": "core_docs/Data_Flow.md:39-41,414", "desc": "Data_Flow.md mislabeled LUH2 side-layers (luh2_side_layers.cs3, genuinely LUH2) as 'Initial land use' AND omitted the actual land-use-init source avl_land_t.cs3 -> f10_land (LUH3, CMIP7 input4MIPs v3.1.1, via mrlandcore::calcLanduseInitialisation). :414 'LUH2 land-use patterns' stale -> LUH3. Fix: relabel side-layers as LUH2, add the LUH3 init file, change :414 to LUH3."}],
   "notes": "Major = answerer claimed avl_land_t/f10_land 'originates from LUH2'; actual LUH3 (verified via preproc-agent boundary.json avl_land_t->calcLanduseInitialisation + smoke test manual_smoke_questions.md:15-17 calcLanduseInitialisationBase->calcOutput('LUH3'); luh2_side_layers.cs3 IS genuine LUH2). All mechanical claims correct (avl_land_t.cs3->f10_land via $include input.gms:8-12; pm_land_start/hist/pcm_land; first-consumer q10_land_area). LENS-BRIDGE WIN: auditor's blanket ':39 LUH2->LUH3' recommendation was REFINED after direct doc read - the :39 files are genuine LUH2 side-layers, so a literal replace would have INTRODUCED an error; real fix = relabel + add omitted LUH3 file."},

  {"id": "R48-P6", "archetype": "dependency-structure",
   "question": "Per Module_Dependencies, trade(21)<->production(17)<->demand(15/16): which interface vars trade CONSUMES vs PRODUCES, modules on each side, doc accurate/complete?",
   "docs_tested": ["core_docs/Module_Dependencies.md", "modules/module_21.md"], "modules_tested": [21, 17, 16, 15, 11],
   "score": 8, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 2, "bugs_informational": 1, "bugs_found": 3,
   "root_causes": ["doc_error_answerer_beat_it", "answerer_confabulation"],
   "doc_errors_latent": [{"id": "R48-P6-DOC1", "severity": "critical_by_future_reader_harm", "root_cause": "doc_error_answerer_beat_it", "fixed": True, "file": "modules/module_21.md:622-635", "desc": "module_21.md Dependency Chains claimed 'Total Connections 9 (provides to 8 modules: M11,M16,M17,M73,+4; depends on 1)' + unsupported 'Centrality Rank 6 of 46'. Verified vs code @ee98739fd: M21 produces ONLY vm_cost_trade_tariff/margin/feasibility (21_trade/selfsuff_reduced/declarations.gms:21-23) consumed by M11 ONLY (11_costs/default/equations.gms:30-32); depends on 2 (M16 vm_supply, M17 vm_prod_reg). R20-anchor producer-set class. Fixed to provides-to-1/depends-on-2 with code citations."}],
   "notes": "Docs-only answer correctly REFUTED the doc's producer set -> doc_error_answerer_beat_it (does NOT lower score). 2 Minor = answer's own FALSE claims about WHERE in Module_Dependencies.md content appears (claimed M21 in section-3.1 Layer-3 list; claimed C5 in section-4.2 'Demand-to-Land Chain') - answerer_confabulation. 1 Info (vm_prod_reg/vm_supply dim is kall not k). Doc bug is in module_21.md, NOT Module_Dependencies.md. Producer set re-verified independently via rg before fix."},

  {"id": "R48-G4", "archetype": "regression-calibration-anchor", "regression_anchor": "G4",
   "question": "How does magpie4::getReport organize reporting? Dispatch pattern, # unique report* fns, signature, file:line from pinned clone; control arg or grepl filtering?",
   "docs_tested": ["agent/helpers/magpie4_reference.md", ".cache/sources/magpie4/R/getReport.R"], "modules_tested": [],
   "score": 10, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0, "bugs_found": 0,
   "drift_observed": False, "root_causes": [],
   "doc_errors_latent": [],
   "notes": "ACCURATE, drift FALSE. Verified 117 total calls / 106 unique report* (matches expected); NO control arg, NO grepl dispatch filtering (post-dispatch unit-validation grepl L211-218 correctly distinguished from dispatch). Pinned v2.70.0@a360d8c9ec matches version_pins.json (resolution=sha). Calibration trap defeated."}
 ],
 "summary": {
  "mean_score": 8.57,
  "doc_quality_mean": 9.0,
  "n_questions_doc_quality": 6,
  "doc_quality_mean_method": "Raw mean = (P1 8 + P2 6 + P3 10 + P4 10 + P5 8 + P6 8 + G4 10)/7 = 8.57. doc_quality EXCLUDES P2 (its bugs are exclusively answerer pseudo-code/confabulation vs a verified-correct doc); P1/P5/P6 stay IN because each carries a doc_error/doc_error_answerer_beat_it. Kept = P1 8, P3 10, P4 10, P5 8, P6 8, G4 10 -> 54/6 = 9.0, n=6. Honesty note: doc_quality 9.0 does NOT mean zero doc defects - 3 doc bugs were found+fixed; it reflects that most ANSWERS were correct.",
  "total_bugs_scored": 14,
  "bugs_by_severity": {"critical": 0, "major": 2, "minor": 6, "informational": 6},
  "bugs_by_root_cause": {"doc_error": 2, "doc_error_answerer_beat_it": 1, "answerer_confabulation": 4},
  "doc_bugs_fixed": 3,
  "files_fixed": ["cross_module/carbon_balance_conservation.md", "core_docs/Data_Flow.md", "modules/module_21.md"],
  "gate": {"clean": True, "validator": "validate_consistency.sh", "checks": 43, "passed": 39, "errors": 0, "warnings_advisory": 4, "new_errors": [], "note": "4 warnings are pre-existing/advisory (module_18.md arity, 4 unit-claim deltas) - none introduced by R48 edits; Check 25 bare-cite PASS (R48 added full-path citations)."},
  "headline": "cross_module conservation docs (carbon/land/water) + Data_Flow + Module_Dependencies re-validated post-R47. Land + water balance docs CLEAN (10/10). 3 doc bugs found+fixed: carbon emis_land cite range, Data_Flow LUH3 land-use-init mislabel+omission, and an R20-class producer-set bug in module_21.md (M21 produces only vm_cost_trade_* to M11; 'provides to 8 modules' was backwards). G4 magpie4 anchor stable (no drift). Commits PENDING user review.",
  "method_note": "Answerers pinned to claude-sonnet-4-6 (eval-subject pin). Auditors verified vs origin/develop @ee98739fd (working tree == origin/develop, 0/0). All 3 doc fixes independently re-verified vs code (rg) before editing per lens-bridge discipline - which caught and refined the auditor's blanket Data_Flow LUH2->LUH3 recommendation (the :39 files are genuine LUH2 side-layers)."
 }
}

d["rounds"].append(R48)

# regression_questions: append round 48 to G4's used_in_rounds, record drift
for rq in d.get("regression_questions", []):
    if rq.get("id") == "G4" or rq.get("anchor") == "G4" or "G4" in str(rq.get("label", "")):
        rq.setdefault("used_in_rounds", []).append(48)
        rq["last_drift_observed"] = False
        break

# cumulative_stats
cs = d["cumulative_stats"]
cs["total_rounds"] = 48
cs["approx_total_bugs_found"] = cs.get("approx_total_bugs_found", 0) + 15
cs["approx_total_bugs_fixed"] = cs.get("approx_total_bugs_fixed", 0) + 3
cs["last_validation_date"] = "2026-06-05"
cs["mean_score_trend"] = cs["mean_score_trend"] + (
 "->R48 cross_module conservation (carbon/land/water) + 2 core_docs, post-R47 stale set: raw 8.57, doc_q 9.0 "
 "(excl P2 answerer pseudo-formula); land + water balance docs CLEAN 10/10; 3 doc bugs FIXED - emis_land cite "
 "range (carbon_balance_conservation:325 332-335->332-354), LUH3 land-use-init mislabel+omission (Data_Flow:39-41/414), "
 "and R20-class producer-set bug in module_21.md (provides-to 8->1, M21 produces only vm_cost_trade_* to M11, depends-on 1->2) "
 "as doc_error_answerer_beat_it; G4 anchor drift FALSE (106 unique report*, no control/grepl gating). Lens-bridge win: "
 "auditor's blanket Data_Flow LUH2->LUH3 refined after direct read (the :39 files are genuine LUH2 side-layers). Commits pending review."
)

with open(F, "w") as fh:
    json.dump(d, fh, indent=1, ensure_ascii=True)
    fh.write("\n" if False else "")  # original had no trailing newline

print("R48 appended. total_rounds=", cs["total_rounds"])
print("bugs_found=", cs["approx_total_bugs_found"], "bugs_fixed=", cs["approx_total_bugs_fixed"])
