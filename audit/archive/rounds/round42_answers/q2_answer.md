# Q2: How Climate (Module 45) Enters MAgPIE and Affects Yields (M14) and SOM (M59)

**Confidence**: 🟡 Documented (all claims from AI docs read this session; raw GAMS not opened per task constraints)

---

## Overview: What Module 45 Actually Is

Module 45 is a **pure data-provider module** — zero equations, zero optimization variables, one parameter. It reads historical Köppen-Geiger climate classification data (Rubel et al. 2010, period 1976-2000) and makes it available as `pm_climate_class(j,clcl)`, which gives the area share of each of 31 climate types within each of the ~200 simulation cells.

Crucially: **Module 45 carries no CO2 scenario, no climate projection, and no time variation.** The "climate" in its name refers to classification zones used to look up zone-specific biophysical parameters — not to dynamic climate forcing.

Default realization: `static` (the only realization). Set in `config/default.cfg:1474`: `cfg$gms$climate <- "static"`.

---

## (a) Default Climate/CO2 Scenario and Where It Is Set

There is no single "the climate scenario" in MAgPIE. Climate enters through **two independent channels** with separate scenario switches:

### Channel 1: Crop yields (Module 14)

**Switch**: `c14_yields_scenario`
**Default**: `"cc"` (climate change)
**Location**: `config/default.cfg:360`

```
cfg$gms$c14_yields_scenario  <- "cc"   # def = "cc"
```

Options:
- `"cc"` — time-varying LPJmL yields that incorporate climate change projections
- `"nocc"` — all future yields fixed at 1995 values
- `"nocc_hist"` — climate change until `sm_fix_cc` (default: 2025, `default.cfg:228`), then frozen

**What "cc" means mechanistically**: the input file `lpj_yields.cs3` (loaded at `module_14/managementcalib_aug19/input.gms:37`) is a pre-computed LPJmL output table with time-varying crop yields under a climate change scenario. Under `"nocc"`, future rows of that table are replaced by 1995 values (`input.gms:41-42`).

There is no CO2 fertilization effect computed within MAgPIE. Any CO2 effect on plant productivity is embedded in the LPJmL preprocessing that produced `lpj_yields.cs3`. MAgPIE reads the result.

### Channel 2: Soil organic matter topsoil carbon reference (Module 59)

**Switch**: `c59_som_scenario`
**Default**: `"cc"` (climate change)
**Location**: `config/default.cfg:1930`

```
cfg$gms$c59_som_scenario  <- "cc"   # def = "cc"
```

Options are identical in structure (`"cc"` / `"nocc"` / `"nocc_hist"`). Under `"cc"`, the parameter `f59_topsoilc_density(t,j)` — natural vegetation topsoil carbon density from LPJmL — varies over time. Under `"nocc"`, it is frozen at 1995 values (`module_59/input.gms:84`).

### What Module 45 does NOT provide

Module 45 provides no climate scenario at all. The Köppen-Geiger classification is fixed at the 1976-2000 historical baseline regardless of any scenario switch, and there is no RCP/SSP/CMIP6 pathway available through Module 45. Future climate reclassification is explicitly absent (`module_45.md` Limitations §1, §9).

---

## (b) Climate Effect on Yields: Mechanistic or Parameterization?

### Answer: Parameterization, not mechanistic modeling.

**Three-check verification:**

1. **Equation check**: Equation `q14_yield_crop` (`equations.gms:14-16`) is:

   ```gams
   q14_yield_crop(j2,kcr,w) ..
     vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                           vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
   ```

   The equation multiplies a **pre-computed, calibrated yield baseline** (`i14_yields_calib`) by a technological change factor. There is no temperature variable, no precipitation variable, no CO2 concentration variable, and no plant-physiology equation anywhere in Module 14. The climate effect is entirely inside `i14_yields_calib`.

2. **Source check**: `i14_yields_calib` is built in the preloop phase from `f14_yields(t,j,kcr,w)`, which is read from the external input file `lpj_yields.cs3` (`input.gms:37`). That file is pre-computed output from the LPJmL dynamic global vegetation model, run externally under a specified climate scenario before MAgPIE ever starts. The time dimension in `f14_yields` carries the climate change signal. Under `c14_yields_scenario = "nocc"`, the future-year rows of this table are overwritten with 1995 values, eliminating any climate trend. There is no MAgPIE equation that simulates crop-climate response.

