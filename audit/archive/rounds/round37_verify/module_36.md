# Round 37 Adversarial Verification — module_36.md

Verifier: adversarial (Opus 4.8 1M). Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only).
Default stance: skepticism toward consumer/provider-set claims (highest-FP class).

## Summary

| Bug | Class | consumer_set? | Verdict |
|-----|-------|---------------|---------|
| M36-B1 | wrong provider set (class 15) | YES | **UPHELD** |
| M36-B2 | citation mismatch (12) + latent (15) | YES | **UPHELD** |
| M36-B3 | hardcoded count drift (6) | NO | NOT_CONSUMER_SET (independently confirmed true) |
| M36-B4 | citation mismatch (12) | NO | NOT_CONSUMER_SET (independently confirmed true) |

All four reproduce against develop. B1/B2 are genuine consumer/provider-set corrections and re-derived independently; B3/B4 are not consumer-set findings (pass to fixer unchanged) but I verified them anyway and they hold.

---

## M36-B1 — Provides To: phantom Module 11  → UPHELD

**Doc (line 575):** "Provides To: Module 11 (Costs - labor cost parameters), Module 38 (Factor Costs - wage inputs), Reporting modules (employment statistics)"

**Auditor claim:** M36 provides pm_hourly_costs + pm_productivity_gain_from_wages to M38/57/70 only; v36_employment* to NO module; M11 has zero M36 references → "Provides To Module 11" is phantom.

**Independent re-derivation of the true consumer set:**

Equation form (`NAME(`), all modules, M36 excluded:
```
$ rg -n 'pm_hourly_costs' /tmp/magpie_develop_ro/modules/ | grep -v '36_employment'
70_livestock/fbask_jan16_sticky/equations.gms:62
70_livestock/fbask_jan16/equations.gms:62
38_factor_costs/sticky_labor/equations.gms:29,32,40 ; presolve.gms:51,55,60,72
38_factor_costs/per_ton_fao_may22/equations.gms:13
57_maccs/on_aug22/equations.gms:43
38_factor_costs/sticky_feb18/equations.gms:16
$ rg -n 'pm_productivity_gain_from_wages' /tmp/magpie_develop_ro/modules/ | grep -v '36_employment'
38_factor_costs/{sticky_labor,per_ton_fao_may22,sticky_feb18}, 57_maccs/on_aug22, 70_livestock/{fbask_jan16,fbask_jan16_sticky}
```
→ Consumers of BOTH interface params = exactly **{38, 57, 70}**. (38 also reads attribute forms v38_*.l; the M36 params themselves appear in both equation and presolve contexts — covered.)

Attribute form for M36's own output vars, anywhere:
```
$ rg -n 'v36_employment' /tmp/magpie_develop_ro/modules/ | grep -v '36_employment'   → NO MATCH (exit 1)
$ rg -n 'v36_employment|pm_hourly_costs|pm_productivity_gain_from_wages' /tmp/magpie_develop_ro/core/  → NO MATCH (exit 1)
```
→ v36_employment / v36_employment_maccs consumed by NO module (and not in core/). Confirms output-only.

Module 11 — confirm twice + positive control (this is the "zero consumers / phantom member" high-risk claim):
```
$ rg -n 'v36_|pm_hourly_costs|pm_productivity_gain_from_wages|p36_|q36_' /tmp/magpie_develop_ro/modules/11_costs/   → NO MATCH (exit 1)   [equation form]
$ rg -n 'v36_employment\.|pm_hourly_costs\.|pm_productivity_gain_from_wages\.' /tmp/magpie_develop_ro/modules/11_costs/   → NO MATCH (exit 1)   [attribute form .l/.lo/etc]
$ rg -n 'vm_maccs_costs' /tmp/magpie_develop_ro/modules/11_costs/   → default/equations.gms:28   [POSITIVE CONTROL passes]
```
M11 references NO M36 identifier in either form; positive control (vm_maccs_costs at 11_costs/default/equations.gms:28) proves the search reaches that dir. M11 is a genuine phantom in the "Provides To" set.

Cross-check vs other doc lines: the doc's own line 359/367/572/652 already say the real consumers are 38/57/70 — so line 575 is internally inconsistent (it drops 57+70 AND adds the phantom 11). Auditor's fix ({38,57,70}+Reporting, NOT 11) matches code and resolves the internal inconsistency.

**Verdict: UPHELD.** Auditor's proposed line-575 replacement is correct and complete.

---

## M36-B2 — "consumed by Module 11" misattributed to v36_employment_maccs  → UPHELD

**Doc (line 342), under the v36_employment_maccs equation block (formula lines 335-337):**
"Uses: `vm_maccs_costs` from Module 57; consumed by Module 11 (`modules/11_costs/default/equations.gms:28`)"

