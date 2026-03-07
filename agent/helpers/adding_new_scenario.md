# Helper: Creating New MAgPIE Scenarios

**Auto-load triggers**: "scenario", "new scenario", "policy scenario", "combine policies", "config switches", "scenario design"
**Last updated**: 2025-07-15
**Lessons count**: 0 entries

---

## Quick Reference

MAgPIE scenarios are built by combining policy switches that control module realizations, parameter values, and input data. There are three main mechanisms, from simplest to most advanced:

| Mechanism | Where | When to Use |
|-----------|-------|-------------|
| **Scenario CSV + `setScenario()`** | `config/scenario_config.csv` or project-specific CSV | Combining named presets (SSPs, policies) — **recommended for most users** |
| **Direct `cfg$gms$` overrides** in a start script | `scripts/start/projects/your_project.R` | Fine-grained control, project-specific runs |
| **GAMS code modification** | `modules/XX_name/realization/*.gms` | Adding new realizations or behaviors (advanced) |

### The `cfg$gms$` Switch Naming Convention

```
cfg$gms$<prefix><module_number>_<name>

Prefixes:
  c  → categorical switch (selects among named options, e.g. "SSP2", "npi", "ndc")
  s  → scalar switch (numeric value, e.g. 0.5, 2025, Inf)
  (none) → realization selector (chooses which module code to run)
```

**Examples:**
- `cfg$gms$food` → selects realization for module 15 (e.g. `"anthro_iso_jun22"`)
- `cfg$gms$c56_pollutant_prices` → categorical: which carbon price trajectory
- `cfg$gms$s15_exo_waste` → scalar: 0=off, 1=on for exogenous waste reduction

---

## Step-by-Step: Creating a New Scenario

### Step 1: Identify Which Modules to Configure

The most commonly modified modules and their key switches (from `config/default.cfg`):

#### Socioeconomic Drivers (Module 09)
```r
cfg$gms$c09_pop_scenario  <- "SSP2"    # SSP1-5, SDP variants
cfg$gms$c09_gdp_scenario  <- "SSP2"    # SSP1-5, SDP_EI, SDP_RC, SDP_MC
cfg$gms$c09_pal_scenario  <- "SSP2"    # Physical activity level: SSP1-5
```

#### Food Demand & Diets (Module 15)
```r
cfg$gms$s15_exo_diet  <- 0             # 0=off, 1=EAT-Lancet, 3=new EAT-Lancet realization
cfg$gms$c15_EAT_scen  <- "FLX"         # FLX, FLX_hmilk, PSC, VGN, VEG, etc.
cfg$gms$c15_kcal_scen <- "healthy_BMI" # healthy_BMI, no_underweight, etc.
cfg$gms$s15_exo_waste <- 0             # 0=off, 1=on (exogenous waste reduction)
cfg$gms$s15_waste_scen <- 1.2          # waste reduction factor (when s15_exo_waste=1)
cfg$gms$c15_food_scenario <- "SSP2"    # SSP1-5 food demand projection
```

#### Trade (Module 21)
```r
cfg$gms$c21_trade_liberalization <- "l909090r808080"  # Trade liberalization trajectory
cfg$gms$s21_trade_tariff <- 1                         # 0=off, 1=on
```

#### Land Conservation (Module 22)
```r
cfg$gms$c22_protect_scenario <- "none"  # none, BH, BH_IFL, WDPA, etc.
cfg$gms$c22_base_protect <- "WDPA"      # Baseline protected areas
```

#### Cropland (Module 30) & Bioenergy
```r
cfg$gms$c30_bioen_water <- "rainfed"    # rainfed, all (irrigated bioenergy allowed?)
cfg$gms$cropland <- "detail_apr24"      # Realization: simple_apr24, detail_apr24
```

#### Forestry & Afforestation (Module 32)
```r
cfg$gms$c32_aff_policy <- "npi"         # none, npi, ndc
cfg$gms$s32_max_aff_area <- Inf         # Max afforestation area (Mha); Inf=unlimited
cfg$gms$c32_aff_mask <- "noboreal"      # noboreal, onlytropical, unrestricted
cfg$gms$s32_aff_plantation <- 0         # 0=natural regrowth, 1=plantation
```

#### Natural Vegetation (Module 35)
```r
cfg$gms$c35_ad_policy  <- "npi"         # none, npi, ndc (avoided deforestation)
cfg$gms$c35_aolc_policy <- "npi"        # none, npi, ndc (avoided other LUC)
```

