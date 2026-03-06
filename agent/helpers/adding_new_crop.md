# Helper: Adding a New Crop to MAgPIE

**Auto-load triggers**: "add crop", "new crop type", "add commodity", "extend crop set", "new product", "crop type"
**Last updated**: 2026-03-06
**Lessons count**: 1 entries

---

## Quick Reference

Adding a new crop is primarily a **data and set membership** task, not an equation-rewriting task. MAgPIE's equations iterate over the `kcr` set generically — once the new crop is a member and has valid input data, most equations automatically include it.

**Complexity**: 🔴 HIGH — requires ~9 set definition files and ~25+ input data files across 10+ modules. The hardest part is obtaining spatially-explicit biophysical yield data from LPJmL.

**No equation changes needed** unless the crop has special behavior (e.g., rice-like CH₄ emissions).

---

## Understanding MAgPIE's Crop System

### Set Hierarchy (defined in `modules/14_yields/managementcalib_aug19/sets.gms`)

```
kall (41 products)                           ← core/sets.gms:228
 └── k (28 primary)                          ← mod14/sets.gms:12
      └── kve (20 vegetal land-use)           ← mod14/sets.gms:18
           └── kcr (19 cropping activities)   ← mod14/sets.gms:23
                └── knbe14 (17 excl. bioenergy) ← mod14/sets.gms:28
```

The 19 crops in `kcr`: `tece, maiz, trce, rice_pro, soybean, rapeseed, groundnut, sunflower, oilpalm, puls_pro, potato, cassav_sp, sugr_cane, sugr_beet, others, foddr, cottn_pro, begr, betr`

### Cross-Cutting Sets (crop must also join ONE from each pair)

| Set pair | File | Decision |
|----------|------|----------|
| `kfo` (food) vs `knf` (non-food) | `modules/15_food/anthro_iso_jun22/sets.gms:77,118` | Is it consumed as food? |
| `kpr` (processable) vs `knpr` (non-processable) | `modules/20_processing/substitution_may21/sets.gms:10,15` | Does it produce secondary products? |
| `k_trade` vs `k_notrade` | `modules/21_trade/selfsuff_reduced/sets.gms:11,17` | Is it internationally tradable? |
| `crop_ann30` vs `crop_per30` | `modules/30_croparea/simple_apr24/sets.gms:45,48` | Annual or perennial? |
| `k_conc53` vs `k_noconc53` | `modules/53_methane/ipcc2006_aug22/sets.gms:10,16` | Concentrate or roughage feed? |

### Core Production Equation (`modules/30_croparea/simple_apr24/equations.gms:14-15`)

```gams
q30_prod(j2,kcr) ..
  vm_prod(j2,kcr) =e= sum(w, vm_area(j2,kcr,w) * vm_yld(j2,kcr,w));
```

This auto-includes any `kcr` member — no code edits needed.

---

## Step-by-Step: Adding a New Crop

### Step 1: Add to Set Definitions

