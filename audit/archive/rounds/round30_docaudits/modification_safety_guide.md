# Round 30 doc audit — modification_safety_guide.md

**Target**: `cross_module/modification_safety_guide.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (Merge PR #887)
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`
**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-29

---

## Scope and method

Cross-module modification-safety doc. The load-bearing, code-checkable claims are:
interface-variable consumer SETS (the doc's core function — "who breaks if I change X"),
file:line citations, realization names + defaults, M56 switch defaults, cost-variable
attributions, equation names, and derived counts.

All grep probes were run as standalone commands (per the repo's grep-guard: chained
`grep`/`rg` no-match aborts truncate output). Consumer-set claims were verified with rg
word-boundary, cross-checked with `grep -rl`, and (for absence claims) confirmed with a
third method plus positive controls.

Realizations confirmed match doc: `landmatrix_dec18` (M10), `default` (M11),
`flexreg_apr16` (M17), `price_aug22` (M56). All are the configured defaults.

---

## VERIFIED CORRECT (high-value confirmations)

### Consumer sets — all of these match code exactly

- **`vm_land` → 10 direct consumers** (§1.2 table + line 55): 22, 29, 30, 31, 32, 34, 35, 50, 58, 59.
  `rg -l 'vm_land\b'` (word-boundary) gives exactly these 10. A substring grep gives 12 (adds
  39, 80) but 39 references only `vm_landexpansion`/`vm_landreduction` (calib/equations.gms:13-14)
  and 80 references only `vm_landdiff` (lp_nlp_apr17/solve.gms:76) — neither reads bare `vm_land`.
  Doc's "10" is correct.
- **`vm_lu_transitions` → 3** (29, 35, 59) ✓
- **`vm_landexpansion` → 4** (35, 39, 58, 59) ✓
- **`vm_landreduction` → 2** (39, 58) ✓
- **`pcm_land` → 12** (13, 22, 29, 31, 32, 34, 35, 44, 56, 58, 59, 71) ✓
- **18-module union** (§1.2 line 58): doc lists 11, 13, 14, 22, 29, 30, 31, 32, 34, 35, 39, 44,
  50, 56, 58, 59, 71, 80. Computed union of ALL M10-produced interface vars = exactly these 18.
  List is correct (caveat on the footnote gloss — see BUG-E).
- **`vm_prod_reg` → 8** (16, 18, 20, 21, 38, 50, 70, 71) ✓ (§3.2 footnote line 338)
- **`pm_prod_init` → 1** (38_factor_costs) ✓; declared in 17_production/flexreg_apr16/declarations.gms:18 ✓
- **`vm_emission_costs`**: 11_costs ✓ (but ALSO 15_food — see BUG-F omission)
- **`vm_reward_cdr_aff` → 11_costs** only ✓
- **Appendix B counts**: `im_pop_iso`=10 ✓, `pm_interest`=9 ✓, `vm_prod`=8 ✓, `vm_area`=8 ✓.

### Cost-variable attributions (§2.2) — all 9 correct (MANDATE 9)

`vm_cost_prod_crop`→38, `vm_cost_prod_past`→31, `vm_cost_prod_livst`→70,
`vm_nr_inorg_fert_costs`→50, `vm_emission_costs`→56, `vm_cost_landcon`→39,
`vm_cost_trade_tariff`/`margin`/`feasibility`→21. All verified via
`rg '^\s*<var>\b' .../declarations.gms`.

### Equation names + formulas

- `q11_cost_glo` / `q11_cost_reg` / `v11_cost_reg` / `vm_cost_glo` — all in
  11_costs/default/equations.gms:10,15 + declarations.gms:9-15 ✓. `vm_reward_cdr_aff`
  is subtracted (equations.gms:27) — matches §2.3 MISTAKE 3 fix.
- `q10_land_area` (equations.gms:13), `q10_transition_to` (19), `q10_transition_from` (23) ✓.
  Transition row/col sum relationships (§1.2 lines 109-110) match code exactly:
  row sum = `pcm_land(j,land_from)` (q10_transition_from), col sum = `vm_land(j,land_to)`
  (q10_transition_to).
- `q17_prod_reg`: `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))`
  (17_production/flexreg_apr16/equations.gms:10-11) ✓. Equation comment confirms "plant
  commodity" scope (§3.4 MISTAKE 1).
- `q56_emission_costs` (equations.gms:56), `q56_emis_pricing_co2` (19) ✓; line 22 confirms it
  uses `(pcm_carbon_stock - vm_carbon_stock)` — matches §4.5 MISTAKE 3 lag mechanism.
- `land` set = exactly 7 types (core/sets.gms:250-251: crop, past, forestry, primforest,
  secdforest, urban, other) — matches §1 "7 land types".

### M56 switch defaults (§4.3) — values all correct (MANDATE 3)

- `c56_pollutant_prices` = `R34M410-SSP2-NPi2025` (default.cfg:1713, input.gms:84) — doc says
  "SSP2-NPi2025" (acceptable shorthand of the meaningful portion).
- `c56_emis_policy` = `reddnatveg_nosoil` (default.cfg:1810, input.gms:86) ✓
- `c56_carbon_stock_pricing` = `actualNoAcEst` (input.gms:90) ✓
- `s56_c_price_induced_aff` = `1` (default.cfg:1741, input.gms:69) ✓
- "100+ IAM scenarios" / "60+ policies": `ghgscen56` set ~146 members, `scen56` ~67 members.
  Both lower-bound approximations hold.

### M11 dependency count

q11_cost_reg references cost vars declared across exactly **27 source modules** — matches
§2.2 line 217 ("27 modules") and Appendix A line 1057 ("Depends On: 27"). 10_land appears in
that set via `vm_cost_land_transition` (declared 10_land, consumed 11_costs).

### Citation verified correct

- `pcm_land` calc at `modules/10_land/landmatrix_dec18/postsolve.gms:8-9` (§1.2 line 79) ✓
  (line 8 = comment, line 9 = `pcm_land(j,land) = vm_land.l(j,land);`).

---

## BUGS FOUND

### BUG-A (CRITICAL) — `im_pollutant_prices` consumer set is wrong

- **Doc**: modification_safety_guide.md:461 — table row
  "`im_pollutant_prices(t,i,pollutants,emis_source)` | **32_forestry, 60_bioenergy** | Price
  signals for land-use decisions". Propagated to §4.4 line 495 ("Price Signals → 60_bioenergy").
- **Reality**: The ONLY non-self consumer of `im_pollutant_prices` is **57_maccs**
  (on_aug22/preloop.gms:24-25 — divides by the price to compute MAC steps). 32_forestry and
  60_bioenergy reference it **nowhere** (confirmed 3 methods + positive controls). 60_bioenergy
  has no carbon-price token at all; 32_forestry's only price-ish hits are `p32_carbon_density_*`
  (unrelated). Module 56 exports no derived price parameter that 32/60 read either — 56's only
  exported price interface is `im_pollutant_prices` itself (declarations.gms:9).
- **Verify cmds**:
  - `rg -l 'im_pollutant_prices\b' .../modules | awk -F/ '{print $5}' | sort -u | grep -v 56` →
    `57_maccs` (only).
  - `rg -n 'im_pollutant_prices' .../32_forestry` → no match; `.../60_bioenergy` → no match.
  - substring count: `56_ghg_policy 27`, `57_maccs 2` (nothing else).
  - positive control: `grep -rln im_pollutant_prices .../56_ghg_policy` → 3 files (search works).
- **Anchor**: R20 (wrong consumer set on interface var) → Critical. In a modification-safety doc
  the harm is direct: a user editing `im_pollutant_prices` MISSES 57_maccs (its MAC stepping
  divides by the price and breaks silently) while wasting effort on two non-consumers.
- **Severity**: Critical. **Class**: 15 (latent doc error / wrong consumer set; also class 6).
- **Fix**: Replace the consumer cell with `57_maccs` and re-describe the signal. Suggested:
  `| im_pollutant_prices(t_all,i,pollutants,emis_source) | 57_maccs | Certificate prices; 57 reads them to size MAC abatement steps (preloop.gms:24-25) |`.
  In §4.4 line 495 remove the "Price Signals → 60_bioenergy" arrow (or relabel it as an
  economic, not variable-level, linkage). Note `t_all` not `t` in the signature.

### BUG-B (MAJOR) — `pm_prod_init` initialization cited to the wrong file

- **Doc**: modification_safety_guide.md:386-390 (§3.4 MISTAKE 2 FIX) —
  "Use realistic initialization (`modules/70_livestock/fbask_jan16/presolve.gms:10-16`)" followed
  by `pm_prod_init(j,kcr) = sum(w, fm_croparea("y1995",j,w,kcr) * pm_yields_semi_calib(j,kcr,w));`.
- **Reality**: That formula lives at **`modules/17_production/flexreg_apr16/presolve.gms:10`**
  (verbatim). `70_livestock/fbask_jan16/presolve.gms:10-16` is about `vm_feed_balanceflow` and
  scavenging flags — `pm_prod_init` does **not appear in that file at all**.
- **Verify cmds**:
  - `rg -n 'pm_prod_init' .../17_production .../70_livestock` → only 17_production/presolve.gms:10,15.
  - `rg -n 'pm_prod_init' .../70_livestock/fbask_jan16/presolve.gms` → no match.
  - `sed -n '9,11p' .../70_livestock/fbask_jan16/presolve.gms` → `vm_feed_balanceflow.fx...`.
- **Severity**: Major (citation drift to materially-different content; MANDATE 16, class 10/12).
  Formula text is correct; only the file path is wrong.
- **Fix**: Change the citation to `modules/17_production/flexreg_apr16/presolve.gms:10`.

### BUG-C (MAJOR) — `s56_c_price_induced_aff` cited to the wrong line

- **Doc**: modification_safety_guide.md:532-534 (§4.5 MISTAKE 2 FIX) — "Enable CDR if pricing
  CO2 (`modules/56_ghg_policy/price_aug22/input.gms:103`)" then `s56_c_price_induced_aff = 1;`.
- **Reality**: input.gms:103 is `$if "%c56_pollutant_prices%" == "coupling" ;` (a
  pollutant-price coupling conditional). `s56_c_price_induced_aff` is declared at
  **input.gms:69** (`... (1=on 0=off) / 1 /`).
- **Verify cmds**:
  - `sed -n '103p' .../price_aug22/input.gms` → `$if "%c56_pollutant_prices%" == "coupling" ;`.
  - `rg -n 's56_c_price_induced_aff' .../price_aug22/input.gms` → `69: ... / 1 /`.
- **Severity**: Major (citation drift to materially-different content). The default value (1) is
  correct and the user's action is config-side, so harm is lower than BUG-B; `tier_uncertainty`
  could push to Minor, but the cited content is unambiguously unrelated, so Major per the trigger.
- **Fix**: Change the citation to `modules/56_ghg_policy/price_aug22/input.gms:69`.

### BUG-D (MINOR) — "15 modules" downstream-test count is an over-count

- **Doc**: modification_safety_guide.md:157 (§1.5 step 3) — "Verify ALL **15 modules** touched by
  Module 10 interface variables (**10 for `vm_land` + 5** for
  `vm_landexpansion`/`vm_landreduction`/`vm_lu_transitions`) execute without errors".
- **Reality**: The union of consumers of those four variables is **11 modules**, not 15. The
  "+5" naively adds the extra-variable consumers, but 35/58/59 (expansion), 58 (reduction),
  29/35/59 (transitions) are already `vm_land` consumers. Only **39_landconversion** is new.
  10 ∪ {extras} = 11.
- **Verify cmd**: union of `vm_land\b`,`vm_landexpansion\b`,`vm_landreduction\b`,`vm_lu_transitions\b`
  consumers (excl 10_land) = 11 (the 10 vm_land set + 39_landconversion).
- **Severity**: Minor (internally-contradicted set-union over-count; class 6). Also inconsistent
  with the doc's own "18-module union" elsewhere (lines 58, 77, 92). Harm low (tester runs more
  modules than needed) but it is a wrong, code-checkable count.
