# Q4: Land Conversion Costs (M39), Transport Costs (M40), and Urban Land (M34) in the Objective

**Sources used**: `modules/module_39.md`, `modules/module_40.md`, `modules/module_34.md`, `config/default.cfg` (realization confirmation)
**Status**: 🟡 Documented (AI docs; no raw GAMS read this session)
**Default realizations confirmed from `config/default.cfg`**: M39 = `calib`, M40 = `gtap_nov12`, M34 = `exo_nov21`

---

## (a) Module 39 — Land Conversion Costs

### Default realization: `calib`

### Cost variable

**`vm_cost_landcon(j, land)`** — land conversion costs, units: million USD17MER per year.

Declaration: `modules/39_landconversion/calib/declarations.gms:13`.
Dimensions: over cell `j` and the full 7-member `land` set. Only `crop`, `past`, `forestry`, and `urban` carry non-zero establishment costs; `primforest`, `secdforest`, `other` are initialized to zero in `preloop.gms:8` and never overwritten.

### Defining equation

**`q39_cost_landcon(j2, land)`** (`modules/39_landconversion/calib/equations.gms:12-15`):

```
vm_cost_landcon(j2,land) =e=
  (vm_landexpansion(j2,land)*sum((ct,cell(i2,j2)), i39_cost_establish(ct,i2,land))
  - vm_landreduction(j2,land)*sum((ct,cell(i2,j2)), i39_reward_reduction(ct,i2,land)))
  * sum((cell(i2,j2),ct), pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
```

In compact form:

```
Cost(j, land) = [Expansion(j,land) × Cost_per_ha(land)
                 − Reduction(j,land) × Reward_per_ha(land)]
                × r/(1+r)
```

