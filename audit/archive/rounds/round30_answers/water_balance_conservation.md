# Water Balance in MAgPIE: Default Realization

## Default realizations

- **Module 42 (Water Demand)**: `all_sectors_aug13`
- **Module 43 (Water Availability)**: `total_water_aug13`

Both confirmed in `config/default.cfg`.

---

## Core balance equation

**Equation name**: `q43_water`
**Location**: `modules/43_water_availability/total_water_aug13/equations.gms:10-11`

```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l=
  sum(wat_src, v43_watavail(wat_src,j2));
```

**Constraint type**: Inequality (`=l=`, less than or equal).

This is a deliberate contrast with the land balance, which uses strict equality (`=e=`). Water is a flow resource; surplus water can go unused (flow downstream or to the ocean), so an inequality is physically appropriate. Slack in the constraint is water that remains unused; when the constraint is binding (slack = 0), the shadow price of `q43_water` goes positive and water scarcity is transmitted to the rest of the optimization.

---

## Variables

| Variable | Dimensions | Role | Module |
|---|---|---|---|
| `vm_watdem(wat_dem,j)` | demand-sector x cell | Total water withdrawals (mio. m³/yr); LHS of q43_water | 42 |
| `v43_watavail(wat_src,j)` | source x cell | Available water by source (mio. m³/yr); RHS of q43_water | 43 |
| `v42_irrig_eff(j)` | cell | Irrigation efficiency factor (dimensionless); mediates agricultural demand | 42 |
| `vm_water_cost(i)` | region | Pumping cost for irrigation (USD17MER/yr); enters objective | 42 |

`v43_watavail` is fixed (`.fx`) to input data via `modules/43_water_availability/total_water_aug13/presolve.gms` rather than being a free optimization variable; the reason for declaring it as a variable rather than a parameter is to allow GAMS to compute shadow prices (marginals) on the constraint.

---

## Sectoral demands entering the LHS

All five elements of the `wat_dem` set are summed in `q43_water`. They are calculated or fixed in Module 42 (`all_sectors_aug13`):

### 1. Agriculture (endogenous)

The only sector that responds to water scarcity. Calculated by equation `q42_water_demand` (`modules/42_water_demand/all_sectors_aug13/equations.gms:10-14`):

```gams
vm_watdem("agriculture",j2) * v42_irrig_eff(j2) =e=
    sum(kcr, vm_area(j2,kcr,"irrigated") * ic42_wat_req_k(j2,kcr))
  + sum(kli, vm_prod(j2,kli) * ic42_wat_req_k(j2,kli) * v42_irrig_eff(j2));
```

Two components:
- **Crop irrigation**: irrigated area (from Module 30) x per-ha water requirement (LPJmL)
- **Livestock water**: livestock production (from Module 17) x per-ton water requirement (FAO)

The left-hand side is gross withdrawal; `v42_irrig_eff` (default: GDP-based sigmoidal function using 1995 GDP, approximately 64-90%, time-invariant under the default scenario 2) converts net field demand to gross withdrawal.

### 2. Manufacturing (exogenous)

Fixed to WATERGAP-model SSP trajectories (`f42_watdem_ineldo`). Default: SSP2. Set via `.fx` in presolve; does not respond to optimization.

### 3. Electricity (exogenous)

Same data source and fixing mechanism as manufacturing (WATERGAP / SSP2 default).

### 4. Domestic (exogenous)

Same mechanism. Together, manufacturing + electricity + domestic form the `watdem_ineldo` subset.

### 5. Ecosystem (environmental flows, exogenous)

Calculated from the environmental flow protection (EFP) policy (`modules/42_water_demand/all_sectors_aug13/presolve.gms:87-88`):

```gams
vm_watdem.fx("ecosystem",j) = sum(cell(i,j),
    i42_env_flows_base(t,j) * (1 - ic42_env_flow_policy(i))
  + i42_env_flows(t,j) * ic42_env_flow_policy(i));
```

Default: LPJmL Smakhtin-algorithm environmental flows (`s42_env_flow_scenario = 2`), fading in 2025-2040 (`c42_env_flow_policy = "off"` by default means only the 5% base protection applies unless EFP is switched on).

---

## Supply side

The RHS sums `v43_watavail(wat_src,j)` over the `wat_src` set (surface, ground, ren_ground, technical). In practice, only **surface water** is non-zero:

```gams
im_wat_avail(t,"ground",j)     = 0;
im_wat_avail(t,"ren_ground",j) = 0;
im_wat_avail(t,"technical",j)  = 0;
```

Surface water is LPJmL growing-period runoff, distributed by discharge weighting within basins; cells with dams receive full annual runoff.

**Infeasibility buffer**: If the sum of fixed exogenous demands (`watdem_ineldo` + ecosystem) exceeds surface water in a cell, Module 43 pre-calculates a groundwater buffer that covers the shortfall × 1.01, preventing solver infeasibility (`presolve.gms:14-16`). This buffer represents unsustainable fossil-aquifer extraction at zero cost. Agricultural demand is never covered by the buffer; it must fit within renewable (surface) water.

---

## Spatial scope

The constraint is enforced **per cell** (index `j2`), approximately 200 MAgPIE clusters. There is no inter-cell water trading; each cell must balance its own water budget.

---

## Summary

| Property | Value |
|---|---|
| Constraint equation | `q43_water` (M43, `total_water_aug13`) |
| Operator | `=l=` (inequality: demand <= supply) |
| Demand variable | `vm_watdem(wat_dem,j)` |
| Supply variable | `v43_watavail(wat_src,j)` |
| Sectors in LHS | agriculture (endogenous), manufacturing, electricity, domestic, ecosystem (all exogenous except agriculture) |
| Active supply source | surface water only (LPJmL growing-period runoff) |
| Spatial scope | per cell (~200 clusters) |
| Infeasibility guard | fossil groundwater buffer for exogenous demand shortfalls |

---

## Sources

- `cross_module/water_balance_conservation.md` (primary — full cross-module analysis)
- `modules/module_42.md` (Module 42 equations, variables, and configuration)

Epistemic hierarchy: 🟡 Documented — both sources read this session from the magpie-agent AI documentation. Raw GAMS code was not read per task constraint. Line numbers cited carry the standard caveat that they were verified at last documentation sync; consult `project/sync_log.json` for sync currency and check current code for high-stakes modifications.
