#!/usr/bin/env python3
"""Append R43 entry to validation_rounds.json (indent=1, ensure_ascii=True) + update stats + G1/G2 anchors."""
import json, sys

PATH = "/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/audit/validation_rounds.json"
d = json.load(open(PATH))
if any(r.get("round") == 43 for r in d["rounds"]):
    print("R43 already present — aborting."); sys.exit(1)

r43 = {
    "round": 43,
    "date": "2026-06-03",
    "commit_before": "b683388 (magpie-agent main, incl R41/R42 + teammate f4f44b0); MAgPIE develop @ ee98739fd",
    "commit_after": "pending (no doc fixes this round; record-only)",
    "answerer_model": "claude-sonnet-4-6 (Agent model:sonnet, magpie-helper)",
    "auditor_model": "claude-opus-4-8 (Agent model:opus, general-purpose)",
    "type": "full",
    "scope": ("Third round of the user's multi-round request. Two drivers: (1) VALIDATE a teammate's freshly-pulled doc edits "
              "- commit f4f44b0 ('fix(validator): resolve bare cites to default realization; re-anchor freshness to canonical "
              "develop') touched module_80.md and module_37.md, unvalidated; R43-Q1 (M80) and R43-Q2 (M37) probe them docs-only "
              "so any introduced error surfaces. (2) Fresh periphery/high-value coverage respecting the heavy R41/R42 module locks "
              "(30 modules locked at retire_after 44/45): M58 peatland (never deeply probed), a cost-aggregation chain (M39/M40/M34), "
              "timber (M73). Regression anchors G1 + G2 (GAMS anchors). Note: the framing that f4f44b0 'rewrote module_80.md (134 "
              "lines)' was inaccurate - the Q1 auditor clarified it was minor citation-prefix edits (file is 1094 lines, not a "
              "rewrite); validation still confirmed both edited docs accurate."),
    "summary": {
        "total_bugs_reported_by_auditors": 9,
        "auditor_false_positives_withdrawn": 0,
        "total_bugs_net": 9,
        "bugs_by_severity": {"critical": 0, "major": 0, "minor": 3, "informational": 6},
        "bugs_by_root_cause": {"doc_error": 0, "doc_error_answerer_beat_it": 0, "answerer_confabulation": 3, "answerer_style_or_framing": 6},
        "mean_score": 9.57,
        "doc_quality_mean": 10.0,
        "n_questions_doc_quality": 5,
        "doc_quality_mean_method": ("Raw mean=(10+10+10+9+8+10+10)/7=9.57. doc_quality EXCLUDES Q4 (9) and Q5 (8) - both sub-10 scores "
                                    "are exclusively answerer_confabulation (citation-table/preloop line-number drift) against "
                                    "verified-correct docs; kept Q1/Q2/Q3/G1/G2 (all clean 10): (10+10+10+10+10)/5=10.0. ZERO doc bugs "
                                    "this round, so doc_quality is a perfect 10 - the corpus, incl the two teammate-edited docs, is accurate."),
        "score_range": [8, 10],
        "regression_anchors": {
            "G1": {"score": 10.0, "drift_observed": False,
                   "trend": "STABLE. managementcalib_aug19 sole+default (default.cfg:354); exactly 2 equations q14_yield_crop(14-16)+q14_yield_past(35-39); no q14_yieldcalib. 10 across R22/23/25/26/27/29/42/43."},
            "G2": {"score": 10.0, "drift_observed": False,
                   "trend": ("STRONGEST yet (10, up from R41's 9). Declaration M56 price_aug22/declarations.gms:34; populator set "
                             "{29,31,32,34,35,59} exact incl M34-via-.fx-to-0; M52 reader q52_emis_co2_actual(16-19); M56 chain intact; "
                             "c56_carbon_stock_pricing=actualNoAcEst. The §1.5 populator-set doc (module_52.md:424, module_56.md:583/1074) "
                             "still CORRECT - R22->R26 regression stays fixed. Only an exponent-notation Informational (^ vs **, exempt).")}
        },
        "gate_summary": ("No numeric gate. Raw mean 9.57 - the HIGHEST classic-round mean on record (prev high R25 8.93; R42 9.29). "
                         "doc_quality 10.0: ZERO doc bugs across 7 questions. The teammate-edit validation SUCCEEDED: module_80.md "
                         "(M80 default nlp_apr17, CONOPT4, recursive-dynamic, 32 q11 cost terms) and module_37.md (M37 default 'off', "
                         "pm_labor_prod=1, the sticky_feb18/per_ton abort-guard, sticky_labor as the non-default consumer) both verified "
                         "ACCURATE post-f4f44b0. Fresh finds confirmed clean: M58 peatland is pure parameterization (area x IPCC EFs) and "
                         "correctly BYPASSES M52/vm_carbon_stock (routes peatland emis_annual straight to vm_emissions_reg); M39/M40/M34 "
                         "cost-variable attribution all correct incl the urban two-channel treatment (vm_cost_landcon + vm_cost_urban steering "
                         "penalty); M73 timber's no-HWP-delay assumption verified (no harvested-wood-product carbon pool exists). The only 3 "
                         "scored bugs are Minor answerer citation drift (Q4 register-table line; Q5 two preloop if-block lines), docs correct."),
        "bugs_fixed_this_session": 0,
        "bugs_fixed_detail": "No doc fixes - zero doc_error or doc_error_answerer_beat_it bugs found. All load-bearing doc claims (incl the two teammate-edited docs module_80.md + module_37.md) verified accurate against live GAMS @ ee98739fd.",
        "bugs_deferred": 0,
        "not_fixed_detail": ("The 3 Minor answerer_confabulation bugs (Q4: vm_cost_urban register-table cited scaling.gms:8/equations.gms:25-26 "
                             "for the declaration, actual declarations.gms:13 - body text correct; Q5: Churkina + linear-ramp preloop if-blocks "
                             "cited ~6 lines early) need NO doc fix - the docs are correct; the answerers were imprecise. The 6 Informational "
                             "(Q3 pseudocode time-index drops, EF-unit source inconsistency, benign cite widths; Q4 f40_distance off-by-one; "
                             "G2 ^ vs **) are not doc bugs."),
        "validators": "validate_consistency.sh: 39/43 passed, 4 advisory warnings, 0 errors, verdict PASS. No doc files changed in R43 (record-only round), so identical to the R41/R42 post-fix baseline; the 4 advisory warnings remain the pre-existing set.",
        "run_context": ("Interactive run 2026-06-03, third of the user's multi-round request (continuing without interruption). "
                        "magpie-agent main @ b683388 (R41/R42 committed + pushed to mscrawford, teammate f4f44b0 rebased underneath); "
                        "MAgPIE develop clean @ ee98739fd (GAMS ground truth - the GAMS code lives in the parent repo and was NOT touched "
                        "by f4f44b0, which edited only magpie-agent docs). No commits yet for R43 (record-only)."),
        "highlights": [
            "Raw mean 9.57 - highest classic-round mean on record. doc_quality 10.0, ZERO doc bugs across 7 questions.",
            "Teammate-edit validation SUCCEEDED: module_80.md + module_37.md (both touched by f4f44b0) verified ACCURATE post-edit. The pull-rebase-and-validate loop caught nothing wrong - the teammate's edits were sound.",
            "M58 peatland (first deep probe): pure parameterization (endogenous area x exogenous IPCC per-area EFs), and correctly BYPASSES M52/vm_carbon_stock - peatland routes emis_annual straight to vm_emissions_reg. Verified 3 ways.",
            "M73 timber no-HWP-delay assumption verified: no harvested-wood-product carbon pool exists in the code (c_pools = vegc/litc/soilc only); harvested carbon emitted in full at harvest.",
            "Cost-variable attribution (M39 vm_cost_landcon, M40 vm_cost_transp, M34 vm_cost_urban + the urban two-channel treatment) all correct - the high-error cost-attribution class held.",
            "G1=10, G2=10 (G2 strongest yet, up from R41's 9); both drift FALSE. The §1.5 populator-set anchor remains healthy.",
            "Across R41-R43 all four anchors (G1-G4) exercised with zero drift; G4's R37 regression recovered (R41)."
        ]
    },
    "questions": [
        {"id": "R43-Q1", "archetype": "timing/sequencing + quantitative (solve)", "modules_tested": [80, 12, 38, 11],
         "question": "How does MAgPIE solve? (a) M80 default realization + solver + recursive-dynamic vs intertemporal; (b) how M12 interest enters discounting; (c) how M38 factor costs enter the minimized objective. Name scalars/vars/equations, cite file:line.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0,
         "phase_gate": "M80 default nlp_apr17 verified (default.cfg:2282; 4 realizations). VALIDATES teammate edit: module_80.md (1094 lines) accurate on default/solver/solve-statement/scalars/fallback. CONOPT4, solve.gms:34, s80_maxiter=30, s80_toloptimal=1e-08, 4-strategy fallback all exact. Recursive-dynamic (per-timestep, no intertemporal NPV) CORRECT. pm_interest NOT direct in q11 but via (r+d)/(1+r) annuitization in M38/29/32/39/41/56/58 - verified q38_cost_prod_capital(eq:23), s38_depreciation_rate=0.05. M38 sticky_feb18 4 eqs -> q11_cost_reg first term -> q11_cost_glo -> vm_cost_glo. All 6 cross-module q11 cost-term line cites exact; '32 cost terms' exact.",
         "notes": "Clean (10). No doc fixes - module_80/12/38/11.md all accurate. Teammate's f4f44b0 module_80.md edit (minor citation edits, NOT a 134-line rewrite as the orchestrator initially framed) validated correct."},

        {"id": "R43-Q2", "archetype": "default-vs-switch + chain", "modules_tested": [37, 38, 36],
         "question": "In MAgPIE's default config, how does M37 (labor productivity) work? (a) default realization + what it drives; (b) interaction with M38 factor costs; (c) how M36 employment relates. Name realization/vars/params, cite file:line.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0,
         "phase_gate": "M37 default 'off' verified (default.cfg:1214; realizations {off,exo}); off/preloop.gms:8 sets pm_labor_prod(t,j)=1; M37 has no equations. VALIDATES teammate edit: module_37.md accurate. M38 sticky_feb18 ABORTS unless pm_labor_prod=1 (presolve.gms:8-10) - verified; pm_labor_prod correctly absent from q38_cost_prod_labor. 'sticky_labor' is a REAL non-default M38 realization (where pm_labor_prod enters q38_ces_prodfun), not a confusion. M36 exo_may22 provides pm_hourly_costs + pm_productivity_gain_from_wages; q36_employment back-calculates v36_employment as REPORTING-only (used in no constraint, verified via rg).",
         "notes": "Clean (10). No doc fixes. The f4f44b0 module_37.md edit ('resolve bare cites to default realization') correctly disambiguated the non-default sticky_labor consumer from the default abort-realizations - validated accurate."},

        {"id": "R43-Q3", "archetype": "causal chain + parameterization", "modules_tested": [58, 52, 56],
         "question": "How does M58 (peatland) represent GHG emissions? (a) default realization + what drives area/emissions; (b) mechanistic or exogenous per-area emission factors? show param/equation; (c) how peatland emissions reach M52 carbon / M56 pricing. Cite file:line.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 4,
         "phase_gate": "M58 default v2 verified (default.cfg:1853; {v2,off}). PARAMETERIZATION correct: endogenous area x exogenous time-invariant IPCC EFs (f58_ipcc_wetland_ef from f58_ipcc_wetland_ef2.cs3) via q58_peatland_emis_detail(84-87)/q58_peatland_emis(91-94); EF values match input file. BYPASS-M52 claim CORRECT (verified 3 ways): M58 never touches vm_carbon_stock (grep empty); peatland in emis_annual not emis_oneoff (core/sets.gms:320-323); routes vm_emissions_reg(i,peatland,poll58) -> q56_emis_pricing -> vm_emission_costs -> M11. NOT the vm_carbon_stock/q56_emis_pricing_co2 path.",
         "notes": "Clean (10). 4 Informational (pseudocode time-index drop; EF-unit source inconsistency cs3-vs-input.gms header; benign cite widths; .fx-vs-declaration label). No doc fixes; load-bearing claims (module_58.md, module_56.md) code-consistent."},

        {"id": "R43-Q4", "archetype": "cost aggregation", "modules_tested": [39, 40, 34, 11, 10],
         "question": "Trace two cost components into the objective: (a) land-conversion costs (M39) - variable, equation, trigger; (b) transport costs (M40) - variable + what it scales with; (c) how urban land (M34) is treated re land conversion. Name vm_cost_* variables, cite file:line.",
         "score": 9, "bugs_found": 1, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 1,
         "phase_gate": "All defaults + cost-var attribution correct (the high-error class held): M39 calib vm_cost_landcon(j,land) q39_cost_landcon (annuity r/(1+r), target-land-type); M40 gtap_nov12 vm_cost_transp(j,k) q40_cost_transport (vm_prod x f40_distance x f40_transport_costs) - got the vm_cost_transp-vs-vm_cost_transport trap right; M34 exo_nov21 two-channel (vm_cost_landcon(j,urban) via M39 ~12300 + vm_cost_urban steering penalty 1e6 via q34_urban_cell). M11 aggregation lines verified.",
         "notes": "R43-Q4-B1 Minor answerer_confabulation: register-table gives vm_cost_urban declaration as scaling.gms:8/equations.gms:25-26; actual declarations.gms:13 (body text correct) - no doc fix. 1 Informational: f40_distance cite 15-21 vs actual 14-21."},

        {"id": "R43-Q5", "archetype": "causal chain", "modules_tested": [73, 14, 52, 32, 35],
         "question": "How is timber demand satisfied? (a) M73 default realization + what drives demand; (b) production variable + how harvest draws on standing stock; (c) how harvesting interacts with M52 carbon. Cite file:line.",
         "score": 8, "bugs_found": 2, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 2, "bugs_informational": 0,
         "phase_gate": "M73 default 'default' (sole; default.cfg:2205). Timber demand exogenous in preloop (Lauri 2019/Morland 2018, saturate >10000 USD17PPP, M09 GDP/pop) -> pm_demand_forestry. Production q73_prod_wood/woodfuel; M32 q32_prod_forestry + M35 q35_prod_* supply via harvested area x im_growing_stock/timestep -> vm_prod(kforestry). NO-HWP claim CORRECT: c_pools=/vegc,litc,soilc/ only (core/sets.gms:324-325), no harvested-wood-product carbon pool anywhere; harvest -> area drop -> vm_carbon_stock drop -> q52_emis_co2_actual(16-19) emits in full. Producer/consumer correct (M52 READS vm_carbon_stock; M32/M35 POPULATE).",
         "notes": "R43-Q5-B1/B2 two Minor answerer_confabulation: Churkina construction-wood cite preloop.gms:66-69 (actual 72-75) + linear ramp 71-74 (actual 78-80) - ~6 lines early, concept correct. No doc fix (docs correct)."},

        {"id": "R43-G1", "archetype": "default realization (regression anchor)", "modules_tested": [14],
         "question": "What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0,
         "regression_id": "G1", "drift_observed": False,
         "phase_gate": "drift FALSE. managementcalib_aug19 sole+default (default.cfg:354; module.gms:31); exactly 2 equations q14_yield_crop(14-16)+q14_yield_past(35-39) char-exact; no q14_yieldcalib; s14_yld_past_switch=0.25 (input.gms:20).",
         "notes": "Clean anchor, stable 10. No doc fixes."},

        {"id": "R43-G2", "archetype": "causal chain (regression anchor)", "modules_tested": [52, 56, 29, 31, 32, 34, 35, 59],
         "question": "Walk through how vm_carbon_stock is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 1,
         "regression_id": "G2", "drift_observed": False,
         "phase_gate": "drift FALSE, score 10 (up from R41's 9). Declaration M56 price_aug22/declarations.gms:34; populator set {29,31,32,34,35,59} exact incl M34-.fx-to-0; M52 reader q52_emis_co2_actual(16-19); full M56 chain exact; c56_carbon_stock_pricing=actualNoAcEst. §1.5 populator-set doc (module_52.md:424, module_56.md:583/1074) still CORRECT - R22->R26 regression stays fixed.",
         "notes": "Clean (10). 1 Informational: Chapman-Richards exponent ^ vs GAMS ** (exempt, exponent math). No doc fixes; no latent §1.5 bug."}
    ]
}

