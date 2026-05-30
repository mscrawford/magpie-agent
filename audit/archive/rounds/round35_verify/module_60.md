# Round 35 Adversarial Verification — module_60.md

Verifier role: adversarial consumer/populator/dependency-SET refuter.
Ground truth: /tmp/magpie_develop_ro (develop worktree).

## Scope determination

The three auditor findings were screened against the consumer-set definition:
"asserts WHICH modules consume / populate / depend-on an interface variable or
parameter (phantom member, omitted member, wrong producer/consumer set,
direct-vs-transitive)."

**None of the three findings are module-dependency-SET claims.** They are:
- 836: a wrong numerical scale value + a wrong/off-by-one citation pointing at the
  wrong variable (class 13/12).
- 494: a list-truncation + mislabel of which **product-set members** (`pasture`,
  `kap`, `kforestry`) get `vm_dem_bioen.fx = 0` in presolve. The "set" here is over
  PRODUCTS (kall elements), not over MODULES, and the claim does not assert which
  modules consume/populate `vm_dem_bioen`. Closest call of the three, but still not a
  module consumer/producer-set claim — it is a content/truncation bug in a fixing block.
- 592: a hardcoded scenario-COUNT drift (90+ vs 88), no module set involved.

All three therefore pass through as NOT_CONSUMER_SET; the fixer handles them
unchanged. Per instructions I spend no consumer-set re-derivation effort, but I did
cheaply confirm the underlying facts (below) so the verdict is well-grounded — and I
flag one completeness gap in the auditor's proposed_fix for 592.

## Fact confirmation (for grounding only; NOT a consumer-set re-derivation)

### 836 — scaling.gms
`cat -n /tmp/magpie_develop_ro/modules/60_bioenergy/1st2ndgen_priced_feb24/scaling.gms`
```
 8  v60_2ndgen_bioenergy_dem_residues.scale(i,kall) = 1e3;
 9  vm_bioenergy_utility.scale(i) = 1e2;
10  q60_bioenergy_glo.scale = 1e4;
11  q60_bioenergy_reg.scale(i) = 1e2;
12  q60_res_2ndgenBE.scale(i) = 1e3;
```
Auditor is correct: `vm_bioenergy_utility.scale` is on line 9 (doc cites 8) and = 1e2
(=10^2; doc says 10e4 / 10^5). Line 8 holds a different variable. 5 scale statements
exist (8-12), doc shows only one. Auditor finding + proposed_fix are accurate.

### 494 — presolve.gms
`cat -n .../presolve.gms | head -20`
```
 8  vm_dem_bioen.fx(i,"pasture") = 0;
 9  vm_dem_bioen.fx(i,kap) = 0;
10  vm_dem_bioen.fx(i,kforestry) = 0;
```
Auditor is correct: three product groups fixed (pasture, kap=livestock,
kforestry=forestry); doc shows only the kap line and mislabels it "(food, feed,
material)". Proposed relabel/expansion is accurate.

### 592 — sets.gms scen2nd60 count
`sed -n '16,103p' sets.gms | grep -c ','`  -> 87 (commas; last member has none)
`sed -n '16,103p' sets.gms | grep -cE '[A-Za-z0-9]'` -> 88 (content lines)
=> 88 members. Confirmed.
Doc "90+" instances: `grep -n "90+" module_60.md` ->
  592, 780, 1033, 1040, **1067** (auditor's proposed_fix lists only 592/780/1033/1040;
  line 1067 "f60_bioenergy_dem.cs3 ... (90+ scenarios)" is a FIFTH instance the fix omits).
Doc line 279 already states "88 scenarios". Auditor's count is right; flag the missing
1067 for the fixer.

## Verdicts

| id | consumer_set? | verdict | note |
|----|---------------|---------|------|
| module_60:836 | false | NOT_CONSUMER_SET | numerical/citation bug; facts confirm auditor right |
| module_60:494 | false | NOT_CONSUMER_SET | product-set truncation (not module set); facts confirm auditor right |
| module_60:592 | false | NOT_CONSUMER_SET | count drift; 88 confirmed; auditor's fix omits a 5th "90+" at line 1067 |