**Auditor claim:** the trailing "consumed by Module 11 (eq:28)" describes vm_maccs_costs (M57's var), not v36_employment_maccs; a reader attaches it to v36_employment_maccs → false. v36_employment_maccs is consumed by no module.

**Independent verification:**
- The bullet sits under section "v36_employment_maccs" formula (module_36.md:335-337, `Location: equations.gms:27-28`). M36 equation confirms `q36_employment_maccs(i2) .. v36_employment_maccs(i2) =e= (vm_maccs_costs(i2,"labor")) * ...` (`/tmp/magpie_develop_ro/modules/36_employment/exo_may22/equations.gms:27-28`). So "Uses vm_maccs_costs from Module 57" is TRUE.
- vm_maccs_costs declared at `57_maccs/on_aug22/declarations.gms:25` (`rg vm_maccs_costs ...declarations.gms` → line 25; auditor's fix cites 25 — correct).
- M11 line 28 (`sed -n '28p'`) = `+ sum(factors,vm_maccs_costs(i2,factors))` — it consumes **vm_maccs_costs**, NOT v36_employment_maccs.
- v36_employment_maccs consumed by NO module (see B1 grep: `rg v36_employment` excluding M36 → NO MATCH; positive control there is the M11 grep above).

So the "consumed by Module 11 (eq:28)" clause is a true statement about the *wrong* subject — it describes the variable M36 *uses* (vm_maccs_costs), grammatically attached to the variable the bullet *documents* (v36_employment_maccs, which is consumed by nobody). This is exactly a misattributed-consumer (class 15) wrapped in a content-citation mismatch (class 12). Auditor's fix (split into two sentences; vm_maccs_costs → M11 eq:28; v36_employment_maccs consumed by no module) is accurate.

**Verdict: UPHELD.** Adopt auditor's corrected bullet, including the M57 decl:25 and M11 eq:28 citations (both verified) and the explicit "v36_employment_maccs is consumed by no module."

---

## M36-B3 — "6 input data files" should be 7  → confirmed (NOT a consumer set)

class_is_consumer_set = false (hardcoded-count drift, class 6). Passes to fixer unchanged; verified for completeness.

`/tmp/magpie_develop_ro/modules/36_employment/exo_may22/input.gms` has **7** CSV `$include` lines (16, 22, 28, 35, 42, 48, 54), one per table/parameter:
1. f36_weekly_hours (16) 2. f36_weekly_hours_iso (22) 3. f36_hist_hourly_costs (28) 4. f36_regr_hourly_costs (35, parameter) 5. f36_historic_ag_empl (42) 6. f36_unspecified_subsidies (48) 7. f36_nonmagpie_factor_costs (54).

Doc line 415 says "6 input data files"; doc's own §6.1-6.7 list 7. Count is 7. Auditor correct. (Note doc names "f36_historic_hourly_labor_costs"/"f36_regression_hourly_labor_costs" are the CSV *filenames*; in-GAMS table names are f36_hist_hourly_costs / f36_regr_hourly_costs — naming aside, count = 7.)

---

## M36-B4 — limitation citation `module.gms:10-14` misattributed  → confirmed (NOT a consumer set)

class_is_consumer_set = false (content-citation mismatch, class 12). Passes to fixer unchanged; verified for completeness.

- `module.gms:9-19` = @title (9) + @description (11-18): module purpose only; says nothing about labor supply being/not-being a constraint. So citing `module.gms:10-14` for "NO labor supply constraint" points at non-supporting content.
- The actual limitation text — "Labor availability is not seen as a limiting factor for agricultural production..." — is the `@limitations` block at `realization.gms:16-25`.
- Underlying claim TRUE: `rg '=l=|=g=' .../exo_may22/equations.gms` → NO MATCH; positive control `rg '=e='` → lines 24,28. Only equality constraints; no labor-supply inequality.

Auditor's fix (cite `realization.gms:16-25` @limitations; note no `=l=`/`=g=` in equations.gms) is accurate.

---

## Notes on FP-avoidance discipline applied
- Both equation form `NAME(` AND attribute form `NAME.` greps run for the phantom/zero-consumer claims (B1 M11, v36_employment* solution-level reads) — no presolve/postsolve attribute read of M36 vars exists in M11 (the R33 trap).
- Positive control (vm_maccs_costs in 11_costs) run before declaring M11 a non-consumer.
- Co-located-name caveat: M11 eq:28's "Module 11" in the doc is a real consumer of vm_maccs_costs (M57's var) co-located on the same bullet as v36_employment_maccs — exactly the misattribution B2 flags; not a phantom for vm_maccs_costs, but a phantom when read as v36_employment_maccs's consumer.
