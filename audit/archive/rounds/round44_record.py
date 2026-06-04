#!/usr/bin/env python3
"""Append Round 44 (diagnostic weak-spot re-test) to validation_rounds.json.
Schema v1.4. Record-only: ZERO doc bugs found, no doc fixes. Idempotent guard:
refuses to append if R44 already present."""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PATH = os.path.join(ROOT, "audit", "validation_rounds.json")
d = json.load(open(PATH))

if any(r.get("round") == 44 for r in d["rounds"]):
    raise SystemExit("R44 already present — aborting (idempotent guard).")

r44 = {
 "round": 44,
 "date": "2026-06-04",
 "commit_before": "9195687 (magpie-agent main, viz tooling + round44_design); MAgPIE develop @ ee98739fd",
 "commit_after": "pending (record-only, ZERO doc fixes this round)",
 "answerer_model": "claude-sonnet-4-6 (Agent model:sonnet, magpie-helper)",
 "auditor_model": "claude-opus-4-8 (Agent model:opus, general-purpose)",
 "type": "targeted",
 "scope": (
  "DIAGNOSTIC weak-spot re-test designed from the current-quality coverage analysis "
  "(audit/tools/viz_validation_coverage.py figs 5-7, which isolated weak spots the all-rounds "
  "mean had smeared out). Design: audit/archive/rounds/round44_design.md. Targets: M20 processing "
  "(unverified 4.0 @R27, pre-doc-push) and the driver->demand->production chain (M09/M15/M17's "
  "shared 6.0 @R41), plus a stale-module drift check on M54/M71 (healthy 9/8 but pre-push). "
  "Instrumented as a LENS BRIDGE: every answerer_confabulation bug also tagged with the verifier "
  "MANDATE that should have caught it (verifier_gap), so a recurring gap would escalate to a focused "
  "lens audit per design section 5. Outcome: weak spots RESOLVED; verifier_gaps sparse + "
  "idiosyncratic (no recurrence) -> NO lens-audit escalation warranted."
 ),
 "summary": {
  "total_bugs_reported_by_auditors": 8,
  "auditor_false_positives_withdrawn": 0,
  "auditor_root_cause_corrections": 1,
  "total_bugs_net": 8,
  "bugs_by_severity": {"critical": 0, "major": 0, "minor": 3, "informational": 5},
  "bugs_by_root_cause": {
   "doc_error": 0,
   "doc_error_answerer_beat_it": 0,
   "answerer_confabulation": 7,
   "answerer_style_or_framing": 1
  },
  "mean_score": 9.28,
  "doc_quality_mean": 10.0,
  "n_questions_doc_quality": 6,
  "doc_quality_mean_method": (
   "Raw mean = (P1 8.0 + P2 9.5 + P3 9.5 + P4 9.5 + P5 9.5 + G4 9.7)/6 = 9.28. ZERO doc bugs found, "
   "so doc_quality = 10.0 across all 6. CRITICAL synthesis correction: the P5 auditor tagged the "
   "im_feed_baskets/q71_feed_rum_liv conflation as root_cause=doc_error, and P1's M21 trade-equation "
   "citation looked doc-sourced; I verified BOTH docs directly (module_71.md separates q71_feed_rum_liv "
   "L43 from q71_feed_forage L68 correctly; module_21.md L95 cites q21_trade_glo at equations.gms:12-14 "
   "correctly) -> both are answerer_confabulation against verified-correct docs, NOT doc errors. Every "
   "sub-10 score is exclusively answerer-side (loose citations, domain/label slips), so doc_quality is "
   "a clean 10.0; the corpus including the previously-weak M20 doc is accurate."
  ),
  "score_range": [8.0, 9.7],
  "lens_bridge_finding": (
   "verifier_gaps observed: MANDATE-16 (P1 citation), MANDATE-12 (P1 set-member label), MANDATE-18 "
   "(P4 declaration-site attribution) - each ONCE, no recurrence across probes. Per round44_design "
   "section 5 escalation table: idiosyncratic single-occurrence gaps = local, NOT a machinery problem "
   "-> NO focused lens audit warranted. (A full /pipeline-audit also just ran R8 2026-06-03, 0 "
   "criticals, machinery healthy.) Parameterization-vs-mechanism lens checks PASSED on all of P1/P2/P3/P4."
  ),
  "weak_spot_verdict": (
   "RESOLVED. M20 processing 4.0(R27) -> 9.5: the R27 failure was pure answerer_confabulation against "
   "a then-correct doc; the R30-R32 doc push + a careful answerer produced zero substantive errors. "
   "Driver->demand->production chain: P1=8.0, P4=9.5, both well above R41's shared 6.0. M54/M71 stale "
   "but NO drift from the doc push (P5=9.5, both realizations correct)."
  ),
  "regression_anchors": {
   "G4": {
    "score": 9.7,
    "drift_observed": False,
    "trend": (
     "STABLE/load-bearing. magpie4 getReport flat unconditional tryList dispatch (no if/switch), "
     "117 call lines / 106 unique report* fns, signature + filter=c(1,2,7) modelstat semantics all "
     "verified against the SHA-pinned clone. Version pin 2.70.0 @ a360d8c9ec read from "
     "project/version_pins.json (NOT hardcoded) - version-pin discipline CORRECT. Used R24/28/41/44."
    )
   }
  }
 },
 "questions": [
  {
   "id": "R44-P1",
   "archetype": "cross-module causal chain + parameterization-vs-mechanism",
   "modules_tested": [9, 15, 16, 17, 21],
   "question": ("DEFAULT config: higher-population SSP raises food demand - trace the mechanism to "
                "realized crop production; name the interface variable at each hop (drivers->food "
                "demand->aggregation->production) and classify each hop equation-vs-parameterized."),
   "score": 8.0,
   "bugs_found": 2, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 2, "bugs_informational": 0,
   "lens_check": "parameterization-vs-mechanism = CORRECT (all hops classified right: M09 pure preloop param, m15_food_demand standalone NLP in presolve, q15_food_demand a main-solve constraint, M09->M15 the sole parameterized hop)",
   "verifier_gaps": ["MANDATE-16", "MANDATE-12"],
   "phase_gate": ("All 5 realizations correct default (M09 aug17, M15 anthro_iso_jun22, M16 sector_may15, "
                  "M21 selfsuff_reduced, M17 flexreg_apr16). 17-eq standalone-NLP count right; "
                  "q15_food_demand verified 10-14 =g=; standalone-vs-main-solve boundary confirmed by "
                  "code comment. 2 Minor answerer slips only."),
   "notes": ("Bugs: (1) M21 trade eq cited equations.gms:13-15 (actual q21_trade_glo 12-14) + left "
             "unnamed, presenting global variant as the only constraint [confab, MANDATE-16]; (2) "
             "vm_dem_food written (i,kfo), declaration domain is (i,kall) [confab, MANDATE-12]. Docs "
             "verified correct (module_21.md L95 cites 12-14). No doc fix.")
  },
  {
   "id": "R44-P2",
   "archetype": "default/realization + parameterization (M20 4.0 re-test)",
   "modules_tested": [20, 16, 17, 11],
   "question": ("DEFAULT config: how does M20 processing convert primary->secondary products? Name the "
                "conversion equation + conversion-factor parameter; create-or-consume vs M16 balance; "
                "input suppliers + output consumers; state M20 active realization."),
   "score": 9.5,
   "bugs_found": 2, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 2,
   "lens_check": "realization = CORRECT (substitution_may21, default.cfg:633); parameterization = CORRECT (i20_processing_conversion_factors an input param from .cs3, not optimized)",
   "verifier_gaps": [],
   "phase_gate": ("q20_processing verified equations.gms:59-65 (exact body); all 4 interface vars real + "
                  "correctly attributed (vm_dem_processing + vm_secondary_overproduction->M16; "
                  "vm_cost_processing + vm_processing_substitution_cost->M11); q16_supply_secondary 40-49, "
                  "q16_supply_crops 19-29. R27 4.0 weakness FULLY RESOLVED."),
   "notes": ("2 Informational only: missing epistemic badges [style]; loose sets.gms:20-24 range (7-member "
             "processing20 is at L24) [confab]. An in-CODE comment typo (i20_..._cf) was noted but is NOT "
             "an agent-doc bug; answer used the correct name. No doc fix.")
  },
  {
   "id": "R44-P3",
   "archetype": "default-vs-switch + cross-module causal chain",
   "modules_tested": [60, 16, 21, 17, 30, 29, 10],
   "question": ("DEFAULT config: trace 2nd-gen (lignocellulosic) bioenergy demand to land allocation; "
                "which module sets demand, how it enters production, what land type; exogenous or "
                "endogenous by default; name modules + interface vars per hop."),
   "score": 9.5,
   "bugs_found": 1, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 1,
   "lens_check": "default-vs-switch = CORRECT (2nd-gen demand exogenous by default: M60 1st2ndgen_priced_feb24 reads i60_bioenergy_dem from f60_bioenergy_dem input; q60_bioenergy_reg a =g= floor; subsidy off at s60_bioenergy_2nd_price=0)",
   "verifier_gaps": [],
   "phase_gate": ("Full hop chain verified: vm_dem_bioen decl L20; kbe60={betr,begr}; q16_supply_crops "
                  "includes vm_dem_bioen; betr/begr in k_notrade (REMIND comment); q17_prod_reg, q30_prod "
                  "(simple_apr24), q29_cropland->vm_land 'crop', q10_land_area set-sum preserved. All "
                  "realizations match default.cfg."),
   "notes": ("1 Informational: 'REMIND-MAgPIE coupled' gloss on default scenario R34M410-SSP2-NPi2025 - "
             "it is a REMIND-derived input scenario ($else branch), not live coupling mode [confab]. Does "
             "not affect the exogenous conclusion. No doc fix.")
  },
  {
   "id": "R44-P4",
   "archetype": "cross-module causal chain + parameterization-vs-mechanism (income axis)",
   "modules_tested": [9, 15, 70, 16],
   "question": ("DEFAULT config: trace GDP/income per capita -> livestock product demand; which module "
                "holds income driver, how it alters diet composition, interface var into production/trade "
                "balance; is income->diet regression-parameterized or mechanistically optimized?"),
   "score": 9.5,
   "bugs_found": 2, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 1, "bugs_informational": 1,
   "lens_check": "parameterization-vs-mechanism = CORRECT (income->livestockshare is a regression saturation/Hill curve with coefficients from f15_demand_regression_parameters.cs3; the M15 NLP only minimizes a slack penalty, does NOT optimize diet shares)",
   "verifier_gaps": ["MANDATE-18"],
   "phase_gate": ("q15_regr saturation form + coefficients exact; regr15 contains 'livestockshare' "
                  "(sets.gms:133); s15_elastic_demand default 0; s15_calibrate default 1; q15_food_demand "
                  "10-14; q16_supply_livestock 31-37 with vm_dem_food(i2,kap). Lens trap handled exactly."),
   "notes": ("Bugs: (1) 'Michaelis-Menten' label for a generalized Hill function (nonsat exponent) "
             "[confab, Informational]; (2) vm_dem_food listed under M16 interface section but DECLARED in "
             "M15 - ambiguous declaration-site attribution [confab, Minor, MANDATE-18]. No doc fix.")
  },
  {
   "id": "R44-P5",
   "archetype": "active-realization drift check (stale modules M54/M71)",
   "modules_tested": [54, 71, 70, 50, 11],
   "question": ("(a) Does MAgPIE track phosphorus by default - which module, what does it do? (b) M71 "
                "default realization + what it disaggregates + interface var carrying disaggregated "
                "livestock to spatial units."),
   "score": 9.5,
   "bugs_found": 1, "bugs_critical": 0, "bugs_major": 0, "bugs_minor": 0, "bugs_informational": 1,
   "lens_check": "active-realization = CORRECT for both (M54 'off', only realization, phosphorus NOT tracked, vm_p_fert_costs fixed 0; M71 foragebased_jul23, default.cfg)",
   "verifier_gaps": [],
   "phase_gate": ("M54 off realization: vm_p_fert_costs decl L9, .fx=0 preloop L10, wired into q11_cost_reg "
                  "L25 but zero; no active equations. M71: q71_feed_rum_liv + q71_prod_mon_liv exist; "
                  "s71_scale_mon=1.10; vm_prod(j,kli) correct interface carrier. NO drift from doc push."),
   "notes": ("1 Informational: answer attributed im_feed_baskets to q71_feed_rum_liv, but the feed-basket "
             "multiplication lives in q71_feed_forage. ROOT-CAUSE CORRECTED from the P5 auditor's "
             "'doc_error' to 'answerer_confabulation': module_71.md separates the two equations correctly "
             "(q71_feed_rum_liv L43 vs q71_feed_forage L68) - the answerer conflated, the doc is right. "
             "No doc fix. Confirms stale modules retained pre-push quality.")
  }
 ]
}

