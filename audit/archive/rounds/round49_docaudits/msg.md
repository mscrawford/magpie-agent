# Audit Report: modification_safety_guide.md (Round 49)

**Doc**: `cross_module/modification_safety_guide.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (matches working tree)
**Auditor**: Opus 4.8 (1M)
**Date**: 2026-06-06

## Overall verdict: MOSTLY ACCURATE (lower band)

This is a high-quality doc whose consumer/populator SETS are mostly correct — the R3/R4/I1 footnote recomputations evidently held up. The two main exports tables (§1.2 vm_land 10-consumer list, §3.2 vm_prod_reg 8, Appendix B counts) verify exactly against code. The substantive errors are in a secondary "dependency chain" ASCII diagram (§3.3) that contradicts the doc's OWN correct table, and a stale carbon-price default string (§4.3).

---

## Claims verified CORRECT (high-confidence, code-checked)

### Realizations & defaults (MANDATE 8, 3)
- `10_land/landmatrix_dec18`, `11_costs/default`, `17_production/flexreg_apr16`, `56_ghg_policy/price_aug22`, `57_maccs/on_aug22` — all real dirs, all confirmed default in `config/default.cfg` (lines 232, 236, 612, 1613, 1822).
- `s56_c_price_induced_aff` default = 1 — confirmed `modules/56_ghg_policy/price_aug22/input.gms:69` (`/ 1 /`). Doc §4.3 + §4.5 cite input.gms:69 — exact.
- `c56_emis_policy` = `reddnatveg_nosoil` — `config/default.cfg:1810` ✓.
- `c56_carbon_stock_pricing` = `actualNoAcEst` — `config/default.cfg:1817`, input.gms:90 ✓.

### Module 10 consumer sets (§1.2)
- `vm_land` = **10** consumers, exactly {22, 29, 30, 31, 32, 34, 35, 50, 58, 59}. Verified `vm_land\b` grep + paren/attr cross-check. 58 reads via macro `m58_LandMerge(vm_land,...)` (58_peatland/v2/equations.gms:23); 22 reads via `.l`/`.lo` form. ✓
- `pcm_land` = **12** consumers {13, 22, 29, 31, 32, 34, 35, 44, 56, 58, 59, 71}. ✓
- `vm_landexpansion` = 4 {35, 39, 58, 59} ✓; `vm_landreduction` = 2 {39, 58} ✓; `vm_lu_transitions` = 3 {29, 35, 59} ✓.
- 18-module union (§1.2 line 58, §1.4 line 92): {11, 13, 14, 22, 29, 30, 31, 32, 34, 35, 39, 44, 50, 56, 58, 59, 71, 80} — exact match to code. ✓
- `pcm_land` calc cited at `postsolve.gms:8-9` — assignment `pcm_land(j,land) = vm_land.l(j,land);` is at line 9 (comment line 8). ✓
- Variable signatures: `vm_land(j,land)`, `vm_landexpansion(j,land)`, `vm_landreduction(j,land)`, `vm_lu_transitions(j,land_from,land_to)` — all exact (declarations.gms:19-23). ✓
- `land` set = 7 members {crop, past, forestry, primforest, secdforest, urban, other} (core/sets.gms:251). ✓

### Module 11 (§2.2)
- Cost-variable attributions all correct: vm_cost_prod_crop→38, vm_cost_prod_past→31, vm_cost_prod_livst→70, vm_nr_inorg_fert_costs→50, vm_emission_costs→56, vm_cost_landcon→39, trade trio→21. ✓
- "depends on cost variables from 27 modules" + Appendix A "Depends On 27" — enumerated q11_cost_reg cost vars → exactly **27** unique source modules. ✓
- Equation names `q11_cost_glo`, `q11_cost_reg` + FIX snippet `q11_cost_reg(i2) .. v11_cost_reg(i2) =e=` — exact (equations.gms:10,15). ✓
- `vm_cost_glo` is the minimized objective (`q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2))`). ✓

### Module 17 (§3.2)
- `vm_prod_reg` = **8** consumers {16, 18, 20, 21, 38, 50, 70, 71} — exact match to doc's footnote list. ✓
- `pm_prod_init` = **1** consumer {38_factor_costs} ✓.
- Both DECLARED in `17_production/flexreg_apr16/declarations.gms:10,18` ✓ (MANDATE 18).
- `pm_prod_init` formula at `presolve.gms:10`: `pm_prod_init(j,kcr)=sum(w,fm_croparea("y1995",j,w,kcr)*pm_yields_semi_calib(j,kcr,w));` — exact match to doc §3.4 FIX (line 389). ✓

### Module 56 (§4.2, §4.5)
- `vm_emission_costs` consumers = {11_costs, 15_food} ✓. 15_food reads via `vm_emission_costs.l` in `anthro_iso_jun22/intersolve.gms:23` for tax recycling — exactly as doc footnote says. ✓
- `vm_reward_cdr_aff` consumer = {11_costs} ✓.
- `im_pollutant_prices` consumer = {57_maccs} ✓; signature `(t_all,i,pollutants,emis_source)` exact ✓.
- 57 reads im_pollutant_prices for MAC sizing at `on_aug22/preloop.gms:24-25` (`i57_mac_step_n2o`/`i57_mac_step_ch4`) — exact citation. ✓
- `q56_emission_costs` (equations.gms:56), `q56_emis_pricing_co2` (equations.gms:19) — both exist. ✓
- §4.5: `q56_emis_pricing_co2 uses (pcm_carbon_stock - vm_carbon_stock)` — confirmed equations.gms:22. ✓

### Appendix A / B
- Appendix A counts (28/17/16/16/15/14/14/14/13/12) match Module_Dependencies.md:29-40 exactly; cited line range correct.
- Appendix B: im_pop_iso=10, pm_interest=9, vm_prod=8, vm_prod_reg=8, vm_area=8, vm_land=10 — all match code AND Module_Dependencies.md:46-59. ✓

---

## BUGS FOUND

### BUG-1 (Major) — §3.3 dependency-chain diagram lists 2 phantom consumers + wrong count
- **doc_line**: modification_safety_guide.md:355-357
- **Class**: 15 (latent doc error) / MANDATE 17 (direct vs transitive)
- **Trigger**: §1 Major — "wrong consumer set" misleads about behavior (R20 anchor is Critical-prone, but this is a secondary diagram contradicted by the doc's own correct §3.2 table → pull down to Major).
- **Claim**: diagram shows `vm_prod_reg(i,kall)` → Module 21 (Trade) → Module 16 (Demand) → **Module 11 (Costs)** → **Module 73 (Timber)** → "**9 other modules**".
- **Reality**: `vm_prod_reg` has exactly **8** direct consumers: {16_demand, 18_residues, 20_processing, 21_trade, 38_factor_costs, 50_nr_soil_budget, 70_livestock, 71_disagg_lvst}. **11_costs does NOT read vm_prod_reg** (it reads cost vars vm_cost_*); **73_timber does NOT read vm_prod_reg**. Of the 4 named modules, only 21 and 16 are real consumers; remaining real consumers are {18, 20, 38, 50, 70, 71} = 6, so "9 other modules" overcounts. The diagram is internally inconsistent with the doc's own §3.2 table ("8 modules") and Appendix B ("8").
- **file_evidence**: declared `modules/17_production/flexreg_apr16/declarations.gms:10`; consumers confirmed by `rg -l 'vm_prod_reg\b'`; 11_costs negative confirmed twice (rg + grep -E) with positive control (11_costs DOES read vm_cost_processing at `modules/11_costs/default/equations.gms`).
- **verify_cmd**: `rg -l 'vm_prod_reg\b' /tmp/magpie_develop_ro/modules/ --glob '*.gms' | awk -F/ '{print $2}' | sort -u | grep -v '^17_production'` → `16_demand 18_residues 20_processing 21_trade 38_factor_costs 50_nr_soil_budget 70_livestock 71_disagg_lvst` (8). `rg -n 'vm_prod_reg' /tmp/magpie_develop_ro/modules/11_costs/` → (no output); `rg -n 'vm_prod_reg' /tmp/magpie_develop_ro/modules/73_timber/` → (no output).
- **confirmed**: true
- **proposed_fix**: Replace the diagram body (lines 353-357) with the correct 8-consumer set:
```
Module 30 (Croparea) → vm_prod(j,k) → Module 17 → vm_prod_reg(i,kall) → 21_trade
                                                                      → 16_demand
                                                                      → 18_residues, 20_processing,
                                                                        38_factor_costs, 50_nr_soil_budget,
                                                                        70_livestock, 71_disagg_lvst
