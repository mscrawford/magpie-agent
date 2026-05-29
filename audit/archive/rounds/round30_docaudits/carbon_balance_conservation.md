# Doc Audit — cross_module/carbon_balance_conservation.md (Round 30)

**Auditor**: Opus adversarial doc-auditor
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (Merge PR #887)
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`
**Date**: 2026-05-29

## Overall Verdict: MOSTLY ACCURATE (lower band)

The doc is structurally strong: equation citations (M52 emissions, M59 som_target/som_pool, Chapman-Richards macro), set citations (c_pools, emis_oneoff, emis_land), realization defaults (carbon=normal_dec17, som=cellpool_jan23, ghg_policy=price_aug22, methane=ipcc2006_aug22, maccs=on_aug22), scalar defaults (s59_cost_scm_recur=65, c52_carbon_scenario=cc), and most cross-module producer/consumer claims (vm_nr_som→M51, vm_cost_scm→M11, vm_area←M30, vm_fallow/vm_treecover←M29, vm_lu_transitions←M10, vm_feed_intake←M70) all VERIFY against code. The G2-anchor claim (vm_carbon_stock declared in M56/price_aug22/declarations.gms:34) is CORRECT.

Four code-verifiable bugs found, concentrated in §7.5 (populator set) and §7.2/§2.3 (soil-carbon assembly attribution), which are exactly the MANDATE-13/17 surfaces (R20 + R24 anchors). None is Critical (the mis-attributed module is genuinely upstream; defaults/equations are all correct), but the populator-set and soil-assembly errors would mislead a modification-safety analysis.

---

## Bugs Found

### BUG 1 — §7.5 lists Module 30 as a direct provider of `vm_carbon_stock` (it is not; Module 29 is)
- **Severity**: Major
- **Class**: 15 (latent doc error / one-hop mis-attribution) — MANDATE 17, R24 Q4-B3 anchor
- **Doc line**: carbon_balance_conservation.md:591, 610-611
- **Claim**: Header "### 7.5 Modules 30, 31, 32, 35 - Land Use Drives Carbon" + "**All Provide**: `vm_carbon_stock(j,land,c_pools,"actual")`: Current carbon stocks → to Module 52"
- **Reality**: Module 30 (croparea) does NOT reference `vm_carbon_stock` anywhere. It produces `vm_carbon_stock_croparea` (`modules/30_croparea/detail_apr24/equations.gms:88`, `simple_apr24/equations.gms:50`), which Module 29 (cropland) aggregates into `vm_carbon_stock(j2,"crop",...)` at `modules/29_cropland/detail_apr24/equations.gms:39`. This is the exact R24 anchor data path (M30 → M29 aggregate → M52/M56). M30 is a one-hop upstream contributor, not a direct populator.
- **File evidence**: `modules/29_cropland/detail_apr24/equations.gms:39` (`vm_carbon_stock(j2,"crop",ag_pools,stockType) =e=`); `modules/30_croparea/detail_apr24/equations.gms:88` (`vm_carbon_stock_croparea(j2,ag_pools) =e=`)
- **verify_cmd**: `rg -n "vm_carbon_stock\b" /tmp/magpie_develop_ro/modules/30_croparea/*/*.gms` → NONE; `rg -n "vm_carbon_stock\b" .../29_cropland/detail_apr24/equations.gms` → `39: vm_carbon_stock(j2,"crop",ag_pools,stockType) =e=`; positive control `rg vm_carbon_stock_croparea .../30_croparea/*/equations.gms` → hits at :88/:50 (search works in that dir)
- **confirmed**: true
- **Proposed fix**: In §7.5 header and body, replace the cropland-side provider attribution. Change header to "### 7.5 Modules 29, 31, 32, 34, 35 - Land Use Drives Carbon" and add a Module 29 entry noting it aggregates `vm_carbon_stock_croparea` (from M30) into the cropland slice of `vm_carbon_stock`. Keep M30 as an upstream contributor labeled "M30 computes `vm_carbon_stock_croparea`; M29's `q29_carbon` aggregates it into `vm_carbon_stock`".

### BUG 2 — §7.5 omits Module 29 and Module 34 from the `vm_carbon_stock` provider set
- **Severity**: Major
- **Class**: 15 (latent doc error / populator-set omission) — MANDATE 13, R20 anchor
- **Doc line**: carbon_balance_conservation.md:591, 610-611
- **Claim**: provider set is "Modules 30, 31, 32, 35"
- **Reality**: The actual direct populators of `vm_carbon_stock` are M29 (crop slice, equations.gms:39), M31 (past, endo_jun13/equations.gms:23), M32 (forestry, dynamic_may24/equations.gms:108), M34 (urban, exo_nov21/presolve.gms:8 `vm_carbon_stock.fx(...,"urban",...)=0`), M35 (primforest/secdforest/other, pot_forest_may24/equations.gms:43,50,54), plus M59 writes the soilc slice for all land via q59_carbon_soil (equations.gms:61-64). The doc's set omits M29 and M34 entirely.
- **File evidence**: `modules/34_urban/exo_nov21/presolve.gms:8` (`vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`); `modules/29_cropland/detail_apr24/equations.gms:39`
- **verify_cmd**: `rg -ln "vm_carbon_stock\b" /tmp/magpie_develop_ro/modules/*/*/*.gms` → producers: 29_cropland, 31_past, 32_forestry, 34_urban, 35_natveg, 59_som; readers: 52_carbon, 56_ghg_policy (decl in 56)
- **confirmed**: true
- **Proposed fix**: Add Module 34 (urban) to the §7.5 provider list with note "fixes urban carbon stock to 0 via `vm_carbon_stock.fx`", and Module 29 (cropland) per BUG 1. Resulting direct-populator set: 29, 31, 32, 34, 35 (+ M59 for the soilc slice, already covered in §7.2).

### BUG 3 — §2.3 / §7.2 attribute the total-soil-carbon assembly (and subsoil) to Module 52; Module 59 writes the soilc slice of `vm_carbon_stock`
- **Severity**: Major
- **Class**: 2/15 (causal-mechanism mis-attribution; latent doc error)
- **Doc line**: carbon_balance_conservation.md:94, 99, 543-544
- **Claim**: §2.3:99 "Module 52 provides total soil carbon densities (topsoil + subsoil)"; §7.2:543-544 "Module 52 provides total soil carbon (topsoil + subsoil) to `vm_carbon_stock` / Topsoil from Module 59 + Subsoil from Module 52 = Total soil carbon"; §2.3:94 "Subsoil (Module 52): Static (fixed from LPJmL)"
- **Reality**: Module 59 assembles AND writes the soil-carbon slice of the interface. `q59_carbon_soil` (`modules/59_som/cellpool_jan23/equations.gms:61-64`): `vm_carbon_stock(j2,land,"soilc",stockType) =e= v59_som_pool(j2,land) + vm_land(j2,land) * sum(ct,i59_subsoilc_density(ct,j2))`. The subsoil density is a Module-59 parameter `i59_subsoilc_density` (declared `declarations.gms:23`; derived in `preloop.gms:12` as `fm_carbon_density(...,"other","soilc") - f59_topsoilc_density(...)`). Module 52 only READS `vm_carbon_stock` (`normal_dec17/equations.gms:19`); it never writes the soilc slice. M52 supplies the raw `fm_carbon_density` density input from which M59 derives subsoil, but the subsoil parameter and the topsoil+subsoil summation live in M59.
- **File evidence**: `modules/59_som/cellpool_jan23/equations.gms:61-64` (q59_carbon_soil writes vm_carbon_stock soilc); `modules/59_som/cellpool_jan23/preloop.gms:12` (i59_subsoilc_density definition); `modules/52_carbon/normal_dec17/equations.gms:19` (M52 only reads vm_carbon_stock)
- **verify_cmd**: `sed -n '61,64p' .../59_som/cellpool_jan23/equations.gms` → q59_carbon_soil writes soilc = v59_som_pool + vm_land*i59_subsoilc_density; `rg -n "vm_carbon_stock" .../52_carbon/normal_dec17/equations.gms` → only line 19 (a READ inside q52_emis_co2_actual, no LHS write)
- **confirmed**: true
- **Proposed fix**: §7.2: replace "Module 52 provides total soil carbon (topsoil + subsoil) to `vm_carbon_stock`" with "Module 59 assembles the soil-carbon slice of `vm_carbon_stock` via `q59_carbon_soil` (`modules/59_som/cellpool_jan23/equations.gms:61-64`): topsoil pool `v59_som_pool` + subsoil `i59_subsoilc_density` (a Module-59 parameter derived from M52's `fm_carbon_density`)." §2.3: change "Subsoil (Module 52)" to "Subsoil (parameter `i59_subsoilc_density` in Module 59, derived from M52 `fm_carbon_density` of 'other' land; static)" and change line 99 to "Module 52 provides the underlying `fm_carbon_density`; Module 59 derives subsoil and writes the total soilc into `vm_carbon_stock`."

### BUG 4 — §2.3 litter-convergence citation includes a stray line (`start.gms:37`)
- **Severity**: Minor
- **Class**: 10 (stale/wrong file:line citation)
- **Doc line**: carbon_balance_conservation.md:77
- **Claim**: "Linear convergence over 20 years (IPCC assumption, `modules/52_carbon/normal_dec17/start.gms:19,30,37`)"
- **Reality**: start.gms:19 and :30 ARE the litter-carbon linear-growth comments ("20 year time horizon taken from IPCC"). But start.gms:37 is `i52_gs_current_plant(i) = 0;` — a growing-stock calibration initialization, unrelated to litter convergence. The actual litter-convergence code lines are 19/30 (comments) and 20/31 (the `m_growth_litc_soilc(...)` calls).
- **File evidence**: `modules/52_carbon/normal_dec17/start.gms:37` (`i52_gs_current_plant(i) = 0;`); lines 19,30 are the litter comments; lines 20,31 are the litter computations
- **verify_cmd**: `sed -n '19p;30p;37p' .../52_carbon/normal_dec17/start.gms` → 19/30 = litter linear-growth comment; 37 = `i52_gs_current_plant(i) = 0;`
- **confirmed**: true
- **Proposed fix**: Change `start.gms:19,30,37` to `start.gms:19-20,30-31` (the litter comment+computation lines for plantation and secdforest).

---

## Verified-Correct Claims (high-value confirmations)

- **c_pools** `/vegc,litc,soilc/` at `core/sets.gms:324-325` — CORRECT (decl 324, members 325).
- **emis_oneoff** (21 sources, 7 land × 3 pools) at `core/sets.gms:314-318` — CORRECT (decl 314, body 315-318); members match doc list. NOTE: the parent `emis_source` set also includes `peatland` (sets.gms ~313), but emis_oneoff itself is exactly the 21 listed; doc's "21 sources" is right.
- **emis_land** mapping at `core/sets.gms:332-335`; example `crop_vegc . (crop) . (vegc)` on line 333 — CORRECT.
- **q52_emis_co2_actual** at `modules/52_carbon/normal_dec17/equations.gms:16-19` — equation text matches verbatim (pcm_carbon_stock - vm_carbon_stock)/m_timestep_length. CORRECT.
- **vm_carbon_stock** DECLARED in `modules/56_ghg_policy/price_aug22/declarations.gms:34`, 4D `(j,land,c_pools,stockType)` — CORRECT (G2 anchor; doc §2.3:101 right).
- **pcm_carbon_stock** declared `modules/56_ghg_policy/price_aug22/declarations.gms:19` — CORRECT.
- **Chapman-Richards macro** `m_growth_vegc` at `core/macros.gms:18` = `S + (A-S)*(1-exp(-k*(ac*5)))**m` — doc §6.1:435 cites macros.gms:18, formula faithful. CORRECT. (start.gms:17 plantation call, :28 secdforest call both invoke this macro with S from pc52_carbon_density_start=0; doc's start.gms:17 / :28 citations point at the right computations — the literal formula lives in the macro, which the doc separately and correctly cites.)
- **q59_som_target_cropland** at `modules/59_som/cellpool_jan23/equations.gms:20-27` — 4-term structure (base + SCM uplift + fallow + treecover) × natural density matches doc §3.1:124-132 exactly; `i59_scm_target` (doc:134), `i59_cratio_fallow`, `i59_cratio_treecover`, `i59_cratio_scm` all declared in M59. CORRECT.
- **q59_som_pool** at `modules/59_som/cellpool_jan23/equations.gms:46-52` — lossrate × target + (1-lossrate) × Σ(land_from) density × lu_transitions. CORRECT.
- **i59_lossrate** `=1-0.85**m_yeardiff(t)` at `modules/59_som/cellpool_jan23/preloop.gms:45` — CORRECT. Doc §5.2 table (5yr→56%, 10yr→80%, 20yr→96%) is mathematically correct (1-0.85^n); the doc is MORE precise than the code comment at preloop.gms:42 which loosely says "44% in 5 years" (44% = remaining legacy 0.85^5, not convergence).
- **Pasture/managed-forest no-change assumption** at `modules/59_som/cellpool_jan23/realization.gms:21-24` (@limitations) — CORRECT.
- **vm_nr_som** (M59 decl:45, Mt N/yr) consumed by **M51** (`51_nitrogen/rescaled_jan21/equations.gms`) — CORRECT.
- **vm_cost_scm** (M59 decl:41, mio USD17MER/yr) consumed by **M11** (`11_costs/default/equations.gms`) — CORRECT.
- **vm_area←M30**, **vm_fallow←M29**, **vm_treecover←M29**, **vm_lu_transitions←M10** — all declaration sites CONFIRMED.
- **fm_carbon_density**, **pm_carbon_density_plantation_ac/secdforest_ac/other_ac** declared in M52 (declarations.gms:9,11,12) — CORRECT names.
- **c52_carbon_scenario** cc/nocc/nocc_hist at `modules/52_carbon/normal_dec17/input.gms:22-23`; default "cc" (default.cfg:1569) — CORRECT.
- **f52_growth_par.csv** at `input.gms:37-43` — CORRECT.
- **pm_climate_class(j,clcl)** from Module 45 (`45_climate/static/input.gms:10`, a `table`) — CORRECT (doc §6.2:464). [Verified via second method after declarations.gms grep returned empty — it's a `table`, not in declarations.gms.]
- **youngsecdf vegc>20 tC/ha** maturation threshold at `modules/35_natveg/pot_forest_may24/presolve.gms:117` (hardcoded `> 20`), documented at presolve.gms:111 — CORRECT (doc §3.6:238-241; set member `youngsecdf` exact).
- **ac age-class set** ac0..ac300,acx (`core/sets.gms:269-275`) — doc §3.5:222 uses correct ellipsis, no truncation.
- **M53 methane** default `ipcc2006_aug22` (default.cfg:1583); four CH4 sources awms/rice/ent_ferm/resid_burn in emis_annual — CORRECT. **vm_feed_intake(i,kap,kall)←M70** CONFIRMED.
- **M57 maccs** default `on_aug22` (default.cfg:1822); `im_maccs_mitigation(t,i,emis_source,pollutants)` (on_aug22/preloop.gms:46), `vm_maccs_costs(i,factors)` (on_aug22) — CORRECT.
- **urban soilc = other-land soilc** at `modules/52_carbon/normal_dec17/input.gms:35` — CORRECT (doc §3.7:252).

---

## Deferred (not code-verifiable / too fine to flag)

- §3.7 attributes urban vegc/litc zeroing to "Module 52" in the table Module column. The actual stock-zeroing is M34 (`vm_carbon_stock.fx`); M52 supplies densities (and fixes urban soilc to other-land). The split-attribution is defensible at this granularity — not flagged.
- §7.2:537 still uses the simplified `v59_som_target = Σ(crops) Area × C_ratio × Natural_density` shorthand that §3.1:134 explicitly says was superseded by the 4-term form. Internal-consistency nit in labeled "Key Equations" context, not a code-vs-doc error. Not flagged as a code bug.
- §3.1:140 / §5.3:420 call the irrigation effect "optional, controlled by `c59_irrigation_scenario`" without stating its default ("on", default.cfg:1935). Mild MANDATE-4 caveat gap but the doc does not assert it is OFF, so no false claim. Not flagged.
- All §4-§8 numerical examples are explicitly labeled "illustrative / made-up numbers" — not code-checkable, correctly caveated.
- §8.4 uses `s59_scm_target = 0.5` as a labeled scenario intervention; the actual default is 0 (default.cfg:1957). Because it is presented as a scenario knob, not a claimed default, it is not a bug. The doc never asserts 0.5 is the default.

---

## Summary

3 Major + 1 Minor, all reproducible. The Major cluster is the §7.5 `vm_carbon_stock` populator set (M30 mis-attributed as direct provider when M29 aggregates it — R24/MANDATE-17 anchor; M29 and M34 omitted — R20/MANDATE-13) and the §7.2/§2.3 soil-carbon assembly attributed to M52 when M59's q59_carbon_soil writes the soilc slice. Everything else (equations, set citations, realization + scalar defaults, the G2 vm_carbon_stock declaration, and the other producer/consumer claims) verifies clean.
