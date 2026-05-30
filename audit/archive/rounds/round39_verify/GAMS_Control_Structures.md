# Round 39 Adversarial Verification — GAMS_Control_Structures.md

**Verifier**: Opus 4.8 (adversarial). **Ground truth**: official GAMS docs (gams.com) for language semantics; `/tmp/magpie_develop_ro` for MAgPIE-convention claims.
**Date**: 2026-05-30.

## Summary

| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| GCS-B2 | other (hallucinated var/eq name) | true | UPHELD |
| GCS-B3 | other (hallucinated var name) | true | UPHELD |
| GCS-B4 | other (fabricated formula) | true | UPHELD |
| GCS-B5 | other (stale citation) | true | UPHELD |
| GCS-B6 | other (stale citation) | true | UPHELD |
| GCS-B7 | other (stale citation) | true | UPHELD |
| GCS-B8 | other (stale citation + fabricated assignment) | true | UPHELD |
| GCS-B9 | other (stale citation) | true | UPHELD |
| GCS-B10 | other (stale citation) | true | UPHELD |
| GCS-B1 | other (GAMS semantics + over-inclusive location list) | true | CORRECTED |

All 10 file-evidence citations exist and are in range; every claimed identifier/line content reproduced mechanically. Nine bugs UPHELD as-is. B1 CORRECTED: its core GAMS-semantics claim is verified against gams.com, but its recurrence line-list is over-inclusive (sweeps in valid column-1 comments and lines with no comment).

---

## Mechanical file-existence + length (Step A, all bugs)

```
modules/10_land/landmatrix_dec18/equations.gms        EXISTS  54 lines
modules/17_production/flexreg_apr16/presolve.gms       EXISTS  18 lines
modules/35_natveg/pot_forest_may24/presolve.gms        EXISTS 294 lines
modules/35_natveg/pot_forest_may24/declarations.gms    EXISTS 143 lines
modules/70_livestock/fbask_jan16/presolve.gms          EXISTS  70 lines
modules/56_ghg_policy/price_aug22/preloop.gms          EXISTS 123 lines
modules/32_forestry/dynamic_may24/preloop.gms          EXISTS 228 lines
modules/80_optimization/nlp_par/solve.gms              EXISTS 146 lines
```

---

## GCS-B2 — UPHELD (Critical, hallucinated var/eq name)

**Doc claim**: `q10_land_from(j2,land_from)` with variable `v10_lu_transitions`, cited `equations.gms:13-16`.

**Mechanical (read equations.gms in full)**:
- :13-15 = `q10_land_area(j2)`. Real equations: q10_land_area, q10_transition_to (:19), q10_transition_from (:23), q10_landexpansion (:30), q10_landreduction (:35), q10_cost (:42), q10_landdiff (:50). No `q10_land_from`.
- `rg -n 'q10_land_from' modules/10_land/` → NO MATCH.
- `rg -n 'v10_lu_transitions' modules/10_land/` → NO MATCH. Positive control `rg -cn 'vm_lu_transitions' .../equations.gms` → 4 hits. Real name is `vm_lu_transitions` (vm_ prefix).

**proposed_fix verify**: `equations.gms:30-40` = q10_landexpansion + q10_landreduction (off-diagonal sum with `vm_lu_transitions`) — verbatim match. `:13-15` = q10_land_area. Both fix citations sound.

**Verdict**: UPHELD. Auditor's reality reproduces exactly.

## GCS-B3 — UPHELD (Critical, hallucinated var name)

**Doc claim**: `im_demandshare_reg.l(i,kall) = f17_prod_init(i,kall)/...`, cited `presolve.gms:13`.

**Mechanical (read presolve.gms, 18 lines)**: :12-18 real block =
```
if (ord(t) = 1,
$ifthen "%c17_prod_init%" == "on"
vm_prod.l(j,kcr) = pm_prod_init(j,kcr);
$endif
    );
```
- `rg -n 'im_demandshare_reg' modules/` → NO MATCH. `rg -n 'f17_prod_init' modules/` → NO MATCH. Positive control `pm_prod_init` → 2 hits in this file.
- Real block initializes **production levels** (vm_prod.l), not demand shares — caption fix is warranted.

**proposed_fix verify**: `presolve.gms:12-18` matches verbatim. Sound.

**Verdict**: UPHELD.

## GCS-B4 — UPHELD (Critical, fabricated formula)

**Doc claim**: `p35_maturesecdf(...) = (s35_natveg_harvest_secdforest * sum(ac_est,...)) / (...)`, cited `presolve.gms:82`.

