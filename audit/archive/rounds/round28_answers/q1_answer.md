# Q1: Trace second-generation (lignocellulosic) bioenergy demand from demand side through to land allocation and cost objective

---

## 1. Default Realization of Module 60

Module 60 (Bioenergy) runs in the **`1st2ndgen_priced_feb24`** realization by default.

Source: `config/default.cfg` line: `cfg$gms$bioenergy <- "1st2ndgen_priced_feb24"` — also confirmed in `module_60.md` Overview block: "Confirmed in `config/default.cfg`: `cfg$gms$bioenergy <- "1st2ndgen_priced_feb24"`."

---

## 2. Crop-type set members carrying 2nd-generation lignocellulosic bioenergy

The second-generation dedicated bioenergy crops are the members of set **`kbe60(kall)`**, defined in `modules/60_bioenergy/1st2ndgen_priced_feb24/sets.gms:111-112`:

```
kbe60(kall) = / betr, begr /
```

- **`betr`**: Bioenergy trees (woody perennial crops)
- **`begr`**: Bioenergy grasses (herbaceous perennial crops, e.g., switchgrass, miscanthus)

These are distinct from 1st-generation bioenergy (`k1st60` = `oils`, `ethanol`) and from residue-based 2nd-generation demand (`kres`).

### Where betr/begr are grown

`begr` and `betr` are members of crop set `kcr` and are allocated at cell level via Module 30 (Croparea), specifically equation `q30_prod` (`simple_apr24/equations.gms:14-15`), which computes cell-level production as `vm_prod(j,kcr) =e= sum(w, vm_area(j,kcr,w) * vm_yld(j,kcr,w))`. They are therefore grown on cropland cells and subject to the same land allocation logic as any other crop. Module 30 `simple_apr24` also enforces rotational constraints via `q30_rotation_max`/`q30_rotation_min` that bound the share of cropland allocated to any single crop group, including bioenergy.

Crucially, **`begr` and `betr` are classified as non-tradable** (`k_notrade`) in Module 21:
> `begr, betr  - Bioenergy (biomass traded in REMIND, not MAgPIE)` (`modules/21_trade/selfsuff_reduced/sets.gms:11-21`)

This means bioenergy biomass does not cross region boundaries inside MAgPIE. Each region must produce its own 2nd-generation dedicated bioenergy domestically.

---

## 3. Demand side: how the 2nd-generation bioenergy demand target is set

### 3.1 Exogenous scenario input

Demand trajectories come from `f60_bioenergy_dem(t,i,scen2nd60)` (mio. GJ per yr), read from input data (`input.gms:63-67`). The selected scenario is controlled by switch `c60_2ndgen_biodem` (default: `"R34M410-SSP2-NPi2025"`, confirmed `input.gms:45`). A population-weighted blending with non-selected scenario `c60_2ndgen_biodem_noselect` computes the active parameter `i60_bioenergy_dem(t,i)` in `preloop.gms:30-31`.

A minimum demand floor `s60_2ndgen_bioenergy_dem_min = 1` (mio. GJ/yr, `input.gms:41`) is enforced per region in `presolve.gms:56-57` to prevent numerical degeneration.

### 3.2 Active demand constraint (regional mode, default)

The `c60_biodem_level` switch defaults to **1 (regional)** (`input.gms:37`), so the active constraint is:

**`q60_bioenergy_reg`** (`equations.gms:46-47`):
```
sum(kbe60, v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
    sum(ct, i60_bioenergy_dem(ct,i2)) * c60_biodem_level
```

This enforces that within each region `i`, the sum of dedicated 2nd-generation bioenergy demand (across `betr` and `begr`) meets the regional target from the selected scenario. The global alternative `q60_bioenergy_glo` is inactive under the default (`c60_biodem_level = 1` makes its RHS zero, `equations.gms:43-44`).

### 3.3 Total bioenergy demand equation

**`q60_bioenergy`** (`equations.gms:16-21`):
```
vm_dem_bioen(i2,kall) * fm_attributes("ge",kall) =g=
    sum(ct, i60_1stgen_bioenergy_dem(ct,i2,kall))
    + v60_2ndgen_bioenergy_dem_dedicated(i2,kall)
    + v60_2ndgen_bioenergy_dem_residues(i2,kall)
```

