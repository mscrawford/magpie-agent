# Round 33 Doc Audit — module_14.md (Yields, managementcalib_aug19)

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_14.md` (1578 lines)
**Ground truth**: `/tmp/magpie_develop_ro/modules/14_yields/managementcalib_aug19/*.gms`, `/tmp/magpie_develop_ro/modules/14_yields/module.gms`, `/tmp/magpie_develop_ro/config/default.cfg`, plus cross-module consumer/producer files (M32/M35/M52/M45/M13/M70/M30/M31/M10).

---

## Overall verdict: MOSTLY ACCURATE (high band)

This is a high-quality doc. The load-bearing spine — default realization, equation count, equation formulas, all scalar defaults, all declarations.gms citations, all input.gms read-line citations, the im_growing_stock and vm_yld consumer sets, the f_btc2 cluster-level tau change, the pm_climate_class/M45 dependency, and all four cited commit hashes — is correct. Estimated score 7.5/10 (one Major + three Minor).

The pre-run advisory checker's two specific worries were both **REFUTED**:
- "confirm equations.gms defines EXACTLY 2 equations (q14_yieldcalib does NOT exist)" → CONFIRMED correct: `declarations.gms:30-31` and `equations.gms` define exactly `q14_yield_crop` (eq:14-16) and `q14_yield_past` (eq:35-39). No `q14_yieldcalib` anywhere. (G1 anchor holds.)
- "audit M45 climate-input claims for parameterization-vs-mechanism overstatement" → The M45 dependency claim is CORRECT and not overstated: `pm_climate_class(j,clcl)` is declared in `modules/45_climate/static/input.gms:10` and read directly by M14 `presolve.gms:29,38,47,56`. (This required a Python cross-check — see Note on grep artifact below.)

---

## Claims verified CORRECT (high-value)

| Claim | Doc location | Code evidence | Verdict |
|---|---|---|---|
| Default realization `managementcalib_aug19` | module_14:3, 1225, 1234 | `config/default.cfg:354` `cfg$gms$yields <- "managementcalib_aug19"` | ✅ |
| Only realization is managementcalib_aug19 | module_14:1234 | `ls modules/14_yields/` → `input`, `managementcalib_aug19`, `module.gms` only | ✅ |
| Exactly 2 equations, named q14_yield_crop / q14_yield_past | module_14:6, 39, 992 | `declarations.gms:30-31`; `equations.gms:14,35` | ✅ |
| q14_yield_crop formula | module_14:46-48 | `equations.gms:14-16` verbatim match | ✅ |
| q14_yield_past formula | module_14:88-92 | `equations.gms:35-39` verbatim match | ✅ |
| s14_limit_calib default 1 | module_14:541, 546 | `input.gms:15` `/ 1 /` | ✅ |
| s14_calib_ir2rf default 1 | module_14:321, 555 | `input.gms:16` `/ 1 /` | ✅ |
| s14_degradation default 0 | module_14:390, 565 | `input.gms:17` `/ 0 /` | ✅ |
| s14_use_yield_calib default 0 | module_14:348 | `input.gms:18` `/ 0 /` | ✅ |
| s14_minimum_growing_stock default 5 | module_14:507 | `input.gms:19` `/ 5 /` | ✅ |
| s14_yld_past_switch default 0.25 | module_14:110, 580 | `input.gms:20` `/ 0.25 /` | ✅ |
| s14_yld_reduction_soil_loss default 0.08 | module_14:375, 591 | `input.gms:21` `/ 0.08 /` | ✅ |
| sm_carbon_fraction default 0.5, sm_ prefix | module_14:420, 705 | `input.gms:22` `sm_carbon_fraction ... / 0.5 /` | ✅ |
| c14_yields_scenario default cc | module_14:520 | `input.gms:8`; `default.cfg:360` | ✅ |
| All declarations.gms citations (9,11,13,14,15,16,17,18,26) | Sections 7, 9 | `declarations.gms` lines match exactly | ✅ |
| All input.gms read-line citations (30,37,47,53,61,69,77,85,93) | Section 6 | `input.gms` `$include` lines match exactly | ✅ |
| f14_pyld_hist declared input.gms:45, covers y1965–y2020 | module_14:177, 840 | `input.gms:45`; comment `preloop.gms:19` "y1965–y2020" | ✅ |
| im_growing_stock declared in M14 | module_14:698, 865 | `declarations.gms:17` | ✅ |
| im_growing_stock consumers M32 (q32_prod_forestry, i32_growing_stock_at_harvest, pc32_prod_forestry_ini) | module_14:692 | `32_forestry/dynamic_may24/equations.gms:249`, `presolve.gms:181,185` | ✅ |
| im_growing_stock consumers M35 (q35_prod_secdforest, q35_prod_primforest, q35_prod_other) | module_14:693 | `35_natveg/pot_forest_may24/equations.gms:147,156,165` | ✅ |
| Consumers divide by m_timestep_length_forestry | module_14:403, 695 | M32 eq:249 `/ m_timestep_length_forestry`; M35 eq:147,156,165 same | ✅ |
| vm_yld declared in M14, dims (j,kve,w) | module_14:684 | `declarations.gms:26` | ✅ |
| vm_yld external consumers M30 (croparea) + M31 (past) | module_14:679, 1180 | `30_croparea/simple_apr24/equations.gms:15`, `detail_apr24/equations.gms:15`, `31_past/endo_jun13/equations.gms:18` | ✅ |
| vm_tau / pcm_tau at cluster level (j); f_btc2 commit 480e300b1 | module_14:73, 114, 723 | `13_tc/exo/declarations.gms:9,16` and `endo_jan22:13,27` both `(j,tautype)`; `git show 480e300b1` = "Merge PR #805 from pvjeetze/f_btc2" | ✅ |
| fm_tau1995(h) at super-region level | module_14:70 | `13_tc/exo/input.gms:49` `fm_tau1995(h)` | ✅ |
| pm_past_mngmnt_factor from M70 | module_14:109, 749, 1197 | `70_livestock/fbask_jan16/declarations.gms:41` | ✅ |
| pm_carbon_density_plantation_ac / _secdforest_ac from M52 | module_14:445, 477, 732-733 | `52_carbon/normal_dec17/declarations.gms:12,9` + populated `start.gms:28,...` | ✅ |
| pm_carbon_density_other_ac from M52 (Section 4.2 only) | module_14:493 | declared `52_carbon/normal_dec17/declarations.gms:11`, populated `start.gms:48,51` | ✅ |
| pm_land_start from M10 | module_14:758, 1201 | `10_land/landmatrix_dec18/declarations.gms:9` | ✅ |
| pm_climate_class from M45 | module_14:760, 1366 | `45_climate/static/input.gms:10` `table pm_climate_class(j,clcl)`; read in M14 `presolve.gms:29` | ✅ |
| im_growing_stock presolve formulas (all 4 forest types) | module_14:436-490 | `presolve.gms:24-58` verbatim match | ✅ |
| Growing-stock constraints (>=0.0001; <5 → 0) | module_14:500-501 | `presolve.gms:63,65` verbatim | ✅ |
| nl_fix uses vm_tau.l / pcm_tau at super-region (h) | module_14:880-881 | `nl_fix.gms:10,11` (`vm_tau.l(h,"crop")`, `pcm_tau(h,"crop")`) | ✅ |
| nl_release sets vm_yld.lo=0, .up=Inf | module_14:895-896 | `nl_release.gms:10-11` | ✅ |
| Commit c7731e234 exists | module_14:177, 1577 | `git show c7731e234` exists (see Deferred re: subject) | ✅ (hash) |
| Commit 75d7ee167 (PR #869) exists | module_14:402, 700 | `git show 75d7ee167` = "Forestry module overhaul: BEF/BCEF fix..." | ✅ |
| Commit cc84ae5e1 (biocorrect removal) exists | module_14:1234 | `git show cc84ae5e1` = "Update to new revision and clean up old realizations" | ✅ |
| sets: kcr (19), knbe14 (17), ncp_type14 {soil_intact,poll_suff}, ltype14 {crop,past} | Sections 3.6, 6.7, 6.9 | `sets.gms:8-34` match | ✅ |

---

## Bugs found

### Bug 14-B1 — Wrong source module for pm_carbon_density_other_ac (M35 → actually M52)
- **Severity**: Major
- **Class**: 15 (latent doc error — wrong producer attribution) / overlaps Pattern 4-style cross-module mechanism
- **Trigger (§1 Major)**: "Wrong variable prefix / semantic scope wrong" sibling — here a wrong *source-module* attribution for an interface parameter. Resembles the R20/G2 wrong-producer-set anchor (Critical-prone), pulled down to Major by tie-breaker because the doc's primary technical section (4.2) states the correct source (M52) and a reader has the right answer in the same document.
- **Claim in doc** (module_14.md:739-743): "**From Module 35 (Natural Vegetation):** - **pm_carbon_density_other_ac(t,j,ac,"vegc")**: Other natural land carbon density (tC/ha)". Repeated at module_14.md:1192-1193 (Section 16.3): "**Receives Carbon Density From** - **Module 35 (Natural Vegetation):** Other natural land carbon → timber yields".
- **Reality in code**: `pm_carbon_density_other_ac` is **declared in Module 52** (`modules/52_carbon/normal_dec17/declarations.gms:11`) and **populated in Module 52** (`modules/52_carbon/normal_dec17/start.gms:48,51`). M35 is a *consumer* of it (`35_natveg/pot_forest_may24/presolve.gms:240` reads it into a local p35 parameter), not the source. M14 also reads it (`presolve.gms:53`). The doc's own Section 4.2 (module_14.md:493) correctly states "Source: `pm_carbon_density_other_ac` from Module 52" — so Sections 7.2 and 16.3 contradict Section 4.2.
- **File evidence**: `modules/52_carbon/normal_dec17/declarations.gms:11`; `modules/52_carbon/normal_dec17/start.gms:48`.
- **verify_cmd**: `python3` walk for substring `pm_carbon_density_other_ac` →
  - declared: `52_carbon/normal_dec17/declarations.gms:11`
  - populated (`= m_growth_vegc(...)`): `52_carbon/normal_dec17/start.gms:48,51`
  - read-only: `14_yields/.../presolve.gms:53`, `35_natveg/pot_forest_may24/presolve.gms:240`
  Positive control: sibling `pm_carbon_density_secdforest_ac` populator confirmed in M52 `start.gms:28`.
- **confirmed**: true
- **proposed_fix**: In Section 7.2 (module_14.md:739-743), move `pm_carbon_density_other_ac` under the existing "**From Module 52 (Carbon):**" block (alongside plantation/secdforest), and delete the "From Module 35 (Natural Vegetation)" subsection (or relabel it to note M35 only provides land-pool context, not carbon density). In Section 16.3 (module_14.md:1190-1193), change "Module 35 (Natural Vegetation): Other natural land carbon → timber yields" to "Module 52 (Carbon): Other natural land carbon density (`pm_carbon_density_other_ac`) → timber yields". This makes 7.2/16.3 consistent with the already-correct Section 4.2.

### Bug 14-B2 — Preloop Stage line-citations drifted ~7-8 lines (Section 3)
- **Severity**: Minor
- **Class**: 10 (stale file:line citation)
- **Trigger (§1 Minor)**: "Off-by-few line citation where adjacent lines say similar things." Systematic downward shift; the cited code remains within a few lines of the cited range, so a careful reader finds it.
- **Claim in doc**: Section 3 cites preloop ranges that no longer align with current code:
  - 3.3 Step3a "preloop.gms:60-66" (module_14.md:193, 213) — actual `i14_modeled_yields_hist` assignment at **67-73** (lines 60-66 = `i14_croparea_total` + comment).
  - 3.3 Step3b "preloop.gms:75-95" / "preloop.gms:69-95" (module_14.md:217, 251) — actual `loop(t,...)` lambda block at **82-102**.
  - 3.3 Step3c "preloop.gms:101-109" (module_14.md:255, 280) and Section 9 "preloop.gms:101-105" (module_14.md:822) — actual `i14_managementcalib` formula at **108-112**, `i14_yields_calib`/`pm_yields_semi_calib` at **115-116**.
  - 3.4 "preloop.gms:116-143" (module_14.md:286, 323) and "lines 130-140" (module_14.md:306, 317, 319, 951) — actual `if((s14_calib_ir2rf=1)` block at **123-150**; the second FAO recalibration is at **137-147**.
  - 3.5 "preloop.gms:150-167" (module_14.md:329, 350) — actual yield-calib block: header at **155**, `if(s14_use_yield_calib...)` at **165**, multiply assignments at **170-173**.
  - 3.6 "preloop.gms:170-188" / "preloop.gms:171-188" (module_14.md:356, 394) — actual `if((s14_degradation=1)` block at **190-195** (the cited range ENDS at 188, before the degradation block begins — the most material of the set).
- **Reality in code**: Code shifted down ~7-8 lines relative to the doc's line numbers (added comment block in the 2026-04-20 pasture rewrite + 2026-05-16 sync). Section anchors and shown code blocks are otherwise correct.
- **File evidence**: `modules/14_yields/managementcalib_aug19/preloop.gms` lines 67-73 (modeled yields), 82-102 (lambda loop), 108-116 (managementcalib + apply), 123-150 (ir2rf if), 155-173 (yield calib), 190-195 (degradation if).
- **verify_cmd**: `sed -n` on each cited range vs the assignment locations (transcript above). E.g. `sed -n '170,196p' preloop.gms` shows the degradation `if` opens at line 190, outside the cited 170-188.
- **confirmed**: true
- **proposed_fix**: Re-number the Section 3 preloop citations to current develop: 3.3 Step3a → `preloop.gms:60-73` (or `67-73` for the equation); 3.3 Step3b → `preloop.gms:82-102`; 3.3 Step3c → `preloop.gms:108-116` (and Section 9 i14_managementcalib "Computed in" → `preloop.gms:108-112`); 3.4 → `preloop.gms:123-150` (second recalibration "lines 137-147"); 3.5 → `preloop.gms:155-173`; 3.6 → `preloop.gms:186-195` (degradation `if` at 190-195). Verify with `scripts/check_gams_citations.sh` after editing.

### Bug 14-B3 — pm_yields_semi_calib "Set at: preloop.gms:109,142" drifted (Section 7.1)
- **Severity**: Minor
- **Class**: 10 (stale file:line citation)
- **Trigger (§1 Minor)**: off-by-7 citation; the cited lines point at mid-formula content (109 = inside i14_managementcalib; 142 = inside i14_modeled_yields_hist2 dual-condition), so a careful reader would notice and look nearby.
- **Claim in doc** (module_14.md:713): "**Set at:** `preloop.gms:109,142`".
- **Reality in code**: `pm_yields_semi_calib(j,knbe14,w) = i14_yields_calib("y1995",...)` is assigned at `preloop.gms:116` and `preloop.gms:149`.
- **File evidence**: `modules/14_yields/managementcalib_aug19/preloop.gms:116,149`.
- **verify_cmd**: `rg -n "pm_yields_semi_calib" preloop.gms` → `116:`, `149:`.
- **confirmed**: true
- **proposed_fix**: Change "Set at: `preloop.gms:109,142`" to "Set at: `preloop.gms:116,149`".

### Bug 14-B4 — Module 30 mislabeled "Crop" instead of "croparea"
- **Severity**: Minor
- **Class**: 6 (characterization drift) — module number correct, name wrong; internally inconsistent.
- **Trigger (§1 Minor)**: "Module renamed but old name still readable" sibling — the number (30) and the consumer relationship are correct; only the human-readable name is wrong, and other sections of the same doc use the correct "croparea".
- **Claim in doc**: "Module 30 (Crop)" at module_14.md:680, 787, 1180 (and "30_crop" tone in Section 1.1 line 17). Internally inconsistent with module_14.md:1180 vs Section 16.2 line 1370 ("Module 30 (croparea)") and Section 21.2 line 1370.
- **Reality in code**: The module is `30_croparea`; config key is `cfg$gms$croparea <- "simple_apr24"` (`config/default.cfg:896`). There is no `30_crop` module. (CLAUDE.md QUICK MODULE FINDER also lists "30 (croparea)".)
- **File evidence**: `config/default.cfg:896`; `ls modules/30_croparea/` → `simple_apr24`, `detail_apr24`.
- **verify_cmd**: `grep -nE "cfg\$gms\$(crop|croparea) " config/default.cfg` → only `croparea` at line 896.
- **confirmed**: true
- **proposed_fix**: Replace "Module 30 (Crop)" with "Module 30 (Croparea)" at module_14.md:680, 787, 1180 for consistency with Sections 16.2/21.2 and the actual module name. (Minor; relationship is correct.)

---

## Deferred (not edited — uncertain or not code-verifiable)

- Section 3.2 (module_14.md:177) attributes the `p14_pyield_corr` rewrite to commit `c7731e234`, but `git show -s c7731e234` reports subject "Natural-origin tracking for secondary forest carbon density". The hash is real and the code at `preloop.gms:18-27` matches the doc's description, so the commit plausibly bundled the pasture-correction change. Not flagged as a bug (the doc's *code* description is correct and the hash exists); the commit-subject mismatch is a provenance nuance the auditor cannot resolve without the full diff. Verify with `git show c7731e234 -- modules/14_yields/` if provenance precision matters.
- f14_pyld_hist covering exactly y1965–y2020: matches the in-code comment (`preloop.gms:19`) but the underlying `.csv` content was not parsed. Consistent with code; not independently bottom-verified.
- Numerical sanity ranges in Sections 13.4 / 21.4 (e.g. "Young plantations 50-200 tDM/ha", "ratio 1.0-3.0") are illustrative advisory heuristics, not code constants — not code-checkable.
- Section 2.1/2.2 equation-block footers "Citation: equations.gms:14-20" and "equations.gms:24-39": the crop equation is 14-16 and the past equation 35-39; the wider ranges include surrounding `*'` comment lines. Defensible as block citations (comments belong to the equation), so not flagged.
- The `module.gms` citation-line nuances (FAOSTAT `@FAOSTAT` is at root `module.gms:17`, doc Section 17 says `module.gms:16`; `realization.gms` `@limitations` is at 24-27, doc Sections 1.3/11.5 say 23-26/23-24) are off-by-1 and immaterial; not separately flagged (would be Informational at most).

---

## Note on a grep rendering artifact (methodology)

Initial `rg`/`grep -r` over the whole develop tree displayed M14 `presolve.gms` BEF lines as `sum(clcl, ln(j,clcl) * fm_ipcc_bef(clcl))`, which would have implied the M45 climate parameter is named `ln`, not `pm_climate_class`, and that the doc's `pm_climate_class` claim was fabricated. This was a **terminal-rendering artifact** (the long `pm_climate_class` token visually collapsing against adjacent matched lines). Authoritative re-checks — `grep -n`, `sed -n`, `cat -v`, and a Python `repr()` of the raw line — all confirm the file literally contains `pm_climate_class(j,clcl)`, declared in `modules/45_climate/static/input.gms:10`. The doc is correct; the artifact would have produced a false Critical "invented variable" finding. (Matches the project memory "bash-grep-r-unreliable-magpie": always cross-check absence/identity with a second method + positive control.)

---

## Mechanical checks (M1–M6) — doc-level

- M1 file:line citations present: PASS (dense).
- M2 active realization stated: PASS (managementcalib_aug19, noted as only realization).
- M3 variable prefixes valid: PASS.
- M4/M6 epistemic markers: doc is a reference doc (not a Q&A answer); closing "Verified Against" block present.

## Summary

Strong doc. One Major (pm_carbon_density_other_ac wrongly sourced to M35 in Sections 7.2/16.3 while Section 4.2 correctly says M52 — internal contradiction) and three Minor (systematic ~7-8-line preloop citation drift in Section 3; pm_yields_semi_calib set-line drift 109,142→116,149; "Module 30 (Crop)" should be "croparea"). Both advisory-checker worries (q14_yieldcalib non-existence; M45 overstatement) were refuted by code. G1 anchor (default realization + 2-equation list) fully holds.
