# Doc audit: cross_module/nitrogen_food_balance.md (Round 49)

**Auditor**: Opus adversarial doc auditor
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Date**: 2026-06-06
**Verdict**: MOSTLY ACCURATE (high quality). 1 confirmed Minor citation-range bug; several borderline items deferred. No Critical/Major found.

---

## Scope

This is a CROSS-MODULE conservation-law doc covering Nitrogen Balance (M50/51/59) and Food Balance (M16/17/21). Load-bearing, code-checkable claims: interface variable/equation names, file:line citations, demand-component → source-module mapping (a populator/consumer set), realization defaults, the NUE-rescaling formula, and the trade balance equation. Pure illustrative magnitude ranges (e.g. "50-250 kg N/ha/yr", IPCC EF percentages) are not code-checkable and were skipped.

---

## Realization-default verification (MANDATE 8)

`ls /tmp/magpie_develop_ro/modules/NN_*/` + `grep cfg$gms$... config/default.cfg`:

| Module | Doc-relevant realization | Code reality | OK? |
|---|---|---|---|
| 50 nr_soil_budget | macceff_aug22 (only) | macceff_aug22 (sole realization) | ✓ |
| 51 nitrogen | rescaled_jan21 (default) | default `rescaled_jan21`; also `off` | ✓ |
| 59 som | cellpool_jan23 (default) | default `cellpool_jan23`; also `static_jan19` | ✓ |
| 16 demand | sector_may15 (only) | sector_may15 (sole) | ✓ |
| 17 production | flexreg_apr16 (only) | flexreg_apr16 (sole) | ✓ |
| 21 trade | selfsuff_reduced (default) | default `selfsuff_reduced`; also `selfsuff_reduced_bilateral22`, `exo` | ✓ |
| 55 awms | M55 generic | dir `55_awms`; `ipcc2006_aug16` default, `off` | ✓ |
| 15 food | M15 generic | default `anthro_iso_jun22` | ✓ |

No wrong-default-realization errors. The doc does not over-claim a non-default realization anywhere.

---

## Identifier verification (MANDATEs 7, 18, 20)

All 16 substantive backtick identifiers confirmed present in code (`grep -rl` over modules+core, exit-checked):
`f16_waste_shr, f21_trade_balanceflow, n2o_n_direct, n2o_n_indirect, nh3_n, no2_n, no3_n, q16_waste_demand, q21_trade_glo, q21_trade_reg, v21_excess_dem, v21_excess_prod, v50_nr_surplus_cropland, vm_manure_recycling, vm_nr_inorg_fert_reg, vm_supply` → all FOUND.

Prose (non-backtick) identifiers also confirmed: `vm_nr_eff`, `vm_nr_som`, `vm_nr_som_fertilizer`, `vm_dem_food`, `vm_dem_feed`, `vm_dem_processing`, `vm_dem_material`, `vm_dem_bioen`, `vm_dem_seed`, `v16_dem_waste`, `vm_prod_reg`, `vm_prod`.

**`vm_import` / `vm_export` non-existence** (nfb:179): verified by TWO methods + positive control.
- `grep -rln "vm_import\|vm_export" modules core` -> exit 1 (no match).
- `rg -rln "vm_import|vm_export" modules core` -> "NO vm_import/vm_export (rg method)".
- Positive control: `grep -rln "vm_prod_reg" .../21_trade` -> 3 files. Search works; the absence is real.
- Doc correctly allowlists these with `<!-- check-gams-vars: allow vm_export, vm_import -->`. ✓ Claim CORRECT.

**Pollutant set members** (nfb:54-57): `no2_n` initially looked fabricated because `rg -rn "no2_n"` returned EMPTY, but the second-method `grep -rn "no2_n"` found it in `modules/56_ghg_policy/price_aug22/sets.gms:174,191,196,201,205` and `input.gms:60`. Confirmed real (member of `pollutants_all`, `pollutants`, `n_pollutants`, `n_pollutants_direct`, `pollutant_nh3no2_51`). All five labels (`n2o_n_direct, n2o_n_indirect, nh3_n, no3_n, no2_n`) are real. **NOTE: classic rg-silently-misses trap — cross-method check prevented a false-positive "fabricated set member" bug.**

