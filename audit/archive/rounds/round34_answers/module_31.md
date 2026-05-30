# Module 31 (Pasture): Area, Yields, vm_land Population, and Output Consumers

## Default Realization

The default realization is `endo_jun13`, confirmed by `config/default.cfg`:
`cfg$gms$past <- "endo_jun13"`. An alternative `static` realization exists but is effectively deprecated — a `not_used.txt` file is present in the static directory. All descriptions below apply to `endo_jun13`.

---

## How Pasture Area Is Determined

Pasture area is **endogenous** — it is not prescribed exogenously but is determined through the optimization itself. The mechanism works as a chain:

1. Module 70 (Livestock) computes feed demand including the "pasture" commodity.
2. Module 16 (Demand) and Module 21 (Trade) propagate that demand into a regional supply balance.
3. Module 31 constrains how much pasture biomass can be produced from a given pasture area via the production-capacity inequality.
4. Module 10 (Land) allocates area across the seven land types — including `"past"` — to satisfy all demands at minimum cost.

The variable `vm_land(j,"past")` is therefore a decision variable owned by Module 10; Module 31 shapes its lower bound (via conservation constraints) and constrains what production is achievable given any particular area value.

---

## How Yields Enter the Module

Rainfed pasture yields come from Module 14 (Yields) as `vm_yld(j,"pasture","rainfed")` (units: tDM/ha/yr). This is the only water source used — Module 31 does not permit irrigated pasture. Yields are treated as inputs from Module 14; they are not computed within Module 31 itself.

---

## Key Equations (5 Total in endo_jun13)

### 1. `q31_prod` — Production Capacity Constraint
**Location**: `modules/31_past/endo_jun13/equations.gms:16-18`
**Dimensions**: `(j2)` — cells

```gams
vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed")
```

This is the central equation. It is an **inequality** (=l=), not an equality, allowing pasture to be underutilized. The model allocates just enough `vm_land(j,"past")` to satisfy `vm_prod` demand; the inequality permits grazing intensity below the rainfed yield ceiling. This is the mechanism that makes pasture area endogenous: the optimizer can expand or contract `vm_land(j,"past")` until feed supply requirements are met.

### 2. `q31_carbon` — Above-Ground Carbon Stocks
**Location**: `modules/31_past/endo_jun13/equations.gms:22-24`
**Dimensions**: `(j2, ag_pools, stockType)`

```gams
vm_carbon_stock(j2,"past",ag_pools,stockType) =e=
    m_carbon_stock(vm_land,fm_carbon_density,"past")
```

Calculates above-ground carbon stocks (vegetation and litter pools) on pasture land using the `m_carbon_stock` macro. Below-ground (soil) carbon is handled by Module 59, not here.

### 3. `q31_cost_prod_past` — Pasture Production Costs
**Location**: `modules/31_past/endo_jun13/equations.gms:31-32`
**Dimensions**: `(i2)` — regions

```gams
vm_cost_prod_past(i2) =e= sum(cell(i2,j2), vm_prod(j2,"pasture")) * s31_fac_req_past
```

A calibration artifact. The scalar `s31_fac_req_past` is 1 USD17MER/tDM in the initial calibration timestep (preventing overproduction during pasture calibration) and is set to 0 in `postsolve.gms:10` for all subsequent timesteps. The declared output variable `vm_cost_prod_past(i)` is transmitted to Module 11.

### 4. `q31_bv_manpast` — Managed Pasture Biodiversity Value
**Location**: `modules/31_past/endo_jun13/equations.gms:38-40`
**Dimensions**: `(j2, potnatveg)`

```gams
vm_bv(j2,"manpast",potnatveg) =e=
    vm_land(j2,"past") * fm_luh2_side_layers(j2,"manpast")
    * fm_bii_coeff("manpast",potnatveg) * fm_luh2_side_layers(j2,potnatveg)
```

