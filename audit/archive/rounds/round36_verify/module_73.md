# Round 36 Adversarial Consumer-Set Verification — module_73.md

**Verifier role:** adversarial CONSUMER / POPULATOR / DEPENDENCY-SET verifier (highest-capability model).
**Target doc:** `<magpie-agent>/modules/module_73.md`
**Ground truth:** `/tmp/magpie_develop_ro/modules/73_timber/default/*.gms`, `/tmp/magpie_develop_ro/config/default.cfg`
**Date:** 2026-05-30

---

## Triage result

My mandate is to independently re-derive and adversarially test only the auditor findings that assert **which modules consume / populate / depend on an interface variable or parameter** (phantom member, omitted member, wrong producer/consumer set, direct-vs-transitive misattribution).

I classified all 8 confirmed bugs. **None of B1–B8 is a consumer-set / populator / dependency-set claim.** Every one is a content-citation, file:line-drift, formula-staleness, or derivation-value finding internal to module 73's own code. They do not assert anything about the set of modules that consume or populate a `vm_*` / `pm_*` / `im_*` interface object.

| Bug | bug_class (auditor) | Touches "which modules consume/populate X"? | Verdict |
|-----|--------------------|--------------------------------------------|---------|
| 73-B1 | stale formula presented as code (§2.2 q73_prod_residues RHS) | No — it is the equation RHS form (operands `vm_prod_forestry`/`vm_prod_natveg`), not a statement about which *modules* consume a variable | NOT_CONSUMER_SET |
| 73-B2 | stale file:line + wrong value (§11 items 3/7/8/9) | No — input.gms/preloop.gms/equations.gms line refs + cost values | NOT_CONSUMER_SET |
| 73-B3 | stale file:line (equation header drift) | No — equations.gms line numbers only | NOT_CONSUMER_SET |
| 73-B4 | stale file:line (realization.gms:16→22) | No — single line ref for a `@limitations` comment | NOT_CONSUMER_SET |
| 73-B5 | stale file:line (preloop.gms drifts) | No — preloop.gms line numbers only | NOT_CONSUMER_SET |
| 73-B6 | wrong derivation number (60→72 EUR/m3) | No — config-comment derivation arithmetic | NOT_CONSUMER_SET |
| 73-B7 | wrong derivation number (~30%→27%) | No — residue-potential percentage in prose/comment | NOT_CONSUMER_SET |
| 73-B8 | stale reference after rename (typo scalar + line refs) | No — scalar name spelling + input.gms/equations.gms line refs | NOT_CONSUMER_SET |

Per method step 2, NOT_CONSUMER_SET findings pass to the fixer unchanged; I do not issue UPHELD/REFUTED/CORRECTED on them (that would overstep this verifier's lens — a separate citation-verifier owns those).

---

## Sanity reads performed (context only — NOT verdicts)

To confirm my classification (and to make sure no consumer-set dimension was hiding inside the two "Major" content findings B1/B2), I read the live code. These reproduce the auditor's `reality_in_code`, which *supports* (does not establish) that B1/B2 are genuine content bugs — but adjudicating them is outside my consumer-set mandate.

- **equations.gms** (`/tmp/magpie_develop_ro/modules/73_timber/default/equations.gms`):
  - `q73_prod_residues(j2)` at line 75; RHS is `(sum(kforestry, vm_prod_forestry(j2,kforestry)) + sum((land_natveg,kforestry), vm_prod_natveg(j2,land_natveg,kforestry))) * s73_residue_ratio` (lines 75–81). Confirms the doc §2.2 block (doc lines 98–102, still showing `vm_prod(j2,"wood") * s73_residue_ratio`) is stale. The doc's own §7.4 (doc line 462) already carries the correct sum form — internal contradiction, as auditor noted. [supports B1]
  - 8-line `@equations` comment header now occupies lines 8–21; equations begin: `q73_cost_timber`=23, `q73_prod_wood`=43, `q73_prod_woodfuel`=52, `q73_prod_residues`=75. [supports B3]
  - Residue-derivation comment (lines 65–67) says "theoretical potential of logging residues is 27% of stem harvest [@oswalt2019forest] ... 52% ... 0.27 * 0.52 = 0.14 ~ 0.15". [supports B7]
- **input.gms** (`/tmp/magpie_develop_ro/modules/73_timber/default/input.gms`): scalars block lines 14–25:
  - line 15 `s73_timber_prod_cost_wood / 89 /`; line 16 `s73_timber_prod_cost_woodfuel / 44 /`; line 17 `s73_free_prod_cost / 1e+06 /`; line 19 `s73_income_threshold / 10000 /`; line 20 `s73_residue_ratio / 0.15 /`; line 21 `s73_residue_removal_cost / 2.7 /` (correctly spelled, not the old `s73_reisdue_*` typo); line 23 `s73_natveg_cost_premium / 0.15 /`; line 24 `s73_woodfuel_stacking_factor / 0.65 /`. Confirms residue_ratio@20 (not 24), removal_cost=2.7@21 (not 2.5@25), free_prod_cost@17, woodfuel=44@16 (not 74@20). [supports B2, B8]

These observations are recorded so the fixer/citation-verifier has them; they are explicitly **not** consumer-set verdicts.

---

## Consumer-set claims present in the doc but NOT flagged by the auditor

For completeness (and to confirm the auditor did not silently alter a consumer set): the doc *does* contain real consumer/producer-set claims that none of B1–B8 touch, so they are out of scope for this batch:

- doc:320–323 "Other consumers of `pm_climate_class` (outside M73)" → M14 / M58 / M59
- doc:325–327 "Consumers of `pm_demand_forestry` (outside M73)" → M32 / M62
- §10 dependency lists (doc:566–604): inputs from M09/M17/M32/M35; outputs to M32/M62/M11

Since the auditor made no change to any of these, there is no consumer-set correction for me to uphold, refute, or correct in this round. No phantom member was added and no documented member was deleted by any of B1–B8.

---

## Bottom line

8/8 findings → **NOT_CONSUMER_SET**. No consumer-set adjudication required; all pass to the fixer unchanged. No false phantom-deletion or false omitted-member addition risk detected in this batch.
