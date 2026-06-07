# Round 49 Answer: Soil and Peatland Carbon in MAgPIE's Carbon Accounting

**Question**: How does module 59 (SOM) contribute the soilc pool, and how does module 58 (peatland) account for peatland carbon and its emissions? Are these part of vm_carbon_stock or a separate emission stream, which equations compute them, and how do they enter the GHG emission totals? Name the variables/equations, distinguish declared versus populated, and cite file:line.

---

## Overview: Two Entirely Different Accounting Architectures

Module 59 (SOM) and Module 58 (peatland) use fundamentally different approaches:

- **M59** maintains a dynamic carbon stock pool that feeds directly into `vm_carbon_stock`, from which CO2 emissions are derived by Module 52's stock-change equation. It is inside the `vm_carbon_stock` system.
- **M58** tracks no organic carbon stock at all. It computes GHG emissions directly from peatland area multiplied by IPCC emission factors and routes them straight to `vm_emissions_reg`, bypassing `vm_carbon_stock` entirely.

The two modules are independent; `module_59.md` Section 14 explicitly states "No direct interaction in current implementation" between them.

---

## Module 59 (SOM): soilc Pool via vm_carbon_stock

### What it tracks

M59 (realization `cellpool_jan23`, default confirmed in `config/default.cfg`) tracks topsoil organic carbon in `v59_som_pool(j,land)`, a locally declared positive variable (`declarations.gms:` within the M59 realization). This is the only dynamically modeled soil carbon component. Subsoil carbon is represented by a static parameter `i59_subsoilc_density(t,j)`, derived once in preloop from `fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j)` (`preloop.gms:12`).

### The critical interface equation: q59_carbon_soil

The equation that plugs M59 into the wider carbon accounting system is:

**`q59_carbon_soil(j2,land,stockType)`** (`equations.gms:61-64`):
```gams
vm_carbon_stock(j2, land,"soilc",stockType) =e=
    v59_som_pool(j2, land) +
    vm_land(j2, land) * sum(ct,i59_subsoilc_density(ct,j2));
```

- **`vm_carbon_stock`** is DECLARED elsewhere (documented as declared at `modules/56_ghg_policy/price_aug22/declarations.gms:34`, 4-dimensional: j x land x c_pools x stockType); M59 **populates** its `"soilc"` slice for all land types via this equation.
- `v59_som_pool` is both declared and populated within M59.
- The result: total soilc = dynamic topsoil pool + static subsoil area term.

### How the soilc pool is computed

**Cropland equilibrium target** (`q59_som_target_cropland`, `equations.gms:20-27`):
```gams
v59_som_target(j2,"crop") =e=
    (sum((kcr,w), vm_area(j2,kcr,w) * i59_cratio(j2,kcr,w))
     + sum((kcr,w,ct), vm_area(j2,kcr,w) * i59_scm_target(ct,j2)
           * i59_cratio(j2,kcr,w) * (i59_cratio_scm(j2) - 1))
     + vm_fallow(j2) * i59_cratio_fallow(j2)
     + vm_treecover(j2) * i59_cratio_treecover)
    * sum(ct,f59_topsoilc_density(ct,j2));
```

**Non-cropland equilibrium target** (`q59_som_target_noncropland`, `equations.gms:31-34`):
```gams
v59_som_target(j2,noncropland59) =e=
    vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2));
```
Non-cropland is assumed to maintain natural carbon density (a limitation noted in `realization.gms:21-24`).

**Actual pool (dynamic convergence)** (`q59_som_pool`, `equations.gms:46-52`):
```gams
v59_som_pool(j2,land) =e=
    sum(ct,i59_lossrate(ct)) * v59_som_target(j2,land)
    + (1 - sum(ct,i59_lossrate(ct))) *
      sum((ct,land_from), p59_carbon_density(ct,j2,land_from) *
        vm_lu_transitions(j2,land_from,land));
```

The convergence rate is: `i59_lossrate(t) = 1 - 0.85^m_yeardiff(t)` (`preloop.gms:45`), giving ~56% convergence over a 5-year timestep, ~80% over 10 years. The land-use transition matrix `vm_lu_transitions` is used so that when land converts between types, the legacy carbon density from the source type carries forward proportionally.

### How M59 soilc emissions enter the GHG totals

M59 does **not** compute CO2 emissions directly. Once `vm_carbon_stock(j,land,"soilc",stockType)` is populated by `q59_carbon_soil`, it flows into Module 52's stock-change equation:

**`q52_emis_co2_actual`** (`modules/52_carbon/normal_dec17/equations.gms:16-19`):
```gams
vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length
    );
```

This means soil carbon loss (e.g., from cropland expansion reducing `v59_som_pool`) manifests as a positive emission in `vm_emissions_reg`, keyed to the relevant `emis_oneoff` source (e.g., `crop_soilc`). The `emis_land` set at `core/sets.gms:332-354` maps each emis_oneoff to the (land, c_pools) pair. M52 then routes this to Module 56 (GHG policy) for carbon pricing.

