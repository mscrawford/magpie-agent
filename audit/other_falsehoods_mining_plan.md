# Mining the 261 other-falsehood candidates — a tiered method

**Status: TRACK 2. Tier 0 RUN IT (free). Tier 1 DEPRIORITISED and gated on Tier 0's
non-citation tail. Tiers 2-3 NOT AUTHORISED.** Reordered 2026-08-01 - the lead track is
now `audit/corpus_investigation_plan.md` (cross-module claims, docs-only), because a free
re-analysis of R55 put pointer errors at ~4% of confirmed defects and 0 of the
Criticals/Majors, while this pool is ~77% citation drift by crude routing. Read the master
plan first.
Written 2026-08-01 so the stop rule is fixed *before* any results are seen.

> **Scope decision and its consequence.** Mike authorised a first look: Tier 0 + Tier 1
> only, then stop and report. That is the right shape for "is there anything here" — but
> it has a consequence worth stating plainly, because it changes what the run can
> conclude:
>
> **Tier 1 measures whether the CLAIMS are true. It does not measure whether they are
> CORPUS defects.** A pool that is 60% true could be 60% model confabulation, and the
> unknown-unknown count would still be unknown. The doc-trace (Tier 2) is what converts a
> confirmed answer-falsehood into a finding about the docs.
>
> **Mitigation, adopted, costs nothing:** for a MECHANICALLY confirmed item the doc-trace
> is itself mechanical — grep the claim's identifiers and citations across `modules/`,
> `cross_module/`, `core_docs/`. That half folds into Tier 0 at no model cost, so the
> first look still reports a provisional DOC_DEFECT count. Only judgment-heavy items are
> deferred to a later Tier 2.
>
> So the deliverable of this run is: **claim precision per class (exact on the mechanical
> half, sampled on the rest) + a provisional lower-bound DOC_DEFECT yield.** The Tier 3
> gate cannot be fully evaluated until the judgment-half trace runs; if the provisional
> yield already clears it, that is a lower bound and the gate is met a fortiori.

The arena regrade's un-anchored rubric field ("does this answer assert anything *else*
the code contradicts?") produced **261 items across 77 answers**. `arena_1a_regrade.md`
labels the pool correctly: *a candidate pool, not a result — an LLM claim, unverified,
and at that volume it certainly contains false positives.* Nothing from it has ever been
adjudicated.

It is also the largest untapped source of **unknown-unknowns** in the corpus: unlike every
checker, it was not looking for a class anyone had named.

---

## The reframing that decides the whole design

**These are ANSWER-falsehoods. The goal is CORPUS defects. The link is not automatic.**

A confirmed answer-falsehood has three possible sources:

| source | corpus defect? | what it means |
|---|---|---|
| **DOC_DEFECT** — a doc asserts the same wrong thing | **yes — the prize** | an unknown-unknown, mine it |
| **MODEL_CONFAB** — the answer invented it; docs are fine | no | a model property, not a corpus property |
| **DOC_SILENT** — docs simply don't cover it | weakly | a coverage gap, mildly interesting |

Without a doc-tracing step, mining this pool spends compute confirming that a language
model sometimes confabulates — which nobody doubts and which no doc edit can fix.

**So the yield metric is not "how many claims are true". It is DOC_DEFECTs per 100 pool
items.** Everything below is arranged to get that number as cheaply as possible.

---

## Measured composition (done, free)

```
items                                       261
distinct claim strings                      219   (42 exact repeats)
naming a resolvable file:line               119   46%  <- mechanically decidable
```

Crude class routing (first-match, indicative only): citation/line ~77%, attribution ~9%,
path-existence ~4%, mechanism ~2%, default-value ~2%.

The pool is **dominated by citation defects**, which is the class this project can already
decide without judgment. That is what makes a cheap tier possible — and it is also a
warning: the yield of genuinely *novel* classes may sit almost entirely in the ~23% tail.

---

## Tier 0 — mechanical triage (zero LLM cost, hours)

1. **Dedup** on normalised claim text: 261 → 219.
2. **Route each item to an existing checker** where its shape matches:
   - names a `file:line` → `check_citation_content` / `check_answer_identifiers`
   - "module X does not reference `vm_y`" → a scripted grep against the GAMS tree
   - "no such file / contains only" → `test -e`
3. Emit three buckets: **MECH_CONFIRMED**, **MECH_REFUTED**, **NEEDS_JUDGMENT**.
4. **Mechanical doc-trace on MECH_CONFIRMED** (folded down from Tier 2, 2026-08-01):
   grep each confirmed claim's identifiers and citations across `modules/`,
   `cross_module/`, `core_docs/`. Classify DOC_DEFECT / MODEL_CONFAB / DOC_SILENT.
   Costs no model calls and is what makes a Tier-0-only run able to say anything about
   the CORPUS rather than only about the answers.

**Expected to decide ~119 of 219 (46%) with no LLM in the loop**, and it produces an
unbiased precision estimate on the decidable half — a number no sampling can beat.