#### Irrigation (Modules 41/42)
```r
cfg$gms$s42_irrig_eff_scenario <- 2     # 1=low, 2=medium, 3=high efficiency
cfg$gms$c42_env_flow_policy <- "off"    # off, on, mixed
cfg$gms$s42_watdem_nonagr_scenario <- 2 # 1-3: non-agricultural water demand
```

#### Nitrogen Efficiency (Module 50)
```r
cfg$gms$c50_scen_neff <- "baseeff_add3_add5_add10_max65"  # N-efficiency trajectory
```

#### GHG Pricing (Module 56)
```r
cfg$gms$c56_pollutant_prices <- "R34M410-SSP2-NPi2025"  # Carbon price trajectory
cfg$gms$c56_emis_policy <- "reddnatveg_nosoil"           # Which emissions are priced
cfg$gms$s56_c_price_induced_aff <- 1                     # C-price driven afforestation
cfg$gms$s56_cprice_red_factor <- 1                       # 1=full price, 0=no CO2 pricing
cfg$gms$c56_mute_ghgprices_until <- "y2030"              # Mute GHG prices until year
```

#### Peatland (Module 58)
```r
cfg$gms$s58_rewetting_switch <- Inf     # Inf=no rewetting, year=start rewetting
cfg$gms$s58_rewetting_exo <- 0          # 0=off, 1=exogenous rewetting
```

#### Bioenergy Demand (Module 60)
```r
cfg$gms$c60_1stgen_biodem <- "const2020"                 # 1st-gen bioenergy demand
cfg$gms$c60_2ndgen_biodem <- "R34M410-SSP2-NPi2025"     # 2nd-gen bioenergy demand
```

### Step 2: Use the Scenario CSV System (`setScenario`)

MAgPIE provides pre-built scenario bundles in `config/scenario_config.csv`. Each column is a named scenario that sets multiple `cfg$gms$` switches at once.

**Available presets in `config/scenario_config.csv`** (80 rows of switches):

| Category | Preset Names | What They Set |
|----------|-------------|---------------|
| **SSPs** | `SSP1`, `SSP2`, `SSP3`, `SSP4`, `SSP5` | Population, GDP, PAL, food, diet, trade, N-efficiency, many more |
| **SDP variants** | `SDP`, `SDP-EI`, `SDP-RC`, `SDP-MC` | Sustainable development pathways with diet/waste/protection |
| **Climate** | `cc`, `nocc`, `nocc_hist` | Climate change impacts on yields, water, carbon, SOM |
| **Policies** | `NPI`, `NPI-revert`, `NDC` | National policies: afforestation, avoided deforestation, protection reversal |
| **RCPs** | `rcp1p9`, `rcp2p6`, `rcp4p5`, `rcp6p0`, `rcp7p0`, `rcp8p5` | Climate input data (cellular) |
| **Diet** | `eat_lancet_diet_v1`, `eat_lancet_diet_v2` | EAT-Lancet diet transitions |
| **Forestry** | `ForestryEndo`, `ForestryExo`, `ForestryOff` | Timber demand and forestry management |
| **Bioenergy** | `AR-natveg`, `AR-plant` | Afforestation realization: natural vs. plantation |

**Usage in a start script:**
```r
library(gms)
source("scripts/start_functions.R")
source("config/default.cfg")

# Apply one or more presets (later ones override earlier ones)
cfg <- setScenario(cfg, c("SSP2", "NPI", "rcp4p5"))
```

**Project-specific scenario CSVs** are in `config/projects/` (e.g., `scenario_config_fsec.csv`, `scenario_config_genie.csv`). Use them with:
```r
cfg <- setScenario(cfg, c("myPreset"), scenario_config = "config/projects/scenario_config_myproject.csv")
```

The emulator coupling CSV (`config/scenario_config_emulator.csv`) has a different format with columns: `start`, `mag_scen`, `ghgtax_name`, `mifname`, `no_ghgprices_land_until`.

### Step 3: Create a Start Script

Start scripts live in `scripts/start/` (simple runs) or `scripts/start/projects/` (project runs). They follow a standard pattern:

```r
# ----------------------------------------------------------
# description: My custom scenario runs
# position: 5
# ----------------------------------------------------------

library(lucode2)
library(gms)

# Load start_run() function
source("scripts/start_functions.R")

# Load default configuration
source("config/default.cfg")

# Set output folder pattern and options
cfg$results_folder <- "output/:title:"
cfg$force_replace <- TRUE

# Apply scenario presets
cfg <- setScenario(cfg, c("SSP2", "NPI"))

# Override specific switches
cfg$gms$c56_pollutant_prices <- "R34M410-SSP2-PkBudg1000"
cfg$gms$c22_protect_scenario <- "BH"

# Set a descriptive title
cfg$title <- "SSP2_NPI_2degC_BH"

# Launch the run
start_run(cfg, codeCheck = FALSE)
```

