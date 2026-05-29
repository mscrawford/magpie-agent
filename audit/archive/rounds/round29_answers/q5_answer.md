# Q5: MAgPIE Infeasibility — Causes, Diagnosis, Fixes, and Slack Variables

---

## Overview

Model infeasibility means the NLP solver (Module 80, realization `nlp_apr17`, CONOPT by default) cannot simultaneously satisfy all constraints. MAgPIE is a constrained optimization problem — infeasibility occurs when the feasible region shrinks to nothing, usually because multiple binding constraints compete for the same resource (land, water) or demand requirements exceed supply capacity with no safety valve in place.

The first diagnostic question is always: **which timestep failed?** Check `p80_modelstat(t)` — the first timestep with value > 2 (and ≠ 7) is the failure point. Modelstat = 7 ("intermediate non-optimal") is NOT a crash — MAgPIE continues and results may still be usable.

---

## 1. Land Overcrowding — Module 10 (Land)

### Constraint
`q10_land_area(j)` — strict equality — `modules/10_land/landmatrix_dec18/equations.gms:13-15`:
```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```
Total land in every cluster cell must equal the prior-timestep total. This is a HARD equality — no slack, no tolerance. Land cannot be created.

### Mechanism of infeasibility
Each cluster has a fixed land budget. When lower bounds from conservation, restoration, urban expansion, and minimum cropland/pasture together exceed the cell's total area, the =e= constraint has no feasible point. This manifests most often as:

1. **Conservation + agriculture incompatible**: `pm_land_conservation(t,j,land,consv_type)` from Module 22 locks natural land as a lower bound in presolve (Modules 31, 35 use it via `.lo` assignments). If conservation reserves + minimum cropland/pasture needed to meet food demand > total cell area, the model is infeasible.

2. **Urban expansion absorbs too much land**: Module 34 sets `vm_land(j,"urban")` via `q34_urban_land(i)` which fixes regional urban totals to `i34_urban_area(ct,j)` (LUH3 data). Urban land cannot decrease. In SSP3 high-sprawl scenarios, this can crowd out production land.

3. **Afforestation + agriculture compete**: High carbon prices drive `v32_land(j,"aff",ac)` expansion (Module 32). If afforestation targets + cropland requirements + conservation exceed cell area, infeasibility follows.

4. **Transition restrictions bind**: `vm_lu_transitions.fx(j,"primforest","forestry") = 0` (modules/10_land/landmatrix_dec18/presolve.gms:13) and `vm_lu_transitions.fx(j,land_from,"primforest") = 0` (presolve.gms:20) mean primary forest can never increase or be converted to plantations. If these combine with locked conservation minimums and expansion demand, no reallocation path exists.

### Diagnosis
```r
land <- readGDX(gdx, "ov_land", select = list(type = "level"))
# Sum across land types per cluster — compare to prior timestep total
readGDX(gdx, "oq10_land_area", select = list(type = "marginal"))
# High marginals signal tight land balance
```

### Fix
- Relax `c22_protect_scenario` (config switch, not a scalar — common confusion). The dangerous combination is `c22_protect_scenario = "GSN_HalfEarth"` with high BII targets.
- Reduce `s32_aff_plantation` or reduce carbon price aggressiveness.
- Check `s22_conservation_start` — early start years with high targets are a known trigger.
- Allow more land flexibility via `c29_marginal_land = "all_marginal"` (Module 29) to expand cropland suitability area.

---

## 2. Water Unavailability — Module 43 (Water Availability)

### Constraint
`q43_water(j)` — inequality — `modules/43_water_availability/total_water_aug13/equations.gms:10-11`:
```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2));
```
Total water withdrawals ≤ total available renewable water per cell. Applied independently per cluster — no inter-cell water transfer is possible.

### Mechanism of infeasibility
The model has a **built-in infeasibility buffer** for exogenous (non-agricultural) demands: if manufacturing + electricity + domestic + ecosystem demands exceed surface water, Module 43 automatically activates `v43_watavail("ground",j)` groundwater at a 1% safety margin (`presolve.gms:14-16`). This prevents infeasibility for exogenous sectors.

