# Audit Report: GAMS_Control_Structures.md (Round 39 doc-audit)

**Target**: `reference/GAMS_Control_Structures.md`
**Ground truth**: official GAMS language docs (gams.com/latest) for GAMS-language claims; `/tmp/magpie_develop_ro` (develop @ 5ea394f, RC2 4.14.0) for MAgPIE-example claims.
**Auditor**: adversarial doc-audit, Opus.
**Date**: 2026-05-30.

## Overall Verdict: SIGNIFICANT ERRORS
## Accuracy Score: 4/10

The GAMS-language content (dollar conditions, if/elseif, loop/while/repeat/for, break/continue, abort) is **accurate** against the official GAMS documentation — every semantic claim I checked confirmed. The damage is concentrated entirely in the **MAgPIE code examples**: nearly every `modules/.../*.gms:LINE` citation is wrong, several cite **out-of-range line numbers** (file shorter than cited line), and four examples present **fabricated equation/variable names and formulas** that do not exist anywhere in develop. Because this doc is a GAMS *reference* loaded by the agent before writing GAMS code, the fabricated MAgPIE identifiers (`q10_land_from`, `v10_lu_transitions`, `im_demandshare_reg`, `f17_prod_init`) and the fabricated `p35_maturesecdf` formula are high-harm: an agent pattern-matching off these would cite non-existent names as authoritative.

---

## Part A — GAMS-language claims (VERIFIED CORRECT)

Checked against gams.com/latest/docs/UG_CondExpr.html, UG_FlowControl.html, UG_GAMSPrograms.html:

| Doc claim | Doc line | GAMS doc verdict |
|---|---|---|
| Dollar-on-left: assignment only if TRUE, else previous value persists | 119-127 | CORRECT ("previous content ... will remain unchanged") |
| Dollar-on-right: always assigns, zero if FALSE | 138-152 | CORRECT ("value of zero is assigned") |
| Variables NOT allowed in conditions; attributes (.l/.m/.lo/.up) allowed | 53, 267 | CORRECT |
| `inf` and `eps` in conditions evaluate TRUE | 268 | CORRECT (even eps, numerically 0, is TRUE) |
| sameas/diag/card/ord usable in conditions; ord only on 1-D static ordered sets | 95-99, 270 | CORRECT |
| Numeric nonzero = TRUE, zero = FALSE | 46 | CORRECT |
| REPEAT executes ≥1 time, syntax `repeat( ... until cond )` | 717-726 | CORRECT |
| WHILE pre-test, may run 0 times | 682-686 | CORRECT |
| FOR increment must be positive, default 1; `to`/`downto` | 791-800 | CORRECT ("If the increment is given, it has to be a positive real number") |
| BREAK default n=1, terminates n innermost | 858-865 | CORRECT |
| CONTINUE jumps to end of innermost | 891-898 | CORRECT |
| LOOP: no set modification, execution statements only | 626-645 | CORRECT |
| forlim limits while/for/repeat passes | 752-758 | CORRECT |

No GAMS-language bug found. The doc's GAMS semantics are sound.

---

## Part B — Advisory-flagged item: column-0 `*` comment vs indented `*` multiplication

**VERDICT: CONFIRMED BUG (Major).** The advisory's concern is real.

GAMS rule (gams.com): "An asterisk in column one means that the line will not be processed, but treated as a comment." End-of-line comments are NOT supported via `*`; they require `!!` (default) under `$onEolCom`. An asterisk that is **not in column 1** (i.e., indented or after code on the same line) is parsed as **multiplication**, not a comment.

The doc repeatedly places `*` as an **end-of-line comment after a statement on the same line** inside `gams`-fenced blocks. Examples (non-exhaustive): lines 49-50, 61-62, 82-84, 102-104, 124, 159-160, 177, 196, 227, 232, 240-262, 449-471, 502-507, 531, 549, 559, 599, 606, 613, 620, 632-644, 651, 657, 705, 712, 757, 760, 870-876, 903, 957, 1004, 1010, 1024, 1045. A reader copying e.g. `b $ (2*a - 4) = 7;          * Assign b=7 if 2*a-4 is non-zero` (line 49) into GAMS gets `* Assign ...` parsed as multiplication → compile error.