```
(8 direct consumers total — matches §3.2 table. 11_costs and 73_timber consume Module 17's *costs* indirectly via other variables, not vm_prod_reg.)

### BUG-2 (Minor) — §4.3 stale/incomplete carbon-price default value
- **doc_line**: modification_safety_guide.md:478
- **Class**: 13 (wrong parameter default) — but value is a substring of the real one and concept is right → tie-breaker pulls to Minor.
- **Trigger**: §1 Minor — "stale default that's recoverable (correct concept, findable)".
- **Claim**: §4.3 table: `c56_pollutant_prices` | Default `SSP2-NPi2025`.
- **Reality**: actual default is `R34M410-SSP2-NPi2025` (the `R34M410-` scenario-protocol prefix is missing). `config/default.cfg:1713`: `cfg$gms$c56_pollutant_prices <- "R34M410-SSP2-NPi2025"     # def = R34M410-SSP2-NPi2025`; also `input.gms:84`. A user searching the available-scenarios list for the exact string "SSP2-NPi2025" would not find an exact match.
- **file_evidence**: `/tmp/magpie_develop_ro/config/default.cfg:1713`; `modules/56_ghg_policy/price_aug22/input.gms:84`.
- **verify_cmd**: `grep -n 'c56_pollutant_prices' /tmp/magpie_develop_ro/config/default.cfg` → line 1713 `<- "R34M410-SSP2-NPi2025"`; `grep -n 'c56_pollutant_prices' /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/input.gms` → line 84 `$setglobal c56_pollutant_prices  R34M410-SSP2-NPi2025`.
- **confirmed**: true
- **proposed_fix**: In §4.3 table line 478, change the Default cell from `SSP2-NPi2025` to `R34M410-SSP2-NPi2025`.