**DECLARED/POPULATED/READ attributions** (MANDATE 18) — all correct:
- `vm_supply` DECLARED+POPULATED in M16 (`sector_may15/declarations.gms:11`, q16_supply_* eqs). ✓ nfb:116
- `vm_dem_food` DECLARED in M15 (`anthro_iso_jun22/declarations.gms:14`). ✓ nfb:135
- `vm_dem_feed` DECLARED in M70 (`fbask_jan16/declarations.gms:11`). ✓ nfb:136
- `vm_manure_recycling` POPULATED in M55 (`ipcc2006_aug16/equations.gms:83-87` q55_manure_recycling), READ by M50 (q50_nr_inputs:27) and M51 (q51_emissions_man_crop:25). ✓ nfb:34
- `vm_nr_som` / `vm_nr_som_fertilizer` DECLARED in M59 (`cellpool_jan23/declarations.gms:45-46`), READ by M51 (q51_emissions_som:58) and M50 (q50_nr_inputs:30). ✓ nfb:36
- `vm_nr_inorg_fert_reg` DECLARED in M50 (`macceff_aug22/declarations.gms:10`). ✓ nfb:32

---

## Equation / formula verification

**q50_nr_bal_crp** (nfb:38,74, cited :14-16): actual lines 14-16 `vm_nr_eff(i2) * v50_nr_inputs(i2) =g= sum(kcr,v50_nr_withdrawals(i2,kcr));`. It IS the `=g=` constraint. ✓ Citation exact.

**q50_nr_inputs** (nfb:38,74, cited :22-32): actual lines 22-32, ends `+ v50_nr_deposition(i2,"crop");` at line 32. ✓ Citation exact.

**q50_nr_surplus** (nfb:78,86,88,96): `v50_nr_surplus_cropland = v50_nr_inputs - sum(kcr, v50_nr_withdrawals)` (eq lines 46-49). Doc "v50_nr_surplus_cropland = inputs - withdrawals" ✓.

**"No soil-N stock tracked"** (nfb:88,96): VERIFIED. M50 `declarations.gms:9-21` declares only flow variables (all "Tg N per yr" / per-period); no soil mineral-N state/stock variable. Claim is correct.

**NUE-rescaling formula** (nfb:64): `emission = source / (1 - s51_snupe_base) * (1 - vm_nr_eff) * ef`. Matches code structure of q51_emissions_man_crop/inorg_fert/resid/som (e.g. eq:25-27 `vm_manure_recycling(i2,"nr") / (1-s51_snupe_base) * (1-vm_nr_eff(i2)) * sum(ct, i51_ef_n_soil(...))`). ✓ Faithful. `s51_snupe_base = 0.5` confirmed (`rescaled_jan21/input.gms:8`).

**MACCs-via-NUE claim** (nfb:66,104): "MACCs for soil N2O work indirectly through NUE in Module 50, NOT as a direct multiplier on emissions." VERIFIED against `macceff_aug22/presolve.gms:76`: `vm_nr_eff.fx(i) = 1 - (1-i50_nr_eff_bau(t,i)) * (1 - i50_maccs_mitigation_transf(t,i));`. MACCs enter via the transformed mitigation term into the FIXED vm_nr_eff, then rescaling propagates to emissions. ✓ Strong, correct claim.

**q21_trade_glo** (nfb:170-175, cited :12-14): actual lines 12-14 `sum(i2 ,vm_prod_reg(i2,k_trade)) =g= sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade));`. **EXACT match** incl. the balanceflow term. ✓ Citation exact. `f21_trade_balanceflow` is a table (`input.gms:37`, "Domestic balance flows") — doc's "historical trade balance flow / residual to reproduce observed FAO trade" characterization is reasonable.

**q17_prod_reg** (nfb:156): doc `vm_prod_reg(i,k) = sum(cell(i,j), vm_prod(j,k))`; actual (`flexreg_apr16/equations.gms:10-11`) `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`. ✓ Faithful.

**q16_waste_demand / v16_dem_waste / f16_waste_shr** (nfb:258): all present (`sector_may15/equations.gms:69-72`, `v16_dem_waste(i2,kall) =e= vm_supply(i2,kall) * sum(ct,f16_waste_shr(ct,i2,kall)) + ...`). ✓

**Demand-component -> source-module mapping** (nfb:116, 131-141): cross-checked against q16_supply_crops (eq:19-29): vm_dem_food (M15), vm_dem_feed (M70), vm_dem_processing (M20), vm_dem_material (M62), vm_dem_bioen (M60), vm_dem_seed + v16_dem_waste (M16 internal). ALL correct. (Doc omits f16_domestic_balanceflow from the table but mentions "balance flow" at nfb:175 — not a bug.)

---

## Bugs found

