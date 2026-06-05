# P1: Carbon Conservation When Land Is Converted

**Question**: In MAgPIE, when land is converted between uses (e.g. forest → cropland), how is the change in carbon stock computed and accounted for so that carbon is conserved (i.e. a stock loss becomes a CO2 emission rather than vanishing)? Trace the conservation accounting: which equation(s) compute the stock change, where does the released carbon go, and which carbon pools are tracked? Name the variables/equations and cite file:line.

---

## Framing: "Conservation" in MAgPIE

🟡 First, a precision point from the docs. The carbon system is **stock-flow accounting, not a strict conservation law**. Unlike land area (which is conserved by constraint `q10_land_area`) or water, carbon is an open system: it can leave as CO₂ to the atmosphere or be sequestered from it. The accounting ensures that every ton of carbon that disappears from a terrestrial stock is registered as a CO₂ emission — it does not "vanish" unaccounted — but the total is not required to be constant.

`cross_module/carbon_balance_conservation.md §1, §11.1`

---

## Step 1 — Three carbon pools are tracked for every land type

🟡 MAgPIE tracks three carbon pools for each of the seven land types:

| Pool | Code | Description |
|------|------|-------------|
| Vegetation carbon | `vegc` | Above-ground and below-ground live biomass |
| Litter carbon | `litc` | Dead plant material, not yet decomposed |
| Soil carbon | `soilc` | Soil organic matter |

**Set declaration**: `c_pools` set, `core/sets.gms:324–325`.

**Land types** in the emissions mapping: `crop`, `past`, `forestry`, `primforest`, `secdforest`, `urban`, `other`.  
This yields 21 emission source slots (7 land × 3 pools), indexed by the `emis_oneoff` set and mapped through `emis_land(emis_oneoff,land,c_pools)` (`core/sets.gms:332–335`).

`modules/module_52.md §3`

---

## Step 2 — Land-module equations populate `vm_carbon_stock`

🟡 The central interface variable is:

```
vm_carbon_stock(j, land, c_pools, stockType)     [declared in Module 56]
```

declared at `modules/56_ghg_policy/price_aug22/declarations.gms:34`, dimension: cell × land × carbon pool × stock type (typically `"actual"`).

Each land module **writes its own slice** of this variable:

| Land type(s) | Writing module | Key equation |
|---|---|---|
| `primforest` | Module 35 | `q35_carbon_primforest` (`equations.gms:42–44`): `vm_carbon_stock(j,"primforest",ag_pools,stockType) =e= m_carbon_stock(vm_land, fm_carbon_density, "primforest")` |
| `secdforest` | Module 35 | `q35_carbon_secdforest` (`equations.gms:49–51`): area × blended age-class density `p35_carbon_density_secdforest` |
| `other` | Module 35 | `q35_carbon_other` (`equations.gms:53–55`) |
| `crop` | Module 29 | `q29_carbon` (`modules/29_cropland/detail_apr24/equations.gms:39`): aggregates `vm_carbon_stock_croparea` from Module 30 |
| `past` | Module 31 | Pasture area × `fm_carbon_density` (`modules/31_past/endo_jun13/equations.gms:24`) |
| `forestry` | Module 32 | Plantation age-class area × `pm_carbon_density_plantation_ac` |
| `urban` | Module 34 | Fixed to zero: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` (`modules/34_urban/exo_nov21/presolve.gms:8`) |
| **soilc slice (all land types)** | Module 59 | `q59_carbon_soil` (`modules/59_som/cellpool_jan23/equations.gms:61–64`): topsoil pool `v59_som_pool` + subsoil density `i59_subsoilc_density` |

**Carbon density source**: `fm_carbon_density(t_all,j,land,c_pools)` — LPJmL output file `lpj_carbon_stocks.cs3`, loaded by Module 52 (`modules/52_carbon/normal_dec17/input.gms:16–20`). For forests and other land with age-class structure, Module 52 also provides `pm_carbon_density_secdforest_ac`, `pm_carbon_density_plantation_ac`, and `pm_carbon_density_other_ac` using the Chapman-Richards growth equation (`core/macros.gms:18`).

`modules/module_35.md §6.3; modules/module_52.md §2, §4; cross_module/carbon_balance_conservation.md §7`

---

## Step 3 — The previous-timestep stock is preserved as `pcm_carbon_stock`

🟡 At the end of each timestep, Module 56 stores the solved `vm_carbon_stock` as:

```
pcm_carbon_stock(j, land, c_pools, stockType)
```

This is the **previous**-timestep carbon stock (mio. tC), which is fixed (a parameter, prefix `pc`) when the next period's optimization begins.

`modules/module_52.md §3 — "Variables Read by Module 52"`; `modules/module_56.md §2.2`

---

## Step 4 — The stock-change equation turns carbon loss into CO₂ emissions

🟡 **The central accounting equation** is in Module 52:

**`q52_emis_co2_actual`** (`modules/52_carbon/normal_dec17/equations.gms:16–19`):

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
    / m_timestep_length
    );
```

