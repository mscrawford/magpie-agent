# Round 34 Doc Audit — module_38.md (Factor Costs)

**Auditor**: Opus 4.8 (1M ctx), adversarial doc-vs-code audit
**Target doc**: `magpie-agent/modules/module_38.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (Merge PR #887), branch develop worktree
**Date**: 2026-05-30

---

## Overall Verdict: MOSTLY ACCURATE (high band)

Score profile: 1 Major bug (wrong cross-module attribution for `pm_prod_init`). Everything else load-bearing checked out: default realization, all three realizations' equation names + line citations, all scalar defaults, the consumer set of `vm_cost_prod_crop`, the s38_immobile split direction, the annuitization arithmetic, and the verbatim CES snippet. The doc is unusually clean for its length; the single defect is a co-located-citation trap (correct line numbers, wrong module label).

Per §4 weighting: 10 − 2 (one Major) = **8/10**.

---

## Bugs Found

### M38-B1 — `pm_prod_init` attributed to Module 30 (Croparea); actually Module 17 (Production)

- **Severity**: Major
- **Class**: 15 (latent doc error — wrong populator/source module for an interface parameter) / overlaps MANDATE 13 (interface-parameter consumer/producer) + MANDATE 6 (module characterization)
- **Trigger (§1 Major)**: "Wrong variable prefix / semantic scope wrong" sibling — here the *source module* is wrong, which misleads a dependency/modification analysis. Not Critical: it does not point the user at a wrong file to *edit for M38*, and the file:line citation itself (`presolve.gms:31-32`) is correct; only the upstream module label is wrong.
- **Doc line**: `module_38.md:352`
- **Claim in doc**: "**Module 30 (Croparea)**: `pm_prod_init(j,kcr)` — initial production used for first-period capital stock estimation (`modules/38_factor_costs/sticky_feb18/presolve.gms:31-32`)"
- **Reality in code**: `pm_prod_init(j,kcr)` is DECLARED and POPULATED in **Module 17 (production)**, `flexreg_apr16`. It is *read* by M38 (sticky_feb18 + sticky_labor presolve) and by M17 itself. M30 (croparea) neither declares nor populates it. Its description in M17 declarations is "Production initialization for year 1995 (tDM per yr)" — a production-domain variable, populated from `fm_croparea` × `pm_yields_semi_calib`.
- **File evidence**:
  - `modules/17_production/flexreg_apr16/declarations.gms:18` — `pm_prod_init(j,kcr)  Production initialization for year 1995 (tDM per yr)`
  - `modules/17_production/flexreg_apr16/presolve.gms:10` — `pm_prod_init(j,kcr)=sum(w,fm_croparea("y1995",j,w,kcr)*pm_yields_semi_calib(j,kcr,w));`
- **verify_cmd**: `rg -ln 'pm_prod_init' /tmp/magpie_develop_ro/modules/ -g 'declarations.gms'` → only `modules/17_production/flexreg_apr16/declarations.gms`. And `rg -n 'pm_prod_init' .../17_production/flexreg_apr16/presolve.gms` → assigned at line 10 (populator). No M30 hit anywhere.
- **confirmed**: true (declaration + population both in M17; zero references in any 30_* module file — verified by directory-scoped grep + the global declarations grep returning M17 only).
- **proposed_fix**: On `module_38.md:352` replace `**Module 30 (Croparea)**: \`pm_prod_init(j,kcr)\`` with `**Module 17 (Production)**: \`pm_prod_init(j,kcr)\``. (The trailing file:line citation `presolve.gms:31-32` is correct — that is the M38-side read site — and stays.) Pseudocode uses of `pm_prod_init` at lines 202-203 carry no module label and need no change.

---

## Verified Claims (correct — spot list of the load-bearing ones)

