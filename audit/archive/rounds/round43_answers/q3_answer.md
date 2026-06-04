# Q3 Answer: Module 58 (Peatland) — GHG Emission Representation

**Question**: How does Module 58 (peatland) represent GHG emissions in MAgPIE?
- (a) Default realization and drivers of peatland area/emissions
- (b) MECHANISTIC or PARAMETERIZATION? Show the parameter/equation.
- (c) How do peatland emissions reach Module 52 (carbon) / Module 56 (GHG pricing)?

---

## (a) Default Realization and Drivers

**Default realization: `v2`**
Confirmed in `config/default.cfg`: `cfg$gms$peatland <- "v2"`. The alternative `off` disables the module entirely.

Module 58 (`v2`) tracks peatland area across **seven discrete states**: intact, crop (drained for cropland), past (drained for pasture), forestry (drained for plantation), peatExtract (active extraction), unused (drained but unmanaged), and rewetted (restored). Source: `modules/58_peatland/v2/sets.gms:10-11`.

**What drives peatland area changes:**

Area transitions are driven by **managed land dynamics from Modules 10 (land) and 32 (forestry)** via a proportional scaling-factor mechanism. The core equation is `q58_peatlandMan` (`equations.gms:46-50`):

```
v58_peatland(j, manPeat58) =
  pc58_peatland(j, manPeat58)
  + v58_manLandExp(j, manPeat58) * p58_scalingFactorExp(j)
  - v58_manLandRed(j, manPeat58) * p58_scalingFactorRed(j, manPeat58)
  +/- balance terms
```

- **p58_scalingFactorExp** = available peatland / available non-managed land — the fraction of new land expansion expected to drain peatland
- **p58_scalingFactorRed** = drained peatland of type X / total peatland — the fraction of land abandonment expected to rewet peatland of that type

These scaling factors are computed each timestep in `presolve.gms:54-75`. There is no endogenous optimisation over *where* drainage occurs spatially; location is governed by the proportionality rule.

Total peatland area is **conserved** by `q58_peatland` (`equations.gms:12-13`): land transitions between states, is never created or destroyed.

**Historical fixing:** Before `s58_fix_peatland` (default 2020), all peatland areas are fixed to input data (`presolve.gms:9-32`). Dynamic optimization begins after this year.

**What drives emissions:** Emissions are a function of the **optimized peatland area by state** (v58_peatland) combined with exogenous emission factors. The area endogenously responds to land-use pressures and (when activated) GHG pricing — but the per-hectare emission rate is entirely exogenous.

---

## (b) Mechanistic Modeling or Parameterization?

**This is parameterization, not mechanistic modeling.**

Module 58 applies **exogenous, climate-zone-specific, IPCC-derived per-area emission factors** to optimized peatland areas. There is no mechanistic representation of soil carbon decomposition, water table dynamics, or biogeochemical processes. The emission rate per hectare is fixed (read from an input file); only the area is optimized.

**The emission equation** (`q58_peatland_emis_detail`, `equations.gms:84-87`):

```gams
v58_peatland_emis(j2, land58, emis58) =e=
  sum(clcl58,
    v58_peatland(j2, land58) *
    p58_mapping_cell_climate(j2, clcl58) *
    f58_ipcc_wetland_ef(clcl58, land58, emis58)
  );
```

This is purely: **Area × climate-zone indicator × emission factor**.

**Key parameters:**

- `f58_ipcc_wetland_ef(clcl58, land58, emis58)` — the exogenous emission factor table (`modules/58_peatland/input/f58_ipcc_wetland_ef2.cs3`). Dimensions: 3 climate zones (tropical, temperate, boreal) × 7 peatland states × 4 gases (co2, doc, ch4, n2o). Units: t C or t N per ha per year. Sources: IPCC Wetlands 2014, Tiemeyer et al. 2020, Wilson et al. 2016. These are read-only, static, time-invariant input parameters — they do not change with model state.

- `p58_mapping_cell_climate(j, clcl58)` — a binary cell-to-climate-class mapping, derived from `pm_climate_class(j, clcl)` from Module 45 (`preloop.gms:36`).

**Example factors** from the input file:
| Climate | State | CO2 (t C/ha/yr) | CH4 (t CH4/ha/yr) | N2O (t N/ha/yr) |
|---------|-------|-----------------|-------------------|-----------------|
| Tropical | crop | 14.0 | 0.007 | 0.005 |
| Temperate | crop | 9.5 | 0.0206 | 0.0111 |
| Boreal | rewetted | -0.34 | 0.041 | 0.0001 |

**Three-check verification:**

1. **Equation check:** `q58_peatland_emis_detail` *calculates* emissions, but via `area * fixed_factor` — no biogeochemical state is being simulated.
2. **Source check:** `f58_ipcc_wetland_ef` is loaded from `$include ./input/...` — it is an exogenous parameter read at input phase.
3. **Feedback check:** The emission rate does not change with model state (no water table variable, no decomposition pool). Only the area (v58_peatland) is endogenous.

**Correct statement:** "MAgPIE applies exogenous IPCC-derived per-area emission factors scaled by optimized peatland area and climate zone." Not: "MAgPIE models peatland GHG processes."