### M59 secondary interface variables

M59 also DECLARES and POPULATES two interface variables that affect nitrogen accounting (not the soilc pool directly):
- **`vm_nr_som(j)`** (declared `declarations.gms:45`; equation `q59_nr_som`, `equations.gms:69-75`): nitrogen released from SOM turnover, consumed by Module 51 for N2O emissions.
- **`vm_nr_som_fertilizer(j)`** (declared `declarations.gms:46`; equations `q59_nr_som_fertilizer` and `q59_nr_som_fertilizer2`): plant-available N subset, consumed by Module 50 for the soil nitrogen budget.

And one cost variable:
- **`vm_cost_scm(j)`** (declared `declarations.gms:41`; equation `q58_peatland_cost_annuity` - wait, correct reference: `q59_cost_scm`, `equations.gms:98-101`): soil carbon management costs to Module 11.

---

## Module 58 (Peatland): Direct Emission Stream, No vm_carbon_stock

### Critical architectural distinction

M58 (realization `v2`, default confirmed in `config/default.cfg`) does **not** track peatland organic carbon stocks. This is stated explicitly in the documentation: "No carbon stock accounting: Organic carbon stocks in peatlands are not accounted for" (`realization.gms:31-32`). M58 computes GHG emissions directly from area x emission factor, completely outside the `vm_carbon_stock` system.

### What M58 tracks

M58 tracks peatland **area** across 7 states in `v58_peatland(j,land58)`, declared as a positive variable in `declarations.gms:50`. The seven states (defined in `sets.gms:10-11`) are:
- `intact`, `crop`, `past`, `forestry`, `peatExtract`, `unused`, `rewetted`

### Emission calculation: two-step process

**Step 1 - Cell-level emissions by state and gas** (`q58_peatland_emis_detail`, `equations.gms:84-87`):
```gams
v58_peatland_emis(j2,land58,emis58) =e=
    sum(clcl58, v58_peatland(j2,land58) *
    p58_mapping_cell_climate(j2,clcl58) * f58_ipcc_wetland_ef(clcl58,land58,emis58))
```

- `v58_peatland_emis(j,land58,emis58)` is DECLARED and POPULATED within M58 (`declarations.gms:46`; free variable, can be negative for CO2 sequestration).
- `f58_ipcc_wetland_ef(clcl58,land58,emis58)` is loaded from `modules/58_peatland/input/f58_ipcc_wetland_ef2.cs3`, with dimensions: 3 climate classes x 7 peatland states x 4 gases (co2, doc, ch4, n2o). Units are t C/ha/yr (CO2, DOC) or t N/ha/yr (N2O) or t CH4/ha/yr.
- `p58_mapping_cell_climate(j,clcl58)` is a binary cell-to-climate-class mapping (`declarations.gms:13`; populated in `preloop.gms:36` from `pm_climate_class`).

**Important preloop manipulation** (`preloop.gms:43`): The raw input file has no entries for `intact` peatland (zero EFs by default). The preloop explicitly sets `f58_ipcc_wetland_ef(clcl58,"intact",emis58) = f58_ipcc_wetland_ef(clcl58,"rewetted",emis58)` to prevent the optimizer from artificially converting intact to rewetted to exploit zero EFs.

**Step 2 - Regional aggregation and gas mapping** (`q58_peatland_emis`, `equations.gms:91-94`):
```gams
vm_emissions_reg(i2,"peatland",poll58) =e=
    sum((cell(i2,j2),land58,emisSub58_to_poll58(emisSub58,poll58)),
        v58_peatland_emis(j2,land58,emisSub58))
```

- `vm_emissions_reg` is DECLARED by Module 56 (or the ghg_policy module); M58 **populates** the `"peatland"` source slice.
- The mapping `emisSub58_to_poll58` (`sets.gms:39-43`) aggregates: both `co2` and `doc` (dissolved organic carbon) → `co2_c`; `ch4` → `ch4`; `n2o` → `n2o_n_direct`.
- Non-peatland pollutants are fixed to zero at `preloop.gms:31`.

The three gases (co2_c, ch4, n2o_n_direct) then go to Module 56 (GHG policy) for carbon pricing via `vm_emissions_reg`. This is a direct route to the GHG total, not mediated by `vm_carbon_stock` at all.

### Peatland area dynamics (how v58_peatland is determined)

The core dynamics equation is **`q58_peatlandMan`** (`equations.gms:46-50`; only active after `s58_fix_peatland` = year 2020 by default):
```gams
v58_peatland(j2,manPeat58) =e=
    pc58_peatland(j2,manPeat58)
    + v58_manLandExp(j2,manPeat58) * sum(ct, p58_scalingFactorExp(ct,j2)) - v58_balance(j2,manPeat58)
    - v58_manLandRed(j2,manPeat58) * sum(ct, p58_scalingFactorRed(ct,j2,manPeat58)) + v58_balance2(j2,manPeat58)
```

