# R54 Doc Audit — `modules/module_14.md` (Yields, `managementcalib_aug19`)

**Auditor:** Opus 4.8 (adversarial doc audit)
**Date:** 2026-07-14
**Target doc:** `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_14.md` (1618 lines)
**Ground truth:** `/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop; read-only worktree) + `config/default.cfg`
**Realization checked:** `managementcalib_aug19` — **CONFIRMED default** (`config/default.cfg:354`: `cfg$gms$yields <- "managementcalib_aug19"`), and the **only** realization (`ls modules/14_yields/` → `input/`, `managementcalib_aug19/`, `module.gms`; `module.gms:30` has a single `$Ifi` branch).

**Verdict: SIGNIFICANT ERRORS.** The 2026-07-14 `im_growing_stock_ysf` sync section (§4.2, §7.1, §9.3) is **almost entirely correct** — the pre-run advisory's specific worry is largely **refuted**. The real damage is in the **older, un-audited sections**: a fabricated circular dependency (§21.3), four mis-attributed interface parameters (§7.2), a wrong producer module for `fm_croparea` (§16.5/§14.2), an invented producer for `f14_yld_ncp_report` (§3.6), and several wrong modification-safety claims (§21.4).

**Bug count:** 2 Critical, 11 Major, 12 Minor, 1 Informational (26 total).
**Claims verified:** ~120 load-bearing, code-checkable claims.

---

## 1. Advisory item — verified specifically (mostly REFUTED)

The pre-run advisory flagged the 2026-07-14 `im_growing_stock_ysf` additions as never independently audited. **I confirm them as almost entirely correct.**

| Advisory sub-item | Verdict | Evidence |
|---|---|---|
| (a) Which module DECLARES / POPULATES `im_growing_stock_ysf` | ✅ **CORRECT** | DECLARED `modules/14_yields/managementcalib_aug19/declarations.gms:18`; POPULATED `.../presolve.gms:64-71`; CLAMPED `.../presolve.gms:80-81`. Doc (`module_14.md:734`) states exactly this. |
| (b) Is `q35_prod_other` really the SOLE consumer? | ✅ **CORRECT** | `rg -n 'im_growing_stock_ysf' /tmp/magpie_develop_ro` → 6 hits total: CHANGELOG, M14 declarations:18, M14 presolve:64/80/81, and **one** read: `modules/35_natveg/pot_forest_may24/equations.gms:166` (inside `q35_prod_other`, the `youngsecdf` term). Sole consumer **confirmed**. |
| (c) file:line citations for the new parameter | ✅ **CORRECT** | `presolve.gms:64-71` ✓, `presolve.gms:80-81` ✓, `declarations.gms:18` ✓ (§9.3), `equations.gms:166` ✓, `52_carbon/normal_dec17/declarations.gms:10` ✓, `52_carbon/normal_dec17/start.gms:43` ✓, `35_natveg/pot_forest_may24/presolve.gms:242` ✓. **One exception**: `module_14.md:736` "Citation: `declarations.gms:17`" sits under the ysf block but points at `im_growing_stock` (bug M14-B16). |
| (d) The clamp claims (positivity floor + `s14_minimum_growing_stock`) | ✅ **CORRECT** | `presolve.gms:80` = positivity floor (`+ 0.0001$(... = 0)`); `presolve.gms:81` = `$(... < s14_minimum_growing_stock) = 0`. `s14_minimum_growing_stock` = **5** (`input.gms:19`, `/ 5 /`) ✓. Both clamps ARE restated as the doc claims. |
| (e) `land_timber` does not contain `youngsecdf` | ✅ **CORRECT** | `core/sets.gms:256-257`: `land_timber(land) ... / forestry, primforest, secdforest, other /` — **exact match** to the doc's quote and line range. `othertype35 / othernat, youngsecdf /` at `modules/35_natveg/pot_forest_may24/sets.gms:23-24` ✓ exact. |
| (f) `pm_carbon_density_secdforest_ac_uncalib` — "added 2026-07-14 (`6b00f9dea`)" | ❌ **REFUTED — BUG (M14-B5)** | `git show --stat 6b00f9dea` → 4 files, **none in `modules/52_carbon/`**. `git show 6b00f9dea^:modules/52_carbon/normal_dec17/declarations.gms \| grep uncalib` → the parameter **already existed** at line 10. `git blame` → introduced by **`896a9b728` (2026-03-21)**. |

**Also refuted (in the doc's favor):** the doc's `nl_fix.gms:10-11` code block reproduces the code **verbatim**, including the `vm_tau.l(h,"crop")` / `pcm_tau(h,"crop")` **super-region** indices — which look stale next to the f_btc2 cluster-level rename but are what the code actually says. Not a doc bug.

---

## 2. Verified-correct claims (high-confidence, spot list)

| Claim | Evidence |
|---|---|
| Default realization `managementcalib_aug19`; only realization | `config/default.cfg:354`; `modules/14_yields/module.gms:30` |
| 2 equations: `q14_yield_crop`, `q14_yield_past` | `declarations.gms:31-32` |
| `q14_yield_crop` at `equations.gms:14-16`, quoted GAMS **byte-identical** | `equations.gms:14-16` |
| `q14_yield_past` at `equations.gms:35-39`, quoted GAMS **byte-identical** | `equations.gms:35-39` |
| `vm_tau`/`pcm_tau` at **cluster level `(j,tautype)`** (f_btc2) | `modules/13_tc/endo_jan22/declarations.gms:13,27` (default); `exo/declarations.gms:9,16` |
| Commit `480e300b1` = "Merge PR #805 from pvjeetze/f_btc2 — Options for tau on conservation priority land" | `git show --stat 480e300b1` |
| All 6 scalar defaults: `s14_limit_calib`=1, `s14_calib_ir2rf`=1, `s14_degradation`=0, `s14_use_yield_calib`=0, `s14_minimum_growing_stock`=5, `s14_yld_past_switch`=0.25, `s14_yld_reduction_soil_loss`=0.08, `sm_carbon_fraction`=0.5 | `input.gms:15-22` — **every value and line number correct** |
| `c14_yields_scenario` default `cc` | `input.gms:8`; `config/default.cfg:360` |
| **9 input files**, all 9 `$include` line numbers (`input.gms:30,37,47,53,61,69,77,85,93`) | `input.gms` — **all 9 exact** |
| Preloop stage citations: 10-12, 14-27, 67-73, 82-102, 108-116, 123-150, 137-147, 155-173, 190-195 | `preloop.gms` — **all exact**; every quoted GAMS block matches code |
| Presolve blocks: 24-31, 33-40, 42-49, 51-58, 64-71, 75-81 | `presolve.gms` — **all exact**; quoted GAMS matches |
| Growing-stock formula `C / sm_carbon_fraction × fm_aboveground_fraction / fm_ipcc_bef` | `presolve.gms:24-71` ✓ |
| `vm_yld` consumers = **M30 + M31 only** | `rg 'vm_yld\('` AND `rg 'vm_yld\.'` (both forms): `30_croparea/{simple,detail}_apr24/equations.gms:15`, `31_past/endo_jun13/equations.gms:18`. No other module. **MANDATE 13 + solution-level check both clean.** |
| `im_growing_stock` consumers = **M32 + M35** (`q32_prod_forestry`, `i32_growing_stock_at_harvest`, `pc32_prod_forestry_ini`; `q35_prod_secdforest`, `q35_prod_primforest`, `q35_prod_other`) | `32_forestry/dynamic_may24/equations.gms:249`, `presolve.gms:181,185`; `35_natveg/pot_forest_may24/equations.gms:147,156,165` — **all 6 named symbols confirmed** |
| `sm_carbon_fraction`, `fm_aboveground_fraction`, `fm_ipcc_bef` also consumed by **M52 preloop** | `52_carbon/normal_dec17/preloop.gms:60,95` / `:61,96` / `:26` ✓ |
| `pm_past_mngmnt_factor` from **M70** | `70_livestock/fbask_jan16/declarations.gms:41`, populated `presolve.gms:64-67` ✓ |
| `fm_tau1995(h)` from **M13** | `13_tc/endo_jan22/input.gms:51` ✓ |
| M52 carbon-density citations `presolve.gms:26,44,53,66` and `fm_carbon_density` at `presolve.gms:35` | all exact ✓ |
| `nl_release.gms:10-11` quoted verbatim | ✓ |
| §3.6 pollination example (40% dep × 30% deficiency = 12% loss) | arithmetic correct: `y(1-0.4) + y(0.4)(0.7) = 0.88y` ✓ |
| §18 `biocorrect` removed by `cc84ae5e1` "Update to new revision and clean up old realizations" (2021-10-04) | `git show --stat cc84ae5e1` ✓ title matches exactly |
| `ltype14 / crop, past /`, `ncp_type14 / soil_intact, poll_suff /` | `sets.gms:9-10, 33-34` ✓ |
| §11.6 "No Nitrogen or Water Constraints in Yield Equations" | ✓ exhaustive symbol enumeration of M14 finds no N/water/SOM symbol |

---

## 3. Bugs found

### 🔴 M14-B1 — Critical — Fabricated circular dependency (Production-Yield-Livestock triangle)

- **Class:** 15 (latent doc error) / 4 (conceptual pseudo-code)
- **Trigger:** Critical — "build on a false foundation"; "Fabricated formula presented as the code's actual implementation" (here: a fabricated *dependency chain*, presented under the heading "**Resolution mechanism in code**").
- **doc_line:** `module_14.md:1424-1473` (§21.3), chain at `:1432-1446`
- **Claim in doc:**
  > "**Module 14 participates in 1 major circular dependency** … `vm_prod(j,kcr) [17] → Used for calibration of yields` ↓ `pm_yields_semi_calib(j,kcr,w) [14]` ↓ `vm_yld(j,kcr,w) [14]` … ↓ `Manure production [70/55] → Affects soil fertility` ↓ `pm_yields_semi_calib(j,kcr,w) [14] → **BACK TO START** (via soil organic matter effects)`" and "**Resolution mechanism in code** … **SOM effects gradual**: 15% annual convergence (Module 59) → smooth feedback"
- **Reality in code:** **No arrow in this cycle exists.**
  1. M14 **never reads `vm_prod`**. Exhaustive enumeration of every `vm_/pm_/fm_/sm_/im_/pcm_` symbol referenced anywhere in `modules/14_yields/managementcalib_aug19/*.gms` yields exactly: `vm_yld`, `vm_tau`, `pcm_tau`, `fm_tau1995`, `pm_past_mngmnt_factor`, `fm_croparea`, `pm_land_start`, `pm_climate_class`, `fm_carbon_density`, `pm_carbon_density_{plantation,secdforest,secdforest_uncalib,other}_ac`, `fm_ipcc_bef`, `fm_aboveground_fraction`, `sm_carbon_fraction`, `sm_fix_cc`, `pm_yields_semi_calib`, `im_growing_stock`, `im_growing_stock_ysf`. **No `vm_prod`, no SOM, no manure, no nitrogen symbol.**
  2. `pm_yields_semi_calib` does **not** feed `vm_yld`. It is a *1995 snapshot output* (`preloop.gms:116,149`) whose **only** consumer in the model is `modules/17_production/flexreg_apr16/presolve.gms:10` (`pm_prod_init`). `vm_yld` is computed from `i14_yields_calib` (`equations.gms:15`).
  3. There is **no SOM/manure → yield** path. M59/M55/M50 read **no** M14 output, and M14 reads **no** M59/M55/M50 symbol. MAgPIE has **no soil-organic-matter feedback on yields**.
  - The doc **contradicts itself**: §8.3 (`:832`) says "**Circular Dependencies: None directly in equations**", and §11.6 (`:982`) says "Nitrogen impacts on yields are **external** (LPJmL input), not calculated in Module 14".
- **file_evidence:** `modules/14_yields/managementcalib_aug19/preloop.gms:8-197` + `presolve.gms:1-81` (no such symbol); `modules/17_production/flexreg_apr16/presolve.gms:10` (the *only* `pm_yields_semi_calib` read)
- **verify_cmd (with results):**
  - `rg -oN '\b(vm_|pm_|fm_|sm_|im_|pcm_)[a-zA-Z0-9_]+' /tmp/magpie_develop_ro/modules/14_yields/managementcalib_aug19/*.gms | sort -u` → 18 distinct symbols, **none** production/SOM/manure/N
  - `rg -n 'vm_prod|som|manure|nutrient|vm_carbon_stock|p59|v59|vm_nr' /tmp/magpie_develop_ro/modules/14_yields/` → **only** `preloop.gms:160` (the English word "production" in a comment). Positive control: `rg -c 'vm_yld' .../equations.gms` → `2` (search works).
  - `rg -n 'vm_yld|pm_yields_semi_calib|im_growing_stock' /tmp/magpie_develop_ro/modules/59_som/ /tmp/magpie_develop_ro/modules/55_awms/ /tmp/magpie_develop_ro/modules/50_nr_soil_budget/` → **no match**. Positive control: `rg -c 'pm_climate_class' .../59_som/cellpool_jan23/preloop.gms` → `4` (search works).
  - `rg -n 'pm_yields_semi_calib' /tmp/magpie_develop_ro/modules/` → only M14 (decl+2 writes) and `17_production/flexreg_apr16/presolve.gms:10`.
- **confirmed:** true (two independent methods + positive controls)
- **Proposed fix:** Replace §21.3 (`module_14.md:1422-1492`) entirely with:
  > ### 21.3 Circular Dependencies
  >
  > **Module 14 participates in NO circular dependency.** Verified against code (2026-07-14): Module 14's calibration (`preloop.gms`) reads only exogenous file parameters (`f14_yields`, `f14_fao_yields_hist`, `f14_pyld_hist`, `f14_ir2rf_ratio`, `f14_yld_calib`, `f14_yld_ncp_report`, `f14_kcr_pollinator_dependence`) plus `fm_croparea` (Module 30 input file), `pm_land_start` (Module 10), and `fm_tau1995` (Module 13). **No optimization variable enters the calibration.** Module 14 reads **no** `vm_prod`, **no** soil-organic-matter (Module 59), **no** manure (Module 55), and **no** nitrogen variable — see §11.6.
  >
  > The only simultaneity is the **within-timestep** co-solve of `vm_tau` (Module 13, endogenous under the default `endo_jan22`) and `vm_yld` (`q14_yield_crop`, `equations.gms:14-16`); this is resolved by the optimizer, not by a temporal lag. Pasture spillover uses the **previous** timestep's `pcm_tau` (`equations.gms:39`), which is a lag by construction, not a cycle resolution.
  >
  > **There is no SOM → yield feedback in MAgPIE.** Any claim that manure or soil carbon affects Module 14 yields is false; soil-fertility effects are implicit in the LPJmL input yields, not modelled.

  Also delete the "Testing for cycle stability" R block (`:1475-1492`), which tests a non-existent cycle, and align §8.3's hedged "bootstrap dependency" prose with the above.

---

### 🔴 M14-B2 — Critical — `fm_croparea` attributed to **Module 10**; it comes from **Module 30**

- **Class:** 15 (wrong producer set — R20 anchor) / 12
- **Trigger:** §1.5 latent-doc mandate: "a wrong producer/consumer set is **Critical** per the R20 anchor". Repeated in *actionable debugging advice*.
- **doc_line:** `module_14.md:1240` (§16.5) and `module_14.md:1128` (§14.2)
- **Claim in doc:**
  > §16.5: "**Module 10 (Land):** Provides `fm_croparea` (historical cropland patterns) for calibration weighting"
  > §14.2: "**Solutions:** 1. Check cropland input data from **Module 10**"
- **Reality in code:** `fm_croparea(t_all,j,w,kcr)` is **declared and loaded by Module 30 (croparea)** — `modules/30_croparea/simple_apr24/input.gms:71` (the **default** realization, `config/default.cfg:912`) and `modules/30_croparea/detail_apr24/input.gms:76`. Module 10 (`landmatrix_dec18`) contains **zero** occurrences of `croparea`. Module 10 *does* provide `pm_land_start` (`10_land/landmatrix_dec18/declarations.gms:9`, populated `start.gms:8`) — which the doc mis-files elsewhere (see M14-B3).
- **file_evidence:** `modules/30_croparea/simple_apr24/input.gms:71` — `table fm_croparea(t_all,j,w,kcr) Different croparea type areas (mio. ha)`
- **verify_cmd (with results):**
  - `rg -n 'fm_croparea' --glob '!modules/14_yields/**' /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/` → declarations only in `30_croparea/{simple,detail}_apr24/input.gms:71/76`; readers = M17, M30, M59. **Module 10 absent.**
  - `rg -n 'croparea' /tmp/magpie_develop_ro/modules/10_land/` → **NO MATCH**. Positive control: `rg -c 'pm_land_start' /tmp/magpie_develop_ro/modules/10_land/landmatrix_dec18/declarations.gms` → `1` (rg does reach M10).
- **confirmed:** true (two methods + positive control)
- **Proposed fix:**
  - `module_14.md:1240` → `- **Module 30 (Croparea):** Provides \`fm_croparea(t_all,j,w,kcr)\` (historical crop-area patterns, \`modules/30_croparea/simple_apr24/input.gms:71\` — default realization) for calibration weighting (\`preloop.gms:60,68-73,127,138-143\`)`
  - Add to §16.5: `- **Module 10 (Land):** Provides \`pm_land_start(j,"past")\` (\`modules/10_land/landmatrix_dec18/declarations.gms:9\`, populated \`start.gms:8\`) — the weight for the regional LPJmL pasture-yield average (\`preloop.gms:15-16\`)`
  - `module_14.md:1128` → `1. Check cropland input data from **Module 30 (croparea)** — \`fm_croparea\` is loaded in \`modules/30_croparea/simple_apr24/input.gms:71\`, not in Module 10`

---

### 🟠 M14-B3 — Major — §7.2 "From Input Data" mis-attributes four **module-owned** interface parameters

- **Class:** 15 / 12 (interface ownership)
- **Trigger:** Major — misleads about behavior/ownership; wrong interface attribution.
- **doc_line:** `module_14.md:787-794` (§7.2, block header "**From Input Data:**")
- **Claim in doc:**
  > "**From Input Data:** — `fm_croparea(t_all,j,w,kcr)` … `pm_land_start(j,"past")` … `fm_carbon_density(t,j,"primforest","vegc")` … `pm_climate_class(j,clcl)`"
- **Reality in code:** **All four are provided by other modules**, not by Module-14 input files (M14's own file inputs are the nine `f14_*`/`lpj_yields` files in §6):
  - `fm_croparea` → **Module 30** (`30_croparea/simple_apr24/input.gms:71`)
  - `pm_land_start` → **Module 10** (`10_land/landmatrix_dec18/declarations.gms:9`; `start.gms:8`)
  - `fm_carbon_density` → **Module 52** (`52_carbon/normal_dec17/input.gms:16`; the *only* declaration in the repo)
  - `pm_climate_class` → **Module 45** (`45_climate/static/input.gms:10`, default realization `static`, `config/default.cfg:1492`)
- **file_evidence:** `modules/45_climate/static/input.gms:10` — `table pm_climate_class(j,clcl) Koeppen-Geiger climate classification on the simulation cluster level (1)`
- **verify_cmd (with results):** `rg -n 'pm_climate_class|fm_croparea|pm_land_start|fm_carbon_density' /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/ | grep -E 'declarations|input\.gms'` → the four declaration sites above; `rg -n '^\s*(table|parameter[s]?)\s+fm_carbon_density' modules/ core/` → **exactly one hit**, `modules/52_carbon/normal_dec17/input.gms:16`.
- **confirmed:** true
- **Proposed fix:** Replace the `**From Input Data:**` header and its four bullets (`module_14.md:787-794`) with:
  ```
  **From Module 30 (Croparea):**
  - **fm_croparea(t_all,j,w,kcr)**: Historical crop-area patterns (calibration weights) — declared `modules/30_croparea/simple_apr24/input.gms:71` (default realization). Used in `preloop.gms:60,68-73,127,138-143`.

  **From Module 10 (Land):**
  - **pm_land_start(j,"past")**: Initial (1995) pasture area — declared `modules/10_land/landmatrix_dec18/declarations.gms:9`, populated `start.gms:8`. Weight for the regional LPJmL pasture-yield average (`preloop.gms:15-16`).

  **From Module 45 (Climate):**
  - **pm_climate_class(j,clcl)**: Köppen-Geiger climate classification — declared `modules/45_climate/static/input.gms:10` (default realization `static`). Weights `fm_ipcc_bef(clcl)` in the growing-stock conversion (`presolve.gms:29,38,47,56,69`). NOTE: used in **presolve** (growing stock), NOT in the yield calibration.
  ```
  and move `fm_carbon_density` into the existing "**From Module 52 (Carbon)**" block (see M14-B4).

---

### 🟠 M14-B4 — Major — "`fm_carbon_density` … **not an M52 parameter**" — it is declared, loaded and transformed by Module 52

- **Class:** 15 / 12 (interface ownership)
- **Trigger:** Major — wrong interface attribution; hides a real cross-module scenario coupling.
- **doc_line:** `module_14.md:775` (§7.2, closing note of the "From Module 52" block)
- **Claim in doc:**
  > "Note `primforest` reads `fm_carbon_density` (`presolve.gms:35`), a file parameter — **not an M52 `pm_` parameter** — which is why it is absent from this list."
- **Reality in code:** `fm_carbon_density(t_all,j,land,c_pools)` is **declared and `$include`d inside Module 52** (`modules/52_carbon/normal_dec17/input.gms:16`) — the only declaration in the repository (52_carbon has exactly one realization). M52 also **transforms** it: `input.gms:22-23` apply the `c52_carbon_scenario` `nocc`/`nocc_hist` logic, and `input.gms:31` zero-fills forest classes from `"other"`. Consequence the doc misses: **M14's `primforest` growing stock inherits Module 52's carbon scenario switch** (`c52_carbon_scenario`), independently of M14's own `c14_yields_scenario`.
- **file_evidence:** `modules/52_carbon/normal_dec17/input.gms:16,22-23,31`
- **verify_cmd (with results):** `rg -n '^\s*(table|parameter[s]?)\s+fm_carbon_density' /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/` → `modules/52_carbon/normal_dec17/input.gms:16: table fm_carbon_density(t_all,j,land,c_pools) LPJmL carbon density for land and carbon pools (tC per ha)` (single hit). `ls -d /tmp/magpie_develop_ro/modules/52_carbon/*/` → `input/`, `normal_dec17/` (one realization).
- **confirmed:** true
- **Proposed fix:** Replace `module_14.md:775` with:
  > **Citation:** Used in `presolve.gms:26,44,53,66` (`:66` is the youngsecdf block). `primforest` additionally reads **`fm_carbon_density(t,j,"primforest","vegc")`** (`presolve.gms:35`) — a *file* parameter, but one **declared and loaded by Module 52** (`modules/52_carbon/normal_dec17/input.gms:16`) and transformed there by the `c52_carbon_scenario` switch (`input.gms:22-23`) and the forest zero-fill (`input.gms:31`). So M14's `primforest` growing stock is **also** downstream of Module 52's carbon scenario, not only of `c14_yields_scenario`.

---

### 🟠 M14-B5 — Major — `pm_carbon_density_secdforest_ac_uncalib` was **NOT** added by `6b00f9dea`, and is **not** used only for `im_growing_stock_ysf`

- **Class:** 15 / 12 (wrong provenance + wrong consumer set)
- **Trigger:** Major — citation/attribution to content that says something materially different; scope claim false model-wide.
- **doc_line:** `module_14.md:773` (§7.2)
- **Claim in doc:**
  > "**pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")**: Secondary forest carbon density, **uncalibrated** (tC/ha) — **added 2026-07-14 (`6b00f9dea`)**; the pre-calibration snapshot of the secdforest curve (`modules/52_carbon/normal_dec17/start.gms:43`), **used *only* for `im_growing_stock_ysf`**"
- **Reality in code:**
  1. `6b00f9dea` touched **exactly 4 files** — `CHANGELOG.md`, `14_yields/.../declarations.gms` (+1), `14_yields/.../presolve.gms` (+16), `35_natveg/pot_forest_may24/equations.gms` (2 changed). **It never touched `modules/52_carbon/`.** The parameter already exists in that commit's parent. It was introduced by **`896a9b728` (2026-03-21, florianh, "Address review comments: cost regionalization, naming conventions, calibration simplification")**.
  2. Model-wide it has **four consuming modules**, not one: M14 (`presolve.gms:66`), **M29** (`29_cropland/detail_apr24/preloop.gms:46`), **M32** (`32_forestry/dynamic_may24/presolve.gms:59,68`), **M35** (`35_natveg/pot_forest_may24/presolve.gms:117,242,251`). ("Used only for `im_growing_stock_ysf`" is true only *within Module 14* — the sentence does not say so.)
- **file_evidence:** `modules/52_carbon/normal_dec17/declarations.gms:10` (blame → `896a9b728a florianh 2026-03-21`); `modules/29_cropland/detail_apr24/preloop.gms:46`; `modules/32_forestry/dynamic_may24/presolve.gms:59,68`; `modules/35_natveg/pot_forest_may24/presolve.gms:117,242,251`
- **verify_cmd (with results):**
  - `git -C /tmp/magpie_develop_ro show --stat 6b00f9dea` → 4 files changed, none under `modules/52_carbon/`
  - `git -C /tmp/magpie_develop_ro show 6b00f9dea^:modules/52_carbon/normal_dec17/declarations.gms | grep -n uncalib` → `10: pm_carbon_density_secdforest_ac_uncalib(...)` — **already present in the parent**
  - `git -C /tmp/magpie_develop_ro blame -L 10,10 modules/52_carbon/normal_dec17/declarations.gms` → `896a9b728a (florianh 2026-03-21)`
  - `rg -n 'pm_carbon_density_secdforest_ac_uncalib' /tmp/magpie_develop_ro/modules/` → 10 hits across M14, M29, M32, M35, M52
- **confirmed:** true
- **Proposed fix:** Replace `module_14.md:773` with:
  > - **pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")**: Secondary-forest carbon density, **uncalibrated** (tC/ha) — the pre-calibration snapshot of the secdforest curve (declared `modules/52_carbon/normal_dec17/declarations.gms:10`, populated `modules/52_carbon/normal_dec17/start.gms:43`). **Added 2026-03-21 (`896a9b728`), not by `6b00f9dea`** — commit `6b00f9dea` only added Module 14's *read* of it. Model-wide it has four consumers: M14 (`presolve.gms:66`, `im_growing_stock_ysf`), M29 (`detail_apr24/preloop.gms:46`), M32 (`dynamic_may24/presolve.gms:59,68`, afforestation/NDC carbon), M35 (`pot_forest_may24/presolve.gms:117,242,251`, youngsecdf carbon). **Within Module 14** it is used only for `im_growing_stock_ysf`.

---

### 🟠 M14-B6 — Major — `f14_yld_ncp_report` has **no producing module**; the doc invents one

- **Class:** 15 (invented producer) / 2
- **Trigger:** Major — invented interface ownership; would send a reader hunting in M29/M35 for a producer that does not exist, and implies MAgPIE has endogenous NCP tracking (it does not).
- **doc_line:** `module_14.md:392` (§3.6)
- **Claim in doc:**
  > "**NCP Tracking:** Module 14 **expects another module to provide** `f14_yld_ncp_report(t,j,ncp_type14)` with "soil_intact" and "poll_suff" shares (**likely Module 29 or Module 35**)."
- **Reality in code:** `f14_yld_ncp_report` is a **Module-14 file table** (`f14_` prefix = file-read, module-local), declared at `modules/14_yields/managementcalib_aug19/input.gms:83` and optionally `$include`d from `./modules/14_yields/input/f14_yld_ncp_report.cs3` (`input.gms:85`, guarded by `$if exist`). If the file is absent, `preloop.gms:186-188` sets it to **1** (no degradation). **No module writes it** — it appears nowhere outside `modules/14_yields/`. The doc's own §6.7 (`:678`) correctly calls it an input file, contradicting §3.6.
- **file_evidence:** `modules/14_yields/managementcalib_aug19/input.gms:83-88`; `preloop.gms:186-188`
- **verify_cmd (with results):** `rg -n 'f14_yld_ncp_report|yld_ncp' /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/ /tmp/magpie_develop_ro/scripts/` → 6 hits, **all in `modules/14_yields/managementcalib_aug19/`**. Positive control: `rg -c 'f14_kcr_pollinator_dependence' .../preloop.gms` → `2`.
- **confirmed:** true
- **Proposed fix:** Replace `module_14.md:392` with:
  > **NCP data provenance:** `f14_yld_ncp_report(t_all,j,ncp_type14)` is **not produced by any MAgPIE module**. It is an **optional Module-14 input file** (`modules/14_yields/input/f14_yld_ncp_report.cs3`, declared `input.gms:83`, `$include`d only `$if exist` at `input.gms:85`) supplied by the R preprocessing layer. If the file is missing, `preloop.gms:186-188` sets it to **1** everywhere, so degradation has no effect even when `s14_degradation = 1`.

---

### 🟠 M14-B7 — Major — Pasture-management dynamics are **not** realization-dependent in Module 70

- **Class:** 15 / advisory drift
- **Trigger:** Major — "Recommendation that contradicts maintainer practice"; misleading debugging advice.
- **doc_line:** `module_14.md:1164` (§14.5)
- **Claim in doc:**
  > "**Solution:** Check Module 70 realization. **Some realizations provide dynamic `pm_past_mngmnt_factor` based on livestock demand, others use fixed values.**"
- **Reality in code:** Module 70 has exactly two realizations (`fbask_jan16`, `fbask_jan16_sticky`) and their `pm_past_mngmnt_factor` code is **identical** (`diff` of the two `presolve.gms` shows only a comment-wording change at line 24 and the sticky-capital block appended at lines 71-95). The dynamic-vs-fixed behaviour is controlled by the **scalar** `s70_past_mngmnt_factor_fix` — "Year until the pasture management factor is fixed to 1", default **2005** (`70_livestock/fbask_jan16/input.gms:26`; also exposed as `cfg$gms$s70_past_mngmnt_factor_fix <- "2005"`, `config/default.cfg:2173`): `presolve.gms:63-68` sets `pm_past_mngmnt_factor = 1` for `m_year(t) <= s70_past_mngmnt_factor_fix` and applies the cattle-driven formula afterwards.
- **file_evidence:** `modules/70_livestock/fbask_jan16/presolve.gms:63-68`; `modules/70_livestock/fbask_jan16/input.gms:26`; `config/default.cfg:2173`
- **verify_cmd (with results):** `diff /tmp/magpie_develop_ro/modules/70_livestock/fbask_jan16/presolve.gms /tmp/magpie_develop_ro/modules/70_livestock/fbask_jan16_sticky/presolve.gms` → only `24c24` (comment) and `70a71,95` (sticky capital block); the `pm_past_mngmnt_factor` block is byte-identical. `rg -n 's70_past_mngmnt_factor_fix' modules/70_livestock/ config/default.cfg` → `/ 2005 /` in both realizations + `config/default.cfg:2173`.
- **confirmed:** true
- **Proposed fix:** Replace `module_14.md:1162-1166` with:
  > **Likely Cause:** `pm_past_mngmnt_factor` is pinned to 1. In **both** Module-70 realizations (`fbask_jan16`, `fbask_jan16_sticky` — the code is identical here), `modules/70_livestock/fbask_jan16/presolve.gms:63-68` sets `pm_past_mngmnt_factor(t,i) = 1` for every year `m_year(t) <= s70_past_mngmnt_factor_fix` (**default 2005**, `70_livestock/fbask_jan16/input.gms:26`; `config/default.cfg:2173`) and only then applies the cattle-driven formula.
  >
  > **Solution:** Check `s70_past_mngmnt_factor_fix`, **not** the Module-70 realization — switching realization changes nothing here. Also check `s14_yld_past_switch` (default 0.25) for the crop-τ spillover term.

---

### 🟠 M14-B8 — Major — `sm_carbon_fraction` is **not** a "bioenergy yield conversion factor"

- **Class:** 15 / advisory drift
- **Trigger:** Major — advisory drift; wrong parameter role in an actionable "✅ Safe Modifications" list.
- **doc_line:** `module_14.md:1511` (§21.4)
- **Claim in doc:**
  > "✅ **Change bioenergy yield conversion factors** (`sm_carbon_fraction`, superset — was `s14_carbon_fraction` before 2026-04-20) **if using bioenergy scenarios**"
- **Reality in code:** `sm_carbon_fraction` (0.5 tC/tDM, `input.gms:22`) is used **only** in the growing-stock (timber) conversion — `presolve.gms:27,36,45,54,67` — and by **Module 52's growing-stock calibration** (`52_carbon/normal_dec17/preloop.gms:60,95`). It **never touches bioenergy yields**: the bioenergy (`begr`/`betr`) correction is `preloop.gms:11-12`, which uses `fm_tau1995` and `smax(h,fm_tau1995(h))` only. Changing `sm_carbon_fraction` would silently rescale **all four (five, with ysf) growing-stock curves and M52's FRA calibration** while doing nothing at all to bioenergy yields.
- **file_evidence:** `modules/14_yields/managementcalib_aug19/preloop.gms:11-12` (bioenergy, no `sm_carbon_fraction`); `presolve.gms:27,36,45,54,67`; `modules/52_carbon/normal_dec17/preloop.gms:60,95`
- **verify_cmd (with results):** `rg -n 'sm_carbon_fraction' /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/` → 9 hits: `14_yields/.../input.gms:22` (decl), `presolve.gms:16,27,36,45,54,67`, `52_carbon/normal_dec17/preloop.gms:60,95`. **No hit in `preloop.gms:11-12` (the bioenergy block).**
- **confirmed:** true
- **Proposed fix:** Replace `module_14.md:1510-1511` with:
  > - ✅ Modify timber conversion factors — but note the blast radius: `sm_carbon_fraction` (0.5 tC/tDM, `input.gms:22`), `fm_aboveground_fraction`, and `fm_ipcc_bef` are **shared interface parameters read by Module 52's growing-stock calibration** (`52_carbon/normal_dec17/preloop.gms:26,60-61,95-96`) as well as by M14's `presolve.gms:24-71`. Changing any of them shifts **both** M14 growing stock and M52's FRA calibration.
  > - ⚠️ **`sm_carbon_fraction` has nothing to do with bioenergy.** Bioenergy (`begr`/`betr`) yields are corrected in `preloop.gms:11-12` using `fm_tau1995` / `smax(h,fm_tau1995(h))` only.

---

### 🟠 M14-B9 — Major — `s14_limit_calib` treated as a continuous "bound" with lower/upper values

- **Class:** 13 (wrong parameter semantics) / advisory drift
- **Trigger:** Major — right concept, wrong parameter type; would lead a user to set fractional values on a binary switch.
- **doc_line:** `module_14.md:1514-1516` (§21.4 Moderate-Risk) and `module_14.md:1593` (§21.4 Emergency Fixes)
- **Claim in doc:**
  > "⚠️ Change limited calibration **bounds** (`s14_limit_calib`): **Lower bound** → more LPJmL influence → may mismatch FAO; **Higher bound** → more statistical adjustment → may mask climate signal"
  > "If food demand infeasibility: **Increase `s14_limit_calib` upper bound** (allow more statistical adjustment)"
- **Reality in code:** `s14_limit_calib` is a **binary switch**, `/ 1 /` (`input.gms:15`: "Relative managament calibration switch (1=limited 0=pure relative)"). `preloop.gms:85-93` branches on exactly two values: `if (s14_limit_calib = 0) → i14_lambda_yields = 1`; `Elseif (s14_limit_calib = 1) → λ = 1 or sqrt(LPJmL/FAO)`. Any other value leaves `i14_lambda_yields` at its **default 0** (→ pure-additive calibration everywhere). It has no "bounds", no upper value, and raising it does not "allow more statistical adjustment" — `= 1` (the default) *restricts* the relative amplification. The doc's own §5.2 (`:569-575`) states this correctly.
- **file_evidence:** `modules/14_yields/managementcalib_aug19/input.gms:15`; `preloop.gms:82-102`
- **verify_cmd (with results):** `sed -n '15p' input.gms` → `s14_limit_calib   Relative managament calibration switch (1=limited 0=pure relative) / 1 /`; `sed -n '82,102p' preloop.gms` → `if ((s14_limit_calib = 0) … Elseif (s14_limit_calib =1 ) …` (only two branches).
- **confirmed:** true
- **Proposed fix:**
  - `module_14.md:1514-1516` → `- ⚠️ Toggle limited calibration (\`s14_limit_calib\`, **binary 0/1**, default **1**, \`input.gms:15\`): setting it to **0** switches from λ-blended limited calibration to **pure relative** calibration (λ ≡ 1, \`preloop.gms:86\`), which over-amplifies future yields where the LPJmL baseline is underestimated. It is not a continuous "bound".`
  - `module_14.md:1593` → `- If food demand infeasibility: **do not touch \`s14_limit_calib\`** (binary; default 1 is already the conservative setting). Investigate \`f14_yld_calib\` (\`s14_use_yield_calib = 1\`) or the Module 13 τ trajectory instead.`

---

### 🟠 M14-B10 — Major — "Remove calibration entirely (`s14_use_yield_calib = 0` AND `s14_limit_calib = 0`)" — `s14_use_yield_calib = 0` is the **default**, and neither switch removes calibration

- **Class:** 13 (default-state error) / 15
- **Trigger:** Major — "Missing default-state caveat"; presents the **default** config as a high-risk expert-only modification with a consequence it does not have.
- **doc_line:** `module_14.md:1532-1534` (§21.4 High-Risk)
- **Claim in doc:**
  > "🔴 **Remove calibration entirely** (`s14_use_yield_calib = 0` AND `s14_limit_calib = 0`): Pure LPJmL yields often unrealistic … Model likely infeasible (can't meet food demand)"
- **Reality in code:**
  - `s14_use_yield_calib = 0` is the **DEFAULT** (`input.gms:18`, `/ 0 /`). Every stock MAgPIE run already has it. It only skips the *optional post-hoc* `f14_yld_calib` factors (`preloop.gms:165-173`), which are set to 1 when the switch is 0 **or** the CSV is missing.
  - `s14_limit_calib = 0` does **not** remove calibration: it sets λ ≡ 1 (`preloop.gms:86`), i.e. **pure relative FAO calibration**, which is still a full calibration to FAO regional yields (`preloop.gms:108-116`).
  - Neither switch, alone or together, yields "pure LPJmL yields". The FAO limited/relative calibration (`preloop.gms:108-116`) and the AQUASTAT ir2rf calibration (`preloop.gms:123-150`) run regardless.
- **file_evidence:** `input.gms:18` (`/ 0 /`); `preloop.gms:86,108-116,165-173`
- **verify_cmd (with results):** `sed -n '18p' input.gms` → `s14_use_yield_calib  … (1=use facs 0=not use facs) / 0 /`; `sed -n '165,173p' preloop.gms` → `if(s14_use_yield_calib = 0 OR sum((i,ltype14),f14_yld_calib(i,ltype14)) = 0, f14_yld_calib(i,ltype14) = 1;);`
- **confirmed:** true
- **Proposed fix:** Replace `module_14.md:1532-1534` with:
  > - 🔴 There is **no switch that removes calibration**. `s14_use_yield_calib = 0` is the **default** (`input.gms:18`) and merely skips the optional post-hoc `f14_yld_calib` factors (`preloop.gms:165-173`); `s14_limit_calib = 0` switches λ to a constant 1, i.e. **pure relative FAO calibration** (`preloop.gms:86`), not "no calibration". The FAO calibration (`preloop.gms:108-116`) and the AQUASTAT ir2rf calibration (`preloop.gms:123-150`) always run. To obtain uncalibrated LPJmL yields you would have to edit `preloop.gms` itself — a code change, not a config change.

---

### 🟠 M14-B11 — Major — `pm_yields_semi_calib` citation `declarations.gms:18` now points at a **different parameter**

- **Class:** 10 / 12 (citation drift to materially different content)
- **Trigger:** Major — "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different."
- **doc_line:** `module_14.md:752` (§7.1)
- **Claim in doc:** "**pm_yields_semi_calib(j,kve,w)** … **Citation:** `declarations.gms:18`"
- **Reality in code:** `declarations.gms:18` is **`im_growing_stock_ysf(t,j,ac)`** (inserted by `6b00f9dea`, shifting every later line by +1). `pm_yields_semi_calib(j,kve,w)` is at **`declarations.gms:19`**.
- **file_evidence:** `modules/14_yields/managementcalib_aug19/declarations.gms:18-19`
- **verify_cmd (with results):** `sed -n '17,19p' declarations.gms` → `17: im_growing_stock(...)`, `18: im_growing_stock_ysf(...)`, `19: pm_yields_semi_calib(j,kve,w)`
- **confirmed:** true
- **Proposed fix:** `module_14.md:752`: `**Citation:** \`declarations.gms:18\`` → `**Citation:** \`declarations.gms:19\``. Also enrich the "Purpose" line (`:750`), which currently says only "Baseline reference for other modules": its **sole consumer** is `modules/17_production/flexreg_apr16/presolve.gms:10` (`pm_prod_init(j,kcr) = sum(w, fm_croparea("y1995",j,w,kcr) * pm_yields_semi_calib(j,kcr,w))`).

---

### 🟠 M14-B12 — Major — Botched algebra: the λ = 1 "Behavior" line drops the exponent term

- **Class:** 4 (conceptual pseudo-code) / 12
- **Trigger:** Major — "agent fabricated an expanded equation …" (R16 anchor family); wrong algebraic reduction of the code's formula, presented as its behaviour.
- **doc_line:** `module_14.md:276` (§3.3 Step 3c "Behavior")
- **Claim in doc:**
  > "- **λ = 1:** Factor = 1 + [(FAO - LPJmL_reg) / LPJmL_cell] **× 1** = FAO/LPJmL_cell × (ratio), pure relative
  >  - **λ = 0:** Factor = 1 + [(FAO - LPJmL_reg) / LPJmL_cell] **× 1** = additive difference"
- **Reality in code:** `preloop.gms:108-112` — the ratio term is `(f14_yields / (i14_modeled_yields_hist + 1e-8)) ** i14_lambda_yields`, i.e. `(LPJmL_cell / LPJmL_reg)^λ`.
  - At **λ = 0** the term is `x^0 = 1` → Factor = `1 + (FAO − LPJmL_reg)/LPJmL_cell` → **additive** ✓ (doc's second line is right).
  - At **λ = 1** the term is `(LPJmL_cell / LPJmL_reg)`, **not 1** → Factor = `1 + (FAO − LPJmL_reg)/LPJmL_reg` = `FAO / LPJmL_reg` → calibrated yield = `LPJmL_cell × FAO/LPJmL_reg` → **pure relative**. The doc's first line is algebraically wrong (it prints the λ=0 substitution under the λ=1 heading, then a garbled RHS "FAO/LPJmL_cell × (ratio)").
- **file_evidence:** `modules/14_yields/managementcalib_aug19/preloop.gms:108-112`
- **verify_cmd (with results):** `sed -n '108,116p' preloop.gms` → exponent `** sum(cell(i,j),i14_lambda_yields(t,i,knbe14))`. Self-check: the doc's own §15.3 λ=1 example (12 tDM/ha) reproduces only under the *correct* λ=1 reduction, confirming the reading.
- **confirmed:** true
- **Proposed fix:** Replace `module_14.md:274-278` with:
  > **Behavior** (write `R = LPJmL_cell / LPJmL_reg`; the ratio term is `R^λ`):
  > - **λ = 1** → `R^1 = R`: Factor = `1 + (FAO − LPJmL_reg)/LPJmL_cell × R` = `1 + (FAO − LPJmL_reg)/LPJmL_reg` = **`FAO / LPJmL_reg`** → calibrated yield = `LPJmL_cell × FAO/LPJmL_reg` → **pure relative**.
  > - **λ = 0** → `R^0 = 1`: Factor = `1 + (FAO − LPJmL_reg)/LPJmL_cell` → calibrated yield = `LPJmL_cell + (FAO − LPJmL_reg)` → **pure additive**.
  > - **0 < λ < 1:** smooth blend (the additive offset is scaled by `R^λ`).

---

### 🟠 M14-B13 — Major — Upstream and downstream module lists are incomplete / mis-directed (Module 52 omitted as a consumer; Module 70 listed as a *dependent*)

- **Class:** 15 (wrong consumer set — R20 anchor family)
- **Trigger:** Major — wrong consumer/dependency sets. Downgraded from Critical (tie-breaker) because the M52 dependency **is** stated correctly elsewhere in the doc (§4 sync note, §6.5, §6.6, §7.1).
- **doc_line:** `module_14.md:817-828` (§8.2), `module_14.md:1402-1414` (§21.2)
- **Claim in doc:**
  > §8.2 "Critical Downstream Dependencies": Module 30, Module 31, Module 32, Module 17 & Module 11 — **Module 35 and Module 52 absent**.
  > §21.2 "Modules that Module 14 depends on": Module 13, Module 52, Module 45 — **Module 10, Module 30, Module 70 absent**.
  > §21.2 "Modules that depend on Module 14": 30, 31, 32, **35 ("Natural vegetation yields (implicitly through land competition)")**, 17 ("via modules 30/31/32"), **70 ("Feed availability from crop residues (via Module 18)")** — **Module 52 absent**.
- **Reality in code:**
  - **True downstream (direct readers of an M14-provided interface) = {17, 30, 31, 32, 35, 52}.**
    - `vm_yld` → M30 (`{simple,detail}_apr24/equations.gms:15`), M31 (`endo_jun13/equations.gms:18`)
    - `im_growing_stock` → M32 (`equations.gms:249`, `presolve.gms:181,185`), M35 (`equations.gms:147,156,165`)
    - `im_growing_stock_ysf` → M35 (`equations.gms:166`)
    - `pm_yields_semi_calib` → **M17** (`flexreg_apr16/presolve.gms:10`) — a **direct** link the doc never states
    - `sm_carbon_fraction`, `fm_aboveground_fraction`, `fm_ipcc_bef` (all declared in M14) → **M52** (`normal_dec17/preloop.gms:26,60,61,95,96`) — **omitted from every dependent-module list**
  - **M35's dependency is DIRECT and explicit**, not "implicitly through land competition": it reads `im_growing_stock` three times and `im_growing_stock_ysf` once, inside `q35_prod_secdforest` / `q35_prod_primforest` / `q35_prod_other`.
  - **M70 is UPSTREAM, not downstream**: M14 reads `pm_past_mngmnt_factor` from M70 (`equations.gms:38`); M70 reads **no** M14 interface. Listing it under "Modules that depend on Module 14" inverts the data-flow direction (MANDATE 21). Its only link back is transitive via M30/M18/M17.
  - **M11 is not a direct consumer** of any M14 interface (transitive only).
  - **True upstream = {10, 13, 30, 45, 52, 70}** (§8.1 lists only 13 + 52).
- **file_evidence:** `modules/52_carbon/normal_dec17/preloop.gms:26,60,61,95,96`; `modules/17_production/flexreg_apr16/presolve.gms:10`; `modules/35_natveg/pot_forest_may24/equations.gms:147,156,165,166`; `modules/70_livestock/fbask_jan16/declarations.gms:41`
- **verify_cmd (with results):** `rg -n 'sm_carbon_fraction' modules/ core/` → M52 `preloop.gms:60,95`; `rg -n 'fm_aboveground_fraction' modules/ core/` → M52 `preloop.gms:61,96`; `rg -n 'fm_ipcc_bef' modules/ core/` → M52 `preloop.gms:26`; `rg -n 'pm_yields_semi_calib' modules/` → M17 `presolve.gms:10` only; `rg -n 'vm_yld\(' + rg -n 'vm_yld\.' modules/` → M30, M31 only (no M11, no M70).
- **confirmed:** true
- **Proposed fix:**
  - §8.2 (`:817-828`): add
    > **Module 35 (Natural Vegetation):** natural-forest and other-land wood supply = harvested area × `im_growing_stock` / timestep (`q35_prod_secdforest`, `q35_prod_primforest`, `q35_prod_other`; `35_natveg/pot_forest_may24/equations.gms:147,156,165`), **plus** the `youngsecdf` term via `im_growing_stock_ysf` (`equations.gms:166`).
    > **Module 52 (Carbon):** reads three **M14-declared** interface parameters — `sm_carbon_fraction`, `fm_aboveground_fraction`, `fm_ipcc_bef` — in its growing-stock calibration (`52_carbon/normal_dec17/preloop.gms:26,60-61,95-96`). Renaming any of them in M14 breaks M52.
    > **Module 17 (Production):** reads `pm_yields_semi_calib` directly (`17_production/flexreg_apr16/presolve.gms:10`) to build `pm_prod_init`.
    Mark Module 11 explicitly as **transitive** (no direct M14 interface read).
  - §21.2 (`:1402-1414`): add Module 10, Module 30, Module 70 to "depends on"; add **Module 52** to "depend on Module 14"; correct the Module 35 rationale to the direct `im_growing_stock`/`im_growing_stock_ysf` reads; correct the Module 17 rationale to the direct `pm_yields_semi_calib` read; **move Module 70 out of "depend on Module 14"** (it is upstream) or mark it explicitly transitive-only.

---

### 🟡 M14-B14 — Minor — Header LOC count stale (569 → 586)

- **Class:** 6 (hardcoded counts drift)
- **doc_line:** `module_14.md:5` ("**Total Lines of Code:** 569") and `module_14.md:1608` ("557 lines of code analyzed")
- **Reality:** `wc -l modules/14_yields/managementcalib_aug19/*.gms` → **586 total**.
- **verify_cmd:** `wc -l /tmp/magpie_develop_ro/modules/14_yields/managementcalib_aug19/*.gms | tail -1` → `586 total`. Cross-check: `git show 6b00f9dea^:.../declarations.gms | wc -l` → 40 (now 41); `git show 6b00f9dea^:.../presolve.gms | wc -l` → 65 (now 81). 586 − 17 = **569** — i.e. the doc's figure was exactly right *before* the 2026-07-14 commit and was never updated.
- **confirmed:** true
- **Proposed fix:** `module_14.md:5` → `**Total Lines of Code:** 586`. `module_14.md:1608` → `...586 lines of code analyzed...`.

### 🟡 M14-B15 — Minor — `vm_yld` citation off by one (`declarations.gms:26` → `:27`)

- **Class:** 10. **doc_line:** `module_14.md:712`. **Reality:** `declarations.gms:26` = `positive variables`; `vm_yld(j,kve,w)` is at **`:27`** (shifted +1 by `6b00f9dea`).
- **verify_cmd:** `sed -n '26,27p' declarations.gms` → `26: positive variables` / `27:  vm_yld(j,kve,w) …`. **confirmed:** true.
- **Proposed fix:** `**Citation:** \`declarations.gms:26\`` → `**Citation:** \`declarations.gms:27\``

### 🟡 M14-B16 — Minor — Orphaned "Citation: `declarations.gms:17`" under the `im_growing_stock_ysf` block

- **Class:** 12. **doc_line:** `module_14.md:736`. **Reality:** `declarations.gms:17` is `im_growing_stock`; `im_growing_stock_ysf` is at `:18` — which `module_14.md:734` already states correctly two lines above. The stray line reads as the ysf citation.
- **verify_cmd:** `sed -n '17,18p' declarations.gms`. **confirmed:** true.
- **Proposed fix:** Delete `module_14.md:736` (`**Citation:** \`declarations.gms:17\``) — the `**Declared:** declarations.gms:18` line at `:734` already carries the citation. If a citation for `im_growing_stock` is wanted, move it up into that block (`:718-725`) as `**Citation:** \`declarations.gms:17\``.

### 🟡 M14-B17 — Minor — Current `p14_pyield_corr` code attributed to the wrong commit

- **Class:** 5 / 12. **doc_line:** `module_14.md:177` (§3.2 "🔄 Changed 2026-04-20 (commit `c7731e234`)") and `module_14.md:1617` (footer).
- **Reality:** The code the doc describes (`preloop.gms:18-24`) is from **`2fa7b8bea9` (florianh, 2026-04-28)**. `c7731e234` (2026-04-20, "Natural-origin tracking for secondary forest carbon density") implemented a **different, superseded** scheme: trend extrapolation through `sm_fix_SSP2` capped at ±10 % per 5-year step, adding **three** parameters `p14_corr_last`, `p14_corr_prev`, `p14_corr_trend` (declarations `+3`). So the doc's "**No new or renamed parameters**" is true of the *current* state but false as a statement about `c7731e234`.
- **verify_cmd:** `git blame -L 15,27 preloop.gms` → lines 18-24 = `2fa7b8bea9 (florianh 2026-04-28)`; `git show c7731e234 -- modules/14_yields/` → adds `p14_corr_last/prev/trend` + `loop(t$(... <= sm_fix_SSP2), ...)`. **confirmed:** true.
- **Proposed fix:** `module_14.md:177` → `> **🔄 Changed 2026-04-28 (commit \`2fa7b8bea9\`)**: … (An earlier attempt in \`c7731e234\`, 2026-04-20, extrapolated the last t_past trend through \`sm_fix_SSP2\` using three helper parameters \`p14_corr_last\`/\`p14_corr_prev\`/\`p14_corr_trend\`; that version was **superseded** by \`2fa7b8bea9\`, which removed those parameters. Current develop has **no** p14_corr_* parameters.)` Apply the same correction to the footer `module_14.md:1617`.

### 🟡 M14-B18 — Minor — `@Heinke.2013` cited at `preloop.gms:47`; it is at `:54` (and `:106`)

- **Class:** 10. **doc_line:** `module_14.md:251` (§3.3 Step 3b) and `module_14.md:1248` (§17).
- **Reality:** `rg -n 'Heinke' preloop.gms` → **`54:`** `…similar to an additive term (@Heinke.2013).` and **`106:`** `…following the idea of eq. (9) in [@Heinke.2013]:`. Line 47 is `*' To address this issue, the factor \`i14_lambda_yields\` determines the degree`.
- **verify_cmd:** `rg -n 'Heinke' /tmp/magpie_develop_ro/modules/14_yields/managementcalib_aug19/preloop.gms` → lines 54, 106 only. **confirmed:** true.
- **Proposed fix:** `module_14.md:251` → `` `preloop.gms:82-102`, mathematical foundation cited as `@Heinke.2013` in `preloop.gms:54` ``. `module_14.md:1248` → `…foundation for lambda-based calibration (\`preloop.gms:54\`; "eq. (9)" is invoked at \`preloop.gms:106\`)`.

### 🟡 M14-B19 — Minor — `i14_fao_yields_hist` "Computed in: `preloop.gms:88`" → actual `:95`

- **Class:** 10. **doc_line:** `module_14.md:886` (§9.2).
- **Reality:** `preloop.gms:95` = `i14_fao_yields_hist(t,i,knbe14) = f14_fao_yields_hist(t,i,knbe14);`. `preloop.gms:88` = `Elseif (s14_limit_calib =1 ),` — which would mislead a reader into thinking the FAO copy is conditional on `s14_limit_calib` (it is not; it runs unconditionally inside the `y1995` branch).
- **verify_cmd:** `sed -n '88p;95p' preloop.gms` → `88: Elseif (s14_limit_calib =1 ),` / `95: i14_fao_yields_hist(t,i,knbe14) = f14_fao_yields_hist(t,i,knbe14);`. **confirmed:** true. *(Tie-breaker applied: Major trigger "citation drift to different content" vs Minor "off-by-few"; the doc's prose ("copied from input file") is correct and the target sits inside the block the doc itself displays → Minor.)*
- **Proposed fix:** `module_14.md:886` → `**Computed in:** \`preloop.gms:95\` (copied from the input file, unconditionally, inside the \`y1995\` branch; carried forward via \`preloop.gms:99\`)`

### 🟡 M14-B20 — Minor — `@FAOSTAT` cited at `module.gms:16,21`; it is at `module.gms:17`

- **Class:** 10. **doc_line:** `module_14.md:1254` (§17).
- **Reality:** `module.gms:17` = `*' [@FAOSTAT]. For the simulation of the temporal development of agricultural`. `module.gms:16` is the preceding prose line; `module.gms:21` carries **`@fao_aquastat_2016`**, not `@FAOSTAT`.
- **verify_cmd:** `cat -n modules/14_yields/module.gms | sed -n '14,21p'`. **confirmed:** true. (`@bondeau_lpjml_2007` at `module.gms:14` ✓ and `@fao_aquastat_2016` at `module.gms:21` ✓ are both correct.)
- **Proposed fix:** `module_14.md:1254` → `**@FAOSTAT:** FAO Statistical Database — regional yield targets (\`module.gms:17\`; also \`realization.gms:11,17\`)`

### 🟡 M14-B21 — Minor — `@limitations` block cited as `realization.gms:23-26` / `:23-24`; it is `:24-27`

- **Class:** 10. **doc_line:** `module_14.md:31` (§1.3) and `module_14.md:976` (§11.5).
- **Reality:** `realization.gms:24` = `*' @limitations The exogenous implementation of pasture intensification cannot` … `:27` = `*' in  the crop sector towards improvements in pasture management is very uncertain.` Line 23 is blank.
- **verify_cmd:** `sed -n '23,27p' realization.gms`. **confirmed:** true.
- **Proposed fix:** `module_14.md:31` → `(\`realization.gms:24-27\`)`; `module_14.md:976` → `(\`realization.gms:24-25\`)`.

### 🟡 M14-B22 — Minor — "18 crops" → `kcr` has **19** members

- **Class:** 6. **doc_line:** `module_14.md:1501` (§21.4: "Cell-level yields with 200+ cells × **18 crops** × 2 irrigation types").
- **Reality:** `kcr(kve)` = `tece, maiz, trce, rice_pro, soybean, rapeseed, groundnut, sunflower, oilpalm, puls_pro, potato, cassav_sp, sugr_cane, sugr_beet, others, foddr, cottn_pro, begr, betr` → **19**. (`kve` = 20 incl. pasture; `knbe14` = 17, excluding `begr`/`betr`.)
- **verify_cmd:** `sed -n '23,26p' modules/14_yields/managementcalib_aug19/sets.gms` + member count → **19**. **confirmed:** true.
- **Proposed fix:** `module_14.md:1501` → `**Spatial complexity**: cell-level yields over \`kcr\` (**19** cropping activities, \`sets.gms:23-26\`) + pasture × 2 water supply types; \`vm_yld\` is dimensioned \`(j,kve,w)\` with \`kve\` = 20 members.`

### 🟡 M14-B23 — Minor — §15.3 worked example: "≈ 8 tDM/ha" should be ≈ 10

- **Class:** 12. **doc_line:** `module_14.md:1198`.
- **Claim:** "With λ=0.58: Calibrated yield ≈ **8** tDM/ha (reasonable **1.3x** FAO)"
- **Reality:** With the code's formula (`preloop.gms:108-115`), `yield(t) = LPJmL_cell(t) + (FAO − LPJmL_reg) × (LPJmL_cell(t)/LPJmL_reg)^λ`. For the doc's own numbers (LPJmL_reg = 2, FAO = 6, LPJmL_cell(2050) = 4, λ = √(2/6) = 0.577): `4 + 4 × 2^0.577 = 4 + 4(1.492) = **9.97 ≈ 10**` (≈ **1.7×** FAO). The doc's λ=1 line ("4 × 3 = 12") *does* reproduce (`4 + 4 × 2^1 = 12`), which confirms the formula reading.
- **verify_cmd:** algebraic derivation from `preloop.gms:108-115` (λ=1 case cross-checks against the doc's own 12). **confirmed:** true.
- **Proposed fix:** `module_14.md:1198` → `- With λ=0.58: Calibrated yield ≈ **10** tDM/ha (**1.7×** FAO — still high, but the additive blend has removed a third of the pure-relative overshoot)`

### 🟡 M14-B24 — Minor — Points the reader at Module 13's **non-default** realization

- **Class:** 8. **doc_line:** `module_14.md:761` (§7.2: "cluster-level since the f_btc2 rename — verify at `../modules/13_tc/exo/declarations.gms`").
- **Reality:** Module 13's default realization is **`endo_jan22`** (`config/default.cfg:293`), not `exo`. `vm_tau(j,tautype)` / `pcm_tau(j,tautype)` are at `13_tc/endo_jan22/declarations.gms:13` / `:27`. (Both realizations agree on the dimensionality, so no factual harm — but the pointer lands in a non-default file.)
- **verify_cmd:** `grep -n 'cfg\$gms\$tc' config/default.cfg` → `293:cfg$gms$tc <- "endo_jan22"`; `rg -n 'vm_tau|pcm_tau' modules/13_tc/*/declarations.gms`. **confirmed:** true.
- **Proposed fix:** `module_14.md:761` → `…cluster-level since the f_btc2 rename — \`modules/13_tc/endo_jan22/declarations.gms:13,27\` (**default** realization; \`exo\` agrees)`

### 🟡 M14-B25 — Minor — Deprecated "BCE" name still used unmarked

- **Class:** 5 (stale reference after rename). **doc_line:** `module_14.md:1010` (§12.4: "`CarbonDensity / 0.5 × AbovegroundFrac / BCE`") and `module_14.md:792` (§7.2: "Climate classification for **BCE** factors").
- **Reality:** The parameter is `fm_ipcc_bef` (**B**iomass **E**xpansion **F**actor), `input.gms:66`; the doc itself documents the `f14_ipcc_bce` → `fm_ipcc_bef` rename at `module_14.md:409`. Per MANDATE 19, deprecated names must be italicised/marked.
- **verify_cmd:** `rg -n 'bce|BCE' /tmp/magpie_develop_ro/modules/14_yields/` → **no match** (the name no longer exists in code). **confirmed:** true.
- **Proposed fix:** `module_14.md:1010` → `…\`CarbonDensity / sm_carbon_fraction × fm_aboveground_fraction / fm_ipcc_bef\`…`; `module_14.md:792` → `Climate classification weighting \`fm_ipcc_bef\` (formerly *BCE*)`.

### 🟢 M14-B26 — Informational — Quoted scalar text differs from code

- **doc_line:** `module_14.md:605` (§5.5). Doc quotes `…into pasture yield increases  (1)     / 0.25 /`; `input.gms:20` actually reads `…into pasture yieldincreases  (1)     / 0.25 /` (missing space — a typo **in the code**). Value and line are correct.
- **verify_cmd:** `sed -n '20p' input.gms`. **confirmed:** true. **Proposed fix:** reproduce the code verbatim (`yieldincreases`) or drop the verbatim-quote framing; optionally file an upstream typo fix.

---

## 4. Borderline items NOT filed as bugs

- §3.3 header "**File:** `preloop.gms:26-109`" and §1.2 "`preloop.gms:26-145`" — imprecise *section* ranges (they clip into Stage 2's code at :27 and truncate Stage 3 at :109/:116). All three sub-step citations inside them (67-73, 82-102, 108-116) are exact, so no reader is misled to wrong content. Recommend tightening to `preloop.gms:30-150` anyway.
- §6.2 "Used in Stage 2 calibration (`preloop.gms:18`)" — line 18 is the *comment* introducing the pasture correction; the code use is `:22`. Same-topic, same block → not filed.
- §12.5 "(preloop.gms:8-190)" — the degradation block ends at :195. Cosmetic.
- §4 sync note "youngsecdf *carbon* has **always** been read from the uncalibrated curve" — "always" is an overstatement (the uncalib parameter dates from 2026-03-21), but the substantive claim (`35_natveg/pot_forest_may24/presolve.gms:242`) is **correct**.
- §7.1 "Consumers divide by `m_timestep_length_forestry`" — true for the four production equations; `i32_growing_stock_at_harvest` (`32_forestry/.../presolve.gms:181`) uses the stock directly. The doc's phrasing ("to derive per-year production") is defensible.

---

## 5. Deferred (NOT edited — not verifiable against GAMS code)

1. `f14_pyld_hist` "covers y1965–y2020" (`module_14.md:171,177`) — the `.csv` is gitignored (only `modules/14_yields/input/files` is tracked). The doc faithfully repeats the **code's own comment** (`preloop.gms:19`), so it is not a doc error; the underlying data range could not be independently confirmed. Verify with the preproc-agent.
2. §6.8 "Example: Oilpalm ≈0.4, maize ≈0, rapeseed ≈0.3" — `f14_kcr_pollinator_dependence.csv` is gitignored; values not verifiable here.
3. §4 sync note: "the FRA calibration raises the growth-rate `k` in some regions and lowers it in others, so in the latter the fix *increases* youngsecdf wood supply" — depends on the FRA-2025 target data and M52's bisection outcome; not derivable from GAMS source alone.
4. §8.3 "[`fm_croparea`] patterns were **likely** generated by previous MAgPIE runs" — `fm_croparea` provenance is an R-preprocessing question (route to `PREPROC_AGENT.md`). Note it sits oddly next to §3.5, which correctly identifies `f14_yld_calib` (not `fm_croparea`) as the calibration-run product.
5. §21.3 "SOM effects gradual: 15% annual convergence (Module 59)" — the 15% figure is a Module-59 claim I did not verify; it is moot here because the M14↔M59 feedback it "resolves" does not exist (M14-B1), and it is removed by that fix.
6. §13.4 "Young plantations (ac0-ac2): 50-200 tDM/ha …" plausibility bands — depend on input carbon densities; not code-checkable.
7. §21.2 "Centrality Rank: High" / "Total Connections: 5+" — sourced from `Module_Dependencies.md`, not from GAMS. (Note the true direct-interface degree is **12** modules-edges: upstream {10, 13, 30, 45, 52, 70}, downstream {17, 30, 31, 32, 35, 52}.)

---

## 6. Score

`raw_severity_weighted = 4(2) + 2(11) + 1(12) + 0(1) = 8 + 22 + 12 = 42` → **score_0_10 = max(0, 10 − 42) = 0/10**

Per the rubric's per-question formula this floors at 0, which over-reads: the doc's *core technical content* (equations, calibration stages, presolve growing stock, defaults, input files, the entire 2026-07-14 ysf section) is **exemplary** — every equation, every scalar default, every one of the nine input-file citations, and every preloop/presolve line range checks out. The failures are concentrated in (a) the cross-module interface-ownership prose (§7.2, §16.5), (b) the modification-safety and debugging advice (§14, §21.4), and (c) the fabricated §21.3 cycle — sections the 2026-07-14 sync did not touch and which appear never to have been code-verified.

**Verdict: SIGNIFICANT ERRORS** (verdict-to-score band 5-6 on the *content* the reader is most likely to act on; the raw weighted score is dominated by the long Minor tail).
