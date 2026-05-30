# Round 34 Doc Audit — module_35.md (Natural Vegetation / NatVeg)

**Auditor**: adversarial doc-vs-code (Opus, highest capability)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_35.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), default realization `pot_forest_may24`, `config/default.cfg`
**Default realization confirmed**: `cfg$gms$natveg <- "pot_forest_may24"` (config/default.cfg) — single realization dir under `modules/35_natveg/`. Doc correct.

## Overall Verdict: MOSTLY ACCURATE (high band)
## Accuracy Score: 8/10

This is an unusually clean doc. All 32 equation file:line citations verified exact; all presolve/preloop citations verified exact; all scalar/switch defaults verified against `input.gms`; all harvest-cost values correct; all external consumer/provider citations for the 2026-04-20 carbon-density refactor (M14:44, M29:46, M32:59, M52 decl:9-11) verified exact and to the correct (default) realizations. The equation count (32) is correct everywhere. The 2026-04-20 natural-origin tracking section (5.1) is faithful to `presolve.gms` and `postsolve.gms`.

The defects are: (1) one wrong member in the strict "direct consumer" set (M59) — the highest-severity finding; (2) an internal contradiction between two "Provides To" lists; (3) a phantom input variable (`pm_land_start`); (4) stale file-size metadata in §6/§10/§14 (correct values present in the Quick Reference); (5) one citation to a non-default M29 realization.

---

## Checker-lead disposition (verify-each, applied)

The pre-run advisory flagged two leads. Both **REFUTED** as written (the doc does not make the claims the checker inferred):

- **module_35.md:9 — "lists M52 as consumer of `p35_carbon_density_secdforest` and `p35_secdforest_natural`"**: REFUTED. Doc line 9 says the FRA-calibrated curve is *from* Module 52 (M52 *provides* `pm_carbon_density_secdforest_ac`); the `p35_*` parameters are described as M35-internal new parameters, NOT consumed by M52. Confirmed `p35_carbon_density_secdforest`, `p35_secdforest_natural`, `pc35_secdforest_natural` have **zero consumers outside M35** (`rg -ln ... | grep -v 35_natveg` → NONE). No bug.
- **module_35.md:917 — "lists M22 for `v35_secdforest` and `vm_land_other`"**: REFUTED. Doc line 917 lists `v35_secdforest`/`vm_land_other` as M35's *own* residual land types and separately says conservation targets are "enforced via Module 22" (i.e., M35 reads `pm_land_conservation` FROM M22). It does not claim M22 consumes `v35_secdforest`/`vm_land_other`. Confirmed `v35_secdforest` has zero external consumers; `vm_land_other` is consumed outside M35 only in the **non-default** `59_som/static_jan19`. No bug at line 917.