Land expansion and reduction from Modules 10 (land) and 32 (forestry) drive peatland drainage and rewetting through the scaling factor mechanism. Total peatland area is conserved by `q58_peatland` (`equations.gms:12-13`).

### Peatland costs

`vm_peatland_cost(j)` is DECLARED within M58 (`declarations.gms:45`; free variable) and populated by `q58_peatland_cost` (`equations.gms:71-75`). It goes to Module 11 (costs). Default cost parameters: one-time rewetting = 1230 USD17MER/ha, recurring rewetting = 37 USD17MER/ha/yr, recurring drainage = 0.

---

## Summary Table: Architecture Comparison

| Aspect | M59 (SOM) | M58 (Peatland) |
|--------|-----------|----------------|
| Carbon stock variable | `v59_som_pool(j,land)` - declared + populated in M59 | None - no organic carbon stock |
| vm_carbon_stock role | M59 POPULATES the soilc slice via `q59_carbon_soil` | Not populated; M58 bypasses it entirely |
| CO2 emission pathway | Stock change computed by M52 (`q52_emis_co2_actual`) | Direct area x EF, M58 POPULATES `vm_emissions_reg("peatland",co2_c)` |
| GHG entry point | vm_emissions_reg via M52's stock-change equation | vm_emissions_reg via M58's `q58_peatland_emis` directly |
| Module 56 (GHG policy) receives | co2_c from M52 (soilc source within the land-use change accounting) | co2_c, ch4, n2o_n_direct from M58 (peatland source) |
| Key populating equation | `q59_carbon_soil` (`equations.gms:61-64`) | `q58_peatland_emis` (`equations.gms:91-94`) |
| Climate dependence | IPCC 2019 stock change factors by 4-zone climate | IPCC EFs by 3-zone climate (tropical/temperate/boreal) |
| Dynamic mechanism | 15% annual convergence toward equilibrium | Scaling factors tied to land expansion/reduction |

---

## Key Declared vs Populated Distinctions

### vm_carbon_stock
- **Declared**: `modules/56_ghg_policy/price_aug22/declarations.gms:34` (4D: j x land x c_pools x stockType)
- **soilc slice populated by**: M59 via `q59_carbon_soil` (`modules/59_som/cellpool_jan23/equations.gms:61-64`)
- **Other slices populated by**: M29 (crop), M31 (past), M32 (forestry), M34 (urban, fixed zero), M35 (primforest/secdforest/other) for the vegc and litc pools

### vm_emissions_reg
- **Declared**: Module 56 (ghg_policy)
- **Populated for land-use CO2 (including soilc)**: M52 via `q52_emis_co2_actual` (`modules/52_carbon/normal_dec17/equations.gms:16-19`)
- **Populated for peatland gases**: M58 via `q58_peatland_emis` (`modules/58_peatland/v2/equations.gms:91-94`); source label is `"peatland"`, pollutants `co2_c`, `ch4`, `n2o_n_direct`

### v59_som_pool (internal to M59)
- **Declared**: within M59 realization (`cellpool_jan23/declarations.gms`)
- **Populated by**: `q59_som_pool` (`equations.gms:46-52`)

### v58_peatland (internal to M58)
- **Declared**: `modules/58_peatland/v2/declarations.gms:50` (positive variable)
- **Populated by**: `q58_peatlandMan` (dynamic period), or fixed by presolve during historical period (until year 2020)

---

## Critical Limitations

**M59**: Pastures and non-cropland land types are assumed to maintain natural carbon density (`realization.gms:21-24`). Subsoil carbon is static. Default tillage = full tillage, default inputs = medium, both reducing soil carbon vs. no-till or high-input management.

**M58**: No dynamic carbon stock is tracked - only area x emission factor. This means large historical changes in peatland carbon stock depth are not represented. The module's own documentation (`realization.gms:31-32`) explicitly lists "No carbon stock accounting" as a limitation. Fire emissions from drained peatlands are also not included.

**Separation**: The two modules do not interact. M59's IPCC 2019 methodology was designed for mineral soils; peatland mineral soil dynamics, if any cell contains both peat and mineral soil fractions, are not cleanly separated.

---

## Epistemic Status

All factual claims in this answer are 🟡 **Documented** - drawn from:
- `modules/module_59.md` (verified 2026-03-06)
- `modules/module_58.md` (verified 2026-03-06)
- `cross_module/carbon_balance_conservation.md` (verified 2025-10-22)

No raw GAMS source code was read in this session per the question constraints. Line numbers cited match those in the AI documentation as of its last verification date; code changes since then may have shifted them. For the highest-stakes claims (especially the declaration location of `vm_carbon_stock`), verify against current code before acting.
