# Round 38 Doc Audit — module_21.md (Trade)

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target**: `<magpie-agent>/modules/module_21.md`
**Ground truth**: `/tmp/magpie_develop_ro` (worktree HEAD `5ea394f`, "Merge PR #877 rc2-4.14.0"; branch label `master` but this is the develop-equivalent read-only tree)
**Default realization**: `selfsuff_reduced` (confirmed `config/default.cfg:650`)

---

## Verdict: MOSTLY ACCURATE (lower band)

The doc is substantively correct and notably well-maintained on the hard parts. The PR #866 rewrite (vm_cost_trade split into three interface variables) is documented accurately, all 9 selfsuff_reduced equation formulas + line citations match code exactly, the macro `m21_baseline_production` is reproduced verbatim, and the exo (3-eq) / bilateral22 (8-eq) realization structures are correct.

**The R34-flagged regression is NOT present** — the doc currently states bilateral22 has 8 equations, no `q21_cost_trade_feasibility`, and a presolve.gms that fixes `vm_cost_trade_feasibility.fx(i)=0`. All three confirmed against bilateral22's actual files. The doc is currently correct (the R34 regression was reverted and has not regressed again).

4 confirmed bugs: 1 Major hardcoded-count, 2 Major citation-drift, 1 Minor false-consumption claim.

---

## Bugs Found

### BUG 1 — `k_trade` count 38 vs actual 33 (Major)
- **Class**: 6 (Hardcoded counts drift)
- **Trigger**: "Fabricated count for a set/parameter/realization list"
- **Doc** (module_21.md:70): "**Tradable Commodities** (`k_trade`, 38 items):"
- **Reality**: `k_trade` has exactly **33** members. The doc's OWN enumeration just below (lines 71-74) lists 15 crops + 10 processed + 6 livestock/fish + 2 forestry = 33 — so the header "38" contradicts the doc's own member list.
- **Evidence**: `modules/21_trade/selfsuff_reduced/sets.gms:17-21`
- **verify_cmd**: Python tokenize of the code set lines 18-21 → `CODE k_trade count: 33`. Doc-list tokenize (lines 71-74) → 33.
- **Fix**: replace "38 items" with "33 items" at module_21.md:70.
- **Confirmed**: yes

### BUG 2 — `trade_pools.png` citation drift `realization.gms:20` → actually :31 (Major)
- **Class**: 10 (Stale file:line citation) / 12 (content-level mismatch)
- **Trigger**: "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different"
- **Doc** (module_21.md:34): "**Diagram**: `realization.gms:20` references `trade_pools.png`"
- **Reality**: realization.gms:20 is prose ("in production of different superregions, though still being constrained by the upper bounds of the production band."). The `trade_pools.png` reference is at line **31** (`*' ![Implementation of trade.](trade_pools.png){ width=100% }`).
- **Evidence**: `modules/21_trade/selfsuff_reduced/realization.gms:31`
- **verify_cmd**: `grep -n "trade_pools.png" .../selfsuff_reduced/realization.gms` → `31:`
- **Fix**: change `realization.gms:20` to `realization.gms:31` at module_21.md:34.
- **Confirmed**: yes

### BUG 3 — bilateral cost-file source citation `input.gms:45-57` → actually :71-83 (Major)
- **Class**: 10 / 12
- **Trigger**: "Citation points at content materially different (citation drift to wrong content)"
- **Doc** (module_21.md:415): "**Source**: `modules/21_trade/selfsuff_reduced_bilateral22/input.gms:45-57`" — for the table describing `f21_trade_margin_bilat.cs5` / `f21_trade_tariff_bilat.cs5`.
- **Reality**: input.gms:45-57 covers `f21_trade_scenario_adjustments` (closing) + the `f21_import_supply_historical` declaration — different parameters. The bilateral cost includes are at lines **74** (`f21_trade_margin_bilat.cs5`) and **81** (`f21_trade_tariff_bilat.cs5`); the two `parameter` declarations begin at lines 71 and 78.
- **Evidence**: `modules/21_trade/selfsuff_reduced_bilateral22/input.gms:71-83`
- **verify_cmd**: `grep -n "f21_trade_margin_bilat\|f21_trade_tariff_bilat" .../bilateral22/input.gms` → `74:`, `81:`
- **Fix**: change `input.gms:45-57` to `input.gms:71-83` at module_21.md:415.
- **Confirmed**: yes

