# Helper: Debugging Model Infeasibility

**Auto-load triggers**: "infeasible", "won't solve", "no feasible solution", "modelstat", "error 4", "model failed", "solver error", "abort"
**Lessons count**: 3 entries

> **Before anything else, read Step 0.** A run that aborts with "... became infeasible
> during initialisation" is often a *skipped solve* caused by GAMS execution errors, not
> a real optimizer infeasibility. For pure GAMS compile/execution errors (the model does
> not reach a solve), use `agent/helpers/debugging_gams_errors.md`.

---

## Quick Reference

### What "infeasible" means in MAgPIE
The optimizer cannot satisfy all constraints simultaneously. Common causes:
1. **Land constraints too tight** — conservation + production + forestry exceed available land
2. **Water unavailable** — irrigation demand exceeds supply with no trade allowed
3. **Food demand unachievable** — population demand can't be met with available land/trade
4. **Carbon policy too aggressive** — emission caps conflict with production needs
5. **Bioenergy targets impossible** — 2nd-gen bioenergy demand exceeds available land

### First diagnostic steps
```r
# Load the fulldata.gdx produced on failure
library(gdx2)
gdx <- "fulldata.gdx"

# 1. Which timestep failed?
readGDX(gdx, "p80_modelstat")

# 2. Which penalty variables activated (penalty costs)?
# Non-zero levels show where model is straining
readGDX(gdx, "v73_prod_heaven_timber")     # timber penalty var ($1M/tDM)
readGDX(gdx, "v44_bii_missing")            # biodiversity penalty var ($1M/unit)
readGDX(gdx, "v32_land_missing")           # forestry penalty var ($1M/ha)
readGDX(gdx, "v21_import_for_feasibility") # wood import penalty var ($1,500/tDM)

# 3. Check land balance — is total land exhausted?
readGDX(gdx, "ov_land", select = list(type = "level"))
# Sum across land types per cluster — should equal cell area
```

---

## Step-by-Step Debugging Workflow

### Step 0: Is this a real infeasibility, or a skipped solve?

**Do this first.** A MAgPIE run that aborts with a message like
`"<Model> became infeasible already during initialisation run. Stop run."` is often
NOT an optimizer infeasibility. Search `full.lst`/`full.log` for:

```
**** SOLVE from line <N> SKIPPED, EXECERROR = <k>
```

If you find it, the solve was **never executed**: `k` GAMS execution errors (e.g.
`log: FUNC SINGULAR: x = 0`, `division by zero`) fired in preloop/presolve *before* the
solve, so GAMS skipped it and left `modelstat = NA`, which the abort check reports as
"infeasible". In that case STOP here and go to `agent/helpers/debugging_gams_errors.md`;
relaxing constraints, checking marginals, or inspecting the land balance will not help.
Only continue with Steps 1-5 if the model actually solved and returned an infeasible
`modelstat`.

### Step 1: Identify the failing timestep
Check `p80_modelstat(t)` — the first timestep with value > 2 (and ≠ 7) is where it failed. Earlier timesteps solved fine.

### Step 2: Check land balance pressure
```r
land <- readGDX(gdx, "ov_land", select = list(type = "level"))
# If land types sum to cell area in most clusters, land is maxed out
# Look for clusters where conservation + forestry + cropland ≈ 100%
```

**Key equation**: `q10_land_area(j)` — strict equality, total land per cluster is FIXED. No land can be created.

### Step 3: Check which constraints have high marginals
```r
# High marginal = constraint is binding hard
# These are the constraints "causing" infeasibility
readGDX(gdx, "oq10_land_area", select = list(type = "marginal"))  # land
readGDX(gdx, "oq43_water", select = list(type = "marginal"))      # water
readGDX(gdx, "oq21_notrade", select = list(type = "marginal"))    # trade
```

### Step 4: Check configuration switches
See "Dangerous Configurations" below.

