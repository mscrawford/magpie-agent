# Round 36 adversarial verification — module_41.md

Verifier role: adversarial consumer/populator/dependency-set checker (highest-capability model).
Scope per method: only consumer-set findings get independent set re-derivation; non-consumer-set
findings are classified NOT_CONSUMER_SET and pass to the fixer unchanged. I record the incidental
factual confirmation I observed while reading ground truth, but it does not change the verdict class.

Ground truth worktree: /tmp/magpie_develop_ro (develop, read-only).

---

## Classification summary

| Bug | Asserts a module consumer/producer/dependency set? | Verdict |
|-----|----------------------------------------------------|---------|
| module_41-B1 | No — scaling VALUE + magnitude prose (`10e4` vs `1e4`, "10^5" vs "10^4") | NOT_CONSUMER_SET |
| module_41-B2 | No — completeness of documented scaling LINES in Section 10 | NOT_CONSUMER_SET |
| module_41-B3 | No — hardcoded per-file LINE COUNTS in Section 17 | NOT_CONSUMER_SET |

None of the three findings concerns which modules consume, populate, or depend on an interface
variable/parameter. There is no phantom-member, omitted-member, wrong-producer/consumer-set, or
direct-vs-transitive claim in any of them. `class_is_consumer_set = false` for all three; per the
method they receive verdict NOT_CONSUMER_SET and I spend no effort re-deriving consumer sets.

---

## module_41-B1 — NOT_CONSUMER_SET

Claim is about the scaling value at scaling.gms:8 (`10e4` vs code `1e4`) and the magnitude prose
("10^5" vs "10^4"). This is a content-level value/citation mismatch, not a set-membership claim.

Incidental ground-truth confirmation (does not affect verdict):
- `cat -n .../endo_apr13/scaling.gms` line 8 = `vm_cost_AEI.scale(i) = 1e4;`
- Doc module_41.md:693 = `vm_cost_AEI.scale(i) = 10e4;`; module_41.md:698 prose says "10^5".
- 1e4 = 10^4 = 10,000; 10e4 = 10^5. Auditor's correction is factually right, but it is not a
  consumer-set finding, so it passes through unchanged for the fixer to apply.

## module_41-B2 — NOT_CONSUMER_SET

Claim is that Section 10 omits the active second scaling line `q41_cost_AEI.scale(i) = 1e4;`
(scaling.gms:10) and that scaling.gms:9 is a commented-out `q41_area_irrig.scale`. This is a
completeness-of-documented-lines claim, not a module set-membership claim.

Incidental ground-truth confirmation:
- scaling.gms:9 = `*q41_area_irrig.scale(j) = 1e-2;` (commented)
- scaling.gms:10 = `q41_cost_AEI.scale(i) = 1e4;` (active)
- Auditor description accurate; not a consumer-set finding.

## module_41-B3 — NOT_CONSUMER_SET

Claim is that Section 17's hardcoded per-file line counts drift from `wc -l`. Line-count drift,
not set membership.

Incidental ground-truth confirmation (`wc -l`, all files trailing-newline-terminated):
module.gms 20 (doc 21); endo realization 39 (40); endo sets 14 (15); endo declarations 34 (35);
endo input 25 (26); endo equations 23 (24); endo preloop 9 (10); endo presolve 14 (15);
endo postsolve 27 (28); endo scaling 10 (doc 9); static realization 22 (23); static sets 14 (15);
static declarations 26 (27); static input 15 (16); static equations 16 (17); static presolve 11 (12);
static postsolve 22 (23). Matches auditor's table exactly (16 counts +1 high, scaling -1).
Not a consumer-set finding.

---

## Conclusion

All three bugs are out of scope for adversarial consumer-set verification (NOT_CONSUMER_SET).
They reproduce against develop code and pass to the fixer unchanged. No consumer/producer set was
asserted, so no phantom/omitted-member analysis, attribute-form (NAME.) grep, or positive control
was required for set membership. (Reads of scaling.gms and wc -l on the 17 files were done only to
confirm the findings are not silently mislabeled set claims.)
