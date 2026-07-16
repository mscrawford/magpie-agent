# Q&A Answers — Round 58 Hub Regression Test (documentation-only)

**Constraint under which these were written:** AI documentation only (`modules/*.md`, `core_docs/*.md`, `cross_module/*.md`, `agent/helpers/*.md`). No GAMS source was read this session, so nothing is marked 🟢 (verified in code) — all claims are 🟡 (from docs, as verified/asserted by the docs themselves) or 🔴 (inferred). Per-doc "VERIFIED" labels reflect the *documentation's own* claim to have been checked against code on a past date, not something re-verified this session.

---

## Q1

**How does MAgPIE model soil organic carbon in Module 59? Default realization, main equations, mechanism, and is it mechanistically simulated or parameterized?**

🟡 **Default realization**: `cellpool_jan23`, confirmed in `modules/module_59.md:38-39` against `config/default.cfg: cfg$gms$som <- "cellpool_jan23"`. The only alternative is `static_jan19` (static SOC, no temporal dynamics, IPCC 2006 factors) — the docs state these are the only two realizations (`module.gms` per the doc).

🟡 **Mechanism (per the docs)**: Module 59 tracks a topsoil organic carbon pool per cell and land type (`v59_som_pool(j,land)`) that converges toward an equilibrium target (`v59_som_target(j,land)`) at a fixed annual rate. The core equations, as documented in `modules/module_59.md` §3:

