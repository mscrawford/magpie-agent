# Adversarial Verification — module_37 confirmed bugs (R37)

Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only). Default cfg: `/tmp/magpie_develop_ro/config/default.cfg`.
Verifier stance: skeptical; default to REFUTED/CORRECTED unless code reproduces the auditor's claim.

Module 37 realizations on develop: `off` (DEFAULT), `exo`. (Doc line 1262 oddly says "exogenous (exo) or climate-driven (exo)" — a separate cosmetic glitch, not in scope.)
Relevant cfg defaults: `cfg$gms$labor_prod <- "off"` (default.cfg:1214); `cfg$gms$factor_costs <- "sticky_feb18"` (default.cfg:1235).

---

## module_37-B1 — "Depends on: Module 45 (climate)" (doc:1252)

**class_is_consumer_set = true** — it asserts module 37 depends-on (consumes from) module 45. Dependency-set claim.

**Verdict: UPHELD** (with one scoping refinement on the proposed fix; see below).

### Evidence

Search for any `45` token in module 37 GAMS (second method = the foreign-interface grep below; positive control = own `pm_labor_prod` lines, which DO appear, proving the search reaches these files):

```
$ rg -n '45' /tmp/magpie_develop_ro/modules/37_labor_prod/
NO MATCH for 45
```

Search for ANY interface var (`vm_`/`im_`/`pm_`) in module 37 — positive control built in (own `pm_labor_prod` must appear):

```
$ rg -n 'vm_|im_|pm_' /tmp/magpie_develop_ro/modules/37_labor_prod/
off/preloop.gms:8:pm_labor_prod(t,j) = 1;
off/declarations.gms:9: pm_labor_prod(t,j) labor productivity factor (1)
exo/preloop.gms:8:pm_labor_prod(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%",...);
exo/preloop.gms:10:$if ... nocc ... pm_labor_prod(t,j) = pm_labor_prod("y1995",j);
exo/preloop.gms:11:$if ... nocc_hist ... pm_labor_prod(t,j)$(...) = pm_labor_prod(t,j)$(...);
exo/declarations.gms:9: pm_labor_prod(t,j) labor productivity factor (1)
```

The ONLY interface object referenced is the module's OWN `pm_labor_prod`. No foreign `vm_*/im_*/pm_*` (no `pm_*` from M45 or anything else), no `45` token. Positive control passes (own param appears), so the absence of `45` and foreign interfaces is real, not a broken search. Attribute-form (`pm_labor_prod.`) grep returns NO MATCH everywhere — irrelevant for M37's own write but confirms M37 itself does no solution-level read.

Climate signal is pre-baked offline and loaded from a `.cs3`:

```
$ rg -n 'cs3|labourprod|f37' /tmp/magpie_develop_ro/modules/37_labor_prod/exo/input.gms
18:table f37_labor_prod(t_all,j,rcp37,metric37,intensity37,uncertainty37) labor productivity factor (1)
20:$include "./modules/37_labor_prod/exo/input/f37_labourprodimpact.cs3"
```

Filename in the proposed fix (`f37_labourprodimpact.cs3`) is exactly correct (exo/input.gms:20).

