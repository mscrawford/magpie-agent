# Audit Report: module_12.md (Interest Rate)

**Target doc**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_12.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/12_interest_rate/select_apr20/*.gms`, `/tmp/magpie_develop_ro/config/default.cfg`
**Realization checked**: `select_apr20` (confirmed default — `module.gms:20`, `config/default.cfg:` `cfg$gms$interest_rate <- "select_apr20"`)
**Date**: 2026-05-30 (round 31 doc audit)

## Overall Verdict: SIGNIFICANT ERRORS
## Accuracy Score: 5/10

The doc is technically strong on the formula, parameters, citations, and the input-dependency side — every `preloop.gms`/`input.gms` citation and the GDP-dependent formula were verified correct. But the **consumer (PROVIDES-TO) set is internally contradictory and wrong in four prominent sections**: Sections 1, 3A, the §5 "PROVIDES TO (3 modules)" header, and §7 all claim only **3 consumers (13, 39, 41)**, omitting six real direct consumers (29, 32, 38, 56, 58, 70). The doc's own Summary (line 765) and Dependency-Chains (line 835) carry the corrected 9-module list — so the doc was partially updated (R3 2026-05-23) and the stale 3-module claim was left in four places (a MANDATE-15 post-update-grep failure). A wrong/incomplete consumer set is the R20-anchor Critical pattern (a user refactoring `pm_interest` would miss six modules).

---

## Ground-truth consumer set (verified twice + positive control)

`grep -rln "pm_interest" /tmp/magpie_develop_ro/modules/ --include="*.gms"` and `rg -n 'pm_interest' ... -g '*.gms' -l` AGREE. Distinct module numbers (excluding self M12): **13, 29, 32, 38, 39, 41, 56, 58, 70** = **9 modules**. Core does NOT reference it (grep exit 1, confirmed NOT in core).

Direct-read verification per module (all are direct equation/presolve/preloop reads, none transitive — MANDATE 17 clean):
- M13 `endo_jan22/equations.gms:23,42` (DEFAULT) — annuity factor.
- M29 `detail_apr24/equations.gms:111` (DEFAULT) — annuity.
- M32 `dynamic_may24/equations.gms:171,173` + `preloop.gms:41,42,68,75,78,79` (DEFAULT) — Faustmann rotation/discount.
- M38 `sticky_feb18/equations.gms:23`, `presolve.gms:25,26` (DEFAULT) — capital amortization.
- M39 `calib/equations.gms:15` (DEFAULT) — land-conversion annuity.
- M41 `endo_apr13/equations.gms:23` (DEFAULT) — AEI investment annuity.
- M56 `price_aug22/equations.gms:52,78,79` (DEFAULT) — CDR-reward annuity / discounting.
- M58 `v2/equations.gms:80` (DEFAULT) — peatland annuity.
- M70 `fbask_jan16_sticky/equations.gms`, `presolve.gms:80` — **NON-DEFAULT** realization only. The DEFAULT `fbask_jan16` explicitly lists `pm_interest` in `not_used.txt` ("Since no capital stocks are implemented there is no need to consider interest rates"). So M70 consumes it only under the non-default sticky realization.

Default realizations confirmed via `config/default.cfg`: tc=endo_jan22, cropland=detail_apr24, forestry=dynamic_may24, factor_costs=sticky_feb18, landconversion=calib, area_equipped_for_irrigation=endo_apr13, ghg_policy=price_aug22, peatland=v2, livestock=fbask_jan16.

---

## Verified Claims (correct)

- Default realization `select_apr20`, default mode `c12_interest_rate = "gdp_dependent"` — `module.gms:20`, `input.gms:8`, `config/default.cfg`. ✅
- "NO EQUATIONS … runs only in preloop" — no equations.gms in select_apr20 (only declarations/input/preloop/realization). ✅
- GDP-dependent formula (doc lines 54-58) — byte-for-byte matches `preloop.gms:23-26`. ✅
- All scalar defaults: `s12_interest_lic`=0.1, `s12_interest_hic`=0.04, `s12_hist_interest_lic`=0.1, `s12_hist_interest_hic`=0.04, and the four `_noselect` variants all 0.1/0.04 — `input.gms:11-18`. ✅
- `p12_reg_shr` population-weighted formula — `preloop.gms:17`. ✅
- Coupling block `preloop.gms:20-21` (`$ifthen ... p12_interest_select = f12_interest_coupling`). ✅
- Country switch `preloop.gms:12-17`. ✅
- `select_countries12` = exactly **249** country codes (counted) — `input.gms:22-46`. ✅
- `p12_interest_select` "implicitly declared via assignment in preloop.gms:21 (not in declarations.gms)" — confirmed: the name appears ONLY at `preloop.gms:21`, never declared. ✅ (accurate, subtle)
- Input citations `input.gms:11-14`, `15-18`, `21-47`, `22-46`, `49-55`, `57-63`, `8` — all verified correct against the 64-line file. ✅
- DEPENDS ON exactly Module 09, receiving `im_development_state` + `im_pop_iso` — `grep -hoE "(im_|vm_|pm_)..."` on M12 returns only those two inputs + `pm_interest` output. ✅ `im_development_state` declared/assigned in M09 `aug17` (default). ✅
- `f12_interest_fader` declaration string "Protection scenario fader (1)" — exact match `input.gms:49`. ✅
- Transition timing 2025→2050 — matches `realization.gms:15-16`. ✅
- "% per yr" in the Interface Variables table (line 809) matches `declarations.gms:9` canonical string. ✅

---

## Bugs Found

### Bug module_12-B1 — Consumer set understated as 3 modules in four sections (omits 6 real consumers)
- **Severity**: Critical
- **Class**: 15 (Latent doc error — wrong consumer set) / overlaps Pattern 6
- **Trigger** (§1 Critical): "doc said wrong consumer set; user would have missed modules in a refactor" (R20 anchor `pm_carbon_density_ac`).
- **Claim in answer**: line 15 "Used by: Module 13 (TC), Module 39 (Land Conversion), Module 41 (Irrigation)"; line 173-176 same triplet; line 321 "**PROVIDES TO (3 modules)**" listing only 13/39/41; lines 396-399 "Same `pm_interest` applies to ALL investments: Technical change (Module 13), Land conversion (Module 39), Irrigation infrastructure (Module 41)".
- **Reality in code**: 9 modules read `pm_interest` directly: 13, 29, 32, 38, 39, 41, 56, 58, 70 (70 only in non-default sticky). The triplet omits **29, 32, 38, 56, 58, 70**.
- **File evidence**: `modules/29_cropland/detail_apr24/equations.gms:111`, `modules/32_forestry/dynamic_may24/equations.gms:171`, `modules/38_factor_costs/sticky_feb18/presolve.gms:25`, `modules/56_ghg_policy/price_aug22/equations.gms:52`, `modules/58_peatland/v2/equations.gms:80`, `modules/70_livestock/fbask_jan16_sticky/presolve.gms:80`.
- **verify_cmd**: `grep -rln "pm_interest" /tmp/magpie_develop_ro/modules/ --include="*.gms" | sort` → 19 files across modules 12,13,29,32,38,39,41,56,58,70. Cross-checked with `rg -n 'pm_interest' -g '*.gms' -l` (agree). Positive control `vm_carbon_stock` in 52_carbon → hit (search works).
- **Anchor reference**: R20 `pm_carbon_density_ac` (doc cited fewer consumers than code → Critical).
- **Confirmed**: true.
- **Proposed fix**: Replace the 3-module list in all four locations with the verified 9-module list, consistent with line 765. E.g. line 15 → "Used by 9 modules: 13 (TC), 29 (cropland), 32 (forestry), 38 (factor costs), 39 (land conversion), 41 (irrigation), 56 (GHG policy), 58 (peatland), 70 (livestock — sticky realization only)." Update the §5 header "PROVIDES TO (3 modules)" → "PROVIDES TO (9 modules)" and add the six omitted modules as consumer entries; update §7 line 396-399 list likewise.

### Bug module_12-B2 — Inconsistent / fabricated consumer count "10 modules"
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift)
- **Trigger** (§1 Major): "Fabricated count for a set/parameter/realization list".
- **Claim in answer**: line 835 "**Provides to** (10 modules via `pm_interest`): Module 13 …, Module 39 …, Module 41 …, Module 56 …, and downstream cost modules."
- **Reality in code**: 9 modules reference `pm_interest` (13, 29, 32, 38, 39, 41, 56, 58, 70). The same doc's line 765 says "9 consumer modules". "10" is wrong and internally inconsistent with line 765.
- **File evidence**: `grep -rln` distinct module count = 9 (excl. self M12).
- **verify_cmd**: `grep -rln "pm_interest" /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/ --include="*.gms" | grep -oE "^[0-9]+" ... | sort -un` → 12,13,29,32,38,39,41,56,58,70 (10 incl. self → 9 consumers).
- **Confirmed**: true.
- **Proposed fix**: line 835 "(10 modules via `pm_interest`)" → "(9 modules via `pm_interest`)".

### Bug module_12-B3 — Missing default-state caveat on Module 70 consumer
- **Severity**: Minor
- **Class**: 4 / capability-vs-default (MANDATE 4)
- **Trigger** (§1 Minor): wrong detail a careful reader could check; tie-breaker pulls below Major because the doc IS listing capability and M70 genuinely references the variable.
- **Claim in answer**: line 765 lists "70 (livestock)" among consumers with no realization caveat; line 835 implies all are active by default.
- **Reality in code**: M70 consumes `pm_interest` ONLY in the non-default `fbask_jan16_sticky` realization. The DEFAULT `fbask_jan16` lists it in `not_used.txt`.
- **File evidence**: `modules/70_livestock/fbask_jan16/not_used.txt:2` ("pm_interest,input,Since no capital stocks are implemented…"); `modules/70_livestock/fbask_jan16_sticky/presolve.gms:80`.
- **verify_cmd**: `grep -rn "pm_interest" /tmp/magpie_develop_ro/modules/70_livestock/fbask_jan16/` → only `not_used.txt`; `... /fbask_jan16_sticky/` → equations.gms + presolve.gms:80.
- **Confirmed**: true.
- **Proposed fix**: annotate the M70 entry at line 765: "70 (livestock — only in the non-default `fbask_jan16_sticky` realization; the default `fbask_jan16` does not use it)."

---

## Advisory check (pre-run flag) — REFUTED

**Flag**: "check_units.py flags module_12.md:825 - pm_interest unit shown as 'TC' but canonical is '% per yr'."

**Verdict**: **False positive — refuted.** Doc line 825 is prose in the Conservation Laws section: "Interest rates (`pm_interest`) scale annualized capital costs in Modules 13 (TC), 39 (land conversion), and 41 (irrigation)." The token "TC" the checker parsed is the abbreviation for **Technical Change (Module 13)**, inside "Modules 13 (TC)" — it is NOT a unit field. There is no unit declaration at line 825. No edit warranted for this line.

**Real units situation (for the record, not a flagged bug)**: code canonical string is "% per yr" (`declarations.gms:9`), but stored values are fractions (0.1 = 10%, used directly in the formula). The doc reflects both faces: line 809 says "% per yr" (matches code string exactly — correct), while lines 14 and 170 say "fraction per year (1)" (describes the actual value semantics — arguably more accurate than the code label). This is the standard MAgPIE label-vs-value mismatch; line 809's "% per yr" is faithful to code and should NOT be changed. The internal label/value duality is defensible documentation, not a code-checkable error, so it is left un-flagged.

---

## Deferred (not code-verifiable here / uncertain — NO edit proposed)

- **Module-09 development-state formula** (doc lines 295-301): doc presents `development_state = (GDP_pc - GDP_min)/(GDP_max - GDP_min)` attributed to "Calculation (in Module 09)". In GAMS, M09 only READS `im_development_state` from input file `f09_development_state` (`modules/09_drivers/aug17/preloop.gms:45,54`) — there is no such in-GAMS formula. BUT the formula plausibly describes the R-preprocessing normalization (a 0-1 GDP measure), which I cannot read here, and it is a secondary cross-module aside, not a load-bearing M12 interface claim. Per "do not invent a bug when unsure" → deferred. If a preproc-agent confirms no min-max normalization, downgrade to a Minor doc clarification on the M09-doc, not M12.
- **`f12_interest_fader.csv` / `f12_interest_rate_coupling.csv` example values** (doc lines 250-258, 535-557, 583-589): the actual CSVs are not present in the develop worktree (only the `input/files` manifest lists them — they are downloaded input data). The doc labels its values "Example", so no claim of real data is made. Cannot verify the exact fader curve; timing (2025→2050) IS verified against `realization.gms:15-16`. No bug; values unverifiable.
- **`$ondelim`/`$offdelim` omission** in the doc's reproduced fader/coupling GAMS blocks (doc lines 238-243, 271-277) vs actual `input.gms:49-55,57-63`: the doc drops the delimiter directives. This is an illustrative-snippet simplification, not a load-bearing claim; borderline Informational. Noting, not flagging, to keep false-positive rate low.

---

## Summary

Citations, formula, parameter defaults, and the input-dependency side are all verified correct. The defect is the **consumer set**: four prominent sections (lines 15, 173-176, 321, 396-399) still say only 3 consumers (13/39/41) while code has 9 (13,29,32,38,39,41,56,58,70) and the doc's own lines 765/835 carry the corrected list — a stale-after-partial-update Critical (R20 anchor). Plus a Major count inconsistency ("10" vs the real 9 at line 835) and a Minor missing default-realization caveat on M70. The pre-run units advisory on line 825 is a checker false positive (TC = Technical Change abbreviation, not a unit).
