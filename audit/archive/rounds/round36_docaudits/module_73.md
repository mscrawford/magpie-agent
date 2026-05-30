# Round 36 Doc Audit — module_73.md (Timber Production)

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target**: `magpie-agent/modules/module_73.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/73_timber/default/*.gms` + `config/default.cfg`
**Default realization**: `default` (only realization) — confirmed `cfg$gms$timber <- "default"` (config:~) and `ls` shows only `default/` + `input/`.

---

## Overall Verdict: MOSTLY ACCURATE (lower band)

The doc's **core mechanism, equation formulas, scalar values, consumer/producer sets, and default-realization claims are correct**. The R33 advisory is **CONFIRMED correct doc** (refuted as a bug — see below). The defects are concentrated in:
1. A **superseded equation formula** shown as current in §2.2 (Major — internal contradiction with §7.4 and code).
2. **Systematic file:line citation drift** in §2, §3.5, §5, §7, and especially the wholesale-stale **Section 11** ("Code Truth"), which retains pre-2026-04-20 line numbers AND pre-update values (2.5, 74) (Major cluster).
3. A `realization.gms:16` citation that drifted to different content (the @limitations line is at :22) (Major, ×2 occurrences).
4. Minor derivation-number inconsistencies (60 EUR vs 72; 30% vs 27%) and one stale typo'd scalar name in a how-to example.

Estimated score: ~6.5/10 (one Major formula bug + Major citation-drift cluster + several Minor).

---

## R33 Advisory — VERIFIED (refuted as a bug)

**Advisory**: "in the default M73 realization, q73_prod_wood / q73_prod_woodfuel DO populate wood+woodfuel at cell level (only fish is zero). Verify those equations and the vm_prod('wood'/'woodfuel') populator claims."

**Verdict: CONFIRMED — doc is CORRECT.** `equations.gms:43-50` defines `vm_prod(j2,"wood") =e= vm_prod_forestry + sum(land_natveg, vm_prod_natveg) + v73_prod_heaven_timber`; `equations.gms:52-61` defines `vm_prod(j2,"woodfuel") =e= ... + v73_prod_residues + ...`. Both populate `vm_prod` at cell level `j2`. Doc §2.1, §2.2, and the dependency claim "Module 73 calculates this variable" (line 577) are all accurate. No bug. (The "fish is zero" concern is about M17's `vm_prod` for the fish element, which is outside M73's scope.)

---

## Verified-correct claims (high-value confirmations)

- **Realization**: only `default` exists; it IS the config default. (doc:7 ✓)
- **8 .gms files** (doc:5): confirmed (declarations, equations, input, postsolve, preloop, realization, scaling, sets).
- **Scalar defaults** (§8 table) — all match `input.gms` AND `config/default.cfg`:
  - `s73_timber_prod_cost_wood`=89, `_woodfuel`=44, `s73_free_prod_cost`=1e6, `s73_timber_demand_switch`=1, `s73_income_threshold`=10000, `s73_residue_ratio`=0.15, `s73_residue_removal_cost`=**2.7**, `s73_expansion`=0, `s73_natveg_cost_premium`=0.15, `s73_woodfuel_stacking_factor`=0.65. (input.gms:15-24; config:2215-2265)
- **Cost equation 4-term structure** (§5.1, §7.1): matches `equations.gms:23-31` verbatim.
- **Consumer sets (MANDATE 13/17, grep + positive control + `.`-suffix check)**:
  - `pm_demand_forestry` consumers outside M73 = **M32** (`32_forestry/dynamic_may24/presolve.gms:186,187,199,201,204,210,211`) + **M62** (`62_material/exo_flexreg_apr16/equations.gms:37`). Doc §5/§10 lists exactly these two. ✓ COMPLETE.
  - `im_timber_prod_cost` consumer outside M73 = **M32 only** (`32_forestry/dynamic_may24/equations.gms:172`, inside `q32_cost_establishment` which starts line 165). Doc:1030 "Used by Module 32 in `q32_cost_establishment`" ✓ COMPLETE & equation name correct.
  - `vm_cost_timber` consumer outside M73 = **M11 only** (`11_costs/default/equations.gms:34`). ✓
  - `pm_climate_class` other-consumers (doc:320-323): M14 `managementcalib_aug19/presolve.gms:29` ✓, M58 `v2/preloop.gms:36` ✓, M59 `cellpool_jan23/preloop.gms:16` ✓. (M52 also consumes it but is the upstream coupling module described directly above — not misleading.)
  - No solution-level (`.l`/`.m`) reads of these interfaces exist outside M73 (checked `NAME.` patterns).