1. **Cropland equilibrium target** (`q59_som_target_cropland`, `equations.gms:20-27` per doc): equilibrium carbon = Σ(crop area × crop-specific carbon ratio) + SCM uplift term + fallow term + treecover term, all × natural topsoil carbon density (`f59_topsoilc_density`, sourced from LPJmL).
2. **Non-cropland equilibrium target** (`q59_som_target_noncropland`, `equations.gms:31-34`): non-cropland land (pasture, forestry, primforest, secdforest, other, urban) equilibrium = `vm_land × natural topsoil density` — i.e., assumed to sit at natural carbon density, unconditionally.
3. **Actual pool dynamic** (`q59_som_pool`, `equations.gms:46-52`): `v59_som_pool = lossrate × target + (1 - lossrate) × Σ(land-use-transition-weighted legacy carbon density)`. The lossrate formula (`preloop.gms:45`) is `i59_lossrate(t) = 1 - 0.85^m_yeardiff(t)` — i.e., a **fixed 15% annual convergence rate** toward the newly computed equilibrium, applied per timestep (56% convergence over a 5-year timestep, 80% over 10 years, 96% over 20 years, per the doc's worked numbers).
4. **Total soil carbon stock** (`q59_carbon_soil`, `equations.gms:61-64`): `vm_carbon_stock(...,"soilc",...) = v59_som_pool (dynamic topsoil) + vm_land × i59_subsoilc_density (static subsoil reference)`. Subsoil density is NOT dynamically modeled — it's a fixed value derived once as `total soil C (from Module 52's fm_carbon_density) - topsoil C`.
5. Two further equations convert SOM loss to a nitrogen release estimate (`q59_nr_som`, fixed C:N ratio of 15:1) and a soil-carbon-management cost (`q59_cost_scm`).

**Is it mechanistically simulated or parameterized?** 🟡 Per the docs, this is **explicitly parameterized, not mechanistically simulated**. The documentation is unusually direct about this:
- The equilibrium target is computed from **IPCC 2019 Tier-1 stock change factors** (land-use × tillage × input × irrigation multipliers looked up from IPCC tables, `f59_cratio_*` parameters) applied to a **fixed natural-vegetation carbon density baseline from LPJmL** — not from any simulated microbial decomposition, root-carbon-input, or soil-process model.
- The convergence toward that target uses a **single fixed exponential rate (15%/yr, i.e., a fixed half-life)** applied uniformly to all soils, all climates, all land types — this is a first-order relaxation-to-equilibrium approximation, not a dynamic carbon-flux/decomposition model.
- The doc's own "What Module 59 does NOT do" list (`module_59.md:53-59`) states explicitly: it does NOT model microbial decomposition processes, does NOT track subsoil dynamics (static reference), does NOT model tillage effects separately (fixed default = full tillage), does NOT model manure effects separately (fixed default = medium input), and assumes pastures/forests undergo **no** SOM change from natural state at all.
- This matches the CLAUDE.md three-check protocol distinction (mechanistic-modeling vs. parameterization-from-data): Module 59 applies a historical/IPCC-derived stock-change coefficient to compute a target and a fixed relaxation rate toward it — a parameterization, not a mechanistic simulation of carbon cycling.

**Key limitation flagged in the docs** (`module_59.md` §13, `realization.gms:21-24` per doc): pastures and managed forests are assumed to hold the *same* soil carbon as natural vegetation — grazing intensity, degradation, and forest management have **zero** effect on soil carbon in this module. Only land-use-type transitions move the pool.

**Sources**: `modules/module_59.md` (§1 Core Purpose, §3 Key Equations, §13 Key Limitations), `modules/module_59_notes.md`, `cross_module/carbon_balance_conservation.md` §5 (Soil Organic Matter Dynamics).

---

## Q2

**Which interface variables does Module 59 provide to other modules, which modules consume them, and which modules does M59 depend on?**

🟡 **Provided to other modules** (per `modules/module_59.md` §9.1 and the "Interface Variables" table):

| Variable | Consumer module | Purpose (per docs) |
|---|---|---|
| `vm_nr_som(j)` — N release from SOM loss (Mt N/yr) | Module 51 (Nitrogen) | N2O emission calculation, `modules/51_nitrogen/rescaled_jan21/equations.gms` |
| `vm_nr_som_fertilizer(j)` — plant-available N from SOM (Mt N/yr) | Module 50 (Soil Nitrogen Budget) | Nitrogen availability for plant uptake, `modules/50_nr_soil_budget/macceff_aug22/equations.gms:30` |
| `vm_cost_scm(j)` — soil carbon management cost (mio. USD17MER/yr) | Module 11 (Costs) | Added to total regional cost / objective function |
| `vm_carbon_stock(j,land,"soilc",stockType)` — total soil carbon (topsoil+subsoil) | Module 52 (carbon accounting/reads), and Module 56 (declares the variable and prices CO2 off it) | Carbon accounting, CO2 emission/pricing calculations |

Note on `vm_carbon_stock`: per `modules/module_56_notes.md`, this 4-D variable is **declared in Module 56** (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), not Module 59 — Module 59 is one of several **populators** (it writes the `soilc` slice for *all* land types via `q59_carbon_soil`), alongside Module 29 (crop, folding in Module 30's `vm_carbon_stock_croparea`), Module 31 (pasture), Module 32 (forestry), Module 34 (urban, fixed to 0), and Module 35 (primforest/secdforest/other). Module 52 only *reads* it to compute carbon densities/emissions; it does not populate it.

🟡 **Received from (M59's dependencies)** (per `modules/module_59.md` §9.2):
- **Module 10 (Land)**: `vm_land(j,land)` (land area by type, used in non-cropland target + total soil carbon), `vm_lu_transitions(j,land_from,land_to)` (land-use transition matrix, used in the pool-dynamics and N-release equations), `vm_landexpansion(j,land)` (used to bound plant-available N to newly-expanded cropland).
- **Module 30 (Croparea)**: `vm_area(j,kcr,w)` (cropland area by crop and irrigation type, used in the cropland equilibrium target and SCM cost equation).
- **Module 29 (Cropland Management)**: `vm_fallow(j)` and `vm_treecover(j)` (fallow and treecover areas, distinct carbon ratios in the cropland target equation).

🟡 Additionally, the cross-module carbon-balance doc (`cross_module/carbon_balance_conservation.md` §2.3, §5.3, §7.2) notes that Module 59's **subsoil carbon density parameter** (`i59_subsoilc_density`) is *derived from* Module 52's `fm_carbon_density` (total soil carbon from LPJmL minus M59's own topsoil density) during preloop — so M59 has an indirect data dependency on Module 52 even though `module_59.md`'s own interfaces section doesn't list M52 as a direct "receives from" entry. `module_59.md`'s Dependency-Chains summary (bottom of file) states: "**Depends on**: Modules 10 (land), 30 (croparea), 29 (cropland). (Module 35 natveg is a conceptual upstream driver of land transitions via Module 10, not a direct interface dependency.)" — this summary line does not mention Module 52, so there is a minor inconsistency between the detailed equation-level provenance (which implies an M52 read for subsoil density) and the module's own summarized dependency list. I flag this rather than resolve it, since I cannot check the code this session.

🟡 Module_Dependencies.md corroborates the module list qualitatively: it lists M59's "Key Dependencies" as `10_land, 29_cropland, 56_ghg_policy` (§ Degradation System table) — note this table mixes upstream and downstream ("56_ghg_policy" here likely reflects that M59 feeds the carbon-stock chain that terminates in M56's pricing, i.e., a *consumer* relationship, not a dependency M59 receives *from*). The docs give two different connection counts for M59 ("8 connections" in `module_59.md`'s Quick Reference and Dependency-Chains section; "5 dependencies" in `Module_Dependencies.md` §7.3 risk table) — I can't reconcile these different countings from the docs alone; I'd guess (🔴, unconfirmed) they're counting different things (total interface edges vs. inbound-only), but the docs don't define the counting methodology explicitly enough to be sure.

**Sources**: `modules/module_59.md` §9 (Module Interfaces) and Dependency-Chains section, `modules/module_56.md` §4 and §12, `modules/module_56_notes.md`, `cross_module/carbon_balance_conservation.md` §5.2, §7.2, §7.5, `core_docs/Module_Dependencies.md` (Degradation System table, §7.3 risk table).

---

## Q3

**Default realization of Module 14 (Yields), how it calculates crop yields, key equation, and the role of the tau factor.**

🟡 **Default realization**: `managementcalib_aug19` (per `modules/module_14.md:1,3` and `module_14_notes.md:13`, which states this is the *only* realization — an earlier `biocorrect` realization was removed in 2021, and there is no `input` realization despite `modules/14_yields/input/` existing as a data directory rather than a code realization).

🟡 **Mechanism**: Module 14 transforms LPJmL-simulated gridded crop/pasture yields into model-ready yields through (a) an extensive preloop calibration pipeline (bioenergy-yield correction, pasture-management correction, FAO-target "limited calibration," irrigated/rainfed ratio calibration to AQUASTAT, optional post-run calibration factors, and optional degradation effects) producing a calibrated baseline `i14_yields_calib(t,j,kve,w)`, then (b) a single equation that scales that baseline by the ratio of the current technological-change factor to its 1995 baseline value.

🟡 **Key equation** (`q14_yield_crop`, `equations.gms:14-16` per doc):
```
vm_yld(j2,kcr,w) =e= sum(ct, i14_yields_calib(ct,j2,kcr,w)) * vm_tau(j2,"crop")
                       / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```
i.e., `Yield = CalibratedBaselineYield × (τ_current / τ_1995)`.

There is a second, parallel equation for pasture (`q14_yield_past`, `equations.gms:35-39`): `vm_yld(j,"pasture",w) = CalibratedPastureYield × ManagementFactor × [1 + spillover × (τ_crop,previous-timestep/τ_1995 − 1)]`, where only a fraction (default 25%, `s14_yld_past_switch`) of crop-sector technological change spills over to pasture, using the *previous* timestep's crop τ rather than the current one.

🟡 **Role of the tau factor**: τ (tau) is Module 14's technological-change multiplier, supplied by Module 13 (Technological Change) as the optimization variable `vm_tau(j,"crop")`, normalized against its regional 1995 baseline value `fm_tau1995(h)`. It is the sole endogenous driver of yield growth over time in this equation — the calibrated LPJmL/FAO baseline `i14_yields_calib` is fixed per timestep from input data and preloop calibration, so **without τ increasing above 1, yields would stay frozen at the calibrated baseline forever** (per `module_14_notes.md:9`: "If `tc` realization is `off`, yields are static — all scenario results reflect only land-use change, not productivity improvements"). Conceptually: if τ doubles from 1995 to 2050, yields double; if τ=1.5, yields rise 50% relative to the calibrated 1995 baseline. τ is defined at cluster level (as of the "f_btc2" change noted in the docs, commit `480e300b1`), allowing spatial heterogeneity in intensification rates.

**Sources**: `modules/module_14.md` §1 (Overview), §2.1–2.2 (Core Equations), §5.2 (config switch), `modules/module_14_notes.md`.

---

## Q4

**Which modules POPULATE `vm_carbon_stock`, and how does carbon stock information reach Module 56 (GHG policy)? Enumerate the populating modules explicitly.**

🟡 **Populating modules**, per `modules/module_56.md` §4.1/§12.4 and `cross_module/carbon_balance_conservation.md` §7.5 (both docs agree on this list and give the same slice-by-slice breakdown):

| Module | Land-type slice populated | Notes |
|---|---|---|
| **Module 29 (Cropland)** | `crop` | Via `q29_carbon`, which folds in `vm_carbon_stock_croparea` — a *separate* interface variable computed by **Module 30 (Croparea)** and passed to M29, which is the direct populator of the crop slice of `vm_carbon_stock` itself. |
| **Module 31 (Pasture)** | `past`/pasture | — |
| **Module 32 (Forestry)** | `forestry` (plantations) | — |
| **Module 34 (Urban)** | `urban` | Fixed to 0 (`vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0`, per doc citing `modules/34_urban/exo_nov21/presolve.gms:8`). |
| **Module 35 (Natural Vegetation)** | `primforest`, `secdforest`, `other` | — |
| **Module 59 (SOM)** | `soilc` pool, **for all land types** (crop, pasture, forestry, primforest, secdforest, other, urban) | Via `q59_carbon_soil` — topsoil (dynamic) + subsoil (static reference derived from M52). This is explicitly flagged in `module_56_notes.md` as "often missed in the producer list." |

So the six populating modules, explicitly: **29, 30 (indirectly, via 29), 31, 32, 34, 35, and 59.** If counting only modules that write directly into the `vm_carbon_stock` array (rather than into an intermediate variable another module folds in), the direct populators are **29, 31, 32, 34, 35, 59** — Module 30 populates the intermediate `vm_carbon_stock_croparea`, which Module 29 then folds in.

**What does NOT populate it**: Module 52 (Carbon) only *reads* `vm_carbon_stock` — it does not write to it; it computes carbon densities (`fm_carbon_density`, age-class curves) and derives `vm_emissions_reg(...,"co2_c")` from stock differences, but the stock array itself is populated by the land-use modules above. Module 58 (Peatland) does **not** populate `vm_carbon_stock` either — peatland carbon uses a separate emission pathway (`q58_peatland_emis` → `vm_emissions_reg(i,"peatland",...)`, an `emis_annual` source) that bypasses the stock-change accounting entirely (per `cross_module/carbon_balance_conservation.md` §10.2, item 7).

🟡 **How carbon stock information reaches Module 56 (GHG policy)**: Per `modules/module_56_notes.md` ("`vm_carbon_stock` is DECLARED in M56, not M52"), the variable is **declared inside Module 56 itself** (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), not "passed in" from an external module in the usual producer→consumer sense — the land-use/SOM modules populate a variable that lives in Module 56's own namespace. The docs describe the chain (`module_56_notes.md`, "Lessons Learned," 2026-05-25 entry) as:

`q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emis_pricing` → `vm_emissions_reg`

but that's specifically the chain for *annual* (recurring) pollutants (CH4, N2O) that go through `vm_emissions_reg`. For **CO2 from land-use change specifically**, Module 56's equation `q56_emis_pricing_co2` (`equations.gms:19-22` per doc) reads `vm_carbon_stock` **directly**:
```
v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
  sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%")) / m_timestep_length);
