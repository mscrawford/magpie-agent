# Round 37 adversarial consumer-set verification — module_54.md

Verifier: adversarial (Opus 4.8 1M). Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only).
Default posture: skeptical; consumer-set claims are the highest-FP class.

---

## module_54-B1 — VERDICT: UPHELD

**class_is_consumer_set = true.** The finding asserts WHICH modules consume/route the interface
variable `vm_p_fert_costs` (auditor: exactly one consumer, Module 11, DIRECT; Module 38 phantom;
direct-vs-transitive per MANDATE 17). This is squarely a consumer/dependency-set claim.

### What the doc currently says (the error)
module_54.md:259-266 asserts a two-hop routing chain:
- Item 4 — "Module 38 (Factor Costs): Would receive P fertilizer costs from Module 54 ... added to
  total production costs in objective function"
- Item 5 — "Module 11 (Costs): Would aggregate P fertilizer costs **from Module 38**"

i.e. the doc claims M54 -> M38 -> M11.

### Independently re-derived true consumer set: {Module 11 ONLY}, DIRECT

I grepped BOTH the equation form `vm_p_fert_costs(` AND the attribute form `vm_p_fert_costs.`
(.l/.lo/.up/.fx/.m), cross-checked with a third broad unanchored grep, and ran a positive control
on the candidate-phantom module dir (M38).

**(A) Equation form — `rg -n 'vm_p_fert_costs\(' /tmp/magpie_develop_ro/modules/`**
```
54_phosphorus/off/declarations.gms:10:  vm_p_fert_costs(i)   costs for mineral fertilizers (mio. USD17MER per yr)
11_costs/default/equations.gms:25:                   + vm_p_fert_costs(i2)
```
-> declaration in M54 itself + exactly ONE external consumer: M11's q11_cost_reg.

**(B) Attribute form — `rg -n 'vm_p_fert_costs\.' /tmp/magpie_develop_ro/modules/`**
```
54_phosphorus/off/postsolve.gms:10-13:  vm_p_fert_costs.m/.l/.up/.lo(i)   (M54's own reporting)
54_phosphorus/off/preloop.gms:10:       vm_p_fert_costs.fx(i)=0;          (M54 fixes itself to zero)
```
-> ALL attribute-level reads are inside module 54 itself. No OTHER module reads .l/.lo/.up/.fx/.m.
This rules out the R33-style trap (a presolve/postsolve solution-level read invisible to `NAME(`).

**(C) Broad unanchored cross-check — `rg -n 'vm_p_fert_costs' /tmp/magpie_develop_ro/`**
Returns the union of (A)+(B) and nothing else (whole repo, not just modules/). No hits in M38, M14,
M43, M44, or anywhere besides M54 and M11/default/equations.gms:25.

**(D) POSITIVE CONTROL on the alleged phantom (Module 38) — proves the dir is searchable**
```
rg -n 'vm_cost_prod' /tmp/magpie_develop_ro/modules/38_factor_costs/
  -> sticky_labor/postsolve.gms:14,26,38,50  (vm_cost_prod_crop.m/.l/.up/.lo ...)
  -> sticky_labor/declarations.gms:18         (vm_cost_prod_crop(i,factors) ...)   [sibling token FOUND]
rg -n 'vm_p_fert_costs' /tmp/magpie_develop_ro/modules/38_factor_costs/
  -> [CONFIRMED ABSENT in M38]  (both forms, zero hits)
```
A known M38 cost variable is found, so the search machinery works in that dir; `vm_p_fert_costs`
is genuinely absent. Module 38 is a phantom consumer.

### Corroborating checks (strengthen the auditor's proposed replacement text)
- Exact line numbers in q11_cost_reg: `vm_nr_inorg_fert_costs(i2)` at **line 24**, `vm_p_fert_costs(i2)`
  at **line 25** (adjacent, P directly below N). Matches the proposed fix verbatim.
- `vm_p_fert_costs.fx(i)=0;` at **preloop.gms:10** — fixed to zero, so the interface is present but
  contributes nothing. Matches.
- The auditor's analogy ("mirroring N inorganic fertilizer cost which comes from Module 50, not 38"):
  `vm_nr_inorg_fert_costs` is declared/produced in `50_nr_soil_budget/macceff_aug22`
  (declarations.gms:11, equations.gms, postsolve.gms, scaling.gms). CONFIRMED — it does NOT route
  through M38 either. The analogy is sound.
- Active realizations (config/default.cfg): `cfg$gms$costs <- "default"` (line 236, matches cited
  path) and `cfg$gms$phosphorus <- "off"` (line 1587). The "off" realization fixing the var to zero
  is consistent with the "interface present, contributes nothing" framing.
- Doc-internal contradiction confirmed: module_54.md:304-306 (Phase-1 text) correctly names
  "Integration with Module 11 (Costs): Add `vm_p_fert_costs` to objective function" with NO mention
  of M38 — directly contradicting items 4-5 at lines 259-266.

### Why UPHELD (not CORRECTED)
The auditor's correction is fully accurate: the consumer set is {M11}, the link is DIRECT (q11_cost_reg
line 25), Module 38 is a true phantom (positive control passes, both grep forms empty), the line
numbers are exact, and the M50-not-M38 analogy holds. No part of the proposed fix introduces an error.
MANDATE 17 (direct-vs-transitive) is satisfied: M11 reads vm_p_fert_costs directly in its own equation,
not transitively via M38. The proposed_fix text is adopt-as-is.

### Adopt
Delete item 4 (Module 38). Replace items 4-5 with the auditor's proposed_fix text verbatim
(M11 is the sole, direct consumer via q11_cost_reg equations.gms:25; var fixed to 0 in preloop.gms:10;
P cost does NOT route through M38; mirrors N inorg fert cost which comes from M50 not M38).

---

## Summary
1 finding, all consumer-set. Verdict: **UPHELD**. Independent re-derivation reproduces every
claim — single direct consumer (M11), phantom M38 (positive control passed), exact line numbers,
and the supporting M50 analogy. Doc lines 259-266 contain a fabricated M54->M38->M11 routing chain
contradicted both by code and by the doc's own line 304-306.
