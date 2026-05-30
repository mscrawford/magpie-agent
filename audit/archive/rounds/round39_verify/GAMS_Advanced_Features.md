# Round 39 Adversarial Verification — GAMS_Advanced_Features.md

Verifier: highest-capability adversarial verifier. Ground truth: /tmp/magpie_develop_ro (MAgPIE develop).
Method: mechanical citation check (test -f / wc -l / read exact line) + isolated grep with positive controls.
All 6 auditor bugs reproduced. Verdicts: 5 UPHELD, 1 UPHELD-with-citation-nuance (GAF-1).

---

## GAF-1 — UPHELD (Critical). Hallucinated var names + fabricated code.

Doc lines 1131-1136 cite flexreg_apr16/presolve.gms:13 with
`im_demandshare_reg.l(i,kall) = f17_prod_init(i,kall)/sum(i2,f17_prod_init(i2,kall));`

Mechanical:
- `wc -l flexreg_apr16/presolve.gms` = 18 (so :13 in range).
- Read line 12 = `if (ord(t) = 1,`; line 13 = BLANK; line 14 = `$ifthen "%c17_prod_init%" == "on"`; line 15 = `vm_prod.l(j,kcr) = pm_prod_init(j,kcr);`; line 16 = `$endif`; line 18 = `);`.
- `rg -l im_demandshare_reg modules/` -> ABSENT everywhere.
- `rg -l f17_prod_init modules/` -> ABSENT everywhere.
- POSITIVE CONTROL `rg -l pm_prod_init modules/17_production/` -> declarations.gms + presolve.gms (real).

Both cited identifiers are fabricated; the verbatim assignment does not exist. UPHELD.

CITATION NUANCE on the proposed_fix: the 3-line replacement block (`$ifthen ... vm_prod.l(j,kcr) = pm_prod_init(j,kcr); ... $endif`) is verbatim-correct, BUT the fix anchors it at presolve.gms:14 — line 14 is the `$ifthen`, while the `vm_prod.l` assignment is line 15. Fix is safe; recommend citing the range :14-16 (or :15 for the assignment) rather than bare :14.

---

## GAF-2 — UPHELD (Major). Conceptual pseudo-code as real code + out-of-range citation.

Doc lines 931-936 cite fbask_jan16/presolve.gms:119 and lines 1103-1106 cite :120, both with
`p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i);` (a carry-forward).

Mechanical:
- `wc -l fbask_jan16/presolve.gms` = 70 -> lines 119 AND 120 are OUT OF RANGE.
- `rg 'p70_cattle_stock_proxy\(t,i\) *= *p70_cattle_stock_proxy\(t-1,i\)' modules/` -> CARRY_FORWARD_ABSENT (confirmed twice; second probe scoped to the file also absent).
- Read presolve.gms:52 = `if (ord(t)>1,`; :53 = `p70_incr_cattle(t,i) = ( ... * (p70_cattle_stock_proxy(t,i)/p70_cattle_stock_proxy(t-1,i)) + ...` — a growth RATIO, not a carry-forward.
- POSITIVE CONTROL `rg -l p70_cattle_stock_proxy modules/70_livestock/` -> fbask_jan16 declarations+presolve (real).

Citation out of range AND the snippet does not exist anywhere. UPHELD.
Proposed-fix replacements verified real: ratio guarded by `if (ord(t)>1,` at presolve.gms:52 (ratio expr on :53); alt carry-forward `pcm_land(j,land) = vm_land.l(j,land);` confirmed at 10_land/landmatrix_dec18/postsolve.gms:9.

---

## GAF-3 — UPHELD (Major). Wrong variable prefix (v10_ vs vm_) + citation drift.

Doc lines 976-980 cite landmatrix_dec18/equations.gms:16 with
`sum(land_to$(not sameas(land_from,land_to)), v10_lu_transitions(j2,land_from,land_to))`.

Mechanical:
- `wc -l equations.gms` = 54 (:16 in range).
- Read equations.gms:16 = BLANK (line 14 = `sum(land, vm_land(j2,land)) =e=`). The not-sameas summations are at lines 32-33 and 37-38, and both use `vm_lu_transitions`.
- `rg -l v10_lu_transitions modules/` -> ABSENT everywhere.
- POSITIVE CONTROL `rg -l vm_lu_transitions modules/10_land/` -> declarations/equations/presolve/postsolve (real, vm_ interface var).

