# Helper: Water Scarcity Scenarios

**Auto-load triggers**: "water", "water scarcity", "irrigation", "water availability", "water demand", "water constraint", "groundwater", "environmental flow"
**Last updated**: 2025-07-18
**Lessons count**: 0 entries

---

## Quick Reference

Water in MAgPIE is governed by three tightly coupled modules:

| Module | Name | Default Realization | Role |
|--------|------|---------------------|------|
| 42 | `water_demand` | `all_sectors_aug13` | Calculates water withdrawals across 5 sectors |
| 43 | `water_availability` | `total_water_aug13` | Provides renewable surface water supply from LPJmL |
| 41 | `area_equipped_for_irrigation` | `endo_apr13` | Controls irrigation infrastructure expansion |

**Core constraint** — `q43_water(j2)` in Module 43 (`equations.gms:10-11`):
```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2));
```
Total water demand ≤ Total water available, enforced **per cell** as an inequality.

**Key interface variables**:

| Variable | Module | Direction | Units | Description |
|----------|--------|-----------|-------|-------------|
| `vm_watdem(wat_dem,j)` | 42 → 43 | Output → Constraint LHS | mio. m³/yr | Water withdrawals by sector |
| `v43_watavail(wat_src,j)` | 43 | Constraint RHS (fixed) | mio. m³/yr | Water available by source |
| `vm_area(j,kcr,"irrigated")` | 30 → 42 | Input to demand eq. | mio. ha | Irrigated crop area |
| `vm_AEI(j)` | 41 | Upper bound on irrig. area | mio. ha | Area equipped for irrigation |
| `v42_irrig_eff(j)` | 42 | Internal | dimensionless | Irrigation efficiency (conveyance) |
| `vm_water_cost(i)` | 42 | → objective | mio. USD17MER/yr | Pumping cost (if enabled) |
| `vm_cost_AEI(i)` | 41 | → objective | mio. USD17MER/yr | Irrigation expansion cost |

**Water demand sectors** (set `wat_dem`):
- `agriculture` — endogenous (optimized via `q42_water_demand`)
- `domestic`, `manufacturing`, `electricity` — exogenous (fixed from WATERGAP/SSP)
- `ecosystem` — exogenous (environmental flow requirements)

**Water sources** (set `wat_src`): Only `surface` is active. `ground`, `ren_ground`, and `technical` are set to zero (except as automatic infeasibility buffer).

---

## Key Configuration Switches

### Module 42 — Water Demand

| Switch | Default | Options | Description |
|--------|---------|---------|-------------|
| `c42_watdem_scenario` | `"cc"` | `"cc"`, `"nocc"`, `"nocc_hist"` | Climate change impact on crop water requirements |
| `s42_watdem_nonagr_scenario` | `2` | `1`=SSP1, `2`=SSP2, `3`=SSP3 | Non-agricultural water demand trajectory |
| `s42_irrig_eff_scenario` | `2` | `1`=global static, `2`=regional static, `3`=GDP-driven | Irrigation efficiency calculation |
| `s42_irrigation_efficiency` | `0.66` | 0–1 | Global static efficiency (used only if scenario=1) |
| `s42_env_flow_scenario` | `2` | `0`=none, `1`=fraction, `2`=Smakhtin | Environmental flow protection method |
| `s42_env_flow_fraction` | `0.2` | 0–1 | Fraction reserved for environment (scenario=1) |
| `s42_env_flow_base_fraction` | `0.05` | 0–1 | Base fraction without EFP policy |
| `c42_env_flow_policy` | `"off"` | `"off"`, `"on"`, `"mixed"` | Environmental flow protection policy mode |
| `s42_efp_startyear` | `2025` | year | EFP policy ramp-up start |
| `s42_efp_targetyear` | `2040` | year | EFP policy full implementation |
| `s42_pumping` | `0` | `0`=off, `1`=on | Activate pumping cost for irrigation |
| `s42_reserved_fraction` | `0.5` | 0–1 | Fraction of available water reserved (not withdrawn) |

### Module 43 — Water Availability

