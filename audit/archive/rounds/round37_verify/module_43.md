# Round 37 adversarial verification — module_43.md

Verifier role: adversarial (highest-capability). Ground truth: `/tmp/magpie_develop_ro`.
Default posture: skepticism toward consumer/populator/dependency-set claims.

Summary: 3 bugs. 1 is a consumer/dependency-set claim (B1) → independently re-derived → **UPHELD**.
2 are not consumer-set claims (B2 scale value, B3 line counts) → **NOT_CONSUMER_SET** (pass to fixer unchanged);
their underlying facts were nonetheless spot-checked and reproduce exactly.

---

## B1 (module_43.md:871) — "Provides to: Module 11 (costs): Shadow prices on water constraint"

**class_is_consumer_set = true.** This asserts WHICH module M43 provides to (a producer/consumer
dependency edge: M43 → M11). MANDATE-17 direct-vs-transitive class.

**Verdict: UPHELD.** M43 provides nothing to M11. The doc edge is a phantom dependency.

Independently re-derived the true set (both equation `NAME(` and attribute `NAME.` forms + positive control):

1. M11's water cost comes from M42, not M43:
```
$ rg -n 'vm_water_cost' /tmp/magpie_develop_ro/modules/11_costs/
modules/11_costs/default/equations.gms:46:                   + vm_water_cost(i2)
```
Positive control (search works in 11_costs/default/equations.gms):
```
$ rg -n 'vm_cost_glo' /tmp/magpie_develop_ro/modules/11_costs/default/equations.gms
10: q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

2. No M43 token of any kind appears in 11_costs (confirms M11 does not read M43):
```
$ rg -n 'q43_water|v43_watavail|oq43_water|im_wat_avail|i43_|p43_|s43_' /tmp/magpie_develop_ro/modules/11_costs/
(no match)  -> NO M43 token in 11_costs
```

3. `vm_water_cost` is produced (declared + defined) by M42, both realizations:
```
$ rg -n 'vm_water_cost' /tmp/magpie_develop_ro/modules/42_water_demand/
.../agr_sector_aug13/declarations.gms:31:  vm_water_cost(i)  Cost of irrigation water ...
.../agr_sector_aug13/equations.gms:17:   vm_water_cost(i2) =e= sum(cell(i2,j2), vm_watdem("agriculture",j2)) * ic42_pumping_cost(i2);
.../all_sectors_aug13/equations.gms:17:  vm_water_cost(i2) =e= ... (same)
(+ postsolve ov_water_cost lines in both realizations)
```

**Auditor's proposed fix independently verified — all three sub-claims hold:**

(a) M43 owns no cost variable:
```
$ rg -n 'vm_cost|vm_water_cost' /tmp/magpie_develop_ro/modules/43_water_availability/
(no match)  -> NO vm_cost* owned/used by M43
```

(b) M43's real interface output is `im_wat_avail`, produced in M43 and consumed by M42 presolve
(env-flow + reserved-fraction water demand). Both forms checked:
```
# produced by M43:
.../43.../total_water_aug13/preloop.gms:8: im_wat_avail(t,"surface",j) = f43_wat_avail(t,j);  (+10,11,12)
.../43.../total_water_aug13/declarations.gms:9: im_wat_avail(t,wat_src,j) Water availability (mio. m^3 per yr)

# consumed by M42 presolve (im_wat_avail( form):
.../42.../agr_sector_aug13/presolve.gms:38: vm_watdem.fx("manufacturing",j) = sum(wat_src, im_wat_avail(t,wat_src,j)) * s42_reserved_fraction;
.../42.../agr_sector_aug13/presolve.gms:44,67,73  (reserved-fraction + env-flows)
.../42.../all_sectors_aug13/presolve.gms:58,64    (env-flows)
# im_wat_avail. (attribute) form: no match (it's a parameter, no solution attrs) -> expected
```

(c) `oq43_water.marginal` / `v43_watavail.m` are postsolve diagnostic OUTPUTS, read by no other module:
```
$ rg -n 'oq43_water|v43_watavail\.m|q43_water\.m' /tmp/magpie_develop_ro/modules/ | grep -v '/43_water_availability/'
(no match)  -> NO external read of M43 marginals
# in M43 postsolve:
.../total_water_aug13/postsolve.gms:11: oq43_water(t,j,"marginal") = q43_water.m(j);
.../total_water_aug13/postsolve.gms:10: ov43_watavail(t,wat_src,j,"marginal") = v43_watavail.m(wat_src,j);
```

Minor evidence-line note (non-blocking): the auditor's file_evidence cites the marginal at
postsolve.gms:10-11, but line 10 is `ov43_watavail` and line 11 is `oq43_water`. The proposed-fix
PROSE cites only "`oq43_water.marginal`" with no line number, so the corrected claim text is accurate
as written; no change to the fix needed.

Apply the auditor's proposed_fix verbatim.

---

## B2 (module_43.md:463) — scale value `10e4` vs code `1e4`; prose "10^5"; omitted q43_water.scale

**class_is_consumer_set = false.** This is a content-level citation mismatch (fenced code block !=
actual code) about a solver scaling numeric — it asserts nothing about which modules consume/populate
an interface variable. **Verdict: NOT_CONSUMER_SET** (passes to fixer unchanged).

Spot-check (the underlying fact reproduces exactly):
```
$ cat scaling.gms (lines 8-9)
8: v43_watavail.scale(wat_src,j) = 1e4;
9: q43_water.scale(j) = 1e2;
```
Code is `1e4` (10^4 = 10000), not the doc's `10e4` (10^5 = 100000). Doc prose "scale by 10^5"
matches the wrong value. Line 9 (`q43_water.scale(j) = 1e2;`) is genuinely absent from the doc.
Auditor's reality and fix are correct; not my class to gate.

---

## B3 (module_43.md:777-792) — file line-count table off by one

**class_is_consumer_set = false.** Hardcoded-count drift (class 6); no interface-variable
consumer/producer assertion. **Verdict: NOT_CONSUMER_SET** (passes to fixer unchanged).

Spot-check (reproduces exactly):
```
$ wc -l module.gms total_water_aug13/{realization,declarations,input,equations,preloop,presolve,postsolve,scaling}.gms
 21 module.gms
 52 realization.gms
 25 declarations.gms
 27 input.gms
 20 equations.gms
 12 preloop.gms
 16 presolve.gms
 19 postsolve.gms
  9 scaling.gms
201 total
```
Doc values (22,53,26,28,21,13,17,20,9; total ~190) are each +1 except scaling (correct at 9).
Auditor's corrected counts match wc -l. Not my class to gate.

---

### Verifier conclusion
- B1: UPHELD (consumer/dependency-set claim, independently confirmed phantom edge; fix accurate).
- B2: NOT_CONSUMER_SET (content/numeric mismatch; fact reproduces; out of my gating scope).
- B3: NOT_CONSUMER_SET (count drift; fact reproduces; out of my gating scope).
No REFUTED/CORRECTED items. No false-positive consumer-set findings detected.
