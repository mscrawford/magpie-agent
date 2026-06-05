# P4: Water Balance Enforcement in MAgPIE

## Default Realizations

- **Module 42 (Water Demand)**: `all_sectors_aug13` — confirmed in `config/default.cfg`: `cfg$gms$water_demand <- "all_sectors_aug13"`. The alternative `agr_sector_aug13` includes agricultural demand only.
- **Module 43 (Water Availability)**: `total_water_aug13` — the only realization (no alternative).

---

## The Core Balance Equation

The water balance is enforced by a single equation in Module 43:

**`q43_water`** (`modules/43_water_availability/total_water_aug13/equations.gms:10-11`):

```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2));
```

This is an **inequality constraint** (`=l=`): total water withdrawals across all demand sectors must be less than or equal to total water available from all sources. It is applied at the **cell level** (j2, ~200 cells globally). No inter-cell water transfers are modeled; each cell enforces its own water budget independently.

Module 43 holds **no** additional equations. The entire supply-demand enforcement is this one constraint.

---

## Water Demand Sectors (5 total)

All demands flow through `vm_watdem(wat_dem,j)`, declared in Module 42 (`declarations.gms:29`). The full `wat_dem` set is defined in `core/sets.gms:247`; Module 42 defines the exogenous subset `watdem_exo` in `sets.gms:9-13`.

### 1. Agriculture (endogenous)

Calculated by equation **`q42_water_demand`** (`modules/42_water_demand/all_sectors_aug13/equations.gms:10-14`):

```gams
q42_water_demand("agriculture",j2) ..
  vm_watdem("agriculture",j2) * v42_irrig_eff(j2) =e=
    sum(kcr, vm_area(j2,kcr,"irrigated") * ic42_wat_req_k(j2,kcr))
  + sum(kli, vm_prod(j2,kli) * ic42_wat_req_k(j2,kli) * v42_irrig_eff(j2));
```

Components:
- Crop irrigation: irrigated area (from Module 30) × LPJmL crop water requirements
- Livestock water: livestock production (from Module 17) × FAO water requirements per ton
- `v42_irrig_eff(j)`: irrigation efficiency, fixed before solve in `presolve.gms:12-22` using a GDP-based sigmoidal function (default scenario 2 uses 1995 GDP, so efficiency is **time-invariant** by default)

This is the **only endogenous demand** — it responds to water scarcity via the shadow price of `q43_water`.

### 2. Manufacturing, 3. Electricity, 4. Domestic (exogenous, inelastic)

Fixed before each solve in `presolve.gms:40-54`:

```gams
vm_watdem.fx(watdem_ineldo,j) = f42_watdem_ineldo(t,j,ssp_scenario,watdem_ineldo,"withdrawal");
```

Source data: WATERGAP model, SSP scenarios. Default scenario: SSP2 (`s42_watdem_nonagr_scenario = 2`, `input.gms:9`). These three sectors do **not respond** to water scarcity — their demands are locked.

### 5. Ecosystem (exogenous environmental flows)

Fixed before each solve in `presolve.gms:87-88`:

```gams
vm_watdem.fx("ecosystem",j) =
  sum(cell(i,j), i42_env_flows_base(t,j) * (1 - ic42_env_flow_policy(i))
                + i42_env_flows(t,j) * ic42_env_flow_policy(i));
```

This blends a base protection floor with the full environmental flow requirement based on the active EFP policy level (see next section).

---

## Environmental Flow Requirements

### Three Flow Scenarios (`s42_env_flow_scenario`, `input.gms:22`)

- **Scenario 0**: No environmental flows — `i42_env_flows(t,j) = 0`
- **Scenario 1**: Fixed fraction of available water — `s42_env_flow_fraction = 0.2` (20%), spatially uniform (`presolve.gms:63-65`)
- **Scenario 2 (DEFAULT)**: LPJmL-based Smakhtin algorithm — cell-specific values from `lpj_envflow_grper.cs2`

A **base protection floor** always applies when full EFP policy is inactive (`presolve.gms:58`):

```gams
i42_env_flows_base(t,j) = s42_env_flow_base_fraction * sum(wat_src, im_wat_avail(t,wat_src,j));
```

Default: `s42_env_flow_base_fraction = 0.05` (5% of available water, `input.gms:37`).

### Environmental Flow Protection (EFP) Policy

A policy ramp-up fades in from `s42_efp_startyear = 2025` (0% enforcement) to `s42_efp_targetyear = 2040` (100% enforcement), computed in `preloop.gms:13-17`:

```gams
m_linear_time_interpol(p42_efp_fader, s42_efp_startyear, s42_efp_targetyear, 0, 1);
```

Three policy modes (`c42_env_flow_policy`, `input.gms:122`):
- `"off"` — base protection only (5%), no ramp-up
- `"on"` — all countries subject to EFP ramp-up
- `"mixed"` — high-income countries (HIC) only

Country-level targeting: default includes all 249 ISO countries/territories. Regional EFP share is population-weighted (`presolve.gms:69-74`).

Environmental flows consume water from the same cell budget as human sectors, so increasing EFP directly reduces water available for agriculture.

---

## Water Supply: Only Surface Water is Active

Module 43 defines four potential water sources (`wat_src`), but only surface water carries non-zero values:

```gams
im_wat_avail(t,"surface",j) = f43_wat_avail(t,j);   -- LPJmL runoff (active)
im_wat_avail(t,"ground",j)     = 0;                   -- inactive (except buffer)
im_wat_avail(t,"ren_ground",j) = 0;                   -- inactive
im_wat_avail(t,"technical",j)  = 0;                   -- inactive (no desalination)
```

(`modules/43_water_availability/total_water_aug13/preloop.gms:8-12`)

