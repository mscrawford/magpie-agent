#!/usr/bin/env python3
"""Append R42 entry to validation_rounds.json and update cumulative_stats + G1/G3 anchors."""
import json, sys

PATH = "/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/audit/validation_rounds.json"
d = json.load(open(PATH))

if any(r.get("round") == 42 for r in d["rounds"]):
    print("R42 already present — aborting to avoid duplicate.")
    sys.exit(1)

r42 = {
    "round": 42,
    "date": "2026-06-03",
    "commit_before": "8727e7f (magpie-agent main); MAgPIE develop @ ee98739fd",
    "commit_after": "pending (R41+R42 doc fixes recorded together; not yet committed/pushed)",
    "answerer_model": "claude-sonnet-4-6 (Agent model:sonnet, magpie-helper)",
    "auditor_model": "claude-opus-4-8 (Agent model:opus, general-purpose)",
    "type": "full",
    "scope": ("Second round of the user's two-round request, FOLLOWING ON from R41. Three design drivers: (1) dedup - R41 locked "
              "its 18 probed modules to retire_after=44, so R42 centered on different modules; (2) DEEPEN the one fragile area R41 "
              "surfaced - M56 emissions (R41-Q4 found a Major emis-policy-table bug); R42-Q1 was designed to catch the suspected "
              "sibling defect at module_56.md:662, and DID; (3) fill the archetypes R41 missed - quantitative (Q3), edge-case/failure "
              "(Q4), R-to-GAMS provenance (Q5), parameterization-vs-mechanism (Q2). Regression anchors rotated to G1 + G3. Answerers "
              "docs-only (+config); auditors verified vs live GAMS at develop ee98739fd + the SHA-pinned magpie4 clone. Probe-dedup clean."),
    "summary": {
        "total_bugs_reported_by_auditors": 11,
        "auditor_false_positives_withdrawn": 0,
        "total_bugs_net": 11,
        "bugs_by_severity": {"critical": 1, "major": 0, "minor": 1, "informational": 9},
        "bugs_by_root_cause": {
            "doc_error": 1,
            "doc_error_answerer_beat_it": 0,
            "answerer_confabulation": 1,
            "answerer_style_or_framing": 9
        },
        "mean_score": 9.29,
        "doc_quality_mean": 9.29,
        "n_questions_doc_quality": 7,
        "doc_quality_mean_method": ("Raw mean=(5+10+10+10+10+10+10)/7=9.29. No question excluded: the only sub-10 score (Q1=5) was "
                                    "driven by a doc_error (module_56.md:662 sibling bug, reproduced by the answerer), NOT pure answerer "
                                    "noise, so Q1 stays IN per the rule (exclude only exclusively-answerer_confab questions). All other "
                                    "questions clean (10). doc_quality_mean == raw this round."),
        "score_range": [5, 10],
        "regression_anchors": {
            "G1": {"score": 10.0, "drift_observed": False,
                   "trend": ("STABLE. managementcalib_aug19 sole+default (config/default.cfg:354); exactly 2 equations q14_yield_crop "
                             "(equations.gms:14-16) + q14_yield_past (35-39), verbatim; no fabricated q14_yieldcalib (R22 correction "
                             "holds); s14_yld_past_switch=0.25 + 25% prev-timestep tau spillover correct. Consistent 10 across R22/23/25/26/27/29/42.")},
            "G3": {"score": 10.0, "drift_observed": False,
                   "trend": ("STABLE + pin FRESH. version_pins.json = magpie4 v2.70.0 @ a360d8c9ec (resolution sha, captured 2026-05-25); "
                             "the auditor confirmed it MATCHES ../input/renv.lock (Packages.magpie4 Version+RemoteSha) and the "
                             "lock_file_sha256 canary is identical live - pin NOT stale. Answer read version_pins.json (not the drift-prone "
                             "workspace clone, correctly flagged v2.75.1 HEAD), named renv.lock as authority, cited sync_magpie4_clone.py. "
                             "G3 last run R28; recovered cleanly.")}
        },
        "gate_summary": ("No numeric gate. Raw mean 9.29 - the HIGHEST classic-round mean since R25 (8.93) and well above R41's 8.43. Six of "
                         "seven questions scored 10. The follow-on design WORKED: R42-Q1, written specifically to re-probe the M56 emis-policy "
                         "area found fragile in R41-Q4, caught the predicted SIBLING bug (module_56.md:662 redd+natveg_nosoil wrongly marked "
                         "CH4/N2O unpriced; the CSV proves the +-policy is byte-identical to the default on all non-CO2 rows, differing only by "
                         "adding forestry vegc+litc CO2). That single doc_error drove Q1 to 5. Both regression anchors clean (G1=10, G3=10, no "
                         "drift; G3 pin verified fresh vs renv.lock). Two notable correct-handlings: Q2 nailed the parameterization-vs-mechanism "
                         "discipline (M45 = static Koppen classification, climate via exogenous LPJmL input, NOT mechanistic); Q3 verified the "
                         "suspicious-looking macceff_aug22 IS M50's genuine default and dodged the 'surplus exported to M51' trap."),
        "bugs_fixed_this_session": 1,
        "bugs_fixed_detail": ("(1) module_56.md:662 (Q1, Critical doc_error): the redd+natveg_nosoil emis-policy table row marked CH4 and "
                              "N2O as not-priced (the exact sibling of the reddnatveg_nosoil bug fixed in R41). Corrected both to priced-for-"
                              "ag-sources (identical sets to the default row 661) per f56_emis_policy.csv rows 243 (ch4: awms/resid_burn/rice/"
                              "ent_ferm/peatland) + 244/248 (n2o_direct+indirect: inorg_fert/man_crop/awms/resid/resid_burn/man_past/som/rice "
                              "+ indirect N), which are byte-identical to the default policy; also corrected the CO2 gloss from "
                              "'(deforestation + reforestation)' to 'reddnatveg sources + forestry vegc+litc (plantation CO2)' per the co2_c "
                              "row 242 (the + adds forestry_vegc+forestry_litc only). Confirmed the other table rows (none/all/all_nosoil/"
                              "sdp_all) are correct, so 661+662 were the only two defects."),
        "bugs_deferred": 0,
        "not_fixed_detail": ("No doc fixes deferred. The 1 Minor (Q1 'only 4 scenarios price ag CH4/N2O' - actually 33 of 44) is "
                             "answerer set-incompleteness, not a doc bug. The 9 Informational are index-label/terminology slips against "
                             "CORRECT docs (Q2 f14_yields/f59 index labels; Q3 'free variable' vs declared positive variable - the doc "
                             "itself says 'endogenous optimization variable', so no doc carries the slip; Q4 macro line + sum-wrapper "
                             "simplifications; Q5 GJ-unit label + helper line-range). OPTIONAL (not done): a one-line magpie4_reference.md "
                             "note that bioenergy demand has its own reportDemandBioenergy function (the helper curates ~4 entry points/theme "
                             "by design - process_gap, not a doc_error)."),
        "validators": ("validate_consistency.sh: 39/43 passed, 4 advisory warnings, 0 errors, verdict PASS - identical to the R41 post-fix "
                       "baseline; R42's single edit introduced 0 new warnings/errors. The 4 warnings remain the pre-existing advisory set "
                       "(CLAUDE.md-refs in 4 untouched files, cross-cutting-identifier, multi-section-arity, doc-unit)."),
        "run_context": ("Interactive run 2026-06-03, second of the user's two-round request, immediately after R41. magpie-agent main @ "
                        "8727e7f; MAgPIE develop clean @ ee98739fd. Commits LOCAL pending (R41+R42 together) - nothing pushed; user to "
                        "decide commit/push at wrap-up. Orchestrator re-verified the Critical :662 doc fix directly against "
                        "f56_emis_policy.csv (rows 114/115/116 vs 242/243/244/248) before editing."),
        "highlights": [
            "Raw mean 9.29 - highest classic-round mean since R25; 6 of 7 questions scored 10. The R30-R40 doc-push corpus is in strong shape under adversarial Q&A.",
            "FOLLOW-ON SUCCESS: R42-Q1 was designed to re-probe the M56 emis-policy area R41-Q4 flagged, and caught the predicted sibling bug at module_56.md:662 (redd+natveg_nosoil CH4/N2O wrongly ✗). Fixed; the table is now internally consistent.",
            "Parameterization discipline (Q2=10): agent correctly framed climate as PARAMETERIZATION (static Koppen M45 + exogenous LPJmL yield/SOM inputs), not mechanistic in-model climate - the 'uses data about X != models X' rule held.",
            "Wrong-realization trap dodged (Q3=10): the MACC-sounding macceff_aug22 is M50's genuine sole default (MACC mitigation of SNUpE); answer verified rather than assuming.",
            "Edge-case water (Q4=10): EFR-via-vm_watdem.fx(ecosystem), fossil-groundwater x1.01 buffer, and v44_bii_missing all verified real; M44-has-no-direct-water-pathway confirmed both directions.",
            "magpie4 provenance (Q5=10) + G3 pin verified FRESH against renv.lock (SHA256 canary match) - the version-pin discipline the agent relies on for correct magpie4 reads is sound.",
            "G1=10 G3=10, both drift FALSE. Across R41+R42 all four anchors (G1,G2,G3,G4) exercised with zero drift; G4's R37 regression recovered (R41)."
        ]
    },
    "questions": [
        {"id": "R42-Q1", "archetype": "quantitative + chain (follow-on of R41-Q4)", "modules_tested": [56, 52, 11],
         "question": "Once a nonzero CO2 price is active, trace how a tonne of LUC CO2 becomes a cost in the objective: (a) how f56_emis_policy selects priced (pollutant,source) pairs; (b) pricing chain to vm_emission_costs; (c) where it enters the M11 objective. Which non-default c56_emis_policy scenarios price ag CH4/N2O, and does redd+natveg_nosoil?",
         "score": 5, "bugs_found": 2, "bugs_critical": 1, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 0,
         "phase_gate": "Chain mechanics (a)(b)(c) FLAWLESS, all verified exact: f56_emis_policy 0/1 gate x im_pollutant_prices (preloop.gms:84-91, historical override forces reddnatveg_nosoil for yrs<=sm_fix_SSP2); q56_emis_pricing_co2 (equations.gms:19-22, uses vm_carbon_stock actualNoAcEst, bypasses vm_emissions_reg); one-off annuity x m_timestep_length x price x r/(1+r) (45-52); q56_emission_costs->vm_emission_costs (56-58); vm_carbon_stock declared in M56 (declarations.gms:34); q11_cost_reg:26 +vm_emission_costs -> vm_cost_glo.",
         "notes": "R42-Q1-B1 Critical doc_error: (d) claimed redd+natveg_nosoil prices ONLY CO2, NOT ag CH4/N2O - INVERTED. f56_emis_policy.csv rows 242-248 vs 114-120 are byte-identical on every non-CO2 row; the two policies differ only at co2_c forestry_vegc/litc (the + adds plantation-forestry CO2). The answer reproduced the wrong module_56.md:662 table row (the R41-Q4 sibling). FIXED :662. R42-Q1-B2 Minor answerer_confabulation: listed only 4 scenarios pricing ag CH4/N2O; actually 33 of 44 (whole redd*/reddnatveg*/redd+*/ecoSysProt* families) - answerer set-incompleteness, no doc fix.",
         "doc_errors_latent": ["module_56.md:662 - redd+natveg_nosoil row marked CH4/N2O unpriced; sibling of the R41-Q4 bug; Critical; FIXED to priced-for-ag (identical to default row 661) + CO2 gloss corrected to forestry vegc+litc."]},

        {"id": "R42-Q2", "archetype": "causal chain + parameterization detection", "modules_tested": [45, 14, 59],
         "question": "How does climate (M45) enter MAgPIE and affect crop yields (M14) and SOM (M59)? (a) default climate/CO2 scenario + where set; (b) is the yield effect MECHANISTIC or exogenous input data (parameterization)? show the equation/parameter; (c) how M45 feeds M59 SOM. Cite file:line. Be explicit about parameterization vs mechanistic.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 3,
         "phase_gate": "PARAMETERIZATION FRAMING FULLY ACCURATE. M45 static = sets+input only, zero equations, one param pm_climate_class(j,clcl), 31 clcl, frozen 1976-2000 Koppen. Yields: q14_yield_crop (equations.gms:14-16) multiplies precomputed i14_yields_calib (<-lpj_yields.cs3) by vm_tau; climate is the time-dim of an external LPJmL table, no in-model climate equation; c14_yields_scenario=cc (default.cfg:360). SOM: pm_climate_class->clcl_climate59->4 IPCC zones->i59_cratio (preloop:60-67)->q59_som_target_cropland; c59_som_scenario=cc (default.cfg:1930).",
         "notes": "Clean (10). 3 Informational index-label slips (f14_yields(t,j,kcr,w) vs (t_all,j,kve,w); f59_topsoilc_density (t,j) vs (t_all,j); tillage =1 attribution) - cosmetic, load-bearing dims correct. No doc fixes; module_14/45/59.md verified accurate."},

        {"id": "R42-Q3", "archetype": "quantitative verification", "modules_tested": [50, 59, 18, 51, 55],
         "question": "Give the cropland soil-N budget in M50's default realization: (a) balance equation + inputs/outputs; (b) how residue (M18) + SOM (M59) organic inputs enter; (c) how N surplus is computed + what it feeds. Name equation(s)+variables, cite file:line.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 1,
         "phase_gate": "M50 default macceff_aug22 VERIFIED (sole realization; config/default.cfg:1479; the MACC-sounding name is correct - MACC mitigation of SNUpE in M50 presolve). q50_nr_bal_crp (eq:14-16) vm_nr_eff x v50_nr_inputs =g= sum_kcr v50_nr_withdrawals exact; q50_nr_inputs (22-32) all 8 terms verbatim, set-sums preserved; q50_nr_surplus (46-49) exact. M18 q18_res_recycling_nr (flexreg_apr16, 90-96), M59 q59_nr_som (cellpool_jan23, 69-75) exact. Surplus v50_nr_surplus_cropland is M50-internal (consumed nowhere); M51 instead reads vm_nr_eff/vm_nr_eff_pasture/vm_nr_inorg_fert_reg - DODGED the 'surplus exported to M51' trap.",
         "notes": "Clean (10). 1 Informational: 'free variable' for vm_nr_inorg_fert_reg (declared positive variable); meaning correct, terminology slip; the doc says 'endogenous optimization variable' so carries no error. No doc fixes."},

        {"id": "R42-Q4", "archetype": "edge case / failure mode", "modules_tested": [43, 42, 44, 41],
         "question": "What makes MAgPIE's water module infeasible, and how do EFR constrain availability? (a) default water-availability realization + how EFR is represented; (b) supply-demand constraint + infeasibility buffer; (c) how M44 biodiversity interacts. Name variables, cite file:line, state what diagnoses a water infeasibility.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 3,
         "phase_gate": "All verified exact. q43_water (equations.gms:10-11, =l=, sum(wat_dem,vm_watdem) =l= sum(wat_src,v43_watavail)); default total_water_aug13 (sole). EFR = vm_watdem.fx(ecosystem,j) (presolve.gms:87-88) = i42_env_flows_base (5% floor, s42_env_flow_base_fraction=0.05) + i42_env_flows (Smakhtin, s42_env_flow_scenario=2); ecosystem is a real wat_dem member (core/sets.gms:247). Infeasibility buffer = fossil-groundwater x1.01 on watdem_exo (presolve.gms:14-16), agriculture has no slack (the R29 finding). M44 has NO direct water pathway (verified both directions); v44_bii_missing is a REAL slack (declarations.gms:13).",
         "notes": "Clean (10). 3 Informational: EFP macro line 16 vs cited 13-17; q44_bii_target sum(ct,) wrapper dropped; diagnostic var indexing shorthand. No doc fixes; all load-bearing doc facts verified vs code."},

        {"id": "R42-Q5", "archetype": "R-to-GAMS provenance (magpie4)", "modules_tested": ["magpie4 source", 60, 62],
         "question": "Trace the report.mif bioenergy-demand variable from the magpie4 report* function back to its GAMS origin: (a) which report* fn + pinned source file; (b) underlying GAMS variable + module (60/62); (c) any aggregation/unit conversion. Cite pinned magpie4 source path + GAMS file:line.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 2,
         "phase_gate": "All load-bearing verified exact against the SHA-pinned clone + live GAMS. reportDemandBioenergy (called getReport.R:79) reads ov_dem_bioen = vm_dem_bioen(i,kall) declared M60 1st2ndgen_priced_feb24/declarations.gms:20 (verified default, config/default.cfg:1982); M60 sole writer, M16 sector_may15 sole reader. Unit chain GJ-content x (demand.R:120-123) + /1000 (reportDemandBioenergy.R:47/50/53/54) + regglo superAggregate + summationhelper(++) - matches clone. M62 vm_dem_material separate, absent from the bioenergy report fn - correct.",
         "notes": "Clean (10). 2 Informational: 2nd-gen sub-var GJ-vs-mass label (self-correcting in same cell); helper tryList line-range figure cited with attribution. Helper does NOT cover reportDemandBioenergy by name - process_gap BY DESIGN (helper curates ~4 entry points/theme + 'grep+read source on demand'; answerer correctly went to source, every magpie4 line matched). Optional helper polish only, no doc bug."},

        {"id": "R42-G1", "archetype": "default realization (regression anchor)", "modules_tested": [14],
         "question": "What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0,
         "regression_id": "G1", "drift_observed": False,
         "phase_gate": "drift FALSE. managementcalib_aug19 sole+default (config/default.cfg:354; module.gms:31 single include); exactly 2 equations q14_yield_crop (14-16) + q14_yield_past (35-39) verbatim, grep '^ *q14_' declarations.gms = 2; no fabricated q14_yieldcalib (R22 correction holds); s14_yld_past_switch=0.25 (input.gms:20); biocorrect removal commit cc84ae5e1 confirmed.",
         "notes": "Clean anchor, stable 10. No doc fixes; module_14.md (count=2) + module_14_notes.md (only-realization) verified correct."},

        {"id": "R42-G3", "archetype": "magpie4 version-pin (regression anchor)", "modules_tested": ["magpie4 helper", "version_pins.json", "renv.lock"],
         "question": "Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined? Cite the file(s) you read.",
         "score": 10, "bugs_found": 0, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0,
         "regression_id": "G3", "drift_observed": False,
         "phase_gate": "drift FALSE, pin FRESH. version_pins.json = v2.70.0 @ a360d8c9ec (resolution sha, captured 2026-05-25); auditor confirmed it MATCHES ../input/renv.lock (Packages.magpie4 Version+RemoteSha) with identical lock_file_sha256 canary live - NOT stale. On-disk clone HEAD = pin SHA. Answer read version_pins.json (not the v2.75.1 workspace clone, correctly flagged non-authoritative), named renv.lock authority, cited sync_magpie4_clone.py 3-strategy ladder.",
         "notes": "Clean anchor, 10. G3 last run R28; recovered cleanly. No doc fixes; helper + pin both correct + current."}
    ]
}

