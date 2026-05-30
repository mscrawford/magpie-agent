# Round 32 Doc Audit — module_57.md (MACCs, on_aug22)

**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (develop), `config/default.cfg`
**Target**: `magpie-agent/modules/module_57.md`

---

## Summary verdict

**MOSTLY ACCURATE (lower band)**. The equations, set definitions, scalar defaults, parameter names, and the bulk of file:line citations are accurate and verified. Five code-checkable errors found, one of which is Critical (wrong `vm_maccs_costs` consumer set — phantom Module 56 + omitted Module 36, R20 anchor class). The pre-run units advisory is **REFUTED** (the doc's `USD17/tC-eq` label is correct and code-comment-supported).

Default realization `on_aug22` confirmed (`cfg$gms$maccs <- "on_aug22"`). Default `c57_macc_version = PBL_2022`, `c57_macc_scenario = Default` confirmed.

---

## Verified-correct claims (high confidence)

- **2 equations** `q57_labor_costs`, `q57_capital_costs` — declared declarations.gms:20-21, defined equations.gms:35-43 / 45-52. Formulas in doc match code verbatim (incl. the `(i2)` definition alias vs `(i)` declaration index). ✓
- **All 10 set definitions** (sets.gms:10-38) — members and line numbers match exactly: `emis_source_inorg_fert_n2o` {inorg_fert, resid, som, rice, man_crop, man_past}, `emis_source_awms_n2o` {awms}, `emis_source_rice_ch4` {rice}, `emis_source_ent_ferm_ch4` {ent_ferm}, `emis_source_awms_ch4` {awms}, `pollutants_maccs57` {ch4, n2o_n_direct}, `maccs_ch4`, `maccs_n2o`, `maccs_steps` {1*201}, `scen57` {Default, Optimistic, Pessimistic}. ✓
- **Scalar defaults** (input.gms:14-20): all 5 `s57_maxmac_*` = -1 ✓; `s57_implicit_emis_factor` = 0.01 (line 19) ✓; `s57_implicit_fert_cost` = 738 (line 20) ✓.
- **N2O / CH4 conversion chains** (doc:169, 183) — `/298*28/44*44/12` and `/25*44/12` match preloop.gms:24-25 verbatim. ✓
- **Step lengths** 6.15 / 22.4 / 22.4 (preloop.gms:9-13) ✓; **unit-back conversions** `*12/44*298*44/28` (n2o) and `*12/44*25` (ch4) match preloop.gms:109-110 (doc:300-304). ✓
- **`im_maccs_mitigation` consumer set {50, 51, 53}** — CONFIRMED CORRECT. M50 `macceff_aug22/presolve.gms`, M51 `rescaled_jan21/equations.gms`, M53 `ipcc2006_aug22/equations.gms` (all default realizations) read it; M51/M53 `off` realizations have `not_used.txt`. ✓
- **Override block** (preloop.gms:28-39, uses `sm_fix_SSP2`) — doc:206-212 matches. ✓
- **MACC table citations** input.gms:24-37 (n2o), 41-54 (ch4) ✓; input file names ✓.
- **Equation comment citations** equations.gms:9-10, 23-29, 31-33 ✓.

---

## Pre-run advisory — REFUTED

**Advisory**: check_units.py flagged module_57.md:375 `s57_step_length` unit "USD17/tC-eq" vs canonical "usd17mer" (declarations.gms:9).

**Verdict: NOT A BUG (defensible, doc is more precise than the declaration label).**

- declarations.gms:9: `s57_step_length  Step length in MACC data (USD17MER)` — currency-only label, omits the denominator.
- preloop.gms:17-18 (code comment): *"Each step is 6.15 USD17MER per tC eq in case of PBL_2007 and 22.4 USD17MER per tC eq..."* — the code itself states the unit is **USD17MER per tC-eq**.
- The doc's `USD17/tC-eq` is the dimensionally-complete form and is directly supported by the code comment. This is the module_12 "TC"-abbreviation pattern: the declaration label is an abbreviation, not a contradicting unit. No edit warranted.
- Secondary advisory checks (default realization + how MACC costs enter M11): default `on_aug22` ✓; MACC costs enter M11 via `sum(factors,vm_maccs_costs(i2,factors))` at `modules/11_costs/default/equations.gms:28` ✓.

`verify_cmd`: `grep -n "s57_step_length" .../declarations.gms` → `(USD17MER)`; `sed -n '17,18p' .../preloop.gms` → "USD17MER per tC eq".

---

## Bugs found

### BUG 57-1 — Wrong consumer set for `vm_maccs_costs` (phantom M56 + omitted M36)
- **Severity**: Critical
- **Trigger**: §1 Critical — "Wrong module attribution for a cost variable" + R20 anchor (doc says wrong consumer set; user would miss a module in a refactor). Tie note: the table (doc:654-657) is correct-but-incomplete; the prose (doc:326) is affirmatively wrong (phantom M56). Combined → Critical.
- **Class**: 15 (latent doc error — wrong consumer set) / cost-variable attribution.
- **Doc lines**: module_57.md:326 ("**To Module 56 (GHG Policy) or Module 11 (Costs)**:"); module_57.md:654-657 (downstream table lists only M11); module_57.md:664.
- **Claim in doc**: line 326 attributes `vm_maccs_costs` output to "Module 56 (GHG Policy) or Module 11 (Costs)". Downstream table + hub status list only Module 11.
- **Reality in code**: `vm_maccs_costs` is consumed by **Module 11** (`11_costs/default/equations.gms:28`, default realization) AND **Module 36** (`36_employment/exo_may22/equations.gms:28`, default realization, equation `q36_employment_maccs`). **Module 56 does NOT consume it** (positive control: M56 contains `vm_emission_costs` but no `vm_maccs_costs`).
- **File evidence**: `modules/11_costs/default/equations.gms:28` (`+ sum(factors,vm_maccs_costs(i2,factors))`); `modules/36_employment/exo_may22/equations.gms:28` (`=e= (vm_maccs_costs(i2,"labor")) * (1 / sum(ct,f36_weekly_hours...))`).
- **verify_cmd**: `rg -ln "vm_maccs_costs" /tmp/magpie_develop_ro/modules/` → only 57 (self), 36_employment, 11_costs. `rg -ln "vm_maccs_costs" .../56_ghg_policy/` → NO MATCH (positive control `vm_emission_costs` → 4 hits in 56). Defaults: M11 `costs<-"default"`, M36 `employment<-"exo_may22"`.
- **confirmed**: true.
- **Proposed fix**: (a) line 326 change header from "**To Module 56 (GHG Policy) or Module 11 (Costs)**:" to "**To Module 11 (Costs) and Module 36 (Employment)**:". (b) Downstream table (line 656): add a row `| **36** (Employment) | \`vm_maccs_costs(i,"labor")\` | Labor part of MACC costs feeds agricultural-employment accounting (\`q36_employment_maccs\`) |`. (c) Hub status line 661-664: after "Provides mitigation costs to Module 11 (optimization)" add "and the labor share to Module 36 (employment accounting)".

### BUG 57-2 — Wrong scaling value `10e4` vs code `1e4`
- **Severity**: Major
- **Trigger**: §1 Major — "Right concept, wrong number" (10× off).
- **Class**: 12 (content-level citation mismatch) / wrong value at cited line.
- **Doc line**: module_57.md:454.
- **Claim in doc**: "`vm_maccs_costs.scale(i,factors) = 10e4`".
- **Reality in code**: `vm_maccs_costs.scale(i,factors) = 1e4;` (10e4 = 100000 vs 1e4 = 10000; 10× discrepancy).
- **File evidence**: `modules/57_maccs/on_aug22/scaling.gms:8`.
- **verify_cmd**: `sed -n '8p' .../scaling.gms` → `vm_maccs_costs.scale(i,factors) = 1e4;`.
- **confirmed**: true.
- **Proposed fix**: replace `vm_maccs_costs.scale(i,factors) = 10e4` with `vm_maccs_costs.scale(i,factors) = 1e4` (line 454). Also adjust the parenthetical "(costs typically 10⁴-10⁶ range)" only if desired — 1e4 = 10⁴ is consistent, so leave the parenthetical.

### BUG 57-3 — Trapezoid example: conversion `1/25` contradicts code `×25`
- **Severity**: Major
- **Trigger**: §1 Major — "Fabricated/wrong formula presented as the code's implementation" but inside an explicitly-illustrative block, and the doc itself states the correct `×25` at line 304 (internal contradiction); a careful reader is misled about the unit-conversion direction. (Tie-break to Major, not Critical, because it is in a labeled illustrative block.)
- **Class**: 4 (conceptual pseudo-code / wrong formula).
- **Doc lines**: module_57.md:278-281, 285.
- **Claim in doc**: integral example multiplies by `(12/44) × (1/25)` and asserts (line 285) "Conversions 12/44 and 1/25 convert tC-eq pricing to tCH₄ costs"; computes `0.000671 + 0 + 0.002013 = 0.002684`.
- **Reality in code**: the tC-eq → tCH₄ conversion is `* 12/44 * 25` (MULTIPLY by GWP 25), preloop.gms:110 — which the doc itself correctly cites at line 304. Using `1/25` instead of `25` makes the example wrong by a factor of 25² = 625. (The code's own illustrative comment at preloop.gms:78-80 uses `12/44*28`, also not `1/25` — the doc matches neither.)
- **File evidence**: `modules/57_maccs/on_aug22/preloop.gms:110` (`...*12/44*25;`), contrasted with `preloop.gms:78-80` comment (`*12/44*28`).
- **verify_cmd**: `sed -n '110p' .../preloop.gms` → `p57_maccs_costs_integral(...,"ch4") = ...*12/44*25;`; `sed -n '78,80p' .../preloop.gms` → comment uses `*12/44*28`.
- **confirmed**: true.
- **Proposed fix**: Recompute the example using `× 12/44 × 25` to match code, OR replace the bespoke arithmetic with the code's own commented example (preloop.gms:74-80) verbatim and label it as the source's illustration. Minimal fix for the false claim at line 285: change "Conversions 12/44 and 1/25 convert tC-eq pricing to tCH₄ costs" to "Conversion to tCH₄ costs multiplies the tC-eq integral by 12/44 × 25 (GWP), per preloop.gms:110" — and either delete the wrong numeric lines 278-283 or recompute them. (Note: the parallel example block at doc:64-104 / 525-531 uses generic placeholders and is fine; only the CH₄ block at 277-285 carries the wrong `1/25`.)

### BUG 57-4 — Off-by-one citations for N2O / CH4 price-to-step mapping
- **Severity**: Minor
- **Trigger**: §1 Minor — "Off-by-few line citation where adjacent lines say similar things", BUT the cited line points at the OTHER pollutant's mapping (N2O cite lands on the CH4 line) or a blank line — borderline Major (citation drift to materially-different content). Tie-break → Minor because both lines are in the same 2-line mapping block and the surrounding text disambiguates.
- **Class**: 10 (stale file:line citation).
- **Doc lines**: module_57.md:167 ("**N₂O Conversion** (`preloop.gms:25`)"); module_57.md:181 ("**CH₄ Conversion** (`preloop.gms:26`)").
- **Claim in doc**: N2O conversion at preloop.gms:25; CH4 conversion at preloop.gms:26.
- **Reality in code**: N2O mapping (`i57_mac_step_n2o`) is at **preloop.gms:24**; CH4 mapping (`i57_mac_step_ch4`) is at **preloop.gms:25**; line 26 is blank.
- **File evidence**: `modules/57_maccs/on_aug22/preloop.gms:24` (n2o), `:25` (ch4), `:26` (blank).
- **verify_cmd**: `sed -n '24p;25p;26p' .../preloop.gms` → 24 = n2o_n_direct mapping, 25 = ch4 mapping, 26 = blank.
- **confirmed**: true.
- **Proposed fix**: line 167 `preloop.gms:25` → `preloop.gms:24`; line 181 `preloop.gms:26` → `preloop.gms:25`. (Also the doc-internal example label at line 169 and 183 are fine; only the cited line numbers in the headers need bumping down by one. The Data Flow citation at line 314 `preloop.gms:24-25` is already correct.)

### BUG 57-5 — Step-range max price "0-4,502" arithmetically inconsistent
- **Severity**: Minor
- **Trigger**: §1 Minor — wrong detail in a parenthetical; would not mislead into action.
- **Class**: 6 (hardcoded count/number drift).
- **Doc line**: module_57.md:377.
- **Claim in doc**: "PBL_2019/2022: 22.4 (coarser resolution, 201 steps cover 0-4,502 USD17/tC-eq)".
- **Reality in code**: max step price = (201-1) × 22.4 = **4,480** USD17/tC-eq, not 4,502. The "4,502" = 201×22.4 (wrong multiplier); the sibling PBL_2007 figure "0-1,230" correctly uses 200×6.15. Inconsistent basis.
- **File evidence**: `modules/57_maccs/on_aug22/preloop.gms:13` (`s57_step_length = 22.4`); step index runs 1..201, price at step k = (k-1)·step_length.
- **verify_cmd**: `python3 -c "print(200*22.4, 201*22.4, 200*6.15)"` → `4480.0 4502.4 1230.0`.
- **confirmed**: true.
- **Proposed fix**: line 377 change "0-4,502" to "0-4,480" (consistent with the 200×6.15=1,230 basis on line 376).

---

## Deferred / not-edited (uncertain or non-code-verifiable)

- The 10 "Limitations & Assumptions" (doc:669-785) are prose interpretation of what the code does NOT do; broadly consistent with code (static curves, AR4 GWP, discrete 201 steps, factor split). Not individually code-checkable as bugs — no edit.
- "Mitigation Technology Examples" (doc:593-637) are explicitly labeled conceptual/illustrative; MACC `.cs3` input files are not human-readable here, so the per-technology mix is unverifiable. No edit.
- Doc:314 annotates `im_pollutant_prices(t,i,pollutants,emis_source)` (declared `t_all` in M56 declarations.gms:9 but read with `t` in preloop:24-25). The doc uses the read-form `t`; not a fabrication. No edit (informational only).
- Doc:548-554 GWP rationale (AR4 25/298, AR5 28/265) — the model values 25/298 are verified (preloop:20-21); the AR5/AR6 comparison values are general climate-science knowledge, not model claims. No edit.
- "Citation Coverage: 110+" / "Equations: 2" header counts — 2 equations verified; "110+ citations" is an unauditable self-count. No edit.