Variable name wrong (v10_ -> vm_) and cited line is blank. UPHELD.
Proposed-fix re-cite to equations.gms:37 verified: line 37 = `sum(land_to$(not sameas(land_from,land_to)),`.

---

## GAF-4 — UPHELD (Major). Stale file:line citation (x2).

(A) Doc line 663 cites price_aug22/preloop.gms:34 for `v56_emis_pricing.fx(...) = 0;`.
(B) Doc line 1207 cites preloop.gms:82 for `loop(t_all$(m_year(t_all) > max(m_year(%c56_mute_ghgprices_until%), s56_fader_start*s56_ghgprice_fader)),...`.

Mechanical (`wc -l` = 123; all lines in range):
- preloop.gms:13 = `v56_emis_pricing.fx(i,emis_oneoff,pollutants)$(not sameas(pollutants,"co2_c")) = 0;` (the real location).
- preloop.gms:34 = `p56_region_fader_shr(t_all,i) = sum(...)` — NOT the .fx. Doc's :34 STALE.
- preloop.gms:96 = `loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),s56_fader_start*s56_ghgprice_fader)),` (the real loop).
- preloop.gms:82 = `im_pollutant_prices(...,"n2o_n_indirect",...)$(... > s56_limit_ch4_n2o_price*...)` — an n2o clamp, NOT the loop. Doc's :82 STALE.

Both auditor targets (:13, :96) confirmed correct. UPHELD.

---

## GAF-5 — UPHELD (Major). Stale citation + fabricated multi-line reformat.

Doc lines 1038-1043 cite nlp_par/solve.gms:52-53 with a multi-line
`loop(i2, j2(j)$cell(i2,j) = yes; * Dynamically activate cells for region i2 );`.

Mechanical (`wc -l` = 146; lines in range):
- solve.gms:52 = `p80_counter(h) = p80_counter(h) + 1;`; :53 = `p80_extra_solve(h) = 1;` — inside the collection-loop `if(handleStatus...)` block, NOT cell activation. Doc's :52-53 STALE.
- The real pattern is a ONE-LINER: solve.gms:40 = `loop(i2, j2(j)$cell(i2,j) = yes);` (submission loop) AND solve.gms:60 = identical (collection loop).

Citation stale and the doc reformatted a one-liner into a fabricated 3-line block. Auditor's :40 correct. UPHELD.

---

## GAF-6 — UPHELD (Minor). Hallucinated var names in illustrative blocks.

Doc lines 621/647/745-746 use `vm_production` (.lo/.up) and `vm_trade` (.up) in unanchored "Example" blocks.

Mechanical:
- `rg -n vm_production modules/` -> ABSENT_EVERYWHERE (cross-checked with `grep -rw` -> also empty).
- `rg -nw vm_trade modules/` -> ABSENT_EXACT; `rg -n 'vm_trade\(' modules/` -> NO_PAREN_FORM.
- POSITIVE CONTROL: real production var `vm_prod(j,k)` at 17_production/flexreg_apr16/declarations.gms:9; dir-searchable positive control on module 21 returns `vm_cost_trade_tariff/margin/feasibility(i)`.

Neither `vm_production` nor `vm_trade` is a real MAgPIE variable. UPHELD as a Class-2 illustrative hallucination (low priority; sits in Example blocks mixed with real names vm_land/vm_cost_glo, so a reader cannot distinguish).

Note: auditor's parenthetical "real trade family is vm_trade_*/vm_exp_*/vm_imp_*" is imprecise (actual trade vars are vm_cost_trade_* and the realization-specific quantity vars), but this is collateral and does not affect the verdict.

---

## Summary

| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| GAF-1 | other (fabricated code) | true | UPHELD (fix cite :14 -> prefer :14-16/:15) |
| GAF-2 | other (out-of-range + fabricated) | false (119/120 OOR) | UPHELD |
| GAF-3 | producer_declaration (var name+prefix) | true | UPHELD |
| GAF-4 | other (stale citation x2) | true (auditor :13,:96) | UPHELD |
| GAF-5 | other (stale citation + reformat) | true (auditor :40) | UPHELD |
| GAF-6 | producer_declaration (hallucinated name) | true | UPHELD |

All proposed fixes point at real, verified code. The only refinement: GAF-1's fix should anchor the assignment at line 15 (line 14 is the `$ifthen` guard) — cite the :14-16 block.
