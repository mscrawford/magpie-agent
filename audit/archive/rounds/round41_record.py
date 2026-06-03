#!/usr/bin/env python3
"""Append R41 entry to validation_rounds.json and update cumulative_stats + regression anchors."""
import json, sys

PATH = "/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/audit/validation_rounds.json"
d = json.load(open(PATH))

# guard: don't double-append
if any(r.get("round") == 41 for r in d["rounds"]):
    print("R41 already present — aborting to avoid duplicate.")
    sys.exit(1)

r41 = {
    "round": 41,
    "date": "2026-06-03",
    "commit_before": "8727e7f (magpie-agent main); MAgPIE develop @ ee98739fd",
    "commit_after": "pending (R41 doc fixes recorded together with this entry; not yet committed/pushed)",
    "answerer_model": "claude-sonnet-4-6 (Agent model:sonnet, magpie-helper)",
    "auditor_model": "claude-opus-4-8 (Agent model:opus, general-purpose)",
    "type": "full",
    "scope": ("First classic question-based round (GENERATE->ANSWER->AUDIT) since R29. R30-R40 were a doc-centric audit sweep "
              "that revised the whole 46-module corpus + reference docs (~191 confirmed bugs fixed) but never stress-tested it "
              "with adversarial Q&A. R41 = post-doc-push capability check: 5 new probes biased to high-centrality modules and "
              "the highest-yield bug classes (default-realization discipline = R3 Critical-anchor territory; cross-module chains), "
              "one per archetype, + regression anchors G2 (fragile carbon-stock chain) and G4 (magpie4 getReport; drifted at R37). "
              "Answerers docs-only (+config/default.cfg per Step 1c); auditors verified vs live GAMS at develop ee98739fd. "
              "Probe-dedup: clean (all ledger entries retire_after<=35, every name re-probable at R41)."),
    "summary": {
        "total_bugs_reported_by_auditors": 13,
        "auditor_false_positives_withdrawn": 0,
        "total_bugs_net": 13,
        "bugs_by_severity": {"critical": 0, "major": 3, "minor": 7, "informational": 3},
        "bugs_by_root_cause": {
            "doc_error": 3,
            "doc_error_answerer_beat_it": 1,
            "answerer_confabulation": 6,
            "answerer_style_or_framing": 3
        },
        "mean_score": 8.43,
        "doc_quality_mean": 8.83,
        "n_questions_doc_quality": 6,
        "doc_quality_mean_method": ("Raw mean=(6+10+10+7+8+9+9)/7=8.43. doc_quality excludes Q1 (score 6 driven entirely by "
                                    "answerer citation-fabrication against verified-correct module_15.md headers; Q1's only doc issue "
                                    "was a Minor module_09 line-label latent, fixed, non-score-affecting) per the R27 pure-answerer-drag "
                                    "precedent: (10+10+7+8+9+9)/6=8.83. mean_score stays raw for trend."),
        "score_range": [6, 10],
        "regression_anchors": {
            "G2": {"score": 9.0, "drift_observed": False,
                   "trend": ("STABLE. Spine exact: declaration in M56 price_aug22/declarations.gms:34 (not M52); populator set "
                             "{29,31,32,34,35,59} correct incl M34-via-.fx-to-0 (exo_nov21/presolve.gms:8) which an =e= grep alone "
                             "would miss; M52 reader q52_emis_co2_actual (normal_dec17/equations.gms:16-19); M56 chain intact. "
                             "Post-R26 populator-set recovery (the immutable sec-1.5 anchor) HELD - module_52.md/module_56.md still correct. "
                             "1 Minor = answerer citation-span looseness on q56_emission_cost_oneoff (45-52 vs cited 35-52), not a doc bug.")},
            "G4": {"score": 9.0, "drift_observed": False,
                   "trend": ("RECOVERED from R37 drift. Auditor re-counted from the SHA-pinned clone: 106 unique / 117 total report* "
                             "calls (R37 confabulated 101). Clone SHA a360d8c9ec EXACT match to version_pins.json (v2.70.0); NO control "
                             "arg, NO grepl gating confirmed. 1 Minor doc_error = helper line-range label '62-181' presented as the "
                             "getReport function range; relabeled (function L56-235, tryList block L62-182). The 106 count in the helper "
                             "(Pitfall 5) was already correct and kept.")}
        },
        "gate_summary": ("No numeric gate. Raw mean 8.43 sits ABOVE the last classic-round band (R27 7.1, R28 8.4, R29 7.9), "
                         "confirming the R30-R40 doc-centric push holds up under adversarial Q&A. Two Critical immutable anchors NOT "
                         "reproduced: R3 (livestock default feed-basket realization) - fbask_jan16 verified as the CURRENT default "
                         "(historical fbask_jul23 no longer exists on develop), Q2=10; R16 (age-class truncation) - ac set verified 62 "
                         "elements ac0-ac300+acx, Q3=10. Real finds were 2 Major doc bugs of the 'missing default caveat' / wrong-"
                         "attribution class: module_56.md emis-policy table marked CH4/N2O unpriced under the DEFAULT reddnatveg_nosoil "
                         "policy (CSV proves both priced for ag sources); module_22.md listed M13 as an unconditional direct consumer of "
                         "pm_land_conservation when its read is gated by c13_croparea_consv=0 (default OFF). Both fixed."),
        "bugs_fixed_this_session": 4,
        "bugs_fixed_detail": ("(1) module_56.md:661 + :499 (Q4, Major doc_error): emis-policy table row for reddnatveg_nosoil marked "
                              "CH4 and N2O as not-priced; corrected both to priced-for-ag-sources per f56_emis_policy.csv:115-120 "
                              "(ch4: awms/resid_burn/rice/ent_ferm/peatland; n2o_n_direct+indirect: inorg_fert/man_crop/awms/resid/"
                              "resid_burn/man_past/som/rice/peatland), and augmented the :499 bullet to state the policy is 'nosoil' "
                              "not 'CO2-only' and that price level is the separate c56_pollutant_prices switch. "
                              "(2) module_22.md x7 locations (Q5, Major doc_error, reclassified from auditor's tentative answerer_confab "
                              "after confirming the doc carries M13 un-caveated): lines 11, 542-block(+gating line+File-line), 604, 744, "
                              "1332, 1359, 1425 - M13 (TC) was listed as an unconditional DIRECT CONSUMER of pm_land_conservation; "
                              "marked it CONDITIONAL/default-OFF (gated by c13_croparea_consv=1, default 0 per config/default.cfg:309 + "
                              "13_tc/endo_jan22/input.gms:12; read at presolve.gms:40 inside if at :38). "
                              "(3) agent/helpers/magpie4_reference.md:45 + :259 (G4, Minor doc_error): line-range label '62-181' presented "
                              "as the getReport function range; relabeled to function L56-235 / tryList dispatch block L62-182. The 106-"
                              "unique count (Pitfall 5) was correct and kept. "
                              "(4) module_09.md:175 + :212 (Q1, Minor doc_error_answerer_beat_it / latent): 'Calculation' header pointed at "
                              "preloop.gms raw-value lines (i09_*_raw) for the im_*_iso entries; relabeled 'Raw calculation ... the im_* "
                              "interface is the scenario-selected slice assigned later in preloop'. Non-score-affecting precision cleanup."),
        "bugs_deferred": 0,
        "not_fixed_detail": ("No doc fixes deferred. The 6 answerer_confabulation Minors/Major (Q1 citation cluster x3, Q4 tC/tCO2 "
                             "conversion inversion, Q5 p22_wdpa_baseline index imprecision, G2 citation-span) need NO doc fix - the "
                             "underlying docs are correct (auditors verified module_15.md headers, the x12/44 conversion in "
                             "module_56.md:464, p22_wdpa_baseline declaration, and the q56 chain are all right; the answerers were sloppy). "
                             "The 3 Informational (Q2 x2 indexing/attribution looseness, Q3 calibrated-vs-uncalib density prose) are not "
                             "doc bugs."),
        "validators": ("validate_consistency.sh: 39/43 passed, 4 advisory warnings, 0 errors, verdict PASS. The 4 warnings are ALL "
                       "pre-existing and unchanged by R41 (4 before = 4 after): CLAUDE.md-refs in 4 untouched files "
                       "(session_cleanup.md/directory_structure.md/README.md/get_under_control_plan.md), cross-cutting-identifier "
                       "advisory, multi-section-arity advisory, doc-unit advisory. R41 introduced 0 new warnings. Process note: the "
                       "first post-fix run FAILED on 1 self-introduced error - a bare cross-module citation 'endo_jan22/input.gms:12' in "
                       "module_22.md (MANDATE-16 full-path); corrected to 'modules/13_tc/endo_jan22/input.gms:12' and the full re-run "
                       "cleared to PASS."),
        "run_context": ("Interactive run 2026-06-03, user-requested two-round flywheel (R41 then R42). magpie-agent main @ 8727e7f; "
                        "MAgPIE develop tracked code clean @ ee98739fd (verification ground truth). Commits LOCAL pending - nothing "
                        "pushed yet; user to decide on commit/push at wrap-up. Orchestrator re-verified BOTH Major doc bugs against live "
                        "code before editing (module_56 emis-policy CSV; c13_croparea_consv default + the gated read) per the R29 "
                        "process discipline (auditors and docs can both be imprecise on attribution)."),
        "highlights": [
            "First classic question-based round since R29: raw mean 8.43 ABOVE the R27-29 band (7.1/8.4/7.9) - the R30-R40 doc-centric push holds under adversarial Q&A.",
            "R3 Critical anchor (livestock default feed-basket realization) NOT reproduced: fbask_jan16 verified as the CURRENT default; the historical fbask_jul23 no longer exists on develop. Q2=10.",
            "R16 Critical anchor (age-class truncation) NOT reproduced: ac set verified 62 elements (ac0-ac300 + acx, core/sets.gms:269-275). Q3=10.",
            "G2 stable (9, drift FALSE): post-R26 populator-set recovery HELD; answerer correctly characterized M34's .fx-to-0 population that an =e= grep alone would miss.",
            "G4 recovered (9, drift FALSE): re-count from the SHA-pinned clone = 106 unique report* (R37 drift was 101); clone SHA matches version_pins.json exactly; helper line-range label tightened.",
            "2 Major doc bugs found + fixed, both high-harm default/attribution class: module_56 emis-policy table (CH4/N2O wrongly unpriced under default policy) and module_22 M13-consumer (missing default-OFF caveat).",
            "Process: validator caught a self-introduced bare-path citation; full re-run cleared to PASS. Demonstrates the 'rerun-full-clear-before-ship' discipline working as intended."
        ]
    },
    "questions": [
        {"id": "R41-Q1", "archetype": "cross-module causal chain", "modules_tested": [9, 15, 16, 17],
         "question": "In MAgPIE's DEFAULT config, trace how socioeconomic drivers (M09) propagate into food demand then production: (a) default SSP/driver scenario + where set; (b) vars/params carrying population + per-capita income from M09 into M15; (c) how per-capita demand becomes total demand entering M16/M17. Name pm_*/im_* drivers + vm_* food-demand vars, cite file:line.",
         "score": 6, "bugs_found": 4, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 2, "bugs_informational": 0,
         "phase_gate": "Spine fully correct: SSP2 default; im_pop/im_pop_iso/im_gdp_pc_ppp_iso/im_demography/im_physical_inactivity all exist with exact names; q15_food_demand reproduced exactly (per-capita kcal x im_pop x 365); vm_dem_food -> q16_supply_* -> vm_supply -> M21 -> vm_prod_reg chain right. No invented names.",
         "notes": "Major + 2 Minor = answerer_confabulation: the (b)-table fabricated source line numbers (cited module_15.md markdown-render lines 57/105/258 as source; actual 13/52/143) - contradicts the answer's own correct prose cites. Docs (module_15.md headers) verified correct -> NO doc fix for these. EXCLUDED from doc_quality_mean (pure answerer drag, R27 precedent). Separately a Minor latent doc_error_answerer_beat_it in module_09.md:175/212 (the 'Calculation' label points at raw i09_*_raw lines, not the im_ assignment) - FIXED (relabeled 'Raw calculation').",
         "doc_errors_latent": ["module_09.md:175,212 - 'Calculation (preloop.gms:NN)' headers point at the raw i09_*_raw computation rather than the im_* interface assignment; Minor; FIXED (relabeled)."]},

        {"id": "R41-Q2", "archetype": "default-vs-switch + chain", "modules_tested": [70, 30, 31, 14, 16, 21],
         "question": "In MAgPIE's DEFAULT config, trace the cascade from livestock feed demand (M70) to crop+pasture production: (a) DEFAULT feed-basket realization of M70 + where set; (b) parameter holding feed baskets + variable carrying feed demand into crop demand; (c) how feed demand reaches M30 cropland + M31 pasture, and how M14 yields mediate land. Cite file:line.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 2,
         "phase_gate": "R3 CRITICAL ANCHOR NOT REPRODUCED. fbask_jan16 verified DEFAULT (config/default.cfg:2146; ls 70_livestock/ = only fbask_jan16 + fbask_jan16_sticky; no fbask_jul23 on develop). All 6 equations verbatim (q70_feed 17-20 =g=, q16_supply_crops 19-29, q16_supply_pasture 62-63, q30_prod 14-15, q31_prod 16-18 =l=, q14_yield_crop 14-16, q14_yield_past 35-39). M70->M14 side channel (pm_past_mngmnt_factor) VERIFIED not confabulated: assigned only in fbask_jan16/presolve.gms:64,66-67, read only by q14_yield_past.",
         "notes": "Clean. 2 Informational (not scored): im_feed_baskets indexing shorthand; loose 'M21 creates vm_prod_reg' (M17 defines it). No doc fixes - load-bearing doc claims (module_70/14/16) all verified accurate."},

        {"id": "R41-Q3", "archetype": "timing/sequencing", "modules_tested": [28, 32, 52],
         "question": "How do age classes (M28) govern forest growth + carbon accumulation? (a) FULL extent of the age-class set (exact last element + total count); (b) in M32 how stands move between age classes over time (per-timestep shift vs growth) + what governs the rate; (c) how standing biomass feeds carbon stock in M52. Name variables, cite file:line.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 1,
         "phase_gate": "R16 CRITICAL ANCHOR NOT REPRODUCED. ac set verified 62 elements (ac0-ac300 5-yr steps + acx, core/sets.gms:269-275). Defaults verified M28=oct24, M32=dynamic_may24, M52=normal_dec17. s32_shift=m_yeardiff_forestry(t)/5 (presolve.gms:83) deterministic presolve aging + overflow to acx. Chapman-Richards m_growth_vegc (core/macros.gms:18) + bisection-to-FRA-2025 calibration (preloop.gms:23-118) VERIFIED real, not confabulated. q52_emis_co2_actual (pcm-vm)/m_timestep_length token-exact (equations.gms:16-19).",
         "notes": "Clean. 1 Informational: ndc density called 'calibrated' in prose but the answer's own table maps ndc->uncalib correctly 3 lines later. Non-scoring location nit: ac set lives in core/sets.gms, answer said 28_ageclass/oct24/sets.gms (which holds only ac_gfad/ac_young) - count/last-element (the anchor target) stated exactly right. No doc fixes."},

        {"id": "R41-Q4", "archetype": "default-vs-switch", "modules_tested": [56, 57, 51, 52, 53],
         "question": "In MAgPIE's DEFAULT config, are GHG emissions priced? (a) default GHG-price switch value + objective implication; (b) if OFF by default, what that means for M57 MACC abatement; (c) which emission types (N2O M51, CH4 M53, CO2 M52) priced once enabled. Name c56_*/s56_* switch, cite default.cfg + equation file:line.",
         "score": 7, "bugs_found": 2, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 1, "bugs_informational": 0,
         "phase_gate": "Headline CORRECT (Critical default-state trap passed): emissions effectively not priced by default - c56_pollutant_prices=R34M410-SSP2-NPi2025 (~$0), muted until 2030. All cited default strings VERIFIED exact (c56_pollutant_prices default.cfg:1713, c56_mute_ghgprices_until:1726, c56_emis_policy reddnatveg_nosoil:1810, s56_minimum_cprice 3.67:1729). M57 ord(maccs_steps)>1 guard + s57_maxmac=-1 verified. M56 price_aug22 / M57 on_aug22 sole realizations.",
         "notes": "R41-Q4-B1 Major doc_error: module_56.md:661 emis-policy table marked CH4 and N2O as NOT priced under default reddnatveg_nosoil; f56_emis_policy.csv:115-120 proves both ARE priced for ag sources. Answer mirrored the wrong table. FIXED (table row + :499 bullet). R41-Q4-B2 Minor answerer_confabulation: '$3.67/tC ~ $13.4/tCO2' inverts the x12/44 conversion (correct ~$1.00/tCO2); docs + code correct (module_56.md:464) -> no doc fix.",
         "doc_errors_latent": []},

        {"id": "R41-Q5", "archetype": "conservation law", "modules_tested": [22, 35, 10, 29, 31, 32, 13],
         "question": "How do conservation/protected-area constraints (M22) restrict land-use change? (a) DEFAULT conservation realization/scenario + data source defining protected areas; (b) which land pools/vars constrained + by what equation/bound; (c) interaction with M35 natveg + M10 land balance. Name var(s)/param(s), cite file:line.",
         "score": 8, "bugs_found": 2, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 1, "bugs_informational": 0,
         "phase_gate": "Spine correct: sole realization area_based_apr22 (default); c22_base_protect=WDPA (cfg:723), c22_protect_scenario=none (cfg:755); pm_land_conservation(t,j,land,consv_type) decl:15, consv_type={protect,restore}; M22 has no equations; q35_natveg_conservation =g= over land_natveg (equations.gms:19-22) + v35_secdforest.lo per-age-class; q10_land_area =e= and never reads the parameter (M10 transitive only). Verified consumer set: M35/M29/M31/M32 read unconditionally; M13 read is gated default-OFF; M10 transitive.",
         "notes": "R41-Q5-B1 Major doc_error (reclassified from auditor's tentative answerer_confab after confirming the doc): module_22.md lists M13 (TC) as an unconditional DIRECT CONSUMER of pm_land_conservation in 7 places, but M13's read (13_tc/endo_jan22/presolve.gms:40) is gated by if(c13_croparea_consv=1, at :38; default 0 (config/default.cfg:309, input.gms:12) -> M13 is NOT a consumer in a default run. Missing-default-caveat class. FIXED all 7 locations. R41-Q5-B2 Minor answerer_confabulation: p22_wdpa_baseline cited over (wdpa_cat22,land) but declared over base22 (declarations.gms:13) - recoverable, no doc fix.",
         "doc_errors_latent": ["module_22.md:11,542,604,744,1332,1359,1425 - M13 listed as unconditional direct consumer of pm_land_conservation without the c13_croparea_consv=0 default-OFF caveat; Major by future-reader harm (R20 consumer-attribution anchor class); FIXED all 7."]},

        {"id": "R41-G2", "archetype": "causal chain (regression anchor)", "modules_tested": [52, 56, 29, 31, 32, 34, 35, 59],
         "question": "Walk through how vm_carbon_stock is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.",
         "score": 9, "bugs_found": 1, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 0,
         "regression_id": "G2", "drift_observed": False,
         "phase_gate": "drift FALSE. Declaration in M56 (price_aug22/declarations.gms:34, not M52); populator set {29,31,32,34,35,59} exact incl M34-via-.fx-to-0 (exo_nov21/presolve.gms:8); M52 reader q52_emis_co2_actual (normal_dec17/equations.gms:16-19); M56 chain q56_emis_pricing_co2 -> v56_emis_pricing -> q56_emission_cost_oneoff -> v56_emission_cost -> q56_emission_costs -> vm_emission_costs(i) intact. Post-R26 sec-1.5 recovery HELD.",
         "notes": "1 Minor answerer citation-span (q56_emission_cost_oneoff cited 35-52, equation at 45-52; 10-line comment lead-in). Docs verified correct (module_52.md:424, module_56.md:583/616/1037) - no doc bug. Anchor stable, no latent."},

        {"id": "R41-G4", "archetype": "R-to-GAMS / magpie4 structural (regression anchor)", "modules_tested": ["magpie4 helper", "magpie4 source"],
         "question": "How does magpie4::getReport organize its reporting? Describe the dispatch pattern, how many unique report* functions it calls, and cite the file:line range from the pinned clone.",
         "score": 9, "bugs_found": 1, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 0,
         "regression_id": "G4", "drift_observed": False,
         "phase_gate": "drift FALSE - R37 drift RECOVERED. Auditor re-counted from the SHA-pinned clone: 106 unique / 117 total report* calls (R37 confabulated 101). Clone SHA a360d8c9ec EXACT match to version_pins.json (v2.70.0). NO control arg, NO grepl gating confirmed. Answer correctly stated 106 and flagged the prior plan's 108.",
         "notes": "1 Minor doc_error: helper line-range label '62-181' presented as the getReport function range; function is L56-235, tryList dispatch block L62-182. FIXED (magpie4_reference.md:45, :259). The 106-unique count (Pitfall 5) was already correct and kept.",
         "doc_errors_latent": ["agent/helpers/magpie4_reference.md:45,259 - '62-181' labeled as getReport function range; should be function L56-235 / tryList block L62-182; Minor; FIXED."]}
    ]
}

