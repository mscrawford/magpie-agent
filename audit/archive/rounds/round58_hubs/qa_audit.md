# R58 QA Audit — Hub Regression Round

**Auditor**: Opus (code-verified against `magpie` branch `develop` @ `0d7ebeb90`)
**Answerer**: Sonnet, documentation-only (no GAMS source read)
**Date**: 2026-07-17

**Scores**: Q1 6/10 · Q2 8/10 · Q3 10/10 · Q4 9.5/10 — **mean 8.375/10**

Both regression anchors held: **G1 (M14) clean at 10/10**, **G2 (`vm_carbon_stock` populator set) exact — no regression** (cf. R22/R23/R26).

---

## Q1: M59 soil organic carbon — mechanism, and parameterized vs. mechanistic

### Verdict: MOSTLY ACCURATE
### Score: 6/10

The headline judgment the question actually turns on — **parameterized, not mechanistically simulated** — is **correct and correctly argued**. Every equation is named, located, and transcribed accurately. Two Majors, both of the same family: exogenous-but-time-varying inputs described as static, and a default-off mechanism described without its default.

### Verified claims (correct):
- **Default realization `cellpool_jan23`** — `config/default.cfg:1934`. ✓
- **"Only two realizations exist"** — non-trivially correct. `ls modules/59_som/` shows **three** directories (`cellpool_aug16`, `cellpool_jan23`, `static_jan19`), but `cellpool_aug16` contains only an `input/` subdir and is **not registered** in `modules/59_som/module.gms:19-21`, which includes only `cellpool_jan23` and `static_jan19`. The answer's claim survives the trap.
- **All six equations correctly named and located** (`modules/59_som/cellpool_jan23/equations.gms`): `q59_som_target_cropland` (20-27), `q59_som_target_noncropland` (31-35, answer said 31-34 — the statement's `;` is on 35; immaterial), `q59_som_pool` (46-52), `q59_carbon_soil` (61-64), `q59_nr_som` (69-75), `q59_cost_scm` (98-101). All citations land on the claimed content.
- **`q59_som_pool` formula** — `lossrate × target + (1-lossrate) × Σ(p59_carbon_density × vm_lu_transitions)`. Exact (`equations.gms:46-52`). ✓
- **`q59_carbon_soil` formula** — `vm_carbon_stock(j,land,"soilc",stockType) = v59_som_pool + vm_land × i59_subsoilc_density`. Exact (`equations.gms:61-64`). ✓
- **Lossrate `i59_lossrate(t) = 1 - 0.85**m_yeardiff(t)` at `preloop.gms:45`** — exact file:line, exact formula. ✓
- **Convergence arithmetic (56% / 80% / 96%)** — mathematically correct (1-0.85⁵ = 0.556; 1-0.85¹⁰ = 0.803; 1-0.85²⁰ = 0.961). **Notably, the answer beats the source code comment**: `preloop.gms:42` claims "44% in 5 years", which is wrong (44% is 0.85⁵, the *remaining* fraction, not the loss) and inconsistent with its own 80%/96%. The doc corrected the code comment; the answer inherited the correct number.
- **C:N ratio 15:1 fixed** — `equations.gms:71` (`*1/15`). ✓
- **Tillage/input defaults** — `i59_tillage_share(i,"full_tillage")=1` (`preloop.gms:53`), `i59_input_share(i,"medium_input")=1` (`preloop.gms:55`). ✓
- **Pastures/forests assumed at natural SOM** — `q59_som_target_noncropland` sets target = `vm_land × f59_topsoilc_density` unconditionally (`equations.gms:31-34`); limitation text confirmed at `realization.gms:21-24` (exact line range). ✓
- **Parameterization verdict** — upheld under the three-check protocol: (1) *equation structure* — targets are lookup-table products, no state variable for decomposition; (2) *parameter source* — `f59_cratio_landuse` from `f59_ch5_F_LU_2019reg.cs3` (IPCC 2019), `f59_cratio_tillage/inputs/irrigation` from IPCC tables (`input.gms:43-69`); (3) *dynamic feedback* — **`i59_lossrate(t)` carries only a `t` index** (`preloop.gms:45`), so the answer's "applied uniformly to all soils, all climates, all land types" is literally true. ✓

### Bugs found:
- **Major** / "Subsoil density is NOT dynamically modeled — it's a **fixed value derived once**"; "**static** subsoil reference"; and the target rests on "a **fixed** natural-vegetation carbon density baseline from LPJmL" / **Both LPJmL reference densities are time-varying under the default configuration.** `i59_subsoilc_density(t_all,j) = fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j)` (`modules/59_som/cellpool_jan23/preloop.gms:12`) is **indexed on `t_all`** and read at the *current* timestep via `sum(ct,i59_subsoilc_density(ct,j2))` (`equations.gms:64`); `f59_topsoilc_density(t_all,j)` likewise enters the target at `sum(ct,f59_topsoilc_density(ct,j2))` (`equations.gms:27`). Defaults are `c59_som_scenario = "cc"` (`config/default.cfg:1948`) and `c52_carbon_scenario = "cc"` (`config/default.cfg:1587`), so **neither** freeze override fires. **Dispositive structural proof**: the `nocc` overrides at `modules/59_som/cellpool_jan23/input.gms:84` and `modules/52_carbon/normal_dec17/input.gms:22` collapse these to their y1995 values — they would be no-ops if the parameters were already constant. The defensible claim is *exogenous / unresponsive to land use and management* (true); *static in time* is **false by default**. This matters: because `pcm_carbon_stock(...,"soilc",...)` is carried forward each timestep (`postsolve.gms:13`), a climate-driven drift in `i59_subsoilc_density` produces a **real soil CO2 flux even at constant land area**. (Magnitude not quantified — `lpj_carbon_stocks.cs3` is not unpacked in this checkout, only `.mz`; the structural argument stands independently.)
- **Major** / SCM (soil-carbon-management) uplift term and `q59_cost_scm` presented as live parts of the mechanism, with no default-state caveat / **SCM is identically OFF by default.** `s59_scm_target = 0` and `s59_scm_target_noselect = 0` (`modules/59_som/cellpool_jan23/input.gms:11-12`; `config/default.cfg:1975-1976`), and `i59_scm_target(t,j) = fader × (s59_scm_target × weight + s59_scm_target_noselect × (1-weight))` (`presolve.gms:31-33`) ⇒ `i59_scm_target ≡ 0`. In a default run the SCM uplift term in `q59_som_target_cropland` contributes **zero** and `vm_cost_scm ≡ 0`. The answer showed default-awareness for tillage and manure but not for SCM. (The doc *does* carry `s59_scm_target = 0` at `module_59.md:33`; the answer simply did not relay it.)

### Latent doc bugs (doc wrong, answer survived):
- **Major** / `modules/module_59.md:54` / "❌ Does NOT track subsoil carbon dynamics (**uses fixed reference value**)" / Misleading — `i59_subsoilc_density` is `t_all`-indexed and time-varying under the default `cc` scenario (see Bug 1 above). **The answer did NOT survive this one — it inherited and amplified it** ("derived once", "static"). Recorded here because the doc is the root cause and will mislead any future reader who trusts it. Suggested wording: "does NOT respond to land use or management (exogenous LPJmL reference; still varies over time with climate under default `cc`)".

### Missing nuances:
- **`presolve.gms:14-27` is unmentioned.** Before each solve, M59 transfers SOM pools between `primforest`/`other` → `secdforest` to account for natural regrowth and disturbance loss. The answer quoted the `realization.gms:22-24` limitation about this but never described the mechanism, and its "only land-use-type transitions move the pool" glosses over this presolve step.
- The IPCC vintage is **mixed**, not purely 2019: `f59_cratio_landuse` uses IPCC 2019 classes (`climate59_2019`, 6 zones) while tillage/input/irrigation factors use IPCC 2006 classes (`climate59`, 4 zones — `sets.gms:19-23`), and `input.gms:21` cites "IPCC guidelines 2006" for the SCM factor.
- `i59_cratio_treecover = 1` (`preloop.gms:82`) — i.e. cropland tree cover is assumed to hold *natural* soil carbon. Stated as "treecover term" without the value.

---

## Q2: M59 interface variables, consumers, and dependencies

### Verdict: MOSTLY ACCURATE
### Score: 8/10

Consumer side is **perfect** — every consumer verified, no phantoms, no omissions. The answerer's flagged M52 concern is **vindicated by code**. One Major: Module 45 is missing from the dependency set.

### Verified claims (correct):
- **`vm_nr_som` → Module 51 only** — `modules/51_nitrogen/rescaled_jan21/equations.gms:58` (default `nitrogen <- "rescaled_jan21"`, `config/default.cfg:1568`). Grepped both `vm_nr_som(` and `vm_nr_som.`; M51 is the sole consumer. ✓
- **`vm_nr_som_fertilizer` → Module 50 only** — `modules/50_nr_soil_budget/macceff_aug22/equations.gms:30` (default `macceff_aug22`, `config/default.cfg:1497`). **Exact line cited by the answer.** ✓
- **`vm_cost_scm` → Module 11** — `modules/11_costs/default/equations.gms:37` (default `default`, `config/default.cfg:236`). ✓
- **Provided-set is complete** — M59 declares exactly three `vm_` interfaces (`declarations.gms:41,45,46`: `vm_cost_scm`, `vm_nr_som`, `vm_nr_som_fertilizer`) and declares no `pm_` parameters. Nothing omitted. ✓
- **`vm_carbon_stock` is declared in M56, not M59/M52** — `modules/56_ghg_policy/price_aug22/declarations.gms:34`. **Exact.** M59 populates the `soilc` slice; M52 only reads (`modules/52_carbon/normal_dec17/equations.gms:19`). ✓
- **Dependency attribution for M10/M29/M30 is exactly right** — `vm_land`, `vm_lu_transitions` (`modules/10_land/landmatrix_dec18/declarations.gms:23`), `vm_landexpansion` (`:20`), `pm_land_start` (`:9`) → M10; `vm_area` (`modules/30_croparea/simple_apr24/declarations.gms:18`) → M30; `vm_fallow`, `vm_treecover` (`modules/29_cropland/simple_apr24/declarations.gms:22-23`) → M29. Each variable is attached to the correct owner. ✓
- **The M52 flag is CORRECT per code** — and the answerer deserves credit for catching a real doc defect from the docs alone. `modules/59_som/cellpool_jan23/preloop.gms:12` and `:34` both read `fm_carbon_density`, which is declared in `modules/52_carbon/normal_dec17/input.gms:16`. This is a **direct** read of an M52-owned `fm_` interface parameter in M59's preloop — the answer slightly *under*-claimed by calling it "indirect". Its refusal to resolve the doc conflict without code access was correct behaviour.
- **The "8 vs 5" reading of the docs is accurate** — `module_59.md:18` and `:976` say "8 connections"; `core_docs/Module_Dependencies.md:322` says "SOM (59) - 5 dependencies". The answerer's hedged (🔴) guess "total interface edges vs inbound-only" is **close to right** (see latent bug below) and it correctly declined to assert.

### Bugs found:
- **Major** / Dependency list given as M10, M29, M30 (+M52 flagged) — **Module 45 (Climate) is omitted**, and the list is presented as the module's dependency set / M59 reads `pm_climate_class`, declared in `modules/45_climate/static/input.gms:10` (default `climate <- "static"`, `config/default.cfg:1492`), at **four sites** in `modules/59_som/cellpool_jan23/preloop.gms:16, 61, 74, 89` — it is the weighting that maps each cluster onto its IPCC climate zone, so it is load-bearing for every `i59_cratio*` parameter. The true code-level upstream set is **{10, 29, 30, 45, 52}**. Mitigating: the answer attributed the list to `module_59.md` §9.2 rather than claiming independent verification, and M45's absence is inherited from that doc.

### Latent doc bugs (doc wrong, answer survived):
- **Critical** (R20 anchor: wrong dependency set) / `modules/module_59.md:1034` / "**Depends on**: Modules 10 (land), 30 (croparea), 29 (cropland). (Module 35 natveg is a conceptual upstream driver…)" / Omits **both** M45 (`pm_climate_class`, `59/cellpool_jan23/preloop.gms:16,61,74,89`) and M52 (`fm_carbon_density`, `preloop.gms:12,34`), each a direct read of another module's declared interface. The answerer beat the M52 half and inherited the M45 half. Note the doc's *body* contains the M52 formula verbatim at `module_59.md:169` and `:420` — the defect is confined to the summary line, which is exactly the line a hurried reader trusts.
- **Major** / `core_docs/Module_Dependencies.md:210` / `| 59_som | Soil organic matter | 8 | 10_land, 29_cropland, 56_ghg_policy |` / The listed set **mixes directions** — 10 and 29 are upstream, 56 is downstream — and omits upstream 30/45/52 and downstream 11/50/51. The answerer flagged the direction-mixing correctly and unprompted.
- **Major** / `modules/module_59.md:18` + `:976` ("8 connections") vs `core_docs/Module_Dependencies.md:322` ("SOM (59) - 5 dependencies") / Neither doc defines its counting methodology, and **neither number matches the code**. Per code: 5 distinct upstream modules {10, 29, 30, 45, 52}; 5 distinct downstream {11, 50, 51, 52, 56}; **union = 9 distinct connected modules** (52 appears on both sides). So "5" coincidentally equals the true inbound count, and "8" matches nothing (undercounts the union by one). Fix: state the methodology and use 9 (or "5 in / 5 out").
- **Minor** / `modules/module_59.md:180` / cites `config/default.cfg:1810` for `c56_emis_policy` / Actual line is **`config/default.cfg:1828`**. Citation drift; the value quoted (`reddnatveg_nosoil`) is correct.
- **Counter-note (doc CORRECT, worth preserving)**: `core_docs/Module_Dependencies.md:135` — "45_climate → 4 modules (14_yields, 52_carbon, 58_peatland, 59_som)" — is **exactly right** per code (`rg -ln pm_climate_class` returns precisely `14_yields/managementcalib_aug19/presolve.gms`, `52_carbon/normal_dec17/{preloop,start}.gms`, `58_peatland/v2/preloop.gms`, `59_som/cellpool_jan23/preloop.gms`, plus the declaring `45_climate/static/input.gms`). The M45→M59 edge **is** in the docs — just not in `module_59.md`'s own list. This is a routing failure, not a knowledge gap, and points at the cheapest fix: reconcile `module_59.md:1034` against `Module_Dependencies.md:135`.

### Missing nuances:
- M59 also writes `pcm_carbon_stock(j,land,"soilc",stockType)` in postsolve (`postsolve.gms:13`) — a genuine outbound write to a shared interface, consumed by `q52_emis_co2_actual` and `q56_emis_pricing_co2`. Absent from the Q2 provided-table (the answer does cover it in Q4).
- Further upstream reads not listed: `fm_croparea` → M30 (`modules/30_croparea/simple_apr24/input.gms:71`), `pm_avl_cropland_iso` → M29 (`modules/29_cropland/simple_apr24/declarations.gms:16`), `pcm_land` → M10 (`presolve.gms:15-25`). These do not change the module-level set {10, 29, 30, 45, 52}.

---

## Q3: M14 default realization, yield calculation, tau factor (G1 anchor)

### Verdict: ACCURATE
### Score: 10/10

Nothing to correct. Both formulas transcribed character-for-character; every line citation exact; every default checked. **G1 anchor holds.**

### Verified claims (correct):
- **Default realization `managementcalib_aug19`** — `config/default.cfg:354`. ✓
- **"The only realization"** — `ls modules/14_yields/` returns exactly `input/`, `managementcalib_aug19/`, `module.gms`. ✓
- **"No `input` realization despite `modules/14_yields/input/` existing as a data directory"** — correct, and a genuinely useful disambiguation (this is the exact shape of the M59 `cellpool_aug16` trap the answer also cleared).
- **`q14_yield_crop` at `equations.gms:14-16`** — exact. Code:
  `vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) * vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));`
  The answer reproduced this **character-for-character**. ✓
- **`q14_yield_past` at `equations.gms:35-39`** — exact line range. Description ("CalibratedPastureYield × ManagementFactor × [1 + spillover × (τ_crop,prev/τ_1995 − 1)]") matches the code, **including the `pcm_tau` previous-timestep subtlety** (`equations.gms:39`). ✓
- **`s14_yld_past_switch` default 0.25** — `modules/14_yields/managementcalib_aug19/input.gms:20` (`/ 0.25 /`) and `config/default.cfg:366`. ✓
- **τ supplied by Module 13 as `vm_tau(j,"crop")`, at cluster level** — `modules/13_tc/endo_jan22/declarations.gms:13`: `vm_tau(j,tautype) Overall agricultural land use intensity tau at cluster level (1)`. Default `tc <- "endo_jan22"` (`config/default.cfg:293`). The `j` index confirms cluster level. ✓
- **Commit `480e300b1`** — exists: "Merge pull request #805 from pvjeetze/f_btc2". Matches the answer's "f_btc2" attribution. ✓
- **τ as sole endogenous yield driver** — structurally correct: `i14_yields_calib(ct,...)` is a `preloop`/`presolve` parameter, so `vm_tau` is the only *variable* on the RHS of `q14_yield_crop`. The "yields frozen without τ" claim follows. ✓
- Illustrative numbers ("if τ doubles, yields double") are explicitly labeled **Conceptually** — correct per the project's numerical-example rule.

### Bugs found:
- None.

### Latent doc bugs (doc wrong, answer survived):
- None found. `module_14.md` and `module_14_notes.md` produced a fully code-accurate answer.

### Missing nuances:
- `q14_yield_crop` normalizes by `fm_tau1995(h2)` at **superregion** (`h`) level while `vm_tau` is at **cluster** (`j`) level — a deliberate asymmetry from the `f_btc2` change. The answer says "normalized against its regional 1995 baseline" and separately notes τ is cluster-level, which is correct but does not spell out the mixed-resolution ratio.
- The preloop calibration pipeline is summarized rather than enumerated; adequate for the question asked.

---

## Q4: `vm_carbon_stock` populators and the path to Module 56 (G2 anchor)

### Verdict: ACCURATE
### Score: 9.5/10

**The G2 anchor did not regress.** The direct-populator set is **exactly** right under defaults, the direct/indirect M30 distinction is right, both negative claims (M52, M58) verified, and every formula and file:line is exact. One Minor prose slip.

### Verified claims (correct):
- **Direct populator set {29, 31, 32, 34, 35, 59} — EXACT**, verified module-by-module at default realizations (`rg -n "vm_carbon_stock"` across `modules/` + `core/`, both `(` and `.` forms):

| Module | Default realization (`config/default.cfg`) | Populating site | Slice |
|---|---|---|---|
| 29 | `detail_apr24` (:811) | `modules/29_cropland/detail_apr24/equations.gms:39` | `crop`, ag_pools |
| 31 | `endo_jun13` (:985) | `modules/31_past/endo_jun13/equations.gms:23` | `past`, ag_pools |
| 32 | `dynamic_may24` (:992) | `modules/32_forestry/dynamic_may24/equations.gms:108` | `forestry`, ag_pools |
| 34 | `exo_nov21` (:1144) | `modules/34_urban/exo_nov21/presolve.gms:8` | `urban`, ag_pools, `.fx = 0` |
| 35 | `pot_forest_may24` (:1153) | `modules/35_natveg/pot_forest_may24/equations.gms:43,50,54` | `primforest`, `secdforest`, `other` |
| 59 | `cellpool_jan23` (:1934) | `modules/59_som/cellpool_jan23/equations.gms:62` | `soilc`, **all** land types |

- **M30 is an indirect populator via M29** — correct and precisely stated. `vm_carbon_stock_croparea` is declared in `modules/30_croparea/simple_apr24/declarations.gms:20` (default `simple_apr24`, `config/default.cfg:912`), computed at `.../equations.gms:50`, and folded into `vm_carbon_stock(j2,"crop",ag_pools,stockType)` by M29 at `modules/29_cropland/detail_apr24/equations.gms:39-40`. ✓
- **M34 citation exact** — `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` at `modules/34_urban/exo_nov21/presolve.gms:8`, character-for-character. ✓
- **M59 populates `soilc` for all land types incl. urban** — correct and a real catch: M34 fixes only `ag_pools` to zero, so urban `soilc` comes from M59 via `noncropland59` (`sets.gms:10-11` includes `urban`). The answer's flag that this is "often missed in the producer list" is well-founded. ✓
- **M52 reads but does not populate** — verified. Its only occurrence is on the **RHS** at `modules/52_carbon/normal_dec17/equations.gms:19`. ✓
- **M58 does not populate `vm_carbon_stock`** — verified with positive control (the same `rg -n "vm_carbon_stock"` sweep returns hits in 8 other modules, so the search is live; 58 returns none). The stated alternative path is confirmed: `q58_peatland_emis` → `vm_emissions_reg(i2,"peatland",poll58)` at `modules/58_peatland/v2/equations.gms:91-92` (default `peatland <- "v2"`, `config/default.cfg:1871`), and `peatland ∈ emis_annual` at `core/sets.gms:321-322` — so it genuinely bypasses one-off stock-change accounting. ✓
- **`vm_carbon_stock` declared in M56** — `modules/56_ghg_policy/price_aug22/declarations.gms:34`. **Exact.** ✓
- **`q56_emis_pricing_co2` at `equations.gms:19-22`** — exact line range; the answer's transcription matches the code **character-for-character**, including the `%c56_carbon_stock_pricing%` macro. ✓
- **M52/M56 are parallel readers, not a serial chain** — verified: M52 reads the `"actual"` slice (`52/.../equations.gms:19`) → `vm_emissions_reg`; M56 reads the `"%c56_carbon_stock_pricing%"` slice (`56/.../equations.gms:22`) → `v56_emis_pricing`. Independent computations from the same array; M56's CO2 path does bypass `vm_emissions_reg`. Sharper than the answer states: under the default `c56_carbon_stock_pricing = "actualNoAcEst"` (`config/default.cfg:1835`) the two even read **different slices**. ✓
- **Split carry-forward** — `modules/56_ghg_policy/price_aug22/postsolve.gms:8` (ag_pools) + `modules/59_som/cellpool_jan23/postsolve.gms:13` (soilc). Both citations exact. ✓
- **Bug-fix commit `931db85c4` (2026-06-25)** — exists and the answer's characterization matches the commit message: "soil pools off by ~17x in a default H12 run", cumulative-since-initialisation instead of per-timestep flux. ✓
- **"Default runs unaffected"** — correct: `c56_emis_policy <- "reddnatveg_nosoil"` (`config/default.cfg:1828`) excludes soil from pricing. ✓

### Bugs found:
- **Minor** / "So the **six** populating modules, explicitly: 29, 30 (indirectly, via 29), 31, 32, 34, 35, and 59." / Seven items follow the word "six". Not a fabricated count — a prose slip, self-corrected in the very next sentence, which correctly gives the six direct populators as {29, 31, 32, 34, 35, 59}. Costs 0.5.

### Latent doc bugs (doc wrong, answer survived):
- None. `module_56.md`, `module_56_notes.md` and `cross_module/carbon_balance_conservation.md` produced a code-exact answer on the highest-risk hub question in the suite, including the M59-`soilc` populator that has been the historical regression site.

### Missing nuances:
- `modules/56_ghg_policy/price_aug22/preloop.gms:11` and `modules/59_som/cellpool_jan23/preloop.gms:32,35` also assign `vm_carbon_stock.l` (starting values). These are solver initializations overwritten by the equations, so excluding them from the populator set is the right call — but a reader grepping `vm_carbon_stock` will hit them and may be confused. Worth an explicit note in the doc that `.l` initialization ≠ population.
- `emis_oneoff` (`core/sets.gms:314-318`) contains all 21 land×pool combinations **including the `*_soilc` slices** — the soil terms are wired into `q56_emis_pricing_co2` and are excluded only by the *policy* switch, not by the equation structure. This is precisely why the `931db85c4` bug was latent rather than inert, and the answer's framing gets it right without stating the set membership.

---

## Summary

| Q | Topic | Verdict | Score |
|---|---|---|---|
| Q1 | M59 SOC mechanism; parameterized vs mechanistic | MOSTLY ACCURATE | 6/10 |
| Q2 | M59 interfaces, consumers, dependencies | MOSTLY ACCURATE | 8/10 |
| Q3 | M14 default realization, yields, tau (**G1**) | ACCURATE | 10/10 |
| Q4 | `vm_carbon_stock` populators → M56 (**G2**) | ACCURATE | 9.5/10 |
| | | **Mean** | **8.375/10** |

**Bugs by severity** — Critical 0 · Major 3 · Minor 1 · Informational 0.

**Latent doc bugs** — Critical 1 · Major 4 · Minor 1. Concentrated entirely in **M59 dependency metadata**; M14/M56 docs are clean.

**Did the docs produce correct answers?** Mostly yes, with one clear systemic exception. The docs carried two hub questions (G1, G2) to near-perfect code-exact answers, including the M59-`soilc` populator slice that has regressed in three prior rounds — **G2 is holding**. Every equation the answerer quoted from docs across all four questions matched the code character-for-character, and every default it relayed was correct. The failure is localized: `module_59.md`'s **dependency-summary line (`:1034`)** omits two real upstream modules (45, 52), and the two connection counts (8 vs 5) are undefined and both wrong against the code's 9 distinct connected modules. The M45 edge is *already documented correctly* at `Module_Dependencies.md:135`, so this is a **routing/reconciliation failure inside the doc set, not missing knowledge** — the cheapest high-value fix in this round.

The one place the docs actively *caused* a wrong answer is `module_59.md:54`'s "subsoil … uses fixed reference value", which the answerer inherited and amplified into "static"/"derived once". Under the default `cc` scenario the LPJmL reference densities are time-varying, and this is the round's only doc-caused error of substance.

Answerer behaviour was strong and should not be penalized where it hedged: it cleared the `cellpool_aug16`/`14_yields/input` non-realization traps, correctly identified a real doc defect (M52) from docs alone, refused to resolve the 8-vs-5 conflict without code (its hedged guess was close to right), and kept 🟡/🔴 provenance labels honest throughout.
