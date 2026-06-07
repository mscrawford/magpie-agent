# Audit Report: Round 50 — Data_Flow driver trace (population/GDP, Module 09)

**Auditor**: Opus (semantic-validation flywheel)
**Date**: 2026-06-06
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Answer audited**: `audit/archive/rounds/round50_answers/dataflow-drivers.md`

---

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

The trace mechanics (file format, `$include`/`$ondelim` loading, `f_`→`i_`→`im_` prefix chain, preloop processing, scenario/SSP2-baseline logic, consumer counts) are accurate and well-cited. The ONE substantive error is the headline deliverable: the answer names **Module 15 as the "first" consumer in execution sequence**, but the first consumer is **Module 12 (interest_rate)** in its preloop (Phase 1), which runs strictly before Module 15's Phase-3 reads — and which the answer's OWN cited doc (`module_09.md` §7) lists as consumer #1.

---

## Verified Claims (correct)

| Claim | Evidence |
|---|---|
| Population file is `.csv`: `f09_pop_iso.csv` | `modules/09_drivers/aug17/input.gms:36-39` (table `f09_pop_iso(t_all,iso,pop_gdp_scen09)`, `$include .../f09_pop_iso.csv`) |
| GDP files `f09_gdp_ppp_iso.csv` (USD17PPP) and `f09_gdp_mer_iso.csv` (USD17MER) | `input.gms:26-29` (PPP), `:31-34` (MER) |
| `pop_gdp_scen09` set = 9 members (SSP1-5, SDP, SDP_EI, SDP_MC, SDP_RC) | `modules/09_drivers/aug17/sets.gms:9-11`. Answer's "9 SSP/SDP scenarios" is exact. (Note: input.gms `$setglobal` comments list `SSP2EU` as a switch *option*, but the .csv set has no SSP2EU — answer correctly used set cardinality.) |
| `f_` prefix = raw file params, module-internal | `Data_Flow.md` §2.1 table; matches code usage |
| Loading via `$include`/`$ondelim`/`$offdelim` block | `input.gms:36-39` confirms |
| Regional aggregation `i09_pop_raw(t,i,scen) = sum(i_to_iso, f09_pop_iso(...))` at preloop | `modules/09_drivers/aug17/preloop.gms:11` — exact match |
| Per-capita ISO GDP `i09_gdp_pc_ppp_iso_raw = f09_gdp_ppp_iso / f09_pop_iso`, missing countries filled with SSP2 average | `preloop.gms:23-27` — exact (the `= 0` guard + SSP2 fill at :27 matches answer's "Missing countries filled with SSP2 regional average") |
| Scenario selection + SSP2 baseline until `sm_fix_SSP2 = 2025`, then `%c09_*_scenario%` | `preloop.gms:36-56` (if-branch SSP2 :37-45, else-branch scenario :46-55); `sm_fix_SSP2 / 2025 /` at `input.gms:22`; default.cfg:225 confirms 2025 |
| `im_pop_iso`/`im_pop`/`im_gdp_pc_*` are the cross-module interface params written in preloop | `preloop.gms:40-41,44,49-53`; declared `declarations.gms:10-11,16,20,29` |
| `c09_pop_scenario` / `c09_gdp_scenario` default = `SSP2` | `config/default.cfg:211-212`; `input.gms:8,12` |
| Module 09 has NO presolve/equations/postsolve — pure data provider (sets/declarations/input/preloop only) | `modules/09_drivers/aug17/realization.gms:12-15` (only 4 phases included) |
| `im_pop_iso` consumed by **10 modules** | grep: 12,13,15,42,50,55,56,60,70,73 = 10. Matches answer and `module_09.md:484` |
| `im_gdp_pc_ppp_iso` consumed by **4 modules (13,15,38,73)** | grep: 13,15,38,73 = 4. Exact match |
| **14 modules** total receive Module 09 drivers | grep union across all `im_*` drivers: 12,13,15,18,36,38,42,50,55,56,60,62,70,73 = 14. Matches `module_09.md` §7 list (items 1-14) |
| Module 15 uses `im_pop` directly in `q15_food_demand` | `modules/15_food/anthro_iso_jun22/equations.gms:10,13` — `sum(ct,im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365`. Answer's reproduced formula is faithful (balanceflow term honestly elided as `+ ...`) |
| Module 15 default realization `anthro_iso_jun22` | `config/default.cfg:410` (`cfg$gms$food <- "anthro_iso_jun22"`); only realization dir present |
| Module 15 = `m15_food_demand` standalone NLP, `model magpie / all - m15_food_demand` | `Data_Flow.md` §3.4 line 191; `m15_food_demand` solved `intersolve.gms:50`, `presolve.gms:246` |
| Module 15 consumes the broadest driver set (6 vars: `im_pop_iso, im_pop, im_gdp_pc_ppp_iso, im_gdp_pc_mer_iso, im_demography, im_physical_inactivity`) | grep confirms all 6 in M15 files; `module_09.md` §7 item 3 |
| Spatial figure "67,420 grid cells → 200 clusters", 12 regions | `Data_Flow.md` §3.1; default cellular input `..._h12_..._c200_...` at `config/default.cfg:26` (c200 = 200 clusters, h12 = 12 regions) |
| Population upstream = IIASA SSP Database (KC & Lutz 2017) | `module_09.md:253`. Answer's attribution is doc-faithful |
| Module 09 staleness disclosure (IIASA 2017, no post-COVID) | `module_09.md:549-550` confirms the doc owns this limitation; answer's §6 flag is accurate |

---

## Bugs Found

### Bug R50-DF-B1
- **Severity**: Major  (tier_uncertainty: true — it is the question's headline deliverable, which pulls toward Critical, but no Critical §1 trigger fires: no invented identifier, no wrong realization, no cost-variable mis-attribution, no fabricated formula, no destructive-edit target)
- **Class**: 4 (Conceptual pseudo-code / wrong behavioral claim) + module-attribution
- **Trigger matched**: Major — "The claim is wrong in a way that misleads about behavior, but won't directly cause damaging action" (execution-ordering / first-consumer misattribution)
- **Claim in answer** (§4): "**Module 15 (food...) is the first structural consumer.** ... Among all 14 modules that receive Module 09 drivers, **Module 15 is the first in the execution sequence (it runs during the intersolve iteration)** and consumes the broadest set of driver variables." Also §3 trace summary: "→ consumed by Module 15 in q15_food_demand".
- **Reality in code**: The FIRST module to consume a Module 09 driver is **Module 12 (interest_rate)**, which reads `im_pop_iso` and `im_development_state` in its **preloop** (Phase 1):
  - `modules/12_interest_rate/select_apr20/preloop.gms:17` — `p12_reg_shr(...) = sum(i_to_iso(i,iso), p12_country_switch(iso) * im_pop_iso(t_all,iso)) / sum(...)`
  - `modules/12_interest_rate/select_apr20/preloop.gms:23-26` — `pm_interest` uses `im_development_state`
  Modules are `$include`d in numerical order (`modules/include.gms:12-57`: 09 → 10 → 11 → 12 → ...), and the preloop phase runs ONCE for all modules at Phase 1 (before any time-loop iteration). So Module 12's preloop runs immediately after Module 09's preloop produces the `im_*` params, and **before** Module 15 touches any driver. Module 15 reads `im_pop_iso` only in `presolve.gms:44` (Phase 3A) and `im_pop` in `equations.gms:13` (Phase 3B optimization) — both strictly later. Other preloop-phase consumers that also precede M15: Module 38 (`per_ton_fao_may22/preloop.gms:10`), 50, 56, 60, 70 (`fbask_jan16/preloop.gms:37`), 73. (Modules 10, 11 consume no drivers — verified, positive control passed.)
- **Internal inconsistency**: the answer's §3 states "All Module 09 processing is complete during Phase 1 / Preloop," yet §4 calls Module 15 (Phase 3) the "first in the execution sequence" — ignoring the Phase-1 preloop consumers.
- **The answer contradicted its own cited source**: `module_09.md` §7 (lines 334-373, "recomputed 2026-05-24 R4") lists **Module 12 (interest_rate) as consumer #1**, Module 13 as #2, Module 15 as #3 — an ordering that mirrors execution order. The answer cited `module_09.md` §7 for the per-variable consumer counts but disregarded its ordering.
- **Anchor reference**: not a clean match to an immutable anchor; closest in spirit is the R24 one-hop/attribution family (MANDATE 17/18) — here the failure is execution-PHASE/first-consumer attribution rather than direct-vs-transitive, but the same "verify against code which module, in which phase" discipline would have caught it.
- **Root cause**: `answerer_confabulation` (the doc was correct and even listed M12 first; the answerer pattern-matched "first structural/economic consumer = food demand" and invented an execution-order rationale).

---

## Informational (not scored)

- **R50-DF-I1** (§4/§3): "Module 15 ... runs during the intersolve iteration" / "before feeding vm_dem_food into the main MAgPIE core." Slightly imprecise: `m15_food_demand` is solved BOTH in `presolve.gms:246` (initial) and `intersolve.gms:50` (per-iteration). Not a substantive error; does not affect score.
- The answer's "minor documentation gap" flag (Data_Flow.md doesn't name `mrdrivers`) is FAIR and correctly handled — `module_09.md` and `Data_Flow.md` name only institutions (IIASA/World Bank/OECD/IMF); the R package is in AGENT.md's "Adjacent layers." Routing to PREPROC_AGENT.md is correct. Not a bug.

---

## Latent Doc Bugs (recorded independent of answer score)

**None.** Every load-bearing doc claim the answer relied on is correct against develop:
- `Data_Flow.md` §1.1 file-format table, §2.1 prefix table, §3 four-phase pipeline, §3.1 spatial cascade (67,420→200, 12 regions), §3.4 `model magpie / all - m15_food_demand` — all consistent with code/config.
- `module_09.md` §7 consumer list (14 modules, with M12 first) is verified-correct against current code (matches my whole-tree grep union exactly). Notably, this doc had the RIGHT first-consumer ordering; the answer simply did not use it. Therefore NO `doc_error_answerer_beat_it` applies (the doc was not wrong).

(Note for maintainers: `Data_Flow.md` §5.1 carbon-system entry on `pm_carbon_density_secdforest_ac` populators/readers was NOT load-bearing for this driver question and was not re-verified here; it belongs to the G2/carbon regression territory.)

---

## Mechanical Checks

| # | Check | Result |
|---|---|---|
| M1 | File:line citations present | PASS (input.gms / preloop.gms / equations.gms cited) |
| M2 | Active realization stated | PASS — M15 `anthro_iso_jun22` stated; M09 single realization (`aug17`) not named but M09 has only one realization, so no ambiguity |
| M3 | Variable prefixes valid | PASS (`f09_`, `i09_`, `im_` all correct per Data_Flow §2.1 table and code) |
| M4 | Epistemic hierarchy badges | PASS (closing block: all 🟡 Documented, stated) |
| M5 | Confidence tier matches depth | PASS (🟡 honest — answer explicitly read AI docs only, no raw GAMS this session; that constraint makes the B1 confabulation more understandable but not excused, since the cited doc itself had the right ordering) |
| M6 | Closing source statement | PASS |

---

## Scoring

```
critical = 0
major    = 1   (R50-DF-B1)
minor    = 0
info     = 1   (R50-DF-I1, weight 0)

score = max(0, 10 - 4*0 - 2*1 - 1*0) = 8
```

**Score: 8/10** (MOSTLY ACCURATE).

doc_quality note: B1 is `answerer_confabulation` against a correct doc, so for `doc_quality_mean` this question would be EXCLUDED (its only scored bug is answerer noise; the docs it leaned on are clean).

---

## Summary

A strong, well-cited trace of the population/GDP pipeline: file format (`.csv`), GAMS reading (`$include`/`$ondelim` into `f09_*` raw params), preloop processing (ISO→region aggregation, per-capita derivation, SSP2-baseline scenario lock into `im_*` interface params), consumer counts (im_pop_iso=10, im_gdp_pc_ppp_iso=4, 14 modules total), and the IIASA-SSP-2017 staleness flag — all verified correct against `/tmp/magpie_develop_ro` and `config/default.cfg`. The single Major error is the question's headline ask: the answer crowns **Module 15** as the "first" consumer in execution sequence (intersolve), when the first consumer is **Module 12 (interest_rate)** reading `im_pop_iso`/`im_development_state` in its Phase-1 preloop (`modules/12_interest_rate/select_apr20/preloop.gms:17,23`), strictly before Module 15's Phase-3 reads. The answer's own cited doc (`module_09.md` §7) lists Module 12 as consumer #1, so this was an avoidable confabulation, not a doc defect. No latent doc bugs.
