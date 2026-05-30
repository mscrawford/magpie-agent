# Round 36 Doc Audit — module_39.md (Land Conversion Costs)

**Auditor**: Opus adversarial documentation auditor
**Target doc**: `magpie-agent/modules/module_39.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Date**: 2026-05-30

---

## Overall Verdict: MOSTLY ACCURATE (high band)

### Accuracy assessment

Module 39 is a small, stable module (one realization `calib`, one equation `q39_cost_landcon`, one interface output `vm_cost_landcon`). The doc is **unusually accurate** on the load-bearing facts: every scalar name + default value, the equation formula, the declared dimensions, the realization name, and the producer/consumer set all match develop. The bugs found are at the **Minor** tier (representational simplifications, a unit-string drop in a code comment, and one parameterization-vs-mechanism overstatement). No Critical or Major bug found.

The pre-run CHECKER LEAD is **partially confirmed** (the line-578 unit string is imprecise — Minor) and **partially refuted** (the M11 consumer set and the q39 equation set are fully correct).

---

## Ground-truth facts established (with evidence)

| Fact | Code evidence | Doc status |
|---|---|---|
| Default & only realization = `calib` | `config/default.cfg`: `cfg$gms$landconversion <- "calib"`; `ls modules/39_landconversion/` → only `calib/`, `input/`, `module.gms` | ✓ doc:4 correct |
| Equation `q39_cost_landcon(j2,land)` (the only one) | `calib/equations.gms:12-15`; `calib/declarations.gms:9` | ✓ doc:97-100, 928 correct (verbatim) |
| `vm_cost_landcon(j,land)` declared in M39 | `calib/declarations.gms:13`, unit "mio. USD17MER per yr" | ✓ doc:283-286 correct |
| **Sole external consumer = Module 11** | `grep -rn vm_cost_landcon`: only hit outside M39 is `11_costs/default/equations.gms:20` (`+ sum((cell(i2,j2),land), vm_cost_landcon(j2,land))`). M11 default = `default` (only realization). | ✓ doc:254, 291, 950 correct & complete |
| `vm_landexpansion`/`vm_landreduction` from Module 10 | `10_land/landmatrix_dec18/declarations.gms:20-21`, unit "mio. ha" | ✓ doc:237-240, 295-307 correct |
| `pm_interest` from Module 12 | `12_interest_rate/select_apr20/declarations.gms:9` | ✓ doc:245-247 correct |
| Scalars + defaults | `calib/input.gms:9-14`: crop `/12300/`(L9), reward `/7380/`(L10), past `/9840/`(L11), forestry `/1230/`(L12), urban `/12300/`(L13), `s39_ignore_calib /0/`(L14) | ✓ all values & per-scalar citations doc:316/322/327/332/337/386 correct |
| Calibration application | `calib/presolve.gms:12` (crop cost), `:13` (crop reward), `:14` past, `:15` forestry, `:16` urban | ✓ doc:66-69, 369-371 correct |
| Init-to-zero | `calib/preloop.gms:8` (all `i39_cost_establish=0`), `:9` (all `i39_reward_reduction=0`) | ✓ doc:285, 379, 412 correct |
| ignore_calib / missing-file logic | `calib/preloop.gms:13-16` (`if(...=0 OR s39_ignore_calib=1, cost=1; reward=0;)`) | ✓ doc:388-392, 410, 414 correct |
| `i39_*` parameter declarations | `calib/declarations.gms:17` (cost_establish), `:18` (reward_reduction), `:19` (calib) | ✓ doc:344/353/364/374 correct |
| `type39` set = {cost, reward} | `calib/sets.gms:9-10` | ✓ doc:345/355 correct |
| `land` set = 7 members | `core/sets.gms:251`: `crop, past, forestry, primforest, secdforest, urban, other` | ✓ doc:285 "full 7-member" correct |
| `vm_lu_transitions` exists (used in "Better Approach" pseudocode) | `10_land/landmatrix_dec18/declarations.gms:23` | ✓ doc:528 not fabricated |
| Module 38 annuity `(r+d)/(1+r)` | `38_factor_costs/sticky_feb18/equations.gms:23` (`(pm_interest + s38_depreciation_rate)/(1+pm_interest)`) | ✓ doc:142 correct |

---

## Bugs Found

### Bug module_39-B1 — Unit string drops currency-year qualifier in test-code comment

- **Severity**: Minor
- **Class**: 12 (content-level citation mismatch / unit imprecision)
- **Trigger**: §1 Minor — "Wrong detail, but a careful reader wouldn't be misled into action" (the canonical unit is correctly stated elsewhere at doc:286).
- **Claim in doc** (module_39.md:578): `` `vm_cost_landcon` - Total costs (mio USD/yr) `` (also doc:579-580 `mio ha` glosses)
- **Reality in code**: canonical unit is `mio. USD17MER per yr` (`calib/declarations.gms:13`). The doc's PRIMARY units field (doc:286) correctly says "mio USD17MER per yr"; only this testing-section comment drops "17MER".
- **File evidence**: `/tmp/magpie_develop_ro/modules/39_landconversion/calib/declarations.gms:13`
- **verify_cmd**: `grep -n USD modules/39_landconversion/calib/declarations.gms` → `13: vm_cost_landcon(j,land) ... (mio. USD17MER per yr)`
- **Confirmed**: true
- **Proposed fix**: change doc:578 `(mio USD/yr)` → `(mio. USD17MER per yr)` for consistency with the canonical unit. (CHECKER LEAD confirmed on this point.)

### Bug module_39-B2 — Section 2.1 code block uses non-GAMS assignment syntax and a non-contiguous range

- **Severity**: Minor
- **Class**: 4 (conceptual pseudo-code presented as code) / 10 (citation range)
- **Trigger**: §1 Minor.
- **Claim in doc** (module_39.md:32-39): cited as `input.gms:9-14`, shown as `s39_cost_establish_crop = 12300` ... `s39_cost_establish_past = 9840` ... `s39_cost_establish_forestry = 1230` ... `s39_cost_establish_urban = 12300` (4 lines, `=` syntax, contiguous).
- **Reality in code**: `input.gms` uses GAMS scalar-declaration syntax `s39_cost_establish_crop ... / 12300 /`; the cited range 9-14 ALSO contains `s39_reward_crop_reduction /7380/` (L10) and `s39_ignore_calib /0/` (L14), which the block omits; order in code is crop(9), reward(10), past(11), forestry(12), urban(13), ignore(14). Names + values are correct.
- **File evidence**: `/tmp/magpie_develop_ro/modules/39_landconversion/calib/input.gms:9-14`
- **verify_cmd**: `awk 'NR>=9 && NR<=14' input.gms` → confirms `/value/` syntax + reward at L10 + ignore at L14.
- **Confirmed**: true
- **Proposed fix**: replace the `= value` block with the actual GAMS scalar syntax (`s39_cost_establish_crop ... / 12300 /` etc.), or relabel the block "Conceptually (values from `input.gms:9-13`)". Minor; values/names already correct.

### Bug module_39-B3 — "Enforcing minimum 1.0 by 2050" presented as model (GAMS) behavior; actually an input-data property

- **Severity**: Minor
- **Class**: 4 (mechanism description) — parameterization-vs-mechanism (AGENT.md three-check)
- **Trigger**: §1 Minor (tie-breaker pulls down from Major: the convergence OUTCOME is real — it is baked into `f39_calib.csv` — so a reader is not misled about the result, only about WHERE it happens; no file:line is mis-cited because DOES#6 carries none).
- **Claim in doc** (module_39.md:408, DOES list): "**Converges calibration to baseline** by **enforcing** minimum calibration factor of 1.0 by 2050". Also asserted doc:77, 226-229, 350.
- **Reality in code**: No GAMS code in module 39 (or anywhere) enforces a 2050 minimum or any `min/smax` on `i39_calib`. `grep -rn i39_calib --include=*.gms` outside M39 → no match (exit 1; positive control `s39_cost_establish_crop` found, proving the search works). The only mention of "lifted to a minimum of 1 ... by 2050" is the **description comment** `calib/realization.gms:14`. The convergence is therefore a property of the pre-computed input `f39_calib.csv` (preprocessing calibration), read verbatim at `preloop.gms:11` (`i39_calib(t,i,type39) = f39_calib(t,i,type39);`).
- **File evidence**: `/tmp/magpie_develop_ro/modules/39_landconversion/calib/preloop.gms:11`; `calib/realization.gms:14` (comment only); absence verified across all `.gms`.
- **verify_cmd**: `find modules/39_landconversion -name '*.gms' -exec grep -l 'smax\|smin\|min(\|max(\|2050\|m_year' {} +` → only `calib/realization.gms` (a `*'` doc comment, not code).
- **Confirmed**: true
- **Proposed fix**: reword doc:408 to "Receives calibration factors (from input data `f39_calib.csv`) that are constructed to converge to a minimum of 1.0 by 2050; this convergence is a property of the calibration data, not GAMS-side enforcement (no `min`/year logic exists in the `calib` `.gms` files; the realization comment at `realization.gms:14` documents it)." Optionally add a one-line caveat at doc:226-229.

