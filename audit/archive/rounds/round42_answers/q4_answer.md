# Q4 Answer: Water Module Infeasibility and Environmental Flow Requirements

**Question**: What can make MAgPIE's water module infeasible, and how do environmental flow requirements (EFR) constrain water availability? (a) default water-availability realization + EFR representation; (b) the supply-demand constraint and its infeasibility buffer; (c) biodiversity (Module 44) interaction with water/land. Name variables, cite file:line, state diagnostic signals.

**Documentation tags**: 🟡 Documented (module_42.md, module_43.md, module_44.md, cross_module/water_balance_conservation.md)

---

## (a) Default Water-Availability Realization and EFR

### Default realization

Module 43 has **one realization**: `total_water_aug13`. There is no alternative.

🟡 module_43.md §1, §16

### Water supply variable

`v43_watavail(wat_src,j)` (mio. m³/yr, dimensions: water source × cell) holds available water by source. It is declared as an endogenous variable solely to expose shadow prices (GAMS only computes marginals on variables, not parameters). In presolve it is immediately fixed to exogenous values:

```gams
v43_watavail.fx("surface",j) = im_wat_avail(t,"surface",j);   -- presolve.gms:8
v43_watavail.fx("technical",j) = im_wat_avail(t,"technical",j);
v43_watavail.fx("ground",j)   = im_wat_avail(t,"ground",j);
v43_watavail.fx("ren_ground",j)= im_wat_avail(t,"ren_ground",j);
```
🟡 module_43.md §4.1 (citing presolve.gms:8-11)

Only the `"surface"` source is active. The other three sources (`"ground"`, `"ren_ground"`, `"technical"`) are set to zero in preloop:

```gams
im_wat_avail(t,"surface",j)   = f43_wat_avail(t,j);   -- preloop.gms:8
im_wat_avail(t,"ground",j)    = 0;                    -- preloop.gms:10
im_wat_avail(t,"ren_ground",j)= 0;                    -- preloop.gms:11
im_wat_avail(t,"technical",j) = 0;                    -- preloop.gms:12
```
🟡 module_43.md §1.3 (citing preloop.gms:8-12)

Surface water comes from LPJmL runoff during the crop growing period (dataset `lpj_watavail_grper.cs2`). Cells with dams use full annual runoff; all others use only growing-period runoff. 🟡 module_43.md §2.1

### How EFR reserves water for ecosystems

EFR is represented via the `"ecosystem"` element of `vm_watdem(wat_dem,j)` — the interface variable Module 42 provides to Module 43. The ecosystem demand is fixed (exogenous, `.fx`) in Module 42's presolve and thus competes with agricultural and other water uses within the hard cell-level constraint.

The parameter that stores the EFR quantity used in the fix is `i42_env_flows(t,j)` (full EFP scenario) and `i42_env_flows_base(t,j)` (minimum base protection). The fix equation is:

```gams
vm_watdem.fx("ecosystem",j) =
    sum(cell(i,j),
        i42_env_flows_base(t,j) * (1 - ic42_env_flow_policy(i))
      + i42_env_flows(t,j)     * ic42_env_flow_policy(i) );
    -- presolve.gms:87-88
```
🟡 module_42.md §Environmental Flow Protection (citing presolve.gms:87-88)

Key parameters and their defaults:

| Parameter | Default | Effect |
|---|---|---|
| `s42_env_flow_scenario` | `2` (LPJmL Smakhtin algorithm) | Which `i42_env_flows` values to use |
| `s42_env_flow_base_fraction` | `0.05` | 5% of available water reserved even without EFP policy |
| `s42_env_flow_fraction` | `0.20` | 20% fraction used if scenario 1 (uniform fraction) selected |
| `c42_env_flow_policy` | `"off"` | Whether EFP policy ramps up (off / on / mixed) |
| `s42_efp_startyear` | `2025` | EFP linear ramp begins |
| `s42_efp_targetyear` | `2040` | EFP reaches 100% enforcement |

🟡 module_42.md §Configuration Options (citing input.gms:22, 35-38, 122)