**Agricultural demand is NOT buffered.** If `vm_watdem("agriculture",j)` from Module 42 (equation `q42_watdem`) exceeds renewable water even after the model shifts to rainfed, infeasibility can result. The main trigger is aggressive environmental flow policy (`c42_env_flow_policy = "on"` or `"mixed"`) combined with high `s42_watdem_nonagr_scenario` — this raises exogenous demands, leaving less renewable water for agriculture.

### Diagnosis
```r
readGDX(gdx, "oq43_water", select = list(type = "marginal"))
# Non-zero marginals → water-binding cells
readGDX(gdx, "ov43_watavail", select = list(type = "level"))
# Check if v43_watavail("ground",j) > 0 — buffer activation
```

### Fix
- Improve irrigation efficiency via `s42_irrig_eff_scenario` or `s42_irrigation_efficiency` (Module 42).
- Relax environmental flow policy: reduce `s42_efp_startyear` or switch `c42_env_flow_policy` to `"off"`.
- Reduce irrigation expansion (`s41_*` switches in Module 41 for Area Equipped for Irrigation).

---

## 3. Food Demand Unachievable — Modules 15/16/21 Food-Trade Closure

### Constraint
There is **no slack variable for food or standard crop production**. If food demand cannot be met with available land + trade, the model goes infeasible. The binding constraints are the food balance constraint (Module 16 demand supply-closure) and — critically — the non-tradeable constraint for non-tradeable commodities:

`q21_notrade(h,k_notrade)` — `modules/21_trade/selfsuff_reduced/equations.gms:18-19`:
```gams
q21_notrade(h2,k_notrade)..
  sum(supreg(h2,i2),vm_prod_reg(i2,k_notrade)) =g= sum(supreg(h2,i2), vm_supply(i2,k_notrade));
```
Non-tradeable commodities (pasture, fodder, residues, bioenergy crops) must be produced domestically within each super-region.

`q21_trade_reg(h,k_trade)` — `modules/21_trade/selfsuff_reduced/equations.gms:31-35` — enforces minimum self-sufficiency for tradeable commodities. The partial slack here is `v21_import_for_feasibility(h,k_notrade)` which **only covers wood and woodfuel** (NOT food).

### Mechanism of infeasibility
- SSP3 (high population) + `c21_trade_liberalization = "autarky"` removes trade flexibility entirely, so regions must self-supply everything — infeasibility risk is high.
- `c60_biodem_level = 1` (default regional bioenergy) with aggressive 2nd-gen demand: `q60_bioenergy_reg(i)` forces each region to produce its bioenergy target locally — if land is also needed for food, the system over-constrains.
- `s13_max_gdp_shr` (Module 13) caps the share of GDP allocated to agriculture; any finite value is a documented infeasibility trigger when food demand is high.

### Diagnosis
```r
# Check which regions have high food balance marginals
readGDX(gdx, "oq21_notrade", select = list(type = "marginal"))
readGDX(gdx, "oq21_trade_reg", select = list(type = "marginal"))
# Check if v21_import_for_feasibility activated
readGDX(gdx, "ov21_import_for_feasibility", select = list(type = "level"))
```

### Fix
- Use `c21_trade_liberalization = "regionalized"` (default) instead of `"autarky"` or `"fragmented"`.
- Reduce 2nd-gen bioenergy demand (`c60_2ndgen_biodem`) or use global rather than regional targeting (`c60_biodem_level = 0`).
- Keep `s13_max_gdp_shr = Inf` (default).

---

## 4. Carbon Policy Too Aggressive — Module 56 + Module 32/58

### Constraint
`s56_cprice_red_factor` (Module 56) amplifies carbon prices. Combined with:
- `q32_aff_pol(j)` — NPI/NDC forest targets that cannot be relaxed
- `q58_peatland_rewetting` — mandatory rewetting targets
- Land constraints from Module 10

High carbon prices force land-use changes (afforestation, peatland rewetting) that compete with food production.

