# Helper: Choosing Between Realizations

**Auto-load triggers**: "which realization", "choose realization", "realization comparison", "default realization", "switch realization", "alternative realization"
**Last updated**: 2026-03-06
**Lessons count**: 1 entries

---

## Quick Reference

A **realization** is one of several alternative implementations of a MAgPIE module. Each module has exactly one active realization per run, selected at compile time. Non-selected realizations are never compiled into the model.

**Mechanism** (compile-time dispatch chain):
1. `config/default.cfg` sets `cfg$gms$<module> <- "<realization>"` (R syntax)
2. R's `lucode2::manipulateConfig()` rewrites `$setglobal <module> <realization>` in `main.gms`
3. `main.gms` calls `$batinclude "./modules/include.gms" <phase>` for each phase
4. `include.gms` sets `$setglobal phase %1` then includes every `module.gms`
5. Each `module.gms` uses `$Ifi "%module%" == "realization"` to include only the matching `realization.gms`
6. Each `realization.gms` uses `$Ifi "%phase%" == "..."` to include the current phase file

**Key fact**: Many modules (24 of 46) have only 1 realization. Behavioral variation comes from **switches** (`s*`, `c*` scalars) within that realization, not from swapping realizations. Always check switches before assuming you need a different realization.

**Statistics**: 46 modules total, 73 active realizations, 22 modules with multiple realizations.

## How to Switch Realizations

**Method 1 — Edit config directly** (for single runs):
1. Open `config/default.cfg`
2. Find the line `cfg$gms$<module> <- "..."` (search for module name)
3. Change the realization name to your desired option
4. If the module requires recalibration (see table below), set `cfg$recalibrate <- TRUE`
5. Run with `Rscript start.R`

**Method 2 — Start script override** (for scenarios):
1. Create or edit a script in `scripts/start/`
2. Override: `cfg$gms$<module> <- "new_realization"`
3. This overrides `default.cfg` without modifying it

**Method 3 — Programmatic via `lucode2`**:
```r
cfg <- gms::readDefaultConfig()
cfg$gms$trade <- "selfsuff_reduced_bilateral22"
gms::startRun(cfg)
```

**Verification**: After a run starts, check `full.gms` in the output folder — it contains the fully resolved GAMS code with only the selected realizations compiled in.

## Modules with Multiple Realizations

Of 46 modules, **22 have multiple realizations**. The rest have a single implementation.

| Module | Name | Default ✅ | Alternatives | Key Difference |
|--------|------|-----------|--------------|----------------|
| 13 | tc | `endo_jan22` | `exo` | Endogenous TC (NLP) vs exogenous (linear, faster, needs prior endo run) |
| 18 | residues | `flexreg_apr16` | `flexcluster_jul23`, `off` | Regional vs cluster-level residue handling, or disabled |
| 21 | trade | `selfsuff_reduced` | `exo`, `selfsuff_reduced_bilateral22` | Self-sufficiency pools vs exogenous vs bilateral flows |
| 29 | cropland | `detail_apr24` | `simple_apr24` | Fallow land & tree cover modeled vs fixed to zero ⚠️ recalib |
| 30 | croparea | `simple_apr24` | `detail_apr24` | Simple vs detailed rotational constraints ⚠️ recalib |
| 31 | past | `endo_jun13` | `static` | Dynamic vs static pasture management ⚠️ recalib |
| 34 | urban | `exo_nov21` | `static` | SSP-based urban expansion vs fixed 1995 patterns |
| 37 | labor_prod | `off` | `exo` | Labor productivity fixed at 1 vs climate-impacted (only used by `sticky_labor` factor costs) |
| 38 | factor_costs | `sticky_feb18` | `per_ton_fao_may22`, `sticky_labor` | Capital investment vs per-ton vs capital+labor productivity ⚠️ recalib |
| 40 | transport | `gtap_nov12` | `off` | GTAP-calibrated transport costs vs none |
| 41 | irrigation | `endo_apr13` | `static` | Endogenous irrigation investment vs no expansion |
| 42 | water_demand | `all_sectors_aug13` | `agr_sector_aug13` | All-sector WATERGAP data vs ag-only with flat reservation |
| 44 | biodiversity | `bii_target` | `bv_btc_mar21` | BII per 71 biomes vs range-rarity weighted biodiversity value |
| 51 | nitrogen | `rescaled_jan21` | `off` | IPCC N₂O with rescaled efficiency vs disabled |
| 53 | methane | `ipcc2006_aug22` | `off` | IPCC 2006 CH₄ accounting vs disabled |
| 55 | awms | `ipcc2006_aug16` | `off` | Animal waste management vs disabled |
| 58 | peatland | `v2` | `off` | Peatland GHG emissions vs disabled |
| 59 | som | `cellpool_jan23` | `static_jan19` | Dynamic cell-level SOC (IPCC 2019) vs static loss (IPCC 2006) |
| 60 | bioenergy | `1st2ndgen_priced_feb24` | `1stgen_priced_dec18` | 1st+2nd gen bioenergy vs 1st gen only |
| 70 | livestock | `fbask_jan16` | `fbask_jan16_sticky` | Simple proportional costs vs investment-based sticky capital |
| 71 | disagg_lvst | `foragebased_jul23` | `foragebased_aug18`, `off` | Improved forage-based disaggregation vs older version vs off |
| 80 | optimization | `nlp_apr17` | `lp_nlp_apr17`, `nlp_par` | Pure NLP vs LP warmstart→NLP vs parallel NLP |

