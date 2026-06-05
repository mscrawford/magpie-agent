# P2: vm_carbon_stock — Dimensions, Pools, Land Types, Declaration vs Population

---

## 1. Exact Declaration

`vm_carbon_stock` is declared in **Module 56 (GHG Policy)**, realization `price_aug22`:

> **`vm_carbon_stock(j, land, c_pools, stockType)`** — current timestep carbon stock (mio. tC)
> `modules/56_ghg_policy/price_aug22/declarations.gms:34`

🟡 Source: module_52.md (Interface Variables, p. 415–424) + module_56.md (§4.1, p. 578–584)

---

## 2. Exact Index Domain (4 dimensions)

| Position | Set | Members | Notes |
|----------|-----|---------|-------|
| 1 | `j` | Simulation cells (200 clusters) | Spatial unit |
| 2 | `land` | crop, past, primforest, secdforest, urban, other, (plant_pri, plant_sec) | All land types tracked by Module 52 |
| 3 | `c_pools` | vegc, litc, soilc | Verified: `core/sets.gms:324–325` |
| 4 | `stockType` | "actual", "actualNoAcEst" | Stock type; equations typically use the "actual" slice |

The `stockType` dimension is critical for Module 56's pricing equation: `c56_carbon_stock_pricing` (default `"actualNoAcEst"`) governs which slice enters pricing.
`module_56.md:§2.2, equations.gms:19–22`

🟡 Source: module_52.md:415–424; cross_module/carbon_balance_conservation.md:101; module_56.md:108–116

---

## 3. Carbon Pools

Three pools span ALL land types in `vm_carbon_stock`:

### 3.1 `vegc` — Vegetation Carbon
Above-ground and below-ground live biomass. For forests and plantations this grows over decades following the Chapman-Richards equation (Module 52, `core/macros.gms:18`); for croplands it is essentially annual-crop biomass from LPJmL; for primary forest it is fixed at equilibrium.

### 3.2 `litc` — Litter Carbon
Dead plant material not yet decomposed to soil. For age-class land types (plantations, secondary forest, other land), litter converges linearly to equilibrium over 20 years (IPCC assumption). For non-age-class land types it comes directly from LPJmL input.
`module_52.md: macros.gms:20; start.gms:19–20,30–31`