- **Producer/source modules**: `vm_prod_forestry`←M32 (`declarations.gms:73`), `vm_prod_natveg`←M35 (`pot_forest_may24/declarations.gms:88`), `vm_prod`←M17 (`flexreg_apr16/declarations.gms:9`), `im_vol_conv`←M52 (`normal_dec17/declarations.gms:23`, populated `preloop.gms:21`). All ✓.
- **All cited realizations are defaults**: M32 dynamic_may24, M62 exo_flexreg_apr16, M35 pot_forest_may24, M11 default, M17 flexreg_apr16, M52 normal_dec17. ✓
- **Sets §6** (total_wood_products, wood_products, construction_wood, wood_panels, kforestry_to_woodprod, scen_73, build_scen): match `sets.gms:10-51` verbatim. ✓
- **Demand loop / elasticity / regional aggregation** formulas (§3.1-§3.4): match `preloop.gms` verbatim; citations 20-28, 14-16, 30-31 are EXACT. ✓
- **q73_prod_residues NEW formula** (§7.4, doc:462): matches `equations.gms:75-81` (sums plantation+natveg, both products, excludes slack). ✓

---

## Bugs Found

### BUG 73-B1 — Superseded residue formula shown as current code (§2.2)
- **Severity**: Major
- **Class**: 12 (content-level citation mismatch) / 4 (stale formula presented as code)
- **Trigger**: §1 Major — "Citation points at content materially different" + fabricated/superseded formula presented as the code's implementation.
- **Doc**: module_73.md:97-103
- **Claim**: shows `q73_prod_residues(j2).. v73_prod_residues(j2) =l= vm_prod(j2,"wood") * s73_residue_ratio ;` as the residue constraint.
- **Reality**: code is `v73_prod_residues(j2) =l= (sum(kforestry, vm_prod_forestry(j2,kforestry)) + sum((land_natveg,kforestry), vm_prod_natveg(j2,land_natveg,kforestry))) * s73_residue_ratio ;` — the OLD `vm_prod(j2,"wood")` form was replaced 2026-04-20. §7.4 (doc:460-462) shows the NEW form, so the doc internally contradicts itself.
- **File evidence**: `modules/73_timber/default/equations.gms:75-81`
- **verify_cmd**: `sed -n '75,81p' .../equations.gms` → returns the sum-of-forestry+natveg form (see report).
- **Proposed fix**: replace the §2.2 code block (lines 98-102) with the current formula:
  ```gams
  q73_prod_residues(j2)..
    v73_prod_residues(j2)
    =l=
    (sum(kforestry, vm_prod_forestry(j2,kforestry))
    + sum((land_natveg,kforestry), vm_prod_natveg(j2,land_natveg,kforestry)))
    * s73_residue_ratio
    ;
  ```
  and update the surrounding prose at doc:93 (already correct) to keep consistency.

### BUG 73-B2 — Section 11 "Code Truth" is wholesale stale (lines + values)
- **Severity**: Major (cluster)
- **Class**: 10 (stale file:line citation) + 13/wrong-value
- **Trigger**: §1 Major — citation drift to different content; also "right concept, wrong number" (values 2.5/74 predate the 2026-04-20 update to 2.7/44).
- **Doc**: module_73.md:643-672 (Section 11 items 3, 7, 8, 9)
- **Claims vs reality** (each verified):
  - :644 "15% of industrial roundwood available: `input.gms:24`, `equations.gms:66`" → input.gms:24 is `s73_woodfuel_stacking_factor`; the residue ratio is **input.gms:20**. equations.gms:66 is a comment line.
  - :646 & :672 "Removal cost **2.5** USD17MER/tDM: `input.gms:25`, `equations.gms:21`" → value is **2.7** (`input.gms:21`); input.gms:25 is the closing `;`; equations.gms:21 is a comment.
  - :662 "Cost 1 million USD17MER/tDM: `input.gms:21`, `equations.gms:22`" → `s73_free_prod_cost` is at **input.gms:17** (input.gms:21 is residue_removal_cost; equations.gms:22 is blank).
  - :666 "Volumetric conversion factors: `input.gms:47-52`" → input.gms:47-52 is the `f73_regional_timber_demand` table; the per-kforestry volumetric file was REMOVED 2026-04-20 (the doc says so in §9.3). Conversion now via `im_vol_conv` at `preloop.gms:49-51`.
  - :667 "Applied to demand: `preloop.gms:43-45`" → conversion is at **preloop.gms:49-51** (43-45 are comments).
  - :671 "Woodfuel: **74** USD17MER/tDM: `input.gms:20`" → woodfuel cost is **44 USD17MER/m3** (`input.gms:16`); input.gms:20 is residue_ratio.