3. **Feedback check**: Model land-use decisions do not feed back to modify climate, CO2 concentration, or LPJmL outputs within a run. The yield table is fixed at preloop. Yields can change via `vm_tau` (technological change, Module 13) and the management factor `pm_past_mngmnt_factor` (pasture only, Module 70), but neither of those is climate-driven within the model.

**Conclusion**: MAgPIE applies exogenous, climate-conditioned LPJmL yield data. It does not model crop-climate dynamics. The correct language is "MAgPIE uses LPJmL-derived yields that reflect an external climate change scenario" — not "MAgPIE models climate impacts on yields."

### The parameter that carries the climate signal

`f14_yields(t,j,kcr,w)` — dimensions: time × cell × crop × water system. Read from `lpj_yields.cs3` at `module_14/managementcalib_aug19/input.gms:37`. The time variation in this table is the sole source of climate-change effects on crop yields within the GAMS optimization. After calibration, it becomes `i14_yields_calib(t,j,kcr,w)` (`preloop.gms:108-116`), which is what the two yield equations actually use.

### Where pm_climate_class enters Module 14

Module 45's `pm_climate_class(j,clcl)` is used in Module 14's **presolve phase**, not in the yield equations themselves. It appears in the growing-stock (timber) calculation:

```gams
im_growing_stock(t,j,ac,"forestry") =
    pm_carbon_density_plantation_ac(t,j,ac,"vegc")
    / sm_carbon_fraction
    * fm_aboveground_fraction("forestry")
    / sum(clcl, pm_climate_class(j,clcl) * fm_ipcc_bef(clcl));
```

(`presolve.gms:24-31`, same pattern for primforest, secdforest, other at lines 33-58)

This is a climate-weighted average of the IPCC Biomass Expansion Factor `fm_ipcc_bef(clcl)`, used to convert aboveground carbon to stem-only biomass. This affects timber harvest quantities (Modules 32, 35) — not crop yields (`vm_yld`). It is also parameterization: `fm_ipcc_bef` is read from the input file `f14_ipcc_bef.cs3` (`input.gms:69`) indexed by climate class. There is no mechanistic allometry computed in GAMS.

---

## (c) How M45 Feeds M59 SOM Dynamics

The pathway is:

`pm_climate_class(j,clcl)` (M45) → mapped to 4 SOM climate categories → used to select IPCC stock change factors → those factors determine cropland carbon equilibrium targets → which drive the dynamic convergence of soil organic carbon pools.

### Step 1: Climate aggregation (preloop)

Module 59's preloop (`cellpool_jan23/preloop.gms:16-89`) maps the 31 Köppen-Geiger types from M45 into 4 IPCC SOM climate categories defined in `sets.gms:22-24`:
- `temperate_dry`, `temperate_moist`, `tropical_dry`, `tropical_moist`

The aggregation pattern (documented in `module_45.md:163-165`):
```gams
sum(clcl_climate59(clcl,climate59), pm_climate_class(j,clcl))
```

This sums the area share of all Köppen types mapping to each SOM category, giving each cell a vector of SOM climate weights that sum to 1.

### Step 2: Carbon ratio calculation (preloop:60-67)

The climate weights select into IPCC stock change factors:

```gams
i59_cratio(j,kcr,w) = landuse_factor × tillage_factor × input_factor × irrigation_factor
```

Each factor is indexed by `climate59` (the 4-category set), so `pm_climate_class` drives the relative weight given to tropical vs. temperate factor values for cells straddling climate boundaries. The source tables are:
- `f59_cratio_landuse(i,climate59_2019,kcr)` from `f59_ch5_F_LU_2019reg.cs3` (IPCC 2019 Chapter 5, `input.gms:43-46`)
- `f59_cratio_tillage(climate59,tillage59)` from `f59_ch5_F_MG.csv` (`input.gms:49-52`) — default: `full_tillage = 1.0`
- `f59_cratio_inputs(climate59,inputs59)` from `f59_ch5_F_I.csv` (`input.gms:55-58`) — default: `medium_input = 1.0`
- `f59_cratio_irrigation(climate59,w,kcr)` from `f59_ch5_F_IRR.cs3` (`input.gms:65-69`)

**These factors are IPCC tabular parameters, not equations MAgPIE computes.** The soil decomposition physics is embedded in the IPCC 2019 tables; MAgPIE applies them as exogenous lookup values. This is parameterization, not mechanistic soil modeling.

### Step 3: Cropland SOM equilibrium target (equations.gms:20-27)

