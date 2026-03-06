# Helper: Setting Up Carbon Pricing Scenarios

**Auto-load triggers**: "carbon price", "carbon tax", "GHG policy", "emission pricing", "climate policy", "REDD", "afforestation incentive", "carbon budget"
**Last updated**: 2026-03-06
**Lessons count**: 2 entries

---

## Quick Reference

### The 4 key settings for any carbon pricing scenario

```r
# In config/default.cfg or your scenario config:

# 1. PRICE TRAJECTORY — which carbon price path?
cfg$gms$c56_pollutant_prices <- "R34M410-SSP2-NPi2025"  # Current policies (~3°C)
# Ambitious alternatives:
#   "R34M410-SSP2-PkBudg1000"  → well-below 2.0°C
#   "R34M410-SSP2-PkBudg650"   → well-below 1.5°C (caution: may cause infeasibility)
#   "none"                      → no carbon pricing at all

# 2. WHICH EMISSIONS ARE PRICED?
cfg$gms$c56_emis_policy <- "reddnatveg_nosoil"  # Default: CO2 from deforestation + natveg loss; all CH4/N2O
# Common alternatives:
#   "none"                  → no emissions priced
#   "redd_nosoil"           → only forest CO2 + CH4/N2O
#   "redd+natveg_nosoil"    → forest + forestry + natveg CO2 + CH4/N2O
#   "all_nosoil"            → all LUC CO2 + CH4/N2O

# 3. C-PRICE DRIVEN AFFORESTATION?
cfg$gms$s56_c_price_induced_aff <- 1    # 1=on, 0=off
cfg$gms$c56_cprice_aff <- "secdforest_vegc"  # Carbon density reference for aff reward

# 4. PRICE REDUCTION FACTOR
cfg$gms$s56_cprice_red_factor <- 1      # 1=full price, 0.5=half, 0=no CO2 pricing on land
```

### Common scenario recipes

| Scenario | Price | Emissions | Aff | Notes |
|----------|-------|-----------|-----|-------|
| **No policy** | `"none"` | `"none"` | 0 | Baseline, no climate policy |
| **Current policies (NPi)** | `"R34M410-SSP2-NPi2025"` | `"reddnatveg_nosoil"` | 1 | Default, ~3°C |
| **Paris-aligned (2°C)** | `"R34M410-SSP2-PkBudg1000"` | `"reddnatveg_nosoil"` | 1 | Moderate ambition |
| **1.5°C ambitious** | `"R34M410-SSP2-PkBudg650"` | `"reddnatveg_nosoil"` | 1 | ⚠️ Check feasibility |
| **REDD+ only** | `"R34M410-SSP2-PkBudg1000"` | `"redd+_nosoil"` | 1 | Includes forestry |
| **No aff incentive** | `"R34M410-SSP2-PkBudg1000"` | `"reddnatveg_nosoil"` | 0 | No C-price driven afforestation |

---

## Step-by-Step: Building a Carbon Pricing Scenario

### Step 1: Choose your SSP and climate target

The price trajectory encodes both the socioeconomic pathway (SSP) and climate target:
```
R34M410-{SSP}-{Target}
         │      └─ NPi2025 / PkBudg1000 / PkBudg650
         └─ SSP1 / SSP2 / SSP3 / SSP5
```

**⚠️ SSP3 + PkBudg650 is documented as infeasible** (`config/default.cfg:1613`). SSP3's high population growth makes 1.5°C impossible.

### Step 2: Decide which emissions to price

The `c56_emis_policy` switch controls which emission sources face a carbon price:

| Policy | CO2 sources priced | CH4/N2O |
|--------|-------------------|---------|
| `none` | Nothing | Nothing |
| `redd_nosoil` | Forest deforestation | All |
| `reddnatveg_nosoil` | Forest + other natural vegetation | All |
| `redd+_nosoil` | Forest + forestry (managed) | All |
| `redd+natveg_nosoil` | Forest + forestry + natveg | All |
| `all_nosoil` | All land-use types (incl. cropland) | All |

**Key interaction**: If `c56_emis_policy` does NOT include "forestry", there's no cost for deforesting plantations. Set `c56_cprice_aff = "secdforest_vegc"` to still enable C-price driven afforestation.

### Step 3: Configure afforestation incentives