With `c42_env_flow_policy = "off"` (the default), only the 5% base protection (`i42_env_flows_base`) applies. When policy is `"on"` or `"mixed"`, the EFP fader `p42_efp(t,"on")` linearly scales the full EFR `i42_env_flows(t,j)` from 0 (year 2025) to 1 (year 2040), implemented via:

```gams
m_linear_time_interpol(p42_efp_fader, s42_efp_startyear, s42_efp_targetyear, 0, 1);
    -- preloop.gms:13-17
```
🟡 module_42.md §Environmental Flow Protection (citing preloop.gms:13-17)

**Summary**: EFR "reserves" water by placing a fixed, exogenous demand of `vm_watdem("ecosystem",j)` on the left-hand side of the water balance constraint, reducing the water available to agriculture. The parameter `i42_env_flows(t,j)` (loaded from `lpj_envflow_grper.cs2`, based on Smakhtin et al. 2004 algorithm applied to LPJmL discharge) is the cell-specific quantity reserved under the full EFP scenario.

---

## (b) The Supply-Demand Constraint and Its Infeasibility Buffer

### The core constraint

Module 43's single equation (`q43_water`, equations.gms:10-11) is a cell-level inequality:

```gams
q43_water(j2) ..
    sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2));
```
🟡 module_43.md §1.1; cross_module/water_balance_conservation.md §4.1

Expanded:
```
vm_watdem(j,"agriculture") + vm_watdem(j,"manufacturing")
+ vm_watdem(j,"electricity") + vm_watdem(j,"domestic") + vm_watdem(j,"ecosystem")
  <=
v43_watavail(j,"surface")     [+ v43_watavail(j,"ground") when buffer active]
```

Key structural properties:
- **Cell-level enforcement** (~200 clusters): no inter-cell water transfer.
- **Inequality** (`=l=`), not equality: surplus water is allowed (flows unused downstream).
- **Growing period only**: both supply and demand are growing-season quantities, not annual totals.

### How infeasibility arises

The four exogenous demands — `"manufacturing"`, `"electricity"`, `"domestic"`, `"ecosystem"` — are set via `.fx` in presolve, so they have both `.lo` and `.up` equal to their fixed value. If the sum of their lower bounds (`vm_watdem.lo(watdem_exo,j)`) exceeds all available surface water, the constraint `q43_water` cannot be satisfied and the model is infeasible.

**Agricultural demand** (`vm_watdem("agriculture",j)`) is optimized (endogenous) and can be reduced by shifting irrigated crops to rainfed, but it cannot go below zero. It never triggers the infeasibility buffer — that burden falls entirely on the exogenous sectors.

### The infeasibility buffer (1% groundwater safety valve)

Before each solve, Module 43 checks whether exogenous demands alone already exceed surface water. If so, it adds just enough fossil groundwater to cover the shortfall plus a 1% numerical margin:

```gams
v43_watavail.fx("ground",j) =
    v43_watavail.up("ground",j)
    + (((sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
         - sum(wat_src,  v43_watavail.up(wat_src,j))) * 1.01))
      $(sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
        - sum(wat_src, v43_watavail.up(wat_src,j)) > 0);
    -- presolve.gms:14-16
```
🟡 module_43.md §3.2; cross_module/water_balance_conservation.md §5.2

The buffer applies only to `watdem_exo` (manufacturing, electricity, domestic, ecosystem). Agriculture must remain within renewable (surface) water — there is no equivalent buffer for agricultural infeasibility. If agricultural demand plus the minimum exogenous demands cannot be satisfied within surface water, the model goes infeasible on `q43_water` because agriculture has no slack variable.

**Interpretation**: The fossil groundwater added by the buffer represents unsustainable extraction at zero cost — it prevents a GAMS infeasibility message but signals a physically unsustainable configuration.

### What causes infeasibility in practice

Ordered by severity:

1. **High non-agricultural exogenous demands** (SSP3 scenario, `s42_watdem_nonagr_scenario = 3`): if manufacturing + electricity + domestic + ecosystem demands collectively exceed surface water, the buffer activates. If agriculture is then also squeezed to zero, true infeasibility occurs. 🟡 debugging_infeasibility.md §Dangerous Configurations