Additional consumer-set re-derivation (the checker's real concern) DID surface a separate bug at **line 25** (M59) — see B1.

---

## Consumer/provider sets — re-derived from code (default realizations)

Method: for each M35-owned interface variable, `rg -ln 'NAME\('` AND `rg -ln 'NAME\.'` (solution-level), minus `35_natveg`; positive controls run in each target dir.

| M35-owned var | Declared | Direct consumers OUTSIDE M35 (default) |
|---|---|---|
| `vm_prod_natveg` | M35 decl:88 | **M73** (73_timber/default/equations.gms) |
| `vm_cost_hvarea_natveg` | M35 decl:89 | **M11** (11_costs/default/equations.gms) |
| `vm_natforest_reduction` | M35 decl:90 | **M32** (32_forestry/dynamic_may24/equations.gms) |
| `vm_landdiff_natveg` (scalar) | M35 decl:79 | **M10** (10_land/landmatrix_dec18/equations.gms:53) |
| `pm_max_forest_est` | M35 decl:27 | **M32** (32_forestry/dynamic_may24 equations.gms + presolve.gms) |
| `vm_land_other` | M35 decl:78 | **M59 only in non-default `static_jan19`**; default `cellpool_jan23` does NOT read it |

So the TRUE strict direct-consumer set (M35-owned vars, default config) = **{M10, M11, M32, M73}**.

Shared/aggregate variables M35 POPULATES (not owns): `vm_land` (decl M10:19), `vm_carbon_stock` (decl M56:34 — G2 distinction confirmed), `vm_bv` (decl M44:11), `vm_landexpansion` (decl M10). M52 reads `vm_carbon_stock`; M56 reads `vm_carbon_stock`; M59 reads `vm_land` + `vm_carbon_stock` — none read an M35-owned variable. M22/M28 read no M35-owned variable (positive control: vm_carbon_stock IS found in M56 → grep works).

---

## Bugs Found

### B1 — M59 wrongly listed as a strict direct consumer of M35-owned interface variables
- **Severity**: Major  (tier_uncertainty: false)
- **Trigger** (§1 Major): "Wrong variable prefix / wrong direct-consumer attribution" — aligns with MANDATE 17 worked example (module_30.md:360 phantom-direct M52/M56, scored Major). Not Critical: SOM↔natveg coupling is genuinely real via M10's `vm_land`, so no wrong-file-edit cascade.
- **Class**: 15 (latent doc error / wrong consumer set) ; MANDATE 17.
- **doc_line**: module_35.md:25
- **Claim in doc**: "**Provides to**: Modules 10 (land), 11 (costs), 32 (forestry), **59 (SOM)**, 73 (timber) — direct consumers of M35 interface variables (`vm_land_other`, `vm_prod_natveg`, `vm_cost_hvarea_natveg`, `vm_natforest_reduction`, `vm_landdiff_natveg`, `v35_*`), verified 2026-05-23 R3 ..."
- **Reality in code**: In the default M59 realization (`cellpool_jan23`), M59 reads NONE of the listed variables. It reads `vm_land` (M10-owned, decl 10_land:19), `vm_lu_transitions` (M10-owned), and `vm_carbon_stock` (M56-owned, decl 56:34). The only M59 read of an M35-owned var (`vm_land_other`) is in the **non-default** `static_jan19` realization. By the same strict "M35-owned variable" rule the doc uses to *exclude* M52/M56 on the same line, M59 must also be excluded.
- **File evidence**: `modules/59_som/cellpool_jan23/equations.gms:33,51,62,63,73` (reads vm_land / vm_lu_transitions / vm_carbon_stock only); `modules/59_som/static_jan19/equations.gms` (sole `vm_land_other(` hit, non-default).
- **verify_cmd**: `rg -n "vm_land_other|vm_prod_natveg|vm_natforest_reduction" /tmp/magpie_develop_ro/modules/59_som/cellpool_jan23/*.gms` → (no output / exit 1) ; `rg -ln "vm_land_other\(" /tmp/magpie_develop_ro/modules/ -g "*.gms" | grep -v 35_natveg` → `modules/59_som/static_jan19/equations.gms` ; positive control `rg -c pcm_land .../35_natveg/.../presolve.gms` → 19 (grep works).
- **confirmed**: true
- **Proposed fix**: Remove M59 from the line-25 strict direct-consumer list, OR qualify it. Replace "Modules 10 (land), 11 (costs), 32 (forestry), 59 (SOM), 73 (timber)" with "Modules 10 (land), 11 (costs), 32 (forestry), 73 (timber)". If retaining a SOM mention, add: "Module 59 (SOM) reads natveg areas indirectly via `vm_land` (M10-owned), and only the non-default `static_jan19` realization reads `vm_land_other` directly — not a direct consumer of an M35-owned variable under default config."

### B2 — Internal contradiction between the two "Provides To" lists (§Quick-Ref vs §Dependency-Chains)
- **Severity**: Minor  (tier_uncertainty: true — could be folded into B1)
- **Trigger** (§1 Minor): wrong detail a careful reader would notice; not action-causing because each list is individually near-defensible.
- **Class**: 7 (internal cross-reference inconsistency).
- **doc_line**: module_35.md:937 (vs module_35.md:25)
- **Claim in doc**: line 937 "**Provides To**: Module 10 (Land), Module 11 (Costs), **Module 22** (Conservation - eligible restoration area), Module 32 (Forestry...), **Module 52** (Carbon...), **Module 56** (GHG policy - avoided deforestation potential), Module 73 (Timber...)" — 7 modules incl. M22/M52/M56, and OMITS M59. Line 25 lists 5 modules incl. M59 and explicitly EXCLUDES M22/M52/M56.
- **Reality in code**: M22 reads no M35-owned var (coupling is M22→M35 via `pm_land_conservation`, decl 22:15, plus M35's restoration write-back). M52/M56 read `vm_carbon_stock` (M56-owned), which M35 populates — a one-hop/populator relationship, not direct M35-owned consumption. So line 937 uses a looser data-flow framing (defensible for M52/M56 as "M35 contributes the natveg carbon stocks they price") while line 25 uses strict owned-variable framing; the two lists disagree on membership (M22/M52/M56 vs M59).
- **File evidence**: `modules/56_ghg_policy/price_aug22/equations.gms:13,22` (reads vm_carbon_stock, not any M35-owned var); `modules/22_land_conservation/area_based_apr22/declarations.gms:15` (pm_land_conservation is M22→M35).
- **verify_cmd**: `rg -n "vm_land_other|vm_prod_natveg|vm_natforest_reduction|pm_max_forest_est|vm_cost_hvarea_natveg|vm_landdiff_natveg" /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/*.gms` → all NONE; positive control `rg -n vm_carbon_stock .../56.../equations.gms` → lines 13,22.
- **confirmed**: true
- **Proposed fix**: Reconcile the two lists to one framing. Recommended: at line 937 add the direct-vs-populator distinction so it matches line 25's strict claim, e.g. "**Direct consumers of M35-owned variables**: M10, M11, M32, M73. **Populator relationship** (M35 contributes to a variable owned/read elsewhere): M52 + M56 via `vm_carbon_stock` (M56-owned); M44 via `vm_bv` (M44-owned). M22 is upstream (provides `pm_land_conservation` to M35)." Ensure M59 is treated identically in both lists.

### B3 — Phantom input variable `pm_land_start` in "Receives From Module 10"
- **Severity**: Minor  (tier_uncertainty: true — Major-leaning: it is a named interface variable the module never reads)
- **Trigger** (§1 Minor): wrong detail recoverable — the *concept* (M35 receives initial land from M10) is correct; the named variable is wrong and a reader checking M35's files won't find it.
- **Class**: 2/13 (fabricated-interface name in a dependency set).
- **doc_line**: module_35.md:894
- **Claim in doc**: "**From Module 10 (Land)**: `vm_lu_transitions(j,land_from,land_to)` ... `pm_land_start(j,land)` - Initial land areas"
- **Reality in code**: `pm_land_start` is a real M10 variable (decl `10_land/landmatrix_dec18/declarations.gms`; consumed by M14/M32/M59/M71) but is **never referenced anywhere in M35**. M35 obtains initial/previous-timestep land from M10 via `pcm_land(j,land)` (used 19× in presolve.gms; e.g. lines 39,159,258).
- **File evidence**: absence in `modules/35_natveg/pot_forest_may24/*.gms`; `pcm_land` present at e.g. presolve.gms:39,131,159,258.
- **verify_cmd**: `grep -rn "pm_land_start" /tmp/magpie_develop_ro/modules/35_natveg/` → exit 1 (no match); `rg -l "pm_land_start" .../35_natveg/` → exit 1; positive control `rg -c pcm_land .../presolve.gms` → 19.
- **confirmed**: true
- **Proposed fix**: At line 894 replace `pm_land_start(j,land)` with `pcm_land(j,land)` — Previous-timestep land areas (updated each step; M35's actual M10-provided initial/carry-over land). Or delete the `pm_land_start` bullet.

### B4 — Stale file-size metadata in §6/§10/§14 (correct values present in Quick Reference)
- **Severity**: Minor
- **Trigger** (§1 Minor): off-by metadata a reader doesn't act on; the equation COUNT (32) is correct everywhere.
- **Class**: 6 (hardcoded counts drift) — but counts here are cosmetic file sizes, not structural.
- **doc_line**: module_35.md:982, 1139, 1154-1156, 362
- **Claim in doc**: §10 line 982 "1,085 lines across 9 files"; §14 line 1139 "1,085 lines"; line 1154 "presolve.gms (262 lines)"; line 1155 "equations.gms (229 lines)"; line 1156 "postsolve.gms (203 lines)"; §6 line 362 "32 equations in `equations.gms` (229 lines)".
- **Reality in code**: `wc -l` → presolve **294**, equations **233**, postsolve **210**, declarations **143**; 9-file total **1,165** (= header line 5 and Quick Reference lines 43-52, which are all CORRECT). So the doc is internally inconsistent: Quick Reference right (294/233/210), §6/§10/§14 stale (229/262/203, total 1,085).
- **File evidence**: `wc -l modules/35_natveg/pot_forest_may24/{presolve,equations,postsolve,declarations}.gms` → 294 / 233 / 210 / 143.
- **verify_cmd**: `wc -l /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/*.gms` → presolve 294, equations 233, postsolve 210, declarations 143, total 1165.
- **confirmed**: true
- **Proposed fix**: §10 line 982 "1,085 lines" → "1,165 lines"; §14 line 1139 "1,085 lines" → "1,165 lines"; line 1154 "(262 lines)" → "(294 lines)"; line 1155 "(229 lines)" → "(233 lines)"; line 1156 "(203 lines)" → "(210 lines)"; §6 line 362 "(229 lines)" → "(233 lines)".

### B5 — Citation to non-default M29 realization for `vm_lu_transitions` consumer
- **Severity**: Minor
- **Trigger** (§1 Minor): "stale realization citation that's recoverable (correct concept, findable in a different location)".
- **Class**: 8/10 (realization/citation drift).
- **doc_line**: module_35.md:411
- **Claim in doc**: "`vm_lu_transitions` (... also consumed by Module 29 `modules/29_cropland/simple_apr24/equations.gms:49`, Module 59 `modules/59_som/cellpool_jan23/equations.gms:51`)"
- **Reality in code**: M29 default realization is `detail_apr24` (config line 795 `cfg$gms$cropland <- "detail_apr24"`), NOT `simple_apr24`. The `vm_lu_transitions` consumer line in the DEFAULT realization is `detail_apr24/equations.gms:60` (`q29_land_snv_trans`, identical content). The cited `simple_apr24/equations.gms:49` is the same equation in the non-default realization (content correct, realization wrong). The M59 half (`cellpool_jan23/equations.gms:51`) is correct and default.
- **File evidence**: `modules/29_cropland/detail_apr24/equations.gms:60`; cited `modules/29_cropland/simple_apr24/equations.gms:49`.
- **verify_cmd**: `grep -F 'cfg$gms$cropland' config/default.cfg` → `detail_apr24`; `rg -n vm_lu_transitions .../29_cropland/detail_apr24/equations.gms` → line 60; `.../simple_apr24/equations.gms` → line 49.
- **confirmed**: true
- **Proposed fix**: At line 411 change `modules/29_cropland/simple_apr24/equations.gms:49` to `modules/29_cropland/detail_apr24/equations.gms:60` (the default realization). Consumer attribution (M29 consumes vm_lu_transitions) is correct either way.

---

## Verified-correct (high-value spot checks — NOT bugs)

- **32-equation count**: equations.gms defines 32 `q35_*` equations (31 with `(idx)..` + `q35_landdiff ..` scalar, line 92); declarations.gms declares 32. Doc "32 equations" correct.
- **All 32 equation file:line citations** (§6.1-§6.10): exact match (q35_land_secdforest:11, q35_land_other:13, q35_natveg_conservation:19-22, q35_secdforest_restoration:24-28, q35_other_restoration:30-33, q35_carbon_primforest:42-44, q35_carbon_secdforest:49-51, q35_carbon_other:53-55, q35_bv_primforest:59-61, q35_bv_secdforest:63-66, q35_bv_other:68-71, q35_min_forest:78-80, q35_min_other:82, q35_natforest_reduction:84-85, q35_landdiff:92-98, q35_other_expansion:100-102, q35_other_reduction:104-106, q35_secdforest_expansion:108-110, q35_secdforest_reduction:112-114, q35_primforest_reduction:116-118, q35_cost_hvarea:132-138, q35_prod_secdforest:144-147, q35_prod_primforest:153-156, q35_prod_other:162-168, q35_hvarea_secdforest:176-179, q35_hvarea_primforest:181-184, q35_hvarea_other:186-189, q35_max_forest_establishment:196-201, q35_secdforest_regeneration:208-214, q35_other_regeneration:218-223, q35_secdforest_est:228-229, q35_other_est:231-232). All formulas quoted verbatim correctly.
- **All presolve citations** verified exact: disturbance modes (13-16, 18-22, 24-27, 29-33), distribution (35-39), recovery (48-78 incl. steps 53,58,64-66,78), age shift (84-97, 87-90, 99-102), maturation (109-122, 116-122), bounds (143-145 comment, 155-160, 172-180, 175-180, 258-260, 262-266, 268-272, 274-282), carbon density blend (241-242, 248-252), natural-origin (42-45 with 1e-6, 127-128).
- **All defaults** (MANDATE 3, vs input.gms): s35_forest_damage=2 (input:27), s35_hvarea=2 (input:18), s35_natveg_harvest_shr=1 (input:25), s35_secdf_distribution=2 (input:26), s35_npi_ndc_reversal=Inf (input:29), c35_ad_policy=npi (input:8), c35_shock_scenario=none (input:10), c35_pot_forest_scenario=cc (input:12), s35_forest_damage_end=2050 (input:28).
- **Harvest costs** (input:22-24): secdforest 2460, other 3075, primforest 3690 USD17MER/ha — exact.
- **2026-04-20 carbon-density refactor external citations** — all exact and to DEFAULT realizations: `pm_carbon_density_secdforest_ac` decl 52_carbon/normal_dec17/declarations.gms:9, consumed M14 managementcalib_aug19/presolve.gms:44; `pm_carbon_density_secdforest_ac_uncalib` decl 52:10, consumed M29 detail_apr24/preloop.gms:46, M32 dynamic_may24/presolve.gms:59 (+68 NDC, not over-claimed); `pm_carbon_density_other_ac` decl 52:11. M52=normal_dec17, M32=dynamic_may24, M29=detail_apr24, M59=cellpool_jan23 all confirmed default.
- **G2 distinction honored**: `vm_carbon_stock` declared in M56 (decl:34); M35 POPULATES it via q35_carbon_* (49-51 etc.); M52 READS it. Doc frames M35 as providing carbon stocks (populator→reader), consistent with G2 anchor.
- **`im_growing_stock`** decl M14 managementcalib_aug19/declarations.gms:17 ("Harvestable stem biomass per ha by age class (tDM per ha)") — doc's M14 attribution + stock semantics correct.
- **Sets**: othertype35 {othernat, youngsecdf} sets.gms:23-24; combined_loss {shifting_agriculture, wildfire} sets.gms:14-15; shock_scen sets.gms:26-28 — all exact.
- **realization.gms:35-36** (primforest→secdforest one-way; secdforest stays secdforest) and **module.gms:10-15** (core purpose) — exact.
- **20 tC/ha maturation** now uses `pm_carbon_density_secdforest_ac_uncalib` (presolve:117) — doc §2.2 change-note correct.

---

## Deferred (NOT code-verifiable / out of scope — no edit)

- Centrality "Rank 10 of 46", "12 connections (provides to 5, depends on 7)" (lines 933-934, 1145): derived from cross_module dependency-graph analysis, not directly checkable from M35 code. Note the "provides to 5 / depends on 7" counts are themselves inconsistent with both §Quick-Ref (5 provides) and §937 (7 provides) lists; flagged conceptually under B1/B2 but the rank/connection integers are not code-verifiable here.
- "Largest carbon stocks in model" / "dominant carbon pool" (lines 919, 976): empirical model-output claim, not a code fact.
- Circular-dependency cycle descriptions (§ lines 947-961) and modification-safety risk narrative (§ 965-984): qualitative, cross_module-sourced.
- BII coefficient value "primary = 1.0" (line 473): depends on input data `fm_bii_coeff` (.cs* input), not readable here.
- Chapman-Richards form `vegc(age)=A*(1-exp(-k*age))^m` (line 919): this growth curve lives in Module 52 (carbon), not M35; correctness is a Module-52 concern, out of this doc's verifiable scope.

---

## Summary
module_35.md is highly accurate on the load-bearing surface (32 equations, all citations, all defaults, the 2026-04-20 carbon-density refactor). One Major: M59 wrongly in the line-25 strict direct-consumer set (default cellpool_jan23 reads no M35-owned var; coupling is via M10 `vm_land`). Four Minor: §Quick-Ref↔§937 "Provides To" contradiction; phantom `pm_land_start` input (should be `pcm_land`); stale file sizes in §6/§10/§14 (Quick Reference is correct); a vm_lu_transitions citation to the non-default M29 `simple_apr24`. Both pre-run checker leads (line 9, line 917) REFUTED.