The annuity factor `r/(1+r)` converts a one-time physical action into an equivalent annual cost (no depreciation term — land doesn't wear out; contrast Module 38 which uses `(r+d)/(1+r)`).

### What land transitions trigger it

The two driving variables come from Module 10 (Land):

- **`vm_landexpansion(j, land)`** — area of each land type expanding this timestep (mio. ha). A positive expansion entry triggers a cost.
- **`vm_landreduction(j, land)`** — area of each land type contracting this timestep (mio. ha). A positive reduction entry triggers a reward (negative cost) — but only for cropland in regions where `i39_reward_reduction > 0`.

The cost depends only on the **target** land type, not the source (`module_39.md §10, point 1`). Converting forest to cropland costs the same as converting pasture to cropland (both pay `s39_cost_establish_crop` = 12,300 USD17/ha before regional calibration). The four non-zero base costs are:

| Land type | Base cost (USD17/ha) | Regional calibration? |
|-----------|---------------------|-----------------------|
| crop | 12,300 | Yes — multiplied by `i39_calib(t,i,"cost")` (`presolve.gms:12`) |
| past | 9,840 | No — fixed globally (`presolve.gms:14`) |
| forestry | 1,230 | No — fixed globally (`presolve.gms:15`) |
| urban | 12,300 | No — fixed globally (`presolve.gms:16`) |

Reduction rewards apply only to cropland in specific regions (where the 1995–2015 historical trend shows decline and `i39_calib("cost") > 1`), via `i39_reward_reduction(t,i,"crop") = s39_reward_crop_reduction × i39_calib(t,i,"reward")` (`presolve.gms:13`).

### Path to objective

`vm_cost_landcon(j, land)` is summed into Module 11 (Costs), which aggregates regional costs into `vm_cost_glo` — the scalar minimized by Module 80 (Optimization).

---

## (b) Module 40 — Transport Costs

### Default realization: `gtap_nov12`

### Cost variable

**`vm_cost_transp(j2, k)`** — intraregional transportation costs, units: million USD17MER per year.

Declaration: `modules/40_transport/gtap_nov12/declarations.gms:13`.
Dimensions: cell `j2` × commodity `k` (the active commodity set, a subset of `kall`).

### Defining equation

**`q40_cost_transport(j2, k)`** (`modules/40_transport/gtap_nov12/equations.gms:11-13`):

```
vm_cost_transp(j2,k) =e= vm_prod(j2,k) * f40_distance(j2) * f40_transport_costs(k);
```

### What it scales with

The formula is linear in all three terms:

1. **`vm_prod(j2, k)`** — cell-level production by commodity (mio. tDM/yr), provided by Module 17. Doubling production doubles transport cost.
2. **`f40_distance(j2)`** — travel time from cell centroid to nearest city of ≥ 50,000 inhabitants (minutes), from Nelson et al. 2008 circa-2000 data (`input.gms:15-21`). Static throughout the simulation (no infrastructure improvement modeled). Doubling remoteness doubles cost.
3. **`f40_transport_costs(k)`** — commodity-specific cost factor (USD17MER per tDM per minute), calibrated to GTAP 7 1995 data (`input.gms:23-28`). Captures differential transport intensity by commodity (e.g., bulk cereals vs. high-value oilseeds).

**Pasture exception**: `s40_pasture_transport_costs = 0` (`input.gms:10`) — grass is consumed in situ by grazing animals and is not transported to market.

**Path to objective**: `vm_cost_transp(j, k)` flows into Module 11 via the aggregation `sum((cell(i2,j2),k), vm_cost_transp(j2,k))` inside `q11_cost_reg(i2)` (`modules/11_costs/default/equations.gms:21`), then to `vm_cost_glo` and Module 80.

**Off realization note**: The `off` realization fixes `vm_cost_transp.fx(j,k) = 0` (`off/presolve.gms:9`), removing transport costs entirely for counterfactual analysis. Not the default.

---

## (c) Urban Land (Module 34) and Land Conversion in the Default Config

### Default realization: `exo_nov21`

Urban land in MAgPIE is **not conversion-costed the same way as agricultural transitions**. The relevant facts:

### Urban expansion does incur a land conversion cost via M39

`s39_cost_establish_urban` = 12,300 USD17/ha (`modules/39_landconversion/calib/input.gms:13`), equal to the cropland rate. When `vm_landexpansion(j,"urban") > 0` — i.e., when urban land expands — Module 39 applies the same `q39_cost_landcon` equation and charges `vm_cost_landcon(j,"urban")`. However, there is **no reduction reward for urban land**: `i39_reward_reduction` for urban is fixed to zero in `preloop.gms:9` and never overwritten. Urban transitions are one-way in practice.

### Urban land expansion is exogenous, not optimized

Module 34 (`exo_nov21`) drives urban expansion from LUH3 scenario data, not from economic optimization. The regional urban total is a **hard equality constraint** (`q34_urban_land`, `equations.gms:30-31`):

```
sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2))
```

At t=1, `vm_land.fx(j,"urban")` is fixed to the prescribed value (`presolve.gms:11`); in subsequent timesteps the cell-level value is initialized to the target but can deviate, subject to strong punishment costs.

### Module 34's own cost variable: `vm_cost_urban(j)`

**`vm_cost_urban(j)`** — cell-level deviation penalty, equation `q34_urban_cell` (`equations.gms:25-26`):

```
vm_cost_urban(j2) =e= (v34_cost1(j2) + v34_cost2(j2)) * s34_urban_deviation_cost
```

where `s34_urban_deviation_cost` = 1e6 USD17/ha (`input.gms:13`). This is a **technical steering cost**, not a physical conversion cost — it fires only when the optimizer cannot match the prescribed cell-level pattern (e.g., a cell is fully protected). In a feasible, unconstrained solution, `vm_cost_urban(j)` approaches zero. The variable is passed to Module 11 and enters the objective, but its role is to enforce spatial allocation, not to price land transformation work.

### Summary for M34: two separate cost channels

| Channel | Variable | Module | What it represents |
|---------|----------|--------|--------------------|
| Physical conversion cost | `vm_cost_landcon(j,"urban")` | M39 | Establishment cost for urban expansion (12,300 USD17/ha × annuity factor) |
| Spatial deviation penalty | `vm_cost_urban(j)` | M34 | Punishment for deviating from prescribed cell-level urban area (1e6 USD17/ha × deviation area) |

Both flow through Module 11 to `vm_cost_glo`. They serve different purposes: M39 prices the real-world work of establishing urban land; M34's `vm_cost_urban` is a mathematical steering device to enforce the exogenous trajectory.

---

## vm_cost_* variable register (this question)

| Variable | Module | Realization | Declaration file |
|----------|--------|-------------|-----------------|
| `vm_cost_landcon(j, land)` | M39 | `calib` | `modules/39_landconversion/calib/declarations.gms:13` |
| `vm_cost_transp(j, k)` | M40 | `gtap_nov12` | `modules/40_transport/gtap_nov12/declarations.gms:13` |
| `vm_cost_urban(j)` | M34 | `exo_nov21` | `modules/34_urban/exo_nov21/scaling.gms:8` (scaled); declared in `exo_nov21/equations.gms:25-26` |

---

## Source statement

🟡 Based on AI documentation (docs-only answer):
- `modules/module_39.md` (realization `calib`, full coverage)
- `modules/module_40.md` (realization `gtap_nov12`, full coverage)
- `modules/module_34.md` (realization `exo_nov21`, full coverage)
- `config/default.cfg` (realization confirmation — grep verified this session)

No raw GAMS `.gms` files read. Line numbers cited from AI docs; they were verified against code at doc creation time (2025-10-13) but may have shifted since.
