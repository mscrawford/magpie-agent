# Audit Report: R49 cbc-soil (Soil + Peatland carbon in MAgPIE carbon accounting)

**Auditor**: Opus 4.8 (1M)
**Date**: 2026-06-06
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Anchor doc**: `cross_module/carbon_balance_conservation.md` (+ module_58.md, module_59.md)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

score = max(0, 10 - 4*crit - 2*major - 1*minor) = 10 - 2*1(major) - 0 = **8**
(1 Major + 1 Informational; the Informational does not subtract.)

---

## Verified Claims (correct) — the spine of the answer is strong

**Realizations / defaults (all verified in config/default.cfg):**
- M59 default `cellpool_jan23` ✓ (default.cfg:1916)
- M58 default `v2` ✓ (default.cfg:1853); `s58_fix_peatland = 2020` ✓ (default.cfg:1910, input.gms:15)
- M52 default `normal_dec17` ✓ (default.cfg:1556); M56 default `price_aug22` ✓ (default.cfg:1613)
- `s59_scm_target = 0` ✓ (input.gms:11); `s59_cost_scm_recur = 65` ✓ (input.gms:15)
- `s58_cost_rewet_recur = 37` ✓ (input.gms:9); `s58_cost_drain_recur = 0` ✓ (input.gms:11)