2. **EFP policy active in water-scarce cells** (`c42_env_flow_policy = "on"`, Smakhtin scenario): the full LPJmL-based ecosystem demand can be large in some arid cells, compressing the water available to agriculture toward zero.

3. **Climate change + irrigation expansion**: `c43_watavail_scenario = "cc"` reduces surface water in dry regions over time; if irrigation infrastructure (Module 41 `vm_AEI`) has expanded in expectation of higher water availability, `q43_water` becomes binding and eventually infeasible if agriculture cannot retreat to rainfed.

4. **Irrigation efficiency too low**: If `s42_irrig_eff_scenario = 1` (global static 66%) instead of the GDP-based default, agricultural water withdrawals are higher for the same irrigated area, tightening the constraint.

5. **Water constraint is a hard cap**: `q43_water` has no slack variable of its own. The only relaxation mechanism for the non-agricultural side is the groundwater buffer; for agriculture there is none. 🟡 debugging_infeasibility.md §2

### Diagnostic signals

| Signal | How to read it |
|---|---|
| `oq43_water.marginal > 0` (shadow price of q43_water) | Constraint is binding in that cell; water is the limiting factor |
| `ov43_watavail("ground",j).level > 0` | Buffer activated; exogenous demands exceeded surface water in that cell |
| `p80_modelstat(t) = 4` or `= 5` | GAMS infeasible at timestep t; water likely culprit if `oq43_water.marginal` is high at t-1 |
| `vm_area(j,kcr,"irrigated")` << `vm_AEI(j)` | Stranded irrigation infrastructure due to water scarcity |

🟡 module_43.md §9.2; cross_module/water_balance_conservation.md §9.1-9.2; debugging_infeasibility.md §Step 3

---

## (c) Module 44 (Biodiversity) Interaction with Water/Land

Module 44 (`bii_target` realization, the only default) does **not** directly interact with the water balance constraint. There is no variable from Module 44 that enters `q43_water` or `vm_watdem`. The interaction is **indirect, via land use**.

### The indirect land-use pathway

Module 44 aggregates biodiversity stocks `vm_bv(j,landcover44,potnatveg)` — supplied by land-use modules 29, 30, 31, 32, 34, 35 — into biome-level BII (`v44_bii(i,biome44)`) via:

```gams
v44_bii(i2,biome44) =
    sum(cell(i2,j2),landcover44,potnatveg,
        vm_bv(j2,landcover44,potnatveg) * i44_biome_share(j2,biome44))
    / i44_biome_area_reg(i2,biome44);
    -- equations.gms:13-17
```
🟡 module_44.md §Key Equations

If a BII target is active (`s44_bii_target > 0`), the constraint `q44_bii_target` requires:
```gams
v44_bii_missing(i2,biome44) >= p44_bii_target(ct,i2,biome44) - v44_bii(i2,biome44);
    -- equations.gms:22-23
```

Any shortfall `v44_bii_missing > 0` triggers penalty costs `vm_cost_bv_loss(j)` at $1,000,000/unit (default `s44_cost_bii_missing = 1e6`), via:
```gams
sum(cell(i2,j2)) vm_cost_bv_loss(j2) = sum(biome44, v44_bii_missing(i2,biome44) * s44_cost_bii_missing);
    -- equations.gms:28-29
```
🟡 module_44.md §Key Equations

### How this compresses water-available land

