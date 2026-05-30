# Round 35 Adversarial Verification — module_31.md

Verifier: highest-capability model, adversarial (default-skeptical) consumer/populator/dependency-set audit.
Ground truth: /tmp/magpie_develop_ro (develop worktree). All probes run as standalone commands; both `NAME(` and `NAME.` forms; positive controls run.

---

## Classification

| Bug | class_is_consumer_set | Why |
|-----|----------------------|-----|
| R35-31-1 | false | Realization status (deprecated vs functional + not_used.txt convention). No claim about which modules consume/populate/depend-on an interface variable. |
| R35-31-2 | **true** | Asserts dependency direction / "Provides To" set membership (M31→M22). |
| R35-31-3 | false | Set-member-label claim (stockType members). Not a consumer/producer set. |
| R35-31-4 | **true** | Producer/populator/consumer set for vm_carbon_stock (DECLARED-by / POPULATED-by / READ-by). |

Only R35-31-2 and R35-31-4 require independent set re-derivation. R35-31-1 and R35-31-3 pass to the fixer unchanged (NOT_CONSUMER_SET), but I code-checked them anyway to ensure no wrong fix slips through; both auditor claims are factually correct.

---

## R35-31-2 — UPHELD

**Claim:** M31 provides NOTHING to M22; relationship is one-directional M22→M31. Doc line 527 wrongly lists "Module 22 (Conservation)" under "Provides To".

**Independent re-derivation — M31 outputs in modules/22_*** (both forms):
```
$ rg -n 'vm_cost_prod_past' /tmp/magpie_develop_ro/modules/22_*/        -> (no match)
$ rg -n 'vm_cost_prod_past\.' /tmp/magpie_develop_ro/modules/22_*/      -> (no match)
$ rg -n 'vm_bv\(' /tmp/magpie_develop_ro/modules/22_*/                  -> (no match)
$ rg -n 'vm_bv\.' /tmp/magpie_develop_ro/modules/22_*/                  -> (no match)
$ rg -n 'vm_carbon_stock\(' /tmp/magpie_develop_ro/modules/22_*/        -> (no match)
$ rg -n 'vm_carbon_stock\.' /tmp/magpie_develop_ro/modules/22_*/        -> (no match)
$ rg -n 'vm_prod\(' /tmp/magpie_develop_ro/modules/22_*/                -> (no match)
```

**POSITIVE CONTROL (proves grep works in modules/22_*):**
```
$ rg -n 'pm_land_conservation' /tmp/magpie_develop_ro/modules/22_*/
  area_based_apr22/presolve_ini.gms:54,55,66,71,...  (many hits)
  area_based_apr22/declarations.gms:15  (DECLARED here)
  module.gms:17 "transferred to the other land modules via the interface pm_land_conservation"
```
Search works in that dir; the M31-output absences are real, not a silent-empty grep.

