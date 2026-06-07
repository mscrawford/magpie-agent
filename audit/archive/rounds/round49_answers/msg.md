# vm_land Consumer Set: modification_safety_guide.md vs Documentation

## What the safety guide states

`cross_module/modification_safety_guide.md:54-55` gives this verbatim consumer list for `vm_land(j,land)`:

> **Direct vm_land consumers** (the 10 modules that will break if `vm_land` is modified incompatibly):
> - 22_land_conservation, 29_cropland, 30_croparea, 31_past, 32_forestry, 34_urban, 35_natveg, 50_nr_soil_budget, 58_peatland, 59_som

The table at `modification_safety_guide.md:46` lists the count as "10 modules" with risk level EXTREME.

`Appendix B` at `modification_safety_guide.md:1078` repeats: `vm_land(j,land)` has 10 consumers.

The counts were marked as **recomputed 2026-05-23 (R3)** via `find ../modules -name '*.gms' -exec grep -l '<var>' {} \; | awk -F/ '{print $3}' | sort -u | grep -v '10_land'` (`modification_safety_guide.md:52`).

---

## Cross-reference: module_10.md

`module_10.md:315-318` repeats the same list and then adds an important clarifying sentence:

> **Direct consumers of `vm_land`** (10 modules — authoritative list in `cross_module/modification_safety_guide.md:54-55`):
> - 22_land_conservation, 29_cropland, 30_croparea, 31_past, 32_forestry, 34_urban, 35_natveg, 50_nr_soil_budget, 58_peatland, 59_som
>
> `11_costs` consumes `vm_cost_land_transition`, and `39_landconversion` consumes `vm_landexpansion`/`vm_landreduction` — NOT `vm_land` itself. `13_tc`, `44_biodiversity`, and `56_ghg_policy` directly read `pcm_land` (M10 previous-timestep parameter, declared in `declarations.gms:11`, populated in `postsolve.gms:9`; 12 direct consumers — see `cross_module/modification_safety_guide.md`). `14_yields` and `71_disagg_lvst` directly read `pm_land_start`. `80_optimization` reads `vm_landdiff`. None of these six read `vm_land` directly. **Verified: 11/14/39/71/80 contain zero `vm_land(` references in any `.gms` file (origin/develop ee98739fd).**

---

## Per-module code references

The documentation cites, per module, why each consumer reads `vm_land`:

| Module | How it uses `vm_land` | Doc source |
|--------|----------------------|------------|
| **22_land_conservation** | Reads `vm_land(j,land)` to enforce protected-area lower bounds | `module_10.md:302`, `land_balance_conservation.md:225` |
| **29_cropland** | `q29_cropland` sets `vm_land(j,"crop") =e= sum(kcr,w, vm_area) + vm_fallow + v29_treecover` — LHS is `vm_land` | `land_balance_conservation.md:239-248` (eq `modules/29_cropland/detail_apr24/equations.gms:11-12`) |
| **30_croparea** | Reads `vm_land(j,"crop")` as an available area bound | `module_10.md:302` |
| **31_past** | `q31_prod`: `vm_prod(j,"pasture") =l= vm_land(j,"past") * vm_yld(...)` | `land_balance_conservation.md:284-288` (eq `modules/31_past/endo_jun13/equations.gms:16-18`) |
| **32_forestry** | `q32_land` sets `vm_land(j,"forestry") =e= sum(type32,ac, v32_land(...))` — LHS is `vm_land`; also reads `vm_land(j,"primforest")` for establishment caps | `land_balance_conservation.md:312-315` (eq `modules/32_forestry/dynamic_may24/equations.gms:55-56`) |
| **34_urban** | `q34_urban_land`: `sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum(ct,cell(...), i34_urban_area(...))` | `land_balance_conservation.md:336-340` (eq `modules/34_urban/exo_nov21/equations.gms:30-31`) |
| **35_natveg** | `q35_land_secdforest` and `q35_land_other` each write `vm_land(j,...)` LHS; also reads `vm_land(j,"primforest")` for conservation constraints | `land_balance_conservation.md:362-375` (eqs `modules/35_natveg/pot_forest_may24/equations.gms:11,13`) |
| **50_nr_soil_budget** | Reads `vm_land(j,land)` for nitrogen budget area calculations | `module_10.md:302` |
| **58_peatland** | Reads `vm_land(j,land)` to track peatland area changes | `module_10.md:302` |
| **59_som** | Reads `vm_land(j,land)` for soil organic matter tracking | `module_10.md:299-302` |