- **File evidence**: `modules/73_timber/default/input.gms:16,17,20,21`; `equations.gms:66`; `preloop.gms:49-51`
- **verify_cmd**: `sed -n '17p;20p;21p;24p;25p' .../input.gms` and `sed -n '47,52p' .../input.gms` (see report — confirms each mismatch).
- **Proposed fix**: rewrite Section 11 items 3/7/8/9 with correct values and citations:
  - item 3: "15% of timber harvest recoverable: `input.gms:20`, `equations.gms:75-81`"; "Removal cost 2.7 USD17MER/tDM: `input.gms:21`, `equations.gms:29`".
  - item 7: "Cost 1 million USD17MER/tDM: `input.gms:17`, `equations.gms:30`".
  - item 8: replace "Volumetric conversion factors: `input.gms:47-52`" with "Wood density `im_vol_conv(i)` from Module 52; conversion applied at `preloop.gms:49-51`". Remove "Applied to demand: `preloop.gms:43-45`" or change to `preloop.gms:49-51`.
  - item 9: "Wood: 89 USD17MER/m3 (`input.gms:15`); Woodfuel: 44 USD17MER/m3 (`input.gms:16`); Residues: 2.7 USD17MER/tDM (`input.gms:21`)". Delete the "Woodfuel: 74 USD17MER/tDM: `input.gms:20`" line entirely (duplicate + wrong).

### BUG 73-B3 — Equation citation drift (§2.1, §2.2, §5.1, §7) — all equations cited ~7-8 lines early
- **Severity**: Major
- **Class**: 10 (stale file:line citation)
- **Trigger**: §1 Major — "File:line citation drift to adjacent but different content".
- **Doc**: module_73.md:43, 75, 278, 414, 431, 443, 457 (and §11 :635-637)
- **Claim vs reality** (equation start lines; doc quotes the formula correctly, only line refs drift because equations.gms gained an 8-line @equations comment header at lines 8-21):
  - `q73_cost_timber`: doc cites `equations.gms:16-27`; actual **23-31**.
  - `q73_prod_wood`: doc cites `equations.gms:35-42`; actual **43-50**.
  - `q73_prod_woodfuel`: doc cites `equations.gms:44-53`; actual **52-61**.
  - `q73_prod_residues`: doc §7.4 cites `equations.gms:72-79`; actual **75-81**. (doc §2.1 line 39 "equations.gms:35-53" spans the wood+woodfuel eqs, now 43-61.)
- **File evidence**: `modules/73_timber/default/equations.gms` — `grep -n "q73_"` → 23/43/52/75.
- **verify_cmd**: `grep -n "q73_cost_timber\|q73_prod_wood\|q73_prod_woodfuel\|q73_prod_residues" .../equations.gms` → `23:`, `43:`, `52:`, `75:`.
- **Proposed fix**: bump all equations.gms citations: cost 16-27→23-31; prod_wood 35-42→43-50; prod_woodfuel 44-53→52-61; prod_residues 72-79→75-81; §2.1 header "35-53"→"43-61"; §11 items "equations.gms:38,47"→"46,55" / "40,49"→"48,57", "equations.gms:51"→"59".

