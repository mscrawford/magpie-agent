# Round 36 Adversarial Verification — module_71.md (consumer/populator/dependency-set findings)

Verifier model: Opus 4.8 (1M). Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only).
Scope per charter: independently try to REFUTE each CONSUMER / POPULATOR / DEPENDENCY-SET finding. Non-consumer-set findings are passed through (NOT_CONSUMER_SET) with minimal effort.

---

## 71-B1 — Equation count "4 active per mode" — NOT_CONSUMER_SET

**class_is_consumer_set = false.** This finding asserts an equation-activity COUNT (bug class 6, hardcoded counts drift), not which modules consume/populate/depend-on an interface variable or parameter. It is out of my charter scope and passes to the fixer unchanged.

For the record, the auditor's count reproduces against `foragebased_jul23/equations.gms`: only `q71_feed_balanceflow_nlp` (:34, `$(s71_lp_fix=0)`) and `q71_feed_balanceflow_lp` (:44, `$(s71_lp_fix=1)`) are dollar-gated; the other four (`q71_feed_rum_liv` :14, `q71_feed_forage` :21, `q71_prod_mon_liv` :55, `q71_punishment_mon` :66) are unconditional, so 5 are active in each mode. But scoring this is the fixer's job, not mine.

Verdict: **NOT_CONSUMER_SET** (no consumer-set re-derivation required).

---

## 71-B2 — Code-file count "7" / scaling.gms omission — NOT_CONSUMER_SET

**class_is_consumer_set = false.** This asserts a file COUNT and a file-list omission (bug class 6), not a module dependency/consumer/producer set. Out of charter scope; passes through.

For the record: `ls foragebased_jul23/*.gms` = 9 files (declarations, equations, nl_fix, nl_release, postsolve, preloop, realization, scaling, sets); `scaling.gms` is real and included at `realization.gms:27`. Auditor's evidence reproduces. Not my call to score.

Verdict: **NOT_CONSUMER_SET**.

---

## 71-B3 — vm_prod_reg "from Module 70" producer attribution — UPHELD

**class_is_consumer_set = true.** This finding asserts the PRODUCER/PROVIDER of an interface variable (vm_prod_reg): doc:164 says "from Module 70", auditor says it is declared+defined in Module 17 and Module 70 is a consumer. Producer attribution is a dependency-set claim → in scope, re-derived independently.

### Independent re-derivation of the producer

**(1) Where is vm_prod_reg DECLARED?** — Module 17 only.
```
$ rg -n 'vm_prod_reg' /tmp/magpie_develop_ro/modules/*/*/declarations.gms
modules/17_production/flexreg_apr16/declarations.gms:10: vm_prod_reg(i,kall)  Regional aggregated production (mio. tDM per yr)
```
Sole declaration. (Broad file-level sweep `rg -l 'vm_prod_reg' modules/` returns ~20 files, but the ONLY declarations.gms among them is 17's; everything else is equations/postsolve/preloop = use sites.)

**(2) Where is vm_prod_reg DEFINED (the equation that sets its level)?** — Module 17, q17_prod_reg.
```
$ (read) modules/17_production/flexreg_apr16/equations.gms:10-11
q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```
vm_prod_reg = sum over cells of vm_prod. Defining equation is owned by Module 17.

**(3) Is Module 70 a CONSUMER (not producer)? — both forms checked.**
```
$ rg -n 'vm_prod_reg\(' /tmp/magpie_develop_ro/modules/70_livestock/
.../fbask_jan16/equations.gms:18  vm_dem_feed(i2,kap,kall) =g= vm_prod_reg(i2,kap)
.../fbask_jan16/equations.gms:28  ... vm_prod_reg(i2,kli_rum)*sum(ct,im_feed_baskets(...,"pasture"))
.../fbask_jan16/equations.gms:36  v70_feed_intake_pre(i2,kap,kall) =e= vm_prod_reg(i2,kap)
.../fbask_jan16/equations.gms:60,65  vm_cost_prod_livst(...) =e= sum(kli, vm_prod_reg(i2,kli)*...)
.../fbask_jan16/equations.gms:70  vm_prod_reg(i2,"fish")*i70_cost_regr(...)
(+ identical hits in fbask_jan16_sticky)

$ rg -n 'vm_prod_reg\.' /tmp/magpie_develop_ro/modules/70_livestock/
(no output -> no .l/.lo/.up/.fx/.m reads in module 70)
```
In every M70 occurrence vm_prod_reg is on the RHS / inside a sum as an INPUT to M70's own constraints (feed demand, feed intake, factor/fish costs). M70 reads it; it does not declare or define it. Attribute form returns nothing, so there is no hidden solution-level produce either.

**(4) POSITIVE CONTROL — prove the grep works in M70's declarations dir.**
```
$ rg -n 'vm_prod\b' modules/70_livestock/fbask_jan16/declarations.gms   -> (no output)
$ rg -n 'vm_dem_feed' modules/70_livestock/fbask_jan16/declarations.gms -> 11: vm_dem_feed(i,kap,kall) ... (FOUND)
```
The sibling token vm_dem_feed is found at line 11, proving the search reaches M70's declarations. vm_prod (and by extension vm_prod_reg) is genuinely absent there — M70 declares neither. Absence is confirmed by a working search, not a broken one.

### Co-located-name / MANDATE-17 (direct vs transitive) check
The doc line 164 is a component gloss inside the q71_prod_mon_liv formula block; vm_prod_reg genuinely appears in that equation (`foragebased_jul23/equations.gms:57`), so this is not a co-located-name artifact. The error is purely the producer attribution ("from Module 70"). M17 is the DIRECT producer (declares + defines). M70 is the economic DRIVER of the level via demand constraints but is itself a consumer of the variable, not its source — exactly the distinction the auditor draws.

### Note on the doc's own self-consistency
The formal interface table at doc:258-259 already frames vm_prod_reg as "Optimized (regional aggregate)" (correct), and doc:625 lists it as "Optimized / Regional aggregate." Only the component gloss at doc:164 mis-attributes it to "Module 70." So this is a localized line-164 error; the surrounding table framing is already defensible. The auditor's Minor downgrade rationale (user would grep the declaration and land in M17 anyway) is reasonable, but the line is still factually wrong and the fix is a clean improvement.

### Verdict
**UPHELD.** Auditor's correction is correct: vm_prod_reg is declared in Module 17 (declarations.gms:10) and defined by q17_prod_reg as sum(cell, vm_prod) (equations.gms:11); Module 70 is a consumer that drives its level via demand/feed constraints, not its producer. Apply the auditor's proposed fix at doc:164. (Optional, not required: a one-line note at doc:259/272 that vm_prod/vm_prod_reg are owned by Module 17 production.)

---

## Summary
| Bug | consumer_set? | Verdict |
|-----|---------------|---------|
| 71-B1 | no | NOT_CONSUMER_SET |
| 71-B2 | no | NOT_CONSUMER_SET |
| 71-B3 | yes | UPHELD |