### Step 5: Try relaxing constraints
Start by relaxing the most likely constraint (based on marginals) and re-run.

---

## Dangerous Configurations

### Known infeasible combinations (from `config/default.cfg`)

| Configuration | Why it's dangerous |
|---|---|
| SSP3 + PkBudg650 | High population + tight carbon budget = impossible |
| `s13_max_gdp_shr` at finite values | Caps technological-change (TC) investment cost as a share of regional GDP; a tight cap can make yield targets unreachable — documented infeasibility trigger |
| `c22_protect_scenario = "GSN_HalfEarth"` + high BII target | >50% land locked + biodiversity floor |
| `s56_cprice_red_factor` > 1 (price amplified) with limited CDR | Amplified CO2 price forces land-use changes that conflict with food/conservation |

### Configuration switches most likely to cause infeasibility

| Switch | Module | Safe range | Dangerous |
|---|---|---|---|
| `s22_conservation_start` | 22 | ≥ 2025 | Early years with high targets |
| `s32_aff_plantation` | 32 | 0-1 | > available land |
| `s56_cprice_red_factor` | 56 | 1 (default = full scenario CO2 price) | >1 amplifies the CO2 price above the scenario path (more infeasibility risk); <1 reduces it. No code-based safe/dangerous cutoff -- risk depends on the scenario price path. |
| `s13_max_gdp_shr` | 13 | Inf (default) | Any finite value |
| `c21_trade_liberalization` | 21 | "regionalized" | "fragmented" removes trade flexibility |
| `c60_2ndgen_biodem` | 60 | low demand scenario | high demand scenario with limited land |
| `s42_watdem_nonagr_scenario` | 42 | depends | high non-ag water demand |

---

## Built-In Penalty Variables (Safety Valves)

MAgPIE has several penalty variables with high penalty costs. When they activate, the model "pays" a huge cost to relax a constraint. **Non-zero level = constraint strain.** The table below lists the main high-penalty safety valves; it is not exhaustive (e.g. `v32_ndc_area_missing`, `v29_treecover_missing`, `v30_betr_missing`, and the CES relaxation `v38_relax_CES_lp` (only in the non-default `sticky_labor` factor-costs realization) also exist).

| Penalty Variable | Module | Penalty | What it relaxes |
|---|---|---|---|
| `v73_prod_heaven_timber` | 73 | $1,000,000/tDM | Timber production shortfall |
| `v44_bii_missing` | 44 | $1,000,000/unit | Biodiversity target gap |
| `v32_land_missing` | 32 | $1,000,000/ha | Forestry land target gap |
| `v21_import_for_feasibility` | 21 | $1,500/tDM | Wood/woodfuel import (only!) |
| `v29_fallow_missing` | 29 | $615/ha | Fallow land target gap |

**⚠️ Critical gap**: Food, feed, and standard crop production have **NO penalty variables**. If food demand can't be met, the model goes infeasible — there's no "import food for feasibility" option.

---

## Common Pitfalls

### 1. Conservation targets conflict with food production
**Symptom**: Infeasibility in later timesteps (2050+) as population grows
**Cause**: Protected areas (Module 22) + minimum forest (Module 35) lock too much land
**Fix**: Reduce `c22_protect_scenario` (config switch in `config/default.cfg`, not a scalar — common confusion) or use more flexible conservation targets

### 2. Water-limited regions with irrigation expansion
**Symptom**: Infeasibility in arid regions
**Cause**: `q43_water` is a hard cap — no inter-cluster water transfer
**Fix**: Check `s42_irrig_eff_scenario` (irrigation efficiency) or reduce irrigation expansion

### 3. Bioenergy demand exceeds available land
**Symptom**: Infeasibility when 2nd-gen bioenergy demand is high
**Cause**: `q60_bioenergy_reg` is a hard floor — each region MUST produce its bioenergy
**Fix**: Reduce bioenergy demand scenario or allow more land conversion