**Mechanical (read presolve.gms:110-123, declarations.gms:20-31)**:
- Real assignment at :116-117: `p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) = p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);`
- `p35_maturesecdf` declared at declarations.gms:26 (param exists). The **formula** in the doc is fabricated.
- `rg -n 's35_natveg_harvest_secdforest' modules/` → NO MATCH (scalar does not exist). Confirms fabrication.

**proposed_fix verify**: `presolve.gms:116-117` matches verbatim. Sound.

**Verdict**: UPHELD.

## GCS-B5 — UPHELD (Major, stale citation)

**Doc claim**: `if (ord(t)>1, p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i); );`, cited `presolve.gms:120` and `:119-121`.

**Mechanical (file 70 lines; :119-121 OUT OF RANGE)**:
- Real `if (ord(t)>1, ...)` block at :52-58 computes `p70_incr_cattle`, with else-branch = 1.
- `rg -n 'p70_cattle_stock_proxy\(t-1' modules/70_livestock/` → only fbask_jan16/presolve.gms:53 (and sibling fbask_jan16_sticky:53), inside the p70_incr_cattle ratio. The carry-forward `p70_cattle_stock_proxy(t,i)=p70_cattle_stock_proxy(t-1,i)` exists nowhere.

**proposed_fix verify**: `presolve.gms:52-58` matches the real if/else block verbatim. Sound. (Fixer may also drop the file:line and use a generic illustration, per the fix's alternative.)

**Verdict**: UPHELD.

## GCS-B6 — UPHELD (Major, stale citation)

**Doc claim**: `if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > sum(...), ...`, cited `presolve.gms:70` and `:69-75`.

**Mechanical (file 70 lines; :75 OUT OF RANGE)**:
- The `ord(t)=smax... AND card(t)>sum(...)` condition is at :16, nested inside the outer `if (sum(sameas(t_past,t),1) = 1,` at :14. Inner-condition text matches the doc snippet verbatim.

**proposed_fix verify**: `:16` is correct for the inner-if header. Fix instruction to re-quote lines 14-20 correctly captures the now-visible outer wrapper. Sound. (Minor nuance: auditor calls :16 a "single-line if header" — it is the **nested** if, not a top-level one; the fix's 14-20 re-quote handles this.)

**Verdict**: UPHELD.

## GCS-B7 — UPHELD (Major, stale citation)

**Doc claim**: `v56_emis_pricing.fx(i,emis_oneoff,pollutants)$(not sameas(pollutants,"co2_c")) = 0;`, cited `preloop.gms:34`.

**Mechanical (read preloop.gms:1-40)**:
- Statement is at :13 (verbatim). :34 = `p56_region_fader_shr(t_all,i) = ...` (different statement). Content correct, line stale.

**proposed_fix verify**: `:13` correct. Sound.

**Verdict**: UPHELD.

## GCS-B8 — UPHELD (Major, stale citation + fabricated assignment)

**Doc claim**: `loop(ac$(ord(ac) > 1), p32_carbon_density_ac(t,j,"acx",ag_pools) = p32_carbon_density_ac(t,j,ac,ag_pools); );`, cited `preloop.gms:65` and `:65-67`. 1.5.2 section conceptual mismatch (domain-restriction section showing a loop).

**Mechanical (read preloop.gms:60-84)**:
- :65 = `$endif`; :66 = `p32_time(ac) = ord(ac);` (Faustmann block, :66-81). NOT a loop. Citation stale.
- `rg -n 'p32_carbon_density_ac' modules/32_forestry/`: parameter `p32_carbon_density_ac` IS declared (declarations.gms:19) and populated (presolve.gms:59,61,65,68,72) — but ALWAYS indexed by "aff"/"plant"/"ndc", never "acx".
- `rg -n 'p32_carbon_density_ac\([^)]*"acx"' modules/32_forestry/` → NO MATCH. The specific `p32_carbon_density_ac(t,j,"acx",ag_pools)` assignment is fabricated. (Auditor wrote "does not exist anywhere" — strictly the *parameter* exists but the cited *assignment with "acx"* does not; the doc snippet is still fabricated.)
- Real `loop(ac$(ord(ac) > 1)` exists at preloop.gms:22 but assigns `p32_carbon_density_ac_marg`, not the doc's construct.

**proposed_fix verify**: Fix is appropriately GENERIC — "read a verified loop(ac$(...)) construct and cite its exact line, OR substitute a generic illustration." It does NOT pin a wrong line, so it cannot reintroduce a fabrication. Note for fixer: a verified real loop is preloop.gms:22 (`loop(ac$(ord(ac) > 1), p32_carbon_density_ac_marg(t_all,j,ac) = (...)/5; );`). The 1.5.2 conceptual-mismatch point (should show an equation with `$` before `..`, not a loop) is valid.

**Verdict**: UPHELD.

## GCS-B9 — UPHELD (Major, stale citation)

**Doc claim**: `loop(i2, j2(j)$cell(i2,j) = yes);` cited `solve.gms:52-53`; `loop(h$p80_handle(h), ...)` cited `:46`.

**Mechanical (read solve.gms:36-55)**:
- `loop(i2, j2(j)$cell(i2,j) = yes);` at :40 (inside `loop(h,` submission loop). :52-53 are `p80_counter`/`p80_extra_solve` assignments. Stale.
- `loop(h$p80_handle(h),` at :50 (collection loop). :46 = `);`. Stale. Content correct both.

**proposed_fix verify**: `:40` and `:50` correct. Sound.

**Verdict**: UPHELD.

## GCS-B10 — UPHELD (Major, stale citation)

**Doc claim**: `loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),s56_fader_start*s56_ghgprice_fader)), ...)`, cited `preloop.gms:82`.

**Mechanical (read preloop.gms:78-102)**:
- Loop at :96 (verbatim). :82 = `im_pollutant_prices(...,"n2o_n_indirect",...)` price-cap. Content correct, line stale.

**proposed_fix verify**: `:96` correct. Sound.

**Verdict**: UPHELD.

## GCS-B1 — CORRECTED (Major, GAMS semantics correct; location list over-inclusive)

**Doc claim**: Same-line `code;  * comment` examples (representative line 49: `b $ (2*a - 4) = 7;          * Assign b=7 if 2*a-4 is non-zero`) would not compile because GAMS treats `*` as a comment ONLY in column 1; an asterisk after code is parsed as the operator; end-of-line comments require `!!` under `$onEolCom`.

**Ground-truth verify (gams.com/latest/docs/UG_GAMSPrograms.html, WebFetch)**:
- "Users may insert a single line comment on any line by placing an asterisk `*` in column 1." / "An asterisk in column one means that the line will not be processed, but treated as a comment." → asterisk = comment ONLY in column 1. CONFIRMED.
- "The dollar control option `$onEolCom` activates end-of-line comments. The default symbol ... is a double exclamation mark `!!`." → CONFIRMED.
- Minor: `*` after code is **multiplication** (the binary operator; `**` is exponentiation). Auditor said "MULTIPLICATION" — correct.
- Doc's own line 443 uses `!!` (`value(i,j) $ (not sameas(i,j)) = distance(i,j);  !! Off-diagonal only`) — internal inconsistency CONFIRMED.
- Real MAgPIE column-1 example cited (preloop.gms:8) = `* starting value ...` (column 1) — CONFIRMED; that file has no same-line `; *` comments.

**Why CORRECTED, not UPHELD — the recurrence line-list is over-inclusive.** Inspecting all cited lines, three categories appear:
1. GENUINE same-line `code;  * comment` (the real bug): lines **49, 50, 60, 61, 102, 103, 159, 160, 705, 712, 757, 903, 1045**. These misparse if copied literally and should become `!!` (matching line 443) or move to a column-1 line above.
2. VALID column-1 `*` comments (NOT bugs; fixer must NOT touch): lines **449, 454, 459, 651, 657**. The auditor's own proposed_fix already exempts these ("Column-1 '*' lines already inside fenced blocks are fine").
3. Lines with NO same-line `*` comment at all (mis-listed as bug sites): lines **82, 83, 124, 177, 196, 232 (uses `/* */`), 502, 559, 599, 606, 613, 620, 760, 870, 957, 1004, 1010, 1024**. These are loop/equation/`$abort` lines; nothing to change.

The CORE claim and the representative example are correct (citation_ok=true: gams.com evidence + preloop.gms:8 control + line 49 exhibits the pattern). The CORRECTION is scoping: apply the `* → !!` conversion ONLY to category-1 lines. Do NOT convert column-1 comment lines (category 2) and do NOT edit category-3 lines.

**Verdict**: CORRECTED. corrected_set = restrict the fix to the category-1 same-line-comment lines enumerated above; leave column-1 comments and no-comment lines untouched.

---

## Cross-bug notes for the fixer

- All nine UPHELD bugs have verbatim-correct replacement snippets in their proposed_fix; the embedded file:line citations (B2 :30-40/:13-15, B3 :12-18, B5 :52-58, B6 :16, B7 :13, B9 :40/:50, B10 :96, B4 :116-117) were all spot-checked and reproduce.
- B8: do NOT reintroduce a specific fabricated assignment. If a real loop is wanted, preloop.gms:22 (`loop(ac$(ord(ac) > 1), p32_carbon_density_ac_marg ... )`) is verified; otherwise use a generic illustration with no MAgPIE file:line.
- B1: scope the fix to genuine same-line `* comment` lines only (list in the B1 section). The `!!` form (already used correctly at doc line 443) is the in-doc precedent.