| Switch | Default | Options | Description |
|--------|---------|---------|-------------|
| `c43_watavail_scenario` | `"cc"` | `"cc"`, `"nocc"`, `"nocc_hist"` | Climate change impact on water supply |

### Module 41 — Area Equipped for Irrigation

| Switch | Default | Options | Description |
|--------|---------|---------|-------------|
| `cfg$gms$area_equipped_for_irrigation` | `"endo_apr13"` | `"endo_apr13"`, `"static"` | Endogenous expansion vs. fixed at 1995 |
| `c41_initial_irrigation_area` | `"LUH3"` | `"LUH3"`, `"Mehta2024_Siebert2013"`, `"Mehta2024_Meier2018"` | Historical AEI data source |
| `s41_AEI_depreciation` | `0` | ≥0 | Irrigation infrastructure depreciation rate |

### Related Switches in Other Modules

| Switch | Module | Default | Description |
|--------|--------|---------|-------------|
| `c30_bioen_water` | 30 (cropland) | `"rainfed"` | Irrigation of bioenergy crops (`"rainfed"`, `"irrigated"`, `"all"`) |
| `c59_irrigation_scenario` | 59 (som) | `"on"` | Irrigation feedback on soil carbon |

---

## Scenario Recipes

### Recipe 1: Water-Constrained Future (Strict Environmental Flows)

Enforce strong environmental flow protection globally, limiting withdrawals.

```r
cfg$gms$c42_env_flow_policy     <- "on"          # Enforce EFP everywhere
cfg$gms$s42_env_flow_scenario   <- 2             # Smakhtin algorithm (cell-specific)
cfg$gms$s42_efp_startyear       <- 2020          # Start earlier
cfg$gms$s42_efp_targetyear      <- 2030          # Full enforcement sooner
cfg$gms$s42_env_flow_fraction   <- 0.3           # Higher base fraction (if scenario=1)
cfg$gms$c42_watdem_scenario     <- "cc"          # Include climate change on demand
cfg$gms$c43_watavail_scenario   <- "cc"          # Include climate change on supply
```

⚠️ **Risk**: May cause infeasibility in arid regions (Middle East, North Africa, Central Asia). Check `oq43_water` marginals for binding constraints.

### Recipe 2: Irrigation Expansion Scenario

Allow unconstrained irrigation expansion with relaxed water limits.

```r
cfg$gms$area_equipped_for_irrigation <- "endo_apr13"  # Endogenous expansion
cfg$gms$s41_AEI_depreciation         <- 0             # No depreciation
cfg$gms$c42_env_flow_policy          <- "off"         # No EFP enforcement
cfg$gms$s42_env_flow_scenario        <- 0             # No environmental flows
cfg$gms$s42_irrig_eff_scenario       <- 3             # GDP-driven efficiency gains
cfg$gms$c30_bioen_water              <- "all"         # Allow irrigated bioenergy
```

⚠️ **Note**: Removing all water constraints (`s42_env_flow_scenario = 0`) produces unrealistic irrigation expansion. Consider keeping scenario=2 for more realistic results.

### Recipe 3: Climate-Impacted Water Availability

Isolate climate change effects on water by comparing `cc` vs `nocc` scenarios.

**Run A — With climate change (baseline)**:
```r
cfg$gms$c42_watdem_scenario     <- "cc"    # Climate affects crop water needs
cfg$gms$c43_watavail_scenario   <- "cc"    # Climate affects water supply
```

**Run B — Without climate change (counterfactual)**:
```r
cfg$gms$c42_watdem_scenario     <- "nocc"  # Freeze water needs at 1995
cfg$gms$c43_watavail_scenario   <- "nocc"  # Freeze water supply at 1995
```

**Run C — Freeze at historical fix year**:
```r
cfg$gms$c42_watdem_scenario     <- "nocc_hist"  # Historical then freeze at sm_fix_cc
cfg$gms$c43_watavail_scenario   <- "nocc_hist"
```

Compare results to quantify climate-driven water scarcity impacts on land use.

### Recipe 4: Groundwater Stress / Pumping Cost Scenario

Enable pumping costs to penalize unsustainable groundwater use.