**vm_carbon_stock DECLARED/POPULATED/READ (the G2 distinction — handled correctly):**
- DECLARED in M56 `price_aug22/declarations.gms:34`, 4-dim `(j,land,c_pools,stockType)` ✓
- M59 POPULATES the `soilc` slice via `q59_carbon_soil` (`modules/59_som/cellpool_jan23/equations.gms:61-64`) ✓ — exact formula match
- Non-soilc slices populated by M29 (crop), M31 (past), M32 (forestry), M35 (primforest/secdforest/other) ✓ — all verified as direct LHS populators
- **M34 listed as a populator**: correct and shows good grep discipline — M34 does not appear in an equation-LHS grep, but populates via `.fx`: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType)=0` (`modules/34_urban/exo_nov21/presolve.gms:8`). Answer's MANDATE-20-style inclusion is right.
- **M30 correctly OMITTED** from the populator list — M30 populates `vm_carbon_stock_croparea` (a different var) consumed one-hop by M29; not a direct populator of `vm_carbon_stock`. (MANDATE 17 handled correctly.)
- M52 only READS `vm_carbon_stock` (RHS, `normal_dec17/equations.gms:19`) ✓

**M52 emission equation:** `q52_emis_co2_actual` formula + citation `modules/52_carbon/normal_dec17/equations.gms:16-19` verified exact ✓. `emis_land` `crop_soilc` label ✓ (core/sets.gms:335). soilc lands in `emis_oneoff` (incl. `crop_soilc`) ✓ (core/sets.gms:314-318).

**M59 secondary interfaces:** `vm_nr_som` (decl:45; q59_nr_som eq:69-75) → M51; `vm_nr_som_fertilizer` (decl:46) → M50; C:N 15:1 (eq:76); `vm_cost_scm` (decl:41; q59_cost_scm eq:98-101) → M11 — all citations verified ✓. `i59_subsoilc_density = fm_carbon_density(...,"other","soilc") - f59_topsoilc_density` (`preloop.gms:12`) ✓.

**M59 lossrate — answer BEAT the code's own comment:** answer states `i59_lossrate = 1 - 0.85^m_yeardiff` → "~56% per 5-yr". Verified: `1 - 0.85^5 = 0.556`. The code's OWN comment (`preloop.gms:42`) mislabels this as "44% in 5 years" (44% = 0.85^5, the retention fraction). The answer's ~56% is the arithmetically correct loss rate. Not a bug; a positive.

**M58 (all verified):**
- No organic C stock; limitation quote `realization.gms:31-32` ✓
- `v58_peatland` positive var (decl:50); 7 states `land58` (sets.gms:10-11) ✓; `manPeat58 = {crop,past,forestry}` (sets.gms:16-17) ✓
- `v58_peatland_emis` free var (decl:46) ✓
- `q58_peatland_emis_detail` (eq:84-87) + `q58_peatland_emis` (eq:91-94) formulas + citations verified exact ✓
- `emisSub58_to_poll58`: co2→co2_c, doc→co2_c, ch4→ch4, n2o→n2o_n_direct (sets.gms:39-43) ✓
- preloop: intact EF = rewetted EF (`preloop.gms:43`) ✓; non-poll58 fixed 0 (`preloop.gms:31`) ✓
- `q58_peatland` conservation (eq:12-13) ✓; `q58_peatlandMan` (eq:46-50) gated on `s58_fix_peatland`, sources from M10+M32 via `m58_LandMerge(vm_landexpansion, vm_landexpansion_forestry)` ✓
- Pre-fix-year fixing: `v58_peatland.fx = pc58_peatland` (`presolve.gms:23`) ✓
- `vm_peatland_cost` (decl:45; q58_peatland_cost eq:71-75) components verified ✓
- **M58 → GHG totals AND pricing chain CORRECT**: `peatland` ∈ `emis_annual` (core/sets.gms:320-322); M56's `q56_emis_pricing` reads `vm_emissions_reg(i2,emis_annual,...)` (`price_aug22/equations.gms:15-17`), i.e. M56 DOES price the M58-populated `"peatland"` slice. Answer's "M58 writes peatland slice directly → M56 prices" is right.

**M58/M59 no interaction** ✓ (M59 has zero peatland refs; M58's only "SOM" token is ISO code Somalia).

---

## Bugs Found

### Bug R49-cbc-soil-B1 — soilc CO2 pricing path: invented M52→M56 hand-off
- **Severity**: Major
- **Class**: 4 (conceptual mechanism) / MANDATE 2 + 17 (causal-mechanism / direct-vs-transitive)
- **Trigger** (§1 Major): "wrong in a way that misleads about behavior, but won't directly cause damaging action."
- **Claim in answer**:
  > "Once M59 populates the soilc slice of `vm_carbon_stock`, Module 52 takes over via `q52_emis_co2_actual` ... This emission ... [is] then routed to Module 56 for carbon pricing."
  and summary-table row: "**Module 56 receives from** | M52 (land-use CO2 including soilc)".
- **Reality in code**: For one-off (land-use, incl. `*_soilc`) CO2, **M56 reads `vm_carbon_stock` DIRECTLY** in `q56_emis_pricing_co2` (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`) — it does NOT consume M52's output. M52's `q52_emis_co2_actual` (`52_carbon/normal_dec17/equations.gms:16-19`) populates `vm_emissions_reg(emis_oneoff,"co2_c")` for the emission **totals/reporting** stream. M56 reads `vm_emissions_reg` only for the **disjoint** `emis_annual` subset (line 17), which does NOT include the `*_soilc`/land-pool one-off members (`emis_oneoff` and `emis_annual` are disjoint per core/sets.gms:314-322). So M52 and M56 are **parallel readers of `vm_carbon_stock`**, not a producer→consumer pair.
- **File evidence**:
  - `modules/56_ghg_policy/price_aug22/equations.gms:19-22` — `q56_emis_pricing_co2 .. v56_emis_pricing(i2,emis_oneoff,"co2_c") =e= sum(... emis_land ...) (pcm_carbon_stock - vm_carbon_stock(...,"%c56_carbon_stock_pricing%"))/m_timestep_length` (reads the STOCK, not vm_emissions_reg).
  - `modules/56_ghg_policy/price_aug22/equations.gms:15-17` — M56 reads `vm_emissions_reg` only for `emis_annual`.
  - `core/sets.gms:314-322` — `emis_oneoff` (soilc lives here) and `emis_annual` are disjoint.
- **Mitigating**: The question asks "how do they enter the GHG emission **totals**?" — and the totals (vm_emissions_reg) ARE populated by M52's q52 for soilc. The answer's body also separately, correctly named M56 as the pricer and M52 as the stock-reader/emission-writer. The defect is narrowly the **data-flow arrow** (M52→M56) and the summary cell, not a wrong variable/equation/file. Hence Major, not Critical (tie-breaker pulls down; no invented identifier, no wrong edit target — contrast the G2/R20 Critical anchor which is a wrong producer/consumer SET).
- **Root cause**: `answerer_confabulation`. The anchor doc does NOT make this error — `carbon_balance_conservation.md:615` correctly states "All populated slices flow to Module 52 **and** Module 56" (parallel), and :504/:509 show M52 reads the stock from all land modules. The answer collapsed the parallel-readers structure into a serial M52→M56 hand-off.