*Known overlap, and it is a validity check rather than a nuisance:* at least one pool item
("Line 66 is `q30_crop_reg` … `vm_prod` is only at :14-15") is a defect the citation
checker independently produced today. Agreement between an LLM grader and a mechanical
checker on the same item is the cheapest calibration available — **compute it, and report
it as the pool's mechanical precision.**

**Gate to Tier 1:** none. Tier 0 is cheap enough to run unconditionally.

---

## Tier 1 — precision on the judgment half (~20 items, ~1 window)

Sample **20 items at random, stratified by class**, from `NEEDS_JUDGMENT` only. (Tier 0
already settles the decidable half exactly; sampling it again would waste the budget.)

Rules, each earned the hard way:

- **Stratify by class.** Classes differ by 5x in precision — measured today, 100% for
  `off_by_small` vs 20% for `identifier_absent`. A pooled rate over mixed classes is
  close to meaningless.
- **Random, not chosen.** Hand-picked verification measures your picking: 6/6 implied
  ~100% where a stratified random sample gave 57-67%.
- **Blind re-derivation.** The verifier sees the CLAIM and the answer text, never the
  grader's `why_wrong`. `verifiers.md:403` documents a fresh agent reproducing an
  auditor's exact error; showing the reasoning manufactures agreement.
- **Three outcomes**: CONFIRMED / REFUTED / UNDECIDABLE. Undecidable is a real answer and
  must not be folded into either side.

**Output:** pool precision on the judgment half, with a Wilson interval.

---

## Tier 2 — doc tracing on the JUDGMENT half (NOT AUTHORISED YET)

For every CONFIRMED item from Tiers 0 and 1, ask one question against the docs:

> Does any doc assert the same wrong thing?

Classify DOC_DEFECT / MODEL_CONFAB / DOC_SILENT. This is mostly mechanical — grep the
claim's identifiers and citations across `modules/`, `cross_module/`, `core_docs/` — with
judgment only on near-misses.

**Yield = DOC_DEFECTs per 100 pool items.** Everything before this is instrumentation.

---

## Tier 3 — scale, gated on a threshold fixed NOW (NOT AUTHORISED YET)

Run the full 219 through Tier 1+2 **only if**:

> **Tier 0 + Tier 1 together yield ≥ 8 DOC_DEFECTs per 100 pool items, of which ≥ 3 are
> in classes no existing checker covers.**

Rationale for the second clause: if the yield is all citation drift, the pool is
re-discovering what `check_citation_content` already finds for free, and the correct
action is to run the checker over more answers — not to mine the pool. **The pool is only
worth its cost if it surfaces classes nobody named.**

Recording the threshold before looking is the point. "Is the juice worth the squeeze"
answered after seeing results is not a decision, it is a rationalisation.

**If the gate fails:** record the negative result (the pool is mostly re-discovery),
harvest the confirmed DOC_DEFECTs anyway since they are already paid for, and close it.

---

## Cost

| tier | agents | rough tokens | window |
|---|---:|---:|---|
| 0 mechanical | 0 | ~0 | hours of scripting, no model cost |
| 1 sample (20, blind, 2 verifiers each) | ~40 | ~3M | <1 |
| 2 doc tracing on confirmed | ~15 | ~2M | <1 |
| 3 full 219 (only if gated in) | ~180 | ~25M | 1-2 |

Tiers 0-2 together are well under one weekly window and answer the question
"is there anything here". Tier 3 is the only expensive step and it is gated.

---

## Traps carried forward

- **A grader claim is not evidence.** Every item is an LLM assertion; nothing enters any
  ledger without independent re-derivation. This is the same rule that kept the pool
  untouched, and it is still right.
- **Do not report a pool-wide precision.** Report per class. Today's citation checker had
  100% and 20% classes side by side; the average described neither.
- **Watch for the inverse of the seed-inflation trap.** If Tier 0 resolves mostly items
  the existing checkers already catch, the pool's apparent precision is inflated by
  overlap with tools built for that class. Report novel-class yield separately.
- **A crash is not a clean run.** Any scripted checker used in Tier 0 must have its exit
  code checked — `check_gams_citations_impl` was silently crashing on every seeded-bug
  benchmark run (it needs a positional argument the harness never passed), and its "never
  fired" read as a blind spot for a full round.

---

---

# SPRINT P — RELOCATED

Sprint P was absorbed into **`audit/corpus_investigation_plan.md` → TRACK 1 (Sprint X)**
on 2026-08-01, and amended there rather than duplicated here.

What changed in the move, and why:

- **sampling**: random module docs → **stratified, cross-module arm vs within-module arm**.
  With one arm, "process errors concentrate in cross-module claims" is baked into the
  sampling; with two, it is measurable.
- **regime**: unspecified → **docs-only**, with a normal-regime control cell. Run normally
  this measures 3.1% and reports the model, not the corpus.
- **measures**: doc claims only → **outcome (does a reader get misled) plus a trace back to
  the doc claim that caused it**, so a finding is actionable rather than diagnostic.

The free R55 pointer/fact/process estimate that motivated the sprint is reproduced in the
master plan; the derivation is `audit/integrated/depth_residual_density.json`.