**Translation**:

```
Annual CO₂ emission (Tg C/yr) =
    [Previous-period carbon stock  −  Current-period carbon stock]  ÷  Timestep length (yr)
```

**Sign convention**:
- `pcm_carbon_stock > vm_carbon_stock` (stock fell, e.g. forest cleared) → **positive** → emission
- `pcm_carbon_stock < vm_carbon_stock` (stock rose, e.g. afforestation) → **negative** → sequestration
- No change → zero

**Units**: both stock variables in mio. tC; 1 mio. tC = 1 Tg C, so the result is Tg C yr⁻¹.

`modules/module_52.md §3, Key Equations §1`; `cross_module/carbon_balance_conservation.md §4.1`

---

## Step 5 — Where the released carbon goes: `vm_emissions_reg` → Module 56

🟡 The output of `q52_emis_co2_actual` is written to:

```
vm_emissions_reg(i, emis_source, pollutants)
```

declared in Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms`), dimension: region × emission source × gas. The `"co2_c"` element holds land-use-change CO₂ expressed as carbon.

Module 56 then uses this to price emissions via two equations:

1. **`q52_emis_co2_actual`** (Module 52, above) computes the physical emission.
2. **`q56_emis_pricing_co2`** (Module 56, `equations.gms:19–22`) independently re-computes the same stock-change formula to determine **which portion is subject to carbon pricing** — it reads `vm_carbon_stock` with the configurable `stockType` dimension controlled by `c56_carbon_stock_pricing` (default: `"actualNoAcEst"`, which excludes afforestation establishment to avoid double-counting with CDR rewards).

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
    / m_timestep_length);
```

3. **`q56_emission_cost_annual` / `q56_emission_cost_oneoff`** (Module 56, `equations.gms:29–52`) multiply priced emissions by the pollutant price from `im_pollutant_prices` to produce `v56_emission_cost`, which enters the objective function.

So the chain for a deforestation event is:

```
Forest area ↓  →  vm_carbon_stock(primforest/secdforest, vegc/litc/soilc) ↓
→ q52_emis_co2_actual: positive vm_emissions_reg(...,"co2_c")
→ q56_emis_pricing_co2: positive v56_emis_pricing(...,"co2_c")
→ q56_emission_cost_*: emission cost enters objective function
→ optimizer "pays" for land-use change → incentivizes carbon-efficient land allocation
```

`modules/module_56.md §2.1–2.3`; `modules/module_52.md §3 — Variables Written`

---

## Step 6 — Soil carbon: dynamic convergence in Module 59

🟡 Soil carbon (`soilc`) has an extra layer of dynamics. Module 59 (SOM, realization `cellpool_jan23`) tracks topsoil carbon with IPCC 2019 stock-change factors. When land is converted, the new topsoil pool converges gradually toward the equilibrium value for the new land use:

**`v59_som_pool`** equation (`modules/59_som/cellpool_jan23/equations.gms:46–52`):

```
v59_som_pool(j,land) = lossrate × v59_som_target(j,land)
                     + (1 − lossrate) × legacy_carbon
```

where `lossrate = 1 − 0.85^(years_in_timestep)` (15 % annual convergence; `preloop.gms:45`).