The interface variable **`vm_dem_bioen(i,kall)`** (mio. tDM/yr, `declarations.gms:20`) is the mass-based bioenergy demand that flows to the rest of the model. The `fm_attributes("ge",kall)` conversion factor (GJ/tDM) translates mass to energy units. For 2nd-generation dedicated bioenergy, the components that populate `vm_dem_bioen(i,kbe60)` are the `v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)` terms.

The residue component — **`q60_res_2ndgenBE`** (`equations.gms:61-64`) — constrains crop residue demand (`kres`) for 2nd-generation bioenergy:
```
sum(kres, v60_2ndgen_bioenergy_dem_residues(i2,kres)) =g=
    sum(ct, i60_res_2ndgenBE_dem(ct,i2))
```
The default residue demand scenario is `ssp2` (`input.gms:69`). Residues are a separate pathway that competes with feed and material uses (handled in Modules 18 and 16) but follows the same `vm_dem_bioen` interface.

---

## 4. Demand aggregation: Module 16

`vm_dem_bioen(i,kall)` from Module 60 flows to Module 16 (Demand, realization `sector_may15`) via the supply balance equations.

For crops (`kcr`, which includes `begr` and `betr`), the relevant equation is **`q16_supply_crops`** (`equations.gms:19-29`):

```gams
vm_supply(i2,kcr) =e=
    vm_dem_food(i2,kcr)
    + sum(kap4, vm_dem_feed(i2,kap4,kcr))
    + vm_dem_processing(i2,kcr)
    + vm_dem_material(i2,kcr)
    + vm_dem_bioen(i2,kcr)          <-- bioenergy demand from M60 enters here
    + vm_dem_seed(i2,kcr)
    + v16_dem_waste(i2,kcr)
    + sum(ct, f16_domestic_balanceflow(ct,i2,kcr))
```

For residues (`kres`), the analogous equation is **`q16_supply_residues`** (`equations.gms:51-58`), which also includes `vm_dem_bioen(i2,kres)`.

The output **`vm_supply(i,kall)`** (mio. tDM/yr, `declarations.gms:11`) is the total regional commodity demand that must be satisfied by domestic production plus trade.

---

## 5. Trade: Module 21

Module 21 (Trade, default realization `selfsuff_reduced`) connects `vm_supply(i,k)` from Module 16 to regional production `vm_prod_reg(i,k)` from Module 17.

The global production constraint **`q21_trade_glo`** (`equations.gms:12-14`) ensures:
```gams
sum(i2, vm_prod_reg(i2,k_trade)) =g=
    sum(i2, vm_supply(i2,k_trade)) + sum(ct, f21_trade_balanceflow(ct,k_trade))
```

**However**, `begr` and `betr` are in set `k_notrade` (non-tradable), so they are NOT in `k_trade`. Instead, they are governed by **`q21_notrade`**, which requires each region to produce at least as much as its own demand for non-tradable goods. The domestic constraint is effectively: regional production of `begr`/`betr` >= regional supply requirement for `begr`/`betr`. This is why `c60_biodem_level = 1` (regional) and the non-tradable status of `kbe60` are consistent: 2nd-gen dedicated demand is inherently local.

---

## 6. Production aggregation: Module 17

**`q17_prod_reg`** (`equations.gms:10-11`):
```gams
vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```

This aggregates cell-level production up to region level. For `begr`/`betr`, `vm_prod(j, begr)` and `vm_prod(j, betr)` are computed by Module 30.

---

## 7. Land allocation: Module 30 (Croparea)

At the cell level, the crop production equation in Module 30 (default realization `simple_apr24`) is **`q30_prod`** (`simple_apr24/equations.gms:14-15`):

```gams
q30_prod(j2,kcr) ..
  vm_prod(j2,kcr) =e= sum(w, vm_area(j2,kcr,w) * vm_yld(j2,kcr,w));
```

**`vm_area(j,kcr,w)`** (mio. ha) is the area allocated to crop `kcr` under water system `w` in cell `j`. For bioenergy grasses (`begr`) and trees (`betr`), meeting the demand cascade from Module 60 requires the solver to allocate sufficient `vm_area(j,begr,w)` and `vm_area(j,betr,w)`. The total cropland across all crops and water systems is constrained by Module 29 (Cropland) which enforces compatibility with the total land budget from Module 10 (Land).

