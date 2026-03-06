# MAgPIE Infeasibility Debugging Guide

> **Purpose**: Comprehensive reference for diagnosing and resolving MAgPIE model infeasibilities.
> All claims verified against source code. File:line references provided throughout.

---

## Table of Contents

1. [How Infeasibility Is Detected](#1-how-infeasibility-is-detected)
2. [The Infeasibility Handling Pipeline](#2-the-infeasibility-handling-pipeline)
3. [Constraint Risk Ranking](#3-constraint-risk-ranking)
4. [Slack Variables — Built-In Safety Valves](#4-slack-variables--built-in-safety-valves)
5. [Configuration Switches That Affect Feasibility](#5-configuration-switches-that-affect-feasibility)
6. [Dangerous Cross-Module Combinations](#6-dangerous-cross-module-combinations)
7. [Diagnostic Approaches](#7-diagnostic-approaches)
8. [Step-by-Step Debugging Workflow](#8-step-by-step-debugging-workflow)
9. [Quick Reference Tables](#9-quick-reference-tables)

---

## 1. How Infeasibility Is Detected

MAgPIE uses GAMS `modelstat` codes to detect infeasibility. Three optimization realizations exist in `modules/80_optimization/`:

| Realization | Strategy | Default? |
|---|---|---|
| `nlp_apr17` | Direct NLP with solver-cycling retry | Yes (typical) |
| `lp_nlp_apr17` | Linear pre-solve → NLP solve | Alternative |
| `nlp_par` | Parallel NLP per super-region | For large runs |

### 1.1 GAMS Modelstat Codes

| Code | Meaning | MAgPIE Response |
|---|---|---|
| 1 | Optimal | ✅ Accept, save GDX |
| 2 | Locally optimal | ✅ Accept, save GDX |
| 3–6 | Infeasible / unbounded | ❌ Retry loop, then abort |
| 7 | Intermediate infeasible | ⚠️ **Tolerated** — no abort |
| 13 | Error / no solution | ❌ Retry loop, then abort |
| NA | Not available | Forced to 13, then retry |

### 1.2 The Abort Sequence

When retries are exhausted and `modelstat > 2` (and ≠ 7), MAgPIE runs:

```
modules/80_optimization/nlp_apr17/solve.gms:103-106
  1. gmszip scratch directory → magpie_problem_YYYY.zip
  2. Execute_Unload "fulldata.gdx"              ← line 105
  3. abort "no feasible solution found!"         ← line 106
```

Key: `modelstat = 7` is **exempted** from aborting. The model continues with a suboptimal solution.

### 1.3 Key Status Parameters

| Parameter | Dimensions | Purpose |
|---|---|---|
| `p80_modelstat(t)` | Per timestep | Records GAMS modelstat; `(t,h)` in `nlp_par` |
| `p80_num_nonopt(t)` | Per timestep | Count of non-optimal variables (stored, never checked) |

---

## 2. The Infeasibility Handling Pipeline

### 2.1 `nlp_apr17` Realization (file: `modules/80_optimization/nlp_apr17/solve.gms`)

```
Step 1: Pre-flight check (line 29-31)
  └─ if execerror > 0 → abort "Execution error"

Step 2: Initial NLP solve (line 34)
  └─ solve magpie USING nlp MINIMIZING vm_cost_glo

Step 3: NA handling (line 44)
  └─ magpie.modelStat$(magpie.modelStat=NA) = 13

Step 4: Retry loop — up to s80_maxiter=30 iterations (lines 47-91)
  Cycles through 4 solver configurations:
  ┌─────────────────────────────────────────────────────┐
  │ Option 1: CONOPT4, default settings (optfile=0)     │
  │ Option 2: CONOPT4, custom optfile (optfile=1)       │
  │ Option 3: CONOPT4, Lim_Variable=1e25 (optfile=2)   │
  │ Option 4: CONOPT3, fallback solver                  │
  │ → wrap back to Option 1                             │
  └─────────────────────────────────────────────────────┘

Step 5: Penultimate retry → enable solprint (lines 79-81)
  └─ magpie.solprint = 1 → full solution listing in .lst file

Step 6: Status recording (lines 95-96)
  └─ p80_modelstat(t) = magpie.modelstat

Step 7: Success → save GDX (lines 98-100)
  └─ mv magpie_p.gdx magpie_YYYY.gdx

Step 8: Failure → dump + abort (lines 102-107)
  └─ zip scratch dir, Execute_Unload fulldata.gdx, abort
```

### 2.2 `lp_nlp_apr17` Realization (file: `modules/80_optimization/lp_nlp_apr17/solve.gms`)

Two-stage approach with additional diagnostics:

```
Stage A: Linear Pre-Solve
  A1: Linearize model via $batinclude nl_fix (line 55)
      └─ Fixes nonlinear variables to current .l values
  A2: Solve linearized model (line 65)
  A3: If LP optimal → secondary landdiff minimization (lines 74-78)
  A4: If modelstat=2 → abort "Unfixed nonlinear terms" (line 92)
      └─ Means some module's nl_fix.gms is missing
  A5: Release nonlinear variables via nl_release (line 104)
  A6: If LP failed → nl_relax widens bounds (line 113)
      └─ e.g., v13_tau_core.l += 0.1

Stage B: Full NLP Solve (line 130)
  B1: Optional CONOPT3 fallback
  B2: Modelstat 13 recovery (two attempts)

Stage C: Outer retry loop (line 179)
  └─ Repeats LP→NLP if still infeasible

Stage D: Final abort (line 210)
  └─ Execute_Unload "fulldata.gdx"; abort
```

### 2.3 `nlp_par` Realization (file: `modules/80_optimization/nlp_par/solve.gms`)

Solves per super-region (`h`) in parallel:

- `p80_modelstat(t,h)` — **per-region** status tracking
- Problem zips named `magpie_problem_H_YYYY.zip` (per region)
- Final abort checks `smax(h, p80_modelstat(t,h)) > 2` (worst-case across regions)
- **Silently clears** execution errors during retries (line 118: `execerror = 0`)

### 2.4 Food Demand Model (Module 15 — Separate NLP)

The food demand model `m15_food_demand` has its own infeasibility handling:

```
modules/15_food/anthro_iso_jun22/presolve.gms:248-264
  → Initial solve, CONOPT3 fallback, abort on failure

modules/15_food/anthro_iso_jun22/intersolve.gms:54-69
  → Iterative solve, CONOPT3 fallback
  → abort "Food Demand Model became infeasible. Should not be possible."
```

---

## 3. Constraint Risk Ranking

### 🔴 CRITICAL — No Slack Variables (Top Infeasibility Sources)

#### Rank 1: `q10_land_area` — Total Land Conservation
```gams
# modules/10_land/landmatrix_dec18/equations.gms:13-15
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```
**Why critical**: Strict equality — total land per cluster is **constant**. ALL other modules set lower bounds on individual land types. Infeasibility occurs when:
```
Σ vm_land.lo(j, all_land_types) > Σ pcm_land(j, all_land_types)
```
**No slack variable. No escape.**

#### Rank 2: `q43_water` — Water Balance
```gams
# modules/43_water_availability/total_water_aug13/equations.gms:10-11
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2));
```
**Why critical**: Hard physical cap. No inter-cluster water transfer. Only 1 of 5 demand sectors is endogenous (agriculture). Default: 50% of water reserved for manufacturing (`s42_reserved_fraction = 0.5`).
**Partial safety valve**: Presolve hack inflates groundwater for exogenous demand exceedance (`modules/43_water_availability/total_water_aug13/presolve.gms:14-16`), but does NOT protect against combined agricultural+exogenous overuse.

#### Rank 3: `q60_bioenergy_reg` — Regional Bioenergy Demand
```gams
# modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:46-47
q60_bioenergy_reg(i2) ..
  sum(kbe60, v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
  sum(ct, i60_bioenergy_dem(ct,i2)) * c60_biodem_level;
```
**Why critical**: Hard demand floor, **active by default** (`c60_biodem_level = 1`). Every region MUST produce its bioenergy — no inter-regional trade. Minimum floor of 1 mio. GJ/yr per region (`presolve.gms:62`).

#### Rank 4: `q21_notrade` — Non-Tradable Commodities Autarky
```gams
# modules/21_trade/selfsuff_reduced/equations.gms:18-19
q21_notrade(h2,k_notrade) ..
  sum(supreg(h2,i2), vm_prod_reg(i2,k_notrade)) =g=
  sum(supreg(h2,i2), vm_supply(i2,k_notrade));
```
**Why critical**: Non-tradable commodities (foddr, pasture, oilpalm, begr, betr, res_*) must be produced locally within each superregion. **No slack.**

#### Rank 5: `q35_natveg_conservation` — Natural Vegetation Floor
```gams
# modules/35_natveg/pot_forest_may24/equations.gms:19-22
q35_natveg_conservation(j2) ..
  sum(land_natveg, vm_land(j2,land_natveg)) =g=
  sum((ct,land_natveg), pm_land_conservation(ct,j2,land_natveg,"protect"));
```
**Why critical**: Enforces total natural vegetation ≥ protection target. **No slack.** Conservation targets propagate from module 22.

#### Rank 6: `q21_trade_reg` — Self-Sufficiency Band
```gams
# modules/21_trade/selfsuff_reduced/equations.gms:31-35
q21_trade_reg(h2,k_trade) ..
  sum(supreg(h2,i2), vm_prod_reg(i2,k_trade)) =g=
  m21_baseline_production(...) * sum(ct, i21_trade_bal_reduction(ct,k_trade))
  - v21_import_for_feasibility(h2,k_trade);
```
**Note**: `v21_import_for_feasibility` exists BUT is **fixed to 0 for ALL commodities except wood and woodfuel** (`preloop.gms:36-38`). For food crops and livestock: effectively **no slack**.

### 🟡 MODERATE — Have Slacks or Are Conditional

#### `q32_establishment_hvarea` — Replanting ≥ Harvest (Module 32)
```gams
# modules/32_forestry/dynamic_may24/equations.gms:204-208
```
Active when `s32_hvarea = 2` (default). **No slack.** But conditional on establishment dynamics switch.

#### `q35_secdforest_restoration` — Mandatory Restoration (Module 35)
```gams
# modules/35_natveg/pot_forest_may24/equations.gms:24-28
```
Requires agricultural/forestry land → secondary forest. **No slack.**

#### `q35_min_forest` — NPI/NDC Forest Minimum (Module 35)
```gams
# modules/35_natveg/pot_forest_may24/equations.gms:75-77
```

#### `q32_aff_pol` — NDC Afforestation Target (Module 32)
```gams
# modules/32_forestry/dynamic_may24/equations.gms:74-75
```
**Has slack**: `v32_ndc_area_missing(j)` at $1,000,000/ha.

#### `q44_bii_target` — Biodiversity Target (Module 44)
```gams
# modules/44_biodiversity/bii_target/equations.gms:22-23
```
**Has slack**: `v44_bii_missing(i,biome44)` at $1,000,000/unit. **OFF by default** (`s44_bii_target = 0`).

### 🟢 LOW RISK — Cannot Directly Cause Infeasibility

**Module 56 (GHG Policy)**: All 7 equations are `=e=` equalities with no inequalities or slack variables. Drives infeasibility **indirectly** through high carbon prices that make deforestation/land-conversion prohibitively expensive.

---

## 4. Slack Variables — Built-In Safety Valves

### Complete Inventory

| Variable | Module | Penalty (USD/unit) | Relaxes | Default Active? |
|---|---|---|---|---|
| `v73_prod_heaven_timber(j,kforestry)` | 73 | 1,000,000/tDM | Timber production (last resort) | Yes |
| `v44_bii_missing(i,biome44)` | 44 | 1,000,000/unit | BII target | No (`s44_bii_target=0`) |
| `v32_land_missing(j)` | 32 | 1,000,000/ha | Plantation establishment demand | Yes |
| `v32_ndc_area_missing(j)` | 32 | 1,000,000/ha | NDC afforestation target | Yes |
| `v58_balance(j,manPeat58)` | 58 | 1,000,000 | Peatland scaling (expansion) | Yes (post-2020) |
| `v58_balance2(j,manPeat58)` | 58 | 1,000,000 | Peatland scaling (reduction) | Yes (post-2020) |
| `v29_treecover_missing(j)` | 29 | 6,150/ha | Cropland treecover target | Conditional |
| `v30_betr_missing(j)` | 30 | 2,460/ha | Bioenergy tree area target | No (`s30_betr_target=0`) |
| `v21_import_for_feasibility(h,k_trade)` | 21 | 1,500/tDM | Self-sufficiency (**wood/woodfuel ONLY**) | Yes (for k_import21) |
| `v29_fallow_missing(j)` | 29 | 615/ha | Fallow land minimum share | Conditional |
| `v30_penalty(j,rota30)` | 30 | 123–615/ha | Crop rotation violations | No (default: rule-based) |
| `v30_penalty_max_irrig(j,rotamax30)` | 30 | 123–615/ha | Irrigated crop rotation max | Always |
| `v71_additional_mon(j)` | 71 | 15,000/tDM | Monogastric spatial limits | Yes |

### Cost Flow to Objective

All penalties reach `vm_cost_glo` (minimized) through `q11_cost_reg`:
```
vm_cost_glo
 └── q11_cost_reg → sum of regional costs:
       ├── vm_cost_fore(i2)           ← v32_land_missing, v32_ndc_area_missing
       ├── vm_rotation_penalty(i2)    ← v30_penalty, v30_betr_missing
       ├── vm_cost_cropland(j2)       ← v29_fallow_missing, v29_treecover_missing
       ├── vm_cost_bv_loss(j2)        ← v44_bii_missing
       ├── vm_peatland_cost(j2)       ← v58_balance, v58_balance2
       ├── v21_cost_trade_reg(h2,k)   ← v21_import_for_feasibility
       └── vm_cost_timber(i2)         ← v73_prod_heaven_timber
```

### Diagnostic Value of Slack Variables

**If a slack variable has a nonzero `.l` value in `fulldata.gdx`, it means the corresponding constraint was binding.** This is one of the most valuable diagnostic signals:

```r
# In R, after loading fulldata.gdx:
library(gdx)
readGDX("fulldata.gdx", "ov32_land_missing", field = "level")  # If nonzero → timber land insufficient
readGDX("fulldata.gdx", "ov44_bii_missing", field = "level")   # If nonzero → BII target too ambitious
readGDX("fulldata.gdx", "ov21_import_for_feasibility", field = "level")  # If nonzero → trade limits binding
```

---

## 5. Configuration Switches That Affect Feasibility

### 🔴 TIER 1: High Infeasibility Risk

| Switch | Module | Default | Dangerous Value | Why |
|---|---|---|---|---|
| `s13_max_gdp_shr` | 13_tc | `Inf` | Any finite value (e.g., 0.002) | Caps tech investment → blocks intensification. **Documented as infeasibility causer** in `config/default.cfg:302` |
| `s30_annual_max_growth` | 30_croparea | `Inf` | Any small finite value | Hard `.up()` bound on regional cropland growth rate |
| `c22_protect_scenario` | 22_conservation | `"none"` | `"GSN_HalfEarth"`, `"PBL_HalfEarth"` | Protects ~50% of land → lower bounds exceed cluster area |
| `c50_scen_neff` | 50_nr_soil | varies | Aggressive targets (e.g., `max75`) | NUE is hard-fixed via `vm_nr_eff.fx()` → N balance unsatisfiable |
| `s44_bii_target` | 44_biodiversity | `0` (OFF) | ≥ 0.78 | Forces massive land-use change. `config/default.cfg:1414` warns values ~0.7 already cause "very strong land-use changes" |
| `s56_cprice_red_factor` | 56_ghg_policy | `1` | Negative values | Emissions rewarded → objective unbounded |
| `s56_fader_start > s56_fader_end` | 56_ghg_policy | `2030`/`2050` | Inverted → negative fader | Negative GHG prices → unbounded |

### Division-by-Zero Traps

| Parameter | Module | Default | Danger Condition |
|---|---|---|---|
| `s38_ces_elast_subst` | 38 | `0.3` | `= 0` → div/0 in CES exponent |
| `s22_conservation_start = s22_conservation_target` | 22 | `2025`/`2050` | Equal → div/0 in sigmoid fader |
| `s44_start_year = s44_target_year` | 44 | `2030`/`2100` | Equal → div/0 in interpolation |
| `s38_targetyear_labor_share = startyear` | 38 | `2050`/`2025` | Equal → div/0 in fader |

### 🟠 TIER 2: Moderate-High Risk

| Switch | Module | Default | Dangerous Value | Why |
|---|---|---|---|---|
| `c21_trade_liberalization` | 21_trade | `"l909090r808080"` | SSP3: `"l909595r809090"` | Near-autarky for food. `config/default.cfg:1613` notes PkBudg650 is "not feasible for SSP3" |
| `s32_max_aff_area` + `s32_aff_prot=1` | 32_forestry | `Inf` / `1` | Low area + `aff_prot=1` | Permanently fixes ALL afforestation. If target < existing → infeasible |
| `c60_2ndgen_biodem` + `c60_biodem_level` | 60_bioenergy | varies / `1` | `"PkBudg650"` + `1` | Stringent per-region bioenergy demand, no trade, hard `=g=` |
| `s35_natveg_harvest_shr` | 35_natveg | `1` | Near `0` | Locks nearly all forest as `vm_land.lo() = (1-shr) × current_area` |
| `s15_elastic_demand` | 15_food | `0` (OFF) | `1` (ON) | Enables iterative NLP with price-demand feedback; oscillation risk |
| `s12_interest_lic` | 12_interest | `0.1` | `> 0.3` | Cascades through 8+ modules via `(1+r)^15` compounding |

### 🟡 TIER 3: Moderate Risk (Specific Combinations)

| Switch | Module | Default | Dangerous When |
|---|---|---|---|
| `c30_rotation_rules` + `s30_implementation=1` | 30 | `"default"` / `1` | `"agroecology"` caps crops at 30% + 18% min legumes |
| `s39_cost_establish_crop` | 39 | `12,300` | Very high → blocks cropland expansion |
| `c42_env_flow_policy` + `s42_env_flow_fraction` | 42/43 | `"off"` / `0.2` | `"on"` + `0.5` → locks 50% of water for environment |
| `s14_degradation` | 14_yields | `0` (OFF) | `1` → 8% yield reduction stresses land |
| `c44_bii_decrease` | 44 | `1` (allow decrease) | `0` → monotonic ratchet, constraints tighten cumulatively |
| `s73_expansion` + `c73_wood_scen` | 73 | `0` / `"default"` | `> 2` + `"construction"` → ~9× timber demand |

---

## 6. Dangerous Cross-Module Combinations

### Combination 1: "Land Crunch" (Most Common Infeasibility)
```
c22_protect_scenario = "GSN_HalfEarth"     ← locks 50% of land
+ s44_bii_target = 0.78                    ← forces massive pasture→natveg
+ c44_bii_decrease = 0                     ← monotonic ratchet
+ c35_ad_policy = "ndc"                    ← ambitious forest floors
+ s22_conservation_target = 2030           ← rapid phase-in
→ Σ vm_land.lo() across all types exceeds cluster area → q10_land_area INFEASIBLE
```

### Combination 2: "Can't Grow, Can't Intensify"
```
s30_annual_max_growth = 0.01               ← blocks cropland expansion
+ s13_max_gdp_shr = 0.002                 ← blocks intensification
+ c21_trade_liberalization = "l909595..."  ← blocks imports
→ No pathway to meet food demand
```

### Combination 3: "SSP3 + Ambitious Climate" (Documented Infeasibility)
```
c21_trade_liberalization = "l909595r809090"  ← near-autarky
+ c60_2ndgen_biodem = "PkBudg650"            ← massive bioenergy demand
+ c60_biodem_level = 1                        ← per-region enforcement
+ high CO2 prices
→ DOCUMENTED as "not feasible for SSP3" in config/default.cfg:1613
```

### Combination 4: "Interest Rate Cascade"
```
s12_interest_lic = 0.3
→ Inflates costs simultaneously across modules 13 (TC), 32 (forestry),
   38 (factor), 39 (land conversion), 41 (irrigation), 56 (GHG),
   58 (peatland), 70 (livestock)
→ All investment prohibitively expensive → implicit infeasibility
```

### Combination 5: "Nitrogen Lockdown"
```
c50_scen_neff = "baseeff_add3_add5_add10_max75"  ← aggressive NUE cap
+ s14_degradation = 1                              ← yield loss
+ tight land constraints (any combination above)
→ N balance =g= constraint unsatisfiable
```

---

## 7. Diagnostic Approaches

### 7.1 Files Generated on Failure

| File | Generator | Content |
|---|---|---|
| `fulldata.gdx` | `modules/80_optimization/*/solve.gms` and `core/calculations.gms:92` | Complete model state (all variables, parameters, equations) |
| `magpie_problem_YYYY.zip` | `nlp_apr17/solve.gms:103` | GAMS scratch directory archive |
| `magpie_problem_H_YYYY.zip` | `nlp_par/solve.gms:71` | Per-region scratch directory |
| `magpie_YYYY.gdx` | `*/solve.gms` (on success) | Per-timestep savepoint |
| `.lst` file | GAMS (with `solprint=1` on penultimate retry) | Full equation/variable listing |

### 7.2 Post-Processing Scripts

| Script | Purpose |
|---|---|
| `scripts/run_submit/submit.R:45-84` | Reads `p80_modelstat`, sets exit code, saves `runstatistics.rda` |
| `scripts/output/extra/modelstat.R` | Compare modelstat across multiple runs |
| `scripts/output/extra/out_of_bounds_check.R` | Read ALL `ov*` variables, check level vs. bounds |
| `scripts/output/output_check.R` | Calls `magpie4::outputCheck(gdx)` |
| `scripts/output/extra/resubmit.R` | Auto-resubmit runs with `modelstat > 2` |
| `scripts/performance_test.R` | Classifies: optimal / non-optimal / infeasible / compilation error |
| `scripts/calibration/calc_calib.R:85` | `stop("Calibration run infeasible")` if modelstat ∉ {1,2,7} |

### 7.3 Reading fulldata.gdx for Diagnostics

```r
library(gdx)

# 1. Check model status per timestep
readGDX("fulldata.gdx", "p80_modelstat")

# 2. Check slack variables (nonzero = constraint was binding)
readGDX("fulldata.gdx", "ov32_land_missing", field = "level")
readGDX("fulldata.gdx", "ov44_bii_missing", field = "level")
readGDX("fulldata.gdx", "ov21_import_for_feasibility", field = "level")
readGDX("fulldata.gdx", "ov73_prod_heaven_timber", field = "level")
readGDX("fulldata.gdx", "ov29_fallow_missing", field = "level")
readGDX("fulldata.gdx", "ov29_treecover_missing", field = "level")
readGDX("fulldata.gdx", "ov58_balance", field = "level")
readGDX("fulldata.gdx", "ov30_penalty", field = "level")
readGDX("fulldata.gdx", "ov71_additional_mon", field = "level")

# 3. Check land balance — are lower bounds exceeding total?
land <- readGDX("fulldata.gdx", "ov_land", field = "lower")
land_total <- readGDX("fulldata.gdx", "pcm_land")
# Compare: sum of lower bounds vs. total available per cluster

# 4. Check which timestep failed
readGDX("fulldata.gdx", "p80_modelstat")  # Look for values > 2

# 5. Check equation marginals (shadow prices)
# High marginals indicate binding constraints
readGDX("fulldata.gdx", "oq10_land_area", field = "marginal")
readGDX("fulldata.gdx", "oq43_water", field = "marginal")
readGDX("fulldata.gdx", "oq60_bioenergy_reg", field = "marginal")
```

### 7.4 The Presolve Lower-Bound Check

The most direct infeasibility test — check if lower bounds sum exceeds available land:

```r
library(gdx)

# For each cluster j, check:
#   Σ vm_land.lo(j, all_land_types)  vs.  Σ pcm_land(j, all_land_types)
land_lo <- readGDX("fulldata.gdx", "ov_land", field = "lower")
land_current <- readGDX("fulldata.gdx", "pcm_land")

# Aggregate by cluster
lo_sum <- aggregate(value ~ j, data = land_lo, FUN = sum)
current_sum <- aggregate(value ~ j, data = land_current, FUN = sum)

# Find clusters where lower bounds exceed available
merged <- merge(lo_sum, current_sum, by = "j")
infeasible_clusters <- merged[merged$value.x > merged$value.y, ]
print(infeasible_clusters)
```

### 7.5 The `m_boundfix` Macro

`core/macros.gms:14`:
```gams
$macro m_boundfix(x,arg,sufx,sens) x.fx arg$(x.up arg - x.lo arg < sens) = x.sufx arg;
```
Fixes variables when `upper - lower < 1e-6`. Used in presolve files of modules 10, 29, 32, 35. When bounds become nearly equal, this prevents numerical issues but can propagate infeasibility.

---

## 8. Step-by-Step Debugging Workflow

### When You See: `"no feasible solution found!"`

#### Step 1: Identify the Failing Timestep
```r
p80 <- readGDX("fulldata.gdx", "p80_modelstat")
print(p80)  # Find which timestep(s) have modelstat > 2
```
- If **first timestep** fails: likely a calibration or input data issue
- If fails at **specific year (e.g., 2050)**: likely scenario constraint conflicts
- If fails **increasingly later**: accumulating constraint pressure

#### Step 2: Check the Scratch Directory
Look for `magpie_problem_YYYY.zip` (or `magpie_problem_H_YYYY.zip` for `nlp_par`).
Unzip and examine solver logs for constraint violation details.

#### Step 3: Check Slack Variables
```r
# Any nonzero slack = that constraint was under pressure
# Even if the model ultimately solved, slacks warn of future infeasibility
```

#### Step 4: Run the Land Balance Check
```r
# See Section 7.4 above
# Identify which clusters have lower bounds > available land
```

#### Step 5: Trace Back to Configuration
Use the tables in Section 5 to identify which switches are most likely causing the constraint pressure. Common fixes:

| Symptom | Likely Cause | Fix |
|---|---|---|
| Land balance infeasible | Conservation too aggressive | Relax `c22_protect_scenario`, increase `s22_conservation_target` year |
| Water constraint binding | Irrigation demands too high | Enable `s42_pumping = 1`, reduce `s42_env_flow_fraction` |
| Bioenergy can't be met | Regional demand too high | Reduce `c60_biodem_level`, use less ambitious `c60_2ndgen_biodem` |
| Self-sufficiency impossible | Trade too restrictive | Use more liberal `c21_trade_liberalization` |
| Forest can't expand enough | Afforestation targets vs. land | Reduce `s32_max_aff_area`, relax NPI/NDC targets |
| BII target too ambitious | Biodiversity ratchet | Reduce `s44_bii_target`, set `c44_bii_decrease = 1` |
| Tech can't intensify | TC cap active | Remove `s13_max_gdp_shr` cap (set to `Inf`) |
| Crop area can't grow | Growth cap active | Increase `s30_annual_max_growth` |

#### Step 6: Check for Known Infeasible Combinations
- SSP3 + PkBudg650 = documented infeasible (`config/default.cfg:1613`)
- `s13_max_gdp_shr = 0.002` = documented infeasibility causer (`config/default.cfg:302`)

#### Step 7: Progressive Relaxation
If unclear which constraint is binding, progressively relax:
1. First relax conservation (`c22_protect_scenario = "none"`)
2. Then relax trade (`c21_trade_liberalization` to most liberal setting)
3. Then relax bioenergy (`c60_biodem_level = 0`)
4. Then relax NPI/NDC (`c35_ad_policy = "none"`, `c32_aff_policy = "none"`)
5. Then relax biodiversity (`s44_bii_target = 0`)

The first relaxation that makes the model feasible identifies the binding constraint group.

### When You See: `"Food Demand Model became infeasible"`
- Check `modules/15_food/anthro_iso_jun22/intersolve.gms:69`
- This typically means extreme price signals from the main model
- Check if `s15_elastic_demand = 1` — try setting to `0` for exogenous demand

### When You See: `"Unfixed nonlinear terms in linear solve!"`
- Only in `lp_nlp_apr17` realization (`solve.gms:92`)
- Means a module's `nl_fix.gms` file is missing or incomplete
- Check which module was recently added/modified

### When You See: `"Execution error"`
- Only in `nlp_apr17` realization (`solve.gms:30`)
- Pre-solve GAMS error (bad data, domain violations, etc.)
- Check `.lst` file for the specific GAMS error

---

## 9. Quick Reference Tables

### 9.1 All Abort Points in MAgPIE

| File | Line | Message | Trigger |
|---|---|---|---|
| `80_optimization/nlp_apr17/solve.gms` | 30 | `"Execution error..."` | `execerror > 0` |
| `80_optimization/nlp_apr17/solve.gms` | 106 | `"no feasible solution found!"` | modelstat > 2, ≠ 7 |
| `80_optimization/lp_nlp_apr17/solve.gms` | 92 | `"Unfixed nonlinear terms..."` | modelstat = 2 in LP phase |
| `80_optimization/lp_nlp_apr17/solve.gms` | 210 | `"no feasible solution found!"` | modelstat > 2, ≠ 7 |
| `80_optimization/nlp_par/solve.gms` | 139 | `"No feasible solution found!"` | max(modelstat) > 2, ≠ 7 |
| `15_food/anthro_iso_jun22/presolve.gms` | 264 | `"Food Demand Model infeasible during init"` | food modelstat > 2, ≠ 7 |
| `15_food/anthro_iso_jun22/intersolve.gms` | 69 | `"Food Demand Model became infeasible"` | food modelstat > 2, ≠ 7 |
| `13_tc/exo/presolve.gms` | 43 | `"tau value of 0 detected"` | Zero technology coefficient |
| `38_factor_costs/per_ton_fao_may22/presolve.gms` | 9 | `"cannot handle labor prod ≠ 1"` | Configuration mismatch |
| `44_biodiversity/bii_target/preloop.gms` | 20 | `"Start year for BII target..."` | Invalid scenario config |

### 9.2 Optimization Input Parameters

| Parameter | Default | File |
|---|---|---|
| `s80_maxiter` | `30` | `modules/80_optimization/*/input.gms:9` |
| `s80_optfile` | `1` | `modules/80_optimization/*/input.gms:10` |
| `s80_secondsolve` | `0` (OFF) | `modules/80_optimization/*/input.gms:11` |
| `s80_toloptimal` | `1e-08` | `modules/80_optimization/*/input.gms:12` |

### 9.3 Constraint → Module → Fix Lookup

| Constraint | Module | What Sets It | How to Relax |
|---|---|---|---|
| `q10_land_area` | 10_land | Fundamental | Cannot relax — reduce lower bounds from other modules |
| `q43_water` | 43_water | Input data, `s42_*` | Enable pumping (`s42_pumping=1`), reduce reserved fraction |
| `q60_bioenergy_reg` | 60_bioenergy | `c60_*` switches | Reduce `c60_biodem_level`, change `c60_2ndgen_biodem` |
| `q21_notrade` | 21_trade | Trade realization | Switch to `free_apr16` realization (no self-sufficiency) |
| `q21_trade_reg` | 21_trade | `c21_trade_liberalization` | Use more liberal trade scenario |
| `q35_natveg_conservation` | 35_natveg | `pm_land_conservation` from mod 22 | Relax `c22_protect_scenario` |
| `q35_min_forest` | 35_natveg | `c35_ad_policy` | Set to `"none"` |
| `q32_aff_pol` | 32_forestry | `c32_aff_policy` | Set to `"none"`, has slack `v32_ndc_area_missing` |
| `q44_bii_target` | 44_biodiversity | `s44_bii_target` | Set to `0`, has slack `v44_bii_missing` |

### 9.4 The Classic Infeasibility Cascade

```
Scenario demands: food + bioenergy + conservation + NDC afforestation
    ↓
q60_bioenergy_reg → needs cropland for bioenergy crops
q21_notrade       → needs local pasture + fodder
q35_natveg_conservation → locks natveg area (primforest + secdforest + other)
q32_aff_pol       → locks NDC afforestation area
Module 34         → fixes urban area
    ↓
All lower bounds exceed total available land in some cluster j
    ↓
q10_land_area(j): Σ vm_land.lo(j, land) > Σ pcm_land(j, land)
    ↓
INFEASIBLE — no slack variable anywhere in the chain
```

### 9.5 Defense Layers Summary

```
Layer 1: PREVENTION (presolve bounds)
  ├── m_boundfix macro — fixes variables when bounds nearly clash
  ├── Conservation caps — pm_land_conservation ≤ current area
  ├── Water hack — expand groundwater when demand > supply
  └── Bioenergy selective release — prevents demand for non-existent crops

Layer 2: ELASTIC CONSTRAINTS (13 slack variables)
  ├── High-penalty positive variables in constraint equations
  ├── Cost $123–$1,000,000/unit → zero in feasible solutions
  ├── Nonzero values = diagnostic signal of binding constraint
  └── Two-tier timber safety net (trade imports → heaven production)

Layer 3: SOLVER RETRY (module 80)
  ├── Up to 30 iterations cycling 4 solver configurations
  ├── CONOPT4 (default → optfile → relaxed limits) → CONOPT3
  ├── solprint=1 on penultimate retry → full listing in .lst
  └── Modelstat 7 (feasible but not optimal) tolerated

Layer 4: FAILURE HANDLING (abort + diagnostics)
  ├── fulldata.gdx dump — complete model state
  ├── magpie_problem_YYYY.zip — GAMS scratch directory archive
  ├── abort with message
  └── R post-processing: exit code, runstatistics, resubmit option
```

---

*Last updated: Generated from MAgPIE source code analysis. All file:line references verified against codebase.*