### Specific module 58 infeasibility triggers (from Lessons Learned)
The following combinations are documented as **guaranteed infeasibility**:
- `s58_rewetting_switch = 0` + `s58_rewetting_exo = 1` — rewetting mandatory but upper bound = 0
- `s58_annual_rewetting_limit = 0` + any exo rewetting = 1 — impossible rate limit
- `s58_rewet_exo_target_value >= 1.0` with default rate (0.02/yr) — physically unreachable by 2050

### Specific module 57 infeasibility triggers (from Lessons Learned)
- `s57_implicit_emis_factor = 0` — guaranteed division-by-zero in `modules/57_maccs/on_aug22/equations.gms:40,50`
- `s57_maxmac_*` set to step 201 — causes 1/(1-mitigation) blowup when mitigation → 1.0 at `modules/57_maccs/on_aug22/equations.gms:38,48`

### Diagnosis
```r
# Check if model failed in years with policy phase-in
readGDX(gdx, "p80_modelstat")
# Check if rewetted area is growing unrealistically
readGDX(gdx, "ov58_peatland_rewetted", select = list(type = "level"))
```

### Fix
- Reduce `s56_cprice_red_factor` (keep ≤ 0.5 for early start years).
- Ensure `s58_rewetting_switch` is consistent with `s58_rewetting_exo`.
- Keep `s57_implicit_emis_factor` > 0 (small positive, e.g. 0.001 minimum).

---

## 5. Bioenergy Targets Impossible — Module 60

### Constraint
`q60_bioenergy_reg(i)` (default, `c60_biodem_level = 1`) — `modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:46-47`:
```gams
q60_bioenergy_reg(h2,k_trade)..
  sum(kbe60, v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
  sum(ct, i60_bioenergy_dem(ct,i2)) * c60_biodem_level
```
Each region MUST produce its own 2nd-gen bioenergy target. There is no slack variable. Non-tradeable bioenergy crops (begr, betr are in `k_notrade`) cannot be substituted by imports.

### Mechanism
High bioenergy demand scenario with `c60_biodem_level = 1` (regional) requires land for dedicated energy crops that may not be available after food + conservation requirements. The situation worsens in later timesteps as bioenergy demand scales.

### Fix
- Use a lower bioenergy demand scenario.
- Switch to global pooling (`c60_biodem_level = 0`) to allow comparative advantage allocation.
- Allow more cropland expansion (`c29_marginal_land`).

---

## Built-In Slack Variables (Safety Valves)

MAgPIE has **5 documented slack variables** with high penalty costs. Non-zero activation signals constraint strain — the model is "paying" to relax an otherwise-infeasible constraint.

| Slack Variable | Module | Equation | Penalty Cost | What It Relaxes |
|---|---|---|---|---|
| `v73_prod_heaven_timber(j,kwood)` | 73 | `q73_prod_wood`, `q73_prod_woodfuel` (`equations.gms:35-53`) | $1,000,000/tDM (`s73_free_prod_cost = 1e6`, `input.gms:17`) | Timber/woodfuel shortfall when forest supply insufficient |
| `v44_bii_missing(i,biome44)` | 44 | `q44_bii_target` (`equations.gms:22-23`) | $1,000,000/BII unit (`s44_cost_bii_missing = 1e6`) | BII target gap when biodiversity target unachievable |
| `v32_land_missing(j)` | 32 | `q32_cost_total` (`equations.gms:21-27`) | $1,000,000/ha (`s32_free_land_cost = 1e6`, `input.gms:32`) | Timber plantation land target gap |
| `v32_ndc_area_missing(j)` | 32 | `q32_aff_pol` (`equations.gms:74-75`) | $1,000,000/ha (same `s32_free_land_cost`) | NPI/NDC afforestation policy target gap |
| `v21_import_for_feasibility(h,k)` | 21 | `q21_trade_reg` (`equations.gms:31-35`) | $1,500/tDM (implicit in trade cost structure) | Superregional wood/woodfuel self-sufficiency shortfall — **NOTE: only covers wood and woodfuel, NOT food commodities** |

**Also documented as a feasibility-softening mechanism** (not a traditional decision variable slack, but functionally equivalent):
| `v29_fallow_missing(j)` | 29 | `q29_cost_cropland` (`equations.gms:26-32`) | `i29_fallow_penalty(t)` — a scenario-specific penalty | Fallow land target gap (soft penalty, not hard infeasibility prevention) |