### BUG 73-B4 — `realization.gms:16` citation drifted to different content (×2)
- **Severity**: Major
- **Class**: 10 (stale file:line citation)
- **Trigger**: §1 Major — citation drift to materially different content.
- **Doc**: module_73.md:26 ("Does NOT determine timber demand endogenously (`realization.gms:16`)") and module_73.md:690 (same cite under §12.1).
- **Reality**: `realization.gms:16` is `*' Timber can be produced from both timber plantations vm_prod_forestry provided by [32_forestry]`. The "@limitations Timber demand cannot be determined endogenously" line is at **realization.gms:22**.
- **File evidence**: `modules/73_timber/default/realization.gms:22`
- **verify_cmd**: `grep -n "endogenous" .../realization.gms` → `22:*' @limitations Timber demand cannot be determined endogenously`.
- **Proposed fix**: change both `realization.gms:16` → `realization.gms:22`.

### BUG 73-B5 — preloop.gms conversion/cost citation drift (§3.5, §5.1, §5)
- **Severity**: Minor
- **Class**: 10 (stale file:line citation)
- **Trigger**: §1 Minor — "off-by-few line citation where adjacent lines say similar things"; here a few land on comment lines.
- **Doc**: module_73.md:183 (§3.5 "preloop.gms:46-48"), :194 (§3.5 "preloop.gms:42" — this one is CORRECT), :298 (§5.1 "preloop.gms:89-90"), :304/:1034 (§5 natveg "preloop.gms:93-94"), :243 (§4.2 "preloop.gms:76-77").
- **Reality**: m3→tDM conversion is at **preloop.gms:49-51** (doc says 46-48, which are comments); per-m3→per-tDM cost conversion at **preloop.gms:90-91** (doc says 89-90); natveg cost at **preloop.gms:94-95** (doc says 93-94); construction-wood "added on top" at **preloop.gms:83** (doc §4.2 says 76-77).
- **File evidence**: `modules/73_timber/default/preloop.gms:49-51, 90-91, 94-95, 83`
- **verify_cmd**: `sed -n '49,51p;90,91p;94,95p;83p' .../preloop.gms` (see report).
- **Proposed fix**: §3.5 "preloop.gms:46-48"→"49-51"; §5.1 "preloop.gms:89-90"→"90-91"; §5/interface "preloop.gms:93-94"→"94-95"; §4.2 "preloop.gms:76-77"→"83". (§3.5 ":42" stays.)

### BUG 73-B6 — Cost-derivation prose inconsistent with code: "60 EUR/m3" vs code's 72
- **Severity**: Minor
- **Class**: 13-adjacent (wrong derivation number; final value correct)
- **Trigger**: §1 Minor (tie-breaker down from Major) — "right concept, wrong number"; the scalar value 89 is correct, only the cited multiplicand is wrong AND arithmetically inconsistent (60×1.23=73.8≠89).
- **Doc**: module_73.md:296 ("UNECE roundwood price (60 EUR/m3 × 1.23)") and :487 ("(UNECE, 60 EUR/m3 × 1.23)").
- **Reality**: config comment is `s73_timber_prod_cost_wood <- 89 # def = 72 * 1.23 (USD17MER per m3)`. 72×1.23=88.56≈89. The doc's "60 EUR/m3" is wrong; correct multiplicand is **72 EUR/m3**.
- **File evidence**: `config/default.cfg:2220` (`# def = 72 * 1.23`)
- **verify_cmd**: `grep -n "s73_timber_prod_cost_wood" config/default.cfg` → `2220:cfg$gms$s73_timber_prod_cost_wood <- 89  # def = 72 * 1.23 (USD17MER per m3)`.
- **Proposed fix**: change "60 EUR/m3 × 1.23" → "72 EUR/m3 × 1.23" in both locations (doc:296, doc:487).

### BUG 73-B7 — Residue theoretical-potential stated as ~30% (code: 27%) in §1 and §2.2
- **Severity**: Minor
- **Class**: 13-adjacent (wrong derivation number; final 0.15 correct)
- **Trigger**: §1 Minor — wrong sub-value, hedged with "~", final scalar correct, and §7.4 has it right (internal inconsistency).
- **Doc**: module_73.md:33 ("~30% theoretical roundwood-residue potential × ~52%") and :106 ("USDA reports ~30% of roundwood harvested are residues (Oswalt et al. 2019)").
- **Reality**: code comment says "theoretical potential of logging residues is **27%** of stem harvest [@oswalt2019forest] ... 52% ... 0.27 * 0.52 = 0.14 ~ 0.15". §7.4 (doc:473) correctly says 27%.
- **File evidence**: `modules/73_timber/default/equations.gms:65-67`
- **verify_cmd**: `sed -n '63,73p' .../equations.gms` → "...potential of logging residues is 27% of stem harvest...0.27 * 0.52 = 0.14 ~ 0.15".
- **Proposed fix**: change "~30%" → "27%" at doc:33 and doc:106 (align with code and §7.4).

