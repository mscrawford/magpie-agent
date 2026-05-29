# Q2: How does MAgPIE balance water supply and demand?

## Default Realizations

- **Module 42 (Water Demand)**: `all_sectors_aug13` (confirmed `config/default.cfg` line 1317: `cfg$gms$water_demand <- "all_sectors_aug13"`)
- **Module 43 (Water Availability)**: `total_water_aug13` (only realization — no alternative)
- **Module 41 (Area Equipped for Irrigation)**: `endo_apr13` (confirmed `config/default.cfg`: `cfg$gms$area_equipped_for_irrigation <- "endo_apr13"`)

---

## 1. Constraint Type: Inequality, Not Equality

The water balance in MAgPIE is an **inequality constraint** (`=l=`), not a strict equality. This is a fundamental difference from land balance (which is `=e=`). Water is a flow resource: surplus water that is not withdrawn flows downstream or to the ocean and does not need to be "used up."

**The single water balance equation** (Module 43):

```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2));
```

Source: `modules/43_water_availability/total_water_aug13/equations.gms:10-11`

**Translation**: In every cell `j`, total water withdrawals across all demand sectors must be **less than or equal to** total water available from all sources. The slack (available minus withdrawn) is zero in water-scarce cells where the constraint binds, and positive in water-abundant cells where surplus water flows unused.

This is the **only equation in Module 43** (1 equation: `q43_water`).

---

## 2. Water Supply Variable

**`v43_watavail(wat_src,j)`** — water available by source and cell (mio. m³/yr)

Source: `modules/43_water_availability/total_water_aug13/declarations.gms:9`

The set `wat_src` has four members: `surface`, `ground`, `ren_ground`, `technical`.

**Only surface water is active by default** (preloop.gms:8-12):

```gams
im_wat_avail(t,"surface",j) = f43_wat_avail(t,j);

im_wat_avail(t,"ground",j)     = 0;
im_wat_avail(t,"ren_ground",j) = 0;
im_wat_avail(t,"technical",j)  = 0;
```

Source: `modules/43_water_availability/total_water_aug13/preloop.gms:8-12`

All sources are then fixed to these values in presolve (`presolve.gms:8-11`). `v43_watavail` is declared as a variable (not a parameter) only so that the solver computes shadow prices (marginals) on it — those shadow prices signal water scarcity.

**Surface water origin**: LPJmL runoff restricted to the crop growing period (or full annual runoff for cells with dams). Input file: `lpj_watavail_grper.cs2`. Climate scenario `cc` (time-varying LPJmL projections) is the default; `nocc` and `nocc_hist` alternatives freeze availability at 1995 levels.

Source: `modules/43_water_availability/total_water_aug13/input.gms:9-12`, `preloop.gms:8`

---

## 3. Water Demand Variables and Sectors

**`vm_watdem(wat_dem,j)`** — water withdrawals by sector and cell (mio. m³/yr)

Source: `modules/42_water_demand/all_sectors_aug13/declarations.gms:29`

The set `wat_dem` has five members. Module 42 default realization `all_sectors_aug13` includes all five:

| Sector | Code | Type | Data source |
|--------|------|------|-------------|
| Agriculture | `agriculture` | **Endogenous** (optimized) | LPJmL irrigated water requirements + FAO livestock water |
| Manufacturing | `manufacturing` | Exogenous (fixed) | WATERGAP SSP2 by default |
| Electricity | `electricity` | Exogenous (fixed) | WATERGAP SSP2 by default |
| Domestic | `domestic` | Exogenous (fixed) | WATERGAP SSP2 by default |
| Ecosystem | `ecosystem` | Exogenous (fixed) | LPJmL Smakhtin algorithm by default |

Source: `modules/42_water_demand/all_sectors_aug13/equations.gms` (agricultural demand); `presolve.gms:38-54` (non-agricultural fixed); `sets.gms:9-13`

### Agricultural demand (the only endogenous demand)