---

## Deferred (not code-verifiable / not flagging)

- §4.4 "Complex Interactions" diagram (lines 490-496): the arrow `CDR Rewards → 32_forestry (afforestation incentive)` — `vm_reward_cdr_aff` is NOT directly read by 32_forestry (consumer = 11_costs only); 32 instead PRODUCES `vm_cdr_aff` (q32_cdr_aff) which feeds 56's reward, and the optimizer responds via the global objective. The arrow is a CONCEPTUAL/causal-flow claim (the economic incentive to afforest IS real), explicitly under "Complex Interactions", not a direct-consumer table. Borderline MANDATE-17, but the causal statement is true; not flagging as a hard code-contradicting bug. Worth a future tightening pass if the maintainer wants the diagram to be a strict variable-flow graph.
- All R-code snippets (magpie4 function calls: `land()`, `production()`, `costs()`, `land_transitions()`, `trade_balance()`, `carbonstock()`, etc.) — these are downstream magpie4 API, out of scope for code-vs-GAMS audit; not verified against the magpie4 pinned clone.
- Magnitude bounds (§2.2 "USD17/yr" typical magnitudes; §2.4 500-2000 billion; §4.3 "0-1000+ USD/tCO2"; §4.5 "0-500 USD/tCO2 by 2100") — illustrative/order-of-magnitude advisory, not exact code constants; not flagged.
- Doc-to-doc citations ("Source: module_11.md lines 84-115", "module_56.md lines 32-42 / 79-101") — point at the agent's own module docs, not code; out of this audit's scope.
- Appendix A column header "Connections" vs Module_Dependencies.md's "Total" — cosmetic relabel, same values; not a code error.

---

## Notes for the flywheel
The doc's own footnotes (R3 2026-05-23, I1 2026-05-24, R4 2026-05-24) document prior consumer-count recomputations; those held up perfectly under re-audit. The only consumer-set error that slipped through is in the §3.3 ASCII diagram, which was NOT covered by those footnote recomputations (they fixed the tables, not the prose diagrams). Lesson: when recomputing consumer counts for tables, also sweep the prose/diagram dependency-chain sections in the same doc — they drift independently (cf. MANDATE 15 post-rename global grep, same failure shape).