```gams
q59_som_target_cropland(j2) ..
  v59_som_target(j2,"crop") =e=
    (sum((kcr,w), vm_area(j2,kcr,w) * i59_cratio(j2,kcr,w)) + ...
     + vm_fallow(j2) * i59_cratio_fallow(j2)
     + vm_treecover(j2) * i59_cratio_treecover)
    * sum(ct,f59_topsoilc_density(ct,j2));
```

The equilibrium target = sum of crop areas weighted by their climate-conditioned carbon ratios × the natural topsoil carbon density for the cell. `pm_climate_class` enters here via `i59_cratio(j,kcr,w)`.

### Step 4: Dynamic convergence (equations.gms:46-52)

```gams
q59_som_pool(j2,land) ..
  v59_som_pool(j2,land) =e=
    sum(ct,i59_lossrate(ct)) * v59_som_target(j2,land)
    + (1 - sum(ct,i59_lossrate(ct))) *
      sum((ct,land_from), p59_carbon_density(ct,j2,land_from) *
          vm_lu_transitions(j2,land_from,land));
```

The actual SOM pool converges 15% of the gap toward equilibrium per year:
`i59_lossrate(t) = 1 - 0.85^m_yeardiff(t)` (`preloop.gms:45`)

Climate enters this equation only through `v59_som_target` (which depends on `i59_cratio`, which depends on `pm_climate_class`). The convergence rate itself (0.85) is climate-invariant.

### The second climate input to M59: topsoil carbon density

`f59_topsoilc_density(t,j)` is a separate LPJmL-derived input (file: `lpj_carbon_topsoil.cs2b`, `input.gms:77-86`). Under `c59_som_scenario = "cc"`, this parameter varies over time, meaning that the reference natural topsoil carbon pool — the denominator of all IPCC stock change factors — changes as climate changes the potential for carbon sequestration in natural vegetation. Under `"nocc"`, it is fixed at 1995 values.

This is **also parameterization**: LPJmL's prediction of how natural soil carbon changes under climate change is an external input. MAgPIE does not compute soil carbon-climate responses internally.

### Summary of the M45 → M59 pathway

```
pm_climate_class(j,clcl)          [M45, static 1976-2000 zones]
  ↓  mapping via clcl_climate59
climate59 weights per cell
  ↓  multiplied into IPCC tables
i59_cratio(j,kcr,w)               [parameterized, preloop:60-67]
  ↓  enters
v59_som_target(j,"crop")          [q59_som_target_cropland, equations.gms:20-27]
  ↓  drives
v59_som_pool(j,land)              [q59_som_pool, equations.gms:46-52]
  ↓  downstream
vm_nr_som(j) → M51 (N2O emissions)
vm_carbon_stock(j,land,"soilc",.) → M52 (carbon accounting)
```

The climate classification from M45 is **static throughout the simulation** (frozen at 1976-2000) and affects only which IPCC factor table values are applied per cell. It does not represent future climate change in SOM. Future climate change in SOM enters through the separate `f59_topsoilc_density` input and the `c59_som_scenario` switch.

---

## What Is NOT Happening

- MAgPIE does **not** simulate temperature, precipitation, CO2, or any atmospheric variable.
- Module 45 does **not** carry any RCP/SSP climate projection. Climate change cannot enter through reclassification.
- The climate-indexed parameters in M14 (`fm_ipcc_bef(clcl)`) and M52 (`f52_growth_par(clcl,...)`) have **no time dimension** — they are static biophysical lookup tables indexed by historical climate zone. No climate trajectory passes through these.
- Climate change effects on crop yields enter **only** through the time dimension of the LPJmL input file `lpj_yields.cs3`, pre-computed externally.
- Climate change effects on SOM enter **only** through the time dimension of `f59_topsoilc_density(t,j)`, also pre-computed from LPJmL externally.

---

## Source Statement

All claims 🟡 **Documented** — read this session from:
- `magpie-agent/modules/module_45.md` (full document)
- `magpie-agent/modules/module_14.md` (full document, particularly Sections 2, 4, 5, 6, 11)
- `magpie-agent/modules/module_14_notes.md`
- `magpie-agent/modules/module_59.md` (full document, particularly Sections 3, 5, 6, 10)
- `magpie-agent/modules/module_59_notes.md`
- `config/default.cfg` (lines 228, 360, 1474, 1930 — scenario switches verified directly)

Raw GAMS source not opened per task constraint; line numbers cited from AI docs and subject to drift. For high-stakes use, verify line numbers against current GAMS source.