Surface water (`f43_wat_avail`) comes from LPJmL, restricted to growing-period runoff, with a dam exception (cells with dams use full annual runoff). Climate scenario default: `c43_watavail_scenario = cc` (time-varying LPJmL projections).

`v43_watavail(wat_src,j)` is declared as a **variable** (not a parameter) solely to allow GAMS to compute shadow prices (marginal values). It is fixed before the solve via `v43_watavail.fx(...)` in `presolve.gms:8-11`.

---

## Infeasibility Buffer (Groundwater)

Because the exogenous demands (manufacturing, electricity, domestic, ecosystem) are **fixed** (`vm_watdem.lo = vm_watdem.fx`), they can structurally exceed available surface water in some cells. To prevent guaranteed infeasibility, Module 43 automatically adds fossil groundwater before each solve (`presolve.gms:14-16`):

```gams
v43_watavail.fx("ground",j) = v43_watavail.up("ground",j)
  + (((sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
      - sum(wat_src, v43_watavail.up(wat_src,j))) * 1.01))
  $(sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
    - sum(wat_src, v43_watavail.up(wat_src,j)) > 0);
```

This adds exactly (shortfall × 1.01) to groundwater availability when exogenous demands exceed surface water. The 1.01 factor provides a 1% numerical safety margin.

**Key asymmetry**: The buffer is only triggered by `watdem_exo` (manufacturing, electricity, domestic, ecosystem). **Agricultural water is NOT buffered** — if agriculture plus exogenous demands exceed surface water + buffer, the model goes infeasible. Fossil groundwater use is **free** (no cost, no depletion feedback).

Diagnostic: if `ov43_watavail("ground",j,"level") > 0` in the output GDX, the buffer has activated — signaling that exogenous demands exceed sustainable renewable supply in that cell.

---

## What Can Make the Water Module Infeasible?

The water constraint `q43_water` is a **hard cap** with no agricultural slack variable. The model goes infeasible if agricultural water demand cannot fit within surface water, even after the exogenous-demand buffer activates. Specific conditions:

### 1. Agricultural demand structurally exceeds surface water

In very arid cells, even if all non-agricultural demands are buffered, the q43_water constraint on agriculture has no relief mechanism. No inter-cell water trading is possible. The module_42_notes file confirms: "Water availability is from Module 43. When it does and there's no flexibility, the model becomes infeasible."

Trigger in `debugging_infeasibility.md`: "Water-limited regions with irrigation expansion — `q43_water` is a hard cap — no inter-cluster water transfer."

### 2. High non-agricultural water demand scenarios

`s42_watdem_nonagr_scenario = 3` (SSP3) raises manufacturing, electricity, and domestic demands. Even though these are buffered by groundwater, higher exogenous demand leaves less surface water for agriculture (`debugging_infeasibility.md`, "Dangerous Configurations" table: `s42_watdem_nonagr_scenario` listed as a high-risk switch).

### 3. Aggressive Environmental Flow Protection

Setting `c42_env_flow_policy = "on"` and using `s42_env_flow_scenario = 2` (LPJmL Smakhtin) reserves a substantial cell-specific fraction of surface water for the ecosystem. In already water-scarce cells this directly competes with agricultural demand and can make q43_water infeasible for agriculture.

Ecosystem demand IS included in `watdem_exo` and is therefore covered by the groundwater buffer — but higher buffer usage means less renewable water is effectively available to agriculture.

### 4. `off` realization of water demand module

The `off` realization of Module 42 (noted in `module_42_notes.md`) removes all water constraints. Using it unrealistically liberates irrigation expansion, but is not a path to infeasibility — rather the opposite. However, if water module was previously `off` and is re-activated with aggressive demand settings, the now-active constraint may be immediately infeasible.

### 5. Tight climate water scenarios combined with high irrigation demand

Using `c43_watavail_scenario = cc` with a climate model projecting severe runoff decline for a region (e.g., Mediterranean under strong warming) progressively tightens the surface water bound. If irrigation expansion has been optimized in earlier timesteps when water was plentiful, later timesteps may become infeasible as `f43_wat_avail` declines.

---

## Summary: Variable and Equation Inventory

| Name | Type | Module | Location | Role |
|------|------|--------|----------|------|
| `q43_water(j)` | Equation (`=l=`) | 43 | `equations.gms:10-11` | Enforces supply >= demand per cell |
| `q42_water_demand(j)` | Equation (`=e=`) | 42 | `equations.gms:10-14` | Calculates agricultural water demand |
| `q42_water_cost(i)` | Equation (`=e=`) | 42 | `equations.gms:16-17` | Calculates irrigation pumping costs |
| `vm_watdem(wat_dem,j)` | Variable (positive) | 42 | `declarations.gms:29` | Water withdrawals by sector and cell |
| `v43_watavail(wat_src,j)` | Variable (fixed) | 43 | `declarations.gms:9` | Water available by source and cell |
| `v42_irrig_eff(j)` | Variable (fixed) | 42 | `declarations.gms:30` | Irrigation efficiency factor |
| `im_wat_avail(t,wat_src,j)` | Parameter | 43 | `preloop.gms:8-12` | LPJmL surface water availability |

---

## Source Statement

🟢 Verified against AI documentation this session:
- `modules/module_42.md` (default realization `all_sectors_aug13`, equations, sectors, EFP policy)
- `modules/module_43.md` (default realization `total_water_aug13`, q43_water, buffer mechanism)
- `cross_module/water_balance_conservation.md` (full conservation law architecture)
- `modules/module_42_notes.md` (infeasibility warning)
- `agent/helpers/debugging_infeasibility.md` (dangerous configurations, water-scarcity pitfalls)

All file:line citations are from the AI documentation; line numbers were verified at the doc's last sync date and may have shifted if MAgPIE code has since been updated.
