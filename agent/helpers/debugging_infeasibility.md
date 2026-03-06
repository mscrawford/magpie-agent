# Helper: Debugging Model Infeasibility

**Auto-load triggers**: "infeasible", "won't solve", "no feasible solution", "modelstat", "error 4", "model failed", "abort"
**Last updated**: 2026-03-06
**Lessons count**: 0 entries

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
library(gdx)
gdx <- "fulldata.gdx"

# 1. Which timestep failed?
readGDX(gdx, "p80_modelstat")

# 2. Which slack variables activated (penalty costs)?
# Non-zero slacks show where model is straining
readGDX(gdx, "v73_prod_heaven_timber")     # timber slack ($1M/tDM)
readGDX(gdx, "v44_bii_missing")            # biodiversity slack ($1M/unit)
readGDX(gdx, "v32_land_missing")           # forestry slack ($1M/ha)
readGDX(gdx, "v21_import_for_feasibility") # wood import slack ($1,500/tDM)

# 3. Check land balance — is total land exhausted?
readGDX(gdx, "ov_land", select = list(type = "level"))
# Sum across land types per cluster — should equal cell area
```

---

## Step-by-Step Debugging Workflow

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
| `s13_max_gdp_shr` at finite values | Caps agricultural GDP share — documented infeasibility trigger |
| `c22_protect_scenario = "GSN_HalfEarth"` + high BII target | >50% land locked + biodiversity floor |
| Very high `s56_cprice_red_factor` with early start year | Aggressive carbon price + no CDR option |

### Configuration switches most likely to cause infeasibility

| Switch | Module | Safe range | Dangerous |
|---|---|---|---|
| `s22_conservation_start` | 22 | ≥ 2025 | Early years with high targets |
| `s32_aff_plantation` | 32 | 0-1 | > available land |
| `s56_cprice_red_factor` | 56 | 0-0.5 | > 0.8 with early start |
| `s13_max_gdp_shr` | 13 | Inf (default) | Any finite value |
| `c21_trade_liberalization` | 21 | "regionalized" | "autarky" removes trade flexibility |
| `s60_2ndgen_bioenergy` | 60 | "phaseout" | "demandside" with high targets |
| `s43_watdem_nonagr_scenario` | 43 | depends | high non-ag water demand |

---

## Built-In Slack Variables (Safety Valves)

MAgPIE has 13 slack variables with high penalty costs. When they activate, the model "pays" a huge cost to relax a constraint. **Non-zero slack = constraint strain.**

| Slack Variable | Module | Penalty | What it relaxes |
|---|---|---|---|
| `v73_prod_heaven_timber` | 73 | $1,000,000/tDM | Timber production shortfall |
| `v44_bii_missing` | 44 | $1,000,000/unit | Biodiversity target gap |
| `v32_land_missing` | 32 | $1,000,000/ha | Forestry land target gap |
| `v21_import_for_feasibility` | 21 | $1,500/tDM | Wood/woodfuel import (only!) |
| `v21_excess_prod` | 21 | $300/tDM | Excess production disposal |
| `v30_fallow_missing` | 30 | $100/ha | Fallow land target gap |
| `v35_secdforest_missing` | 35 | ~$100/ha | Forest regeneration gap |
| `v35_other_missing` | 35 | ~$100/ha | Other natural land gap |

**⚠️ Critical gap**: Food, feed, and standard crop production have **NO slack variables**. If food demand can't be met, the model goes infeasible — there's no "import food for feasibility" option.

---

## Common Pitfalls

### 1. Conservation targets conflict with food production
**Symptom**: Infeasibility in later timesteps (2050+) as population grows
**Cause**: Protected areas (Module 22) + minimum forest (Module 35) lock too much land
**Fix**: Reduce `s22_protect_scenario` or use more flexible conservation targets

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
**Cause**: `c21_trade_liberalization = "autarky"` or low self-sufficiency ratios
**Fix**: Use "regionalized" or "free" trade settings

### 5. Carbon price + limited CDR
**Symptom**: Infeasibility under ambitious climate policy
**Cause**: High carbon price forces land-use changes that conflict with food/conservation
**Fix**: Reduce `s56_cprice_red_factor`, increase CDR availability, or relax conservation

### 6. Modelstat = 7 (intermediate infeasible) — NOT a real failure
**Symptom**: Model continues but results seem odd
**Cause**: MAgPIE tolerates modelstat=7 (doesn't abort). Solution exists but isn't fully optimal.
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

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
