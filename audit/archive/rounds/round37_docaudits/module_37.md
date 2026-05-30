# Doc Audit: module_37.md (Labor Productivity / Heat Stress)

**Auditor**: Opus adversarial doc auditor (Round 37 doc-audits)
**Target doc**: `magpie-agent/modules/module_37.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Date**: 2026-05-30

---

## Overall Verdict: MOSTLY ACCURATE (lower band)

The doc's core code-checkable spine is **correct**: default realization (`off`), the two realizations and their mechanisms, the `pm_labor_prod(t,j)` interface parameter, the c37 scenario/metric/intensity/uncertainty switches and their defaults, the GAMS sets, and virtually all file:line citations into `37_labor_prod/`. The bugs are in the **downstream-coupling story** (how `pm_labor_prod` feeds Module 38) and one **self-contradicting phantom upstream dependency** (Module 45).

**Accuracy score: 6/10** (1 Major dependency-set bug + 1 Major missing-default-caveat + 1 Minor invented-var = 2+2+1 = 5; 10-5 = 5; rounded to 6 because both Majors are partially self-mitigated within the doc / hedged — see per-bug notes; tie-breaker pulls toward the less-severe edge).

---

## Verified Claims (CORRECT)

- **Default realization `off`**: `config/default.cfg:1214` → `cfg$gms$labor_prod <- "off"`. CONFIRMED (doc lines 6, 14-15, 354).
- **Two realizations only**: `ls /tmp/magpie_develop_ro/modules/37_labor_prod/` → `exo`, `off`. CONFIRMED (doc line 323).
- **c37 switch defaults**: `input.gms:8,13-16` → `c37_labor_prod_scenario=cc`, `c37_labor_rcp=rcp119`, `c37_labor_metric=ISO`, `c37_labor_intensity=400W`, `c37_labor_uncertainty=ensmean`. All CONFIRMED, and mirrored in `default.cfg:1218-1224`. (doc §3.1, §4, §5, §6, §7.1).
- **exo mechanism `preloop.gms:8`**: `pm_labor_prod(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%",...)`. CONFIRMED (doc lines 331-332, 399).
- **off mechanism `off/preloop.gms:8`**: `pm_labor_prod(t,j) = 1;`. CONFIRMED (doc lines 360, 363, 400).
- **nocc / nocc_hist switches `preloop.gms:10-11`**: CONFIRMED (doc §7.1 line 337-340, §11 item 5).
- **`m_fillmissingyears` `input.gms:23`**: CONFIRMED (doc lines 462, 527).
- **Historical constraint `input.gms:25-26`** (pre-`sm_fix_cc` collapse to rcp119/ISO/400W/ensmean): CONFIRMED (doc lines 469-470, 531).
- **Sets `sets.gms:9-19`**: rcp37 {rcp119,rcp585}, metric37 {ISO,HOTHAPS}, intensity37 {300W,400W}, uncertainty37 {enslower,ensmean,ensupper}. CONFIRMED. `sets.gms:10` = `/ rcp119, rcp585 /` (doc §12 item 2 line 567). CONFIRMED.
- **`pm_labor_prod(t,j)` declared `declarations.gms:9`**, units "labor productivity factor (1)". CONFIRMED (doc lines 388, 548). It is the SOLE interface parameter of M37 (verified both realizations' declarations.gms). (doc §8 "1 interface parameter").
- **Sole consumer = Module 38**: `rg pm_labor_prod` across all modules → only `37_labor_prod/*` and `38_factor_costs/*`. Core has zero (exit 1). CONFIRMED that M38 is the only consumer module (doc §8.1 "Used By", §10.1, §16).
- **M70 (livestock) does NOT use `pm_labor_prod`**: `rg pm_labor_prod modules/70_livestock/` → exit 1 (absent), positive control passed. CONFIRMED (doc §12 item 8 line 596).
- **exo Code Size 104 lines / 5 .gms files**; **off 36 lines / 3 .gms files**: `wc -l` confirms 104 and 36. CONFIRMED (doc lines 352, 370). ("140 across 8 files" header line 8 = exo+off summed, excluding the 21-line dispatcher module.gms; internally consistent, not flagged.)
- **Data table dimensions `(t_all,j,rcp37,metric37,intensity37,uncertainty37)`**: matches `input.gms:18`. CONFIRMED (doc line 428).
- **§17 realization.gms:8-12 citation**: lines 8-12 are the @description (LAMACLIMA / Orlov 2021). Reasonable. OK.

---

## Bugs Found

### Bug 1 — Phantom upstream dependency on Module 45 (self-contradicting)

- **Severity**: Major
- **Class**: 15 (latent doc error — wrong dependency set) / R20-anchor-adjacent
- **Trigger (§1 Major)**: "File:line citation drift to adjacent but different content" does not fit; the matching Major trigger is the dependency-set error described in the R20 anchor logic (wrong producer/consumer/dependency set) — assessed Major rather than Critical because the doc *itself* states the opposite elsewhere (self-contradiction limits the harm) and the claim is hedged "(optional, depends on realization)".
- **Doc line**: module_37.md:1252 (and link at :1323)
- **Claim in doc**: "**Depends on**: Module 45 (climate): Climate data for heat stress calculations (optional, depends on realization)"
- **Reality in code**: Module 37 reads NOTHING from Module 45. `rg -n "45" /tmp/magpie_develop_ro/modules/37_labor_prod/ --glob "*.gms"` → exit 1 (no match). Positive control: `sm_fix_cc` IS found in the same dir (search works). The exo realization's climate signal is pre-baked into the input file `f37_labourprodimpact.cs3` (produced upstream by LAMACLIMA preprocessing), not read from MAgPIE's runtime Module 45. The doc's OWN §10.2 (line 505-508) and §16 (line 1030) correctly state "Receives FROM: NONE — pure source module."
- **File evidence**: absence in `/tmp/magpie_develop_ro/modules/37_labor_prod/*.gms` (no `45`, no `vm_/im_/pm_` from other modules); only own `pm_labor_prod`, `f37_labor_prod`, and core `sm_fix_cc`.
- **verify_cmd**: `rg -n "45" /tmp/magpie_develop_ro/modules/37_labor_prod/ --glob "*.gms"` → EXIT 1 (absent); positive control `rg -n "sm_fix_cc" ...` → hits at preloop.gms:9,11 + input.gms:11,24,25,26 (EXIT 0).
- **Proposed fix**: In the "Dependency Chains" block (module_37.md:1251-1252), DELETE the "Depends on: Module 45 (climate)..." bullet and replace with: "**Depends on**: NONE (pure source module). The exogenous climate signal is pre-computed offline (LAMACLIMA) and loaded from `f37_labourprodimpact.cs3`; Module 37 reads no runtime variable from any other module, including Module 45." Also remove the "Climate data (Module 45) → `modules/module_45.md`" link at line 1323 (or re-label it as "upstream data origin, not a GAMS dependency").

### Bug 2 — Missing default-state caveat: default factor-costs realization ABORTS when pm_labor_prod != 1

- **Severity**: Major
- **Class**: 4 (conceptual/behavioral mischaracterization) + missing-default-caveat
- **Trigger (§1 Major)**: "Missing default-state caveat (mechanism described as if always active when it's OFF by default)."
- **Doc line**: module_37.md:402 (and the whole impact-chain/testing narrative: §8.1 line 402, §10.1 lines 486-501, §13.1 lines 613-640, §13.5 lines 729-764)
- **Claim in doc**: "**Used By**: Module 38 (Factor Costs)" (line 402) with an elaborate impact chain (Climate → pm_labor_prod ↓ → Labor costs ↑ → ...) and R recipes comparing `exo` vs `off` runs (§13.1/§13.5) — all presented as if they work under the default configuration.
- **Reality in code**: `pm_labor_prod` is consumed in a cost EQUATION only by the **non-default** `sticky_labor` realization of M38. The DEFAULT M38 realization is `sticky_feb18` (`config/default.cfg:1235`), which — together with `per_ton_fao_may22` — **aborts** the model if `pm_labor_prod != 1`: `modules/38_factor_costs/sticky_feb18/presolve.gms:8-10` → `if (smax(j,pm_labor_prod(t,j)) <> 1 OR smin(...) <> 1, abort "This factor cost realization cannot handle labor productivities != 1");`. `config/default.cfg:1210` documents this: "The labour productivity factor is currently only considered in the sticky_labor [realization]." So under default config you CANNOT run `labor_prod=exo` — the model aborts. The doc never mentions `sticky_labor`, `sticky_feb18`, or the abort (`rg "sticky_labor|abort|sticky_feb18" module_37.md` → exit 1).
- **File evidence**: `modules/38_factor_costs/sticky_feb18/presolve.gms:8-10` (abort); `modules/38_factor_costs/per_ton_fao_may22/presolve.gms:8-10` (abort); `modules/38_factor_costs/sticky_labor/equations.gms:22` (the only real consumer — CES: `(1-i38_ces_shr)*(sum(ct, pm_labor_prod(ct,j2) * ...) * v38_laborhours_need)**(-s38_ces_elast_par)`); `config/default.cfg:1235` (`factor_costs <- "sticky_feb18"`), `:1210` (note).
- **verify_cmd**: `rg -n "pm_labor_prod" /tmp/magpie_develop_ro/modules/38_factor_costs/ --glob "*.gms"` → hits in sticky_labor (nl_relax:11, equations:13,22, presolve:61), per_ton_fao_may22/presolve:8, sticky_feb18/presolve:8; `sed -n '8,11p' .../sticky_feb18/presolve.gms` → the abort; `rg 'cfg\$gms\$factor_costs' config/default.cfg` → `sticky_feb18` default.
- **Proposed fix**: Add a prominent caveat near §8.1 (after line 402) and at the head of §13.1/§13.5, e.g.: "⚠️ **Default-config caveat**: `pm_labor_prod` is only consumed in the cost equation by Module 38's **non-default** `sticky_labor` realization (`38_factor_costs/sticky_labor/equations.gms:22`). The DEFAULT factor-costs realization `sticky_feb18` (and `per_ton_fao_may22`) **abort** the run if `pm_labor_prod != 1` (`38_factor_costs/sticky_feb18/presolve.gms:8-10`). Therefore, to run the `exo` heat-stress scenario you MUST also set `cfg$gms$factor_costs <- 'sticky_labor'`; otherwise the model aborts. With default settings (`labor_prod='off'`, `factor_costs='sticky_feb18'`), `pm_labor_prod=1` everywhere and has no cost effect." Update the §13 R recipes to note `factor_costs='sticky_labor'` is required.

### Bug 3 — Invented variable `vm_labor_costs` and fabricated application formula (conceptually labeled)

- **Severity**: Minor
- **Class**: 2 (hallucinated variable name) — downgraded by the explicit "(conceptual)" label per MANDATE 5
- **Trigger**: would be "Invented variable name presented as authoritative" (Critical), but the block is explicitly headed "(conceptual)", so it is NOT presented as authoritative code → tie-breaker + MANDATE-5 hedge → Minor.
- **Doc line**: module_37.md:405-409
- **Claim in doc**: a GAMS-styled block "**Application in Module 38** (conceptual): ... `vm_labor_costs(i) = baseline_labor_costs(i) / sum(cell(i,j), pm_labor_prod(t,j))`"
- **Reality in code**: No variable `vm_labor_costs` exists anywhere in MAgPIE. The real M38 mechanism is a CES production function where labor efficiency is **multiplied** by `pm_labor_prod` (not a simple division of a labor-cost variable): `38_factor_costs/sticky_labor/equations.gms:22`. The crop factor-cost interface variable is `vm_cost_prod_crop(i,factors)`, not `vm_labor_costs`.
- **File evidence**: `rg -n "vm_labor_costs" /tmp/magpie_develop_ro/modules/ --glob "*.gms"` → EXIT 1 (absent). Positive control: `rg -n "vm_cost_prod_crop\b" .../38_factor_costs/*/declarations.gms` → 3 hits (search works). Real eq: `sticky_labor/equations.gms:22`.
- **verify_cmd**: `rg -n "vm_labor_costs" /tmp/magpie_develop_ro/modules/ --glob "*.gms"` → EXIT 1; positive control `vm_cost_prod_crop` → sticky_feb18/declarations.gms:16, sticky_labor/declarations.gms:18, per_ton_fao_may22/declarations.gms:14.
- **Proposed fix**: Replace the conceptual block (lines 404-409) with a code-true conceptual note that does not invent a variable name: "**Application in Module 38** (conceptual; real consumer is the non-default `sticky_labor` realization): labor efficiency in the CES factor-cost function is *multiplied* by `pm_labor_prod` — higher productivity raises effective labor input, lowering the labor hours (`v38_laborhours_need`) needed per unit output, hence lower cost. See `38_factor_costs/sticky_labor/equations.gms:22`. (There is no `vm_labor_costs` variable; crop factor costs are `vm_cost_prod_crop(i,factors)`.)"

---

## Deferred (not code-verifiable from the worktree; NOT flagged as bugs)

- The `.cs3` data file contents/size (doc §9: "~240,000 data points", "1995-2150", "0.5° grid", "200 clusters") — the file is not checked into develop (only a 64-byte `files` placeholder; data arrives via input.tgz). Dimensions that ARE checkable (the 4 scenario sets) match `sets.gms`. Point counts / temporal extent / spatial resolution are preprocessing facts → route to preproc-agent; not auditable here.
- WBGT formula (doc §2.2 line 64) and the ISO/HOTHAPS rest-break tables (§3) — these are labeled "(simplified)"/"(conceptual)" domain descriptions of the external LAMACLIMA methodology, not MAgPIE code. Not code-checkable.
- Quantitative productivity ranges by region/RCP (§5, §6, §13, §14) — illustrative numbers, not in the GAMS code; the actual values live in the unreadable `.cs3`. Not flagged.
- Literature/DOIs (§15) — bibliographic, out of scope for code audit.
- "200 MAgPIE cells" — correct for the DEFAULT `c200` cellular input (`default.cfg:26`); the j-set size is input-dependent in general. Treated as correct, not flagged.

---

## Pre-run advisory verification (explicitly requested)

Advisory: "Verify default realization. Verify labor-productivity parameters/equations and how they feed M38 factor costs (pm_labor_prod or similar); consumer/producer sets. Both grep forms + positive control."

- **Default realization**: CONFIRMED `off` (`default.cfg:1214`). Doc correct.
- **Parameter**: CONFIRMED sole interface = `pm_labor_prod(t,j)` (declarations.gms:9, both realizations). M37 has NO equations (it's a preloop data provider) — doc's "no equations" claim correct.
- **Feed into M38**: CONFIRMED, and this is where the doc is **incomplete** → Bug 2 (only non-default `sticky_labor` uses it in a cost equation; default `sticky_feb18` + `per_ton_fao_may22` ABORT on `!= 1`). Both grep forms used (`pm_labor_prod(` covered by the bare token search; also checked `pm_labor_prod.` attribute form — none present, M37 is a parameter not a variable, so no `.l/.lo/.up` reads exist). Positive controls run (`vm_cost_prod_crop`, `sm_fix_cc`).
- **Consumer/producer set**: producer = M37 only; consumer = M38 only. Doc correct at module level; Bug 1 (phantom M45 upstream dependency) and Bug 2 (realization specificity) are the refinements.

Advisory: **CONFIRMED with refinements** (the M38 feed is real but realization-gated and default-aborting — a material caveat the doc omits).