- **Fix**: Replace "ALL 15 modules touched by Module 10 interface variables (10 for `vm_land` + 5
  for ...)" with "ALL 11 modules touched by `vm_land`, `vm_landexpansion`, `vm_landreduction`,
  `vm_lu_transitions` (the 10 `vm_land` consumers plus 39_landconversion)". Or, to match line 58,
  point to the 18-module union of ALL M10 interface variables.

### BUG-E (MINOR) — §1.2 footnote parenthetical omits two of the union-driving variables

- **Doc**: modification_safety_guide.md:57 — the 18-module union is described as modules "affected
  by changes to `vm_landexpansion`, `vm_landreduction`, `vm_lu_transitions`, `pcm_land`, or
  `pm_land_hist/start`".
- **Reality**: The 18-module list is CORRECT, but two of its members are pulled in by variables
  NOT named in that parenthetical: **80_optimization** enters only via `vm_landdiff`
  (lp_nlp_apr17/solve.gms:76), and **11_costs** enters only via `vm_cost_land_transition`
  (consumed by 11_costs; declared in 10_land/declarations.gms:22). Neither 80 nor 11 references
  any of the five variables the footnote lists. A reader re-deriving the union by grepping only
  the named vars comes up 2 modules short.
- **Verify cmds**:
  - `rg -n 'vm_land...' .../11_costs` for all five named vars + bare `vm_land` → no match;
    `rg -n 'vm_cost_land_transition' .../11_costs` → present.
  - `rg -n 'vm_landdiff' .../80_optimization/lp_nlp_apr17/solve.gms` → :76,77,196,197.
