# Round 36 Doc Audit — module_71.md (Livestock Disaggregation, foragebased_jul23)

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_71.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (Merge PR #887)
**Default realization**: `foragebased_jul23` — CONFIRMED `config/default.cfg:2200` (`cfg$gms$disagg_lvst <- "foragebased_jul23"`)
**Realizations on disk**: `foragebased_aug18`, `foragebased_jul23`, `off` — CONFIRMED via `ls`

---

## Overall Verdict: MOSTLY ACCURATE (lower band)

### Accuracy Score: 7.5/10

The doc is largely faithful: all 6 equation formulas match code, all equation/declaration/preloop/nl_fix/nl_release citations verified line-exact, the entire alternative-realization (`foragebased_aug18`) comparison section is accurate, and the received/provided interface variable list is correct in membership. Bugs are confined to (1) two off-by-N count errors in the Summary Statistics, and (2) an imprecise producer attribution of `vm_prod_reg` to Module 70 (declared in Module 17).

---

## Verified Claims (correct)

### Default realization & structure
- Default `foragebased_jul23` — `config/default.cfg:2200`. ✓
- 6 equations, exactly 2 conditional (`$(s71_lp_fix=0)`, `$(s71_lp_fix=1)`), 4 unconditional — `equations.gms:14,21,34,44,55,66`. ✓

### Equation formulas (all 6 match code)
- **q71_feed_rum_liv** (doc:49) `vm_prod(j2,kforage) =g= v71_feed_forage + v71_feed_balanceflow` — `equations.gms:14-17`. ✓ Cite `equations.gms:14-17` ✓.
- **q71_feed_forage** (doc:74-76) — `equations.gms:21-24`. ✓ (doc simplifies the inner `sum((ct,cell(i2,j2)),...)` wrapper; acceptable). Cite ✓.
- **q71_feed_balanceflow_nlp** (doc:107-109) with division `vm_prod/vm_prod_reg` — `equations.gms:34-37`. ✓ Cite ✓. Active when `s71_lp_fix=0` ✓.
- **q71_feed_balanceflow_lp** (doc:133-135) — `equations.gms:44-46`. ✓ Cite ✓. Active when `s71_lp_fix=1` ✓.
- **q71_prod_mon_liv** (doc:157) — `equations.gms:55-59`. ✓ (doc omits `sum(cell(i2,j2),...)` around `vm_prod_reg`; acceptable simplification). Cite ✓.
- **q71_punishment_mon** (doc:188) — `equations.gms:66-69`. ✓ Cite ✓. Calibration note cite `equations.gms:71-72` ✓.

### Configuration scalars (defaults verified in code)
- `s71_lp_fix = 0` — `preloop.gms:12`. ✓
- `s71_scale_mon = 1.10` — `preloop.gms:13`. ✓
- `s71_punish_additional_mon = 15000` — `preloop.gms:14`. ✓
- `vm_prod_reg.lo(i,kli_rum)$(s71_lp_fix=0) = 10**(-6)` — `preloop.gms:17`. ✓ (doc:298 correctly shows the `$(s71_lp_fix=0)` condition).

### Sets
- `kli_rum = {livst_rum, livst_milk}` — `sets.gms:9-12`. ✓
- `kli_mon = {livst_pig, livst_chick, livst_egg}` — `sets.gms:14-17`. ✓
- `kforage = {pasture, foddr}` — `sets.gms:19-23`. ✓ Cite `sets.gms:9-17` and `sets.gms:19-23` ✓.

### Interface variables — RECEIVED (membership all correct; M71 directly reads all 7)
- `vm_feed_balanceflow` → Module 70: declared `70_livestock/fbask_jan16/declarations.gms:17` (`vm_feed_balanceflow(i,kap,kall)`). ✓ (doc specializes signature to `(i,kli_rum,kforage)` = M71's usage subset; acceptable).
- `im_feed_baskets` → Module 70: declared `70_livestock/fbask_jan16/declarations.gms:36` (`im_feed_baskets(t_all,i,kap,kall)`). ✓ doc:430 cites this exact line ✓.
- `pm_land_start` → Module 10: declared `10_land/landmatrix_dec18/declarations.gms`; read in `71.../preloop.gms:9`. ✓
- `pcm_land` → Module 10: declared `10_land/landmatrix_dec18/declarations.gms`; read in `71.../nl_fix.gms:13-14`. ✓
- `fm_feed_balanceflow` → Module 70 (input): `70_livestock/fbask_jan16/input.gms`; read in `71.../nl_fix.gms:10-12`. ✓
- `vm_prod`, `vm_prod_reg` → declared in **Module 17** (`17_production/flexreg_apr16/declarations.gms:9,10`); both are endogenous optimization variables M71 reads/constrains. The formal interface table (doc:258-259) says "Optimized in 71" / "Optimized (regional aggregate)" — defensible framing. (See BUG-3 for the conflicting prose attribution at doc:164.)

### Interface variable — PROVIDED (consumer set complete)
- `vm_costs_additional_mon(i)` → consumed ONLY by Module 11. Verified `rg -ln vm_costs_additional_mon -g "*.gms"`: only non-71 hit is `11_costs/default/equations.gms:40`. ✓ Enters `q11_cost_reg` (defines `v11_cost_reg(i2)`); `vm_cost_glo = sum(i2, v11_cost_reg(i2))` (`11_costs/default/equations.gms:10`). doc:354 telescopes these two equations into `vm_cost_glo = ... + Σ(i2) vm_costs_additional_mon(i2) + ...` — mathematically valid substitution, not flagged.

### Downstream coupling (doc:359-367)
- M31 reads `vm_prod(j2,"pasture")` — `31_past/endo_jun13/equations.gms:17`. ✓
- M30 defines `vm_prod(j2,kcr)` (incl. fodder crop) — `30_croparea/{simple,detail}_apr24/equations.gms:15`. ✓
- Disaggregation chain M70 (regional totals) → M71 (cellular constraints) → M31/M30 (land) is conceptually correct via shared `vm_prod`. ✓

### nl_fix / nl_release
- nl_fix operations (doc:317-322) — `nl_fix.gms:10-14`. ✓ (sign-conditioned `.lo/.up/.fx` + land-absence `.fx`). Cites `nl_fix.gms:10-14` and `nl_fix.gms:10-12` ✓.
- nl_release (doc:334-337) `.lo=-Inf`, `.up=Inf` — `nl_release.gms:10-11`. ✓

### Alternative realization foragebased_aug18 (doc:525-536) — ALL ACCURATE
- No nl_fix/nl_release files — CONFIRMED (`ls .../foragebased_aug18/nl_*.gms` → no such file). ✓
- 5 equations: `q71_feed_rum_liv`, `q71_balanceflow_constraint`, `q71_sum_rum_liv`, `q71_prod_mon_liv`, `q71_punishment_mon` — `foragebased_aug18/equations.gms:14,29,37,44,55`. ✓
- Multiplicative approach via `q71_balanceflow_constraint` + `v71_feed_balanceflow_share` — declared `foragebased_aug18/declarations.gms:15,20`. ✓
- `vm_prod_reg.lo = 10**(-6)` unconditional at `foragebased_aug18/preloop.gms:16` ✓; `+ 10**(-10)` epsilon in denominator at `foragebased_aug18/equations.gms:32` ✓.
- No `s71_lp_fix` toggle — CONFIRMED (`rg s71_lp_fix foragebased_aug18/*.gms` → exit 1, no matches). ✓

### Declaration-site citations (Quick Reference, doc:626-635) — all line-exact
- `v71_feed_forage` :9 ✓ | `v71_additional_mon` :10 ✓ | `vm_costs_additional_mon` :11 ✓ | `v71_feed_balanceflow` :15 ✓ | `i71_urban_area_share` :28 ✓ | `s71_lp_fix` :32 ✓ | `s71_scale_mon` :33 ✓ | `s71_punish_additional_mon` :34 ✓.

### Other citations
- `realization.gms:8-13` (two mechanisms) ✓ | `realization.gms:18` (monogastric limitation) ✓ | `realization.gms:19-20` (residue) ✓ | `realization.gms:20` (forage transport) ✓ | `realization.gms:13` (@robinson_mapping_2014) ✓ | `module.gms:10-13` ✓.

---

## Bugs Found

### BUG-1 — Wrong active-equation count ("4 active" should be "5 active")
- **Bug ID**: 71-B1
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift)
- **Trigger** (§1 Major): "Fabricated count for a set/parameter/realization list" / right concept, wrong number.
- **Claim in doc** (module_71.md:608): "**Equations**: 6 (4 active in NLP mode, 4 in LP mode - `q71_feed_balanceflow_nlp` and `q71_feed_balanceflow_lp` mutually exclusive)"
- **Reality in code**: 6 equations; only the nlp/lp pair is gated. The other 4 (`q71_feed_rum_liv`, `q71_feed_forage`, `q71_prod_mon_liv`, `q71_punishment_mon`) are UNCONDITIONAL. In each mode exactly one of the gated pair is active → **5 active per mode**, not 4.
- **File evidence**: `modules/71_disagg_lvst/foragebased_jul23/equations.gms:14,21,34,44,55,66` — only lines 34 (`$(s71_lp_fix=0)`) and 44 (`$(s71_lp_fix=1)`) carry `$`-conditions.
- **verify_cmd**: `rg -n "^q71_" .../foragebased_jul23/equations.gms` → `14:q71_feed_rum_liv(j2,kforage)`, `21:q71_feed_forage(j2)`, `34:q71_feed_balanceflow_nlp(j2)$(s71_lp_fix=0)`, `44:q71_feed_balanceflow_lp(i2)$(s71_lp_fix=1)`, `55:q71_prod_mon_liv(j2,kli_mon)`, `66:q71_punishment_mon(i2)` — 4 unconditional + 1 gated = 5 active per mode.
- **confirmed**: true
- **Proposed fix**: Replace doc:608 with: "**Equations**: 6 (5 active in NLP mode, 5 in LP mode - `q71_feed_balanceflow_nlp` and `q71_feed_balanceflow_lp` are mutually exclusive; the other 4 equations are unconditional)".

### BUG-2 — Wrong code-file count (7) and file list omits scaling.gms
- **Bug ID**: 71-B2
- **Severity**: Minor
- **Class**: 6 (Hardcoded counts drift)
- **Trigger** (§1 Minor): wrong detail a careful reader wouldn't act on; (the parenthetical list itself contradicts the count, signalling it's metadata).
- **Claim in doc** (module_71.md:615): "**Code files**: 7 (realization, sets, declarations, equations, preloop, postsolve, nl_fix, nl_release)"
- **Reality in code**: The `foragebased_jul23/` directory contains **9** `.gms` files: declarations, equations, nl_fix, nl_release, postsolve, preloop, realization, **scaling**, sets. The doc's count "7" disagrees even with its own list (8 names), and the list omits `scaling.gms` (a real phase file `$include`-d at `realization.gms:27`).
- **File evidence**: `ls .../foragebased_jul23/*.gms` → 9 files; `scaling.gms` present (content: commented `q71_*.scale` factors); `realization.gms:27` `$Ifi "%phase%" == "scaling" $include ".../scaling.gms"`.
- **verify_cmd**: `ls -1 .../foragebased_jul23/*.gms | wc -l` → `9`; full list includes `scaling.gms`.
- **confirmed**: true
- **Proposed fix**: Replace doc:615 with: "**Code files**: 9 in `foragebased_jul23/` (realization, sets, declarations, equations, scaling, preloop, postsolve, nl_fix, nl_release; `module.gms` is the parent dispatcher)".