### BUG 4 — false "reads vm_land" claim (Minor)
- **Class**: 15 (latent doc error / wrong consumption assertion) — MANDATE 17/20 surface
- **Trigger**: tie-break to Minor (the load-bearing conclusion "does NOT participate in Land Balance" is CORRECT; only the parenthetical justification is fabricated; no invented variable name; advisory subsection)
- **Doc** (module_21.md:612): "Land Balance: ❌ Does NOT participate (**reads `vm_land`** but doesn't affect land allocation)"
- **Reality**: Module 21 does NOT reference `vm_land` in ANY file (equations/presolve/postsolve/preloop, both `vm_land(` and `vm_land.` forms). The "reads vm_land" claim is fabricated.
- **Evidence**: `rg -l "vm_land" /tmp/magpie_develop_ro/modules/21_trade/` → 0 files (exit 1). Positive control `rg -l "vm_prod_reg"` → 3 files (exit 0). Confirmed via second method, MANDATE 20 both-forms covered (bare-string search).
- **Fix**: at module_21.md:612 replace "(reads `vm_land` but doesn't affect land allocation)" with "(does not read `vm_land`; trade operates on production/supply aggregates, not land allocation)".
- **Confirmed**: yes

---

## Verified-Correct Claims (high-value confirmations)

**Equations (selfsuff_reduced, default)** — all 9 names, formulas, AND line citations exact:
- q21_trade_glo (eq:12-14), q21_notrade (18-19), q21_trade_reg (31-35), q21_trade_reg_up (39-42), q21_excess_dem (47-51), q21_excess_supply (56-58), q21_cost_trade_tariff (62-65), q21_cost_trade_margin (69-72), q21_cost_trade_feasibility (76-78). Every cited range matches code. Equation count = 9. ✓
- Macro `m21_baseline_production`: `core/macros.gms:115-119`, expansion reproduced verbatim. ✓
- presolve.gms:11-12 releases `vm_cost_trade_feasibility.lo=0/.up=Inf`. ✓
- preloop.gms:36 `v21_import_for_feasibility.fx=0`. ✓ preloop.gms:27-31 tariff switch ✓. preloop.gms:33-34 forestry margin floor ✓. preloop.gms:11-19 pool allocation loop ✓. preloop.gms:21-23 export-share computation ✓.

**Interface variables (MANDATE 18 DECLARED/POPULATED/READ)**:
- vm_cost_trade_tariff/margin/feasibility — DECLARED selfsuff_reduced/declarations.gms:21-23; present in all 3 realizations; READ only by Module 11 (`11_costs/default/equations.gms:30,31,32` — sole external consumer, confirmed via rg). ✓ Doc's "Used By: Module 11" exactly right.
- vm_prod_reg DECLARED Module 17 (`17_production/flexreg_apr16/declarations.gms:10`) ✓; vm_supply DECLARED Module 16 (`16_demand/sector_may15/declarations.gms:11`) ✓.
- v21_excess_dem/v21_excess_prod/v21_import_for_feasibility internal to selfsuff_reduced (declarations.gms:18-20) ✓.

