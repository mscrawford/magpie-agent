# Adversarial Doc Audit — core_docs/Data_Flow.md

**Auditor**: Opus (round30 doc-audit)
**Date**: 2026-05-29
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (develop) + `config/default.cfg`; magpie4 names via SHA-pinned clone `.cache/sources/magpie4/`.
**Target**: `core_docs/Data_Flow.md` (468 lines)

---

## Scope note

Data_Flow.md is largely a pipeline-architecture narrative with many illustrative pseudo-code blocks (prefixed with `#` comments, `×` for multiplication). Per the rubric, pure prose/advice is skipped; I enumerated and checked the load-bearing, code-verifiable claims: interface variable/parameter declarations, file:line citations, multi-module consumer/dependency SETS, realization names + defaults, set/region lists, the model statement, solver-option defaults, and the magpie4 function list.

Input-data files (`.cs3/.cs4/.mz/.csv`) are NOT in the git worktree (delivered via `input.tgz`); their absence on disk is NOT a doc bug. I verified instead that the cited filenames are referenced by `$include` in the realization `.gms` files and that the cited realization directory paths are real.

---

## Verified-correct claims (high-value)

| Claim | Doc line | Evidence (develop) | Verdict |
|---|---|---|---|
| `model magpie / all - m15_food_demand /;` | 191 | `main.gms:279` exact match | ✓ |
| `option iterlim = 1000000;` / `option reslim = 1000000;` | 192-193 | `main.gms:281-282` | ✓ |
| `vm_land(j,land)` mio. ha | 204 | `modules/10_land/landmatrix_dec18/declarations.gms` (vm_land … "Land area … (mio. ha)") | ✓ |
| `vm_area(j,kcr,w)` mio. ha | 205 | `modules/30_croparea/{detail,simple}_apr24/declarations.gms` | ✓ |
| `vm_prod(j,k)` mio. tDM | 206 | `modules/17_production/flexreg_apr16/declarations.gms` (mio. tDM per yr) | ✓ |
| `vm_yld(j,kve,w)` tDM/ha/yr | 207 | `modules/14_yields/managementcalib_aug19/declarations.gms` | ✓ |
| `vm_carbon_stock(j,land,c_pools,stockType)` mio. tC | 208 | `modules/56_ghg_policy/price_aug22/declarations.gms` (matches G2 anchor: declared in M56) | ✓ |
| `vm_tau(j,tautype)` unit 1 | 209 | `modules/13_tc/{endo_jan22,exo}/declarations.gms` ("… tau … (1)") | ✓ |
| `v21_trade(i_ex,i_im,k_trade)` mio. tDM | 210 | `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms` | ✓ |
| `vm_watdem(wat_dem,j)` mio. m³ | 211 | `modules/42_water_demand/{agr_sector,all_sectors}_aug13/declarations.gms` | ✓ |
| `q14_yield_crop` equation body | 216-221 | `modules/14_yields/managementcalib_aug19/equations.gms:14-16` verbatim (set-based `sum`, not expanded) | ✓ |
| `oq52_emis_co2_actual(t,i,emis_oneoff,<attr>)` postsolve | 227-230 | `modules/52_carbon/normal_dec17/postsolve.gms:9-12` (attr order cosmetically differs; structure correct) | ✓ |
| `pcm_land(j,land)` | 287 | `modules/10_land/landmatrix_dec18/declarations.gms:11` | ✓ |
| `pm_land_start(j,land)` | 288 | `…/declarations.gms:9` | ✓ |
| `vm_lu_transitions(j,land_from,land_to)` | 289 | `…/declarations.gms:23` | ✓ |
| `fm_carbon_density(t_all,j,land,c_pools)` From LPJmL | 292 | `modules/52_carbon/normal_dec17/input.gms:16` (`table fm_carbon_density(t_all,j,land,c_pools)`) | ✓ |
| `i14_yields_calib(t,j,kve,w)` | 297 | `modules/14_yields/managementcalib_aug19/declarations.gms:9` | ✓ |
| Regions `i`: CAZ,CHA,EUR,IND,JPN,LAM,MEA,NEU,OAS,REF,SSA,USA (12) | 253 | `core/sets.gms:18` exact | ✓ |
| Super-regions `h` = same set | 254-255 | `core/sets.gms:21` identical list | ✓ |
| 200 simulation clusters | 137,245 | `config/default.cfg:26` cellular input `…_c200_…`; `h12` confirms 12 regions | ✓ |
| Age-class set extends to `ac300, acx` (referenced generically, not truncated) | 277-279 | `core/sets.gms:269-275`; `pc35_secdforest(j,ac-s35_shift)` matches `presolve.gms:94` | ✓ |
| `s35_shift = m_timestep_length_forestry/5` (usually 1) | 277 | `modules/35_natveg/pot_forest_may24/presolve.gms:85-86` | ✓ |
| Loop: `while(sm_intersolve = 0, solve … intersolve)` + presolve_ini/presolve/postsolve | 143-163 | `core/calculations.gms:52,54,57,59,76,81,87`; `sm_intersolve` real (`core/declarations.gms:9`, default 0) | ✓ |
| Phase 3A: `vm_land.lo(j,"primforest") = (1-s35_natveg_harvest_shr)*pcm_land(...)` | 171 | `modules/35_natveg/pot_forest_may24/presolve.gms:159` | ✓ |
| Default realization `managementcalib_aug19` (yields) | 34 path | `config/default.cfg` `cfg$gms$yields <- "managementcalib_aug19"` | ✓ |
| Default realization `fbask_jan16` (livestock), path real | 37 | `config/default.cfg` `cfg$gms$livestock <- "fbask_jan16"`; file referenced in `fbask_jan16/input.gms` | ✓ |
| Default realization `landmatrix_dec18` (land) dir exists | 41 | `ls modules/10_land/` | ✓ |
| Yield input-loading example (table f14_yields, nocc filter, m_fillmissingyears, calib formula) | 89-119 | matches `modules/14_yields/managementcalib_aug19/input.gms:32-44` + `preloop.gms:108-115` (illustrative, faithful) | ✓ |
| Cited input filenames referenced via `$include` (f53_EFch4Rice.cs4, f70_hist_prod_livst.cs3, etc.) | 44-54 | e.g. `modules/53_methane/ipcc2006_aug22/input.gms:19` | ✓ |
| magpie4 `reportLandUse`, `reportEmissions`, `reportProduction` exist | 334-336 | `.cache/sources/magpie4/NAMESPACE:198`; files present | ✓ |