d["rounds"].append(r44)

# update cumulative_stats
cs = d["cumulative_stats"]
cs["total_rounds"] = 44
cs["approx_total_bugs_found"] = cs.get("approx_total_bugs_found", 0) + 8
cs["last_validation_date"] = "2026-06-04"
cs["mean_score_trend"] = cs["mean_score_trend"] + (
 "->R44 DIAGNOSTIC weak-spot re-test (targeted): raw 9.28; M20 processing 4.0(R27)->9.5 RESOLVED "
 "(R27 was answerer_confab vs a correct doc); driver->demand->production chain P1=8.0/P4=9.5 recovered "
 "from R41's shared 6.0; ALL parameterization-vs-mechanism lens checks PASSED (P1/P2/P3/P4); ZERO doc "
 "bugs (doc_quality 10.0, incl 1 synthesis root-cause correction P5 doc_error->answerer_confab after "
 "verifying module_71.md/module_21.md directly); verifier_gaps sparse+idiosyncratic (MANDATE-12/16/18 "
 "once each, NO recurrence) -> NO lens-audit escalation per round44_design section 5; G4 drift FALSE "
 "(pin 2.70.0@a360d8c verified fresh)."
)

# append round 44 to G4 regression anchor usage
for g in d.get("regression_questions", []):
    if g.get("id") == "G4":
        uir = g.setdefault("used_in_rounds", [])
        if 44 not in uir:
            uir.append(44)

with open(PATH, "w") as f:
    json.dump(d, f, indent=1, ensure_ascii=True)
    f.write("\n")

print("R44 appended. total_rounds=%d, bugs_found=%d, G4.used_in_rounds=%s" % (
    cs["total_rounds"], cs["approx_total_bugs_found"],
    next(g["used_in_rounds"] for g in d["regression_questions"] if g["id"] == "G4")))
