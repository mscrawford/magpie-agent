# Corpus investigation — master plan, priority-ordered

**Written 2026-08-01. Supersedes the ordering in `other_falsehoods_mining_plan.md`,
which remains the detailed spec for track 2.** Every gate and threshold here is fixed
*before* the corresponding run.

## The reordering, and what caused it

The 2026-08-01 session fixed 25 doc defects. **Every one was a pointer error** — a
citation pointing at the wrong line, or a path naming the wrong realization. Every
checker built that day binds a pointer. Then a free re-analysis of R55's depth audit
(`audit/integrated/depth_residual_density.json`, 3 hub docs, 5 decorrelated lenses, every
Critical/Major adversarially refuted) put that layer in proportion:

```
POINTER         1 / 27   3.7%     0 of 8 Criticals+Majors
BINDABLE FACT  21 / 27  77.8%     6 of 8
PROCESS         5 / 27  18.5%     2 of 8
```

**Pointer errors are ~4% of confirmed defects and zero of the serious ones.** A day of
work had been spent hardening the layer that carries almost none of the harm. (Lead, not
result: n=27, one round, the most-audited hub docs, and the lens set determines what is
found. The 1-item gap against 28 reported confirmed is unreconciled and flagged.)

At the same time, the arena's only two significant effects both point the same way:

```
class = attribution_role   28.1%  vs  4.2% all other classes   p = 0.0012
regime = docs-only         29.2%  vs  3.1% normal              p = 0.0157
```

**Attribution-role IS a cross-module claim** — who declares vs. populates vs. reads a
variable across module boundaries. The class effect and the process layer are the same
finding reached from two directions, and nothing else in the arena exceeds ~4%.

---

# TRACK 1 (lead) — Sprint X: cross-module claims, docs-only

Absorbs and supersedes "Sprint P" as originally drafted. Not yet run.

## The question

Do the docs mislead a reader about **how MAgPIE works across module boundaries** — and if
so, how often, per claim?

## Why docs-only is the whole measurement, not a detail

Run normally (strong model, tools on), this flywheel would measure **3.1%**, because the
model self-corrects from source. The result would look like validation and would say
almost nothing about the docs.

**Docs-only converts a model measurement into a corpus measurement.** It is also the
regime closest to colleagues on weaker models — the population the corpus exists for.
Keep a small normal-regime control cell so the regime gap is re-measured rather than
assumed from arena round 1A.

## Design

| axis | levels | why |
|---|---|---|
| **claim locus** | cross-module vs within-module | **both arms, or the concentration is assumed rather than measured** |
| **regime** | docs-only (main) + normal (control cell) | isolates corpus from model capability |
| **lens** | all 5 from `doc_depth_audit.workflow.js`, reported per lens | `citation_formula` = pointer, `mechanism_direction` = process |

1. **Exhaustive claim ledger first.** `cross_module/` is 5,330 lines over 6 substantive
   docs (safety guide, circular dependencies, 4 balance docs) — small enough to enumerate
   every load-bearing claim, so rates carry real denominators rather than estimates.
2. **Within-module arm** sampled at RANDOM, not by centrality. R55 and R58 both ran on
   hubs and R58 found its own selection survivorship-biased; hub residual density is a
   floor, not an estimate.
3. **Trace every propagated error back to the doc claim that caused it.** A flywheel
   measures whether a reader is misled — the outcome, which is what matters — but without
   tracing it reports that a miss happened, not which claim to fix. Same gap that keeps
   the 261 unactionable.
4. **Lens ablation on a subset**: drop `mechanism_direction` and measure what is lost.
   That estimates what the standing checker battery — which has no process lens at all —
   is blind to. This is the number that justifies or kills further process-layer
   investment.
5. **Adversarially refute every Critical/Major** before counting, as R55 did. Process
   claims are the most confabulation-prone to audit precisely because they need reasoning.

## Reuse, do not rebuild

`audit/tools/doc_depth_audit.workflow.js` already builds a per-claim ledger with a
coverage denominator (`total_checkable`) and already separates the pointer lens from the
process lens. The semantic flywheel (`/validate-semantic`) already exists. This is a
targeted variant, not new machinery.

## Pre-registered decision rules

- **PROCESS < 5% of defects and ~0 Criticals** → pointer/fact mechanization was the right
  investment; the corpus is healthier than feared. Stop.
- **PROCESS > 20% or carrying most Criticals** → the entire battery addresses the minority
  layer, and the docs-only 29.2% has a mechanism. Process layer becomes top priority, and
  the answer is an LLM-audit cadence, not more deterministic checkers.
- **BINDABLE FACT dominates (the R55 signal, 78%)** → highest-value work is neither
  extreme: finish the role-map / set-index mechanization, which is partly built.
- **Cross-module ≈ within-module** → the locus hypothesis is wrong, and that is a real
  result worth recording; re-target on class (attribution_role) instead of locus.

## Cost

~40-60 agents, ~15-20M tokens, ~1 window, including the ablation subset.

---

# TRACK 2 — the 261 other-falsehood candidates

Full spec: **`audit/other_falsehoods_mining_plan.md`** (pre-registered, unchanged).

**Re-scoped 2026-08-01 after the reordering:**

- **Tier 0 — RUN IT, it is free.** No model calls. Dedup (261 → 219), route by shape to
  existing checkers, then the mechanical doc-trace on confirmed items. Also yields a
  **grader-vs-checker agreement number** on items both saw — the cheapest calibration
  available anywhere in this project, and worth having on its own.
- **Tier 1 — DEPRIORITISED, now gated.** Run only if Tier 0's **non-citation tail**
  surfaces something. Rationale: the pool is ~77% citation drift by crude routing, i.e.
  mostly the pointer layer now measured at ~4% of real defects. Hand-adjudicating 20 LLM
  claims about *answers* is a weaker use of a window than measuring the corpus layer that
  carries the harm.
- **Tiers 2-3 — unchanged, still NOT AUTHORISED**, gates intact.

---

# Standing traps (apply to both tracks)

- **Sample from CLAIMS, not FINDINGS**, when estimating an unmeasured class. A findings
  pool measures what the instruments look for, and process errors are by definition the
  class no instrument binds. R57 recorded this as survivorship.
- **A crash is not a clean run.** `check_gams_citations_impl` raised IndexError on every
  benchmark invocation (needs a positional argv the harness never passed) and its zero
  findings read as a blind spot for a full round.
- **A benchmark seeded with cases your new detector was built for measures the seed
  list.** Report the pre-existing rate separately (41%, not the 57% headline).
- **Verify a RANDOM stratified sample before quoting any rate.** Hand-picked 6/6 implied
  ~100% where a random sample gave 57-67%; a 10-item eyeball put a class at "dominant"
  where the census put it at 0.9%.
- **Adjudicate at the tool's own offset**, never by re-searching its string — that lands
  on a different occurrence and you review text the tool never flagged.
- **Report per class, never pooled.** Today's citation checker had a 100% class and a 20%
  class side by side; the average described neither.
