# R59 — QUESTIONS (12 probes: 5 Arm A + 5 Arm B + 2 regression)

Designed per PLAN.md §3/§4/§5. **Arm A and Arm B scores are NEVER pooled** (§0.2).

---

## ARM A — fix-verification (5 probes)

> These re-probe modules whose docs were rewritten by R58 fix agents at 07:07–07:20 on
> 2026-07-17 (`77a666f`, `4d9bbb9`, `228b26c`+`2b74f9e`, `3791bd1`; ~720 insertions,
> never validated). **Arm A scores measure "did the fix hold", NOT capability** (§3).
> Probe regions verified this session against `git diff 71029ad..HEAD` hunk headers.

### A1 — Cropland carbon + age-class density chain
**Modules**: 29, 52, 32, 59 · **Region probed**: `module_29.md:779-841`

> In Module 29 (cropland), how is the carbon density of tree cover on cropland determined?
> Name the parameters involved and their source, state which age-class dimension is used, and
> give the equation that turns density into a carbon stock. Then: which module DECLARES
> `vm_carbon_stock`, and which modules POPULATE it for the cropland slice? Explain how the
> resulting stock reaches Module 52's CO₂ accounting. Cite file:line for each step.

### A2 — Cropland total / available / fallow limit
**Modules**: 29, 30, 10 · **Regions**: `module_29.md:137-178`, `:370-382`

> By default, what constrains total cropland in Module 29? Give the equations for (a) total
> cropland composition, (b) the available-cropland limit, and (c) the fallow-land maximum.
> Name the scalar controlling the fallow target and its scenario fader parameter, state that
> scalar's default value, and explain how cropland enters Module 10's land balance. State
> which realization you are describing and whether it is the default.

### A3 — Feed balanceflow + scavenging + feed-scen default
**Modules**: 70, 71, 16, 17 · **Regions**: `module_70.md:122`, `:416-453`, `:904`

> In Module 70 (livestock), explain (a) how `vm_feed_balanceflow` is set for ruminants on
> pasture, (b) the endogenous scavenging-flag mechanism and specifically what prevents a
> division by zero in it, and (c) the default value of `c70_feed_scen` and what it selects.
> Name the equations and parameters, state which realization you are describing, and explain
> how livestock feed demand connects to Modules 16 and 17.

### A4 — Livestock cost formation → M11 handoff
**Modules**: 70, 38, 11 · **Regions**: `module_70.md:269`, `:590`, `:825`

> Trace how livestock production costs are formed in Module 70 and handed to Module 11's
> objective. Cover the capital-need parameter and the factor-requirement input it uses, the
> cost-regression parameters and where their coefficients come from, and name every `vm_cost_*`
> variable Module 70 populates. State which module DECLARES `vm_cost_prod_fish`, and how these
> costs enter the Module 11 aggregation. Cite file:line.

### A5 — M11 cost aggregation set + M59 SOM → carbon stock
**Modules**: 11, 59, 52, 56 · **Regions**: `module_11.md:185-253`, `module_59.md:194`, `:1049`

> How many cost terms does Module 11's objective aggregate, and via what set and equation?
> Then: how does Module 59 (SOM) populate soil carbon into `vm_carbon_stock`, what does
> `pcm_carbon_stock` do at the start of a timestep and how does it differ from `vm_carbon_stock`,
> and by what chain does that reach Module 56's GHG pricing? Name the realization for each
> module and cite equations with file:line.

---

## ARM B — central + never-depth-audited (5 probes)

> Fresh probes on high-centrality modules that have **never** had a claim-level depth audit
> (M35 = #3 hub, M50 = #7; M52 = #9, last at R55). Centrality held roughly level with R58's
> hubs so the arms are comparable in that respect (§4).

### B1 — Natveg land dynamics → land balance
**Modules**: 35, 10, 52, 22

> Describe how Module 35 (natveg) determines its land pools and their dynamics. Name the
> default realization, list the land types it manages, give the equations governing the pools
> and any transitions between them, explain how `vm_land` is populated for the natveg slices,
> how the conservation constraint from Module 22 restricts them, and how this enters Module 10's
> land balance. Cite file:line.

### B2 — Natveg carbon + age classes
**Modules**: 35, 52, 28, 32

> How does Module 35 compute carbon stocks for its land pools? Name the carbon-density
> parameters and their dimensions, state how age classes (Module 28) enter secondary-forest
> carbon accounting, identify exactly which `ac` set members are used and how many there are,
> and explain how Module 35's contribution reaches Module 52. Briefly contrast with how
> Module 32 handles age-class carbon. Cite file:line.

### B3 — Soil N balance chain
**Modules**: 50, 51, 18, 55

> Walk through Module 50's soil nitrogen budget. Name the default realization, give the balance
> equation and every inflow and outflow term it contains, state where crop-residue nitrogen
> (Module 18) and animal-waste nitrogen (Module 55) enter, and explain how the resulting surplus
> is passed to Module 51 for emission calculation. Cite equations and file:line.

### B4 — Inorganic fertilizer → cost handoff
**Modules**: 50, 11, 38, 17

> How is inorganic (mineral) fertilizer demand determined in Module 50? What determines its
> cost, which `vm_cost_*` variable carries it, and which module DECLARES that variable? Explain
> how it reaches Module 11's objective, and state whether the fertilizer price is exogenous or
> endogenous under the default configuration. Cite file:line.

### B5 — Carbon stock read + CO₂ pricing chain
**Modules**: 52, 56, 59, 29 · *(bridges to R55's depth arm)*

> Module 52's default realization computes CO₂ emissions from carbon-stock changes. Name the
> realization and every equation it defines. Explain the role of the `stockType` dimension and
> what its members mean, how `pcm_carbon_stock` relates to `vm_carbon_stock` across timesteps,
> and identify which modules populate the cropland and SOM slices of that variable. Then state,
> in one step, how Module 52's emission variable is consumed by Module 56. Cite file:line.

---

## REGRESSION ANCHORS (2)

Both last used **R49** — the coldest pair (verified this session against
`validation_rounds.json.regression_questions[].used_in_rounds`: G1→[…,49], G3→[…,49],
G2→[…,52], G4→[…,50]). Text is **verbatim** from the JSON; do not paraphrase.

### G1 — Module 14 default realization (stability anchor)

> What is the default realization of module 14 (yields)? List the equations defined in its
> equations.gms.

### G3 — magpie4 source-of-truth discipline (version-pin anchor)

> Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that
> version determined? Cite the file(s) you read.

⚠️ **G3 auditor MUST read `project/version_pins.json` at audit time** to compute the expected
version/SHA. Scoring against a hardcoded version is a rubric violation — the pin advances with
upstream renv.lock (§5, rubric §6/G3).