**One structural nuance:** DOC (dissolved organic carbon) is tracked as a separate gas (`doc` in `emis58`) and mapped to `co2_c` via `emisSub58_to_poll58` (`sets.gms:39-43`). This means CO2 and DOC both contribute to the `co2_c` pollutant total, but both are applied as fixed per-area rates — not simulated.

**Intact peatland EF override:** In the raw input data, intact peatland has no emission factor entries (zero by default). The preloop sets intact EFs equal to rewetted EFs (`preloop.gms:43`): `f58_ipcc_wetland_ef(clcl58,"intact",emis58) = f58_ipcc_wetland_ef(clcl58,"rewetted",emis58)`. This prevents the optimizer from exploiting zero EFs to artificially favour intact→rewetted conversion.

---

## (c) How Peatland Emissions Reach M52 and M56

### Route to Module 56 (GHG Policy) — direct

Module 58 writes to the interface variable `vm_emissions_reg(i,"peatland",poll58)` via equation `q58_peatland_emis` (`equations.gms:91-94`):

```gams
vm_emissions_reg(i2, "peatland", poll58) =e=
  sum((cell(i2,j2), land58, emisSub58_to_poll58(emisSub58, poll58)),
    v58_peatland_emis(j2, land58, emisSub58));
```

This aggregates cell-level (j) emissions to region (i) and maps the 4-gas internal set to the 3 policy gases (`poll58 = {co2_c, ch4, n2o_n_direct}`). Declaration: `preloop.gms:31-33`.

Module 56 (`price_aug22`) then reads `vm_emissions_reg(i, "peatland", poll58)` in `q56_emis_pricing` (`equations.gms:15-17`). "Peatland" is an `emis_annual` source (recurring annual emissions, not a one-off stock depletion), so it enters the annual emission pricing equation — not the stock-change CO2 path. The cost per unit is determined by `im_pollutant_prices(t,i,pollutants,"peatland")`, which is configured by the `c56_emis_policy` matrix and the `c56_pollutant_prices` scenario. Under the default policy "reddnatveg_nosoil", peatland emissions ARE included in pricing (the policy matrix has `f56_emis_policy("reddnatveg_nosoil",...,"peatland") = 1` for peatland — confirmed in `module_56.md:§3.7`). Source: `modules/56_ghg_policy/price_aug22/equations.gms:12-17`.

**Important:** The default price scenario `R34M410-SSP2-NPi2025` is near-zero through 2025-2030, so in baseline runs the policy routing exists but peatland emission costs are near-zero in the near term.

### Route to Module 52 (Carbon) — there is none

**Module 58 does not write to Module 52 and Module 52 does not read from Module 58.**

Module 52 (`normal_dec17`) calculates LULUCF CO2 from land-use change using carbon stock differences (equation `q52_emis_co2_actual`, `equations.gms:16-19`). It reads `vm_carbon_stock(j,land,c_pools,"actual")` populated by Modules 29, 31, 32, 34, 35, and 59. Module 58 does NOT populate `vm_carbon_stock`. Peatland soil/vegetation carbon stocks are not tracked in a carbon pool that feeds M52. This is explicitly noted in `module_56.md:§4.1`: "Module 58 (peatland) does NOT populate [vm_carbon_stock]."

The conceptual reason is documented in M58's limitations (`module_58.md:§13.1`): "No carbon stock accounting — organic carbon stocks in peatlands are not accounted for." Peatland emissions enter Module 56 directly via `vm_emissions_reg`, bypassing the carbon stock accounting path entirely.

**Summary diagram:**

```
M58 (v2, equations.gms:84-94)
  v58_peatland_emis  =  area  ×  f58_ipcc_wetland_ef  (PARAMETERIZATION)
          |
          v
  vm_emissions_reg(i,"peatland",poll58)
          |
          +-----> M56 (q56_emis_pricing) -> emission cost -> M11 (objective)
          |
          X  (no link to M52 or vm_carbon_stock)
```

---

## Closing Source Statement

All claims are 🟡 **documented** — sourced from AI documentation read this session:

- Primary source: `modules/module_58.md` (§3.4, §6.4, §7.6, §10.2, §12, §13, §14)
- Supporting: `modules/module_56.md` (§2.1, §3.7, §4.1-4.2)
- Supporting: `modules/module_52.md` (§3)
- Config verification: `config/default.cfg` (peatland <- "v2")

No raw `.gms` files were opened; all claims are from verified AI documentation. Line-number citations from docs were last verified at the doc's last sync date and may drift with code evolution.

---

## Doc Wished Existed

A **cross-module "emission accounting map"** showing, for every emission source (peatland, soil N, livestock CH4, LULUCF CO2, etc.): (1) which module computes it, (2) via `vm_emissions_reg` vs. `vm_carbon_stock` vs. neither, (3) whether it is `emis_annual` or `emis_oneoff` in M56's eyes, and (4) which `c56_emis_policy` entries control its pricing. This is currently fragmented across module_56.md, module_52.md, module_58.md, and other emission modules. The distinction between the stock-change CO2 path (M52 → vm_carbon_stock → M56 q56_emis_pricing_co2) and the direct `vm_emissions_reg` path (M58 and others → M56 q56_emis_pricing) is easy to conflate without such a map.