### 3.3 `soilc` — Soil Organic Carbon
Soil organic matter. This pool in `vm_carbon_stock` is **written by Module 59 (SOM)**, not by Module 52. Module 59 (`cellpool_jan23`) assembles the soilc slice via equation `q59_carbon_soil` (`modules/59_som/cellpool_jan23/equations.gms:61–64`): topsoil dynamic pool (`v59_som_pool`) + static subsoil density (`i59_subsoilc_density`, derived from Module 52's `fm_carbon_density`). Module 52 provides the underlying `fm_carbon_density` but does NOT itself write the soilc slice.

Key limitation: age-class-specific carbon densities (`pm_carbon_density_secdforest_ac`, `pm_carbon_density_plantation_ac`, `pm_carbon_density_other_ac`) cover only `ag_pools` (vegc and litc) — **soilc is NOT age-class-specific** in Module 52.
`module_52.md:919–922; carbon_balance_conservation.md:94–101`

🟡 Source: cross_module/carbon_balance_conservation.md:§2 + §7.2; module_52.md:§4 (Limitations, "Only above-ground pools")

---

## 4. Land Types

`vm_carbon_stock` covers all 7 operational land types:

| Land type | vegc | litc | soilc populator | Notes |
|-----------|------|------|-----------------|-------|
| `crop` | LPJmL annual crops | LPJmL | Module 59 (dynamic IPCC 2019) | Module 30 computes `vm_carbon_stock_croparea`; Module 29 folds it in via `q29_carbon` |
| `past` | LPJmL grassland | LPJmL | Module 59 (assumed constant = natural density) | Grazing does not affect C |
| `forestry` (plantations) | Chapman-Richards growth, age-class | Linear 20-yr, age-class | Module 59 (converges to natural density) | Module 32 populates this slice |
| `primforest` | LPJmL mature (static) | LPJmL (static) | Module 52 via LPJmL | Module 35 populates; no age-class dynamics |
| `secdforest` | Chapman-Richards growth, age-class | Linear 20-yr, age-class | Module 59 | Module 35 populates |
| `other` | Chapman-Richards growth, age-class | Linear 20-yr, age-class | Module 59 | Module 35 populates |
| `urban` | **Fixed to 0** | **Fixed to 0** | soilc set to "other" land value | Module 34 does `.fx(j,"urban",ag_pools,stockType) = 0` (`presolve.gms:8`) |

`module_52.md:§1 (land types); cross_module/carbon_balance_conservation.md:§3; module_56.md:583`

---

## 5. How Carbon Stock is Computed from Carbon Density and Area

The governing formula for each land type is:

```
vm_carbon_stock(j, land, c_pools, "actual") [mio. tC]
    = carbon_density(j, land, c_pools) [tC/ha]
    × vm_land(j, land)                 [mio. ha]
```

The multiplication is performed inside the land modules (29, 31, 32, 35) that populate each land-type slice. For example:

- **Cropland** (`q29_carbon`): `vm_carbon_stock(j2,"crop",c_pools,"actual") =e= sum(kcr,w, fm_carbon_density(t,j2,"crop",c_pools) * vm_area(j2,kcr,w))` (simplified; actual equation at `modules/29_cropland/detail_apr24/equations.gms:39`)
- **Forestry** (Module 32): sums `pm_carbon_density_plantation_ac(t,j,ac,c_pools) × v32_land(j,ac,...)` over age classes
- **Natural vegetation** (Module 35): sums `pm_carbon_density_secdforest_ac(t,j,ac,c_pools) × v35_secdforest(j,ac)` over age classes, plus uses `fm_carbon_density` for primforest

The key conceptual split:
- **Module 52** provides the density parameters (`fm_carbon_density`, `pm_carbon_density_*_ac`).
- **Land modules (29, 31, 32, 34, 35)** multiply density by area and write the result into `vm_carbon_stock`.
- **Module 59** overwrites the `soilc` slice for all land types.

Unit result: (tC/ha) × (mio. ha) = mio. tC — consistent with the `vm_carbon_stock` unit declaration.

🟡 Source: module_52.md:§3 (q52_emis_co2_actual components, p. 349–350); carbon_balance_conservation.md:§7.5 (p. 592–616)

---

## 6. Declaration vs. Population: Which Module Does What

### Declares `vm_carbon_stock`

**Module 56 (GHG Policy)** — `price_aug22` realization:
> `modules/56_ghg_policy/price_aug22/declarations.gms:34`

This is the single authoritative declaration. Module 56 is also the module that updates the companion parameter `pcm_carbon_stock` (previous timestep's carbon stock), storing `vm_carbon_stock.l` after each solve for use in the next timestep's emission equation.

### Populates `vm_carbon_stock`

Different land-type and pool slices are written by different modules:

| Slice | Module | File/Equation | Notes |
|-------|--------|---------------|-------|
| `(j,"crop",c_pools,"actual")` | **Module 29** (Cropland) | `q29_carbon`, `modules/29_cropland/detail_apr24/equations.gms:39` | Folds in `vm_carbon_stock_croparea` from M30 |
| `(j,"past",c_pools,"actual")` | **Module 31** (Pasture) | pasture equations | Uses `fm_carbon_density` from M52 |
| `(j,"forestry",c_pools,"actual")` | **Module 32** (Forestry) | `modules/32_forestry/dynamic_may24/equations.gms` | Age-class-weighted sum |
| `(j,"urban",ag_pools,stockType)` | **Module 34** (Urban) | `.fx` bound in `modules/34_urban/exo_nov21/presolve.gms:8` — fixed to 0 | Hard-fixed, not an equation |
| `(j,"primforest",c_pools,"actual")`, `(j,"secdforest",...)`, `(j,"other",...)` | **Module 35** (Natural Veg) | `modules/35_natveg/pot_forest_may24/equations.gms` | Age-class dynamics for secdforest/other |
| `soilc` slice for ALL land types | **Module 59** (SOM) | `q59_carbon_soil`, `modules/59_som/cellpool_jan23/equations.gms:61–64` | Topsoil (`v59_som_pool`) + subsoil (`i59_subsoilc_density`) |

**Module 52 (Carbon)** is the data provider for densities but does NOT populate `vm_carbon_stock` directly. It reads `vm_carbon_stock` in equation `q52_emis_co2_actual` to compute CO2 emissions.

**Module 58 (Peatland)** does NOT populate `vm_carbon_stock` — peatland emissions enter `vm_emissions_reg` via a separate pathway.

🟡 Source: module_52.md:415–424; module_56.md:§4.1 (p. 578–584); carbon_balance_conservation.md:§7.5 (p. 592–616)

---

## 7. Use in the Emission Equation

Module 52's single equation reads `vm_carbon_stock` to compute CO2 emissions:

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

`modules/52_carbon/normal_dec17/equations.gms:16–19`

And Module 56's pricing equation also reads `vm_carbon_stock` directly (bypassing `vm_emissions_reg`), using the configurable `stockType` slice:

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

`modules/56_ghg_policy/price_aug22/equations.gms:19–22`

The difference between these two equations is the `stockType` argument: Module 52 always uses `"actual"` for emission reporting; Module 56 uses the configurable `c56_carbon_stock_pricing` (default `"actualNoAcEst"`, which excludes afforestation establishment to avoid double-counting with CDR rewards).

---

## Summary

- **Declaration**: `vm_carbon_stock(j, land, c_pools, stockType)` — declared at `modules/56_ghg_policy/price_aug22/declarations.gms:34`; units mio. tC; 4 dimensions.
- **Carbon pools**: vegc (live biomass), litc (litter), soilc (soil organic matter) — all three span all land types; `core/sets.gms:324–325`.
- **Land types**: all 7 (crop, past, forestry, primforest, secdforest, urban, other); urban is hard-fixed to 0 for vegc and litc.
- **Density × area formula**: each land module multiplies Module 52-supplied carbon density parameters by its own land area variable and writes the result into `vm_carbon_stock`.
- **Populated by**: M29 (crop), M31 (past), M32 (forestry), M34 (urban, .fx = 0), M35 (primforest/secdforest/other), M59 (soilc for all land types). Module 52 reads it; it does not write it.
- **Module 52's role**: central density provider and CO2 emission calculator — it is a consumer of `vm_carbon_stock`, not a populator.

---

**Source statement**: All claims from AI documentation — 🟡 `modules/module_52.md` (Interface Variables §, Limitations §4), 🟡 `modules/module_56.md` (§2.2, §4.1), 🟡 `cross_module/carbon_balance_conservation.md` (§2, §3, §7.2, §7.5). No raw GAMS code read this session.