### 4. Trade restrictions too tight
**Symptom**: Regional infeasibility (some regions can't self-supply)
**Cause**: `c21_trade_liberalization = "fragmented"` (low trade liberalization) or low self-sufficiency ratios
**Fix**: Use a more liberal setting such as `regionalized` or `globalized`

### 5. Carbon price + limited CDR
**Symptom**: Infeasibility under ambitious climate policy
**Cause**: High carbon price forces land-use changes that conflict with food/conservation
**Fix**: Reduce `s56_cprice_red_factor`, increase CDR availability, or relax conservation

### 6. Modelstat = 7 (intermediate non-optimal) — NOT a real failure
**Symptom**: Model continues but results seem odd
**Cause**: MAgPIE tolerates modelstat=7 (doesn't abort). Solution is feasible but not fully optimal.
**Action**: Check results carefully but don't assume failure. May indicate near-binding constraints.

---

## Module Cross-References

| Topic | Read |
|---|---|
| Land balance mechanics | `modules/module_10.md`, `cross_module/land_balance_conservation.md` |
| Conservation constraints | `modules/module_22.md`, `modules/module_35.md` |
| Water constraints | `modules/module_42.md`, `modules/module_43.md` |
| Trade and food balance | `modules/module_21.md`, `cross_module/nitrogen_food_balance.md` |
| Carbon policy setup | `modules/module_56.md` |
| Optimization mechanics | `modules/module_80.md` |
| Full debugging reference | `reference/Infeasibility_Debugging_Guide.md` |

---

## Related Helpers & Docs

- **GAMS compile/execution errors** → `agent/helpers/debugging_gams_errors.md` (errors *before/instead of* a solve; the "skipped solve" false infeasibility of Step 0)
- **Modification safety** → `agent/helpers/modification_impact_analysis.md` (code changes that cause infeasibility)
- **Carbon policy pitfalls** → `agent/helpers/scenario_carbon_pricing.md` (aggressive pricing → infeasibility)
- **Conservation constraints** → `cross_module/land_balance_conservation.md` (land conflicts)
- **Water constraints** → `cross_module/water_balance_conservation.md` (irrigation limits)

---

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
- 2026-03-06: Module 57 — `s57_implicit_emis_factor=0` causes guaranteed division-by-zero in modules/57_maccs/on_aug22/equations.gms:40,50. Very small values (e.g. 0.0001) destabilize solver by inflating the MACC cost correction term 100×. Also: `s57_maxmac_*` at step 201 causes `1/(1-mitigation)` blowup when mitigation→1.0 (modules/57_maccs/on_aug22/equations.gms:38,48). (source: deep validation agent analysis)
- 2026-03-06: Module 58 — `s58_rewetting_switch=0` + `s58_rewetting_exo=1` = guaranteed infeasibility (upper bound=0 vs mandate for positive rewetted area). Also: `s58_annual_rewetting_limit=0` + any exo=1 = guaranteed infeasibility. And: `s58_rewet_exo_target_value≥1.0` with default rate limit (0.02/yr) is likely infeasible — max achievable ~50% by 2050 from 2025. Silent bug: `s58_fix_peatland` set to non-timestep year (e.g. 2019) → p58_peatland_ref never populated → targets silently zeroed. (source: deep validation agent analysis)
- 2026-07-14: "Model became infeasible already during initialisation" is frequently a SKIPPED solve, not a real infeasibility. Search `full.lst`/`full.log` for `SOLVE ... SKIPPED, EXECERROR = k`: k GAMS execution errors (log(0), division by zero) in preloop/presolve made GAMS skip the solve, leaving `modelstat = NA`, which the abort check misreports as infeasible. Fix the execution errors (see `debugging_gams_errors.md`); do NOT relax constraints or chase marginals. Added "Step 0" to the workflow to check this first. (source: session experience — fallow branch; a "Food Demand Model became infeasible" abort was actually a `log(0)` on `f36_hist_hourly_costs` in module 36)
