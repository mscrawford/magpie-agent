# Round 54 — Adversarial doc audit: `modules/module_32.md` (Forestry)

**Auditor**: Opus (adversarial doc-vs-code)
**Date**: 2026-07-14
**Target doc**: `<magpie-agent>/modules/module_32.md` (1,421 lines)
**Ground truth**: `/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop, read-only worktree) + `config/default.cfg` + the R layer (`scripts/start_functions.R`, `scripts/npi_ndc/start_npi_ndc.R`)
**Claims checked**: 112 load-bearing, code-checkable claims
**Verdict**: **SIGNIFICANT ERRORS** in the dependency/interface sections; the equation-level and default-parameter content is excellent.

---

## 0. Headline

The doc's **equations, scalars, defaults, realization, and the freshly-retracted `ndcdelay`/`affexp` text are all correct** — the retraction verified clean (see §1). The damage is concentrated in **§8 (Module Dependencies)**: **Module 58 (peatland) — the actual consumer of four Module-32 interfaces — is missing from the doc entirely**, and its links were mis-attributed to Modules 10 and 35. This is the R20 anchor bug class (wrong consumer set → Critical).

| Severity | Count |
|---|---|
| 🔴 Critical | 3 |
| 🟠 Major | 8 |
| 🟡 Minor | 8 |
| 🟢 Informational | 2 |

---

## 1. RETRACTION VERIFICATION (highest priority) — ✅ **CONFIRMED CLEAN**

The pre-run advisory asked me to verify that the retracted `ndcdelay`/`affexp` "silently zero" claim is gone and that the replacement text is correct — and not an over-correction. **All four sub-checks pass. No residual false claim; no over-correction. No edit needed.**

| Check | Doc text | Code evidence | Verdict |
|---|---|---|---|
| (a) `ndcdelay` + `affexp` documented as WORKING | §9.2 lines 832-833 list both as live options with descriptions | `sets.gms:19-20` → `pol32 / none, npi, ndc, affexp, ndcdelay /` | ✅ |
| (b) No residual "silently zero" assertion | Line 838: "*a stale header on disk does **not** mean a policy is unusable*" | — | ✅ (retraction fully absorbed) |
| (c) Not an over-correction | Lines 838 + 913 retain the real footgun: `cfg$recalc_npi_ndc <- FALSE` skips regeneration | `start_functions.R:375` (`if(cfg$recalc_npi_ndc=="ifneeded")`) and `:434` (`if(cfg$recalc_npi_ndc){`) — both false when the user sets `FALSE` ⇒ no regeneration | ✅ correctly scoped to the non-default |
| (d) R-layer regeneration mechanism (verified myself, not inherited) | "`scripts/start_functions.R:380-391` detects a missing column (`affexp_missing` / `ndcdelay_missing`) … under the default `cfg$recalc_npi_ndc <- "ifneeded"` (`config/default.cfg:123`)" | `start_functions.R:380` `affexp_missing <- (cfg$gms$c32_aff_policy == "affexp") && !("affexp" %in% getNames(aff_pol))`; `:382` `ndcdelay_missing <- …`; `:388` used in the OR; `:390` `cfg$recalc_npi_ndc <- TRUE`; `:434-440` `source("scripts/npi_ndc/start_npi_ndc.R"); calc_NPI_NDC(...)`. `config/default.cfg:123` = `cfg$recalc_npi_ndc <- "ifneeded"    # def = ifneeded` | ✅ **exact** |

Supporting facts re-derived this session:
- `.gitignore:7` (`*.cs*`) **does** match `modules/32_forestry/input/npi_ndc_aff_pol.cs3` (`git check-ignore -v` confirms) — the file is a run-time product; it is not even on disk in a fresh worktree (`modules/32_forestry/input/` contains only the `files` manifest).
- `calc_NPI_NDC()` is defined at `scripts/npi_ndc/start_npi_ndc.R:15`, reads `pol_def_file = "policies/policy_definitions.csv"` (`:16`), writes `out_aff_file = "npi_ndc_aff_pol.cs3"` into `../../modules/32_forestry/input/` (`:22-23`). ⇒ doc §10.1 line 911 is **exactly right**.
- "**No GAMS code branch for any policy**" (line 837): confirmed — `c32_aff_policy` occurs in the whole GAMS layer exactly twice: `input.gms:9` (`$setglobal`) and `preloop.gms:182` (`p32_aff_pol(t,j) = round(f32_aff_pol(t,j,"%c32_aff_policy%"),6);`). ✅
- `f32_aff_pol` table description (`input.gms:71`): "npi+ndc+affexp+ndcdelay re-afforestation policy (Mha new forest wrt to 2010)" ⇒ doc's "Mha new forest relative to 2010" ✅
- `ndcdelay` commit `58bde5788` = "added ndcdelay afforestation policy (PRISMA Asymmetric Roll-back)", 2026-07-02 ✅ (doc: "added on develop 2026-07, commit `58bde5788`").
- `affexp` commit `a54cd02c6`, 2026-05-27, "…Designed per Good Performance scenario in the ELEVATE project" ✅ (doc: "added on develop 2026-05 for the ELEVATE project 'Good Performance' scenario").

**The retraction is verified correct. Do not touch this text.**

---

## 2. 🔴 CRITICAL bugs (wrong consumer sets — R20 anchor)

Module 58 (peatland, realization `v2`, **default** per `config/default.cfg:1871`) merges managed-forest land into its peatland accounting via the `m58_LandMerge` macro. It is the **sole external consumer** of four Module-32 interfaces. The doc never mentions Module 58 and mis-routes its links to Modules 10 and 35.

### C1 — `vm_landexpansion_forestry` / `vm_landreduction_forestry` attributed to Module 10
- **Doc** (module_32.md:691-692):
  `| **10_land** | vm_landexpansion_forestry | Forestry expansion by type | equations.gms:61-62 |`
  `| **10_land** | vm_landreduction_forestry | Forestry reduction by type | equations.gms:64-65 |`
- **Code**: the only external references are
  `modules/58_peatland/v2/equations.gms:28` → `v58_manLandExp(j2,manPeat58) =e= m58_LandMerge(vm_landexpansion,vm_landexpansion_forestry,"j2");`
  `modules/58_peatland/v2/equations.gms:31` → `v58_manLandRed(j2,manPeat58) =e= m58_LandMerge(vm_landreduction,vm_landreduction_forestry,"j2");`
  Module 10 references **neither** variable. (M10 *does* consume `vm_landdiff_forestry` — `modules/10_land/landmatrix_dec18/equations.gms:54` — that row of the doc is correct.)
- **Verify** (two methods + positive control):
  `rg -n 'vm_landexpansion_forestry|vm_landreduction_forestry' --glob '*.gms' .` → hits only in `32_forestry` and `58_peatland/v2/equations.gms:28,31`
  `find modules core -name '*.gms' -exec grep -Hn 'vm_landexpansion_forestry\|vm_landreduction_forestry' {} + | grep -v 32_forestry` → same two lines
  positive control: `find modules/10_land -name '*.gms' -exec grep -Hn 'vm_landdiff' {} +` → 5 hits (search works in that dir)
- **Harm**: a user refactoring M32's land interfaces would look in M10 (nothing there) and never open M58 → silent breakage of peatland land accounting. Exactly the R20 anchor.

### C2 — `pcm_land_forestry` attributed to Module 35 "for max forest establishment calc"
- **Doc** (module_32.md:694): `| **35_natveg** | pcm_land_forestry | Forestry land for max forest establishment calc | presolve.gms:102 |`
- **Code**: sole external consumer = `modules/58_peatland/v2/presolve.gms:11` → `pc58_manLand(j,manPeat58) = m58_LandMerge(pcm_land,pcm_land_forestry,"j");`
  Module 35 does **not** read `pcm_land_forestry`. `pm_max_forest_est` is built from the *land-pool* interface, not the type32-resolved one:
  `modules/35_natveg/pot_forest_may24/preloop.gms:63` → `pm_max_forest_est(t,j) = f35_pot_forest_area(t,j) - sum(land_forest, pcm_land(j,land_forest));`
  `modules/35_natveg/pot_forest_may24/postsolve.gms:22` → `pm_max_forest_est(t+1,j) = f35_pot_forest_area(t+1,j) - sum(land_forest, vm_land.l(j,land_forest));`
  with `land_forest / forestry, primforest, secdforest /` (`core/sets.gms:259-260`). So M35 *is* a genuine downstream reader of M32's output — but via `pcm_land(j,"forestry")` / `vm_land(j,"forestry")` (which M32 writes at `presolve.gms:100-101`), **not** via `pcm_land_forestry`.
- **Verify**: `rg -n 'pcm_land_forestry' --glob '*.gms' modules core | grep -v 32_forestry` → 1 hit (58_peatland); cross-checked with `find … -exec grep` → same 1 hit; positive control `grep 'pcm_land' modules/35_natveg` → 8+ hits.

### C3 — `vm_land_forestry` described as an interface "to Module 10 (Land)"
- **Doc** (module_32.md:34): "- Provides `vm_land_forestry(j,type32)` interface to Module 10 (Land)"
- **Code**: sole external consumer = `modules/58_peatland/v2/equations.gms:23` → `v58_manLand(j2,manPeat58) =e= m58_LandMerge(vm_land,vm_land_forestry,"j2");`. `module.gms:15` says only "made available to other modules via the interface `vm_land_forestry`" — it names no module; the doc invented Module 10.
- **Verify**: `rg -n 'vm_land_forestry' --glob '*.gms' .` → M32 (decl/eq/postsolve) + `58_peatland/v2/equations.gms:23` only.

---

## 3. 🟠 MAJOR bugs

### M1 — §4.2 prose repeats the C1 misattribution (doc:272, doc:281)
"Net forestry expansion **reported to Module 10**" / "Net forestry reduction **reported to Module 10**". Same code evidence as C1. Scored Major (not Critical) only because C1 already carries the table-level error; the tie-breaker pulls the duplicate down.

### M2 — Timber production units given as volume (m³) (doc:1080)
- **Doc** §12 item 7: "Yield measured in volume (m³) only".
- **Code**: `vm_prod_forestry(j,kforestry)` is **mio. tDM per yr** (`modules/32_forestry/dynamic_may24/declarations.gms:73`) and `im_growing_stock` is **tDM per ha** (`modules/14_yields/managementcalib_aug19/declarations.gms:17`). There is no m³ anywhere in Module 32 (volume conversion `im_vol_conv` lives in Module 73). The doc contradicts its own interface table (line 1409: "mio. tDM/yr").
- **Verify**: `grep -n 'vm_prod_forestry' modules/32_forestry/dynamic_may24/declarations.gms` → `(mio. tDM per yr)`.

### M3 — `p32_rotation_regional` described as an **area-weighted** average (doc:175, doc:951)
- **Doc**: fenced pseudo-formula "p32_rotation_regional(t,i) = weighted average of cellular rotations by area" and "**Aggregation**: Area-weighted average of cellular rotations".
- **Code** (`preloop.gms:105`): `p32_rotation_regional(t_all,i) = ceil(sum(cell(i,j), p32_rot_length_ac_eqivalent(t_all,j))/p32_ncells(i));` with `p32_ncells(i) = sum(cell(i,j),1)` (`preloop.gms:101`) — an **unweighted cell-count mean, rounded up**. No area weight appears anywhere in the calculation.

### M4 — `fm_bii_coeff` cited to the wrong file (doc:708)
- **Doc**: `| **44_biodiversity** | fm_bii_coeff | BII coefficients by age class | equations.gms:131, 136, 141 |`
- **Code**: `fm_bii_coeff` occurs **0 times** in `modules/32_forestry/dynamic_may24/equations.gms` (`grep -c` → 0). It is read only in **`preloop.gms:204, 206, 208, 209`** (into `p32_bii_coeff`). The cited equation lines use `p32_bii_coeff`, the derived module-internal parameter. (The *source module* claim is right: `fm_bii_coeff` is declared in `modules/44_biodiversity/bii_target/input.gms:17` — `bii_target` is the default, `config/default.cfg:1435`.)

### M5 — Wrong resolution mechanism for the `pm_max_forest_est` dependency (doc:719)
- **Doc**: "**Resolved**: `pm_max_forest_est` calculated in Module 35 presolve, available before Module 32 presolve".
- **Code**: it is initialised in Module 35 **preloop** (`pot_forest_may24/preloop.gms:63-64`) and refreshed for `t+1` in Module 35 **postsolve** (`postsolve.gms:22-23`); M35's presolve only clips it (`presolve.gms:216-217`). And the ordering is the reverse of what the doc claims: `modules/include.gms:29` (32_forestry) precedes `:31` (35_natveg), so **Module 32's presolve runs BEFORE Module 35's presolve**. The value M32 reads at timestep *t* comes from M35's postsolve of *t−1* (or preloop in the first timestep).

### M6 — Wrong resolution mechanism for the Module 32 ↔ Module 73 "circularity" (doc:724, echoed doc:1379)
- **Doc**: "**Resolved**: Demand from previous timestep used for establishment decisions" / "**Circular**: With modules 10 and 73 (resolved via temporal lag)".
- **Code**: `pm_demand_forestry(t_ext,i,kforestry)` is **exogenous** (GDP/population-driven) and computed once in Module 73 **preloop** (`modules/73_timber/default/preloop.gms:49-85`) over `t_all`/`t_ext`. It does not depend on M32's output, so there is no circularity in the parameter direction and no lag. M32 in fact reads **future** demand (`t` + rotation length): `presolve.gms:201` → `sum(t_ext$(t_ext.pos = t.pos + p32_rotation_regional(t,i)), pm_demand_forestry(t_ext,i,kforestry))`. The doc contradicts its own §4.3 ("Forward-looking demand").

### M7 — Connectivity counts wrong; provides-table omits 4 consumer modules (doc:683, table 687-696)
- **Doc**: "**VERIFIED**: Module 32 has moderate connectivity (5 provides, 6 receives)" — while the table right below lists 8 provides-rows and the receives table lists 11 rows, and line 749 says "depends on 11".
- **Code** — actual consumer modules of M32 outputs (7): **10** (`vm_land(j,"forestry")`, `vm_landdiff_forestry` @ `10_land/landmatrix_dec18/equations.gms:54`), **11** (`vm_cost_fore` @ `11_costs/default/equations.gms:33`), **44** (`vm_bv` slices @ `44_biodiversity/bii_target/equations.gms:16`), **52** (`pm_land_plantation` @ `52_carbon/normal_dec17/preloop.gms:88,90,94`; `vm_carbon_stock` forestry slice @ `52_carbon/normal_dec17/equations.gms:19`), **56** (`vm_cdr_aff` @ `56_ghg_policy/price_aug22/equations.gms:77`; `vm_carbon_stock` @ `price_aug22/equations.gms:22`), **58** (four interfaces, see C1-C3), **73** (`vm_prod_forestry` @ `73_timber/default/equations.gms:46,55,78`).
  The provides table lists only 10/11/35/56/73 → M44, M52, M56-via-`vm_carbon_stock`, and M58 are missing; M35 is listed for the wrong variable (C2).

### M8 — Receives table omits Module 12 entirely (doc table 700-712)
- **Code**: M32 reads `pm_interest` (declared `modules/12_interest_rate/select_apr20/declarations.gms:9`; default realization per `config/default.cfg:240`) at **`equations.gms:171` and `:173`** (annuity factor + compound discounting in `q32_cost_establishment`) and at `preloop.gms:41, 68, 75, 78-79` (IGR / Faustmann rotations). Module 12 appears **nowhere** in module_32.md's dependency structures.
- Also missing from the table: **`vm_natforest_reduction`** (declared `modules/35_natveg/pot_forest_may24/declarations.gms:90`, consumed by M32 at `equations.gms:80` in `q32_ndc_aff_limit`) and **`fm_carbon_density`** (declared `modules/52_carbon/normal_dec17/input.gms:16`, consumed at `presolve.gms:176`).

---

## 4. 🟡 MINOR bugs

| ID | Doc | Claim | Reality |
|---|---|---|---|
| m1 | :712 | `im_timber_prod_cost` … `equations.gms:165` | `equations.gms:165` is a **blank line**; the use is at **`equations.gms:172`** |
| m2 | :1161 | §13.3 "Effect (`presolve.gms:52-56`)" | the `s32_aff_plantation` branch is **`presolve.gms:58-62`** (52-56 = the "END ndc" marker + comment header). §2.3 line 109 cites it correctly — internal inconsistency |
| m3 | :313-317 | ```gams``` block for forward-looking demand shows `if(s32_demand_establishment = 1,` immediately followed by the `t_ext` assignment | the code has a nested branch between them: `presolve.gms:198-200` uses the **fix-year demand** while `m_year(t) <= sm_fix_SSP2`. Presented as verbatim source with the branch silently elided |
| m4 | :959 | "**Formula**: `im_growing_stock(t,j,ac_rotation,"forestry")`" | **`ac_rotation` is not a set/index in MAgPIE** (`rg 'ac_rotation' modules core` → absent). Real formula (`presolve.gms:181`): `sum(ac$(ac.off = p32_rotation_cellular_estb(t,j)), im_growing_stock(t,j,ac,"forestry"))` |
| m5 | :62, :962 | "Renamed 2026-04-20 (**PR #869**, commit `75d7ee167`)" | commit SHA correct; **PR #869 is `ipopt_part1` from georg-schroeter** (merge `85cbcb82b`, 2026-03-16). The forestry overhaul landed via **PR #872** (`a0d5767ef`, "Merge pull request #872 from flohump/fix/bef-bcef-option2", 2026-03-25); the commit itself is dated 2026-03-15 |
| m6 | :1074-1077 | §12 item 6 "**Does NOT vary costs regionally or temporally**" | the establishment/recurring/harvesting **scalars** are global (`input.gms:23-27`) ✅, but `q32_cost_establishment` uses region-specific `im_timber_prod_cost(i2,kforestry)` (`equations.gms:172`) and region- and time-specific `pm_interest(ct,i2)` (`:171,:173`) — contradicts the doc's own §5.1 note (line 499) |
| m7 | :754 | "**Depends On**: … Module 56 (Carbon price)" | M32 reads **no** Module-56 interface (`rg 'pm_carbon_price|p56_|vm_emission_costs' modules/32_forestry/` → only M32's own `q32_carbon` populating `vm_carbon_stock`). The carbon-price incentive reaches M32 **only through the objective function** (M32 provides `vm_cdr_aff`; M56 prices it). MANDATE 17 (direct vs transitive) |
| m8 | :1377-1379 | §15 Summary: "Receives from: 10, 22, 28, 44, 52, 73" / "Provides to: 10, 11, 35, 56, 73" / "Circular: with 10 and 73 (temporal lag)" | receives omits **12, 14, 29, 30, 35**; provides omits **44, 52, 58** and lists 35 for the wrong variable; the "temporal lag" claim is refuted in M6 |

---

## 5. 🟢 Informational

| ID | Doc | Claim | Reality |
|---|---|---|---|
| i1 | :5 | "Code Size: **1,331** lines across 9 files" | `wc -l` on the 9 `dynamic_may24/*.gms` files = **1,332** (173+260+100+209+228+231+47+33+51) |
| i2 | :940-951 | `p32_rotation_cellular_estb(t,j)`, `p32_rotation_cellular_harvesting(t,j)`, `p32_rotation_regional(t,i)` | declared over `t_all`: `(t_all,j)`, `(t_all,j)`, `(t_all,i)` (`declarations.gms:27,29,30`) |

---

## 6. Verified-correct claims (sample of the 112 — this doc is strong outside §8)

**Realization / structure**
- `dynamic_may24` is the **only** realization (`ls modules/32_forestry/` → `dynamic_may24`, `input`) and the default (`config/default.cfg:992`). ✅
- Authors "Florian Humpenöder, Abhijeet Mishra" ✅ (`module.gms:22`). Three types via `type32 / aff, ndc, plant /` ✅ (`sets.gms:16-17`).
- "**31 equations**" ✅ — I counted 31 in `equations.gms` and 31 declarations (`declarations.gms:87-117`). All 31 are documented in §4.

**Every scalar default cross-checked against `input.gms` AND `config/default.cfg`** — all correct:
`s32_hvarea=2` (:22 / cfg:1122) · `s32_est_cost_plant=2460` (:23 / cfg:1102) · `s32_est_cost_natveg=2460` (:24 / cfg:1106) · `s32_est_cost_plant_reest=1230` (:25 / cfg:1112 `0.5 *`) · `s32_recurring_cost=615` (:26) · `s32_harvesting_cost=1230` (:27) · `s32_planning_horizon=50` (:28 / cfg:999) · `s32_rotation_extension=1` (:29) · `s32_free_land_cost=1e6` (:33) · `s32_max_aff_area=Inf` (:34 / cfg:1034) · `s32_aff_plantation=0` (:35 / cfg:1008) · `s32_aff_bii_coeff=0` (:39 / cfg:1016) · `s32_max_aff_area_glo=1` (:40 / cfg:1047) · `s32_aff_prot=1` (:41 / cfg:1044) · `s32_npi_ndc_reversal=Inf` (:48 / cfg:1029) · `s32_annual_aff_limit=0.03` (:50 / cfg:996) · `c32_aff_policy=npi` (:9 / cfg:1026) · `c32_aff_mask=noboreal` (:7 / cfg:1056) · `c32_aff_bgp=nobgp` (:11 / cfg:1067) · `c32_rot_calc_type=current_annual_increment` (:15 / cfg:1130) · `c32_shock_scenario=none` (:17 / cfg:1138) · plantation-contribution fader 7%→0%, 1995→2025, cap 1 (:42-46).

**Equation citations** — all 31 equation file:line ranges spot-checked; every one lands on the right equation (`q32_cost_total` 21-27, `q32_cdr_aff` 36-39, `q32_bgp_aff` 41-43, `q32_aff_est` 46, `q32_land` 55-56, `q32_land_type32` 58-59, `q32_land_expansion_forestry` 61-62, `q32_land_reduction_forestry` 64-65, `q32_land_replant` 67-70, `q32_aff_pol` 74-75, `q32_ndc_aff_limit` 79-80, `q32_co2p_aff_limit` 84-86, `q32_max_aff` 94-96, `q32_max_aff_reg` 98-100, `q32_carbon` 108-109, `q32_land_diff` 113-115, `q32_land_expansion` 117-119, `q32_land_reduction` 121-122, `q32_bv_aff` 128-131, `q32_bv_ndc` 133-136, `q32_bv_plant` 138-141, `q32_cost_establishment` 166-173, `q32_cost_recur` 181-182, `q32_prod_forestry_future` 197-201, `q32_establishment_demand` 205-209, `q32_establishment_hvarea` 213-217, `q32_establishment_fixed` 224-225, `q32_forestry_est` 231-232, `q32_hvarea_forestry` 237-240, `q32_prod_forestry` 246-249, `q32_cost_hvarea` 254-258). Quoted GAMS bodies match the source verbatim.

**Presolve citations**: `:65`, `:68`, `:71-72`, `:75-78`, `:83`, `:89-91`, `:94`, `:102`, `:108-136`, `:144`, `:149-153`, `:152`, `:156-159`, `:176`, `:180-181` — all correct.

**The `vm_bv` per-slice-ownership note (doc:458)** — audited in full and **entirely correct**: declared in M44 (`bii_target/declarations.gms:11`, default realization ✅); populated slice-by-slice by M29 (`detail_apr24/equations.gms:77`), M30 (`simple_apr24/equations.gms:57`), M31 (`endo_jun13/equations.gms:38`), M34 (`exo_nov21/equations.gms:35`), M35 (`pot_forest_may24/presolve.gms:285`), M32 itself; sole RHS consumer = M44 (`bii_target/equations.gms:16`). Full `rg 'vm_bv'` sweep found no populator outside that set. (Nit, not a bug: M29 also populates the `crop_tree` slice at `detail_apr24/equations.gms:102`; and in the default `detail_apr24` it is an *equation*, not a `.fx` — "fixes" is the `simple_apr24` behavior.)

**Rename hygiene (MANDATE 19)**: `pm_timber_yield` and `p32_yield_forestry_future` are **absent** from develop (`rg` over `modules core` → no hits); the doc italicizes them as deprecated. ✅ `i32_growing_stock_at_harvest` (`declarations.gms:24`) and `im_growing_stock` (`14_yields/managementcalib_aug19`) are correctly attributed. The discounting-fix annotation (`9ccd6290d`, 2025-11-28) matches git exactly.

---

## 7. Deferred (NOT edited — not code-verifiable or out of scope)

1. **"Centrality: Rank 4 of 46", "Total Connections: 16", "EXTREME RISK"** — derived from the agent's own dependency analysis; I cannot reproduce the ranking methodology from code. (Note: my own count gives 7 consumer + 11 source modules = 18 links, so "16" is likely stale — but the counting convention is unstated.)
2. **Code-side inconsistency, not a doc bug**: `input.gms:12` comments `* options: ann,nobgp` and `config/default.cfg:1063-1066` lists `ann`/`djf`/`jja` for `c32_aff_bgp`, but the `bgp32` set is `/ nobgp, ann_bph /` (`sets.gms:27-28`) and `preloop.gms:194` indexes `f32_aff_bgp(j,"%c32_aff_bgp%")`. The doc's §13.5 `ann_bph` matches the **set** (the only value that can work). Worth reporting upstream; do **not** "fix" the doc to match the stale code comment.
3. §14 testing heuristics ("rotations 20-60 years", "CDR 2-10 tC/ha/yr") — empirical expectations, not code-checkable. (Related missing nuance, not a bug: `preloop.gms:94` hard-caps rotation length at 18 age classes / 90 years — the doc never mentions the cap.)
4. `q32_land_diff` "Used by Module 10 for land-use change tracking" ✅ correct, but note M10's `q10_landdiff` is the *only* place — no action needed.
5. Whether "Module 11 (Costs + **CDR rewards**)" (doc:752) is a fair description — the CDR reward is computed in M56 and reaches M11 as `vm_emission_costs`; loose but defensible.

---

## 8. Fix order (recommended)

1. C1/C2/C3 + M1 + M7 + M8 — rewrite §8.1/§8.2 tables and the §1 role bullet; **add Module 58 (peatland) as a consumer** and **Module 12 (interest_rate) as a source**.
2. M5/M6 — rewrite the two §8.3 "Resolved" bullets.
3. M2/M3/M4 — unit, aggregation formula, and `fm_bii_coeff` citation.
4. Minors m1-m8, informationals i1-i2.
5. **Do not touch** §9.2 / §10.1 (the retraction text) — verified correct.