### Bug R49-cbc-soil-B2 — peatland EF magnitudes claimed "from the data file" but not actually read
- **Severity**: Informational (tie-breaker pull-down: magnitudes cannot be shown wrong)
- **Class**: 1.5-adjacent sourcing/framing (no Bug_Taxonomy content-error established)
- **Claim in answer**: "Key factor values **from the data file**: tropical drained cropland CO2 = 14 tC/ha/yr; temperate crop = 9.5; boreal rewetted CO2 = -0.34 tC/ha/yr."
- **Reality**: `f58_ipcc_wetland_ef2.cs3` is a downloaded input (`modules/58_peatland/input/`) and is NOT present in the worktree; the answer's epistemic footer states "No raw GAMS code read." The values are thus attributed to "the data file" they did not read. I can neither verify nor refute the magnitudes (file absent). The provenance claim overstates verification depth.
- **File evidence**: `modules/58_peatland/v2/input.gms:74-78` declares the table with units "(Tg per ha per yr)" and `$include` of the (absent) `f58_ipcc_wetland_ef2.cs3`. (Answer's per-gas units gloss "tC/tN/tCH4 per ha/yr" is a defensible reading of the Tg-per-gas mapping; not scored.)
- **Root cause**: `answerer_style_or_framing` (false source attribution; values plausibly correct).

---

## Latent doc bugs (recorded independent of answer score)

**None found.** The load-bearing carbon-stock claims in `cross_module/carbon_balance_conservation.md` were cross-checked against develop and are correct:
- Declaration site M56 `price_aug22/declarations.gms:34` (doc:101, :542) ✓
- `q59_carbon_soil` at `cellpool_jan23/equations.gms:61-64` (doc:542) ✓
- `q52_emis_co2_actual` at `normal_dec17/equations.gms:16-19` (doc:265, formula block :268-272) ✓
- M34 `.fx` at `34_urban/exo_nov21/presolve.gms:8` (doc:605) ✓
- M30→M29 one-hop; M29 direct crop populator (doc:593-594) ✓
- Direct-populator set {29,31,32,34,35}+59 soilc; "flow to M52 and M56" parallel framing (doc:612-615) ✓

The doc is the SSOT the answer should have followed on the pricing path; the answer deviated from it (B1), so no doc fix is warranted.

---

## Missing Nuances (not scored)
- The answer never states that M56's CO2 pricing uses `c56_carbon_stock_pricing` to choose the `stockType` slice (default `cc`/`"actual"` per the `%c56_carbon_stock_pricing%` macro at `price_aug22/equations.gms:22`) — minor omission, the question did not ask for the pricing-scenario switch.
- `som` ALSO appears as an `emis_annual` source (core/sets.gms:321) — but that is the N2O-from-SOM path (M59 `vm_nr_som` → M51), NOT a CO2 channel; the answer correctly kept `vm_nr_som` separate from the soilc CO2 question, so no confusion introduced.

---

## Summary
A strong, citation-dense answer. The architectural split (M59 = dynamic stock into `vm_carbon_stock`; M58 = direct area×EF emission stream to `vm_emissions_reg`, no stock) is correct, and the DECLARED/POPULATED/READ discipline on `vm_carbon_stock` is handled better than most rounds (M30 correctly excluded as one-hop, M34 correctly included via `.fx`). The M58 chain is fully correct including the `peatland ∈ emis_annual → M56 q56_emis_pricing` pricing route. One Major mechanism error: the soilc-CO2 **pricing** path is misdescribed as M52→M56 routing, when M56 reads `vm_carbon_stock` directly and M52 only feeds the totals stream (the two are parallel readers; doc:615 had it right and the answer regressed off it). One Informational: peatland EF magnitudes attributed to a data file the answer did not read. Net: 1 Major → **8/10**.