---

## Modules explicitly excluded from the direct vm_land consumer set

The docs explicitly rule out several plausible-looking candidates:

| Module | Variable it actually consumes | Source |
|--------|------------------------------|--------|
| **11_costs** | `vm_cost_land_transition(j)` — NOT vm_land | `module_10.md:304-305,317` |
| **39_landconversion** | `vm_landexpansion`, `vm_landreduction` — NOT vm_land | `module_10.md:304-305,317` |
| **13_tc** | `pcm_land` (previous-timestep parameter) — NOT vm_land | `module_10.md:317-318` |
| **44_biodiversity** | `pcm_land` — NOT vm_land | `module_10.md:317-318` |
| **56_ghg_policy** | `pcm_land` — NOT vm_land | `module_10.md:317-318` |
| **14_yields** | `pm_land_start` — NOT vm_land | `module_10.md:317-318` |
| **71_disagg_lvst** | `pm_land_start` — NOT vm_land | `module_10.md:317-318` |
| **80_optimization** | `vm_landdiff` — NOT vm_land | `module_10.md:317-318` |

The "18-module broader union" mentioned in `modification_safety_guide.md:57-58` covers ALL these modules as potentially affected if any Module 10 interface variable is changed, but they are not direct vm_land consumers.

---

## Is the consumer set accurate and complete?

### Accuracy

The 10-module list appears **accurate** as stated within the documentation. `module_10.md:317-318` contains an in-line verification note explicitly confirming that modules 11, 14, 39, 71, and 80 have zero `vm_land(` references, citing commit `ee98739fd` (origin/develop). This is the most specific code-level anchor provided in the documentation. The R3 recomputation note (`modification_safety_guide.md:52`) also corrected earlier overcounting in the safety guide — the original guide had "overstated" these counts, then corrected them.

### Completeness — known gap: the broader 18-module impact set

The docs are internally consistent but contain a complexity worth flagging. `modification_safety_guide.md:57-58` and `module_10.md` §5 both note that **18 modules in total** are touched by any Module 10 interface variable. The 10 vm_land direct consumers are a strict subset of this 18. The additional 8 modules (11, 13, 14, 39, 44, 56, 71, 80) consume other M10 variables (`pcm_land`, `pm_land_start`, `vm_landexpansion`, `vm_landreduction`, `vm_cost_land_transition`, `vm_landdiff`). The safety guide is explicit about this distinction and the 10-module vs 18-module boundary, so this is not an omission — it is an intentional scope choice.

### Phantom consumers

The documentation identifies **none**: the explicitly excluded modules (13, 14, 39, 44, 56, 71, 80, 11) are ruled out with stated reasons. No phantom consumers are identified in the docs, and the per-commit verification (`module_10.md:317-318`, `ee98739fd`) provides the strongest assurance the documentation offers.

### Caveats to this assessment

This assessment is **based entirely on the AI documentation** — I have not read raw GAMS files, per the constraint of this question. The code-level claim ("verified: 11/14/39/71/80 contain zero `vm_land(` references... ee98739fd") is quoted verbatim from `module_10.md:318`. The branch has since seen commits beyond ee98739fd; any changes touching vm_land usage in previously-excluded modules would not be reflected in these docs without a `/sync`. Check `project/sync_log.json` for current staleness status.

Also note: the question asked about **solution-level** reads (`vm_land.l`/`vm_land.lo`) in presolve/postsolve. The documentation confirms `pcm_land` is populated from `vm_land.l` in `postsolve.gms:9` (`pcm_land(j,land) = vm_land.l(j,land)`) — this is inside Module 10 itself. The docs do not enumerate any external consumer modules that read `vm_land.l` or `vm_land.lo` directly in presolve/postsolve files. Any such reads in other modules (e.g., presolve bounds-setting using the solved value) would require direct code inspection to confirm and are not addressed in the current documentation.

---

## Epistemic status

- 🟡 **Documented**: All claims above drawn from `cross_module/modification_safety_guide.md` (R3 recomputation, 2026-05-23), `modules/module_10.md` (last verified 2026-03-06, includes a commit-specific verification anchor for the exclusion claims), `cross_module/land_balance_conservation.md`, and `core_docs/Module_Dependencies.md:50`.
- 🔴 **Not independently verified in code this session** — the AI documentation is the source, not raw `.gms` files.
- For high-stakes modification work, re-verify with `find ../modules -name '*.gms' -exec grep -l 'vm_land(' {} \; | grep -v 10_land` against current HEAD.
