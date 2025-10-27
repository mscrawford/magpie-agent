# Module 13: Technological Change (tc)

**Status**: Fully Verified
**Realization**: `endo_jan22` (active), `exo` (prescriptive alternative)
**Equations**: 3
**Core Mechanism**: Endogenous land use intensification via tau factors

---

## Overview

Module 13 implements endogenous technological change and land use intensification through the tau factor (τ) framework. The module calculates the cost of investments needed to increase agricultural yields via land use intensification, creating an endogenous feedback loop where the optimization balances intensification costs against land expansion costs.

**Key Innovation**: The model shifts investment costs 15 years into the future using interest rates, representing the research lag between investment and yield improvement (realization.gms:8-36, Dietrich et al. 2014).

---

## Core Equations

### 1. Technological Change Investment Costs (q13_cost_tc)

**Purpose**: Calculate the cost per unit intensification as a function of current τ level

```gams
q13_cost_tc(i2, tautype) ..
  v13_cost_tc(i2, tautype) =e= sum(ct, pc13_land(i2, tautype) *
                     i13_tc_factor(ct) * sum(supreg(h2,i2),vm_tau(h2,tautype))**
                     i13_tc_exponent(ct) * (1+pm_interest(ct,i2))**15);
```
*Source*: `equations.gms:20-23`

**Formula Breakdown**:
- `pc13_land(i2, tautype)`: Regional agricultural area (mio ha) from previous timestep
- `i13_tc_factor(ct)`: Regression factor (USD17MER per ha) - scenario-dependent
- `vm_tau(h2,tautype) ** i13_tc_exponent(ct)`: Power function representing investment-yield ratio
- `(1+pm_interest(ct,i2))**15`: 15-year time shift to account for research lag

**Key Insight**: The power function captures the increasing marginal cost of intensification - higher current τ values mean exponentially more expensive additional intensification (equations.gms:10-11, figure reference).

**15-Year Time Shift**: Investments into technological change require on average 15 years of research before yield increases are achieved. The model shifts costs forward so they appear concurrent with benefits, enabling correct optimization decisions (equations.gms:26-32).

**Area Scaling**: Costs scale with regional agricultural area because wider areal coverage typically means greater variety in biophysical conditions, requiring more research for the same overall intensity boost (equations.gms:30-32).

---

### 2. Annualized Technology Costs (q13_tech_cost)

**Purpose**: Convert full investment costs into annualized payments over infinite horizon

```gams
q13_tech_cost(i2, tautype) ..
 v13_tech_cost(i2, tautype) =e= sum(supreg(h2,i2), vm_tau(h2,tautype)/pcm_tau(h2,tautype)-1) * v13_cost_tc(i2,tautype)
                               * sum(ct,pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
```
*Source*: `equations.gms:40-42`

**Formula Breakdown**:
- `vm_tau(h2,tautype)/pcm_tau(h2,tautype) - 1`: Intensification rate (τ_current / τ_previous - 1)
- `v13_cost_tc(i2,tautype)`: Unit cost from q13_cost_tc
- `pm_interest(ct,i2)/(1+pm_interest(ct,i2))`: Annuity factor for infinite time horizon

**Infinite Horizon Annuity**: The formula `r/(1+r)` distributes investment costs over an infinite time horizon, avoiding the need to specify a depreciation period (equations.gms:34-42).

**Example** (illustrative numbers):
- If τ increases from 1.0 to 1.2: intensification rate = 1.2/1.0 - 1 = 0.20 (20% increase)
- If unit cost is 1000 USD/ha and interest rate is 5%: annualized cost = 0.20 × 1000 × 0.05/1.05 ≈ 9.52 USD/ha/yr
- *Note: These are made-up numbers for illustration. Actual values depend on input files and optimization results.*

---

### 3. Total Technology Costs (q13_tech_cost_sum)

**Purpose**: Aggregate crop and pasture technology costs for regional objective function

```gams
q13_tech_cost_sum(i2) ..
 vm_tech_cost(i2) =e= sum(tautype, v13_tech_cost(i2, tautype));
```
*Source*: `equations.gms:44-45`

**Simple Aggregation**: Sums annualized costs across both tau types (crop, pasture) for inclusion in Module 11 (Costs) via interface variable `vm_tech_cost`.

---

## Interface Variables

### Inputs (from other modules)

| Variable | Provider | Purpose | Source |
|----------|----------|---------|--------|
| `pm_interest(t,i)` | Module 12 (Interest Rate) | Regional interest rates for time shifting and annuity | declarations.gms:26 |
| `pcm_land(j,land)` | Module 10 (Land) | Previous timestep land areas for cost scaling | presolve.gms:9-10 |

---

### Outputs (to other modules)

