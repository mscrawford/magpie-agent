# Audit Report: Q2 (Module 37 Labor Productivity; M37–M38–M36 interaction)

**Round**: 43 | **Auditor**: Opus | **Date**: 2026-06-03
**Ground truth**: live GAMS at `modules/`, `config/default.cfg` (develop, HEAD ee98739fd, clean)
**Context**: validates freshly-edited `module_37.md` (commit f4f44b0, "resolve bare cites to default realization", previously UNVALIDATED)

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

The answer is exemplary. Every load-bearing claim — default realizations, the abort mechanism, the two distinct labor-cost equations (default vs non-default), the employment back-calculation, and all consumer/producer sets — was verified against code with no discrepancies. The answer correctly leads with the DEFAULT realization, clearly flags the non-default `sticky_labor` as the only consumer of `pm_labor_prod`, reproduces equations verbatim, and gets every variable/equation/parameter name and file:line citation right.

---

## Mechanical checks (M1–M6)

| Check | Result | Evidence |
|---|---|---|
| **M1** File:line citations present | ✅ PASS | `off/preloop.gms:8`, `sticky_feb18/presolve.gms:8-10`, `sticky_feb18/equations.gms:15-17`, `sticky_labor/equations.gms:19-23`, `exo_may22/equations.gms:23-25`, `preloop.gms:49`/`:63`, config `:1214,1235,1191` |
| **M2** Active realization stated | ✅ PASS | States default for all three: M37 `off`, M38 `sticky_feb18`, M36 `exo_may22`; explicitly marks `sticky_labor` as NON-default and required for the `exo` scenario |
| **M3** Variable prefixes valid | ✅ PASS | `pm_labor_prod`, `pm_hourly_costs`, `pm_productivity_gain_from_wages` (pm_); `vm_cost_prod_crop`, `vm_prod_reg`, `vm_cost_prod_livst` (vm_); `v38_laborhours_need`, `v36_employment` (v{N}_); `p38_labor_need` (p{N}_); `s36_*` (s{N}_) — all correct scope |
| **M4** Epistemic badges present | ✅ PASS | 🟡 badges throughout; closing source-statement block with per-claim tagging |
| **M5** Confidence tier matches depth | ✅ PASS | All claims tagged 🟡 (documented) with doc citations; honestly states raw `.gms` NOT opened per docs-only constraint; does NOT over-claim 🟢 |
| **M6** Closing source statement | ✅ PASS | "Based on AI documentation (module_37/38/36.md)" + cross-check note on default.cfg |

---

## Verified Claims (all correct)