**bilateral22 (non-default) — R34 regression NOT present**:
- 8 equations (declarations.gms:29-38): q21_notrade, q21_trade_reg, q21_trade_lower, q21_trade_upper, q21_costs_tariffs, q21_costs_margins, q21_cost_trade_tariff, q21_cost_trade_margin. ✓
- NO q21_cost_trade_feasibility. ✓
- presolve.gms:11 `vm_cost_trade_feasibility.fx(i)=0` (presolve.gms EXISTS). ✓
- bilateral param dims (declarations.gms:8-14) all match doc table (lines 504-511). ✓
- tariff fade preloop.gms:60-72 ✓; scalars input.gms:16-27 (10 scalars, all defaults match: factor 1, startyear 2025, targetyear 2050, import_supply 1, import_supply_targetyear 2050, stddev_lib 1, cost_import 1500, forestry 62, scenario_adjustments 0). ✓

**exo (non-default)**: 3 equations (q21_notrade over (h,kall) + tariff + margin) ✓; presolve.gms:10 `vm_cost_trade_feasibility.fx(i)=0` ✓; scalars input.gms:8-11 (only s21_trade_tariff + s21_min_trade_margin_forestry) ✓; declarations.gms:20-24 ✓.

**Sets**: k_notrade=8 ✓ (sets.gms:11-12), k_hardtrade21=16 ✓ (sets.gms:26-29), trade_regime21 (sets.gms:31-46) ✓, k_import21 declared input.gms:12-13 ✓.

**Config defaults (config/default.cfg:644-708 block)**: trade=selfsuff_reduced (650), s21_cost_import=1500 (672-ish), c21_trade_liberalization=l909090r808080 (670), s21_trade_bal_damper=0.65 (673), s21_trade_tariff=1 (694), s21_trade_tariff_factor=1, s21_min_trade_margin_forestry=62 (708). All ✓. Block-end citation 708 correct.

**s21_trade_bal_damper claim (module_21.md:551)**: IS in config (line 673, 0.65) but NOT consumed by any trade .gms code (rg → 0 files, positive control passed). Doc claim "not yet wired into module code" CORRECT. ✓

**f21_exp_shr "no longer exists" claim (module_21.md:218, 500)**: CORRECT. `f21_exp_shr` appears ONLY in a stale realization.gms:26 code-comment, not as a declared/read parameter. The real parameter is `i21_exp_shr` (declared declarations.gms:10, computed preloop.gms:21-23, read equations.gms:58). Doc accurately distinguishes the internal `i21_exp_shr` from a (non-existent) file-read `f21_exp_shr`. ✓

**Schmitz citations**: equations.gms:24-25 ✓, equations.gms:53-54 ✓ (@schmitz_trading_2012 present at both).

**Scaling**: scaling.gms:8-10, all three `.scale(i)=1e5`, equation-scale lines commented out. ✓

---

## Deferred (NOT edited — uncertain or not directly code-checkable)

1. **"Provides To (8 modules)" centrality (module_21.md:621-630)**: M21 POPULATES only the three `vm_cost_trade_*` (read solely by M11). The "provides to Module 16/17/73 + 4 other modules" framing is NOT backed by any interface variable M21 provides; it appears to be a dependency-graph centrality metric sourced from `core_docs/Module_Dependencies.md` (Section 6.2, cited in doc). Whether circular-dependency edges count as "provides" is a graph-convention call defined in another doc. Flagging for review but not editing — would require auditing Module_Dependencies.md's centrality methodology, and the conceptual coupling (M21's balance constraints affect M16/M17/M73 solutions in the simultaneous system) is defensible.

2. **"c21_trade_scenario-style scenario hook" phrasing (module_21.md:551)**: imprecise — config does NOT list `c21_trade_scenario` (verified absent), though the doc's immediate clarification ("appears only in a bilateral22/realization.gms comment") is correct (`realization.gms:37`). The phrasing "config also lists a c21_trade_scenario-style scenario hook" is loose but the doc self-corrects in the same sentence. Not a clean confirmable bug.

3. **`(t,...)` vs `(t_all,...)` time-index shorthand** (e.g., module_21.md:36, parameter tables): doc uses `t` where code declares `t_all`. Conventional doc shorthand throughout MAgPIE docs; not load-bearing. Not edited.