```r
cfg$gms$s42_pumping                <- 1       # Enable pumping costs
cfg$gms$s42_multiplier_startyear   <- 2020    # Apply multiplier from 2020
cfg$gms$s42_multiplier             <- 5       # Increase pumping cost 5×
cfg$gms$c42_env_flow_policy        <- "on"    # Enforce environmental flows
cfg$gms$s42_env_flow_scenario      <- 2       # Smakhtin algorithm
```

⚠️ **Note**: Pumping costs are currently parameterized primarily for India (`f42_pumping_cost`). Results outside India may not reflect real-world groundwater costs. The groundwater infeasibility buffer in Module 43 (`presolve.gms:14-16`) adds free groundwater when exogenous demands exceed supply — this is NOT penalized even with `s42_pumping = 1`.

---

## Water Balance Architecture

### How Water Flows Through the Model

```
┌─────────────────────────────────────────────────────────────────────┐
│ MODULE 42: WATER DEMAND                                            │
│                                                                    │
│  Agriculture (endogenous):                                         │
│    q42_water_demand:                                               │
│      vm_watdem("agriculture",j) × v42_irrig_eff(j) =              │
│        Σ(kcr) vm_area(j,kcr,"irrigated") × ic42_wat_req_k(j,kcr)  │
│        + Σ(kli) vm_prod(j,kli) × ic42_wat_req_k(j,kli)            │
│                              × v42_irrig_eff(j)                    │
│                                                                    │
│  Non-agriculture (exogenous, fixed):                               │
│    vm_watdem("domestic"|"manufacturing"|"electricity",j)           │
│      ← f42_watdem_ineldo (WATERGAP/SSP scenario)                  │
│                                                                    │
│  Ecosystem (exogenous, fixed):                                     │
│    vm_watdem("ecosystem",j)                                        │
│      ← i42_env_flows (LPJmL Smakhtin or fraction)                 │
├─────────────────────────────────────────────────────────────────────┤
│ MODULE 43: WATER AVAILABILITY                                      │
│                                                                    │
│  v43_watavail("surface",j)                                         │
│    ← f43_wat_avail(t,j)    LPJmL growing-period runoff             │
│                                                                    │
│  v43_watavail("ground",j)   = 0                                   │
│    (auto-buffered if exogenous demand > surface supply)             │
│                                                                    │
│  CONSTRAINT q43_water(j2):                                         │
│    Σ(wat_dem) vm_watdem ≤ Σ(wat_src) v43_watavail                  │
│    → Shadow price = water scarcity value (USD/m³)                  │
├─────────────────────────────────────────────────────────────────────┤
│ MODULE 41: AREA EQUIPPED FOR IRRIGATION                            │
│                                                                    │
│  q41_area_irrig(j):                                                │
│    Σ(kcr) vm_area(j,kcr,"irrigated") ≤ vm_AEI(j)                  │
│    → Irrigated area cannot exceed equipped area                    │
│                                                                    │
│  q41_cost_AEI(i): expansion cost → objective function              │
└─────────────────────────────────────────────────────────────────────┘
```

### Decision Chain

1. **Optimizer decides** irrigated crop area `vm_area(j,kcr,"irrigated")`, bounded by `vm_AEI(j)`
2. **Module 42 calculates** agricultural water demand from irrigated areas + livestock
3. **Module 42 adds** exogenous demands (domestic, manufacturing, electricity, ecosystem)
4. **Module 43 enforces** total demand ≤ available surface water per cell
5. If water is scarce → `oq43_water.marginal > 0` → optimizer shifts to rainfed or other cells
6. If AEI expansion is needed → `q41_cost_AEI` adds annuitized investment cost to objective

### Environmental Flow Protection Logic

EFP implementation ramps linearly from `s42_efp_startyear` to `s42_efp_targetyear`:
- `"off"`: No EFP anywhere (ecosystem demand = base fraction only)
- `"on"`: EFP enforced everywhere (ecosystem demand = Smakhtin or higher fraction)
- `"mixed"`: EFP enforcement depends on development status (HIC=on, LIC/MIC=off), weighted by population share per region (`p42_EFP_region_shr`)