**`vm_yld(j,kcr,w)`** comes from Module 14 (Yields), via **`q14_yield_crop`** (`equations.gms:14-16`):
```gams
vm_yld(j2,kcr,w) =e= sum(ct, i14_yields_calib(ct,j2,kcr,w))
                     * vm_tau(j2,"crop")
                     / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

Bioenergy crop yields scale with the technological change factor `vm_tau(j,"crop")` from Module 13, making endogenous intensification apply to `begr`/`betr` in the same way as food crops.

---

## 8. Cost objective: Modules 38 and 11

### 8.1 Crop production costs (Module 38 -> Module 11)

Producing `begr` and `betr` on cropland enters the objective through **`vm_cost_prod_crop(i,factors)`** from Module 38 (Factor Costs, default realization `sticky_feb18`). The labor cost equation **`q38_cost_prod_labor`** (`sticky_feb18/equations.gms:15-17`) is:

```gams
vm_cost_prod_crop(i2,"labor") =e=
    sum(kcr, vm_prod_reg(i2,kcr)
             * sum(ct, p38_labor_need(ct,i2,kcr) * ...));
```

Since `kcr` includes `begr` and `betr`, their regional production `vm_prod_reg(i,begr)` and `vm_prod_reg(i,betr)` directly enter the labor (and capital) cost calculation. This cost is then aggregated into Module 11.

### 8.2 Bioenergy utility / subsidy (Module 60 -> Module 11)

Module 60 provides a second cost pathway via the bioenergy incentive equation **`q60_bioenergy_incentive`** (`equations.gms:73-75`):

```gams
vm_bioenergy_utility(i2) =e=
    sum((ct,k1st60), vm_dem_bioen(i2,k1st60) * fm_attributes("ge",k1st60)
        * (-i60_1stgen_bioenergy_subsidy(ct)))
    + sum((ct,kbe60), vm_dem_bioen(i2,kbe60) * fm_attributes("ge",kbe60)
        * (-i60_2ndgen_bioenergy_subsidy(ct)))
```

**`vm_bioenergy_utility(i)`** (mio. USD17MER/yr, `declarations.gms:26`) is negative when subsidies are positive, thereby acting as a benefit (cost reduction) in the objective. Under the default configuration, `s60_bioenergy_2nd_price = 0` (`config/default.cfg`), so the 2nd-generation subsidy `i60_2ndgen_bioenergy_subsidy(t)` is zero for all time steps after the historical baseline and `vm_bioenergy_utility` for `kbe60` is zero. The 1st-generation floor subsidy `s60_bioenergy_1st_subsidy = 6.5` USD17MER/GJ (`input.gms:38`) still applies for `oils` and `ethanol`.

### 8.3 Aggregation in Module 11

Module 11 (Costs, realization `default`) assembles all regional costs into `vm_cost_glo` which is the objective MAgPIE minimizes. The relevant terms in **`q11_cost_reg`** (`equations.gms:15-47`) that are affected by bioenergy production are:

| Term in q11_cost_reg | Variable | Source | Bioenergy link |
|---|---|---|---|
| Crop factor costs | `sum(factors, vm_cost_prod_crop(i2,factors))` | Module 38 | `begr`/`betr` production enters `vm_prod_reg(i,kcr)` |
| Land conversion costs | `sum((cell(i2,j2),land), vm_cost_landcon(j2,land))` | Module 39 | If new cropland is cleared for bioenergy |
| Tech change investment | `vm_tech_cost(i2)` | Module 13 | Intensification costs apply to bioenergy crops via tau |
| Transport costs | `sum((cell(i2,j2),k), vm_cost_transp(j2,k))` | Module 40 | Transport of `begr`/`betr` to regional market |
| Bioenergy utility | `vm_bioenergy_utility(i2)` | Module 60 | Negative if subsidies active; zero by default for 2nd gen |

Global objective:

**`q11_cost_glo`** (`equations.gms:10`): `vm_cost_glo =e= sum(i2, v11_cost_reg(i2));`

MAgPIE minimizes `vm_cost_glo`, so bioenergy land allocation competes against all other land uses on cost grounds. Since `begr`/`betr` demand is enforced by hard lower bounds (`q60_bioenergy_reg` is an inequality constraint), the solver must find the minimum-cost combination of land allocation, intensification, and possibly land conversion to meet the regional bioenergy targets.

---

## 9. Complete flow summary

```
Exogenous scenario data
  f60_bioenergy_dem(t,i,scen2nd60)          [input: M60 input files]
    → i60_bioenergy_dem(t,i)                [preloop blending, M60 preloop.gms:30-31]
    ↓