### Bug nfb-B1 (Minor) — citation range omits the named regional equation
- **Severity**: Minor (tier_uncertainty: between Minor and Major; tie-breaker pulls down — the range IS in the correct file/realization and contains sibling trade equations, and the section's global equation has its own correct citation two lines above).
- **Class**: 10 (stale/imprecise file:line citation) / partial Pattern-12 content-mismatch.
- **Trigger**: "File:line citation drift to adjacent but different content" (§1 Major) — downgraded to Minor per tie-breaker because the cited range is the correct file and points at the section's other (global) equation, with the target equation recoverable 6-20 lines below.
- **doc_line**: nitrogen_food_balance.md:183
- **Claim in doc**: "**Source**: Module 21, `modules/21_trade/selfsuff_reduced/equations.gms:10-25`" (closing the section that includes the "Regional Balance (Module 21, `q21_trade_reg`)" subsection at nfb:178-179).
- **Reality in code**: `q21_trade_reg(h2,k_trade)..` is at **lines 31-35**, OUTSIDE the cited 10-25 range. Lines 10-25 contain q21_trade_glo (12-14) and q21_notrade (18-19) only. A reader following the source pointer to find the named regional self-sufficiency equation would not find it in 10-25.
- **file_evidence**: `modules/21_trade/selfsuff_reduced/equations.gms:31` (q21_trade_reg); range 10-25 holds q21_trade_glo:12 + q21_notrade:18.
- **verify_cmd**: `grep -n "q21_trade_glo\|q21_trade_reg\b\|q21_notrade" /tmp/magpie_develop_ro/modules/21_trade/selfsuff_reduced/equations.gms` -> `12: q21_trade_glo`, `18: q21_notrade`, `31: q21_trade_reg`.
- **confirmed**: true.
- **proposed_fix**: Change nfb:183 to `**Source**: Module 21, `modules/21_trade/selfsuff_reduced/equations.gms:12-14` (q21_trade_glo) and `:31-35` (q21_trade_reg).` — or broaden the range to `equations.gms:12-42` so it spans both the global constraint and the regional production-band equations (q21_trade_reg 31-35, q21_trade_reg_up 39-42).

---

## Deferred (NOT edited — borderline, not a clear code-contradiction)

1. **nfb:104 "vm_nr_inorg_fert_reg, a free variable in Module 50"** — declared under `positive variables` (declarations.gms:9-10), i.e. GAMS-bounded >=0, not a GAMS `free variable`. BUT the model's OWN source comment (`macceff_aug22/equations.gms:20`) literally says "Inorganic fertilizers are a free variable that allow to balance...". The doc echoes the source's economic-sense "free" (free to adjust), not the GAMS keyword. Defensible; not flagged as a bug. (If the maintainer wants strict GAMS terminology, change "a free variable" -> "an endogenous (positive) variable".)

2. **nfb:179 "managed through ... `v21_excess_dem`, `v21_excess_prod`"** — `v21_excess_dem` actually appears in `q21_excess_dem` (global excess demand, eq:47), not literally in `q21_trade_reg`; `v21_excess_prod` is in m21_baseline_production used by q21_trade_reg (eq:33). Both are real components of the trade mechanism; the prose is a slightly loose summary of "trade variables" rather than a precise per-equation attribution. Not a clear contradiction.

3. **nfb:42 pseudocode in a ```gams fence** — `vm_nr_inorg_fert_reg(i,land_ag) + other_inputs >= N_withdrawal` is schematic (placeholders `other_inputs`, `N_withdrawal`; indexing `(i,land_ag)` vs the regional `(i2)` balance). Labeled "**Key Equation**" and clearly not literal GAMS. Borderline against MANDATE 5 (pseudocode-in-code-fence), but the actual equation is separately cited (q50_nr_bal_crp :14-16) and the placeholders make the schematic nature obvious. Not flagged.

4. **Equation glob `q51_emissions_*`** (nfb:59,68) — two of the eight M51 emission equations are actually named `q51_emissionbal_*` (q51_emissionbal_awms, q51_emissionbal_man_past), so the `q51_emissions_*` glob doesn't literally match all. But it's presented as a glob/family reference, not an exact equation name, and the doc never names a non-existent specific equation. Not flagged.

---

## Summary table spot-check (nfb:280-284)

Module-set attributions per balance law are coarse but consistent with the codebase: Land 10,29-35; Water 42,43 (water_demand, water_availability confirmed); Carbon 52,56,59; Nitrogen 50,51,59; Food 16,17,21. No errors worth flagging at this granularity.

---

## Overall

This doc is unusually clean — authored with evident code verification. It pre-empts the common confabulations (explicit vm_import/vm_export non-existence note + allowlist; correct DECLARED-vs-flow distinction for the no-soil-N-stock claim; faithful NUE-rescaling formula; correct demand-component source mapping). The single confirmed code-verifiable defect is the nfb:183 citation range that omits the regional equation it nominally sources (Minor). Everything else checked out against develop.

**claims_verified**: ~45 load-bearing claims (8 realization defaults, 16 backtick + 12 prose identifiers, 8 equation/formula checks, demand-component mapping with 7 sources, 5 file:line citations, vm_import/vm_export absence, no-soil-N-stock, MACCs-via-NUE).