## Key Decision Points

### Modules with Only One Realization (no switching possible)
These major modules have a single realization — use **switches** for behavioral variation:
- **14_yields** (`managementcalib_aug19`): Use `s14_degradation`, `s14_calib_ir2rf` switches
- **15_food** (`anthro_iso_jun22`): Use `s15_elastic_demand`, `c15_food_scenario`, `c15_calibscen` switches
- **32_forestry** (`dynamic_may24`): Use `s32_hvarea`, `c32_rot_calc_type`, `c32_aff_policy` switches
- **35_natveg** (`pot_forest_may24`): Use `s35_forest_damage`, `s35_hvarea`, `c35_ad_policy` switches
- **52_carbon** (`normal_dec17`): Use `c52_carbon_scenario` switch
- **56_ghg_policy** (`price_aug22`): Use `c56_pollutant_prices`, `c56_emis_policy` switches

### Module 13 — Technological Change: `endo_jan22` vs `exo`
- **`endo_jan22`** (default): TC is endogenously optimized. Introduces non-linearity (NLP). Use for standard research runs.
- **`exo`**: TC is prescribed from a prior endogenous run (requires input file `f13_tau_scenario.csv`). Removes NLP non-linearity. Use for faster runs, debugging, or when linearizing the model.
- ⚠️ `exo` **requires a completed `endo_jan22` run** to generate its input.

### Module 21 — Trade: `selfsuff_reduced` vs `exo` vs `bilateral22`
- **`selfsuff_reduced`** (default): Two-pool trade at superregional level. Best balance of speed and trade representation.
- **`exo`**: Fully exogenous trade, regions isolated. Use for debugging or fixed-trade scenarios.
- **`selfsuff_reduced_bilateral22`**: Adds explicit bilateral flows, tariff fadeout. Use when analyzing specific trade corridors or bilateral tariff policy. Slowest option.
- All three expose the same interface (`vm_cost_trade`) — fully interchangeable.

### Module 38 — Factor Costs: `sticky_feb18` vs `per_ton_fao_may22` vs `sticky_labor`
- **`sticky_feb18`** (default): Capital investment with depreciation. Path-dependent costs create realistic inertia.
- **`per_ton_fao_may22`**: Simple per-ton costs from FAO data. No capital dynamics. Use for simplified analysis.
- **`sticky_labor`**: Extends `sticky_feb18` with climate-affected labor productivity from Module 37. Use when studying climate impacts on labor. Requires `cfg$gms$labor_prod <- "exo"` to be meaningful.
- ⚠️ All three require **recalibration** when switching.

### Module 42 — Water Demand: `all_sectors_aug13` vs `agr_sector_aug13`
- **`all_sectors_aug13`** (default): Uses WATERGAP data for manufacturing, electricity, domestic water demand. SSP-differentiated. Use for water scarcity studies.
- **`agr_sector_aug13`**: Reserves a flat 50% of water for non-ag uses. Simpler. Use when water competition detail is not needed.

### Module 59 — Soil Organic Matter: `cellpool_jan23` vs `static_jan19`
- **`cellpool_jan23`** (default): Dynamic SOC with 15%/yr convergence, crop-specific factors (IPCC 2019), nitrogen release feedback to Module 51. Use for SOC studies, nitrogen cycling, modern standard runs.
- **`static_jan19`**: Instantaneous SOC loss at conversion, single factor (IPCC 2006). Use for legacy comparisons or speed.
- Key: `cellpool_jan23` provides meaningful `vm_nr_som` to nitrogen module; `static_jan19` effectively returns zero.

### Module 70 — Livestock: `fbask_jan16` vs `fbask_jan16_sticky`
- **`fbask_jan16`** (default): Simple proportional feed costs. Each timestep is independent. Use for standard runs.
- **`fbask_jan16_sticky`**: Adds investment-based capital with depreciation. Creates path dependency — expansion is costly, contraction is "free" (sunk capital). Use for structural change studies or consistency with `sticky_feb18` factor costs.