### BUG 73-B8 — Stale typo'd scalar name in §13.6 how-to example
- **Severity**: Minor
- **Class**: 5 (stale reference after rename)
- **Trigger**: §1 Minor — module/var renamed but old name still present in a secondary (example) section; MANDATE 15 (post-rename grep missed §13.6).
- **Doc**: module_73.md:841 (`s73_reisdue_removal_cost = 1.0` in a modification snippet) and the surrounding citation :848 ("`input.gms:24-25`, `equations.gms:21, 66`").
- **Reality**: scalar is `s73_residue_removal_cost` (`input.gms:21`); the typo `*s73_reisdue_removal_cost*` was corrected (the doc itself notes this at :272, :310, :493). The example would fail if copy-pasted. Citation `input.gms:24-25` is also stale (24 = stacking factor, 25 = `;`).
- **File evidence**: `modules/73_timber/default/input.gms:21`
- **verify_cmd**: `grep -n "reisdue" .../*.gms` → no match in code (only correct `s73_residue_removal_cost` at input.gms:21).
- **Proposed fix**: doc:841 change `s73_reisdue_removal_cost = 1.0` → `s73_residue_removal_cost = 1.0`; doc:848 change "`input.gms:24-25`, `equations.gms:21, 66`" → "`input.gms:20-21`, `equations.gms:29, 75-81`".

---

## Deferred (not edited — uncertain or non-code-checkable)

- **"12 MAgPIE regions"** (doc:175, 679, 987): true for the default h12 regionmapping but is a config-resolution claim, not M73 code; the §3.4 cite "preloop.gms:31" points at the i-aggregation line which doesn't literally state "12". Not flagged (standard, not misleading).
- **`module.gms:8-16`** (doc:13): the @description spans module.gms:8-15 and broadly matches "provides pm_demand_forestry to [32]/[62], merges vm_prod for [17]/[21]". Range includes line 16 (one past), but content matches. Borderline; not flagged.
- **`equations.gms:10-15`** (doc:663 "Ensures model feasibility"): the @equations comment block (lines 8-21) does describe the slack variable's role; the 10-15 sub-range lands inside it. Acceptable interpretive cite; not flagged.
- **`pm_climate_class` "Other consumers (outside M73)" omits M52**: M52 consumes pm_climate_class (to build im_vol_conv) but is described as the upstream coupling module immediately above; listing M14/58/59 as the *other independent* consumers is reasonable. Not flagged as a phantom/omission bug.
- **Income-elasticity "typical values" (~0.4-0.8 roundwood, ~-0.5 woodfuel)** (doc:522-524, 826): these are illustrative ranges, not read from the `.csv` input (binary/data file I cannot parse). Labeled "Typical" in the doc. Not code-checkable; deferred.
- **R/magpie4 validation snippets in §14** (readGDX of `ov_prod`, `ov73_prod_residues`, etc.): output names `ov73_prod_residues`/`ov_cost_timber` are confirmed declared (`declarations.gms:38-44`), but the literal `2.5`/`1e6` constants in the §14.4 R snippet are illustrative and `2.5` is now stale (2.7). Minor and example-only; folded conceptually into B2's value-staleness rather than a separate bug (the R snippet is user-facing illustrative code, not a doc claim about code).

---

## Summary

Doc spine (mechanism, formulas, scalar defaults, consumer/producer sets, default realization) is **correct**, and the R33 advisory is **confirmed correct (refuted as a bug)**. Defects: 1 Major superseded-formula (§2.2 residue eq), a Major citation-drift cluster (Section 11 stale lines+values 2.5/74, all 4 equation cites off by ~7-8 lines, `realization.gms:16`→:22), plus Minor drifts (preloop conversion lines, 60-vs-72 EUR derivation, 30-vs-27% residue potential, stale `s73_reisdue_removal_cost` typo in §13.6).