Add the crop identifier to ALL of these sets (model won't compile if any is missing):

| # | File | Set | Line |
|---|------|-----|------|
| 1 | `core/sets.gms` | `kall` | 228-235 |
| 2 | `modules/14_yields/managementcalib_aug19/sets.gms` | `k(kall)` | 12 |
| 3 | same file | `kve(k)` | 18 |
| 4 | same file | `kcr(kve)` | 23 |
| 5 | same file | `knbe14(kcr)` | 28 (skip if bioenergy) |
| 6 | `modules/30_croparea/simple_apr24/sets.gms` | `crop_ann30` or `crop_per30` | 45 or 48 |
| 7 | same file | `crp_kcr30(crp30,kcr)` mapping | 18-37 |
| 8 | `modules/30_croparea/detail_apr24/sets.gms` | same subsets (mirror changes) | 56-95, 103-107 |
| 9 | `modules/15_food/anthro_iso_jun22/sets.gms` | `kfo` or `knf` | 77 or 118 |
| 10 | `modules/20_processing/substitution_may21/sets.gms` | `kpr` or `knpr` | 10 or 15 |
| 11 | `modules/21_trade/selfsuff_reduced/sets.gms` | `k_trade` or `k_notrade` | 17 or 11 |
| 12 | `modules/21_trade/selfsuff_reduced_bilateral22/sets.gms` | same (mirror) | — |
| 13 | `modules/21_trade/exo/sets.gms` | same (mirror) | — |
| 14 | `modules/18_residues/flexcluster_jul23/sets.gms` | `kres_kcr` mapping or `nonused18` | 28 or 23 |
| 15 | `modules/53_methane/ipcc2006_aug22/sets.gms` | `k_conc53` or `k_noconc53` | 10 or 16 |

If food crop, also add to relevant `kfo` subsets: `kfo_pp` (:93), `kst` (:88), `kfo_st` (:105), etc.

### Step 2: Create Rotation Constraint Entry

For `simple_apr24`, either map to an existing `crp30` type or create a new one:

**Option A: Map to existing type** — add crop to existing group in `crp_kcr30` mapping.
**Option B: New rotation type** — add new entry to `crp30` set, `crp_kcr30` mapping, and both CSV files:
- `modules/30_croparea/simple_apr24/input/f30_rotation_max.csv` (e.g., `newcrop_r,0.5`)
- `modules/30_croparea/simple_apr24/input/f30_rotation_min.csv` (e.g., `newcrop_r,0`)

For `detail_apr24`, update `rota30`, `rotamax30`/`rotamin30`, and `rota_kcr30` plus corresponding CSV files in `detail_apr24/input/`.

### Step 3: Provide Input Data

See the **Required Input Data** table below. The most critical and hardest to obtain:

1. **Biophysical yields** (`lpj_yields.cs3`) — requires LPJmL simulation or a defensible proxy
2. **Historical croparea** (`f30_croparea_w_initialisation.cs3`) — from FAO/FAOSTAT via madrat preprocessing
3. **FAO calibration yields** (`f14_region_yields.cs3`) — for yield calibration pipeline
4. **Product attributes** (`fm_attributes.cs3`, `fm_nutrition_attributes.cs3`) — nutritional/chemical properties

### Step 4: Test and Validate

1. Compile test: `gams main.gms action=C` — checks set consistency
2. Short test run: single timestep, one region
3. Check `vm_area.l` for the new crop — should it have nonzero area?
4. Check `vm_prod.l` — does production match area × yield?
5. Verify demand balance: `vm_supply` should cover demand
6. Check yield calibration: compare `vm_yld.l` against FAO targets

---

## Required Input Data

### Core Data (model fails without these)

| Parameter | Dimensions | File | Module |
|-----------|-----------|------|--------|
| `f14_yields` (biophysical yields) | `(t_all,j,kve,w)` | `modules/14_yields/input/lpj_yields.cs3` | 14 |
| `f14_fao_yields_hist` (FAO yields) | `(t_all,i,kcr)` | `modules/14_yields/managementcalib_aug19/input/f14_region_yields.cs3` | 14 |
| `f14_kcr_pollinator_dependence` | `(kcr)` | `modules/14_yields/input/f14_kcr_pollinator_dependence.csv` | 14 |
| `fm_croparea` (historical area) | `(t_all,j,w,kcr)` | `modules/30_croparea/input/f30_croparea_w_initialisation.cs3` | 30 |
| `fm_attributes` (DM/GE/NR/P/K/WM/C) | `(attributes,kall)` | `modules/16_demand/sector_may15/input/fm_attributes.cs3` | 16 |
| `fm_nutrition_attributes` (kcal/protein) | `(t_all,kall,nutrition)` | `modules/15_food/anthro_iso_jun22/input/fm_nutrition_attributes.cs3` | 15 |

### Secondary Data (needed for full model runs)

| Parameter | Dimensions | File | Module |
|-----------|-----------|------|--------|
| Factor costs | `(kcr)` or `(t_all,i,kcr)` | `modules/38_factor_costs/*/input/f38_fac_req*.csv` | 38 |
| Water requirement | `(t_all,j,kve)` | `modules/42_water_demand/input/lpj_airrig.cs2` | 42 |
| Residue attributes (AG) | `(attributes,kve)` | `modules/18_residues/input/f18_attributes_residue_ag.csv` | 18 |
| Residue attributes (BG) | `(dm_nr,kve)` | `modules/18_residues/input/f18_attributes_residue_bg.csv` | 18 |
| Crop growth functions | `(cgf,kve)` | `modules/18_residues/*/input/f18_cgf.csv` | 18 |
| N fixation (free-living) | `(kcr)` | `modules/50_nr_soil_budget/*/input/f50_fixation_freeliving.cs4` | 50 |
| N fixation (biological) | `(t_all,i,kcr)` | `modules/50_nr_soil_budget/*/input/f50_ndfa.cs4` | 50 |
| SOM land-use factor | `(i,climate59,kcr)` | `modules/59_som/*/input/f59_ch5_F_LU*.cs3` | 59 |
| SOM irrigation factor | `(climate59,w,kcr)` | `modules/59_som/*/input/f59_ch5_F_IRR.cs3` | 59 |
| Seed share | `(t_all,i,kcr)` | `modules/16_demand/sector_may15/input/f16_seed_shr.csv` | 16 |
| Waste share | `(t_all,i,kall)` | `modules/16_demand/input/f16_waste_shr.csv` | 16 |
| Domestic balance flow | `(t_all,i,kall)` | `modules/16_demand/input/f16_domestic_balanceflow.csv` | 16 |
| Self-sufficiency ratios | `(t_all,h,kall)` | `modules/21_trade/*/input/f21_self_suff.cs3` | 21 |
| Trade margins | `(h,kall)` | `modules/21_trade/*/input/f21_trade_margin.cs3` | 21 |
| Trade tariffs | `(h,kall)` | `modules/21_trade/*/input/f21_trade_tariff.cs3` | 21 |
| Food demand (if food) | `(t_all,iso,kfo)` | `modules/15_food/*/input/f15_kcal_pc_iso.cs3` | 15 |
| Processing (if processable) | `(t_all,processing20,ksd,kpr)` | `modules/20_processing/*/input/f20_processing_*.cs3` | 20 |

---

## Modules That Need Updates

| Module | Impact | What Changes | Auto-iterates? |
|--------|--------|-------------|----------------|
| **14_yields** | 🔴 Set definitions + 3 input files | Core yield calibration | Yes, via `kcr` |
| **30_croparea** | 🔴 Set definitions + 1 input file + rotation CSVs | Area allocation, rotation groups | Yes, via `kcr` |
| **16_demand** | 🔴 3 input files (`kall`-level) | Seed/waste/balance flow | Yes, via `kall` |
| **15_food** | 🔴 Set membership + input files | Food demand (if food crop) | Yes, via `kfo` |
| **38_factor_costs** | 🔴 2 input files | Production costs | Yes, via `kcr` |
| **18_residues** | 🟡 Set mapping + 4 input files | Residue production | Yes, via `kve` |
| **21_trade** | 🟡 Set membership + 4 input files | Trade parameters | Yes, via `kall` |
| **50_nr_soil_budget** | 🟡 2 input files | N fixation rates | Yes, via `kcr` |
| **59_som** | 🟡 2 input files | Soil carbon factors | Yes, via `kcr` |
| **42_water_demand** | 🟡 1 input file | Irrigation water needs | Yes, via `kve` |
| **20_processing** | 🟡 Input files (if processable) | Conversion factors | Yes, via `kpr` |
| **17_production** | 🟢 None | Spatial aggregation | Yes, auto |
| **29_cropland** | 🟢 None | Sums over `kcr` | Yes, auto |

---

## Validation Checklist

```
COMPILATION
  ☐ gams main.gms action=C passes without errors
  ☐ No "element not found" warnings in .lst file

SET CONSISTENCY
  ☐ Crop appears in kall, k, kve, kcr (and knbe14 if non-bioenergy)
  ☐ Crop appears in exactly one of: kfo/knf, kpr/knpr, k_trade/k_notrade
  ☐ Crop appears in exactly one of: crop_ann30/crop_per30
  ☐ Crop mapped in rotation constraints (crp_kcr30 or rota_kcr30)
  ☐ Crop mapped in residue sets (kres_kcr or nonused18)
  ☐ All three trade realizations updated consistently

YIELDS & PRODUCTION
  ☐ vm_yld.l(j,newcrop,w) has reasonable values (tDM/ha)
  ☐ vm_area.l(j,newcrop,w) is nonzero where expected
  ☐ vm_prod.l(j,newcrop) ≈ sum(w, area × yield)
  ☐ Calibration λ factors stay within [0,1] for limited calibration

DEMAND BALANCE
  ☐ vm_supply(i,newcrop) covers all demand components
  ☐ No infeasibilities from unsatisfied food demand (if kfo member)
  ☐ Trade balance flow sensible (f21_self_suff values reasonable)

NUTRIENT BALANCE
  ☐ fm_attributes values reasonable (compare with similar crops)
  ☐ N budget (module 50) not distorted
  ☐ Residue production proportional to harvest
```

---

## Common Pitfalls

1. **Missing from a subset** — Crop added to `kcr` but forgotten in `k_trade`/`k_notrade`. GAMS won't error but the crop will silently not participate in trade.

2. **Inconsistent realizations** — `sets.gms` exists in each realization separately (`simple_apr24`, `detail_apr24`). Updating only the default realization causes compile errors when switching.

3. **Zero yields everywhere** — If `lpj_yields.cs3` has no data for the crop, yields are zero and the optimizer allocates zero area. No error, just no production.

4. **Missing from residue mapping** — If not in `kres_kcr` AND not in `nonused18`, residue equations may produce unexpected results.

5. **Forgetting `fm_attributes`** — This static parameter has no time/region dimension. Missing entries cause zero nutrient content, breaking N/P/K budgets.

6. **Hardcoded crop proxies** — Some modules use specific crops as proxies (e.g., `"tece"` for fallow N-fixation at `modules/50_nr_soil_budget/macceff_aug22/equations.gms:26`, `"maiz"` for fallow SOM at `modules/59_som/cellpool_jan23/preloop.gms:75`). A new crop won't need changes here unless replacing the proxy.

7. **Food demand structure** — Module 15 uses regression-based demand with **fixed within-group shares** from historical FAO data. A new food crop needs entries in `f15_kcal_pc_iso.cs3` at the iso-country level, or it will have zero demand.

8. **Bioenergy special treatment** — If the new crop IS bioenergy: it needs `kbe30` membership, special yield correction in `modules/14_yields/managementcalib_aug19/preloop.gms:11-12`, and bioenergy switch handling in `modules/30_croparea/*/presolve.gms`.

---

## Module Cross-References

- [Module 14: Yields](../../modules/module_14.md) — Yield calibration pipeline, LPJmL input processing
- [Module 17: Production](../../modules/module_17.md) — Spatial aggregation (cluster → region)
- [Module 29: Cropland](../../modules/module_29.md) — Total cropland envelope
- [Module 30: Croparea](../../modules/module_30.md) — Per-crop area allocation, rotation constraints
- [Module 15: Food Demand](../../modules/module_15.md) — Regression-based food demand
- [Module 20: Processing](../../modules/module_20.md) — Primary → secondary product conversion
- [Data Flow](../core_docs/Data_Flow.md) — Input data pipeline and preprocessing

---

## Related Helpers & Docs

- **Modification safety** → `agent/helpers/modification_impact_analysis.md` (impact analysis for crop additions)
- **Infeasibility** → `agent/helpers/debugging_infeasibility.md` (new crop causing solver failures)
- **Land balance** → `cross_module/land_balance_conservation.md` (cropland allocation constraints)
- **Nitrogen balance** → `cross_module/nitrogen_food_balance.md` (nutrient requirements)

---

## Lessons Learned
<!-- APPEND-ONLY -->
- 2026-03-06: The kcr set (core/sets.gms) has 20 crop types. Adding a new crop requires entries in at least 15 set definition files and ~25 input data files. The most commonly missed step is forgetting to add the crop to SUBSETS (knbe14, kbe14, kcr_analog14, etc.) — the model compiles but produces wrong results because the new crop is excluded from key equations. (source: code analysis of set hierarchy)