d["rounds"].append(r41)

# update regression_questions used_in_rounds + last drift
for g in d.get("regression_questions", []):
    if g.get("id") == "G2":
        if 41 not in g.setdefault("used_in_rounds", []):
            g["used_in_rounds"].append(41)
        g["drift_observed"] = False
    if g.get("id") == "G4":
        if 41 not in g.setdefault("used_in_rounds", []):
            g["used_in_rounds"].append(41)
        g["drift_observed"] = False

# update cumulative_stats
cs = d["cumulative_stats"]
cs["total_rounds"] = 41
cs["total_bugs_found"] = cs.get("total_bugs_found", 0) + 13
cs["total_bugs_fixed"] = cs.get("total_bugs_fixed", 0) + 4
cs["last_validation_date"] = "2026-06-03"
cs["mean_score_trend"] = cs.get("mean_score_trend", "") + "->R41 classic Q-round post-doc-push: raw 8.43 / docq 8.83; G2=9 G4=9 (both drift FALSE, G4 recovered 106 from R37's 101); R3+R16 Critical anchors NOT reproduced (Q2=10,Q3=10); 2 Major doc bugs fixed (M56 emis-table CH4/N2O, M22 M13 default-OFF caveat)"

json.dump(d, open(PATH, "w"), indent=2, ensure_ascii=False)
print("R41 appended OK.")
print("total_rounds:", cs["total_rounds"], "| total_bugs_found:", cs["total_bugs_found"], "| total_bugs_fixed:", cs["total_bugs_fixed"])
print("G2 used_in_rounds:", [g["used_in_rounds"] for g in d["regression_questions"] if g["id"]=="G2"][0])
print("G4 used_in_rounds:", [g["used_in_rounds"] for g in d["regression_questions"] if g["id"]=="G4"][0])