---

## BUGS

### DF-1 — Carbon System consumer set wrong (phantom M56 + omitted M14) — CRITICAL

- **Severity**: Critical
- **Trigger**: §1.5 latent-doc-bug mandate / R20 anchor — wrong consumer/populator set (a user refactoring the parameter would miss a real consumer and waste effort on a phantom). Bug class 15 (latent doc error) + 13 (interface-consumer grep, MANDATE 13).
- **Doc line**: Data_Flow.md:294
- **Claim in doc**: `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` — "Used by: modules 35, 32, 52, 56"
- **Reality in code** (base parameter `pm_carbon_density_secdforest_ac`, distinguished from the `_uncalib` sibling):
  - **M52** declares it (`declarations.gms:9`) and populates it (`preloop.gms:71`) — it is the OWNER/POPULATOR, not a "user".
  - **M35** reads it — consumer ✓ (`pot_forest_may24/presolve.gms:248,250,251`).
  - **M14** reads it — consumer, but **OMITTED from the doc list** (`managementcalib_aug19/presolve.gms:44`: `pm_carbon_density_secdforest_ac(t,j,ac,"vegc")`).
  - **M32** references ONLY `pm_carbon_density_secdforest_ac_uncalib` (`dynamic_may24/presolve.gms:59,68`), NOT the named base parameter — listing M32 as a consumer of the base param is wrong (it consumes the uncalibrated sibling).
  - **M56** does NOT reference `pm_carbon_density_secdforest_ac` at all — **PHANTOM** (confirmed twice + positive control).
- **File evidence**: `modules/52_carbon/normal_dec17/declarations.gms:9`, `preloop.gms:71`; `modules/14_yields/managementcalib_aug19/presolve.gms:44`; `modules/35_natveg/pot_forest_may24/presolve.gms:248-251`; `modules/32_forestry/dynamic_may24/presolve.gms:59,68` (uncalib only); M56 absent.
- **verify_cmd / results**:
  - `grep -rln "pm_carbon_density_secdforest_ac" modules/ --include=*.gms` → files in 14, 29, 32, 35, 52 only (NOT 56).
  - `grep -rn "pm_carbon_density_secdforest_ac" modules/32_forestry/ --include=*.gms | grep -v _uncalib` → EMPTY (M32 base-param absent, confirmed; also confirmed via `rg -n 'pm_carbon_density_secdforest_ac[^_]' modules/32_forestry/` → no match).
  - `rg -ln "pm_carbon_density_secdforest_ac" modules/56_ghg_policy/` → NO MATCH (method 2). Positive control `rg -ln "vm_carbon_stock" modules/56_ghg_policy/` → 7 files (search works in that dir).
  - `grep -n "pm_carbon_density_secdforest_ac" modules/14_yields/managementcalib_aug19/presolve.gms` → `44: pm_carbon_density_secdforest_ac(t,j,ac,"vegc")`.