d["rounds"].append(r43)
for g in d.get("regression_questions", []):
    if g.get("id") in ("G1", "G2"):
        if 43 not in g.setdefault("used_in_rounds", []):
            g["used_in_rounds"].append(43)
        g["drift_observed"] = False

cs = d["cumulative_stats"]
cs["total_rounds"] = 43
# R8 renamed these keys to approx_* (orphaned-counter relabel); use the new names.
cs["approx_total_bugs_found"] = cs.get("approx_total_bugs_found", 0) + 9
cs["approx_total_bugs_fixed"] = cs.get("approx_total_bugs_fixed", 0) + 0
cs["last_validation_date"] = "2026-06-03"
cs["mean_score_trend"] = cs.get("mean_score_trend", "") + "->R43 validate-teammate-edits + periphery: raw 9.57 (HIGHEST on record), doc_quality 10.0, ZERO doc bugs; teammate f4f44b0 module_80.md+module_37.md validated ACCURATE; M58 peatland bypasses M52 (parameterized), M73 no-HWP verified; G1=10 G2=10 drift FALSE"

# IMPORTANT: indent=1, ensure_ascii=True to match the file's existing format (else 5500-line reformat)
json.dump(d, open(PATH, "w"), indent=1, ensure_ascii=True)
print("R43 appended OK (indent=1, ensure_ascii=True).")
print("total_rounds:", cs["total_rounds"], "| approx_bugs_found:", cs["approx_total_bugs_found"], "| approx_bugs_fixed:", cs["approx_total_bugs_fixed"])
