# Highest-Centrality Modules and Modification Risk in MAgPIE

**Question**: Which MAgPIE modules are highest-centrality and riskiest to modify, and why? Concretely, what downstream interfaces break if I change module 10 (land) or module 11 (costs)?

---

## 1. The Four Highest-Centrality Modules

According to `core_docs/Module_Dependencies.md` (§1.2) and `cross_module/modification_safety_guide.md` (§Appendix A), the top-4 by total inter-module connections are:

| Rank | Module | Total Connections | Provides To | Depends On | Role |
|------|--------|-------------------|-------------|------------|------|
| 1 | **11_costs** | 28 | 1 | 27 | Objective function aggregator |
| 2 | **10_land** | 17 | 15 | 2 | Land allocation hub |
| 3 | **56_ghg_policy** | 16 | 13 | 3 | Environmental-economic bridge |
| 4 | **32_forestry** | 16 | 5 | 11 | Forestry/plantation hub |

Module 17 (production) is close behind at rank 7 with 14 total connections and is also treated as high-risk. The focus below is on M10 and M11 as requested.

The reason the top-4 are most dangerous is structural:
- **M10** is a *provider* hub: 15 modules downstream depend on its outputs.
- **M11** is a *consumer* hub: it aggregates inputs from 27 modules into the single variable the solver minimizes. If M11 is broken, the model has no objective function.
- **M56** is a *bridge*: it converts physical quantities (emissions) into the economic domain (costs in `vm_emission_costs`) and so propagates perturbations from the physical accounting layer into the optimization.

---

## 2. Module 10 (Land) — Concrete Downstream Breakage

### 2.1 Architectural role

M10 (`landmatrix_dec18`) is the **central land allocation hub** (`module_10.md`, §1). Its sole two inputs are exogenous land-area totals; everything else is output. It enforces `q10_land_area`, the **strict land area conservation constraint**:

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```

Breaking this equation makes the model physically infeasible — the solver will immediately abort with "no feasible solution" / "Equation infeasible."

### 2.2 Interface variables and their consumers

M10 exports five interface variables. Consumer counts were recomputed in R3 (2026-05-23) by file-level grep across the GAMS source tree, excluding the producer module.

| Variable | Consumers (count) | Consumers (named) | Risk if broken |
|----------|------------------|--------------------|----------------|
| `vm_land(j,land)` | 10 modules | 22, 29, 30, 31, 32, 34, 35, 50, 58, 59 | EXTREME — all land-use sectors immediately fail |
| `pcm_land(j,land)` | 12 modules | (broader set including 11, 13, 14, 39, 44, 56, 71, 80, and the vm_land set) | EXTREME — previous-period land used everywhere |
| `vm_landexpansion(j,land)` | 4 modules | 39, 52, 56, and further downstream | HIGH |
| `vm_landreduction(j,land)` | 2 modules | 52, 56 | MEDIUM |
| `vm_lu_transitions(j,land_from,land_to)` | 3 modules | 32, 39, 44 | HIGH |

The **18-module union** touched by ANY M10 interface variable:

> 11_costs, 13_tc, 14_yields, 22_land_conservation, 29_cropland, 30_croparea, 31_past, 32_forestry, 34_urban, 35_natveg, 39_landconversion, 44_biodiversity, 50_nr_soil_budget, 56_ghg_policy, 58_peatland, 59_som, 71_disagg_lvst, 80_optimization

(`cross_module/modification_safety_guide.md`, §1.2)

### 2.3 What breaks and how

**Adding or renaming a land type in the `land` set** is the highest-blast-radius change. The `land` set is defined globally in `core/sets.gms`. Every module that sums or indexes over `land` breaks — this is all 10 direct `vm_land` consumers plus any module whose equations reference specific land-type names (e.g., `"crop"`, `"primforest"`). The land conservation constraint also has to be updated, as do carbon pools in M52 (each land type has a `vm_carbon_stock` pool) and cost accounting in M11 (which aggregates `vm_cost_landcon(j,land)` and `vm_cost_land_transition(j)`).

**Modifying transition matrix accounting** (`q10_transition_to`, `q10_transition_from`) breaks the gross-change bookkeeping used by M39 (land conversion costs), M44 (biodiversity accounting on land-use change), and M52 (carbon emissions from land-use change). Note: `landmatrix_dec18` tracks **gross** between-type transitions, not net stock differences; these are not the same thing (`module_10_notes.md`, warning §1).

**Changing bounds or fixing `vm_land`** directly propagates to every module that uses land area as a multiplier — M14 (yields: yield × area = production), M29/M30/M31 (cropland/pasture area constraints), M52 (carbon stock = carbon density × area), M58/M59 (peatland and soil carbon), M50 (nitrogen budget).

### 2.4 Conservation cascade

M10 sits at the top of the land balance (`cross_module/land_balance_conservation.md`). Violating it cascades through:

1. **Land balance** (strict equality) → infeasibility
2. **Carbon balance** (M52 reads `vm_land`) → CO2 emissions wrong
3. **Water balance** (M43 irrigation water demand is area-dependent) → water accounting wrong
4. **Food balance** (M17 production aggregates cell area × yield) → trade and demand wrong

---

## 3. Module 11 (Costs) — Concrete Downstream Breakage

### 3.1 Architectural role

M11 (`default` realization) is a **pure aggregator** with no input data and no independent logic (`module_11.md`, §1.2). It implements exactly two equations:

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));

q11_cost_reg(i2) .. v11_cost_reg(i2) =e=
    sum(factors,vm_cost_prod_crop(i2,factors))
    + vm_cost_prod_past(i2)
    + sum(factors,vm_cost_prod_livst(i2,factors))
    + vm_nr_inorg_fert_costs(i2)
    + vm_emission_costs(i2)
    - vm_reward_cdr_aff(i2)
    + vm_cost_landcon(j2,land)   [summed over cells]
    + vm_cost_land_transition(j2) [summed over cells]
    ... [32 total terms across 27+ modules]
```