The doc is **internally inconsistent**: it correctly uses `!!` at lines 263 (`!! Off-diagonal only` via line 443) and shows it works, but elsewhere uses post-statement `*`. Note that **column-1** `*` lines inside a fenced block (e.g., lines 449, 454, 599 where `*` starts the line) are fine; the bug is specifically the `code; * comment` same-line pattern. Recorded as one consolidated bug (GCS-B1).

---

## Part C — MAgPIE code-example bugs (the dominant vein)

All file paths under `/tmp/magpie_develop_ro/`. Realization dir names verified via `ls` (all correct: `fbask_jan16`, `price_aug22`, `landmatrix_dec18`, `pot_forest_may24`, `dynamic_may24`, `flexreg_apr16`, `nlp_par`, `exo`).

### GCS-B2 (CRITICAL) — Fabricated equation + variable in the 10_land example
**Doc lines 106-116 and 182-189** cite `modules/10_land/landmatrix_dec18/equations.gms:13-16` and `:13` for:
```
q10_land_from(j2,land_from) ..
    v10_lu_transitions(j2,land_from,"crop")
    =e=
    sum(land_to$(not sameas(land_from,land_to)),
        v10_lu_transitions(j2,land_from,land_to));
```
- `q10_land_from` does NOT exist (`rg -n "q10_land_from"` → no match). Real equation names: `q10_land_area, q10_transition_to, q10_transition_from, q10_landexpansion, q10_landreduction, q10_cost, q10_landdiff`.
- `v10_lu_transitions` does NOT exist; real name is `vm_lu_transitions` (vm_ prefix). `rg -n "v10_lu_transitions"` → no match; `vm_lu_transitions` → 4 hits in equations.gms.
- `equations.gms:13-16` is actually `q10_land_area(j2) .. sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));`.
- The `not sameas(land_from,land_to)` off-diagonal pattern DOES exist, but in `q10_landexpansion`/`q10_landreduction` (lines 30-40), not in a `q10_land_from`.

Triggers: "Invented equation name presented as authoritative" + "Wrong variable prefix (vm_ vs v{N}_)". This appears in TWO places (1.2.4 set functions, 1.5.1 within-equation algebra). Critical.

### GCS-B3 (CRITICAL) — Fabricated variable + input + formula in the 17_production example
**Doc lines 360-364** cite `modules/17_production/flexreg_apr16/presolve.gms:13` for:
```
if (ord(t) = 1,
  im_demandshare_reg.l(i,kall) = f17_prod_init(i,kall)/sum(i2,f17_prod_init(i2,kall));
);
```
- `im_demandshare_reg` does NOT exist anywhere in develop (`rg -n "im_demandshare_reg"` → no match).
- `f17_prod_init` does NOT exist anywhere (`rg -n "f17_prod_init"` → no match).
- The file is only 18 lines. The actual `if (ord(t) = 1, ...)` block (lines 12-18) is:
  `vm_prod.l(j,kcr) = pm_prod_init(j,kcr);` (guarded by `$ifthen "%c17_prod_init%" == "on"`).
- "Initializes regional demand shares" mischaracterizes the code (it initializes production levels).

Triggers: "Invented variable name presented as authoritative" + fabricated formula. Critical.

### GCS-B4 (CRITICAL) — Fabricated formula for p35_maturesecdf (35_natveg)
**Doc lines 129-134** cite `modules/35_natveg/pot_forest_may24/presolve.gms:82` for:
```
p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) =
    (s35_natveg_harvest_secdforest * sum(ac_est, p35_secdforest(t,j,ac_est)))
    / (sum(ac_sub, 1$(not sameas(ac_sub,"acx"))) * s35_natveg_harvest_secdforest + (1-s35_natveg_harvest_secdforest));
```
- `p35_maturesecdf` DOES exist (declarations.gms:26), but the assignment is at **presolve.gms:116-117**, not line 82 (line 82 region is the age-class-shift block; `s35_shift` at line 85).
- The formula is FABRICATED. Actual code (line 116-117):
  `p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) = p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);`
- `s35_natveg_harvest_secdforest` does NOT exist (`rg -n` → no match). The doc's entire RHS (harvest-ratio weighting) is invented.

