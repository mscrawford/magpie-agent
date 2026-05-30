# Round 33 Doc Audit — module_52.md (Carbon, normal_dec17)

**Auditor**: Opus adversarial doc auditor
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (Merge PR #887); config `config/default.cfg`
**Date**: 2026-05-30
**Doc**: `magpie-agent/modules/module_52.md` (1223 lines)

## Overall Verdict: MOSTLY ACCURATE (lower band)
## Accuracy estimate: ~7/10 for the doc as a whole

The doc is **substantively correct** on every high-stakes claim:
- Default realization `normal_dec17` ✓ (config:1556)
- The G2-anchor populator set for `vm_carbon_stock` (M29/31/32/34/35/59; M30→`vm_carbon_stock_croparea`; M58 does NOT populate) — fully correct ✓
- `vm_carbon_stock`/`pcm_carbon_stock`/`vm_emissions_reg` declared in M56 (not M52); M52 only READS the stocks and WRITES emissions — producer/consumer distinction correct ✓
- All four consumer citations on line 4 (secdforest_ac→M14:44+M35:248; plantation_ac→M14:26+M32:65) — **all CORRECT** (refutes the pre-run checker lead) ✓
- Equation formula `q52_emis_co2_actual` (equations.gms:16-19) — exact match ✓
- Scalar defaults `s52_growingstock_calib=1` (input.gms:46), `s52_k_high_secdf=0.1` (47), `s52_k_high_plant=0.15` (48), `c52_carbon_scenario=cc`, `c52_land_carbon_sink_rcp=RCPBU` — all verified ✓
- Macros `m_growth_vegc` (macros.gms:18), `m_growth_litc_soilc` (:20), `m_timestep_length` (:51) — exact ✓
- Set citations `emis_oneoff` (sets.gms:314-318, 21 members), `c_pools` (:324-325), `emis_land` (:332-335) — exact ✓
- PR #869 provenance (commit 75d7ee167, branch ipopt_part1, author Georg Schroeter), preloop.gms = 118 lines, iter52 = iter1*iter25 (25 iters) — all verified ✓
- im_vol_conv → M73 (im_timber_prod_cost preloop.gms:90-91, pm_demand_forestry :49,51); f73_volumetric_conversion.csv gone — verified ✓
- All upstream interface providers (sm_carbon_fraction M14:input.gms:22=0.5; fm_ipcc_bef/fm_aboveground_fraction M14; im_forest_ageclass M28; pm_land_plantation M32) — verified ✓
- im_growing_stock downstream (M32 presolve:181, M35 equations:147) — verified, correctly labeled as one-hop ✓

The problems are **pervasive file:line citation drift** caused by PR #869 inserting blocks into `input.gms` (~+30 lines before the Grassi section) and `start.gms` (~+13 lines before the other-land block). The doc updated the NEW sections' citations and the primary Section-2 citations, but left STALE citations in the Limitations/Data/older sections. All findings below trace to this one mechanism plus a couple of name slips.

---

## BUGS

### BUG-1 (Major) — `fm_carbon_density` consumer set omits Module 32
- **Class**: 15 (latent doc error — interface-consumer set incomplete) / MANDATE 13
- **Trigger**: §1 Major — "Fabricated/incomplete consumer set" territory; R20 anchor (consumer-set omission is Critical-prone). Tie-breaker pulls to Major: 1-of-8 omission, M32 is listed elsewhere as an M52 consumer so it's on a reader's radar, var is documented as "broadly used".
- **Doc claim** (lines 265-272 and line 483): consumers listed as M14, M29, M30, M31, M35, M56, M59 (and at 483: "Modules 14, 29, 30, 31, 35, 56, and 59"). M32 is absent from both lists.
- **Reality**: M32 directly reads `fm_carbon_density` at `modules/32_forestry/dynamic_may24/presolve.gms:176` (`v32_land.fx(j,"aff",ac_est)$(fm_carbon_density(t,j,"forestry","vegc") <= 20) = 0;`).
- **verify_cmd**: `grep -rln "fm_carbon_density" /tmp/magpie_develop_ro/modules/ --include="*.gms" | grep -v 52_carbon` → returns 30(simple+detail), 56, 32, 31(static+endo), 14, 35, 59(cellpool+static), 29(detail). Then `grep -n "fm_carbon_density" .../32_forestry/dynamic_may24/presolve.gms` → `176: v32_land.fx(...)$(fm_carbon_density(t,j,"forestry","vegc") <= 20)`.
- **tier_uncertainty**: true (a reasonable auditor could call this Critical under the R20 anchor).
- **Proposed fix**: In the Section-2.C list (lines 265-272) add a bullet: `- Module 32 (Forestry) — modules/32_forestry/dynamic_may24/presolve.gms:176`. In line 483 change "Modules 14, 29, 30, 31, 35, 56, and 59" → "Modules 14, 29, 30, 31, 32, 35, 56, and 59".

### BUG-2 (Major) — Grassi land-carbon-sink citations drift ~30 lines onto materially-different content
- **Class**: 10/12 (stale file:line citation → content mismatch)
- **Trigger**: §1 Major — "Citation points at content that's no longer at the cited line, AND the actual content says something materially different." R20 citation-drift anchor.
- **Doc claim**: the entire "Land Carbon Sink Adjustment Factors" treatment cites lines that are ~30 too low. Specifically: line 361 "(input.gms:45-66)"; line 363 "(input.gms:49)"; line 365 "(input.gms:45)"; line 367 "(input.gms:51-56)"; line 379/666 "(input.gms:58-66)"; line 381 "(input.gms:59)"; line 387 "(input.gms:60-62)"; line 395 "(input.gms:63-66)"; line 404 "(input.gms:46-47)"; line 587 "(input.gms:53)".
- **Reality**: After PR #869 the scalar block + FRA files + volumetric file occupy input.gms:45-73, pushing the Grassi block down. Actual locations: Grassi comment header = input.gms:75-79; table `f52_land_carbon_sink` = 80-86; selection `$ifthen` logic = 88-96; `i52_land_carbon_sink(...) nocc` = 89; `nocc_hist` = 90-92; RCP branch = 93-96. The doc's cited lines (45-66) land on the `scalars` block (45-49), `f52_fra_nrf_gs` (51-57), `f52_fra_pla_gs` (59-65), `f52_volumetric_conversion` (67-73) — i.e. unrelated content.
- **file_evidence**: `/tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/input.gms:75-96` (Grassi block); :45-73 (the inserted block now occupying the doc's cited lines).
- **verify_cmd**: `sed`-free Read of input.gms lines 45-96 (done): confirmed scalars at 45-49, FRA/vol at 51-73, Grassi comment at 75, table at 81, selection logic at 88-96.
- **Proposed fix**: Re-point every Grassi-section citation: 45-66→75-96; 45→75; 49→79; 51-56→80-86 (or 81 for the table line); 58-66→88-96; 59→89; 60-62→90-92; 63-66→93-96; 46-47→75-78; Section-3 file `f52_land_carbon_sink_adjust_grassi.cs3` 53→83. (Note: the NEW FRA/vol citations at lines 606/607/619/672 are correct/off-by-one only — leave or trim the leading line by 1.)

### BUG-3 (Major) — `start.gms:35 / :37 / :38` citations are stale (PR #869 shifted other-land block to 48/50/51)
- **Class**: 10/12 (stale citation → materially-different content)
- **Trigger**: §1 Major — cited lines now hold calibration-init/blank content, not the claimed growth/litter code.
- **Doc claim**:
  - lines 497, 580, 864, 923: "(start.gms:17,28,35)" for climate-weighted/Chapman-Richards growth-parameter application.
  - line 216: "20-year litter equilibrium: IPCC guidelines (start.gms:19, 30, 37)".
  - line 164: "this macro is applied only to litter carbon ... (start.gms:20, 31, 38)".
- **Reality**: start.gms:35 = `i52_k_calib_plant(i) = 0;`; :37 = `i52_gs_current_plant(i) = 0;`; :38 = blank. The other-land VEGC growth (Chapman-Richards) is at start.gms:48; other-land LITC growth at :51; other-land IPCC-comment at :50. The doc itself uses the correct 48/51 in Section 2 (lines 140, 199-206) but the limitations/data sections retain the pre-insertion 35/37/38.
- **file_evidence**: `/tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/start.gms:33-51`.
- **verify_cmd**: Read start.gms:33-51 → lines 34-37 are i52_* zero-inits, 38 blank, 48 = other vegc m_growth_vegc, 50 = IPCC litter comment, 51 = other litc m_growth_litc_soilc.
- **Proposed fix**: lines 497/580/864/923: "start.gms:17,28,35" → "start.gms:17,28,48". line 216: "start.gms:19, 30, 37" → "start.gms:19, 30, 50". line 164: "start.gms:20, 31, 38" → "start.gms:20, 31, 51".

### BUG-4 (Minor) — M32 uncalib-consumer line citations off by one (58→59, 60→61, 69→68)
- **Class**: 10 (off-by-few citation, adjacent content is the SAME assignment)
- **Trigger**: §1 Minor — off-by-few line citation where adjacent lines say similar things.
- **Doc claim**: lines 278, 457, 477 cite M32 `dynamic_may24/presolve.gms:58` (aff secdforest_uncalib), `:60` (aff plantation_uncalib), `:69` (ndc secdforest_uncalib).
- **Reality**: presolve.gms:59 = `p32_carbon_density_ac(...,"aff",...) = pm_carbon_density_secdforest_ac_uncalib` (under `s32_aff_plantation=0`); :61 = `... = pm_carbon_density_plantation_ac_uncalib` (under `=1`); :68 = `...,"ndc",...) = pm_carbon_density_secdforest_ac_uncalib`.
- **file_evidence**: `/tmp/magpie_develop_ro/modules/32_forestry/dynamic_may24/presolve.gms:58-68`.
- **verify_cmd**: `grep -n "pm_carbon_density_secdforest_ac_uncalib" .../32_forestry/dynamic_may24/presolve.gms` → `59:`, `68:`; plantation_uncalib → `61:`.
- **Proposed fix**: globally in lines 278/457/477: presolve.gms:58→59, :60→61, :69→68. (Doc line 278 "presolve.gms:58,60" → "presolve.gms:59,61".)

### BUG-5 (Minor) — Wrong intermediate variable: `v32_cost_establishment` named where `p32_carbon_density_ac` is assigned
- **Class**: 4 (conceptual mechanism with wrong variable) / MANDATE 2/7
- **Trigger**: §1 Minor — wrong detail in a parenthetical; load-bearing claim (M32 consumes uncalib for afforestation) is itself correct and recoverable.
- **Doc claim** (line 278): "(type `"aff"` — `v32_cost_establishment` uses either secdforest or plantation uncalib depending on `s32_aff_plantation`)".
- **Reality**: At presolve.gms:58-62 the variable assigned from the uncalib param is `p32_carbon_density_ac(t,j,"aff",ac,ag_pools)`, NOT `v32_cost_establishment`. `v32_cost_establishment` exists in M32 (equations/declarations/scaling/postsolve) but is NOT present in presolve.gms and is not the immediate sink of the uncalib density.
- **file_evidence**: presolve.gms:58-62; `grep -rln v32_cost_establishment .../32_forestry/ --include=*.gms` → equations.gms, scaling.gms, declarations.gms, postsolve.gms (NOT presolve.gms).
- **verify_cmd**: `grep -rln "v32_cost_establishment" /tmp/magpie_develop_ro/modules/32_forestry/ --include="*.gms"` (no presolve.gms hit); Read presolve.gms:58-62.
- **Proposed fix**: line 278 replace "`v32_cost_establishment` uses either secdforest or plantation uncalib" with "`p32_carbon_density_ac(...,"aff",...)` is set from either secdforest or plantation uncalib".

### BUG-6 (Minor) — `af_ndc` described as an M32 "realization"; no such realization exists
- **Class**: 8 (realization-name) / MANDATE 8, 12
- **Trigger**: §1 Minor — recoverable concept (clearly the aff/ndc afforestation logic), in an advisory note.
- **Doc claim** (line 138): "still used downstream for afforestation/NDC use cases (Module 32's `af_ndc` realization logic, ...)".
- **Reality**: M32 has exactly ONE realization, `dynamic_may24` (config:976; `ls modules/32_forestry/` = dynamic_may24 + input). `af_ndc` is not a realization. The relevant objects are set `type32 / aff, ndc, plant /` (`dynamic_may24/sets.gms:16-17`). `grep -rln "af_ndc" modules/32_forestry/` → no hits.
- **file_evidence**: `/tmp/magpie_develop_ro/modules/32_forestry/dynamic_may24/sets.gms:16-17`; config:976.
- **verify_cmd**: `grep -rln "af_ndc" /tmp/magpie_develop_ro/modules/32_forestry/` → EXIT 1 (none); `grep -nE "^cfg\$gms\$forestry" config/default.cfg` → `dynamic_may24`.
- **Proposed fix**: line 138 replace "Module 32's `af_ndc` realization logic" with "Module 32's `aff` and `ndc` plantation types (set `type32`)".

### BUG-7 (Minor) — `declarations.gms` line citations off by one for three parameters
- **Class**: 10 (off-by-few citation; adjacent content is a sibling parameter declaration)
- **Trigger**: §1 Minor.
- **Doc claim**: line 459 `pm_carbon_density_other_ac (declarations.gms:12)`; line 466 `pm_carbon_density_plantation_ac (declarations.gms:13)`; line 473 `pm_carbon_density_plantation_ac_uncalib (declarations.gms:14)`.
- **Reality**: declarations.gms:11 = other_ac; :12 = plantation_ac; :13 = plantation_ac_uncalib. (secdforest_ac:9, secdforest_ac_uncalib:10, im_vol_conv:23 are all CORRECT in the doc.)
- **file_evidence**: `/tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/declarations.gms:9-23`.
- **verify_cmd**: Read declarations.gms (done).
- **Proposed fix**: line 459 declarations.gms:12→11; line 466 :13→12; line 473 :14→13.

### BUG-8 (Minor) — preloop.gms internal line-citation drift cluster (~+5)
- **Class**: 10 (off-by-few; all within the calibration block, adjacent similar content)
- **Trigger**: §1 Minor.
- **Doc claim vs reality** (all in `normal_dec17/preloop.gms`):
  - im_vol_conv aggregation: line 235 says ":21" (CORRECT); but line 488 ":21" (CORRECT); line 624 "preloop.gms:22" → actual 21.
  - line 240 "Step 2 ... (preloop.gms:28-33)" → i52_bef_avg at 26, m_avg at 29-30 (range start off).
  - line 286/515 `fm_ipcc_bef` "(preloop.gms:27)" → actual 26.
  - line 247/284/503 `im_forest_ageclass` read "(preloop.gms:47)" → actual 53/55.
  - line 286/521 `fm_aboveground_fraction` "(preloop.gms:56)" → actual 61 (secdforest) / 96 (forestry).
  - line 526/527 `sm_carbon_fraction` "(preloop.gms:56)" → actual 60 / 95.
  - line 285/509 `pm_land_plantation` read "(preloop.gms:83)" → actual 88.
  - line 274/275 diagnostic logging "(preloop.gms:108-113)" → actual put_utility block 106-111.
  - line 497 `pm_climate_class` usage "(preloop.gms:22,27-31)" → actual 21,26,29-30.
  - (CORRECT: secdforest overwrite 71-73 line 260 ✓; plantation overwrite 114-116 line 263 ✓; im_vol_conv 21 ✓.)
- **file_evidence**: `/tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/preloop.gms` (full read).
- **verify_cmd**: Read preloop.gms 1-118 (done).
- **Proposed fix**: re-point the drifted internal citations: 22→21 (im_vol_conv/pm_climate_class); 27→26 (fm_ipcc_bef); 47→53 (im_forest_ageclass read); 56→61 (fm_aboveground_fraction read) and 56→60 (sm_carbon_fraction read); 83→88 (pm_land_plantation read); 108-113→106-111 (diagnostic); 28-33→26-30 (Step 2); 27-31→29-30.

---

## Pre-run checker lead — VERDICT

> "module_52.md:4 lists M35 ...:248 and M32 ...:65 ... with no grep-hit."

**REFUTED.** Both are genuine direct consumers at the exact cited lines:
- `grep -n pm_carbon_density_secdforest_ac .../35_natveg/pot_forest_may24/presolve.gms` → `248: p35_carbon_density_secdforest(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac(...)` ✓
- `grep -n pm_carbon_density_plantation_ac .../32_forestry/dynamic_may24/presolve.gms` → `65: p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(...)` ✓
- M14:44 (secdforest) and M14:26 (plantation) also confirmed.

> "module_52.md:291 M35 listing was a confirmed FP last push."

**Now CORRECT (not a FP).** Line 291 says `pm_carbon_density_secdforest_ac_uncalib` "also consumed by Module 35 ...presolve.gms:117". Verified: `117: p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20)`. Genuine consumer. (Also used at M35 presolve:242.) No action.

> "_calib vs _uncalib sibling distinction (M29/M32 consume the _uncalib siblings)."

**CONFIRMED correct in doc.** M29 consumes ONLY the _uncalib siblings (preloop.gms:46 secdf, :48 plant). M32 consumes BOTH: calibrated plantation_ac (presolve:65, "plant") and uncalib (aff/ndc). Doc distinguishes these correctly. M14/M35 consume the calibrated (non-uncalib) versions. All verified.

---

## DEFERRED (not edited — uncertain or not code-checkable)

- Config has `cfg$gms$s52_plantation_threshold <- 8` (default.cfg:1572) and CHANGELOG references it as an M52 scalar, but it is NOT present in any current M52 .gms file (`grep -rn s52_plantation_threshold modules/` → only config + CHANGELOG). It appears to be an orphaned config switch whose consuming code was removed. The doc does NOT claim it exists, so omission is defensible — NOT a doc bug. Flagging only so a future maintainer notes the config/code mismatch (out of scope for module_52.md).
- Historical/narrative prose in §Key Insights and §Limitations (e.g., "one-way coupling", "LPJmL as carbon oracle") is interpretive, not code-checkable — not audited.
- Footer "Last Verified 2026-05-16 ... sync to commit c7731e234": commit `c7731e234` not in the current `git log` reachable set I searched (only checked --all grep for 869/ipopt). The two scalars it claims that commit added (s52_k_high_secdf/plant) DO exist with the stated defaults, so the substantive claim holds; the SHA itself I did not independently confirm reachable — left as-is (low stakes, metadata footer).

---

## Summary
Doc spine is solid: every load-bearing claim (default realization, G2 populator set, M56 declaration site, producer/consumer distinction, line-4 consumers, equation formula, scalar defaults, macros, sets, PR #869 provenance, M73/im_vol_conv, upstream providers) is verified CORRECT. The checker's phantom-consumer lead is refuted. The defects are citation drift from PR #869 insertions: 2 Major (BUG-1 M32 omitted from fm_carbon_density consumers; BUG-2 Grassi section ~30-line drift onto unrelated content), 1 Major (BUG-3 start.gms:35/37/38 stale → 48/50/51), and 4 Minor (BUG-4..8: off-by-one M32 lines, wrong intermediate var v32_cost_establishment, af_ndc non-realization, declarations off-by-one, preloop internal drift cluster).