---

## Notes / smaller imprecisions (NOT recorded as separate bugs — sub-Minor, internal to explanatory glosses)

- Doc:113-114 and doc:1130 gloss `i39_cost_establish` / `i39_reward_reduction` as `(i,land)` (2-dim) in prose "Where:" lists; the declared and equation-used form is 3-dim `(t,i,land)` / `(ct,i2,land)`. The FORMAL equation block (doc:97-100) has it right with `ct`. This is an explanatory-gloss simplification, consistent within itself; fold into B2's general "prose drops time index" if desired.
- Doc:400 (DOES#2) cites `input.gms:18-22` for "applies regional calibration factors" — that range is actually the `f39_calib` table-read block (`$onEmpty / table f39_calib ... / $offdelim`), i.e. where the calibration DATA is loaded, not where it is applied (application is `presolve.gms:12`, which DOES#2 also cites). Defensible; not flagged.
- Modification sections (doc:461, 482, 500, 559) likewise use `s39_x = value` rather than editing the `/ value /` scalar default. Same class as B2; the "Was: X" framing makes intent clear. Not flagged separately.

---

## CHECKER LEAD disposition

> "vm_cost_landcon at module_39.md:578 claims unit 'mio USD/yr' but canonical is 'mio. usd17mer per yr' (calib/declarations.gms:13)"

**CONFIRMED** as Bug module_39-B1 (Minor — it is a test-code comment; the canonical unit is correctly given at doc:286). 

> "Verify default realization and q39_* land-conversion-cost equations + vm_cost_landcon consumer set (M11). Both grep forms."

**REFUTED (i.e., doc is correct)**: default realization `calib` ✓; the only equation is `q39_cost_landcon` and the doc claims no others ✓; `vm_cost_landcon` sole external consumer is Module 11 (`11_costs/default/equations.gms:20`), verified with both `grep -rn` and `rg -n` plus a `vm_cost_landcon.` (solution-attribute) grep that found only M39's own postsolve/scaling. Consumer set in doc is correct and complete.

---

## Deferred (not code-verifiable here)

- The exact regional `i39_calib` values / patterns (doc §4.3, Eastern-Europe examples): live in `f39_calib.csv` runtime input (not in the develop worktree; only a `files` manifest is present). Cannot confirm specific values.
- Literature-citation accuracy (doc §13.1, Strassburg 2014 / Schmitz 2014 / Dietrich 2019 / Popp 2014): not code-checkable.
- Behavioral/range claims in the R testing section (e.g., "20-50% less expansion with doubled cost", "2-5x more reduction with rewards"): require model runs; not statically verifiable.
- The realization.gms `@limitations` "Data availability ... very limited" (doc:1126 cites `realization.gms:16`): confirmed present at `realization.gms:16` — correct, no bug.

---

## Summary

module_39.md is a high-accuracy doc. All interface variable/parameter/equation names, scalar defaults (12300/7380/9840/1230/12300/0), the equation formula, dimensions, the single realization (`calib`), and the producer (M10/M12) and consumer (M11, sole) sets match develop. Three Minor bugs: (B1) a unit string drops "17MER" in a test-code comment; (B2) the §2.1 code block uses non-GAMS `=` syntax over a non-contiguous range; (B3) "enforcing minimum 1.0 by 2050" is presented as GAMS behavior but is actually an input-data (`f39_calib.csv`) property documented only in a `realization.gms` comment. No Critical/Major bugs. Score ≈ 8.5/10.
