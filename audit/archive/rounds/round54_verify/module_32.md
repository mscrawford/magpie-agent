# R54 Adversarial Verification — module_32.md (Forestry)

**Verifier**: adversarial (Opus, max capability)
**Target doc**: `<magpie-agent>/modules/module_32.md` (1,420 lines)
**Ground truth**: `/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop worktree; working tree NEVER consulted)
**Date**: 2026-07-14

**Headline**: **20 / 20 bugs UPHELD.** Every `file:line` citation in every bug reproduced exactly. Two side-errors found in auditor *rationale* text (neither propagates into a proposed doc edit) — recorded below as **CAVEAT-A** and **CAVEAT-B**.

Module 32 has exactly **one** realization (`dynamic_may24`) — so the R33 cross-realization confabulation class is structurally impossible here. That removed the highest-risk failure mode, which is consistent with (but does not by itself explain) the clean result. The consumer/producer sets were the real risk, and those I re-derived from scratch rather than checking the auditor's work.

---

## Method (what makes this more than a rubber stamp)

1. **Step A (mechanical, every bug)**: `test -f` → `wc -l` → read the exact cited line and confirm it contains the claimed token. No exceptions, including for `other`-class bugs.
2. **Step C (independent re-derivation, not verification-of-the-auditor)**: I extracted M32's **complete** interface-token set with
   `rg -o -I '\b(vm_|pm_|pcm_|im_|fm_|sm_)\w+' *.gms | sort -u` (30 tokens), then mapped **each** to its declaring module via `declarations.gms` / `input.gms`. The provides/receives sets below are derived from that sweep, *then* compared to the auditor — not read off the auditor's list.
3. **Negative claims** (the highest-risk class) got: repo-wide `rg` + an **independent second method** (`find … -exec grep`) + a **positive control** proving the search works in that directory.
4. **Both forms** (`NAME(` and `NAME.`) grepped for every variable, per the R33 `vm_area.l` near-miss.

### Live methodology note (worth propagating)
`rg -oh` **silently printed ripgrep's help text** instead of searching — `-h` is `--help`; the no-filename flag is `-I`. This is the same family as the recorded `rg -r` = `--replace` trap. Had I not read the output, I'd have concluded "no interface tokens found." Corrected invocation: `rg -o -I --no-line-number`.

---

## Positive controls run (proof the searches worked)

| Control | Result |
|---|---|
| `vm_landdiff_forestry` in `modules/10_land/` | **FOUND** at `landmatrix_dec18/equations.gms:54` → rg *does* reach 10_land |
| `find /…/10_land -exec grep 'land.*_forestry'` (2nd method) | **EXIT 1** → M10 genuinely references none of the three |
| `tDM` in M32 `declarations.gms` | 13 hits → the "no m³ in M32" search was live |
| `ac_est` in `core/sets.gms` | 2 hits → the "`ac_rotation` does not exist" search was live |

---

## Default realizations (all auditor citations confirmed)

`config/default.cfg`: `:232` land=`landmatrix_dec18` · `:240` interest_rate=`select_apr20` · `:354` yields=`managementcalib_aug19` · `:992` forestry=`dynamic_may24` · `:1153` natveg=`pot_forest_may24` · `:1435` biodiversity=`bii_target` · `:1574` carbon=`normal_dec17` · `:1631` ghg_policy=`price_aug22` · **`:1871` peatland=`v2`** · `:2223` timber=`default`.

The peatland default (`v2`) is load-bearing for C1/C2/C3/M1 — and it is confirmed. (The `off` realization's `not_used.txt:4,5,10,11` independently corroborates that M58 is the *registered* recipient of all four M32 interfaces.)

---

## Independently re-derived interface sets (the core result)

### M32 PROVIDES → **7 modules** (doc says 5)

| Consumer | Interface | Consumption site (verified) |
|---|---|---|
| **10_land** | `vm_land(j,"forestry")` slice; `vm_landdiff_forestry` | `10_land/landmatrix_dec18/equations.gms:54` |
| **11_costs** | `vm_cost_fore` | `11_costs/default/equations.gms:33` |
| **44_biodiversity** | `vm_bv` slices `aff_co2p`/`aff_ndc`/`plant` | `44_biodiversity/bii_target/equations.gms:16` |
| **52_carbon** | `pm_land_plantation`; `vm_carbon_stock` forestry slice | `52_carbon/normal_dec17/preloop.gms:88,90,94`; `equations.gms:19` |
| **56_ghg_policy** | `vm_cdr_aff`; `vm_carbon_stock` forestry slice | `56_ghg_policy/price_aug22/equations.gms:77`; `:22` |
| **58_peatland** | `vm_land_forestry`, `vm_landexpansion_forestry`, `vm_landreduction_forestry`, `pcm_land_forestry` | `58_peatland/v2/equations.gms:23,28,31`; `presolve.gms:11` |
| **73_timber** | `vm_prod_forestry` | `73_timber/default/equations.gms:46,55,78` |

M52 and M56 read `vm_carbon_stock` **independently and in parallel** (M52 `equations.gms:19`, M56 `equations.gms:22`) — this is *not* a serial hand-off, exactly as MANDATE 21 / R51 requires. M32 owns only the `"forestry"` slice (`equations.gms:108`, LHS of `q32_carbon`).

### M32 RECEIVES ← **11 modules** (doc's table lists 10; doc line 683 says 6)

10 (`pcm_land`, `pm_land_start`, `fm_luh2_side_layers`) · **12 (`pm_interest`)** · 14 (`im_growing_stock`) · 22 (`pm_land_conservation`) · 28 (`ac`/`ac_est`/`ac_sub`) · 29 (`vm_fallow`) · 30 (`vm_area`) · 35 (`pm_max_forest_est`, **`vm_natforest_reduction`**) · 44 (`fm_bii_coeff`) · 52 (**`fm_carbon_density`**, `pm_carbon_density_*`) · 73 (`pm_demand_forestry`, `im_timber_prod_cost`)

**This matches the auditor's M7/M8/m8 sets exactly.** Bold = absent from the doc.

---

## Per-bug verdicts

### M32-C1 — UPHELD (consumer_set) — citation_ok ✅
`58_peatland/v2/equations.gms:28` = `v58_manLandExp(j2,manPeat58) =e= m58_LandMerge(vm_landexpansion,vm_landexpansion_forestry,"j2");` — token present.
`:31` = same for `vm_landreduction_forestry`. Repo-wide `rg` on both variables returns **only** M32 (declare/populate/postsolve) + M58/v2 + `58/off/not_used.txt` + CHANGELOG. **Zero** M10 references, confirmed by a second method (`find`+`grep` in `10_land` → EXIT 1) with a passing positive control. The doc's separate `vm_landdiff_forestry`→M10 row is correct and must be kept.

### M32-C2 — UPHELD (consumer_set) — citation_ok ✅
`pcm_land_forestry` repo-wide: declared M32 `declarations.gms:48`, written M32 `presolve.gms:102`, read **only** at `58_peatland/v2/presolve.gms:11`. M35 never touches it.
Second half confirmed: M35 builds `pm_max_forest_est` from `f35_pot_forest_area − sum(land_forest, pcm_land(j,land_forest))` (`preloop.gms:63`) / `vm_land.l` (`postsolve.gms:22`), with `land_forest = / forestry, primforest, secdforest /` at `core/sets.gms:259-260` — so M35 consumes the forestry slice via a **set-sum**, not via `pcm_land_forestry`. M32 writes that slice at `presolve.gms:100` (`vm_land.l(j,"forestry")`) and `:101` (`pcm_land(j,"forestry")`) — the auditor's added-row citation is exact.

### M32-C3 — UPHELD (consumer_set) — citation_ok ✅
`vm_land_forestry` sole external consumer = `58_peatland/v2/equations.gms:23`. Declared `32_forestry/dynamic_may24/declarations.gms:76`. `module.gms:15` reads "available to other modules via the interface `vm_land_forestry`" — names no module, as the auditor said.

### M32-M1 — UPHELD (consumer_set) — citation_ok ✅
Prose restatement of C1 at doc:272/281. Same evidence.

### M32-M2 — UPHELD (other / wrong_units) — citation_ok ✅
`declarations.gms:73` = `vm_prod_forestry(j,kforestry) … (mio. tDM per yr)`. `im_growing_stock … (tDM per ha)` at `14_yields/managementcalib_aug19/declarations.gms:17` (default per cfg:354). Zero `m3|vol_conv|volume|cubic` tokens in all of `modules/32_forestry/` (positive control passed). Doc:1409 already says `mio. tDM/yr` → self-contradiction confirmed.

> **CAVEAT-A (auditor rationale error — does NOT enter the doc).** The auditor wrote "the volume conversion `im_vol_conv` lives in Module 73." **False.** `im_vol_conv` is **declared** in `52_carbon/normal_dec17/declarations.gms:23` (`Regional basic wood density (tDM per m3)`) and **populated** at `52_carbon/normal_dec17/preloop.gms:21` (+ `start.gms:40`); M73 is only a **consumer** (`73_timber/default/preloop.gms:49,51,90,91`). The proposed_fix string contains no such claim, so applying it verbatim is safe — but do not repeat this attribution anywhere.

### M32-M3 — UPHELD (other / fabricated_formula) — citation_ok ✅
`preloop.gms:105` = `p32_rotation_regional(t_all,i) = ceil(sum(cell(i,j), p32_rot_length_ac_eqivalent(t_all,j))/p32_ncells(i));`
`preloop.gms:101` = `p32_ncells(i) = sum(cell(i,j),1);` and `declarations.gms:42` = "Number of cells in each region (1)". **Unweighted cell mean, ceil-rounded.** No area weight exists anywhere. The doc's "weighted average … by area" is fabricated.

### M32-M4 — UPHELD (producer_declaration) — citation_ok ✅
`fm_bii_coeff` occurs **0×** in M32's `equations.gms`; its only M32 occurrences are `preloop.gms:204,206,208,209`. The doc's cited lines `equations.gms:131,136,141` all contain `p32_bii_coeff` (verified by reading 128-142). Declared `44_biodiversity/bii_target/input.gms:17` as `table fm_bii_coeff(bii_class44,potnatveg)` — indexed by **BII class**, not age class (the age-class mapping `ac_to_bii_class_secd` is applied separately inside M32's equations).

### M32-M5 — UPHELD (other / wrong_mechanism + phase order) — citation_ok ✅
- `pm_max_forest_est` **init** `35/pot_forest_may24/preloop.gms:63-64`; **refresh for t+1** `postsolve.gms:22-23`; M35 `presolve.gms:216-217` only **raises** it to the `youngsecdf` floor.
- **Ordering proven mechanically**: `core/calculations.gms:54` = `$batinclude "./modules/include.gms" presolve` — a *single* presolve pass over `modules/include.gms`, which lists `32_forestry` at **:29** and `35_natveg` at **:31**. ⇒ **M32 presolve runs BEFORE M35 presolve.** The doc has the dependency backwards.

> **Nuance for the fixer (not a defect in the fix).** "The value M32 reads at `t` comes from M35's postsolve at `t-1`" is precisely true of M32's **presolve** read (`presolve.gms:22-23`). At **solve** time (`equations.gms:86`, `sum(ct,pm_max_forest_est(ct,j2))`) M35's presolve floor-raise *has* already been applied. The proposed text is accurate as written; just don't over-extend it to the equation.

### M32-M6 — UPHELD (other / fabricated temporal lag) — citation_ok ✅
`pm_demand_forestry(t_ext,i,kforestry)` declared `73_timber/default/declarations.gms:11`; populated **only** at `73/default/preloop.gms:49,51,83,85` from `p73_timber_demand_gdp_pop × im_vol_conv` — **exogenous**, no M32 feedback. `preloop` runs **once**, before the time loop (`core/calculations.gms:15`). M32 reads **future** demand at `presolve.gms:201` (`t_ext.pos = t.pos + p32_rotation_regional`). **No previous-timestep lag exists anywhere.** Doc line 724 is fabricated and contradicts the doc's own §4.3.

### M32-M7 — UPHELD (consumer_set) — citation_ok ✅
All 7 `file_evidence` citations reproduce. My independent sweep (above) returns **exactly** the auditor's 7-provides / 11-receives sets. Doc:683 ("5 provides, 6 receives") is contradicted by the doc's own tables (5 and 10 distinct modules) *and* by doc:749 ("depends on 11").

> **CAVEAT-B (count convention — read before writing "11").** A **12th** source module exists if global scalars are counted: `sm_fix_SSP2` is declared in `09_drivers/aug17/input.gms:22` and read by M32 at `presolve.gms:198-199`. The auditor and the doc both exclude it. **Keep "11"** so the fix stays consistent with doc:749; do not write "12" unless line 749 is changed in the same edit.

### M32-M8 — UPHELD (producer_declaration) — citation_ok ✅
- `pm_interest`: declared `12_interest_rate/select_apr20/declarations.gms:9` (default per cfg:240); consumed M32 `equations.gms:171,173` + `preloop.gms:41,68,75,78,79`. All exact.
- `vm_natforest_reduction`: declared `35_natveg/pot_forest_may24/declarations.gms:90`, populated by M35 `equations.gms:84`; consumed by M32 `equations.gms:80` (`q32_ndc_aff_limit`). Genuine M35→M32 input, absent from the doc.
- `fm_carbon_density`: declared `52_carbon/normal_dec17/input.gms:16`; consumed M32 `presolve.gms:176` — and it *is* the 20 tC/ha threshold (`v32_land.fx(j,"aff",ac_est)$(fm_carbon_density(t,j,"forestry","vegc") <= 20) = 0;`).

### M32-m1 — UPHELD (other / stale citation) — citation_ok ✅
`equations.gms:165` **is blank** (verified by reading 163-175). `im_timber_prod_cost` appears in M32 exactly once: `equations.gms:172`.

### M32-m2 — UPHELD (other / stale citation) — citation_ok ✅
`presolve.gms:52` = `** END ndc **`; 53-57 = blank + comment header; the `s32_aff_plantation` branch is at **58-62**. Doc:109 already cites `presolve.gms:58-62` for the same block → internal inconsistency confirmed.

### M32-m3 — UPHELD (other / elided branch) — citation_ok ✅
Read `presolve.gms:197-205` verbatim. The doc's fenced block jumps from `if(s32_demand_establishment = 1,` straight to the `t_ext` line, silently dropping the nested `if(m_year(t) <= sm_fix_SSP2, …)` branch at 198-200. The auditor's replacement block matches source (only a trivial whitespace difference after the comma on :201).

### M32-m4 — UPHELD (other / invented identifier) — citation_ok ✅
`ac_rotation` occurs **0×** in the entire repo (positive control: `ac_est` found in `core/sets.gms`). `presolve.gms:181` = `i32_growing_stock_at_harvest(t,j) = sum(ac$(ac.off = p32_rotation_cellular_estb(t,j)), im_growing_stock(t,j,ac,"forestry"));` — the auditor's replacement formula is verbatim.

### M32-m5 — UPHELD (other / broken cross-ref) — citation_ok ✅
Proven by `git merge-base --is-ancestor`:
- `75d7ee167` ("Forestry module overhaul: BEF/BCEF fix, IPCC wood density, stacking factor, growing stock calibration", florianh, **2026-03-15**)
- **NOT** an ancestor of `85cbcb82b` = "Merge pull request **#869** from georg-schroeter/ipopt_part1" (2026-03-16) → did *not* land via #869.
- **IS** an ancestor of `a0d5767ef` = "Merge pull request **#872** from flohump/fix/bef-bcef-option2" (2026-03-25) → landed via **#872**. That branch's log includes "Address review comments: **cost regionalization**, naming conventions, calibration simplification", corroborating the `im_timber_prod_cost` regionalization.

### M32-m6 — UPHELD (other / overbroad negative) — citation_ok ✅
`input.gms:23-27` = the five cost scalars (`s32_est_cost_plant` 2460, `s32_est_cost_natveg` 2460, `s32_est_cost_plant_reest` 1230, `s32_recurring_cost` 615, `s32_harvesting_cost` 1230) — global constants, correct. **But** `q32_cost_establishment` uses region-specific `im_timber_prod_cost(i2,kforestry)` (`equations.gms:172`) and region+time-specific `pm_interest(ct,i2)` (`equations.gms:171,173`). Doc:499 already states the region-dimensioning → self-contradiction confirmed.

### M32-m7 — UPHELD (consumer_set / direct-vs-transitive, MANDATE 17) — citation_ok ✅
M56 (`price_aug22`) declares exactly **5** interfaces: `im_pollutant_prices` (:9), `vm_carbon_stock` (:34), `vm_emission_costs` (:39), `vm_emissions_reg` (:40), `vm_reward_cdr_aff` (:43). M32's complete 30-token interface set contains **only** `vm_carbon_stock`, and it appears in M32 exactly once — `equations.gms:108`, as the **LHS** of `q32_carbon` (populated, not consumed). M32 contains **no** carbon-price token at all (`carbon_price|c_price|pollutant|pm_taxrate` → 0 hits). The price incentive reaches M32 only through the objective function. Doc:754's "Module 56 (Carbon price)" as a *dependency* is a transitive/objective-function link, not an interface read.

### M32-m8 — UPHELD (consumer_set + producer_declaration) — citation_ok ✅
Doc:1377 receives (6) omits **12, 14, 29, 30, 35**; doc:1378 provides omits **44, 52, 58** and wrongly includes **35** (the C2 error propagating). The auditor's replacement sets match my independent derivation exactly. The "resolved via temporal lag" circularity claim for M73 is refuted by M6.

### M32-i1 — UPHELD (other / count) — citation_ok ✅
`wc -l` on `dynamic_may24/*.gms`: 173+260+100+209+228+231+47+33+51 = **1,332** (doc says 1,331, at both :5 and :1354). `module.gms` = 26 lines.

### M32-i2 — UPHELD (other / wrong domain) — citation_ok ✅
`declarations.gms:27` `p32_rotation_regional(t_all,i)` · `:29` `p32_rotation_cellular_estb(t_all,j)` · `:30` `p32_rotation_cellular_harvesting(t_all,j)` — all **`t_all`**, not `t`. Load-bearing: `preloop.gms:128` writes `p32_rotation_cellular_harvesting(t_all+p32_rotation_offset,j)`, i.e. into non-optimization timesteps. (By contrast `i32_growing_stock_at_harvest(t,j)` at `:24` genuinely is `t` — the doc is right there.)

---

## Two things NOT bugs (checked, doc is correct — do not "fix")

- **"31 equations"** (doc:1355): I enumerated all `q32_*` in `equations.gms` → exactly **31**. Correct.
- **`vm_landdiff_forestry` → 10_land** (doc:691 region): correct and independently confirmed (`10_land/landmatrix_dec18/equations.gms:54`). C1 must not delete this row.

## Fixer instructions

Apply all 20 proposed fixes as written, with two edits to the auditor's *rationale* (not its fix text):
1. **CAVEAT-A** — never repeat "`im_vol_conv` lives in Module 73"; it is declared/populated in **52_carbon**, consumed by 73.
2. **CAVEAT-B** — write "**11**" receives (not 12); `sm_fix_SSP2` from 09_drivers is excluded by the doc's own convention at line 749.