### BUG-3 — vm_prod_reg attributed "from Module 70" (declared in Module 17)
- **Bug ID**: 71-B3
- **Severity**: Minor
- **Class**: 15 (latent doc error — producer attribution) / borderline Major-prone (R20 producer/consumer-set class), downgraded per tie-breaker.
- **Trigger**: producer/consumer attribution (MANDATE 17 / 13). Tie-breaker pulls to Minor because: (a) variable name is correct, (b) the formal interface table at doc:258-259 already gives the defensible "Optimized (regional aggregate)" framing, (c) M70 IS the economic driver of the livestock production level even though M17 declares the variable, and (d) a user would not edit a wrong file (they'd grep for the declaration and land in M17).
- **Claim in doc** (module_71.md:164): "`vm_prod_reg(i,kli_mon)`: Regional monogastric production from Module 70 (mio. tDM/yr)". (Also implied at doc:363 "Module 70 determines regional livestock production totals" — defensible, since M70's demand/feed constraints drive the level.)
- **Reality in code**: `vm_prod` and `vm_prod_reg` are DECLARED in Module 17 (`17_production/flexreg_apr16/declarations.gms:9,10`), and `vm_prod_reg` is DEFINED by `q17_prod_reg`: `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))` (`17_production/flexreg_apr16/equations.gms:11`). Module 70 is a CONSUMER of `vm_prod_reg` (e.g., `vm_dem_feed(i2,kap,kall) =g= vm_prod_reg(i2,kap)`, `70_livestock/fbask_jan16/equations.gms:18`), not its producer. Module 17 is the only declaring module; consumers include M16, M18, M20, M21, M38, M50, M70, M71.
- **File evidence**: `17_production/flexreg_apr16/declarations.gms:9-10`; `17_production/flexreg_apr16/equations.gms:11`; `70_livestock/fbask_jan16/equations.gms:18`.
- **verify_cmd**: `rg -ln "vm_prod_reg" -g declarations.gms modules/` → only `17_production/flexreg_apr16/declarations.gms`; `rg -n "vm_prod_reg" .../17_production/flexreg_apr16/equations.gms:11` → `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))`.
- **confirmed**: true
- **Proposed fix**: Edit doc:164 to: "`vm_prod_reg(i,kli_mon)`: Regional monogastric production (declared in Module 17 as `sum(cell, vm_prod)`; its level is driven by Module 70's demand/feed constraints) (mio. tDM/yr)". Optionally add a one-line note at doc:259/272 that `vm_prod`/`vm_prod_reg` are owned by Module 17 (production), not Module 71 or 70.

---

## Missing Nuances (not bugs)

- doc:53 glosses `livst_rum` as "Beef cattle" (doc:227) / "livst_rum = beef" (doc:79). `livst_rum` is ruminant MEAT (cattle + sheep + goats), not beef-only (MANDATE 12 generalization). Pervasive MAgPIE-doc convention; all formula-facing references use the exact set name `kli_rum`/`livst_rum`. Not flagged — borderline Informational, no code-facing impact.
- doc:75/261/631 write `im_feed_baskets(...,kli,...)` and `vm_feed_balanceflow(i,kli_rum,kforage)`; full declarations use `kap`/`kall`. The doc shows M71's usage subset, which matches the equation indices. Acceptable simplification.
- doc:282 simplifies the nested `sum(cell(i,j),sum(cell2(i,j3),...))` normalization to `Σ(cell(i,j3))`. Captures intent; not flagged.

---

## R33 Pre-run advisory — RESOLVED
Advisory: "Verify M71's vm_prod_reg / livestock-product consumer sets and the M70<->M71 relationship; verify default realization; both grep forms + positive control."
- **Default realization**: `foragebased_jul23` confirmed (`config/default.cfg:2200`). ✓
- **M70↔M71 relationship**: doc's framing (M70 sets regional totals → M71 disaggregates to cells) is conceptually correct; refined by BUG-3 (the *variable* `vm_prod_reg` is declared in M17, M70 is a peer consumer/driver).
- **vm_prod_reg consumer set**: enumerated from code (M16, M17, M18, M20, M21, M38, M50, M70, M71) via `rg -ln "vm_prod_reg" -g "*.gms"` — the doc makes no phantom downstream consumer claim for it.
- **vm_costs_additional_mon consumer set**: ONLY Module 11 (`11_costs/default/equations.gms:40`), confirmed with positive control (the grep returned the known M11 hit and the M71 self-references; no other module). No phantom, no omission.
- Both grep forms used; `vm_prod.`/`vm_prod_reg.` attribute reads checked in M30/M31 (none — they use `vm_prod(`).

---

## Summary
3 bugs: 1 Major (active-equation count 4→5, doc:608), 2 Minor (code-file count 7→9 + scaling.gms omitted, doc:615; vm_prod_reg "from Module 70" producer mis-attribution, doc:164 — declared in M17). All formulas, all citations, and the full foragebased_aug18 comparison verified correct. No phantom/omitted consumers; default realization correct. Score 7.5/10.
