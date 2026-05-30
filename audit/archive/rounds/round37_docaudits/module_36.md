# Round 37 Doc Audit — module_36.md (Employment)

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_36.md` (1195 lines)
**Ground truth**: `/tmp/magpie_develop_ro/modules/36_employment/exo_may22/*.gms` + `config/default.cfg`
**Default realization**: `exo_may22` (confirmed sole realization; `cfg$gms$employment <- "exo_may22"`)

---

## Overall Verdict: MOSTLY ACCURATE (lower band)
## Accuracy Score: 7/10

The doc is largely faithful: every `preloop.gms`, `presolve.gms`, `equations.gms`, `declarations.gms`, and `input.gms` citation I checked is line-accurate, all interface-variable names exist, all scalar defaults are correct, and the downstream consumer set (38/57/70) and upstream producer set (09/38/57/70) are correct. The headline error is a **phantom Module 11 linkage**: the doc twice asserts that Module 36 provides to / is consumed by Module 11, conflating Module 36's reporting variable `v36_employment_maccs` with `vm_maccs_costs` (Module 57's variable, which Module 11 genuinely consumes at `11_costs/default/equations.gms:28`). This contradicts the doc's own (correct, repeated) claim that Module 36 is output-only and touches no optimization. Plus a minor input-file count drift and one imprecise limitation citation.

---

## Method / probes run

Default realization:
- `rg -n 'cfg\$gms\$employment' config/default.cfg` → `exo_may22` (line in default.cfg). Only one realization dir exists (`ls modules/36_employment/` → `exo_may22`, `module.gms`).

Interface-consumer enumeration (MANDATE 13, both `(` and `.` forms, cross-checked with `grep -rc`, positive controls run):
- `pm_hourly_costs` consumers: M38 (sticky_labor, sticky_feb18, per_ton_fao_may22), M57 (on_aug22), M70 (fbask_jan16, fbask_jan16_sticky), M36 (preloop/presolve/equations). → doc set {38,57,70} CORRECT.
- `pm_productivity_gain_from_wages` consumers: same set {38,57,70} + M36. → CORRECT.
- `v36_employment` / `v36_employment_maccs`: referenced ONLY in M36's own equations.gms/postsolve.gms/declarations.gms. No external consumer (neither `(` nor `.`/solution-level form). Positive control: `rg 'v36_employment_maccs' .../equations.gms` → hit at line 27 (grep works). External `.l/.m/.lo/.up` read search returned empty.

Upstream producer attribution (MANDATE 9):
- `vm_cost_prod_crop` → M38 (all 3 realizations declare it). CORRECT.
- `vm_cost_prod_livst` → M70 (fbask_jan16:12, fbask_jan16_sticky:12). CORRECT.
- `vm_maccs_costs` → M57 (on_aug22/declarations.gms:25). CORRECT.
- `pm_factor_cost_shares` → M38. CORRECT.
- `im_gdp_pc_mer_iso` → M09 (aug17/declarations.gms:16). CORRECT.

Module 11 cross-check (the phantom):
- `rg -n 'v36_employment' modules/11_costs/` → EXIT 1 (no hit).
- `rg -n 'pm_hourly_costs|pm_productivity_gain|_employment' modules/11_costs/` → EXIT 1 (no hit).
- `grep -rc 'v36_employment' modules/11_costs/` → no nonzero file.
- `rg -n 'vm_maccs_costs|v36_employment' modules/11_costs/default/equations.gms` → ONLY `28: + sum(factors,vm_maccs_costs(i2,factors))`. So `11_costs/default/equations.gms:28` is `vm_maccs_costs`, NOT `v36_employment_maccs`.

---

## Verified Claims (correct)

- **All preloop.gms citations line-accurate**: calibration 9-10, total-hours 11, base regression 18-19, historical constraint 23, wage-increase 27, phase-in 41, phase-out 43, post-2100 45, regional aggregation 49, productivity gain 63. (`rg -n` on each statement matched the doc's cited line.)
- **presolve.gms:15-17** nonmagpie labor cost formula matches code exactly. CORRECT.
- **equations.gms:23-25 / 27-28** — both equations match code verbatim, including `vm_cost_prod_crop(i2,"labor")`, `vm_cost_prod_livst(i2,"labor")`, `sum(ct,p36_nonmagpie_labor_costs(ct,i2))`, `vm_maccs_costs(i2,"labor")`. CORRECT.
- **declarations.gms:15 / :16** — `v36_employment(i)` line 15, `v36_employment_maccs(i)` line 16. CORRECT.
- **Scalar defaults** (MANDATE 3): `s36_weeks_in_year=52.1429` (input.gms:9), `s36_minimum_wage=0` (input.gms:10), `s36_scale_productivity_with_wage=0` (input.gms:11). All CORRECT — no inverted defaults.
- **Downstream consumer set {38,57,70}** for both interface params. CORRECT (MANDATE 13).
- **Cited consumer lines**: `57_maccs/on_aug22/equations.gms:43` reads pm_hourly_costs (doc line 1050) ✓; `70_livestock/fbask_jan16/equations.gms:62` reads pm_hourly_costs (doc line 1051) ✓. Both are DEFAULT realizations (maccs=on_aug22, livestock=fbask_jan16 confirmed in default.cfg).
- **"NO labor supply constraint"** claim is TRUE — no `=l=`/`=g=` in equations.gms (only `=e=` reporting definitions); no external solution-level read of v36_employment. (Citation imprecise — see M36-B4.)
- **"Code Size: 282 lines across 8 files"** — exactly correct (37+28+56+28+65+19+36+13 = 282 across the 8 exo_may22 .gms files).
- **Author: Debbora Leip** — matches `module.gms:20 @authors`.
- **Advisory check (vm_cost_prod_livst('labor') at equations.gms:24)**: CONFIRMED present. Doc correctly attributes it to M70. No bug.

---

## Bugs Found

### M36-B1 — Phantom "Provides To: Module 11"
- **Severity**: Major (tier_uncertainty: true — R20 "wrong consumer/provider set" anchor argues Critical; pulled down by tie-breaker because section 7.1/7.2 list the correct set {38,57,70} elsewhere, so a cross-referencing reader catches the inconsistency, and no variable name is invented).
- **Class**: 15 (latent doc error / wrong consumer-set) + 2-adjacent (false interface assertion).
- **Trigger**: §1 Major — "claim wrong in a way that misleads about behavior"; resembles R20 anchor (wrong consumer/populator set).
- **Doc line**: module_36.md:575
- **Claim in doc**: "**Provides To**: Module 11 (Costs - labor cost parameters), Module 38 (Factor Costs - wage inputs), Reporting modules (employment statistics)"
- **Reality in code**: Module 36 provides `pm_hourly_costs` + `pm_productivity_gain_from_wages` (to M38/57/70 only) and `v36_employment*` (to NO module). Module 11 contains zero references to any Module 36 variable/parameter. The "labor cost parameters provided to Module 11" interface does not exist.
- **File evidence**: `rg 'pm_hourly_costs|pm_productivity_gain|_employment' /tmp/magpie_develop_ro/modules/11_costs/` → EXIT 1 (no match); positive control `rg 'pm_hourly_costs' modules/57_maccs/on_aug22/equations.gms` → hit at :43.
- **Why it matters**: Asserting M36 feeds Module 11 (the central cost-aggregation module) implies employment outputs enter the optimization — flatly contradicting the doc's own repeated, correct claim that M36 is post-processing/output-only (lines 24, 241-244, 555-565, 1092). A modification-safety reader could wrongly conclude editing M36 ripples into cost optimization.
- **Proposed fix**: Replace line 575 with: `**Provides To**: Module 38 (Factor Costs - wage + productivity inputs), Module 57 (MACCs - wage + productivity inputs), Module 70 (Livestock - wage + productivity inputs), Reporting modules (employment statistics). Module 36 does NOT provide to Module 11 (employment variables are output-only and enter no cost equation).`

### M36-B2 — Misleading "consumed by Module 11" on v36_employment_maccs
- **Severity**: Major (tier_uncertainty: true).
- **Class**: 12 (content-level citation mismatch) + 15 (latent doc error).
- **Trigger**: §1 Major — "citation points at content that says something materially different" / misleads about behavior.
- **Doc line**: module_36.md:342
- **Claim in doc**: "**Uses**: `vm_maccs_costs` from Module 57; consumed by Module 11 (`modules/11_costs/default/equations.gms:28`)" — in section 4.2 documenting the variable `v36_employment_maccs`.
- **Reality in code**: The subject being documented (`v36_employment_maccs`) is consumed by NO module. The "consumed by Module 11 (equations.gms:28)" clause actually describes `vm_maccs_costs` (Module 57's variable) — `11_costs/default/equations.gms:28` is `+ sum(factors,vm_maccs_costs(i2,factors))`, which has nothing to do with employment. In a variable-documentation block headed by `v36_employment_maccs`, a reader attaches "consumed by Module 11" to the documented variable → false.
- **File evidence**: `rg -n 'vm_maccs_costs|v36_employment' /tmp/magpie_develop_ro/modules/11_costs/default/equations.gms` → only `28: + sum(factors,vm_maccs_costs(i2,factors))`. `rg 'v36_employment' modules/11_costs/` → EXIT 1.
- **Proposed fix**: Replace the "**Uses**" bullet content at line 342 with: `- **Uses**: `vm_maccs_costs(i,"labor")` from Module 57 (`modules/57_maccs/on_aug22/declarations.gms:25`).` and DELETE the "consumed by Module 11" clause. If a note on `vm_maccs_costs`'s own downstream use is desired, add a separate sentence: `(Separately, `vm_maccs_costs` itself enters Module 11's cost aggregation at `modules/11_costs/default/equations.gms:28`; `v36_employment_maccs` does not — it is a reporting variable consumed by no module.)`

### M36-B3 — Input-file count drift ("6" should be "7")
- **Severity**: Minor.
- **Class**: 6 (hardcoded counts drift).
- **Trigger**: §1 Minor — "wrong detail; a careful reader wouldn't be misled into action" (the doc then lists all 7 correctly).
- **Doc line**: module_36.md:415
- **Claim in doc**: "Module 36 uses **6 input data files** (`input.gms:14-56`)"
- **Reality in code**: 7 input CSV files / tables (`rg -c '\$include.*\.csv' input.gms` → 7): f36_weekly_hours, f36_weekly_hours_iso, f36_historic_hourly_labor_costs, f36_regression_hourly_labor_costs, f36_historic_ag_employment, f36_unspecified_subsidies, f36_nonmagpie_factor_costs. The doc's own sections 6.1-6.7 enumerate 7.
- **File evidence**: `rg -c '\$include.*\.csv' /tmp/magpie_develop_ro/modules/36_employment/exo_may22/input.gms` → 7.
- **Proposed fix**: Change "**6 input data files**" to "**7 input data files**" at line 415.

### M36-B4 — Imprecise limitation citation (module.gms:10-14)
- **Severity**: Minor.
- **Class**: 12 (content-level citation mismatch).
- **Trigger**: §1 Minor — "off-by citation where the claim itself is true but the cited content doesn't support it".
- **Doc line**: module_36.md:661
- **Claim in doc**: "❌ **NO labor supply constraint** (`module.gms:10-14`)"
- **Reality in code**: `module.gms:10-14` is the `@description` block (module purpose), which says nothing about labor supply being a constraint or not. The actual statement that labor availability is NOT limiting is in `realization.gms:16-25` (`@limitations` block: "Labor availability is not seen as a limiting factor for agricultural production..."). The underlying claim (no labor-supply constraint) is TRUE (no `=l=`/`=g=` in equations.gms), but the citation points at non-supporting content.
- **File evidence**: `sed -n '9,19p' module.gms` (description block, no constraint statement); `realization.gms:16-25` contains the limitation text.
- **Proposed fix**: Change citation at line 661 from "(`module.gms:10-14`)" to "(`realization.gms:16-25` @limitations; no `=l=`/`=g=` constraint in `equations.gms`)".

---

## Deferred (not code-verifiable in this worktree / not edited)

- Input-data SOURCE attributions (FAO AgSE, ILO ILOSTAT, FAO EAA, "typical values 40-60 h/week", "slope 0.6-0.8", "share 5-10%") are preprocessing/empirical claims not resolvable from the GAMS worktree. The GAMS table descriptions are consistent with them but do not confirm the FAO/ILO provenance. Route to preproc-agent if challenged.
- `reportAgEmployment` / SDG-8 output naming (advisory mention) is magpie4 (downstream R) territory, not GAMS-checkable here. Doc makes no false GAMS claim about it.
- Section 5.1 lists `pm_hourly_costs` consumed by "36 (presolve)" — M36 actually uses it in preloop+presolve+equations; "presolve" is incomplete but not wrong. Not flagged.
- Doc's informal "Numerator/Denominator" annotation of the presolve formula (lines 296-299) is loose phrasing; the formula shown (lines 268-273) matches code exactly. Not a factual error.
- "12 regions" throughout — consistent with the h12 regionmapping default (`cfg$input` uses `_h12_`). Standard. Not flagged.
- "Centrality: ~35 of 46 modules" / "Status: 1076 lines documented, 3.8x expansion" — doc-meta/metadata, not a code claim (and doc is now 1195 lines; the "1076" is stale self-metadata but harmless metadata, not flagged as a code bug).