Triggers: "Fabricated formula presented as the code's actual implementation" + citation out of date. Critical (an agent would cite a non-existent scalar and a wrong formula as the model's actual secondary-forest maturation).

### GCS-B5 (MAJOR) — Fabricated p70_cattle_stock_proxy carry-forward, out-of-range citations (70_livestock)
**Doc lines 64-69** (under 1.2.2) cite `presolve.gms:120`, and **doc lines 389-396** (under 2.5) cite `presolve.gms:119-121`, for:
```
if (ord(t)>1,
  p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i);
);
```
- `fbask_jan16/presolve.gms` is only **70 lines** → lines 119-121 and 120 are OUT OF RANGE (fabricated).
- The `p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i)` carry-forward does NOT exist anywhere (`rg -n "p70_cattle_stock_proxy\(t-1,i\)"` → only inside the `p70_incr_cattle` formula at line 53, as a ratio, never as a simple carry-forward).
- The real `if (ord(t)>1, ...)` block is at line 52 and computes `p70_incr_cattle(t,i) = (...)`, not a cattle-stock carry-forward.

Triggers: out-of-range citation (fabricated) + fabricated content. Two occurrences. Major-to-Critical; scored Major (illustrative section, not a load-bearing interface-variable definition) with tie-breaker pulling down from Critical.

### GCS-B6 (MAJOR) — Citation drift: `if (ord(t) = smax...)` example (70_livestock)
**Doc lines 163-168** cite `presolve.gms:70`; **doc lines 371-381** cite `presolve.gms:69-75`. The snippet `if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > sum(t_all$(t(t_all) and t_past(t_all)), 1),` is at develop line **16**, not 70 / 69-75. Content otherwise matches. (`rg -n "ord\(t\) = smax"` → line 16.) Citation drift to wrong line (here, off by ~54 lines; under 2.5 the cited range 69-75 is also out of range since the file is 70 lines and line 75 does not exist). Major.

### GCS-B7 (MAJOR) — Citation drift: v56_emis_pricing.fx example (56_ghg_policy)
**Doc lines 86-89** cite `modules/56_ghg_policy/price_aug22/preloop.gms:34` for `v56_emis_pricing.fx(i,emis_oneoff,pollutants)$(not sameas(pollutants,"co2_c")) = 0;`. Develop has this at **line 13**, not 34. (Line 34 in develop is a comment about region price share.) Content correct, line wrong. Major (citation drift; the variable and statement are real, so harm is bounded to a careful reader landing on the wrong line).

### GCS-B8 (MAJOR) — Citation drift + content mismatch: 32_forestry loop example
**Doc lines 201-206** (1.5.2) cite `modules/32_forestry/dynamic_may24/preloop.gms:65`; **doc lines 547-554** (3.5) cite `:65-67`. The snippet shown is:
```
loop(ac$(ord(ac) > 1),
  p32_carbon_density_ac(t,j,"acx",ag_pools) = p32_carbon_density_ac(t,j,ac,ag_pools);
);
```
- Develop line 65 is `p32_time(ac) = ord(ac);` (Faustmann rotation block) — NOT a loop.
- `p32_carbon_density_ac(t,j,"acx",ag_pools)` assignment does NOT exist (`rg -n 'p32_carbon_density_ac\(t,j,"acx"'` → no match).
- Additionally, the 1.5.2 placement is conceptually mismatched: the section is titled "Domain Restriction (Before ..)" for equation generation, but the example is a `loop`, not an equation domain restriction. Minor secondary issue folded in.

Major (wrong line + content the variable/assignment doesn't exist as shown).

### GCS-B9 (MAJOR) — Citation drift: 80_optimization solve.gms examples
**Doc lines 528-535** (3.4) cite `modules/80_optimization/nlp_par/solve.gms:52-53` for `loop(i2, j2(j)$cell(i2,j) = yes);` — develop has `loop(i2, j2(j)$cell(i2,j) = yes);` at **line 40**, not 52-53. **Doc lines 586-593** (3.7) cite `:46` for `loop(h$p80_handle(h),` — develop has it at **line 50**, not 46. Content correct, both lines wrong. Major (citation drift, two locations).

### GCS-B10 (MAJOR) — Citation drift: 56_ghg_policy filtered loop example
**Doc lines 564-569** (3.6) cite `modules/56_ghg_policy/price_aug22/preloop.gms:82` for `loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),s56_fader_start*s56_ghgprice_fader)), ...)`. Develop has this loop at **line 96**, not 82 (line 82 is an `im_pollutant_prices` n2o cap). Content correct, line wrong. Major (citation drift).

### Co-located note (NOT a bug)
The 13_tc example (doc 509-516, `modules/13_tc/exo/preloop.gms:13`, `loop(t, im_technological_change(t,i,kcr) = f13_tcguess(t,i,kcr));`) is ALSO drifted/mismatched: develop `exo/preloop.gms:8-16` is a `loop(t, if(m_year(t)<=sm_fix_SSP2, i13_tc_factor(t)=f13_tc_factor(t,"medium"); ...))` and neither `im_technological_change` nor `f13_tcguess` appears in that file. I flag this in `deferred` rather than as a confirmed bug only because I did not exhaustively confirm those two identifiers are absent module-wide — see deferred list. (Pre-check: the cited line 13 content is `i13_tc_factor(t) = f13_tc_factor(t,"%c13_tccost%");`, which does NOT match the doc.) Treat as a probable additional citation/identifier bug.

---

## Root-cause synthesis

Two clean root causes, suitable for grouped fixes:

1. **All MAgPIE file:line citations are stale/fabricated** (B5-B10 + the 13_tc deferred). The line numbers appear to have been drawn from an OLD MAgPIE version (or invented), never re-verified post-merge. Several point past EOF (70-line and 18-line files cited at 119-121 / 52-53). Fix per MANDATE 16: re-read each cited file in current develop and correct every line number; for B6/B5 the example content itself must be replaced because the cited construct no longer exists.

2. **Four examples carry fabricated identifiers/formulas** (B2, B3, B4, and the carry-forward in B5). These are not drift — the names (`q10_land_from`, `v10_lu_transitions`, `im_demandshare_reg`, `f17_prod_init`, `s35_natveg_harvest_secdforest`) and the `p35_maturesecdf` RHS do not exist in develop at all. Fix: replace each with a real, verified snippet (candidates below).

The GAMS-language spine (Parts A, plus the `!!` vs `*` rule the doc partly respects) is sound; the doc would be a solid reference once the MAgPIE examples are re-sourced.

## Recommended replacements (verified against develop @ 5ea394f)

- **B2** → use real off-diagonal transition: `q10_landexpansion(j2,land_to) .. ... sum(land_from$(not sameas(land_from,land_to)), vm_lu_transitions(j2,land_from,land_to)) ...` at `modules/10_land/landmatrix_dec18/equations.gms:30-40` (read and quote exact lines). Or use `q10_land_area` (lines 13-15) which is what is actually at 13-16.
- **B3** → `if (ord(t) = 1, ... vm_prod.l(j,kcr) = pm_prod_init(j,kcr); );` at `modules/17_production/flexreg_apr16/presolve.gms:12-18`.
- **B4** → `p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) = p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);` at `modules/35_natveg/pot_forest_may24/presolve.gms:116-117`.
- **B5** → `if (ord(t)>1, p70_incr_cattle(t,i) = (...); else p70_incr_cattle(t,i) = 1; );` at `modules/70_livestock/fbask_jan16/presolve.gms:52-58`.
- **B6** → fix line to `modules/70_livestock/fbask_jan16/presolve.gms:16`.
- **B7** → fix line to `:13`. **B8** → re-source the acx-copy loop (the documented loop does not exist; replace with a real `loop(ac$(...))` from this module or drop the MAgPIE label). **B9** → fix to `:40` and `:50`. **B10** → fix to `:96`.
- **B1** → change every same-line `code; * comment` to `code; !! comment` (matching the doc's own correct usage at line 443), or move `*` comments to their own column-1 line.

## Mechanical checks
- M1 (citations present): pass (many present) but ~all wrong — the failure mode the gate exists to catch.
- M3 (prefixes valid): FAIL — `v10_lu_transitions` should be `vm_`.
