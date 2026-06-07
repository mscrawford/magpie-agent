#!/usr/bin/env python3
"""Append R49 + R50 (semantic) to validation_rounds.json and R9 (structural) to
pipeline_audit_rounds.json. Concise-but-faithful: per-doc scores + severity counts +
brief notes; full per-bug detail lives in audit/archive/rounds/round49_*, round50_*,
and pipeline_audit_round9_findings.md. Matches file style (indent=1, ensure_ascii=True).
Run once. Backups at /tmp/*.bak before running."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
VR = os.path.abspath(os.path.join(HERE, "..", "..", "validation_rounds.json"))
PR = os.path.abspath(os.path.join(HERE, "..", "..", "pipeline_audit_rounds.json"))

# ---------------- R49 (semantic, hybrid; cross_module integrative + 2 core probes) ----------------
R49 = {
 "round": 49, "date": "2026-06-06", "type": "full",
 "answerer_model": "claude-sonnet-4-6 (Agent model:sonnet, magpie-helper)",
 "auditor_model": "claude-opus (workflow: doc-audit + question-audit + adversarial verify)",
 "commit_before": "f5050c3", "commit_after": None,
 "scope": "Targeted flywheel on the still-drifting integrative corpus (cross_module + core_docs) via doc_audit_round.workflow.js. 6 probes + G1/G3. Code base ee98739fd (0 drift), so findings are pre-existing doc errors R47 missed. verify: 0 refuted / 6 upheld.",
 "questions": [
  {"id": "R49-nfb", "archetype": "conservation", "docs_tested": ["cross_module/nitrogen_food_balance.md"], "score": 9, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 1, "doc_audit_bugs_fixed": 1, "root_causes": ["doc_error", "answerer_confabulation"], "notes": "N budget trace near-flawless; 1 Minor citation drift fixed (q21_trade_reg span). Latent module_55.md:265 vm_manure cite (69->78) deferred -> fixed in R50."},
  {"id": "R49-cdr", "archetype": "dependency-structure", "docs_tested": ["cross_module/circular_dependency_resolution.md"], "score": 10, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 2, "bugs_informational": 0, "doc_audit_bugs_fixed": 3, "root_causes": ["doc_error"], "notes": "Answer clean (10). doc_audit found+fixed 3: 1 Major (Sec 2.1 land-conversion-cost = M39 area-based, not M29/30 lagged-carbon) + 2 Minor (pm_carbon_density_*_ac; q10_land_area). All 3 verify UPHELD."},
  {"id": "R49-msg", "archetype": "consumer-set", "docs_tested": ["cross_module/modification_safety_guide.md"], "score": 7, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 1, "bugs_informational": 1, "doc_audit_bugs_fixed": 2, "root_causes": ["doc_error", "answerer_style_or_framing"], "notes": "vm_land 10-consumer set ACCURATE+COMPLETE. Fixed 1 Major (sec 3.3 phantom vm_prod_reg consumers 11_costs+73_timber; real=8) + 1 Minor (default scenario R34M410-SSP2-NPi2025). verify UPHELD."},
  {"id": "R49-moddep-ghg", "archetype": "dependency-structure", "docs_tested": ["core_docs/Module_Dependencies.md", "modules/module_56.md"], "score": 8, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 0, "bugs_informational": 0, "doc_audit_bugs_fixed": 0, "root_causes": ["doc_error"], "notes": "Module_Dependencies.md code-faithful (0 confirmed). 2 latent bugs in module_56.md (M52 LULUCF + M57 wrongly listed as vm_emissions_reg providers; emis_oneoff/annual disjoint) -> deferred, fixed in R50."},
  {"id": "R49-corearch", "archetype": "structural-count", "docs_tested": ["core_docs/Core_Architecture.md"], "score": 8, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 0, "bugs_informational": 0, "doc_audit_bugs_fixed": 0, "root_causes": ["doc_error"], "notes": "Core_Architecture.md 0 confirmed. 1 Major latent in AGENT.md:205/207: ls -d snippet counts input/ as a realization -> '40 of 46'; true 22 of 46 (verified 2 ways). FIXED + redeployed."},
  {"id": "R49-cbc-soil", "archetype": "conservation", "docs_tested": ["cross_module/carbon_balance_conservation.md"], "score": 8, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 0, "bugs_informational": 1, "doc_audit_bugs_fixed": 1, "root_causes": ["answerer_confabulation"], "notes": "G2 populator/reader sets complete+correct. 1 Minor doc cite fixed (c52_carbon_scenario input.gms:22-23 -> 8-23). Major was answerer pseudo-formula vs correct doc."},
  {"id": "R49-G1", "archetype": "regression-calibration-anchor", "regression_anchor": "G1", "docs_tested": ["modules/module_14.md"], "score": 9, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 0, "drift_observed": False, "root_causes": [], "notes": "Default managementcalib_aug19, 2 eqs (q14_yield_crop/past), q14_yieldcalib absent (R22 held). 1 Minor cite slip. No drift."},
  {"id": "R49-G3", "archetype": "regression-calibration-anchor", "regression_anchor": "G3", "docs_tested": ["agent/helpers/magpie4_reference.md"], "score": 10, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0, "drift_observed": False, "root_causes": [], "notes": "v2.70.0 @ a360d8c9ec from version_pins.json; reads pin not workspace clone. 0 bugs."}
 ],
 "summary": {
  "mean_score": 8.63, "doc_quality_mean": 8.63, "n_questions_doc_quality": 8,
  "doc_quality_mean_method": "(9+10+7+8+8+8+9+10)/8 = 8.63; all questions retained (each cross_module/core probe carried a doc_error or latent doc bug).",
  "total_bugs_scored": 16, "bugs_by_severity": {"critical": 0, "major": 6, "minor": 5, "informational": 5},
  "doc_bugs_fixed": 7, "files_fixed": ["cross_module/nitrogen_food_balance.md", "cross_module/circular_dependency_resolution.md", "cross_module/modification_safety_guide.md", "cross_module/carbon_balance_conservation.md"],
  "verify_summary": {"refuted": 0, "corrected": 0, "citation_failed": 0, "upheld": 6},
  "gate": {"clean": True, "errors": 0, "warnings": 4},
  "headline": "Integrative corpus still drifts at 0 code-drift: 7 doc bugs fixed (R47-missed) + surfaced 4 cross-doc bugs (AGENT.md realization miscount FIXED; module_56 producer-set + module_55 cite -> fixed in R50). Anchors G1/G3 stable.",
  "design_ref": "audit/archive/rounds/round49_{docaudits,answers,audits,verify}/"
 }
}

# ---------------- R50 (semantic, hybrid; module_56 emissions cluster + 2 core docs) ----------------
R50 = {
 "round": 50, "date": "2026-06-07", "type": "full",
 "answerer_model": "claude-sonnet-4-6 (Agent model:sonnet, magpie-helper)",
 "auditor_model": "claude-opus (workflow; hit session cap mid-run, completed via resume)",
 "commit_before": "f5050c3", "commit_after": None,
 "scope": "Drift-triggered re-validation of the module_56 GHG/emissions cluster (R49 detected drift) + 2 core docs, via doc_audit_round.workflow.js. 5 probes + G2/G4. verify: 0 refuted / 3 corrected / 8 upheld. NOTE: capped mid-fix; resumed (resume must re-pass args).",
 "questions": [
  {"id": "R50-m56-emis", "archetype": "producer-set", "docs_tested": ["modules/module_56.md"], "score": 5, "bugs_critical": 0, "bugs_major": 2, "bugs_minor": 1, "bugs_informational": 2, "doc_audit_bugs_fixed": 8, "root_causes": ["doc_error_answerer_beat_it", "answerer_confabulation"], "notes": "Fixed 17 edits incl the R49-deferred latent: module_56.md:66/590/714/1024/1066/1074 wrongly listed M57 as vm_emissions_reg PRODUCER (it only READS; real populators {51,52,53,58}) + scen56 '60+'->44. verify 4 upheld + 1 corrected ('101'-> keep '100+')."},
  {"id": "R50-m55-awms", "archetype": "consumer-set", "docs_tested": ["modules/module_55.md"], "score": 8, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 0, "bugs_informational": 1, "doc_audit_bugs_fixed": 1, "root_causes": ["answerer_confabulation"], "notes": "vm_manure consumer set verified. Fixed 1 Minor: sm_fix_SSP2 doc 2015 -> code 2025 (verify UPHELD). Answerer Major = misread module_50.md markdown lines as code lines (doc correct)."},
  {"id": "R50-m51-nremis", "archetype": "producer-set", "docs_tested": ["modules/module_51.md"], "score": 6, "bugs_critical": 0, "bugs_major": 1, "bugs_minor": 1, "bugs_informational": 0, "doc_audit_bugs_fixed": 2, "root_causes": ["doc_error", "answerer_confabulation"], "notes": "M51 vm_emissions_reg populator role + im_maccs_mitigation application. 2 doc fixes. verify 1 upheld + 1 corrected."},
  {"id": "R50-dataflow-drivers", "archetype": "provenance", "docs_tested": ["core_docs/Data_Flow.md"], "score": 8, "bugs_critical": 0, "bugs_major": 2, "bugs_minor": 0, "bugs_informational": 0, "doc_audit_bugs_fixed": 2, "root_causes": ["doc_error"], "notes": "Driver-input provenance trace. 2 Major doc fixes. verify 2 upheld."},
  {"id": "R50-qpat", "archetype": "worked-example", "docs_tested": ["core_docs/Query_Patterns_Reference.md"], "score": 10, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 0, "doc_audit_bugs_fixed": 1, "root_causes": ["doc_error"], "notes": "Worked-pattern examples re-verified vs code. 1 Minor fixed (a stale value). verify 1 corrected. Never-deep-probed core doc now covered."},
  {"id": "R50-G2", "archetype": "regression-calibration-anchor", "regression_anchor": "G2", "docs_tested": ["modules/module_52.md", "modules/module_56.md"], "score": 10, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0, "drift_observed": False, "root_causes": [], "notes": "vm_carbon_stock DECLARED M56, populated by land modules+M59, M52 reads. No drift."},
  {"id": "R50-G4", "archetype": "regression-calibration-anchor", "regression_anchor": "G4", "docs_tested": ["agent/helpers/magpie4_reference.md"], "score": 10, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 0, "drift_observed": False, "root_causes": [], "notes": "getReport flat tryList ~106 unique report*; no control-arg/grepl. No drift."}
 ],
 "summary": {
  "mean_score": 8.14, "doc_quality_mean": 8.14, "n_questions_doc_quality": 7,
  "doc_quality_mean_method": "(5+8+6+8+10+10+10)/7 = 8.14.",
  "total_bugs_scored": 12, "bugs_by_severity": {"critical": 0, "major": 6, "minor": 4, "informational": 2},
  "doc_bugs_fixed": 14, "files_fixed": ["modules/module_56.md", "modules/module_55.md", "modules/module_51.md", "core_docs/Data_Flow.md", "core_docs/Query_Patterns_Reference.md"],
  "verify_summary": {"refuted": 0, "corrected": 3, "citation_failed": 0, "upheld": 8},
  "gate": {"clean": True, "errors": 0, "warnings": 4},
  "headline": "module_56 emissions cluster re-validated (drift-triggered from R49): 23 edits across 5 docs incl the M57-producer fix. Anchors G2/G4 stable. Completed via resume after a session-cap interruption.",
  "design_ref": "audit/archive/rounds/round50_{docaudits,answers,audits,verify}/"
 }
}

d = json.load(open(VR))
d["rounds"].extend([R49, R50])
# regression anchors used_in_rounds
used = {"G1": [49], "G3": [49], "G2": [50], "G4": [50]}
for rq in d.get("regression_questions", []):
    rid = rq.get("id")
    if rid in used:
        rq.setdefault("used_in_rounds", []).extend(used[rid])
        rq["last_drift_observed"] = False
cs = d["cumulative_stats"]
cs["total_rounds"] = 50
cs["approx_total_bugs_found"] = cs.get("approx_total_bugs_found", 0) + 28
cs["approx_total_bugs_fixed"] = cs.get("approx_total_bugs_fixed", 0) + 21
cs["last_validation_date"] = "2026-06-07"
cs["mean_score_trend"] = cs.get("mean_score_trend", "") + (
 " ->R49 integrative corpus (cross_module + 2 core docs) raw 8.63, 7 doc bugs fixed + AGENT.md realization-count self-bug (40->22) + 3 cross-doc bugs surfaced;"
 " ->R50 module_56 emissions cluster + 2 core docs raw 8.14, 23 edits incl M57-not-a-vm_emissions_reg-producer fix, anchors G2/G4 stable, completed via resume after a session cap. Both rounds: verify 0 refuted. Commits pending review.")
json.dump(d, open(VR, "w"), indent=1, ensure_ascii=True)
print("validation_rounds.json: now", len(d["rounds"]), "rounds; cumulative total_rounds=", cs["total_rounds"])

# ---------------- R9 (structural pipeline-audit; C3/C4/C6 via pipeline_audit_round.workflow.js) ----------------
R9 = {
 "round": 9, "date": "2026-06-07", "commit": None,
 "auditor_model": "claude-opus (pipeline_audit_round.workflow.js: lens + per-finding adversarial verify + synthesis)",
 "round_type": "consolidation C3/C4/C6 subset (first real run of the reusable workflow; round-901 was a 1-lens smoke validation)",
 "lenses_run": ["C3-drift", "C4-untested-testers", "C6-coherence"],
 "findings_total": 15, "by_severity": {"CRITICAL": 1, "HIGH": 4, "MEDIUM": 7, "LOW": 3},
 "by_lens": {"C3-drift": 4, "C4-untested-testers": 7, "C6-coherence": 4},
 "verify_stage": "per-finding adversarial verify: 12 verified, 11 UPHELD, 1 CORRECTED, 0 REFUTED, 0 CITATION_FAILED",
 "root_cause_clusters": [
  {"cluster": "Cluster A (HIGH): false-GREEN validator harness. 6 check_*.py (gating 15/16/25 + advisory 20/24/23/26) have no real --self-test; selftest_validator.sh trusts exit-0, so a check that ignores --self-test mints a false positive control and gating checks go GREEN on a 0/0 denominator if their regex breaks. CI blocks on this guard health.",
   "findings": ["C4-1", "C4-2", "C4-3", "C4-4", "C4-5", "C4-6", "C4-7"],
   "candidate_intervention": "Harden selftest_validator.sh to require a SELFTEST_OK sentinel (not exit-0) + make check_*.py exit 2 on unimplemented --self-test; then add real --self-test (synthesize-bug-first, denominator>0, 0/0=fail) to gating checks 15/16/25, then advisory. DEFERRED to a focused next round (validator-machinery surgery)."},
  {"cluster": "Cluster B (MEDIUM): hand-copied derived values drift (no binding check). modules/README.md:34 '40 checks' (live 43); README.md:7 '47 rounds' (live 48->50).",
   "findings": ["C3-1", "C3-2"], "candidate_intervention": "Deferral, not a new check: mirror README.md:109 live-count phrasing; defer the round count to validation_rounds.json. FIXED 2026-06-07."}
 ],
 "report_path": "audit/archive/rounds/pipeline_audit_round9_findings.md",
 "guards_added": [],
 "status": "triaged (workflow). FIXED 2026-06-07: C6-1 (CRITICAL flywheel_rubric.md:30 fbask anchor inverted -> corrected + rubric v1.2->v2.0 bump), C6-2 (AGENT.md schema v1.3 de-hardcoded), C6-3 (rubric 14->15 classes), C6-4 (verifiers.md lessons-count 0->3), C3-1, C3-2. DEFERRED to next round: Cluster A (C4-1..7 harness hardening), C3-3/C3-4/C6-5 (UNVERIFIED). See audit/burst_2026-06-07_continuation.md."
}
p = json.load(open(PR))
prounds = p["rounds"] if isinstance(p, dict) and "rounds" in p else p
prounds.append(R9)
json.dump(p, open(PR, "w"), indent=1, ensure_ascii=True)
print("pipeline_audit_rounds.json: now", len(prounds), "rounds")