**Realizations / structure**
- Default `sticky_feb18` — `config/default.cfg`: `cfg$gms$factor_costs <- "sticky_feb18"` ✓
- 3 realizations: `sticky_feb18`, `sticky_labor`, `per_ton_fao_may22` (`ls modules/38_factor_costs/`) ✓
- Line counts: sticky_feb18 = 307, sticky_labor = 511, per_ton = 231 ✓ (all 3 verified by `wc -l`)
- File counts: 9 / 12 / 9 ✓; sticky_labor includes `nl_fix/nl_relax/nl_release.gms` ✓

**sticky_feb18 equations + citations (all exact)**
- `q38_cost_prod_labor` @ `equations.gms:15-17` ✓ (doc snippet matches code verbatim)
- `q38_cost_prod_capital` @ `equations.gms:21-24` ✓
- `q38_investment_immobile` @ `equations.gms:33-36` ✓
- `q38_investment_mobile` @ `equations.gms:41-44` ✓
- declarations: `vm_cost_prod_crop` @ :16, `v38_investment_immobile` @ :17, `v38_investment_mobile` @ :18 ✓

**sticky_labor**
- 6 q38 eqns: `q38_ces_prodfun`, `q38_labor_share_target`, `q38_cost_prod_labor`, `q38_cost_prod_capital`, `q38_investment_immobile`, `q38_investment_mobile` ✓
- CES @ `equations.gms:19-23` — doc's GAMS block (lines 242-246) matches code character-for-character ✓
- `v38_capital_need`, `v38_laborhours_need`, `v38_relax_CES_lp` are variables ✓
- `i38_ces_shr` / `i38_ces_scale` calibrated in `sticky_labor/presolve.gms:55-56` ✓
- min-labor-share ramp (0 → target between start/target years × fulfillment) @ `presolve.gms:25-37` ✓
- CES activates `m_year(t) > s38_startyear_labor_substitution` @ `presolve.gms:59` ✓
- Orlov CES citation present in code as `@orlov_ces_2021` ✓

**per_ton_fao_may22**
- 2 eqns: `q38_cost_prod_crop_labor`, `q38_cost_prod_crop_capital` ✓
- doc's "Conceptually" formula matches code (fac_req = `i38_fac_req`, shares = `pm_factor_cost_shares`, wage scaling + productivity divisor on labor) ✓ — correctly labeled conceptual (MANDATE 5 satisfied)

**Scalar defaults (all verified in code; MANDATE 3)**
- `s38_depreciation_rate` = 0.05 (`sticky_feb18/input.gms:13`) ✓
- `s38_immobile` = 1 (`input.gms:15`) ✓
- `c38_fac_req` = `glo` (`input.gms:8`) ✓
- `s38_ces_elast_subst` = 0.3, `s38_startyear_labor_substitution` = 2025, `s38_target_labor_share` = 0 (OFF), `s38_targetyear_labor_share` = 2050, `s38_target_fulfillment` = 0.5 (`sticky_labor/input.gms:16-20`) ✓

**Consumer set of `vm_cost_prod_crop` (MANDATE 13 + 17 — checked paren-form AND `.`-attr form)**
- Equation-level readers across ALL modules: **only** M11 `q11_cost_reg` (`11_costs/default/equations.gms:15`, both factors via `sum(factors,...)`) and M36 `q36_employment` (`36_employment/exo_may22/equations.gms:23-25`, `"labor"` slice). No phantom consumers, no omitted consumers. ✓
- `vm_cost_prod_crop.` attr-form hits are all within M38's own postsolve/scaling (self-reporting), not external consumers ✓

**Other §6 dependency attributions (all correct except B1)**
- `vm_prod_reg(i,kall)`, `vm_prod(j,k)` → M17 ✓
- `pm_interest` @ `presolve.gms:25-26` + `equations.gms:23` ✓
- `pm_hourly_costs`, `pm_productivity_gain_from_wages` → M36 ✓
- `pm_labor_prod` → M37 (realizations `exo`/`off`) ✓
- `im_gdp_pc_ppp_iso` → M09 (drivers), used `preloop.gms:10,12` ✓