`vm_cost_glo` is the objective function variable — the one the solver minimizes. It has exactly **1 downstream consumer**: the solver itself.

### 3.2 What breaks and how

**Omitting a cost component** for a new activity is the most insidious failure mode. If a new module adds a production variable but M11's `q11_cost_reg` does not include its cost variable, that activity has an implicit cost of zero in the objective function. The solver will exploit it to the maximum extent possible ("free lunch" / infinite exploitation), producing unrealistic results rather than an error.

**Negative cost terms** cause the same problem in reverse. `vm_reward_cdr_aff(i2)` is the only intentional negative term in `q11_cost_reg` (a CDR revenue for afforestation, from M56). Any other accidental negative cost — e.g., a timber revenue entered as a cost reduction — causes the model to pursue that activity without bound. M56 handles this correctly via an explicit reward variable pattern.

**Wrong cost units** produce an objective function that is numerically miscalibrated. All terms in M11 must be in `mio. USD17MER/yr`. A cost entered in raw USD/ha (rather than mio. USD/ha = one unit) is off by a factor of 10^6, completely dominating the objective.

**Downstream**: since M11 is a pure consumer, it has only 1 downstream path — but that path is the entire optimization. Every decision the solver makes about land use (M10), cropland (M29/M30), pasture (M31), forestry (M32), trade (M21), technology (M13), and emissions policy (M56) flows through `vm_cost_glo`. A corrupt objective corrupts all of those simultaneously, in ways that may not be immediately visible (the model solves and produces numbers, just wrong ones).

### 3.3 The "silent failure" problem

M10 violations typically cause **hard failures** (infeasibility) that are easy to detect. M11 violations typically cause **silent failures**: the model solves, produces output numbers, but those numbers are economically meaningless. This makes M11 modifications more treacherous in practice.

---

## 4. Why Centrality Translates Directly to Risk

The centrality rankings reflect two distinct risk profiles:

**High-fan-out (M10, M17)**: Many modules read their outputs. Any interface change (variable renamed, dimension added, unit changed) requires coordinating updates across all consumers simultaneously. Missing one consumer compiles fine but produces wrong results or infeasibility at runtime.

**High-fan-in (M11)**: Many modules write to it. Adding a new cost-generating module requires updating M11's aggregation equation. Missing this update is a silent failure. The risk here is not "many places to update" but "easy to forget one addition and never see a failure signal."

The asymmetry between hard and silent failures is the key practical distinction between M10 and M11 risks.

---

## 5. Safe vs. Unsafe Modification Patterns

From `cross_module/modification_safety_guide.md` (§1.6, §7.4):

| Action | Risk | Reason |
|--------|------|--------|
| Add a constraint on existing `vm_lu_transitions` | Low | Narrows optimization space; does not change interface dimensions |
| Add a new `vm_cost_*` term to `q11_cost_reg` | Low-medium | Requires adding cost variable AND verifying units AND checking the activity is plausible |
| Change dimensions of `vm_land` (add land type) | Extreme | Requires updating `core/sets.gms`, all 10+ direct consumers, M52 carbon pools, M11 cost accounting |
| Fix `vm_land.fx()` directly | High | Bypasses conservation constraint; can make model infeasible or over-constrained |
| Remove a cost from `q11_cost_reg` | High | Creates silent free-lunch exploitation |
| Modify `q10_land_area` (conservation equation) | Never | Model becomes physically infeasible |

---

## Sources

- `cross_module/modification_safety_guide.md` (§1, §2, §Appendix A) — primary reference for centrality rankings and breakage catalogs
- `core_docs/Module_Dependencies.md` (§1.2, §2.1) — authoritative dependency counts (recomputed R3 2026-05-23)
- `modules/module_10.md` (§1-3) — M10 equations, variables, land set definitions
- `modules/module_10_notes.md` — net vs. gross transition distinction warning
- `modules/module_11.md` (§1-2) — M11 equations, full `q11_cost_reg` term list
- `cross_module/land_balance_conservation.md` — cascade from `q10_land_area` violation

---

## Epistemic Status

🟡 Documented — all claims sourced from AI documentation read this session. Consumer counts for M10 interface variables were recomputed in R3 (2026-05-23) via GAMS source grep and are cited as authoritative. The `q11_cost_reg` equation text is reproduced from `module_11.md` (§2.2), which was verified against `equations.gms` at the time of documentation. Line numbers may have drifted since the last `/sync`; for code-modification work, verify against current `equations.gms` before acting.

For M10 specifically: the default realization is `landmatrix_dec18` (single realization — no Step 1c ambiguity). For M11: the default and only realization is `default`.