**Running multiple scenarios in a loop** (common pattern from real project scripts):

```r
for (pol in c("NPI", "NDC")) {
  for (diet in c(0, 1)) {
    cfg <- setScenario(cfg, c("SSP2", pol, "rcp4p5"))
    cfg$gms$s15_exo_diet <- diet
    cfg$title <- paste("SSP2", pol, ifelse(diet == 1, "EATLancet", "baseline"), sep = "_")
    start_run(cfg, codeCheck = FALSE)
  }
}
```

**Important:** Always re-source `config/default.cfg` or re-apply `setScenario()` before each run in a loop — switches from the previous iteration persist in the `cfg` object.

### Step 4: Understand the `cfg$gms$` Mechanism

When MAgPIE starts, the `cfg$gms` list is written to a GAMS-readable file. The switches control behavior in two ways:

1. **Realization selection** — switches without a prefix (e.g., `cfg$gms$food <- "anthro_iso_jun22"`) select which folder of GAMS code gets compiled for that module.

2. **Scalar/categorical parameters** — switches with `s` or `c` prefixes are passed as GAMS scalars or set elements that conditional logic reads inside the GAMS code.

The `_noselect` variants (e.g., `cfg$gms$c22_protect_scenario_noselect`) apply to countries NOT in the `select_countries` list, enabling country-specific policies:
```r
cfg$gms$scen_countries15 <- "IND"                  # Apply diet change to India only
cfg$gms$s15_exo_diet <- 1                          # Diet change for selected countries
cfg$gms$c15_food_scenario_noselect <- "SSP2"       # Rest of world uses SSP2
```

### Step 5: Testing and Validation

After running your scenario, check these:

1. **Check for infeasibilities** — look at the `.lst` file for `*** INFES` markers:
   ```bash
   grep -c "INFES" output/<run_name>/full.lst
   ```

2. **Check modelstat** — should be 1 (optimal) or 2 (locally optimal) for each time step:
   ```bash
   grep "modelstat" output/<run_name>/full.lst | tail -20
   ```

3. **Compare key outputs** against a baseline run using `output.R` reporting scripts

4. **Sanity checks:**
   - Total land area stays constant (~13,000 Mha)
   - Food demand is met (check `q15_food_demand` marginals)
   - Emissions respond to carbon pricing as expected
   - Cropland/forest area changes are directionally correct

5. **Run validation** via the output processing:
   ```bash
   Rscript output.R
   ```

---

## Common Policy Combinations

### 1. Climate + Land Policy (Carbon Pricing + Forest Protection)

```r
source("config/default.cfg")
cfg <- setScenario(cfg, c("SSP2", "NDC", "rcp2p6"))

# Carbon pricing: 2°C-compatible pathway
cfg$gms$c56_pollutant_prices    <- "R34M410-SSP2-PkBudg1000"
cfg$gms$c56_emis_policy         <- "reddnatveg_nosoil"
cfg$gms$s56_c_price_induced_aff <- 1

# Land protection: Half-Earth (Biodiversity Hotspots)
cfg$gms$c22_protect_scenario    <- "BH"

# Afforestation: NDC commitments, tropical only
cfg$gms$c32_aff_policy          <- "ndc"
cfg$gms$c32_aff_mask            <- "onlytropical"
cfg$gms$s32_max_aff_area        <- 500
```

### 2. Demand-Side: Diet Change + Food Waste Reduction

```r
source("config/default.cfg")
cfg <- setScenario(cfg, c("SSP2", "NPI"))

# EAT-Lancet diet transition
cfg$gms$s15_exo_diet             <- 1
cfg$gms$c15_EAT_scen             <- "FLX"
cfg$gms$c15_kcal_scen            <- "healthy_BMI"
cfg$gms$s15_exo_monogastric      <- 1
cfg$gms$s15_exo_ruminant         <- 1
cfg$gms$s15_exo_fish             <- 1
cfg$gms$s15_exo_fruitvegnut      <- 1
cfg$gms$s15_exo_pulses           <- 1
cfg$gms$s15_food_substitution_start  <- 2025
cfg$gms$s15_food_substitution_target <- 2050

# Food waste reduction
cfg$gms$s15_exo_waste            <- 1
cfg$gms$s15_waste_scen           <- 1.2
```

### 3. Supply-Side: Yield Intensification + Irrigation Expansion