**Mechanics not inverted**
- s38_immobile split: mobile = `× (1-s38_immobile)`, immobile = `× s38_immobile` (`presolve.gms:25-26`) — doc §2.7 step 3 has it in the correct direction ✓ (R20-style inversion trap avoided)
- Annuitization factor (r+d)/(1+r) = (0.05+0.05)/1.05 = 0.0952 ✓ (doc §2.1.2 arithmetic correct)
- Capital init `if (ord(t)=1)` @ `presolve.gms:28-32`; depreciation `**m_timestep_length` @ 38-39; postsolve stock update @ `postsolve.gms:9-10` ✓
- abort-if-`pm_labor_prod`≠1 @ `presolve.gms:8-10` ✓
- "factor costs independent of harvested area" limitation @ `realization.gms:15-18` ✓

**Input filenames** (`input/files` manifest): `f38_fac_req_fao.csv`, `f38_fac_req_fao_regional.cs4`, `f38_historical_share_iso.csv`, `f38_regression_cap_share.csv`, `f38_hist_factor_costs_iso.csv` — all match doc §7 / §13.2 ✓

---

## Pre-run advisory — adjudicated

The advisory raised three checks. Verdicts:

1. **"Default may be sticky_labor with a CES prodfun — verify"** → REFUTED. Default is `sticky_feb18` (no CES). Doc states this correctly throughout. ✓
2. **"R28 fixed q38_ces_prodfun — verify it held"** → HELD. `q38_ces_prodfun` exists in `sticky_labor/equations.gms:19-23` exactly as the doc quotes it; the doc correctly scopes it to the non-default `sticky_labor`. ✓
3. **"M36 reads vm_cost_prod_livst('labor') — verify vm_cost_prod_* consumer attribution"** → NO BUG in module_38.md. `q36_employment` reads BOTH `vm_cost_prod_crop(i2,"labor")` (from M38) and `vm_cost_prod_livst(i2,"labor")` (from M70) on `equations.gms:24`. The doc attributes only the *crop* labor slice to M38, which is correct; it does not misattribute the livestock slice. ✓

---

## Deferred (not code-verifiable / not load-bearing — NOT edited)

- §7.2 / §13.2: `f38_historical_share_iso.csv` "range 0.2-0.8"; "FAO Value of Production 2005 benchmark"; "USDA factor cost shares" — the CSVs are not committed (only the `input/files` manifest is). Data-content claims unverifiable against this worktree.
- `p38_croparea_start(j,w,kcr)` is DECLARED at `sticky_feb18/declarations.gms:31` but never used anywhere in the realization (dead/vestigial declaration). The doc's §2.3 parameter table omits it. Omitting an unused declaration does not mislead a reader, so this is not flagged as a bug — noted only for awareness.
- §7.1 line 372: "loaded in `input.gms:18-32`" is slightly narrow — the f38 `$include` block actually runs to line 52 (`f38_hist_factor_costs_iso.csv`). The cited 18-32 range does cover the two fac_req loads the sentence is about, so it is imprecise rather than wrong-content. Borderline; deferred rather than flagged.
- §3.1 line 261 "(1/σ) − 1" definition of `s38_ces_elast_par`: the code uses `s38_ces_elast_par` directly (computed from `s38_ces_elast_subst` elsewhere); the algebraic relation is standard CES and the doc labels the math "conceptual". Not separately verified against the par-computation line; low risk, deferred.

---

## Method notes / grep hygiene

- Used `rg -n` for all probes; ran each probe standalone (no chaining that an exit-1 could truncate).
- Consumer search done BOTH as `vm_cost_prod_crop\(` (paren) and `vm_cost_prod_crop\.` (solution-attr) to catch presolve/postsolve `.l/.lo/.up/.m` reads (R33 near-miss class). Attr-form hits were all M38-internal.
- Positive controls run: `pm_interest` present in M12 (confirms grep works in that tree); `s38_depreciation_rate` present in `input.gms:13` (confirms grep works before concluding any absence).
- `pm_prod_init` absence in M30 confirmed by TWO methods: directory-scoped global `declarations.gms` grep (M17 only) + content read of the M17 populator line — satisfies the "confirm twice before calling a documented attribution wrong" bar.
