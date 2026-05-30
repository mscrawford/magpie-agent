# Adversarial doc audit — module_35.md (Natural Vegetation)

**Auditor**: Opus 4.8 (1M ctx), round35_docaudits
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_35.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Default realization (verified)**: `pot_forest_may24` — `config/default.cfg:1135` (`cfg$gms$natveg <- "pot_forest_may24"`). Doc covers the correct (default) realization.

---

## Scope

Verified every load-bearing code-checkable claim: 32 equation names + line citations, ~40 presolve/preloop/postsolve/input/sets/realization citations, parameter defaults, the Section 5.1 natural-origin refactor, interface-variable producer/consumer sets, and set ranges. Most of the doc is accurate; the equation citations and the Section 5.1 refactor documentation are essentially flawless. Five confirmed bugs plus internal-consistency issues below.

---

## CHECKER LEADS — both REFUTED

**Lead 1 (module_35.md:9 → M52 consumer of `p35_carbon_density_secdforest` / `p35_secdforest_natural`)**: REFUTED. Line 9 says the *FRA-calibrated curve* comes "from Module 52" (true — `pm_carbon_density_secdforest_ac` is M52's). It does NOT claim M52 consumes the `p35_*` params. Verified those params are module-internal (`p35_` prefix) and appear ONLY in M35 files:
- `rg -l 'p35_carbon_density_secdforest' /tmp/magpie_develop_ro/modules/ --glob '*.gms'` → only 3 M35 files (declarations/presolve/equations).
- `rg -n 'p35_carbon_density_secdforest|p35_secdforest_natural' /tmp/magpie_develop_ro/modules/52_carbon/` → NO MATCH IN M52.

**Lead 2 (module_35.md:917 → M22 consumer of `v35_secdforest` / `vm_land_other`)**: REFUTED. Line 917 says conservation targets are "enforced via Module 22" (i.e., M35 *receives* `pm_land_conservation` from M22). It does not claim M22 reads those vars. Verified M22 (`area_based_apr22`, default per `config/default.cfg:714`) references none of M35's interface vars; positive control: `pm_land_conservation` IS declared in `modules/22_land_conservation/area_based_apr22/declarations.gms:15`.

---

## BUGS

### BUG 1 — Critical — Age-class range truncation (Pattern 11 / R16 immutable anchor)

- **doc_line**: module_35.md:133-134
- **Claim**: "`ac0`, `ac5`, `ac10`, ..., `ac150`, `acx` (mature, > 150 years)"
- **Reality**: The authoritative `ac` set in `core/sets.gms:269-275` is `ac0, ac5, ..., ac295, ac300, acx` — 62 elements, last numbered class **ac300**, so `acx` is > 300 years (not > 150).
- **file_evidence**: `core/sets.gms:269-275`
- **verify_cmd**: `grep -n -A8 'ac Age classes' /tmp/magpie_develop_ro/core/sets.gms` → `/ ac0,ac5,...,ac295, ac300, acx /`
- **Trigger**: §1 Critical — this is the exact R16 immutable anchor ("agent claimed age classes go to ac140, acx; actual set extends to ac300 (62 elements) → Critical, downstream calculations off by ~2× in element count"). Doc truncates at ac150 (~half the real range) and mis-states the acx threshold.
- **confirmed**: true
- **proposed_fix**: Replace line 134 bullet with: "`ac0`, `ac5`, `ac10`, ..., `ac295`, `ac300`, `acx` (62 age classes; `acx` is the mature/absorbing class, > 300 years). Defined in `core/sets.gms:269-275`."

### BUG 2 — Major — Wrong consumer attribution for `vm_natforest_reduction` (MANDATE 17 / Pattern 12)

- **doc_line**: module_35.md:655
- **Claim**: "This interface variable is provided to other modules (e.g. Module 73 timber)." (re: `vm_natforest_reduction`)
- **Reality**: The sole direct consumer of `vm_natforest_reduction` is **Module 32 (forestry)** — `modules/32_forestry/dynamic_may24/equations.gms:80` (`q32_aff_pol`: `sum(ct, p32_aff_pol_timestep(ct,j2)) * vm_natforest_reduction(j2) =e= 0;`). M73 does NOT reference `vm_natforest_reduction` at all (positive control: M73 references `vm_prod_natveg` 5×).
- **file_evidence**: `modules/32_forestry/dynamic_may24/equations.gms:80`
- **verify_cmd**: `rg -n 'vm_natforest_reduction' /tmp/magpie_develop_ro/modules/32_forestry/` → equations.gms:80 ; `rg -n 'vm_natforest_reduction' /tmp/magpie_develop_ro/modules/73_timber/` → NOT IN M73
- **Trigger**: §1 Major — wrong consumer set; would mislead modification-safety reasoning (a user editing `vm_natforest_reduction` would look at M73, not the M32 afforestation-policy constraint).
- **confirmed**: true
- **proposed_fix**: Change "provided to other modules (e.g. Module 73 timber)" → "consumed by Module 32 (forestry): `modules/32_forestry/dynamic_may24/equations.gms:80`, where the afforestation-policy constraint `q32_aff_pol` forces `vm_natforest_reduction = 0` when afforestation policy is active."

### BUG 3 — Major — Phantom input `pm_land_start` (Pattern 12 / phantom dependency)

- **doc_line**: module_35.md:894
- **Claim**: "From Module 10 (Land): ... `pm_land_start(j,land)` - Initial land areas"
- **Reality**: M35 never references `pm_land_start`. Both rg and grep return no match across all M35 files (EXIT=1); positive controls in the same dir: `vm_lu_transitions` (4 hits) and `pcm_land` (19 hits in presolve) confirm the search is valid. (`pm_land_start` IS declared in `modules/10_land/landmatrix_dec18/declarations.gms`, but M35 is not a consumer.)
- **file_evidence**: absent from `modules/35_natveg/pot_forest_may24/*.gms` (declared at `modules/10_land/landmatrix_dec18/declarations.gms`)
- **verify_cmd**: `rg -n 'pm_land_start' /tmp/magpie_develop_ro/modules/35_natveg/ --glob '*.gms'; echo EXIT=$?` → EXIT=1 (no match); `grep -rn 'pm_land_start' /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/` → EXIT=1; positive control `rg -cn 'pcm_land' .../presolve.gms` → 19
- **Trigger**: §1 Major — fabricated dependency in the interface section.
- **confirmed**: true
- **proposed_fix**: Delete the `pm_land_start(j,land)` bullet at line 894. M35's actual M10 input is `vm_lu_transitions(j,land_from,land_to)` (already listed at line 893); the per-timestep land state it reads is the core `pcm_land` (not an M10 interface parameter).

### BUG 4 — Minor — M59 listed as direct consumer without non-default-realization caveat (MANDATE 8)

- **doc_line**: module_35.md:25
- **Claim**: "Provides to: Modules 10 (land), 11 (costs), 32 (forestry), 59 (SOM), 73 (timber) — direct consumers of M35 interface variables (`vm_land_other`, ...)"
- **Reality**: The only M35-declared variable M59 consumes is `vm_land_other`, and ONLY in the **non-default** `static_jan19` realization (`modules/59_som/static_jan19/equations.gms:23-24`). The default SOM realization is `cellpool_jan23` (`config/default.cfg:1916`), which does NOT consume `vm_land_other` or any M35 interface variable (positive control: `vm_land` hits 3× in `cellpool_jan23/equations.gms`, so the dir search works; `vm_land_other` → NOT FOUND).
- **file_evidence**: `modules/59_som/static_jan19/equations.gms:23-24` (consumer); `modules/59_som/cellpool_jan23/` (no consumption)
- **verify_cmd**: `rg -n 'vm_land_other' /tmp/magpie_develop_ro/modules/59_som/cellpool_jan23/` → NOT FOUND; `rg -n 'vm_land_other' /tmp/magpie_develop_ro/modules/59_som/static_jan19/equations.gms` → lines 23-24
- **Trigger**: §1 Minor (tie-break down from Major). The doc's own footnote says this was a grep-based R3 verification that does not distinguish realizations, so it is not a fabrication; but a careful reader running the default config would find M59 does not read any M35 var. Tie-broken to Minor because line 25 is a high-level dependency summary, not a default-behavior mechanism claim.
- **confirmed**: true
- **proposed_fix**: Annotate the M59 entry: "59 (SOM — only in the non-default `static_jan19` realization, via `vm_land_other`; the default `cellpool_jan23` does not consume any M35 interface variable)."

### BUG 5 — Minor — File-size / total-line-count drift (Pattern 6, metadata)

- **doc_line**: module_35.md:362 (and 982, 1139, 1154-1156)
- **Claim**: line 362 "32 equations in `equations.gms` (229 lines)"; line 982 / 1139 "1,085 lines across 9 files"; lines 1154-1156 "presolve.gms (262 lines)", "equations.gms (229 lines)", "postsolve.gms (203 lines)".
- **Reality**: `wc -l` gives equations.gms **233**, presolve.gms **294**, postsolve.gms **210**, total **1,165**. The doc HEADER (lines 43-46, updated in the 2026-05-16 sync) already has the correct 294/233/210/143; these body/footer values are stale pre-sync numbers and now contradict the header.
- **file_evidence**: `wc -l modules/35_natveg/pot_forest_may24/*.gms` → presolve 294, equations 233, postsolve 210, total 1165
- **verify_cmd**: `wc -l /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/*.gms`
- **Trigger**: §1 Minor — line-count metadata a reader does not act on; the equation COUNT (32) is correct everywhere. Internal-consistency cleanup (header is already right).
- **confirmed**: true
- **proposed_fix**: line 362 "(229 lines)" → "(233 lines)"; lines 1154-1156 → presolve 294 / equations 233 / postsolve 210; lines 982 and 1139 "1,085 lines" → "1,165 lines".

---

## INTERNAL-CONSISTENCY NOTES (not separate code bugs; fold into fixes)

- **M52/M56 provides-to contradiction**: line 25 states "Modules 22, 28, 52, 56 do NOT directly consume any M35 interface variable", while line 875-876 lists "To Module 52 (Carbon): `vm_carbon_stock`" and line 937 lists "Provides To: ...52, 56...". Both framings are individually defensible (G2 pattern: `vm_carbon_stock` is DECLARED in M56 `price_aug22/declarations.gms:34`, POPULATED by M35 via `q35_carbon_*`, READ by M52 `normal_dec17/equations.gms:16-19`). The doc just uses two different definitions of "M35 interface variable" in the same document. Recommend one consistent framing: M35 *populates* the shared `vm_carbon_stock`/`vm_bv` (declared in M56/M44 respectively), which M52/M56/M44 then read. This is informational, not a hard code error — no edit required if the line-875 populate-and-read framing is treated as canonical, but the two statements should be reconciled.
- **"provides to 5" vs 7 listed**: line 934 says "Total Connections: 12 (provides to 5, depends on 7)" but line 937 lists 7 provides-to modules (10, 11, 22, 32, 52, 56, 73). The "5 vs 7" stems from the same declared-vs-populated ambiguity (5 modules read M35-*declared* vars; +M52/M56 read the populated `vm_carbon_stock`). Reconcile alongside the M52/M56 note. (Centrality rank "10 of 46" is from an external graph analysis not reproducible from code — deferred.)

---

## VERIFIED-CORRECT (high-value confirmations)

- **All 27 equation file:line citations** in Section 6 match `equations.gms` exactly (q35_land_secdforest:11, q35_carbon_secdforest:49-51, q35_cost_hvarea:132-138, q35_prod_*:144-168, q35_hvarea_*:176-189, q35_secdforest_regeneration:208-214, etc.). 32 equations declared (declarations.gms:42-73) AND 32 defined (`comm -23/-13` diff empty) — count correct.
- **Section 5.1 natural-origin refactor**: every cited line verified — disturbance reduction presolve.gms:42-45; age-shift 99-102; maturation 116-122; safety clamp 127-128; protection lower bound 175-180; blended density 248-252; youngsecdf density 241-242; preloop init 49-50; postsolve 11-16. The `1e-6` threshold matches presolve.gms:44. New params `p35_secdforest_natural`/`pc35_secdforest_natural`/`p35_carbon_density_secdforest` all in declarations.gms:16-17,29.
- **20 tC/ha maturation now uses `pm_carbon_density_secdforest_ac_uncalib`**: presolve.gms:117 (`> 20`) — confirmed.
- **Carbon-density consumer sets (MANDATE 13)**: `pm_carbon_density_secdforest_ac` → M14 `managementcalib_aug19/presolve.gms:44` (verified line content); `pm_carbon_density_secdforest_ac_uncalib` → M29 `detail_apr24/preloop.gms:46` + M32 `dynamic_may24/presolve.gms:59` + M35 itself (all verified). `vm_lu_transitions` extra consumers M29 `simple_apr24/equations.gms:49` + M59 `cellpool_jan23/equations.gms:51` — both verified.
- **Disturbance modes 1-4** (presolve.gms:13-33), distribution (35-39), age progression (84-97), recovery (48-78), harvest control (274-282), harvest share (155-160), age-class restrictions (268-272), protection dist (172-180), NPI/NDC (258-260), reversal (262-266), restoration shift (191-198) — all citations match.
- **Defaults (MANDATE 3)**: `s35_hvarea=2` (input.gms:18), harvest costs 2460/3075/3690 (input.gms:22-24), `s35_natveg_harvest_shr=1` (25), `s35_forest_damage=2` (27), `s35_forest_damage_end=2050` (28), `s35_secdf_distribution=2` (26), `s35_npi_ndc_reversal=Inf` (29), `c35_ad_policy=npi` (8), `c35_shock_scenario=none` (10), `c35_pot_forest_scenario=cc` (12) — all confirmed.
- **`im_growing_stock` provided by M14** (declarations + computed in `managementcalib_aug19/presolve.gms:24,33,42`) — the 2026-04-20 correction is right.
- **Provides-to per-variable**: `vm_prod_natveg`→M73, `vm_cost_hvarea_natveg`→M11, `vm_landdiff_natveg`→M10, `pm_max_forest_est`→M32 — all verified by grep outside M35.
- **realization.gms:35-36** (harvested primf→secdf, secdf stays secdf), **module.gms:10-15** (Section 1) — citations match.
- Header file sizes (lines 43-51) and the 32-equation count are correct.

---

## DEFERRED (not code-verifiable / out of scope — no edit)

- Centrality "Rank 10 of 46" and "12 connections" — derived from an external module-graph analysis, not reproducible from GAMS source.
- Commit-history claims (`1e-12` raised to `1e-6` by refactor `2fa7b8bea`; PR #869 rename of *pm_timber_yield*→`im_growing_stock`) — current code value `1e-6` matches and `im_growing_stock` exists, but the diff lineage cannot be confirmed from the worktree snapshot. Current-state claims verified; history claims left as-is.
- `s35_secdf_distribution=2` label ("Poulter/MODIS" in input.gms:26 comment vs "GFAD" in preloop.gms:19 comment) — the code itself uses both terms; doc's "MODIS/Poulter satellite data (GFAD)" is consistent with the code's own mixed terminology, not a clear error.
- Section 10.1 line 917 "secondary forest (age-classes 1-15)" — same truncation root cause as BUG 1; if BUG 1 is fixed, sweep this line too (informational; "15" likely refers to GFAD's 15 classes, which is a different set `ac_gfad`).