- **Anchor reference**: R20 (`pm_carbon_density_*_ac` consumer omission → Critical) and MANDATE 13 / MANDATE 17 (base-vs-sibling, direct-vs-transitive).
- **confirmed**: true
- **Proposed fix**: Replace line 294 with:
  `- Populated by: Module 52 (owner; declared in normal_dec17/declarations.gms:9, set in preloop.gms:71). Read by: modules 14 (presolve.gms:44) and 35 (presolve.gms:248-251). (Modules 29, 32, 35 instead read the uncalibrated sibling pm_carbon_density_secdforest_ac_uncalib.)`

### DF-2 — Invented magpie4 function names (reportPrices / reportWater / reportBiodiversity) — MAJOR

- **Severity**: Major
- **Trigger**: Fabricated name in a list (§1 Major). Note §1 Critical "invented variable name" is framed for GAMS vm_/pm_; these are R functions in an illustrative list with correct concept annotations and a user gets an immediate call error (not silent wrong action), so tie-breaker pulls to Major. G4 anchor calibration intent (magpie4 `report*` name fidelity).
- **Doc line**: Data_Flow.md:337-339
- **Claim in doc**: lists `reportPrices()  # Shadow prices`, `reportWater()  # Water stress`, `reportBiodiversity()  # BII indicators` among "Key Functions".
- **Reality in code**: none of these three are exported by magpie4. Actual exported names:
  - prices → `reportPriceAgriculture`, `reportPriceFoodIndex`, `reportPriceLand`, `reportPriceWater`, … (no generic `reportPrices`).
  - water → `reportWaterUsage`, `reportWaterAvailability`, `reportWaterIndicators` (no generic `reportWater`).
  - biodiversity → `reportBII` (no `reportBiodiversity`).
- **File evidence**: `.cache/sources/magpie4/NAMESPACE` — `export(reportBII)` @151; `export(reportPriceAgriculture…)` @219-227; `export(reportWaterAvailability/Indicators/Usage)` @259-261. No `export(reportPrices|reportWater|reportBiodiversity)`.
- **verify_cmd / results**:
  - `grep -cE "export\((reportPrices|reportWater|reportBiodiversity)\)" NAMESPACE` → `0`.
  - Positive control `grep -n reportLandUse NAMESPACE` → `198:export(reportLandUse)` (search works).
  - `for f in reportPrices reportWater reportBiodiversity; do [ -f R/$f.R ]` → all MISSING; `grep -rn reportBiodiversity R/` → empty; `grep "reportWater <-" R/` (excluding Usage/Avail) → empty.
- **confirmed**: true
- **Proposed fix**: Replace the three lines with real exported functions, e.g.:
  ```
  reportPriceAgriculture()  # Agricultural producer prices (also reportPriceFoodIndex(), reportPriceLand())
  reportWaterUsage()        # Water use by sector (also reportWaterAvailability(), reportWaterIndicators())
  reportBII()               # Biodiversity Intactness Index
  ```

### DF-3 — Non-existent set element `"fires"` in disturbance pseudo-code — MINOR

- **Severity**: Minor
- **Trigger**: §1 Minor (wrong detail a careful reader notices). MANDATE 12 (exact set-member labels). Tie-breaker pulls down from Major because the block is explicitly illustrative (`#` comments, `×` operator, omits `sum(cell(i,j),…)` and `m_timestep_length_forestry`).
- **Doc line**: Data_Flow.md:177-179
- **Claim in doc**: `p35_disturbance_loss_secdf(t,j,ac) = pc35_secdforest(j,ac) × f35_forest_lost_share(i,"fires")`
- **Reality in code**: the disturbance loss uses the element `"shifting_agriculture"` (and there is NO element `"fires"`). The `driver_source` set is `/ overall, deforestation, shifting_agriculture, forestry, wildfire, urbanization /`; the fire-related element is `wildfire`.
- **File evidence**: `modules/35_natveg/pot_forest_may24/presolve.gms:14` (`… f35_forest_lost_share(i,"shifting_agriculture") * m_timestep_length_forestry`); set at `modules/35_natveg/pot_forest_may24/sets.gms:10-12`.
- **verify_cmd / results**:
  - `grep -rn '"fires"' modules/35_natveg/` → no match.
  - `Read sets.gms:8-16` → `driver_source / overall, deforestation, shifting_agriculture, forestry, wildfire, urbanization /`.
  - `grep -n "f35_forest_lost_share" .../presolve.gms` → uses `"shifting_agriculture"` (lines 14,20,25) and `combined_loss` (lines 25/26), never `"fires"`.
