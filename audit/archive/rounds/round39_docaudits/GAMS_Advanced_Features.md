# Doc Audit — reference/GAMS_Advanced_Features.md (Round 39)

**Auditor**: Opus 4.8 (1M)
**Date**: 2026-05-30
**Develop HEAD**: `5ea394f` (Merge PR #877 rc2-4.14.0), read-only clone `/tmp/magpie_develop_ro`
**Ground truth**: official GAMS docs (gams.com/latest) for language semantics; develop code for MAgPIE-convention claims.

---

## Scope and method

This is a GAMS-language reference (macros, dollar-control options, variable attributes, set operations, time indexing). Most content is stable GAMS syntax → low bug density, as the pre-run advisory predicted. The MAgPIE-specific surface is: (a) the `core/macros.gms` macro citations + bodies, (b) a handful of module file:line citations used as examples, (c) illustrative variable names.

I enumerated every load-bearing, code-checkable claim and verified each:
- 14 macro citations (line number + body) against `core/macros.gms`.
- 6 module/core file:line citations against develop.
- GAMS-language claims (`.fx` semantics, default bounds tables, attribute list, dollar-control options, inline-comment gating, set-operation symbols) against gams.com via WebFetch.
- Illustrative variable names (`vm_land`, `vm_cost_glo`, `vm_production`, `vm_trade`, `pcm_land`, `pm_land_hist`, `pm_land_start`) against declarations.

---

## VERIFIED CORRECT (high-confidence)

### Macros (`core/macros.gms`) — all citations + bodies correct
Every cited line number and macro body matches develop exactly:

| Macro | Doc cite | Develop | Body match |
|-------|----------|---------|-----------|
| `m_weightedmean` | macros.gms:16 | 16 | exact |
| `m_boundfix` | macros.gms:14 | 14 | exact (doc drops trailing `;`, harmless) |
| `m_growth_vegc` | macros.gms:18 | 18 | exact |
| `m_growth_litc_soilc` | macros.gms:20 | 20 | exact |
| `m_annuity_ord` | macros.gms:25 | 25 | exact |
| `m_annuity_due` | macros.gms:31 | 31 | exact |
| `m_year` | macros.gms:37 | 37 | exact (`+1964`, 1964 base) |
| `m_yeardiff` | macros.gms:41 | 41 | exact |
| `m_timestep_length` | macros.gms:51 | 51 | exact |
| `m_fillmissingyears` | macros.gms:68-75 | 68-75 | exact |
| `m_linear_time_interpol` | macros.gms:79-83 | 79-83 | exact |
| `m_sigmoid_time_interpol` | macros.gms:86-91 | 86-91 | exact |

`verify_cmd`: `cat -n /tmp/magpie_develop_ro/core/macros.gms` (full file read, 119 lines).
The Jordan et al. (2000) reference and the "used for TC, land conversion, irrigation" note for `m_annuity_due` both faithfully reproduce the code comment at macros.gms:27-28.
`m_growth_vegc` "(Module 52 - Carbon)" attribution confirmed: used in `modules/52_carbon/normal_dec17/start.gms`.

### Alias citations — correct
`core/sets.gms:222` = `alias(t,t2);`; `:358-360` = `alias(ac,ac2);`/`(ac_sub,ac_sub2)`/`(ac_est,ac_est2)`. All exact.
`verify_cmd`: `rg -n "alias\(" /tmp/magpie_develop_ro/core/sets.gms` → 222, 358, 359, 360.

### GAMS-language claims — correct (verified against gams.com)
- **`.fx` semantics** (§3.4 line 656): doc claims `.fx` sets `.lo=.up=.l=value` (activity level also reset). GAMS official: "The attribute .fx also resets the activity level .l to the fixed value." **CORRECT.**
- **Default bounds by type** (§3.2, §3.3): free→±inf, positive→[0,+inf], negative→[-inf,0], binary→[0,1], integer→[0,+inf]. All match GAMS Table 1. **CORRECT.**
- **Attribute list + read-only attrs** (§3.8): `.scale`, `.prior`, `.stage` (assignable); `.range=.up-.lo`, `.slacklo=max(0,.l-.lo)`, `.slackup=max(0,.up-.l)`, `.slack=min(...)` (read-only). All match GAMS. **CORRECT.**
- **Dollar control** (§2): `$batInclude` %1/%2/%3 substitution; `$eval` compile-time numerical eval; `$drop`/`$dropGlobal`/`$dropLocal`; `$ifI` case-insensitive; `$ifE` expression-eval; `$onText/$offText` block comment; `/* */` requires `$onInline`; `!!` requires `$onEolCom`. All confirmed on gams.com. **CORRECT.** (The §2.9 inline-comment caveat is notably precise and right.)
- Set-operation symbols `+` (union), `*` (intersection), `-` (difference), `not` (complement) match GAMS. **CORRECT.** (The added `or`/`and` word-form equivalence is a nuance — see Deferred.)

### Illustrative MAgPIE names that ARE real
`vm_land` (real), `vm_cost_glo` (M11 `default/declarations.gms`), `pcm_land` (M10/29/32/34…), `pm_land_hist` (M10 `landmatrix_dec18/declarations.gms:10`), `pm_land_start` (M10 declarations.gms:9), `p70_cattle_stock_proxy` (M70 declarations.gms:37). All confirmed.

---

## BUGS

### BUG-1 (Critical) — Fabricated variable + fabricated code at M17 flexreg presolve:13
**Class**: 2 (hallucinated variable name) / 1 (prefix) | **Trigger**: "Invented variable name presented as authoritative" + "Fabricated formula presented as code's actual implementation".
**Doc line**: GAMS_Advanced_Features:1131-1136 (§5.3).
**Claim**: cites `modules/17_production/flexreg_apr16/presolve.gms:13` with verbatim code
`im_demandshare_reg.l(i,kall) = f17_prod_init(i,kall)/sum(i2,f17_prod_init(i2,kall));`
**Reality**: Neither `im_demandshare_reg` nor `f17_prod_init` exists ANYWHERE in develop. The actual presolve.gms:13 is `if (ord(t) = 1,`; the surrounding real code (lines 10-15) is `pm_prod_init(j,kcr)=...` and (under `$ifthen "%c17_prod_init%" == "on"`) `vm_prod.l(j,kcr) = pm_prod_init(j,kcr);`. The doc invented both names AND the assignment.
**File evidence**: `modules/17_production/flexreg_apr16/presolve.gms:10-16` (real content); names absent repo-wide.
**verify_cmd**:
- `rg -n "im_demandshare_reg" /tmp/magpie_develop_ro/` → NO MATCH (repo-wide)
- `rg -n "f17_prod_init" /tmp/magpie_develop_ro/modules/` → NO MATCH
- positive control `rg -ln "p70_cattle" /tmp/magpie_develop_ro/modules/` → 4 files (search works)
- `sed -n '10,16p' .../flexreg_apr16/presolve.gms` → shows `pm_prod_init` / `if (ord(t)=1,` / `vm_prod.l`
**confirmed**: true.
**Note**: this is the realization-default case (`flexreg_apr16` is M17's only realization, fine) but the variable/code is invented. Presented as a verbatim cited example a reader could copy — Critical per the fabricated-implementation trigger.
**proposed_fix**: Replace the example block (lines 1132-1136) with the real first-timestep init from this file:
```gams
$ifthen "%c17_prod_init%" == "on"
vm_prod.l(j,kcr) = pm_prod_init(j,kcr);
$endif
```
cited as `modules/17_production/flexreg_apr16/presolve.gms:14`. (Or pick a simpler verified `ord(t)=1` example.)

### BUG-2 (Major) — Fabricated code example + out-of-range citation at M70 presolve:119/120
**Class**: 4 (conceptual pseudo-code presented as real) / 10 (stale/out-of-range citation) | **Trigger**: "File:line citation drift to … different content" + fabricated-implementation. Anchor: MANDATE-16 module_21 out-of-range case.
**Doc line**: GAMS_Advanced_Features:931-936 (§4.3) AND :1103-1106 (§5.2).
**Claim**: §4.3 cites `presolve.gms:119` →
`if (ord(t)>1, p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i); );`
§5.2 cites `presolve.gms:120` → `p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i);`
**Reality**: `fbask_jan16/presolve.gms` is only **70 lines** — lines 119/120 do not exist. The carry-forward assignment `p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i)` does NOT exist anywhere. What exists (line 52): `if (ord(t)>1, p70_incr_cattle(t,i) = ( ... * (p70_cattle_stock_proxy(t,i)/p70_cattle_stock_proxy(t-1,i)) + ... );` — a growth RATIO inside `p70_incr_cattle`, not a simple carry-forward. The variable `p70_cattle_stock_proxy` is real; the cited assignment is invented and the line numbers are out of range.
**File evidence**: `modules/70_livestock/fbask_jan16/presolve.gms` (70 lines total); `if (ord(t)>1` at line 52; ratio usage lines 53-54.
**verify_cmd**:
- `wc -l .../fbask_jan16/presolve.gms` → `70`
- `rg -n "p70_cattle_stock_proxy\(t,i\)\s*=\s*p70_cattle_stock_proxy\(t-1,i\)" /tmp/magpie_develop_ro/modules/` → NO MATCH (no carry-forward anywhere)
- `rg -n "ord\(t\)>1" .../fbask_jan16/presolve.gms` → `52:`
- `sed -n '50,55p'` → shows `p70_incr_cattle` ratio block
**confirmed**: true. Two doc locations affected (§4.3 and §5.2 share the same fabricated snippet).
**Severity rationale**: pedagogical example of a generic GAMS pattern (lag operator / `ord(t)>1`), not a load-bearing interface/default/consumer claim, so Major not Critical — but the "verbatim" cited code is fabricated and the line is out of range, which misleads any reader who opens the file.
**proposed_fix**: Replace both example snippets with a real lag-operator example. Best in-file option (lines 53-54): `p70_incr_cattle` uses `p70_cattle_stock_proxy(t,i)/p70_cattle_stock_proxy(t-1,i)` guarded by `if (ord(t)>1,` at `modules/70_livestock/fbask_jan16/presolve.gms:52`. Quote that ratio (cited :52) rather than the invented assignment; or use a documented carry-forward from elsewhere (e.g. M10 postsolve `pcm_land(j,land) = vm_land.l(j,land)`).

### BUG-3 (Major) — Wrong prefix + citation drift: `v10_lu_transitions` at M10 equations:16
**Class**: 1 (prefix confusion) / 10 (citation drift) | **Trigger**: "Wrong variable prefix (v{N}_ vs vm_) — semantic scope wrong" + citation drift to different content.
**Doc line**: GAMS_Advanced_Features:976-980 (§4.3 sameas example).
**Claim**: cites `modules/10_land/landmatrix_dec18/equations.gms:16` with
`sum(land_to$(not sameas(land_from,land_to)), v10_lu_transitions(j2,land_from,land_to))`.
**Reality**: (a) the variable is **`vm_lu_transitions`** (a `vm_` interface variable), NOT `v10_lu_transitions` — `rg "v10_lu_transitions"` returns nothing; the real declared name is `vm_lu_transitions`. (b) equations.gms:16 is `vm_land(j2,land_to);` (tail of `q10_transition_to`); the `not sameas(land_from,land_to)` summations are at lines 32 and 37, not 16.
**File evidence**: `modules/10_land/landmatrix_dec18/equations.gms:32,37` (`sum(land_from$(not sameas(land_from,land_to)),` / `sum(land_to$(not sameas(land_from,land_to)),`); declared `vm_lu_transitions`.
**verify_cmd**:
- `rg -n "v10_lu_transitions" /tmp/magpie_develop_ro/` → NO MATCH
- `rg -n "vm_lu_transitions|sameas\(land_from,land_to\)" .../landmatrix_dec18/equations.gms` → 32, 37 (and `vm_lu_transitions` present)
- `sed -n '12,22p'` → line 16 = `vm_land(j2,land)` region
**confirmed**: true.
**proposed_fix**: Change `v10_lu_transitions` → `vm_lu_transitions` and re-cite to `modules/10_land/landmatrix_dec18/equations.gms:37` (the `sum(land_to$(not sameas(land_from,land_to)), vm_lu_transitions(j2,land_from,land_to))` line).

### BUG-4 (Major) — Citation drift ×2 in M56 examples (lines 34, 82 → actual 13, 96)
**Class**: 10 (stale file:line citation) | **Trigger**: "File:line citation drift to adjacent but different content".
**Doc line**: GAMS_Advanced_Features:663 (§3.4) and :1207 (§5.7).
**Claim A** (§3.4): `modules/56_ghg_policy/price_aug22/preloop.gms:34` for `v56_emis_pricing.fx(i,emis_oneoff,pollutants)$(not sameas(pollutants,"co2_c")) = 0;`.
**Claim B** (§5.7): `preloop.gms:82` for `loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"), s56_fader_start*s56_ghgprice_fader)), ...)`.
**Reality**: The CODE in both claims is correct and present, but the line numbers are wrong:
- `v56_emis_pricing.fx(...)` is at **line 13** (preloop.gms:34 is a population-share comment + `p56_region_fader_shr` assignment).
- The `loop(t_all$(m_year(t_all) > max(...)))` is at **line 96** (preloop.gms:82 is a CH4 price-limit clamp `im_pollutant_prices(...,"ch4",...)$(... > s56_limit_ch4_n2o_price*...) = ...`).
**File evidence**: `modules/56_ghg_policy/price_aug22/preloop.gms:13` and `:96`.
**verify_cmd**:
- `rg -n "v56_emis_pricing\.fx" .../price_aug22/preloop.gms` → `13:`
- `rg -n "c56_mute_ghgprices_until" .../price_aug22/preloop.gms` → `72`, `96`, `123` (the `loop(t_all$...` form is `96`)
- `sed -n '30,40p'` and `sed -n '78,90p'` confirm the cited lines hold different content
**confirmed**: true.
**proposed_fix**: §3.4 line 663: change `preloop.gms:34` → `preloop.gms:13`. §5.7 line 1207: change `preloop.gms:82` → `preloop.gms:96`.

### BUG-5 (Major) — Citation drift: M80 nlp_par solve:52-53 → actual 40/60
**Class**: 10 (stale file:line citation) | **Trigger**: citation drift to different content.
**Doc line**: GAMS_Advanced_Features:1038-1043 (§4.4 dynamic-sets example).
**Claim**: cites `modules/80_optimization/nlp_par/solve.gms:52-53` with
`loop(i2, j2(j)$cell(i2,j) = yes; * Dynamically activate cells for region i2 );`
**Reality**: The pattern `loop(i2, j2(j)$cell(i2,j) = yes);` is a one-liner at solve.gms:**40** (and again at **60**), not 52-53. Lines 52-53 are inside a collection-loop `repeat` block (`magpie.handle = p80_handle(h); execute_loadhandle magpie;`). The doc also reformats the one-liner into a multi-line block with an invented inline comment.
**File evidence**: `modules/80_optimization/nlp_par/solve.gms:40` (`  loop(i2, j2(j)$cell(i2,j) = yes);`) and `:60`.
**verify_cmd**:
- `rg -n "j2\(j\)\$cell\(i2,j\)" .../nlp_par/solve.gms` → `40:`, `60:`
- `sed -n '48,58p'` → lines 52-53 = `magpie.handle`/`execute_loadhandle` region
**confirmed**: true. (`nlp_par` is non-default — default optimization is `nlp_apr17` — but the doc cites it only as a GAMS-pattern example and makes no default claim, so realization choice is not itself a bug; the line drift is.)
**proposed_fix**: line 1038: change `nlp_par/solve.gms:52-53` → `nlp_par/solve.gms:40`, and present the real one-liner `loop(i2, j2(j)$cell(i2,j) = yes);` (drop the fabricated multi-line reformat).

### BUG-6 (Minor) — Non-existent illustrative `vm_*` names presented alongside real ones
**Class**: 2 (hallucinated variable name) but in illustrative context | **Trigger**: tie-break down from Major (illustrative, no file:line) to Minor.
**Doc line**: GAMS_Advanced_Features:621 (`vm_production.lo`), 647 (`vm_trade.up`), 745-746 (`vm_production.lo/.up`).
**Claim**: examples use `vm_production` and `vm_trade` as if MAgPIE variables.
**Reality**: neither is declared anywhere in develop (`vm_prod` is the real production variable; trade is `vm_trade_*`/`vm_exp_*`/`vm_imp_*` family). These appear in "Example" blocks with no file:line citation, mixed with genuine names (`vm_land`, `vm_cost_glo`), so a reader cannot tell which are real.
**File evidence**: `rg -ln "vm_production" .../declarations.gms` → none; `rg -ln "vm_trade" .../declarations.gms` → none; positive control `vm_prod` → `17_production/flexreg_apr16/declarations.gms`.
**verify_cmd**: `rg -ln "vm_production" /tmp/magpie_develop_ro/modules/*/*/declarations.gms` → empty; same for `vm_trade`.
**confirmed**: true (names absent), but severity is Minor because they are explicitly illustrative examples, not cited authoritative claims.
**proposed_fix** (optional, low priority): either (a) replace with real names (`vm_prod.lo(i,kcr)`, and a real trade var), or (b) rename to obviously-generic placeholders (`v_production`, `v_trade`) so they are not mistaken for MAgPIE interface variables. If left as-is, add "(illustrative; not a real MAgPIE variable)".

---

## DEFERRED (not code-verifiable / nuance / not editing)

- **`or`/`and` as set-operation equivalents** (§4.2 lines 855, 870): doc claims `set1(i) or set2(i)` = union and `set1(i) and set2(i)` = intersection. GAMS documents `+`/`*` as the canonical set-algebra operators; `and`/`or` are documented under logical/conditional expressions, not as set-op synonyms. In practice they DO produce equivalent results via logical evaluation on 1/0 membership. Borderline semantics-nuance vs error; advisory said "defer pure style". Not asserting a confirmed bug.
- **`pcm_` = "Previous Current Module"** (§5.5 line 1179): no code comment defines this expansion. The `pcm_`/`pc` prefix for previous-timestep-carried parameters is a real MAgPIE convention, but the exact gloss is unverifiable from code. Low-stakes aside; not editing.
- **`.prior` lower=higher priority** (§3.8 line 780): the gams.com Variables page did not state the direction explicitly; this is correct per general GAMS knowledge (lower prior branches first) but I could not quote it from the fetched page. Not flagging.
- **`$eval` example** (§2.4 lines 462-468): uses `$set` for inputs then `$eval` for the difference; expected output `Time_horizon: 30 years` capitalizes the leading word vs the lowercase display string. Cosmetic/Informational only — not editing.

---

## Summary

GAMS-language content (the bulk of the doc) is accurate — `.fx` reset-`.l` semantics, default-bounds tables, attribute list, dollar-control options, inline-comment gating, and set-operation symbols all verified against gams.com. All 12 `core/macros.gms` citations (line + body) are exact. The errors cluster entirely in the **module file:line example citations**: one fabricated variable+code (M17, Critical), one fabricated+out-of-range example reused twice (M70, Major), one wrong-prefix+drift (M10 `v10_` vs `vm_lu_transitions`, Major), and two pure line-drifts (M56 ×2, M80) — consistent with the repo's dominant "citation drift / DECLARED-vs-real-name" vein. Plus a Minor illustrative-name issue (`vm_production`/`vm_trade` don't exist). The pre-run advisory ("stable syntax → low bug density; flag wrong MAgPIE examples") is CONFIRMED: every bug is a MAgPIE-example error, zero GAMS-semantics errors.

Bugs: 1 Critical, 4 Major, 1 Minor.