```r
# Enable/disable C-price driven afforestation
cfg$gms$s56_c_price_induced_aff <- 1  # 1=on, 0=off

# Carbon density reference for calculating afforestation reward
cfg$gms$c56_cprice_aff <- "secdforest_vegc"
# Options: "forestry_vegc", "primforest_vegc", "secdforest_vegc"
# secdforest_vegc = use secondary forest carbon density (conservative, recommended)

# Buffer for non-permanence risk (reduces afforestation incentive)
cfg$gms$s56_buffer_aff <- 0.5  # 50% of credits withheld (default)

# Price expectation horizon (years of future C revenue considered)
cfg$gms$s56_c_price_exp_aff <- 50  # Max 50 years (should ≤ s32_planning_horizon)

# Temporal fade-in of afforestation incentive
cfg$gms$s56_fader_cpriceaff_start <- 2030  # Start year
cfg$gms$s56_fader_cpriceaff_end <- 2030    # End year (same = immediate)
```

### Step 4: Fine-tune with advanced settings

```r
# Mute ALL GHG prices until this year (minimum price still applies)
cfg$gms$c56_mute_ghgprices_until <- "y2030"  # Default: prices start after 2030

# Minimum carbon price floor (prevents zero-price jumps)
cfg$gms$s56_minimum_cprice <- 3.67  # USD17MER per tC (≈ 1 USD/tCO2)

# Cap on CH4/N2O prices (prevents extreme non-CO2 costs)
cfg$gms$s56_limit_ch4_n2o_price <- 4920  # USD17MER per tC

# Scale GHG prices with development state (lower for developing countries)
cfg$gms$s56_ghgprice_devstate_scaling <- 0  # 0=off (all regions same price), 1=on

# GHG policy fader (gradual phase-in of carbon pricing)
cfg$gms$s56_ghgprice_fader <- 0  # 0=off, 1=on (for developing countries)
```

### Step 5: Choose carbon stock accounting method

```r
cfg$gms$c56_carbon_stock_pricing <- "actualNoAcEst"
# "actual"       → all carbon stock changes priced (including new forests)
# "actualNoAcEst" → excludes newly established areas (avoids double-counting with aff reward)
```

---

## Common Pitfalls

### 1. Forgetting `c56_emis_policy` interaction with afforestation
Setting `c56_emis_policy = "redd_nosoil"` (forest only) but expecting afforestation incentives → no incentive unless `c56_cprice_aff` uses forest carbon density.

### 2. Aggressive price + conservation = infeasibility
High carbon prices drive massive afforestation, but conservation targets (Module 22) already lock land. The combination can leave insufficient land for food.

### 3. `s56_cprice_red_factor = 0` silently disables CO2 pricing
This scales ALL CO2 prices to zero. CH4/N2O still priced. The model runs but produces misleading results.

### 4. Mismatched SSP between drivers and prices
Using SSP2 drivers (Module 09) with SSP1 carbon prices creates inconsistency. The price trajectory assumes a specific socioeconomic context.

### 5. `c56_mute_ghgprices_until` masks the start year
Default "y2030" means prices only take effect AFTER 2030. If your scenario needs earlier action, change this.

### 6. Non-CO2 price cap too low
`s56_limit_ch4_n2o_price = 4920` caps non-CO2 prices at the maximum MACC abatement level. Lowering this reduces mitigation potential.

---

## Module Cross-References

| Topic | Read |
|---|---|
| GHG policy mechanics | `modules/module_56.md` |
| MACC curves (CH4/N2O mitigation) | `modules/module_57.md` |
| Carbon stock calculation | `modules/module_52.md` |
| Methane emissions | `modules/module_53.md` |
| Forestry and afforestation | `modules/module_32.md` |
| Natural vegetation (REDD+) | `modules/module_35.md` |
| Peatland emissions | `modules/module_58.md` |
| Cost aggregation | `modules/module_11.md` |
| Debugging infeasibility | `agent/helpers/debugging_infeasibility.md` |

---

## Related Helpers & Docs

- **Infeasibility from aggressive pricing** → `agent/helpers/debugging_infeasibility.md`
- **Carbon balance mechanics** → `cross_module/carbon_balance_conservation.md`
- **Module modification safety** → `cross_module/modification_safety_guide.md`
- **Realization choices** → `agent/helpers/realization_selection.md` (GHG module realizations)

---

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
- 2026-03-06: Module 56 c56_cprice_aff="secdforest_vegc" interacts with c56_emis_policy — if forestry isn't in the emission policy, setting cprice_aff alone won't create afforestation incentives. Always check both settings together. (source: deep validation of module 56)
- 2026-03-06: The c56_mute_ghgprices_until setting means carbon prices only take effect AFTER the specified year (default y2030). If running short historical scenarios, prices may appear to have no effect — this is by design, not a bug. (source: config/default.cfg analysis)