- **Severity**: Minor / Informational (the count and list are right; the mechanistic gloss is
  incomplete). Class 6-adjacent (explanatory, not the count itself).
- **Fix**: Add `vm_landdiff` and `vm_cost_land_transition` to the parenthetical, e.g. "...may be
  affected by changes to `vm_landexpansion`, `vm_landreduction`, `vm_lu_transitions`, `vm_landdiff`,
  `pcm_land`, `pm_land_hist/start`, or `vm_cost_land_transition`".

### BUG-F (MINOR) — `vm_emission_costs` consumer table omits 15_food

- **Doc**: modification_safety_guide.md:459 — "`vm_emission_costs(i)` | **11_costs** | Total GHG
  costs (enters objective)".
- **Reality**: `vm_emission_costs` is also consumed by **15_food**
  (anthro_iso_jun22/intersolve.gms:23 reads `vm_emission_costs.l(i)` for tax recycling;
  scaling.gms:22 sets `.scale`). The "Consumers: 11_costs" cell is incomplete.
- **Verify cmd**: `rg -l 'vm_emission_costs\b' .../modules | awk -F/ '{print $5}' | sort -u |
  grep -v 56` → `11_costs`, `15_food`.
- **Severity**: Minor (single omission of a secondary consumer; the primary objective-function
  consumer (11) is correct). Note 15_food's read is in intersolve (a tax-recycling side channel),
  not the core cost path — lower modification-safety stakes than BUG-A, hence Minor not Critical.