Multiplies total pasture area by the (fixed) LUH2 managed-pasture share, then by the BII coefficient and the potential natural vegetation share.

### 5. `q31_bv_rangeland` — Rangeland Biodiversity Value
**Location**: `modules/31_past/endo_jun13/equations.gms:42-44`
**Dimensions**: `(j2, potnatveg)`

Identical structure to `q31_bv_manpast`, but uses `"rangeland"` for the LUH2 share and BII coefficient. Rangeland has lower management intensity, so BII coefficients are typically closer to 1. The LUH2 shares satisfy: `fm_luh2_side_layers(j,"manpast") + fm_luh2_side_layers(j,"rangeland") = 1` across the pasture cell.

---

## How vm_land Is Populated for the Pasture Land Type

`vm_land(j,"past")` is not declared or assigned within Module 31 — it is declared and owned by Module 10. Module 31's role is twofold:

1. **Lower bound** (`presolve.gms:9`):
   ```gams
   vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))
   ```
   Protected grassland/pasture areas from Module 22 establish a floor that the optimizer cannot breach.

2. **Productive constraint** (`q31_prod`): The inequality `vm_prod =l= vm_land * vm_yld` creates the incentive for the optimizer to allocate sufficient `vm_land(j,"past")` to meet pasture feed demand. The endogenous value is therefore set by the overall NLP solve, not by any explicit assignment within Module 31.

---

## Consumers of Module 31 Outputs

| Output variable | Consuming module | Purpose |
|---|---|---|
| `vm_cost_prod_past(i)` | Module 11 (Costs) | Enters objective function (calibration only; zero after first timestep) |
| `vm_carbon_stock(j,"past",ag_pools,stockType)` | Module 52 (Carbon) | Above-ground pasture carbon stocks for carbon accounting and CO2 flux |
| `vm_bv(j,"manpast",potnatveg)`, `vm_bv(j,"rangeland",potnatveg)` | Module 44 (Biodiversity) | Biodiversity Intactness Index aggregation |
| `vm_prod(j,"pasture")` (constrained here) | Module 70 (Livestock) via supply chain | Feed availability for livestock demand satisfaction |
| `vm_land(j,"past")` (bounded here) | Module 10 (Land) | Enters land balance conservation constraint (land types must sum to total) |

The critical linkage in the system is: Module 70 demand → Module 31 production constraint → Module 10 land allocation → `vm_land(j,"past")` value. This loop — not any single bilateral dependency — is what makes pasture area endogenous.

---

## What Module 31 Does NOT Model

- Irrigated pastures (rainfed only)
- Endogenous grazing intensity or management type (managed/rangeland split is fixed via LUH2 side layers)
- Pasture degradation or productivity feedbacks from overgrazing
- Below-ground carbon (handled by Module 59)
- Seasonal dynamics or stocking density limits
- Fertilization, reseeding, or prescribed burning

---

## Source

All claims based on `modules/module_31.md` (magpie-agent AI documentation), verified against:
- `modules/31_past/endo_jun13/equations.gms` (5 equations)
- `modules/31_past/endo_jun13/declarations.gms`
- `modules/31_past/endo_jun13/input.gms`
- `modules/31_past/endo_jun13/presolve.gms`
- `modules/31_past/endo_jun13/preloop.gms`
- Last verification date per docs: 2025-10-13

---

## Epistemic Status

- Default realization name (`endo_jun13`), equation names, variable names, and formulas: 🟢 **Verified** — read from `modules/module_31.md`, which was cross-referenced against GAMS source at verification date 2025-10-13.
- Consumer module list: 🟡 **Documented** — drawn from the module doc's "Module Connections" section; not independently re-checked against consuming modules' source files this session.
- Line numbers cited: carry a **caveat** — verified at the doc's last sync; code changes since 2025-10-13 may have shifted them. For critical modification work, re-verify against current `../modules/31_past/endo_jun13/equations.gms`.