Doc self-contradiction confirmed (auditor's claim that 10.2 + summary say "Receives FROM: NONE"):

```
module_37.md:503  #### 10.2 Receives FROM (Upstream Modules)
module_37.md:505  **NONE** - Module 37 is a pure source module
module_37.md:1030 - **Receives from**: NONE (pure source, external ESM data)
```

So line 1252 ("Depends on: Module 45") directly contradicts the doc's own 10.2 (line 505) and 11.4 summary (line 1030). The dependency-set claim at 1252 is WRONG; the corrected set is "Depends on: NONE." UPHELD.

### Scoping refinement to the proposed fix (CORRECTED only on the link, not the core)

The core deletion of the "Depends on: Module 45" bullet is correct and should be applied verbatim with the NONE replacement.

The proposed fix also says to "remove/re-label the 'Climate data (Module 45) -> modules/module_45.md' link at line 1323." That link sits under a generic **Links** block (1320-1323) and is a *conceptual data-provenance* pointer (the heat-stress signal ultimately derives from climate/ESM data), NOT a GAMS runtime-dependency assertion. Hard-deleting it is defensible, but the more conservative and equally-correct action is to RE-LABEL it so a reader does not infer a runtime coupling, e.g. `Climate/ESM provenance of the offline heat-stress signal (conceptual, not a runtime dependency) -> modules/module_45.md`. Either action removes the false-coupling implication. I record this as the precise instruction so the fixer does not silently delete a legitimate provenance cross-reference. The dependency-set verdict itself is UPHELD.

---

## module_37-B2 — default-config caveat: pm_labor_prod cost-consumed ONLY by sticky_labor (doc:402)

**class_is_consumer_set = true** — the finding's load-bearing factual core is a consumer-set claim: "pm_labor_prod is consumed in a cost equation ONLY by the non-default sticky_labor realization; sticky_feb18 / per_ton_fao_may22 abort if pm_labor_prod != 1." (The surrounding caveat is class-4 behavioral, but it stands or falls on this consumer set, so I verify it as one.)

**Verdict: UPHELD.**

### Evidence

All `pm_labor_prod(` occurrences across all modules (equation form):

```
$ rg -n 'pm_labor_prod\(' /tmp/magpie_develop_ro/modules/
37_labor_prod/off/preloop.gms:8       pm_labor_prod(t,j) = 1;                  # producer (off, DEFAULT)
37_labor_prod/exo/preloop.gms:8,10,11                                          # producer (exo)
38_factor_costs/sticky_labor/equations.gms:22   ... pm_labor_prod(ct,j2) * ... # REAL cost-eqn consumer (CES)
38_factor_costs/sticky_labor/presolve.gms:61    ... (pm_labor_prod(t,j) * ...) # sticky_labor presolve init
38_factor_costs/sticky_labor/nl_relax.gms:11    ... pm_labor_prod(t,j) * ...   # sticky_labor relaxation init
38_factor_costs/per_ton_fao_may22/presolve.gms:8  if(smax/smin pm_labor_prod<>1, abort ...)  # ABORT guard only
38_factor_costs/sticky_feb18/presolve.gms:8       if(smax/smin pm_labor_prod<>1, abort ...)  # ABORT guard only
```

Attribute form — confirms no solution-level (`.l/.lo/.up/.fx/.m`) consumer is being missed:

```
$ rg -n 'pm_labor_prod\.' /tmp/magpie_develop_ro/modules/
NO MATCH for pm_labor_prod.
```

Per-realization confinement (positive control = the matches above prove rg reaches each dir):

```
$ rg -n 'pm_labor_prod' /tmp/magpie_develop_ro/modules/38_factor_costs/sticky_feb18/
sticky_feb18/presolve.gms:8: if (smax(j, pm_labor_prod(t,j)) <> 1 OR smin(j, pm_labor_prod(t,j)) <> 1,
$ rg -n 'pm_labor_prod' /tmp/magpie_develop_ro/modules/38_factor_costs/per_ton_fao_may22/
per_ton_fao_may22/presolve.gms:8: if (smax(j, pm_labor_prod(t,j)) <> 1 OR smin(j, pm_labor_prod(t,j)) <> 1,
```

Abort text (sticky_feb18/presolve.gms:8-10, identical in per_ton_fao_may22/presolve.gms:8-10):

```
if (smax(j, pm_labor_prod(t,j)) <> 1 OR smin(j, pm_labor_prod(t,j)) <> 1,
  abort "This factor cost realization cannot handle labor productivities != 1"
);
```

CES multiply consumer (sticky_labor/equations.gms:22) — confirms MULTIPLY, not divide:

```
(1 - i38_ces_shr(j2,kcr))*(sum(ct, pm_labor_prod(ct,j2) * sum(cell(i2,j2), pm_productivity_gain_from_wages(ct,i2))) * v38_laborhours_need(j2,kcr))**(-s38_ces_elast_par)
```

default.cfg confirms both the comment and the defaults:

```
default.cfg:1209-1210  "# * The labour productivity factor is currently only considered in the sticky_labor / # * realization of the [38_factor_costs] module."
default.cfg:1214       cfg$gms$labor_prod <- "off"            # default = off
default.cfg:1235       cfg$gms$factor_costs <- "sticky_feb18" # default = "sticky_feb18"
```

Consequence chain is real: under DEFAULT `factor_costs=sticky_feb18`, setting `labor_prod=exo` makes `pm_labor_prod != 1`, which trips the abort at sticky_feb18/presolve.gms:8-10 -> run aborts. The caveat (must also set `factor_costs <- "sticky_labor"`) is code-true. The consumer set "cost-equation consumer = {sticky_labor} only" is exactly correct. UPHELD.

Minor wording note for the fixer (does not change verdict): the default `labor_prod` is `off` (default.cfg:1214), so out-of-the-box `pm_labor_prod=1` and there is no abort and no cost effect. The abort only bites when a user deliberately switches `labor_prod` to `exo` while leaving `factor_costs` at its default. The proposed caveat already states "With default settings pm_labor_prod=1 and has no cost effect," which is consistent — keep that sentence.

---

## module_37-B3 — hallucinated `vm_labor_costs`; division vs CES-multiply (doc:404-409)

**class_is_consumer_set = true** — the bug itself is a hallucinated-variable (class 2), but the auditor's PROPOSED FIX makes two consumer/producer-set assertions I must independently confirm: (a) "real consumer is non-default sticky_labor," (b) "crop factor costs are vm_cost_prod_crop(i,factors)." Verifying as consumer-set.

**Verdict: UPHELD.**

### Evidence

`vm_labor_costs` anywhere in the repo (whole-tree, two-method: rg below + the `rg -n 'vm_'` M37 grep in B1 which never shows it):

```
$ rg -n 'vm_labor_costs' /tmp/magpie_develop_ro/
NO MATCH for vm_labor_costs (CONFIRMS ABSENT)
```

Positive control that the search works and that the auditor's replacement var IS real:

```
$ rg -n 'vm_cost_prod_crop' /tmp/magpie_develop_ro/modules/38_factor_costs/
sticky_labor/declarations.gms:18: vm_cost_prod_crop(i,factors)  Regional factor costs of capital and labor for crop production (mio USD17MER per yr)
sticky_labor/equations.gms:39: q38_cost_prod_labor(i2).. vm_cost_prod_crop(i2,"labor") =e= ...
sticky_labor/equations.gms:46: q38_cost_prod_capital(i2).. vm_cost_prod_crop(i2,"capital")=e= ...
per_ton_fao_may22/equations.gms:11,16; per_ton_fao_may22/declarations.gms:14
sticky_feb18/... (postsolve/scaling/declarations)
```

So `vm_labor_costs` is a phantom (absent under a working search that finds the real sibling `vm_cost_prod_crop`). The real interface variable is `vm_cost_prod_crop(i,factors)` with `factors` member `"labor"` (sticky_labor/equations.gms:39) — exactly the auditor's replacement. (a) confirmed: the only cost-equation consumer of `pm_labor_prod` is sticky_labor (see B2 grep). (b) confirmed: crop factor costs = `vm_cost_prod_crop(i,factors)`.

Mechanism direction: B1/B2 CES grep (sticky_labor/equations.gms:22) shows `pm_labor_prod` MULTIPLIES the labor term inside the CES aggregator, not a division of a "baseline_labor_costs / sum(pm_labor_prod)". So the doc's formula (line 408) is wrong in both the variable name AND the operation; the auditor's conceptual rewrite (multiply in CES, no vm_labor_costs, costs = vm_cost_prod_crop) is code-true. UPHELD.

Note: the doc block is labeled "(conceptual)" (line 404), so per MANDATE 5 the severity downgrade to Minor is appropriate — the fix is still correct and worth applying.

---

## Cross-bug coherence check

The three fixes are mutually consistent and collectively make module_37.md internally consistent:
- B1 removes the false M45 runtime dependency (aligning 1252 with the already-correct 505 + 1030).
- B2 + B3 both correctly localize the real `pm_labor_prod` cost consumer to the non-default `sticky_labor` realization (equations.gms:22) and surface the sticky_feb18/per_ton abort guard.
- B3 replaces the phantom `vm_labor_costs` with the verified `vm_cost_prod_crop(i,factors)`.

No fix introduces a new error. One refinement recorded (B1 link re-label vs hard-delete).