Module 59 assembles the soilc slice of `vm_carbon_stock` via **`q59_carbon_soil`** (`equations.gms:61–64`): topsoil `v59_som_pool` + static subsoil density `i59_subsoilc_density`.

This convergence means soil carbon loss from a forest-to-cropland conversion is spread over ~20 years, but it is fully captured in the stock-change equation of `q52_emis_co2_actual` at each timestep — the difference `pcm_carbon_stock − vm_carbon_stock` for the `soilc` pool registers as a positive emission each period until the new equilibrium is reached.

`cross_module/carbon_balance_conservation.md §5; modules/module_52.md §7.2`

---

## Step 7 — Vegetation carbon: age-class dynamics for forests

🟡 For forests and other age-structured land, vegetation carbon is not simply `area × static_density`. Module 35 manages age-class area arrays (`v35_secdforest(j,ac)`, `vm_land_other(j,othertype35,ac)`); Module 52 provides Chapman-Richards growth curves (`pm_carbon_density_secdforest_ac`, etc.). When deforestation occurs, the harvested area is removed from its age class and its carbon density falls to the new land type's density (e.g., bare cropland). That lower density is what `vm_carbon_stock` reflects in the post-conversion period, and the difference from `pcm_carbon_stock` is exactly the emitted carbon.

As of 2026-04-20 (PR #869), Module 35 blends two growth curves for secondary forest via `p35_carbon_density_secdforest` (existing managed secdforest uses the FRA-calibrated curve; newly-naturally-recovered secdforest uses the uncalibrated Braakhekke et al. curve) — the conservation accounting is unchanged; only the carbon density fed into `q35_carbon_secdforest` is more accurate.

`modules/module_35.md §5.1, §6.3; modules/module_52.md §2.C`

---

## Summary: The Full Accounting Chain

| Step | What happens | Key variable/equation | File:line |
|---|---|---|---|
| Land modules compute current carbon stocks | Area × carbon density (with age-class dynamics for forests) | `vm_carbon_stock(j,land,c_pools,"actual")` | M35 `equations.gms:42–55`; M29, M31, M32, M34; M59 `equations.gms:61–64` |
| Previous-period stock preserved | Module 56 stores last solution | `pcm_carbon_stock(j,land,c_pools,"actual")` | M56 `declarations.gms:34` |
| Stock change → CO₂ emission | Core accounting equation in M52 | `q52_emis_co2_actual` | M52 `equations.gms:16–19` |
| Emission recorded | Populated variable | `vm_emissions_reg(i,emis_oneoff,"co2_c")` | M56 `declarations.gms` |
| Emission priced | M56 re-reads stocks for pricing | `q56_emis_pricing_co2` | M56 `equations.gms:19–22` |
| Cost enters objective | Emission × carbon price | `v56_emission_cost` via `q56_emission_cost_*` | M56 `equations.gms:29–52` |
| Soil carbon lag | 15%/yr convergence to new equilibrium | `v59_som_pool`, `q59_carbon_soil` | M59 `equations.gms:46–52`, `61–64` |

**Pools tracked**: `vegc`, `litc`, `soilc` for all 7 land types (21 source slots in `emis_oneoff`).  
**NOT a hard conservation constraint**: carbon exits the terrestrial system as atmospheric CO₂ (or enters via sequestration); the total is not required to be constant. The invariant is: every unit of stock loss is registered as a positive emission.

---

## Sources

🟡 Based on:
- `cross_module/carbon_balance_conservation.md` (§1, §2, §4, §5, §7, §11)
- `modules/module_52.md` (§2, §3, §4, §7 — Interface Variables)
- `modules/module_56.md` (§2.1–2.3)
- `modules/module_35.md` (§5.1, §6.3)
- `modules/module_10.md` (§2 — transition matrix)

Line numbers from Module 52: verified as docs state (`equations.gms:16–19`).  
Line numbers from Module 56: `equations.gms:15–52`.  
Line numbers for Module 35 carbon equations: `equations.gms:42–55`.  
Line numbers for Module 59 SOM: `equations.gms:46–52`, `61–64`.

⚠️ Line-number caveat: citations reflect doc state at last sync; verify against current GAMS code for high-stakes work.