### Irrigation Efficiency

Conveyance loss factor (`v42_irrig_eff`) calculation depends on `s42_irrig_eff_scenario`:
- **Scenario 1**: Global constant (default 0.66)
- **Scenario 2** (default): Regional static, sigmoidal function of 1995 GDP per capita
- **Scenario 3**: Regional dynamic, sigmoidal function of current GDP per capita

Formula: `v42_irrig_eff = 1 / (1 + 2.718282^((-22160 - GDP_pc) / 37767))`

---

## Common Pitfalls

1. **Infeasibility from strict environmental flows**: Enabling `c42_env_flow_policy = "on"` with `s42_env_flow_scenario = 2` (Smakhtin) in arid regions can make the model infeasible. The water constraint `q43_water` is a hard cap with no slack variable. Check `oq43_water` marginals to identify binding cells, and consider a later `s42_efp_startyear` or the `"mixed"` policy mode.

2. **Mismatched climate scenarios**: Setting `c42_watdem_scenario = "cc"` but `c43_watavail_scenario = "nocc"` (or vice versa) creates an inconsistent water balance. Both should typically use the same climate scenario to avoid artifacts.

3. **Disabling water constraints entirely**: Setting `s42_env_flow_scenario = 0` removes environmental flow demands, but the `q43_water` constraint still exists. To fully remove water constraints, you must switch to the `agr_sector_aug13` realization, which excludes non-agricultural sectors — but this still enforces agricultural water limits.

4. **No inter-cell water transfer**: Water availability is enforced per cell (`j2`). There is no mechanism for water trade or transfer between cells. Arid cells with high agricultural potential may be infeasible even if neighboring cells have surplus water.

5. **Free groundwater buffer hides stress**: Module 43's infeasibility buffer (`presolve.gms:14-16`) automatically adds zero-cost groundwater when exogenous demands exceed surface water. This means the model always solves, but results may mask unsustainable groundwater mining. Check `v43_watavail.l("ground",j)` in outputs for non-zero values.

6. **Irrigation expansion without water**: Setting `area_equipped_for_irrigation = "endo_apr13"` allows unlimited irrigation expansion, but this is only economically constrained (via `q41_cost_AEI`), not physically constrained by water availability alone. The water constraint `q43_water` must also be active and binding to limit irrigation realistically.

7. **Pumping costs limited to India**: The `s42_pumping = 1` switch activates pumping costs, but the input data (`f42_pumping_cost`) is parameterized primarily for India. Results for other regions will have zero or minimal pumping cost and should be interpreted cautiously.

---

## Diagnostic Outputs

Key outputs for analyzing water scarcity results:

| Output Variable | What It Shows |
|----------------|---------------|
| `oq43_water(t,j,"marginal")` | Water scarcity shadow price — positive = constraint binding |
| `oq43_water(t,j,"level")` | Slack in water constraint — 0 = fully utilized |
| `ov43_watavail(t,wat_src,j,"level")` | Water available by source and cell |
| `ov43_watavail(t,"ground",j,"level")` | Non-zero = infeasibility buffer activated |
| `vm_watdem.l("agriculture",j)` | Agricultural water withdrawals |
| `vm_AEI.l(j)` | Area equipped for irrigation (result) |

---

## Module Cross-References

- [Module 42 — Water Demand](../../modules/module_42.md)
- [Module 43 — Water Availability](../../modules/module_43.md)
- [Module 41 — Area Equipped for Irrigation](../../modules/module_41.md)
- [Water Balance Conservation](../../cross_module/water_balance_conservation.md)

## Related Helpers & Docs

- [Debugging Infeasibility](debugging_infeasibility.md) — water-related infeasibility diagnosis
- [Scenario: Carbon Pricing](scenario_carbon_pricing.md) — carbon pricing can interact with land use and irrigation
- [Realization Selection](realization_selection.md) — choosing between `all_sectors_aug13` and `agr_sector_aug13`
- [Modification Impact Analysis](modification_impact_analysis.md) — assessing impact of water parameter changes

---

## Lessons Learned

*(append-only — add dated entries below as discoveries are made)*
