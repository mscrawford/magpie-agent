# Round 34 Doc Audit — module_21.md (Trade)

**Auditor**: Opus 4.8 (1M)
**Date**: 2026-05-30
**Target**: `magpie-agent/modules/module_21.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`

## Overall Verdict: MOSTLY ACCURATE (lower band)
## Accuracy Score: 7/10

This doc is unusually high-quality for the **default `selfsuff_reduced`** realization: every equation formula, every default-realization file:line citation, every scalar default, the macro, and the Module 11 consumption were verified exact. The PR #866 narrative (split of `vm_cost_trade` into three `vm_cost_trade_*` interface variables) is **real and correctly described** for the default. All errors found are concentrated in the **`selfsuff_reduced_bilateral22`** (non-default alternative) description and one self-inconsistent set count.

---

## Verified Claims (correct)

- **Default realization** = `selfsuff_reduced` — `config/default.cfg:650` (`cfg$gms$trade <- "selfsuff_reduced"`). ✓
- **Three interface variables** `vm_cost_trade_tariff`, `vm_cost_trade_margin`, `vm_cost_trade_feasibility` exist in all three realizations — `selfsuff_reduced/declarations.gms:21-23`, `exo/declarations.gms:15-17`, `bilateral22/declarations.gms:25-27`. ✓
- **9 equations in selfsuff_reduced**, all names + formulas + line citations exact: `q21_trade_glo` (12-14), `q21_notrade` (18-19), `q21_trade_reg` (31-35), `q21_trade_reg_up` (39-42), `q21_excess_dem` (47-51), `q21_excess_supply` (56-58), `q21_cost_trade_tariff` (62-65), `q21_cost_trade_margin` (69-72), `q21_cost_trade_feasibility` (76-78). All match `selfsuff_reduced/equations.gms` verbatim. ✓
- **Macro** `m21_baseline_production` at `core/macros.gms:115-119` — exact two-case expansion matches doc lines 144-150. ✓
- **Module 11 consumption**: all three vars summed individually in `q11_cost_reg` at `11_costs/default/equations.gms:30,31,32`. Doc cites `:30-32`. ✓
- **Scalar defaults** (selfsuff_reduced/input.gms:16-19 + config:644-708): `s21_trade_tariff=1`, `s21_cost_import=1500`, `s21_min_trade_margin_forestry=62`, `c21_trade_liberalization=l909090r808080`. ✓
- **bilateral22 config scalars** (default.cfg:694-708 + bilateral22/input.gms:16-27): `s21_trade_tariff_factor=1`, `s21_trade_tariff_startyear=2025`, `s21_trade_tariff_targetyear=2050`, `s21_import_supply_scenario=1`, `s21_import_supply_scenario_targetyear=2050`, `s21_stddev_lib_factor=1`, `s21_trade_scenario_adjustments=0`. All match doc table (lines 537-545). ✓
- **`s21_trade_bal_damper` (0.65) and `c21_trade_scenario` not wired into module code** (doc line 551): `rg s21_trade_bal_damper modules/` → empty (positive control `s21_cost_import` → 4 hits); `c21_trade_scenario` appears ONLY in `bilateral22/realization.gms:37` comment. ✓ Doc's "treat as not yet wired" is correct.
- **`k_notrade` = 8** (oilpalm, foddr, pasture, res_cereals, res_fibrous, res_nonfibrous, begr, betr) — `sets.gms:12`. ✓
- **`k_hardtrade21` = 16** — `sets.gms:26-29`, counted 16. ✓
- **`i21_exp_shr` computed in preloop** (not file-read): `preloop.gms:21-23`. ✓ (`f21_exp_shr` survives only as a stale comment in `realization.gms:26`; no parameter declaration — doc line 500 "no longer exists" is defensible.)
- **Tariff/margin preloop**: tariff switch `preloop.gms:27-31`, margin from file `:25`, forestry floor `:33-34`, feasibility bounds `:36-38`. All exact. ✓
- **presolve.gms:11-12** releases `vm_cost_trade_feasibility.lo/.up` in selfsuff_reduced. ✓
- **exo = 3 equations** (`q21_notrade(h2,kall)`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`), and exo DOES fix `vm_cost_trade_feasibility.fx(i)=0` at `exo/presolve.gms:10`. ✓ (exo claim correct; bilateral22 claim is NOT — see Bug 2.)
- **`q21_trade_bilat` no longer exists** — `rg` empty. ✓
- **bilateral22 parameter dimensions table** (doc lines 504-511) matches `bilateral22/declarations.gms:8-14`. ✓
- **vm_prod_reg from Module 17** (`17_production/.../declarations.gms:10`, `vm_prod_reg(i,kall)`), **vm_supply from Module 16** (`16_demand/sector_may15/declarations.gms:11`, `vm_supply(i,kall)`). ✓ Module 21 is the equation-level consumer of both (Module 16 produces vm_supply via `=e=`; no hidden `.l/.lo` consumer found outside M21).
- **bilateral22 tariff fade** at `preloop.gms:60-72`. ✓

---

## Bugs Found

### Bug 21-B1 — bilateral22 equation count wrong (8 vs 9); omits `q21_cost_trade_feasibility`
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift) / fabricated realization-list count
- **Trigger**: §1 Major — "Fabricated count for a set/parameter/realization list".
- **Claim in doc** (multiple sites):
  - line 7: "**Total Equations**: 9 (selfsuff_reduced default) | 3 (exo) | 8 (selfsuff_reduced_bilateral22)"
  - line 468: "**Equation counts**: `selfsuff_reduced` = 9 | `exo` = 3 | `selfsuff_reduced_bilateral22` = 8."
  - line 485: "Explicit **bilateral** trade flows ... 8 equations:" followed by an 8-row table (lines 489-496) that omits `q21_cost_trade_feasibility`.
  - line 787: "`selfsuff_reduced_bilateral22` has 8 (see Realization Comparison)".
- **Reality in code**: bilateral22 defines **9** equations. `q21_cost_trade_feasibility(i2)` is the 9th (`bilateral22/equations.gms:97-99`), declared at `bilateral22/declarations.gms:40`.
- **File evidence**: `modules/21_trade/selfsuff_reduced_bilateral22/equations.gms:30,38,48,61,72,81,87,92,97` (9 `q21_*..` definitions); `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:31-41` (9 equation declarations).
- **verify_cmd**: `rg -c "^ q21_|^q21_" .../bilateral22/equations.gms` → `9`; `rg -n "^\s*q21_\w+\(" .../bilateral22/equations.gms` → lists `q21_trade_reg, q21_notrade, q21_trade_lower, q21_trade_upper, q21_costs_tariffs, q21_costs_margins, q21_cost_trade_tariff, q21_cost_trade_margin, q21_cost_trade_feasibility`.
- **confirmed**: true
- **proposed_fix**: Change all four "8" to "9" for bilateral22; add a 9th row to the table at line 496:
  `| q21_cost_trade_feasibility | (i) | Aggregates emergency-import penalty over commodities -> vm_cost_trade_feasibility |`

### Bug 21-B2 — bilateral22 falsely claimed to have NO feasibility penalty; phantom presolve.gms:11 citation
- **Severity**: Major
- **Class**: 12 (Content-level citation mismatch) + 4 (wrong mechanism for a realization) + phantom file:line
- **Trigger**: §1 Major — "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different" (here the cited file does not exist at all) + wrong-behavior description of an alternative realization.
- **Claim in doc**:
  - line 292: "**Bilateral22 / exo differ**: In `selfsuff_reduced_bilateral22` and `exo` ... there is **no feasibility penalty** — `vm_cost_trade_feasibility.fx(i) = 0` is set in their `presolve.gms`."
  - line 460: "`v21_excess_dem`, `v21_excess_prod`, and `v21_import_for_feasibility` do **not** exist in bilateral22."
  - line 498: "No feasibility penalty (`vm_cost_trade_feasibility.fx(i) = 0` in `modules/21_trade/selfsuff_reduced_bilateral22/presolve.gms:11`)."
- **Reality in code**: bilateral22 has **NO `presolve.gms` file** (directory listing has none). `vm_cost_trade_feasibility.fx` appears ONLY in `exo/presolve.gms:10` — never in bilateral22. bilateral22 DOES declare `v21_import_for_feasibility(i_ex,i_im,k_trade)` (`declarations.gms:28`), uses it in `q21_trade_upper` (`equations.gms:66`), and has an ACTIVE `q21_cost_trade_feasibility` equation (`equations.gms:97-99`: `vm_cost_trade_feasibility(i2) =g= sum((i_im,k_trade), v21_import_for_feasibility(i2,i_im,k_trade) * s21_cost_import)`). So bilateral22's feasibility mechanism is functionally identical to selfsuff_reduced (emergency wood/woodfuel imports with `s21_cost_import` penalty), just with bilateral dimensions. The exo half of line 292 is correct; the bilateral22 half is false.
- **File evidence**: `ls modules/21_trade/selfsuff_reduced_bilateral22/` → no presolve.gms; `modules/21_trade/selfsuff_reduced_bilateral22/equations.gms:97-99` (active feasibility eq); `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:28` (`v21_import_for_feasibility` exists). Contrast `modules/21_trade/exo/presolve.gms:10` (the only `.fx=0` site).
- **verify_cmd**: `rg -n "vm_cost_trade_feasibility\.fx" modules/21_trade/` → only `exo/presolve.gms:10` (positive control `.lo` → 4 hits across realizations incl. selfsuff_reduced/presolve.gms:11, proving search works); `ls modules/21_trade/selfsuff_reduced_bilateral22/` → declarations, equations, input, input.gms, postsolve, preloop, realization, scaling, sets, trade_pools.png (NO presolve.gms).
- **confirmed**: true
- **proposed_fix**:
  - Line 292 → "In `exo`, there is **no feasibility penalty** — `vm_cost_trade_feasibility.fx(i) = 0` is set in `modules/21_trade/exo/presolve.gms:10`. `selfsuff_reduced_bilateral22` keeps the feasibility mechanism (active `q21_cost_trade_feasibility`, bilateral `v21_import_for_feasibility`)."
  - Line 460 → remove `v21_import_for_feasibility` from the "do not exist in bilateral22" list (it DOES exist, with dims `(i_ex,i_im,k_trade)`). Keep `v21_excess_dem`/`v21_excess_prod` (those truly are absent from bilateral22 — confirmed: not in `bilateral22/declarations.gms`).
  - Line 498 → "Feasibility penalty present (active `q21_cost_trade_feasibility`, `equations.gms:97-99`); bilateral22 has NO presolve.gms." Remove the phantom `presolve.gms:11` citation.

### Bug 21-B3 — `k_trade` count wrong (38 vs 33)
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift)
- **Trigger**: §1 Major — "Fabricated count for a set ... list". Self-inconsistent with the doc's own enumeration.
- **Claim in doc** (line 70): "**Tradable Commodities** (`k_trade`, **38 items**):"
- **Reality in code**: `k_trade` has **33** members (`sets.gms:17-21`). The doc's own enumerated list (lines 71-74) contains exactly 33 items (15 crops + 10 processed + 6 livestock/fish + 2 forestry), so "38" contradicts the doc's own content.
- **File evidence**: `modules/21_trade/selfsuff_reduced/sets.gms:17-21`.
- **verify_cmd**: python count of the sets.gms `k_trade` member string → `k_trade count: 33` (`k_hardtrade21: 16`, `k_notrade: 8` both confirmed correct).
- **confirmed**: true
- **proposed_fix**: Line 70: replace "38 items" with "33 items".

### Bug 21-B4 — `trade_pools.png` citation drift (realization.gms:20 vs :31)
- **Severity**: Minor
- **Class**: 10 (Stale file:line citation)
- **Trigger**: §1 Minor — "Off-by-few line citation" within a short doc-comment file; a careful reader would still find it.
- **Claim in doc** (line 34): "**Diagram**: `realization.gms:20` references `trade_pools.png`"
- **Reality in code**: `trade_pools.png` is referenced at `selfsuff_reduced/realization.gms:31` (`![Implementation of trade.](trade_pools.png){ width=100% }`). Line 20 is mid-prose about the production band.
- **File evidence**: `modules/21_trade/selfsuff_reduced/realization.gms:31`.
- **verify_cmd**: Read of realization.gms — png at line 31.
- **confirmed**: true
- **proposed_fix**: Line 34: change `realization.gms:20` to `realization.gms:31`.

---

## Deferred (not flagged — no code-verifiable error or non-load-bearing)

- Doc uses shorthand dims `(t,h,k)` / `(i,k)` for `f21_self_suff` / `vm_prod_reg` / `vm_supply`; actual declarations use `(t_all,h,kall)` / `(i,kall)`. Conventional doc shorthand (`k`⊂`kall`); not load-bearing. Not flagged.
- Doc line 53 "Source: `realization.gms:8-16`, `equations.gms:25-30`" and line 733 "`realization.gms:22-23`" are loose pointers into a 46-line comment file; the cited concepts are roughly nearby (8-35 / 22-27). Borderline-Minor citation looseness, not content-wrong; left deferred to avoid over-flagging soft prose pointers.
- Doc line 663 (R section) etc. not applicable.
- bilateral22 `q21_costs_margins` is `=g=` while `q21_costs_tariffs` is `=e=` (equations.gms:73 vs 82) — doc's table doesn't specify constraint types, so no claim to check.

---

## Notes on the pre-run advisory
- "vm_supply is read here (R33 confirmed M21 is vm_supply's ONLY equation-consumer)": **CONFIRMED**. Outside M21, `vm_supply` appears only in `16_demand/sector_may15` (where it is PRODUCED via `=e=` on the LHS, plus postsolve `.l/.m/.up/.lo`) and a `70_livestock/module.gms` comment. No other equation-level reader; no hidden solution-level (`vm_supply.`) consumer. Doc's "from Module 16" + M21-reads is correct.
- "R29 set k_notrade to an 8-member set - verify it held": **CONFIRMED 8** (`sets.gms:12`). Doc correct (lines 61, 127).
- vm_prod_reg / vm_supply producer/consumer sets verified with both `name(` and `name.` greps + positive control. **CONFIRMED**.
- The advisory did NOT flag the bilateral22 equation-count / feasibility-mechanism errors or the k_trade=38 self-inconsistency; those are this audit's net-new findings.