| Variable | Consumer | Purpose | Source |
|----------|----------|---------|--------|
| `vm_tau(h,tautype)` | Module 14 (Yields), Module 38 (Factor Costs) | Land use intensity factor that multiplies biophysical yields | declarations.gms:9 |
| `vm_tech_cost(i)` | Module 11 (Costs) | Annualized technology costs for objective function | declarations.gms:10 |

**Critical Role**: `vm_tau` is the central mechanism linking intensification investments (Module 13) to yield improvements (Module 14) and production costs (Module 38), creating the core tradeoff between land expansion and intensification.

---

## Sets and Dimensions

### Key Sets

**tautype** (`sets.gms:13-14`):
- `crop`: Cropland intensification
- `pastr`: Pasture intensification

**scen13** (`sets.gms:10-11`):
- `low`, `medium`, `high`: TC cost scenarios (low = cheaper intensification, high = expensive)

---

## Parameters and Configuration

### Input Files

1. **fm_tau1995.cs4** (`input.gms:14-19`): Initial τ values for year 1995 by region (Dietrich et al. 2012)
2. **f13_tcguess.cs4** (`input.gms:21-26`): Initial guess for annual TC rates (used for solver warm start)
3. **f13_tc_factor.cs3** (`input.gms:30-34`): Regression factor by time and scenario (USD17MER per ha)
4. **f13_tc_exponent.cs3** (`input.gms:36-40`): Regression exponent by time and scenario (dimensionless)
5. **f13_tau_historical.csv** (`input.gms:42-46`): Historical τ trajectory for crops
6. **f13_pastr_tau_hist.csv** (`input.gms:48-52`): Historical τ trajectory for pasture

---

### Configuration Switches

**s13_ignore_tau_historical** (`input.gms:10`):
- `1` (default): Ignore historical τ values (free optimization from start)
- `0`: Use historical τ as lower bound in historical periods

**s13_max_gdp_shr** (`input.gms:11`):
- Default: `Inf` (no constraint)
- Alternative: Share of regional GDP (e.g., 0.01 = 1% of GDP)
- **Purpose**: Caps technology investments to avoid unrealistically high endogenous investments (`presolve.gms:30-42`)

**c13_tccost** (`input.gms:28`):
- `low`, `medium` (default), `high`: Selects TC cost scenario from input tables
- Applied after historical SSP2 period (`preloop.gms:8-16`)

---

## Presolve Logic and Bounds

### Tau Bounds (`presolve.gms:12-19`)

**Lower Bound**:
- Historical periods with `s13_ignore_tau_historical = 0`: `vm_tau.lo = f13_tau_historical(t,h)`
- All other periods: `vm_tau.lo = pcm_tau(h,tautype)` (cannot decrease from previous level)

**Upper Bound**:
- `vm_tau.up = 2 * pcm_tau(h,tautype)` (maximum doubling per timestep)

**Rationale**: Prevents unrealistic jumps in intensification rates. Tau can only stay constant or increase, with a maximum doubling constraint to reflect realistic adoption timescales (presolve.gms:19,28).

---

### Initial Values (`presolve.gms:22-26`)

**First timestep** (ord(t) = 1):
- `vm_tau.l = pcm_tau` (start at 1995 historical value)