### Module 29/30 — Cropland & Croparea: `detail_apr24` vs `simple_apr24`
- **29_cropland `detail_apr24`** (default): Models fallow land and tree cover on cropland. **30_croparea `simple_apr24`** (default): Simple rotational constraints.
- Switching either to the alternative changes crop area dynamics significantly.
- ⚠️ Both require **recalibration** when switching. These are often switched together.

### Module 31 — Pasture: `endo_jun13` vs `static`
- **`endo_jun13`** (default): Dynamic pasture with endogenous management intensification.
- **`static`**: Pasture area and management fixed. Use for debugging or isolating cropland dynamics.
- ⚠️ Requires **recalibration** when switching.

### Module 80 — Optimization: `nlp_apr17` vs `lp_nlp_apr17` vs `nlp_par`
- **`nlp_apr17`** (default): Direct NLP solve per region. Standard choice.
- **`lp_nlp_apr17`**: LP solve first as warmstart, then NLP. Can improve convergence for difficult scenarios.
- **`nlp_par`**: Parallel NLP across regions. Use on multi-core machines for speed.

## Compatibility Considerations

### Recalibration Required ⚠️
These modules require `cfg$recalibrate <- TRUE` when switching realizations:
- **29_cropland**: `detail_apr24` ↔ `simple_apr24`
- **30_croparea**: `simple_apr24` ↔ `detail_apr24`
- **31_past**: `endo_jun13` ↔ `static`
- **38_factor_costs**: any switch between the three realizations

### Cross-Module Dependencies
- **`38_factor_costs/sticky_labor`** → requires **`37_labor_prod/exo`** to have any effect (otherwise the labor productivity factor is just 1.0)
- **`13_tc/exo`** → requires a **prior completed run with `endo_jan22`** for input data
- **Timber demand ON** (`s73_timber_demand_switch = 1`) → requires `s32_hvarea = 2` AND `s35_hvarea = 2` (dynamic plantations). Conversely, timber OFF → use `s32_hvarea = 0|1` and `s35_hvarea = 0|1`
- **`70_livestock/fbask_jan16_sticky`** is sensitive to Module 12 (interest_rate) via its annuity formula

### GHG Module Group (on/off together)
Modules 51 (nitrogen), 53 (methane), 55 (awms), 58 (peatland) each have `off` realizations. When disabling GHG accounting for speed, turn them off as a group. The default has all ON except phosphorus (54, always off).

## Common Pitfalls

1. **Forgetting recalibration**: Switching realizations for modules 29, 30, 31, or 38 without `cfg$recalibrate <- TRUE` will produce poor results with mismatched calibration parameters.
2. **Using `tc/exo` without input**: The `exo` TC realization fails without the `f13_tau_scenario.csv` file from a prior `endo_jan22` run.
3. **Confusing realizations with switches**: Most behavioral variation in MAgPIE comes from switches (`s*`, `c*` parameters), not from swapping realizations. For example, Module 15 (food) has only one realization but 20+ switches controlling demand behavior.
4. **Assuming `off` means harmless**: Disabling nitrogen (51) or methane (53) removes emission costs from optimization, which can change land-use patterns by making otherwise costly conversions "free."
5. **Mismatched sticky realizations**: Using `sticky_labor` factor costs with `labor_prod/off` adds computational cost without benefit — the labor factor stays at 1.0.
6. **Orphaned directories**: `44_biodiversity/bii_target_apr24` and `59_som/cellpool_aug16` are data stubs, not functional realizations — they have no `realization.gms`.

## Module Cross-References

| Decision Area | See Module Docs |
|---------------|-----------------|
| Trade model choice | `modules/module_21.md` |
| Forestry configuration | `modules/module_32.md` |
| Livestock feed & costs | `modules/module_70.md` |
| Natural vegetation | `modules/module_35.md` |
| Food demand switches | `modules/module_15.md` |
| Factor cost approaches | `modules/module_38.md` |
| Core architecture | `core_docs/Core_Architecture.md` |
| All module details | `modules/module_XX.md` |

---

## Related Helpers & Docs

- **Modification impact** → `agent/helpers/modification_impact_analysis.md` (safety of switching)
- **Infeasibility risk** → `agent/helpers/debugging_infeasibility.md` (realization-specific issues)
- **Carbon policy** → `agent/helpers/scenario_carbon_pricing.md` (GHG module realization choices)

---

## Lessons Learned
<!-- APPEND-ONLY -->
- 2026-03-06: Module 70 (livestock) has two realizations: fbask_jan16 (default, flexible baskets) and fbask_jan16_sticky (investment-based capital). The sticky realization adds path-dependent costs with depreciation. When switching from fbask_jan16 to fbask_jan16_sticky, ensure Module 15 food demand settings are compatible — sticky assumes slower structural transitions. (source: deep validation of module 70)
