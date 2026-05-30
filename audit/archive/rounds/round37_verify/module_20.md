# Round 37 Adversarial Verification — module_20.md

Verifier: adversarial (Opus 4.8 1M). Ground truth: `/tmp/magpie_develop_ro` develop worktree.
Date: 2026-05-30.

## Consumer-set classification

The verifier's primary mandate is the CONSUMER / POPULATOR / DEPENDENCY-SET class (which modules
consume/populate/depend-on an interface variable). **None of the three confirmed bugs make such a
claim:**

- 20-B1: numeric scale value (bug class 13, wrong number) — NOT consumer-set.
- 20-B2: hardcoded output-variable count (bug class 6, count drift) — NOT consumer-set.
- 20-B3: reversed file:line citation range (bug class 10) — NOT consumer-set.

Therefore each receives verdict **NOT_CONSUMER_SET** and passes to the fixer unchanged. Per method,
I spend no consumer-set re-derivation effort on them. However, since I read the code anyway, I
record below whether the auditor's underlying factual claim reproduces (it does, for all three) — so
the fixer has independent confirmation.

---

## 20-B1 — vm_cost_processing.scale / vm_processing_substitution_cost.scale values

**Verdict: NOT_CONSUMER_SET** (underlying factual claim independently CONFIRMED correct).

Code read — `/tmp/magpie_develop_ro/modules/20_processing/substitution_may21/scaling.gms:8-9`:
```
8  vm_cost_processing.scale(i) = 1e5;
9  vm_processing_substitution_cost.scale(i) = 1e4;
```

- `1e5` = 100,000. Doc:253 writes `10e5` (= 1,000,000) annotated "1 million USD" — 10x too high.
- `1e4` = 10,000. Doc:280 writes `10e4` (= 100,000) annotated "10,000 USD" — written value 10x too
  high; the parenthetical annotation "10,000" happens to match the code but the written `10e4` does not.

Auditor's reality_in_code and proposed_fix (`1e5` / 100,000 USD; `1e4` / 10,000 USD) match code
exactly. No consumer-set content; passes through unchanged.

## 20-B2 — Interface Variables (Outputs) count

**Verdict: NOT_CONSUMER_SET** (underlying factual claim independently CONFIRMED correct).

Independent grep, BOTH the structural read and a positive control on the same dir:
```
$ rg -n '^\s*vm_' /tmp/magpie_develop_ro/modules/20_processing/substitution_may21/declarations.gms
16:  vm_dem_processing(i,kall)              Demand for processing use ...
19:  vm_secondary_overproduction(i,kall,kpr) Overproduction of secondary couple products ...
20:  vm_cost_processing(i)                  Processing costs ...
24:  vm_processing_substitution_cost(i)     Costs or benefits of substituting one product ...
```
Exactly 4 `vm_` outputs (16, 19, 20, 24). Lines 17-18 (`v20_dem_processing`, `v20_secondary_substitutes`)
are module-internal `v20_`, correctly excluded. Doc's own Outputs table (module_20.md:292-295) lists
all 4; header line 7 says 3 — internally inconsistent with both table and code. Auditor's fix
(3 -> 4) is correct. This is a self-count of THIS module's own outputs, not a claim about other
modules' consumption — NOT consumer-set. Passes through unchanged.

## 20-B3 — reversed citation range equations.gms:142-132

**Verdict: NOT_CONSUMER_SET** (underlying factual claim independently CONFIRMED correct).

Doc:526 cites `equations.gms:142-132` (end < start — impossible range, clear typo).

Code read — `/tmp/magpie_develop_ro/modules/20_processing/substitution_may21/equations.gms`:
- Quality-cost PROSE block: lines 127-132 (heterogeneity of oils, low-quality palm oil more
  expensive / high-quality cheaper, magnitude from price differences standardized to soybean oil).
- f20_quality_cost TERM applied: confirmed at line 142 via
  `$ rg -n 'f20_quality_cost' .../equations.gms` -> `142:  * f20_quality_cost(ksd,kpr));`

The doc sentence ("Quality cost adjustments for oils f20_quality_cost provide some differentiation")
is about the quality-cost concept; the prose explaining that differentiation is 127-132. Adjacent doc
lines already anchor there (doc:524 cites 127-129; doc:276-277 cite 127-129/129-130/130-132). Auditor's
fix (-> `equations.gms:127-132`) is well-chosen and correct. (An alternative anchor `140-142` for the
term itself would also be defensible, but 127-132 better matches the explanatory-prose intent of the
sentence.) Not a consumer-set claim. Passes through unchanged.

---

## Summary

| Bug | consumer-set? | verdict | factual claim reproduces? |
|-----|---------------|---------|---------------------------|
| 20-B1 | no | NOT_CONSUMER_SET | yes — fix matches scaling.gms:8-9 |
| 20-B2 | no | NOT_CONSUMER_SET | yes — 4 vm_ outputs, fix 3->4 correct |
| 20-B3 | no | NOT_CONSUMER_SET | yes — reversed range, fix ->127-132 correct |

No consumer/populator/dependency-set findings were submitted, so no phantom-member, omitted-member,
or direct-vs-transitive re-derivation was required. All three findings are sound and pass to the fixer
unchanged.