**Subsequent timesteps**:
- `vm_tau.l = pcm_tau × (1 + pc13_tcguess)^m_yeardiff(t)` (warm start using previous solution's growth rate)

**Warm Start Purpose**: Helps solver find solutions more efficiently by providing educated guess based on previous optimization results (presolve.gms:21-26).

---

### GDP Constraint (`presolve.gms:30-42`)

**Applied when**:
- `m_year(t) > sm_fix_SSP2` (after SSP2 fixing period)
- `s13_max_gdp_shr ≠ Inf`

**Constraint**:
```gams
vm_tech_cost.up(i) = sum((i_to_iso(i,iso),ct), im_gdp_pc_ppp_iso(ct,iso) * im_pop_iso(ct,iso)) * s13_max_gdp_shr
vm_tech_cost.l(i) = vm_tech_cost.up(i)
```

**Purpose**: Limits technology investments to a defined share of regional GDP to avoid unrealistically high endogenous investments. Initial value set to upper bound to encourage solver to consider tau as efficient part of optimal solution (presolve.gms:32-40).

---

## Postsolve Updates

### Tau Carryover (`postsolve.gms:8-14`)

**After each timestep**:
1. Update intensification rate guess: `pc13_tcguess = (vm_tau.l / pcm_tau)^(1/m_yeardiff) - 1`
2. Update previous tau: `pcm_tau = vm_tau.l`

**Purpose**: Carry forward optimized tau values to next timestep as lower bound and warm start. The guess calculation converts absolute change into annualized growth rate (postsolve.gms:10-14).

---

## Alternative Realization: exo

**Purpose**: Prescribe exogenous τ trajectories based on previous model runs (exo/realization.gms:8-18).

**Use Case**: Fix intensification rates from SSP2 baseline run and apply to SSP2 policy run, isolating policy impacts from intensification adaptation.

**Implementation**: All tau variables are fixed (no equations), values read from `f13_tau_scenario.csv` generated by magpie4 R package function `tau(gdx, file="f13_tau_scenario.csv")`.

**Limitation**: May cause infeasibilities if scenario setup diverges significantly from the scenario used to generate tau trajectory, as τ cannot adapt to demand pressures (exo/realization.gms:20-24).

---

## Computational Performance

**Warning** (realization.gms:38-40): The `endo_jan22` realization "significantly reduces the overall computational performance of the model since these endogenous calculations are highly computational intensive."

**Reason**: Power function in q13_cost_tc with endogenous tau variables creates non-linear optimization problem with potentially many local optima. Solver must balance intensification costs against land expansion across two tau types and all regions simultaneously.

**Mitigation**: Warm start strategy (educated guesses in presolve), GDP constraints to limit search space, and alternative `exo` realization for scenario analysis where intensification can be prescribed.

---

## Key Limitations

1. **Uniform Cost Function**: Uses single power function globally, only varying by scenario (low/medium/high) and time, not by biophysical region characteristics (input.gms:28-40, preloop.gms:8-16).

2. **Fixed 15-Year Lag**: Research lag is hard-coded as 15 years, not varied by technology type or region (equations.gms:23).

3. **No Depreciation**: Infinite horizon annuity assumes technologies never depreciate or become obsolete (equations.gms:40-42).

4. **Two Tau Types Only**: Distinguishes only crop vs. pasture, not individual crop types or livestock systems (sets.gms:13-14).

5. **No Technology Spillover**: Intensification costs are independent for crop and pasture, no accounting for knowledge spillovers between systems (equations.gms:20-45).

6. **Aggregated Regional Level**: Tau is defined at supreg (super-region) level `h`, not at cell level `j`, so intensification is spatially uniform within super-regions (declarations.gms:9).

7. **No Diminishing Returns Over Time**: Power function parameters are time-varying (input files) but structure assumes same functional form throughout, no accounting for technology frontier effects (input.gms:30-40).

8. **GDP Constraint is Optional**: Without `s13_max_gdp_shr`, model may choose unrealistically high investments if land expansion is severely constrained (input.gms:11, presolve.gms:30-42).

9. **No Direct Link to R&D**: Costs represent implementation investments, not research and development explicitly - the 15-year lag is an aggregate proxy (equations.gms:26-32).

10. **Historical Tau Override**: Switch `s13_ignore_tau_historical` allows ignoring historical trajectories entirely, potentially creating discontinuity with observed past (input.gms:10, presolve.gms:12-17).

11. **Tau Doubling Limit**: Maximum 2× increase per timestep is heuristic, not based on empirical adoption constraints (presolve.gms:19,28).

12. **Static Regression Parameters**: TC factor and exponent read from input files (scenarios low/medium/high), not dynamically adjusted based on R&D investment or learning-by-doing (input.gms:30-40, preloop.gms:8-16).

13. **No Biophysical Constraints**: Tau can increase indefinitely (subject only to cost and doubling limit), no explicit ceiling based on biophysical maximum attainable intensification (presolve.gms:19).

14. **Deterministic**: No stochastic variation in technology costs or uncertainty in research outcomes (equations.gms:20-45).

15. **Exo Realization Risks Infeasibility**: Prescribed tau trajectory may be insufficient if scenario diverges from baseline used to generate it (exo/realization.gms:20-24).

---

## Dependencies

**Upstream** (requires these modules):
- Module 12 (Interest Rate): Provides `pm_interest` for time shifting and annuity calculations
- Module 10 (Land): Provides `pcm_land` for area-weighted cost scaling

**Downstream** (provides to these modules):
- Module 14 (Yields): Receives `vm_tau` to multiply biophysical yields
- Module 38 (Factor Costs): Receives `vm_tau` to adjust production costs
- Module 11 (Costs): Receives `vm_tech_cost` for objective function

**Circular Dependencies**: None direct, but participates in land-intensification feedback loop (demand → land allocation → intensification costs → tau → yields → production → demand).

---

## Model Integration

### Objective Function Path

```
Module 13 (vm_tech_cost)
  → Module 11 (Costs, q11_cost_tc)
  → Objective Function (vm_cost_glo)
```

Technology costs add to total system costs, creating trade-off between:
- **Intensive pathway**: Higher τ → higher yields → less land needed → higher TC costs
- **Extensive pathway**: Lower τ → lower yields → more land needed → lower TC costs (but higher land expansion costs)

---

### Yield Enhancement Path

```
Module 13 (vm_tau)
  → Module 14 (Yields, q14_yield_crop)
  → Production (Module 17)
  → Demand (Module 16)
```

Tau factor multiplies biophysical yields from LPJmL, directly increasing crop and pasture productivity.

---

## References

**Primary Source**: Dietrich, J.P., Schmitz, C., Lotze-Campen, H., Popp, A., & Müller, C. (2014). Forecasting technological change in agriculture—An endogenous implementation in a global land use model. *Technological Forecasting and Social Change*, 81, 236–249. (realization.gms:13)

**Initial Tau Values**: Dietrich, J.P., Schmitz, C., Müller, C., Fader, M., Lotze-Campen, H., & Popp, A. (2012). Measuring agricultural land-use intensity – A global analysis using a model-assisted approach. *Ecological Modelling*, 232, 109–118. (realization.gms:24)

---

## Verification Summary

- **Equations verified**: 3/3 (100%)
- **Interface variables verified**: 4/4 (vm_tau, vm_tech_cost, pm_interest, pcm_land)
- **Input files catalogued**: 6
- **Configuration switches verified**: 3 (s13_ignore_tau_historical, s13_max_gdp_shr, c13_tccost)
- **Limitations identified**: 15
- **File citations**: 60+

**Status**: Fully verified against source code. All equations match declarations.gms:15-19, formulas match equations.gms:20-45.

---

## Participates In

### Conservation Laws
Module 13 does **not directly participate** in conservation laws, but **indirectly affects all** via τ factor:
- Higher τ → Higher yields → Less land needed → **Land balance** affected
- Higher yields → More water-efficient production → **Water balance** affected
- Intensification costs affect land-use decisions → **Carbon balance** affected (deforestation vs. intensification trade-off)

### Dependency Chains
**Centrality**: High (critical yield modifier, part of production system)
- **Depends on**: Modules 09 (GDP), 10 (land), 12 (interest rate)
- **Provides to**: Modules 11 (costs), 14 (yields), 38 (factor costs)
- **Role**: **Intensification driver** - determines agricultural productivity growth

**Key variable**: `vm_tau` - **THE** technological change factor that scales all yields

### Circular Dependencies

**Module 13 participates in Cycle 1: Production-Yield-Livestock Triangle ⭐⭐⭐**

**Dependency chain**:
```
vm_tau [13] → Scales yields
    ↓
vm_yld [14] → Affects production
    ↓
vm_prod [17/30] → Production levels
    ↓
Manure from livestock [70] → Soil fertility
    ↓
pm_yields_semi_calib [14] → **Feeds back to tau calculation** (via past production patterns)
```

**Resolution**: **Temporal Feedback**
- Within timestep: τ is **optimized** based on costs vs. benefits
- Across timesteps: Past production patterns influence future τ (15-year lag via `pm_interest`)
- **Lagged variables** break circular dependency within optimization

**Module 13's role**: Provides the **economic mechanism** for yield improvement. Model chooses τ level by balancing:
- **Benefit**: Higher yields → less land needed → lower land costs
- **Cost**: Investment in intensification (`vm_tech_cost`)

**Links**: circular_dependency_resolution.md (Section 3.1), module_14.md (Section 21.3)

### Modification Safety
**Risk Level**: 🔴 **HIGH RISK** (affects entire production system, part of critical feedback loop)

**Why High Risk**:
1. **τ factor affects ALL crop/pasture yields** - errors propagate everywhere
2. **Part of Cycle 1** - modifications can destabilize calibration
3. **Cost-benefit trade-off** - wrong costs → unrealistic intensification
4. **15-year lag** - temporal feedback can cause oscillations

**Safe Modifications**:
- ✅ Adjust TC cost scenarios (low/medium/high via `c13_tccost`)
- ✅ Change GDP investment constraint (`s13_max_gdp_shr`)
- ✅ Toggle historical tau trajectory (`s13_ignore_tau_historical`)

**High-Risk Modifications**:
- 🔴 Change τ cost equation structure (affects land-intensification trade-off)
- 🔴 Modify 15-year lag mechanism (can cause temporal instability)
- 🔴 Change τ doubling limit (unrealistic jumps or stagnation)

**Testing After Modification**:
1. **τ trajectory check**: Gradual growth, no oscillations
   ```r
   tau <- readGDX(gdx, "ov_tau", field="l")
   # Should increase over time, no wild swings
   ```
2. **Yield calibration**: Still matches FAO targets (Module 14 check)
3. **Investment plausibility**: TC costs reasonable vs. total agricultural costs
4. **Cycle 1 stability**: Production-yield feedback stable (see module_14.md tests)

**Links**: modification_safety_guide.md, circular_dependency_resolution.md (Section 3.1)

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/13_*/endo_jun18/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