**Direction confirmation (M22→M31):**
```
$ rg -n 'pm_land_conservation' /tmp/magpie_develop_ro/modules/31_past/
  endo_jun13/presolve.gms:9: vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type));
  static/not_used.txt:4: pm_land_conservation,input,questionnaire
```
M31 READS pm_land_conservation (M22's output). Direction is M22→M31, never M31→M22. Doc already correctly lists M22 under "Receives Input From" (line 488), so listing it under "Provides To" is internally contradictory. UPHELD.

**Note on M17 (subtlety in auditor's replacement set):** Auditor's prose says "remove Module 22" but the replacement `corrected_set` also drops "Module 17 (Production)" from line 527. I checked this:
```
$ rg -n 'vm_cost_prod_past' /tmp/magpie_develop_ro/modules/17_*/   -> (no match)
$ rg -n 'vm_prod' /tmp/magpie_develop_ro/modules/31_past/endo_jun13/equations.gms
  17: vm_prod(j2,"pasture") =l= vm_land(j2,"past")      (q31_prod CONSTRAINS vm_prod)
  32: vm_cost_prod_past(i2) =e= sum(cell(i2,j2), vm_prod(j2,"pasture")) * s31_fac_req_past
```
M31 does NOT push any output into module 17; it places an upper-bound constraint on vm_prod (M17's own variable). The canonical "Provides Output To" list at module_31.md:493-498 also omits M17. So dropping both M22 and M17 from line 527 makes it consistent with lines 493-498. The auditor's corrected_set is correct as written.

**corrected_set:** "Provides To: Module 10 (Land), Module 11 (Costs), Module 52 (Carbon), Module 70 (Livestock feed)" — i.e. remove BOTH Module 22 (Conservation) and Module 17 (Production) from line 527 to match the canonical list at lines 493-498. M22 remains under Receives Input From / Depends On only.

---

## R35-31-4 — UPHELD

**Claim:** vm_carbon_stock is DECLARED in Module 56 (not 52). M31 POPULATES it. M52 only READS it. "Source: Module 52 (Carbon) - but calculated here" (doc:309-310) misattributes the declaration.

**DECLARED set (both forms via declarations.gms scan):**
```
$ rg -n 'vm_carbon_stock' /tmp/magpie_develop_ro/modules/*/*/declarations.gms
  30_croparea/detail_apr24/declarations.gms:23  vm_carbon_stock_croparea(j,ag_pools)   <- DIFFERENT var
  30_croparea/simple_apr24/declarations.gms:20  vm_carbon_stock_croparea(j,ag_pools)   <- DIFFERENT var
  56_ghg_policy/price_aug22/declarations.gms:34 vm_carbon_stock(j,land,c_pools,stockType)  <- THE declaration
```
Co-located-name caveat applied: the two croparea hits are `vm_carbon_stock_croparea`, a distinct variable, not vm_carbon_stock. Sole true declaration is 56_ghg_policy/price_aug22/declarations.gms:34. NOT module 52.

**M52 usage (READ-only, no declaration, no population):**
```
$ rg -n 'vm_carbon_stock' /tmp/magpie_develop_ro/modules/52_carbon/
  normal_dec17/equations.gms:14  (comment)
  normal_dec17/equations.gms:19  (pcm_carbon_stock(...) - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length  <- READ inside q52_emis_co2_actual
```
M52 only reads vm_carbon_stock; it does not declare or populate it.

**M31 POPULATES it:**
```
$ rg -n 'vm_carbon_stock' /tmp/magpie_develop_ro/modules/31_past/endo_jun13/equations.gms
  23: vm_carbon_stock(j2,"past",ag_pools,stockType) =e= ...   (LHS of q31_carbon, equations.gms:22-23)
```
DECLARED-in-M56 / POPULATED-by-M31 / READ-by-M52 — exactly the G2 distinction. Auditor UPHELD.

**corrected_set:** vm_carbon_stock — Declared in: Module 56 (56_ghg_policy/price_aug22/declarations.gms:34). Populated here by Module 31 (q31_carbon, "past" slice, equations.gms:22-23). Read by: Module 52 (q52_emis_co2_actual) and Module 56. (Reword doc:309-310 and the line-497 "Provides Output To: Module 52" parenthetical so neither implies M52 declares the variable.) fm_carbon_density "Source: Module 52" stays unchanged (correct — lives in 52_carbon/normal_dec17/input.gms).

---

## R35-31-1 — NOT_CONSUMER_SET (passes to fixer unchanged; auditor claim factually correct)

Not a consumer/populator/dependency-set finding (realization status + file-convention claim). Code-checked anyway:
```
$ find /tmp/magpie_develop_ro/modules -name not_used.txt | wc -l   -> 26
  ...includes defaults: 38_factor_costs/sticky_labor, 59_som/cellpool_jan23,
     29_cropland/simple_apr24, 30_croparea/simple_apr24, 70_livestock/fbask_jan16, ...
$ ls /tmp/magpie_develop_ro/modules/31_past/static/  -> not_used.txt, presolve.gms, realization.gms
```
static/presolve.gms fixes vm_land.fx(j,"past")=pcm_land, vm_carbon_stock.fx, vm_bv.fx(manpast/rangeland), vm_cost_prod_past.fx(i)=0. static/realization.gms has a normal @description ("pasture areas are constant over time") + @limitations ("no computational limitations to this realization") — no "deprecated" language anywhere. not_used.txt is a standard convention file (26 realizations incl. defaults), not a deprecation marker. Auditor is right; classified NOT_CONSUMER_SET only because it is not a set-membership claim.

---

## R35-31-3 — NOT_CONSUMER_SET (passes to fixer unchanged; auditor claim factually correct)

Set-member-label claim, not a consumer/producer set. Code-checked anyway:
```
$ rg -n 'stockType' /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/sets.gms
  212: stockType Carbon stock types
$ Read sets.gms:212-214  ->  / actual, actualNoAcEst /
$ rg -n 'stockType.*reference|reference.*stockType' /tmp/magpie_develop_ro/modules/  -> (no 'reference' stockType anywhere)
```
Members are exactly `actual, actualNoAcEst` (sets.gms:213). No `reference` member exists. Auditor's correction (replace "Actual vs. reference stocks" at doc:140-141 with the real members) is factually correct.

---

## Summary

| Bug | class_is_consumer_set | Verdict |
|-----|----------------------|---------|
| R35-31-1 | false | NOT_CONSUMER_SET |
| R35-31-2 | true  | UPHELD |
| R35-31-3 | false | NOT_CONSUMER_SET |
| R35-31-4 | true  | UPHELD |

Both consumer-set findings independently reproduced with both grep forms + positive controls. No phantom-member or silent-empty-grep artifacts. No refutations or corrections needed beyond noting that R35-31-2's corrected_set legitimately drops Module 17 as well as Module 22 (verified: M31 provides nothing to M17, only constrains vm_prod).