```r
source("config/default.cfg")
cfg <- setScenario(cfg, c("SSP2", "NPI"))

# Higher nitrogen efficiency → higher yields
cfg$gms$c50_scen_neff <- "baseeff_add3_add15_add25_max75"

# Irrigation: allow bioenergy irrigation, improve efficiency
cfg$gms$c30_bioen_water          <- "all"
cfg$gms$s42_irrig_eff_scenario   <- 3       # High efficiency gains
cfg$gms$c42_env_flow_policy      <- "on"    # But respect environmental flows
cfg$gms$s42_efp_targetyear       <- 2040

# Lower tech change costs → faster intensification
cfg$gms$c13_tccost               <- "low"
```

### 4. Comprehensive SDP: Sustainability Across All Dimensions

```r
source("config/default.cfg")
# The SDP preset bundles many switches at once
cfg <- setScenario(cfg, c("SDP", "NPI", "rcp1p9"))

# SDP already sets: diet change, waste reduction, BH protection,
# high irrigation efficiency, environmental flows, trade liberalization
# You can further customize:
cfg$gms$c56_pollutant_prices    <- "R34M410-SSP1-PkBudg650"
cfg$gms$c56_emis_policy         <- "all_nosoil"
cfg$gms$s29_snv_shr             <- 0.2     # 20% semi-natural vegetation on cropland
cfg$gms$s29_snv_scenario_target <- 2050
```

---

## Common Pitfalls

### ⚠️ Switch Interactions That Cause Infeasibility

1. **Aggressive carbon pricing + strict land protection** — very high carbon prices (e.g., `PkBudg650`) combined with `BH_IFL` protection can make it impossible for the model to find enough land for food production + afforestation. Start with `PkBudg1000` and test before going more ambitious.

2. **Exogenous diet + inconsistent food product switches** — if `s15_exo_diet=1`, you must also set the individual product switches (`s15_exo_monogastric`, `s15_exo_ruminant`, etc.) to 1 for the diet change to apply across food groups. Setting `s15_exo_diet=1` alone activates the EAT-Lancet framework, but individual product convergence requires those switches.

3. **Bioenergy + limited land** — high 2nd-generation bioenergy demand (`c60_2ndgen_biodem` from an ambitious climate scenario) combined with strict land protection and afforestation targets can exhaust available land. Consider setting `s32_max_aff_area` to a finite value.

4. **Environmental flows + irrigation expansion** — enabling `c42_env_flow_policy="on"` restricts water availability, which may conflict with expanded irrigation (`c30_bioen_water="all"`). This is realistic but can cause infeasibility in water-scarce regions.

### ⚠️ Order-Dependent Configurations

- **`setScenario()` overwrites previous values** — if you call `setScenario(cfg, c("SSP2", "NPI"))` and then manually set `cfg$gms$c32_aff_policy <- "none"`, the manual setting wins. But if you call `setScenario()` *after* your manual overrides, the preset will overwrite them.
- **Always apply presets first, then override** — the pattern is: `source("config/default.cfg")` → `setScenario()` → manual `cfg$gms$` overrides → `start_run()`.
- **In loops, reset cfg each iteration** — re-source `default.cfg` or keep a clean copy: `cfg_base <- cfg` before the loop, then `cfg <- cfg_base` at the start of each iteration.

### ⚠️ Forgetting Dependent Switches

- **`c56_pollutant_prices` needs matching `c60_2ndgen_biodem`** — in coupled scenarios, the carbon price and bioenergy demand trajectories should come from the same REMIND scenario (same `R34M410-SSP2-...` prefix).
- **`c56_mute_ghgprices_until`** — defaults to `"y2030"`. If you set a carbon price but mute until 2150, you effectively have no land-based carbon pricing. The scenario CSV sets this to `"y2150"` for the `BASE` preset intentionally.
- **`_noselect` variants** — if you use country-specific policies (e.g., `cfg$gms$scen_countries15`), remember to set BOTH the main switch AND the `_noselect` variant, or non-selected countries will use the default value.
- **Climate input data** — `cc`/`nocc`/`nocc_hist` switches across modules (14, 42, 43, 52, 59) should be consistent. The `cc`, `nocc`, and `nocc_hist` presets in `scenario_config.csv` handle this automatically. If overriding manually, set ALL of: `c14_yields_scenario`, `c42_watdem_scenario`, `c43_watavail_scenario`, `c52_carbon_scenario`, `c59_som_scenario`.

---

## Lessons Learned

*(No entries yet — this section will be populated with user feedback and discovered patterns.)*