When BII targets are active, the optimizer is penalized for converting natural vegetation (primary/secondary forest, `"primforest"`, `"secdforest"`) to cropland or pasture, because those land covers carry low BII coefficients. This creates indirect competition with irrigated agriculture for productive land: the model shifts crops toward cells with more water but perhaps lower BII conflict, and may be forced to use less-efficient rainfed land instead. The result is higher agricultural water demand (rainfed crops don't use irrigation water, but the BII-driven land reallocation affects where irrigated crops can go), which can tighten `q43_water` in the cells that remain irrigated.

### What Module 44 does NOT do

- Module 44 does **not** place any constraint on `vm_watdem` or `v43_watavail`.
- Module 44 does **not** enforce any flow reservation for aquatic biodiversity (that is handled by the `"ecosystem"` sector in Module 42).
- `v44_bii_missing` is a technical slack variable that prevents hard infeasibility from BII targets; it has no water-balance analog. Water has no such slack.

🟡 module_44.md §Key Limitations §6; module_44.md §Participates In

### Summary of the M44 ↔ water link

The connection is one-directional and indirect:
- BII targets → constrain natural land conversion → shrink available irrigated cropland area → feed through to `vm_area(j,kcr,"irrigated")` → change `vm_watdem("agriculture",j)` → affect `q43_water` binding.
- Water scarcity → reduces irrigated area → shifts production to rainfed → changes `vm_bv` contributions from cropland → affects `v44_bii`.
- No variable passes directly from Module 44 to Module 42 or 43.

---

## Variable and Parameter Quick Reference

| Name | Type | Module | Description |
|---|---|---|---|
| `q43_water(j)` | Equation (=l=) | M43 | Core water balance: Σ demands ≤ Σ supply |
| `v43_watavail(wat_src,j)` | Variable (fixed) | M43 | Water available by source; shadow price diagnostic |
| `im_wat_avail(t,wat_src,j)` | Parameter | M43 | Input storage for water availability (from LPJmL) |
| `f43_wat_avail(t,j)` | Input parameter | M43 | LPJmL surface water (from `lpj_watavail_grper.cs2`) |
| `vm_watdem(wat_dem,j)` | Variable | M42 | Water demand by sector; provided to M43 |
| `i42_env_flows(t,j)` | Parameter | M42 | EFR target from LPJmL Smakhtin algorithm |
| `i42_env_flows_base(t,j)` | Parameter | M42 | Base EFR = 5% × available water |
| `ic42_env_flow_policy(i)` | Parameter | M42 | Blending weight between base and full EFR |
| `p42_efp_fader(t)` | Parameter | M42 | Linear 0→1 ramp 2025–2040 for EFP fade-in |
| `v42_irrig_eff(j)` | Variable (fixed) | M42 | Irrigation efficiency (GDP-based sigmoidal, fixed at 1995 GDP by default) |
| `v44_bii(i,biome44)` | Variable | M44 | BII by region × biome; not in water constraint |
| `v44_bii_missing(i,biome44)` | Variable | M44 | BII shortfall slack (has no water analog) |
| `vm_cost_bv_loss(j)` | Variable | M44 | Penalty cost for BII target gap |
| `vm_bv(j,landcover44,potnatveg)` | Variable | M44 (declared), M29-35 (set) | Biodiversity stock by land cover |
| `oq43_water(t,j).marginal` | Output | M43 | Shadow price of water constraint; >0 signals binding |
| `ov43_watavail("ground",j).level` | Output | M43 | Groundwater buffer used; >0 signals unsustainable use |
| `p80_modelstat(t)` | Output | M80 | Solver status; 4 or 5 = infeasible at timestep t |

---

## Source Statement

All claims draw from AI documentation only (docs-only mode per task specification); no raw GAMS `.gms` files were opened this session. Citations are 🟡 (documented).

Primary sources:
- `modules/module_43.md` (Module 43, `total_water_aug13` realization — the only realization)
- `modules/module_42.md` (Module 42, `all_sectors_aug13` realization — confirmed default in `config/default.cfg`: `cfg$gms$water_demand <- "all_sectors_aug13"`)
- `modules/module_44.md` (Module 44, `bii_target` realization — confirmed default in `config/default.cfg`: `cfg$gms$biodiversity <- "bii_target"`)
- `cross_module/water_balance_conservation.md`
- `modules/module_42_notes.md`
- `agent/helpers/debugging_infeasibility.md`

Line numbers in the doc citations (e.g., `presolve.gms:14-16`) were current at the docs' last verification date (2025-10-12 to 2025-10-22). Code changes since the last `/sync` may have shifted them.