```
i.e., CO2 pricing = (previous-timestep carbon stock − current-timestep carbon stock) / timestep length, computed **inside Module 56 itself** from the stock values the land modules just populated — this deliberately **bypasses** `vm_emissions_reg` entirely (the doc is explicit that this is "a deliberate design choice," §2.2, and that Module 52's LULUCF CO2 emission calculation, which *does* feed `vm_emissions_reg(...,"co2_c")` in the `emis_oneoff` slice, is a **parallel, independent** computation from the same `vm_carbon_stock` source, not something Module 56 consumes — `cross_module/carbon_balance_conservation.md` §7.3: "M52 and M56 are **parallel readers** of `vm_carbon_stock`, not a serial producer→consumer chain").

The **previous-timestep** reference `pcm_carbon_stock` used in that equation is carried forward across timesteps in a **split** fashion (per `module_59.md` §3.4 and `module_56_notes.md`): Module 56's own postsolve carries forward the above-ground pools (`ag_pools` = vegc, litc; `modules/56_ghg_policy/price_aug22/postsolve.gms:8`), while **Module 59's** postsolve carries forward the `soilc` slice (`modules/59_som/cellpool_jan23/postsolve.gms:13`) — the docs flag this soil carry-forward as the subject of a bug fix in develop commit `931db85c4` (2026-06-25): previously the soil slice of `pcm_carbon_stock` was never updated after preloop initialization, causing the soil CO2 term to be computed as a cumulative-since-init change rather than a per-timestep flux (documented as ~17x error in a default H12 run for soil-inclusive policies; default runs unaffected because the default `c56_emis_policy = reddnatveg_nosoil` excludes soil carbon from pricing).

**Sources**: `modules/module_56.md` §2.2 (q56_emis_pricing_co2), §4.1, §12.4; `modules/module_56_notes.md`; `modules/module_59.md` §3.4, §9.1; `cross_module/carbon_balance_conservation.md` §2.3, §7.1–7.3, §7.5.