- **confirmed**: true
- **Proposed fix**: Change `f35_forest_lost_share(i,"fires")` to `f35_forest_lost_share(i,"shifting_agriculture")` (the element actually applied in presolve), or use `"wildfire"` if a fire illustration is intended — but NOT `"fires"`, which is not a set member. (Note: CLAUDE.md flags "fire" labeling as a known sensitivity — the disturbance is driven by shifting_agriculture/combined_loss in code, not by a generic "fires" rate.)

### DF-4 — `pm_carbon_density_secdforest_ac` first dimension is `t_all`, not `t` — MINOR

- **Severity**: Minor
- **Trigger**: §1 Minor (off-by-one detail in a dimension list; doesn't mislead into a wrong action). MANDATE 7.
- **Doc line**: Data_Flow.md:293
- **Claim in doc**: `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)`
- **Reality in code**: declared over `t_all` (full period set), not `t`.
- **File evidence**: `modules/52_carbon/normal_dec17/declarations.gms:9` — `pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)`.
- **verify_cmd / results**: `grep -n "pm_carbon_density_secdforest_ac" modules/52_carbon/normal_dec17/declarations.gms` → line 9 shows `(t_all,j,ac,ag_pools)`.
- **confirmed**: true
- **Proposed fix**: Change `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` to `pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)`.

---

## Deferred (not edited — could not code-verify or out of scope)

- File-format COUNTS in §1.1 (`.cs3` 20, `.cs4` 10, `.mz` 26, `.csv` 76, `.rds` 22) and "~72 MB / ~172 files": depend on the runtime `input.tgz`, which is not in the worktree. Not verifiable against committed code; not flagged.
- "67,420 actual land cells" and "259,200 theoretical cells": 360×720=259,200 is correct arithmetic; 67,420 is a standard MAgPIE figure tied to a specific cellular input version, not checkable in the worktree. Not flagged.
- Prefix-convention table (§2.1) including `x_` = "eXtremely important outputs", `o_` outputs: no canonical machine-checkable source in the GAMS tree (README has partial naming guidance). Concept consistent with MAgPIE usage; not code-verified, not flagged.
- "Flow: Module 14 → 30 → 17" (line 299), "Module 14 → 30 → 17" production chain, and the magpie4 output-format bullets (IAMC/NetCDF/CSV/ggplot2): high-level pipeline description, not a single-line code claim; not flagged.
- Run-statistics table (§8.2: ~100k vars, ~150k eqs, solve times, output sizes): runtime/empirical, version- and config-dependent; not code-verifiable. Not flagged.
- Validation-metrics block (§9.1: "R² > 0.8", "±10%"): claims about preprocessing/validation targets, not GAMS code; route to preproc layer. Not flagged.
- magpie4 generic `report*` set in §6.2 beyond the three flagged: `reportLandUse/Emissions/Production` confirmed present; the rest of the file's R-side claims (formats) deferred as above.
- Cosmetic: line 184 illustrative snippet indexes `pm_land_conservation(t,j,land,"protect")` for a `land_natveg` row (code uses `land_natveg` consistently); illustrative, not flagged. Postsolve attr ordering (227-230) differs cosmetically from code; not flagged.

---

## Summary

4 confirmed bugs. The load-bearing one is **DF-1 (Critical)**: the Carbon System dependency line (294) lists a phantom consumer (M56, zero references — confirmed twice + positive control) and omits a real direct consumer (M14, presolve.gms:44), while attributing the base parameter to M32 which actually reads only the `_uncalib` sibling — the exact R20 consumer-set failure mode (a refactor would miss M14 and chase M56). **DF-2 (Major)**: three invented magpie4 function names (`reportPrices`/`reportWater`/`reportBiodiversity`) absent from the pinned-clone NAMESPACE. **DF-3/DF-4 (Minor)**: a non-existent set element `"fires"` in an illustrative disturbance snippet (code uses `shifting_agriculture`; the fire element is `wildfire`) and a `t` vs `t_all` dimension slip. All structural interface-variable declarations, the model statement, solver defaults, region/cluster lists, the q14_yield_crop equation, and the realization defaults checked out clean.