d["rounds"].append(r42)

for g in d.get("regression_questions", []):
    if g.get("id") == "G1":
        if 42 not in g.setdefault("used_in_rounds", []):
            g["used_in_rounds"].append(42)
        g["drift_observed"] = False
    if g.get("id") == "G3":
        if 42 not in g.setdefault("used_in_rounds", []):
            g["used_in_rounds"].append(42)
        g["drift_observed"] = False

cs = d["cumulative_stats"]
cs["total_rounds"] = 42
cs["total_bugs_found"] = cs.get("total_bugs_found", 0) + 11
cs["total_bugs_fixed"] = cs.get("total_bugs_fixed", 0) + 1
cs["last_validation_date"] = "2026-06-03"
cs["mean_score_trend"] = cs.get("mean_score_trend", "") + "->R42 follow-on (quantitative/edge-case/provenance/parameterization): raw 9.29 (highest since R25); 6/7=10; G1=10 G3=10 drift FALSE (G3 pin verified fresh vs renv.lock); caught the predicted M56:662 emis-policy sibling bug (1 Critical doc_error fixed); Q2 parameterization + Q3 wrong-realization traps both handled correctly"

json.dump(d, open(PATH, "w"), indent=2, ensure_ascii=False)
print("R42 appended OK.")
print("total_rounds:", cs["total_rounds"], "| total_bugs_found:", cs["total_bugs_found"], "| total_bugs_fixed:", cs["total_bugs_fixed"])
print("G1 used_in_rounds:", [g["used_in_rounds"] for g in d["regression_questions"] if g["id"]=="G1"][0])
print("G3 used_in_rounds:", [g["used_in_rounds"] for g in d["regression_questions"] if g["id"]=="G3"][0])