- **Fix**: Change the consumer cell to `11_costs, 15_food` and (optionally) note 15_food reads it
  for food-tax recycling in `intersolve.gms`.

---

## DEFERRED (not code-verifiable / out of code scope)

- Appendix A graph metrics (line 1055-1068): "Connections / Provides To / Depends On" columns are
  explicitly sourced to `Module_Dependencies.md:29-40` under that doc's own counting convention.
  Independent code check of 10_land "Provides To" = 18 distinct consuming modules vs the table's
  "15", and "Connections 17" — but these graph metrics depend on Module_Dependencies.md's
  inclusion rules (likely excludes init params / cost aggregates / `vm_landdiff`), which I cannot
  reconstruct from GAMS alone. M11 "Depends On: 27" WAS independently confirmed. Defer the rest to
  a Module_Dependencies.md-vs-code audit rather than flag here.
- Internal doc-to-doc line citations not checkable against GAMS: module_11.md:84-115 (line 229),
  Module_Dependencies.md:151-179 (line 606), Module_Dependencies.md:29-40 (line 1068),
  Module_Dependencies.md §2.1 lines 46-59 (line 1087), nitrogen_food_balance.md:229-250 (line 424),
  carbon_balance_conservation.md:450-550 (line 504). Verify in a sibling-doc audit.
- §1.2 historical narrative "pcm_land 5 → 12; others OVERSTATED" (line 52): metadata about a past
  recompute. The CURRENT counts are all verified correct; the historical deltas are not load-bearing.
- §4.4 flow diagram "CDR Rewards → 32_forestry (afforestation incentive)" (line 493): `vm_reward_cdr_aff`
  is consumed only by 11_costs (not 32). But this arrow is framed as an economic/emergent linkage in a
  conceptual diagram (the reward enters the objective via 11, then the optimizer expands forestry), not
  as a "32 consumes vm_reward_cdr_aff" interface claim. Not flagged as a hard bug; noted for awareness.
- `c56_pollutant_prices` doc shorthand "SSP2-NPi2025" vs full `R34M410-SSP2-NPi2025`, and
  `im_pollutant_prices(t,...)` vs declared `(t_all,...)`: acceptable abbreviations, not bugs.

---

## Summary

6 bugs: 1 Critical (`im_pollutant_prices` consumer set lists 32/60, actual sole consumer is
57_maccs — R20 anchor), 2 Major citation drifts (`pm_prod_init` cited to 70_livestock not
17_production; `s56_c_price_induced_aff` cited to input.gms:103 not :69), 3 Minor (15-vs-11
module over-count; footnote omits 2 union-driving vars; `vm_emission_costs` table omits 15_food).
The doc's core consumer-set tables for `vm_land` (10), `pcm_land` (12), `vm_prod_reg` (8), all
Appendix B counts, all 9 cost-variable attributions, the M56 switch defaults, equation names, and
the M11 "27 dependencies" are all VERIFIED CORRECT against develop @ ee98739fd.