### (a) M37 default realization + what it drives
- **Default `off`** — `config/default.cfg:1214` `cfg$gms$labor_prod <- "off"`. ✅
- **M37 realizations = {`off`, `exo`}** — `ls modules/37_labor_prod/` confirms exactly these two. ✅
- **`off` sets `pm_labor_prod(t,j) = 1;`** — `off/preloop.gms:8` (file is 8 lines; line 8 is the statement, verbatim). ✅
- **`pm_labor_prod(t,j)` is a `parameter` dim `(t,j)`, declared `off/declarations.gms:9`** — verified: `parameters / pm_labor_prod(t,j) labor productivity factor (1)`. ✅ (doc's `declarations.gms:9` cite exact)
- **Zero GAMS equations / pure source module** — `find modules/37_labor_prod -name equations.gms` returns nothing in either realization. ✅
- **`exo` populates from `f37_labourprodimpact.cs3` via the 5-key selection** — `exo/preloop.gms:8` verbatim: `pm_labor_prod(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%","%c37_labor_metric%","%c37_labor_intensity%","%c37_labor_uncertainty%");`. ✅
- **"Pure parameterization, not endogenous"** — correct (no equations; values from external ESM data). Proper MANDATE-4 capability-vs-default + parameterization-vs-mechanistic discipline. ✅

### (b) M37 → M38 interaction
- **M38 default `sticky_feb18`** — `config/default.cfg:1235` `cfg$gms$factor_costs <- "sticky_feb18"`. ✅
- **M38 realizations = {`per_ton_fao_may22`, `sticky_feb18`, `sticky_labor`}** — `ls` confirms. The answer's `sticky_labor` is a REAL M38 realization, NOT a confusion with `sticky_feb18` (the auditor's reconciliation concern resolves cleanly — both names exist and are correctly distinguished). ✅
- **`sticky_feb18` ABORTS if `pm_labor_prod` ≠ 1** — `sticky_feb18/presolve.gms:8-10`: `if (smax(j, pm_labor_prod(t,j)) <> 1 OR smin(j, pm_labor_prod(t,j)) <> 1, abort "This factor cost realization cannot handle labor productivities != 1");`. ✅ (answer's prose "abort if ≠ 1" faithful to the smax/smin check)
- **`q38_cost_prod_labor` formula** — `sticky_feb18/equations.gms:15-17` verbatim match: `vm_cost_prod_crop(i2,"labor") =e= sum(kcr, vm_prod_reg(i2,kcr) * sum(ct, p38_labor_need(ct,i2,kcr) * (1/pm_productivity_gain_from_wages(ct,i2)) * (pm_hourly_costs(ct,i2,"scenario")/pm_hourly_costs(ct,i2,"baseline"))))`. ✅
- **`pm_labor_prod` does NOT appear in `sticky_feb18`'s labor cost equation** — confirmed by reading the equation. ✅
- **The divisor `pm_productivity_gain_from_wages` is from M36 (not M37)** — confirmed; populated `36_employment/exo_may22/preloop.gms:63`. ✅
- **Output var `vm_cost_prod_crop(i,"labor")`, mio USD17MER/yr, split labor/capital** — confirmed (`q38_cost_prod_capital` sets the "capital" factor at `equations.gms:21-24`). ✅
- **Non-default `sticky_labor` consumes `pm_labor_prod` in `q38_ces_prodfun`** — `sticky_labor/equations.gms:19-23`; line 22 carries `sum(ct, pm_labor_prod(ct,j2) * sum(cell(i2,j2), pm_productivity_gain_from_wages(ct,i2))) * v38_laborhours_need(j2,kcr)`. ✅ Mechanism ("lower pm_labor_prod → optimizer raises endogenous `v38_laborhours_need` → higher labor cost") is the correct reading of the CES term. ✅

### (c) M36 employment relationship
- **M36 default `exo_may22`** — `config/default.cfg:1191`. ✅ (single realization: `ls` shows only `exo_may22`)
- **M36 provides `pm_hourly_costs(t,i,wage_scen)` and `pm_productivity_gain_from_wages(t,i)`** — populated `preloop.gms:49` and `:63` respectively (exact line cites). ✅
- **`pm_productivity_gain_from_wages` default = 1.0** — `preloop.gms:63` with `s36_scale_productivity_with_wage = 0` (config:1205) yields `0*ratio + (1-0) = 1`. ✅
- **`q36_employment` back-calculates `v36_employment`** — `exo_may22/equations.gms:23-25` verbatim: `v36_employment(i2) =e= (vm_cost_prod_crop(i2,"labor") + vm_cost_prod_livst(i2,"labor") + sum(ct,p36_nonmagpie_labor_costs(ct,i2))) * (1 / sum(ct,f36_weekly_hours(ct,i2)*s36_weeks_in_year*pm_hourly_costs(ct,i2,"scenario")))`. ✅
- **`v36_employment` is REPORTING-only, not a constraint** — STRONGLY confirmed: `rg v36_employment modules/` shows it used ONLY in its own defining `q36_employment` (equations.gms:23) and in `postsolve.gms` (`.l/.m/.up/.lo` extraction into `ov36_employment`). No other module reads it; it bounds nothing; there is no labor-supply limit. ✅ (This is the kind of claim that is easy to assert and hard to verify; the answer got it right and the code confirms it.)
- **M36 does NOT read `pm_labor_prod` directly; M37→M36 link is fully mediated by M38's `vm_cost_prod_crop`** — confirmed (`pm_labor_prod` appears only in M37 and M38, never in M36). ✅

### Summary-table consumer/producer claims (all verified)
- **`vm_cost_prod_crop` consumers = M11 (`q11_cost_reg`) + M36 (`q36_employment`)** — `rg` confirms `11_costs/default/equations.gms:15` `q11_cost_reg(i2) .. v11_cost_reg(i2) =e= sum(factors,vm_cost_prod_crop(i2,factors))` and `36_employment/exo_may22/equations.gms`. ✅ (equation name `q11_cost_reg` exact)
- **`pm_hourly_costs` consumers = M38, M57, M70** — `rg pm_hourly_costs\(` confirms M38 (all 3 realizations), `57_maccs/on_aug22/equations.gms`, `70_livestock/fbask_jan16{,_sticky}/equations.gms`. ✅
- **`pm_productivity_gain_from_wages` consumers = M38, M57, M70** — confirmed identically. ✅

---

## Bugs Found

**None.** Zero Critical, zero Major, zero Minor, zero Informational.

`raw_severity_weighted = 0` → `score = max(0, 10 - 0) = 10`.

---

## Latent doc bugs (§1.5)

**None.** The answer relied on `module_37.md` §8.1 "Default-config caveat", which I cross-checked against code:
- §8.1 claim: "DEFAULT `sticky_feb18` — and also `per_ton_fao_may22` — abort if pm_labor_prod != 1 (`sticky_feb18/presolve.gms:8-10`)." → **VERIFIED**: `per_ton_fao_may22/presolve.gms:8` carries the same `smax/smin ... abort` guard. Both abort. ✅
- §8.1 claim: "pm_labor_prod only consumed in the cost equation by `sticky_labor` (`equations.gms:22`)." → **VERIFIED**: line 22 is the `pm_labor_prod` term in `q38_ces_prodfun`. ✅
- Doc §8 "There is no vm_labor_costs variable; crop factor costs are tracked via vm_cost_prod_crop(i,factors)." → **VERIFIED** (no `vm_labor_costs` exists; the answer correctly never invents one). ✅

The freshly-edited `module_37.md` is **accurate** on every claim load-bearing to this question. The f4f44b0 edit ("resolve bare cites to default realization") correctly disambiguated the `sticky_labor` (non-default consumer) vs `sticky_feb18`/`per_ton_fao_may22` (default, abort) split — exactly the MANDATE-4/8 discipline. No doc fix required.

---

## Missing Nuances (non-scoring, informational)

1. **"200 MAgPIE cells"** (answer §a + table; also in `module_37.md` §8.1): the `j` set size is set by clustering config, not hard-coded in M37. 200 is the conventional default (c200), and the doc states 200, so this is not fabrication and not a bug — but it is a config-dependent number, not a code constant. A maximally-careful phrasing would say "the spatial cells `j` (200 in the default clustering)." Negligible.
2. The answer's "documentation gaps" section proposes a new `cross_module/labor_factor_costs_employment.md`. Reasonable suggestion; not a correctness issue. The existing per-module §8.1 caveats already cover the default-config trap adequately, so this is low-priority.
3. The answer's `q38_cost_prod_labor` line cite in prose (b) says `equations.gms:15-17`; the equation occupies lines 15–17 exactly (statement starts at 15, terminates with `;` at 17). Precise.

---

## Summary

A flawless answer. It demonstrates the full anti-confabulation discipline this flywheel exists to enforce:
- **Default-first** (MANDATE 4): leads with `off`/`sticky_feb18`/`exo_may22`, marks `sticky_labor` clearly as non-default capability.
- **Capability vs default**: explicitly separates "pm_labor_prod is wired to scale cost in sticky_labor" (capability) from "under default it's identically 1 and sticky_feb18 aborts otherwise" (default state).
- **Producer/consumer fidelity** (MANDATE 13/17/18): every consumer set (vm_cost_prod_crop → M11+M36; pm_hourly_costs / pm_productivity_gain_from_wages → M38+M57+M70) verified exact.
- **No invented variables**: correctly states there is no `vm_labor_costs`.
- **Reporting-vs-constraint distinction**: the hardest-to-verify claim (`v36_employment` is reporting-only) is correct and code-confirmed.

The freshly-edited `module_37.md` (f4f44b0) passes validation with no required fixes.

**Score: 10/10 — ACCURATE.**