Governed by equation `q42_water_demand` (the first of Module 42's two equations):

```gams
q42_water_demand("agriculture",j2) ..
  vm_watdem("agriculture",j2) * v42_irrig_eff(j2) =e=
    sum(kcr, vm_area(j2,kcr,"irrigated") * ic42_wat_req_k(j2,kcr))
  + sum(kli, vm_prod(j2,kli) * ic42_wat_req_k(j2,kli) * v42_irrig_eff(j2));
```

Source: `modules/42_water_demand/all_sectors_aug13/equations.gms:10-14`

Components: irrigated area (from Module 30) × crop water requirement (LPJmL `lpj_airrig.cs2`), plus livestock production (from Module 17) × FAO livestock water requirement, all scaled by irrigation efficiency `v42_irrig_eff(j2)`.

The second Module 42 equation is `q42_water_cost` (pumping costs), which is active only when `s42_pumping = 1`; the default is `s42_pumping = 0` (pumping costs disabled).

Source: `modules/42_water_demand/all_sectors_aug13/input.gms:39`, `equations.gms:16-17`

### Non-agricultural sectors (exogenous, fixed)

These three human-use sectors are fixed via `.fx` in presolve before each solve, reading from WATERGAP model data under SSP2 by default (`s42_watdem_nonagr_scenario = 2`):

```gams
vm_watdem.fx(watdem_ineldo,j) = f42_watdem_ineldo(t,j,"ssp2",watdem_ineldo,"withdrawal");
```

Source: `modules/42_water_demand/all_sectors_aug13/presolve.gms:40-54`

### Ecosystem (environmental flow) demand

Fixed via ecosystem water demand calculation. Default is scenario 2 (LPJmL-based Smakhtin algorithm, `s42_env_flow_scenario = 2`):

```gams
vm_watdem.fx("ecosystem",j) = sum(cell(i,j), i42_env_flows_base(t,j) * (1 - ic42_env_flow_policy(i))
                                            + i42_env_flows(t,j) * ic42_env_flow_policy(i));
```

Source: `modules/42_water_demand/all_sectors_aug13/presolve.gms:87-88`

Base protection is 5% of available water (`s42_env_flow_base_fraction = 0.05`). Environmental flow protection (EFP) policy ramps from 0% to 100% between 2025 and 2040 when `c42_env_flow_policy = "on"` (or the `mixed` development-state-dependent mode). The default policy mode in `default.cfg` is `"off"` (base protection only, 5%).

Source: `modules/42_water_demand/all_sectors_aug13/input.gms:35-38, 122`

### Alternative realization note

The alternative Module 42 realization `agr_sector_aug13` models only agricultural water demand endogenously; manufacturing, electricity, and domestic sectors are still exogenous but the module structure is simpler. The default `all_sectors_aug13` explicitly models all five sectors.

Source: `modules/42_water_demand/all_sectors_aug13/module.gms:22-23`; `config/default.cfg:1317`

---

## 4. What Happens to Unused Water

When the water constraint is not binding (slack > 0), the surplus water is **not used** — there is no mechanism by which it is reallocated, stored inter-temporally, or transferred to adjacent cells. It represents water that flows unused downstream or to the ocean within the growing period. Each cell's water budget is enforced independently; there is no inter-cell water trading or river-basin transfer.

Source: `modules/43_water_availability/total_water_aug13/equations.gms:10-11`; `cross_module/water_balance_conservation.md` §4.2-4.3

The shadow price of `q43_water` is zero when there is slack (abundant cells) and positive when the constraint binds (scarce cells). Diagnostically, surplus is reflected in `oq43_water.level` (the equation level = available minus withdrawn, ≥ 0).

Source: `modules/43_water_availability/total_water_aug13/postsolve.gms:11-17`

---

## 5. Infeasibility Buffer: The One Exception to "Renewable Surface Water Only"

A structural complication arises when **exogenous demands** (manufacturing, electricity, domestic, ecosystem — which are fixed before the solve and cannot be adjusted by the optimizer) collectively exceed available surface water in a cell. The optimizer cannot reduce those fixed demands, so the constraint would be infeasible with zero groundwater.

Module 43 prevents this via an automatic **groundwater buffer** computed in presolve:

```gams
v43_watavail.fx("ground",j) = v43_watavail.up("ground",j)
  + (((sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
      - sum(wat_src, v43_watavail.up(wat_src,j))) * 1.01))
  $(sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
    - sum(wat_src, v43_watavail.up(wat_src,j)) > 0);
```

Source: `modules/43_water_availability/total_water_aug13/presolve.gms:14-16`

**Logic**: If (minimum exogenous demand − total available water) > 0, groundwater availability is set to exactly cover the shortfall × 1.01 (1% safety margin). Otherwise groundwater stays at zero.

**Key asymmetry**: The buffer applies only to exogenous sectors (`watdem_exo`: manufacturing, electricity, domestic, ecosystem). Agricultural demand must still fit within renewable surface water; there is no buffer for agriculture. This means all water scarcity burden is borne by the agricultural sector.

**Interpretation**: The buffer represents unsustainable fossil-aquifer extraction. It carries no cost and no depletion penalty. It is a model-feasibility mechanism, not a representation of sustainable groundwater management.

Source: `modules/43_water_availability/total_water_aug13/realization.gms:40-42`; `cross_module/water_balance_conservation.md` §5

---

## 6. Role of Module 41 (Area Equipped for Irrigation)

Module 41 does **not** directly participate in the water balance conservation law. Its role is to constrain how much irrigated cropland Module 30 can place:

```gams
q41_area_irrig(j2) ..
  sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);
```

Source: `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`

The link to water is indirect: `vm_AEI(j2)` sets an upper bound on irrigated area, which determines `vm_area(j,kcr,"irrigated")` in Module 30, which drives agricultural water demand in Module 42, which feeds into the Module 43 water constraint. Module 41 does not check water availability itself; it can invest in irrigation infrastructure (incurring costs via `q41_cost_AEI`) even in cells where Module 43 will ultimately prevent full utilization of that infrastructure — a "stranded assets" scenario documented as a known limitation.

Source: `modules/41_area_equipped_for_irrigation/module.gms:10-13`; `module_41.md` §4.4; `module_43.md` §10.2

---

## 7. Complete Variable Inventory

| Variable | Module | Type | Description |
|----------|--------|------|-------------|
| `vm_watdem(wat_dem,j)` | 42 | Interface variable | Withdrawals by sector and cell (mio. m³/yr) |
| `v42_irrig_eff(j)` | 42 | Internal variable (fixed) | Irrigation efficiency (dimensionless) |
| `vm_water_cost(i)` | 42 | Interface variable | Pumping costs (USD17MER/yr); zero by default |
| `v43_watavail(wat_src,j)` | 43 | Variable (fixed in presolve) | Available water by source and cell (mio. m³/yr) |
| `im_wat_avail(t,wat_src,j)` | 43 | Interface parameter | Water availability passed to Module 42 |
| `vm_AEI(j)` | 41 | Interface variable | Area equipped for irrigation (mio. ha) |
| `vm_cost_AEI(i)` | 41 | Interface variable | Annualized irrigation investment cost (mio. USD17MER/yr) |

---

## 8. Equation Summary

| Equation | Module | File:line | Type | Purpose |
|----------|--------|-----------|------|---------|
| `q43_water` | 43 | `equations.gms:10-11` | `=l=` (inequality) | Enforces demand ≤ supply at cell level |
| `q42_water_demand` | 42 | `equations.gms:10-14` | `=e=` (equality) | Calculates agricultural water demand |
| `q42_water_cost` | 42 | `equations.gms:16-17` | `=e=` (equality) | Calculates pumping costs (inactive by default) |
| `q41_area_irrig` | 41 | `equations.gms:10-11` | `=l=` (inequality) | Irrigated area ≤ AEI capacity |
| `q41_cost_AEI` | 41 | `equations.gms:19-23` | `=e=` (equality) | Annualized AEI investment cost |

The water balance constraint `q43_water` is `=l=`. All other equations cited here are equality constraints (`=e=`) or the AEI capacity constraint (`=l=`).

---

## 9. Summary of Key Properties

1. **Constraint type**: Inequality (`=l=`), not equality. Surplus water is allowed and flows unused.
2. **Single enforcing equation**: `q43_water` in Module 43, applied independently at each of ~200 cells.
3. **Supply variable**: `v43_watavail(wat_src,j)` — in practice equal to surface water only (`v43_watavail("surface",j)` from LPJmL) with ground/ren_ground/technical set to zero, except when the infeasibility buffer activates.
4. **Demand variable**: `vm_watdem(wat_dem,j)` — five sectors summed on the LHS of `q43_water`.
5. **Sectors active by default (all_sectors_aug13)**: agriculture (endogenous), manufacturing, electricity, domestic (all exogenous SSP2), ecosystem (exogenous, LPJmL-based EFP).
6. **Unused water**: No mechanism to reallocate, store, or transfer it — it flows away. No cost or penalty for having surplus.
7. **Infeasibility buffer**: Fossil groundwater at zero cost, activated only when exogenous demands exceed surface water, applies only to non-agricultural sectors. Agriculture has no buffer.
8. **Module 41 role**: Indirect — constrains irrigated area capacity but does not directly enforce the water balance. Can produce stranded infrastructure if water is scarce.

---

## Documentation Sources

- `cross_module/water_balance_conservation.md` — authoritative system-level description
- `modules/module_42.md` — Module 42 implementation (all_sectors_aug13)
- `modules/module_42_notes.md` — warnings and tips
- `modules/module_43.md` — Module 43 implementation (total_water_aug13)
- `modules/module_41.md` — Module 41 implementation (endo_apr13)
- `config/default.cfg:1317` — confirms `all_sectors_aug13` as default for Module 42

**Confidence**: High for constraint type, variable names, sector list, and buffer mechanism. Line numbers are from documentation last verified against MAgPIE 4.x source; verify against current code before citing in high-stakes contexts.