### Critical gap
Food, feed, and standard crop production have **NO slack variables**. If food demand cannot be met — whether due to land exhaustion, trade restrictions, or water scarcity — the model goes infeasible with no safety valve. This is by design: food security is a non-negotiable hard constraint in MAgPIE.

---

## Step-by-Step Diagnostic Workflow

### Step 1: Identify failing timestep
```r
library(gdx2)
readGDX("fulldata.gdx", "p80_modelstat")
# First t with value > 2 (and != 7) is the failure point
```

### Step 2: Check active slack variables
```r
readGDX(gdx, "v73_prod_heaven_timber")   # Timber supply
readGDX(gdx, "v44_bii_missing")          # Biodiversity
readGDX(gdx, "v32_land_missing")         # Forestry land
readGDX(gdx, "v21_import_for_feasibility") # Wood trade
readGDX(gdx, "ov_land", select = list(type = "level")) # Land by type
```

### Step 3: Identify binding constraints via marginals
```r
readGDX(gdx, "oq10_land_area", select = list(type = "marginal"))  # Land
readGDX(gdx, "oq43_water", select = list(type = "marginal"))      # Water
readGDX(gdx, "oq21_notrade", select = list(type = "marginal"))    # Trade
```

### Step 4: Check configuration for known dangerous combinations

| Configuration | Risk |
|---|---|
| SSP3 + PkBudg650 | High population + tight carbon budget |
| `c22_protect_scenario = "GSN_HalfEarth"` + high BII | >50% land locked + biodiversity floor |
| `s13_max_gdp_shr` at any finite value | Agricultural GDP cap — documented infeasibility trigger |
| `c21_trade_liberalization = "autarky"` or `"fragmented"` | No trade flexibility for regional supply gaps |
| `s56_cprice_red_factor > 0.8` with early start | Aggressive carbon price + no CDR option |
| `c60_2ndgen_biodem` high + `c60_biodem_level = 1` | Regional bioenergy mandate + limited land |
| `s58_rewetting_switch = 0` + `s58_rewetting_exo = 1` | Guaranteed infeasibility |
| `s57_implicit_emis_factor = 0` | Guaranteed division-by-zero in MACC equations |

---

## Summary of What Is and Is Not Covered by Docs

**Well-covered by docs**: land balance mechanics, slack variable identities, dangerous switch combinations, water buffer mechanism, food-demand safety valve absence, Module 58 and 57 specific infeasibility traps, Module 60 bioenergy constraints.

**NOT fully covered by docs**: exact penalty values for `v32_ndc_area_missing` (implied to be `s32_free_land_cost = 1e6` from `q32_cost_total` structure but not stated explicitly as a separate entry in the helper); exact list of which food balance equations in Module 16 are the binding closure equations (docs focus on the trade side).

---

## Sources Used

- Primary: `agent/helpers/debugging_infeasibility.md` (Lessons Learned including Modules 57, 58 traps)
- `cross_module/land_balance_conservation.md` (q10_land_area, transition restrictions, presolve.gms line citations)
- `cross_module/water_balance_conservation.md` (q43_water, infeasibility buffer mechanism)
- `modules/module_21.md` (q21_notrade, q21_trade_reg, v21_import_for_feasibility — wood only)
- `modules/module_32.md` (v32_land_missing, v32_ndc_area_missing, s32_free_land_cost, q32_cost_total)
- `modules/module_44.md` (v44_bii_missing, s44_cost_bii_missing, q44_bii_target)
- `modules/module_60.md` (q60_bioenergy_reg, c60_biodem_level)
- `modules/module_73.md` (v73_prod_heaven_timber, s73_free_prod_cost)
- `modules/module_29.md` (v29_fallow_missing, i29_fallow_penalty, q29_cost_cropland)
- `modules/module_56.md` (s56_cprice_red_factor, GHG policy switches)
- `modules/module_58.md` (peatland rewetting infeasibility combinations)

🟡 Based on module documentation (verified in code at last sync — see `project/sync_log.json` for current staleness). Line numbers cited from docs; may drift between syncs. For critical modifications, verify against current GAMS source.