q60_bioenergy_reg (M60, default active)     [regional constraint: sum(kbe60, ...) >= i60_bioenergy_dem]
    → v60_2ndgen_bioenergy_dem_dedicated(i,kbe60)
    ↓
q60_bioenergy (M60)                         [mass-energy conversion]
    → vm_dem_bioen(i,kbe60)  [mio. tDM/yr] → to Module 16
    ↓
q16_supply_crops (M16, sector_may15)        [demand aggregation]
    → vm_supply(i,kcr)  [includes begr, betr]  → to Module 21
    ↓
q21_notrade (M21, selfsuff_reduced)         [begr/betr non-tradable: each region self-sufficient]
    → forces vm_prod_reg(i,begr), vm_prod_reg(i,betr) >= regional requirement
    ↓
q17_prod_reg (M17, flexreg_apr16)           [spatial aggregation]
    → vm_prod_reg(i,k) = sum_j vm_prod(j,k)
    ↓
q30_prod (M30, simple_apr24)                [land allocation × yield = production]
    → vm_prod(j,begr) = sum_w vm_area(j,begr,w) * vm_yld(j,begr,w)
    → vm_area(j,begr,w), vm_area(j,betr,w) allocated by optimizer
    ↓
q14_yield_crop (M14, managementcalib_aug19) [yields scale with tau]
    → vm_yld(j,begr,w) = i14_yields_calib * vm_tau(j,"crop") / fm_tau1995(h)
    ↓
COST OBJECTIVE
    vm_cost_prod_crop(i,factors) [M38, q38_cost_prod_labor] — begr/betr in sum(kcr,...)
    vm_bioenergy_utility(i)      [M60, q60_bioenergy_incentive] — zero by default for kbe60
    → q11_cost_reg [M11]  → q11_cost_glo → minimized by solver
```

---

## 10. What the docs do NOT cover

- The **exact yields for `begr` and `betr`** in `i14_yields_calib` are embedded in binary input data files (`.cs3`) that cannot be read from docs alone. Whether these differ substantially from food crop yields in particular regions is not documented in the module docs.
- The **capital cost treatment of bioenergy crops** in Module 38 `sticky_feb18` is not explicitly distinguished from food crops in the docs; it is documented that `vm_cost_prod_crop` sums over all `kcr` (which includes `begr`/`betr`), but whether bioenergy-specific capital parameters differ is not stated.
- **Module 30's `c30_bioen_type` and `c30_bioen_water` switches** (referenced in `config/default.cfg` comments) that control which bioenergy crop types are eligible and whether they can be irrigated — their detailed effect on land allocation is not covered in the docs read this session.
- The **`q30_betr_missing`** equation (noted in the module_30.md overview as tracking "bioenergy tree land targets and penalties") is referenced briefly but its formula is not expanded in the doc sections read here.

---

## 11. Epistemic status

- Module 60 equations, sets, and interface variables: **🟡 Documented** (module_60.md, fully verified against source as of 2025-10-13)
- Module 16 equations: **🟡 Documented** (module_16.md, verified 2025-10-13)
- Module 21 non-tradable classification of `begr`/`betr`: **🟡 Documented** (module_21.md)
- Module 17 aggregation equation: **🟡 Documented** (module_17.md, verified 2025-10-12)
- Module 30 production equation: **🟡 Documented** (module_30.md, verified)
- Module 14 yield equation: **🟡 Documented** (module_14.md, verified 2025-10-12)
- Module 38 labor cost equation: **🟡 Documented** (module_38.md)
- Module 11 cost aggregation: **🟡 Documented** (module_11.md, verified 2026-05-16)
- Default config values confirmed: **🟢 Verified** (read `config/default.cfg` this session)

No GAMS source `.gms` files were read this session (documentation-only test). All variable names, equation names, realization directory names, and line citations are copied directly from the module documentation files.
