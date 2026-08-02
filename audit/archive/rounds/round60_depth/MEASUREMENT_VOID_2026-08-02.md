# Round 60 (depth) — MEASUREMENT: **VOID RUN**

**Date**: 2026-08-02
**Intended scope**: depth-first per-claim audit, hub arm (`modules/module_10.md`, `modules/module_52.md`, `modules/module_56.md`) plus the planned random within-module arm
**Actual scope**: **zero documents. Zero claims. Zero lenses. Zero verifications.**
**Verdict**: **TARGETED_ONLY** — carried forward unchanged from R55. **This run contributed no evidence and moved nothing.**

> ⚠️ **READ THIS BEFORE QUOTING ANY NUMBER BELOW.** The matrix handed to this synthesizer is
> all-zero with an all-zero denominator. That is **not** a clean bill of health for the hub docs.
> It is the signature of a workflow invoked with an empty argument payload. Recording this run as
> "hubs clean at depth" would be a textbook instance of the failure this whole audit program exists
> to prevent: a reassuring aggregate over an unstated (here, empty) subset. See §2.

---

## 0. Why this file is not named `MEASUREMENT.md`

The canonical slot in this directory is deliberately left empty for the real R60 result. A void run
must not occupy the filename a future reader will treat as R60's finding. When R60 actually runs,
it writes `MEASUREMENT.md`; this file remains as the record of the failed invocation.

The round number itself was **inferred, not supplied**. The output path handed to the synthesizer
was literally `.../round<undefined>_depth/MEASUREMENT.md` under the placeholder repo root that
`audit/tools/doc_depth_audit.workflow.js:23-24` documents as "PLACEHOLDERS and MUST be overridden".
`round60_depth/` exists (empty, created by the R60 setup commit `8ea74a6`), and `8ea74a6` describes
the R60 arm this invocation was meant to execute, so `round60_depth/` is the correct home.

---

## 1. The matrix as handed

| Class | Crit | Major | Minor | Info | Confirmed | Denominator | Density /100 |
|---|---:|---:|---:|---:|---:|---:|---|
| attribution_declare | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| attribution_populate | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| attribution_read | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| citation | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| formula | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| default_value | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| realization | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| mechanism | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| data_flow_direction | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| set_membership | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| other | 0 | 0 | 0 | 0 | 0 | **0** | undefined (0/0) |
| **TOTAL** | **0** | **0** | **0** | **0** | **0** | **0** | **undefined** |

Per-doc detail: `[]`. Pooled `denominator.total`: `0`.

**A residual density with a zero denominator is undefined, not zero.** Both GO criteria are
therefore inevaluable, not failed:

- **Criterion (a)** asks for ">=1 confirmed Critical attribution omission **per hub**". Zero hubs were
  audited, so the per-hub quantity does not exist.
- **Criterion (b)** asks for a rate "per 100 attribution claims checked". Zero attribution claims were
  checked; the ratio has no denominator.

---

## 2. The disambiguation: broken instrument, not a clean corpus

Three independent signals, each sufficient on its own, all read from
`audit/tools/doc_depth_audit.workflow.js` this session:

1. **`per_doc` is empty.** Line 337 builds the per-doc array as `DOCS.map(...)`, and line 353 keys
   `matrix.per_doc` off the same iteration. Every document in `DOCS` produces an entry **even when
   its ledger agent and all five lens agents return null** (line 338 falls back to
   `{ total_checkable: 0, by_class: {} }`; line 339 reads an empty bug bag). An empty `per_doc`
   is therefore only reachable via `DOCS.length === 0`. It cannot be produced by three clean docs.
2. **`DOCS = A.docs || []`** (line 19). No `docs` key in the argument payload means every phase
   iterated an empty list: `parallel([])` in Enumerate (line 282), an empty `auditJobs` array in
   Audit (lines 290-293), an empty Verify pool (line 314). **No agent was ever spawned.**
3. **The output path proves the payload was missing wholesale, not just `docs`.** `R = A.round`
   (line 18) rendered as `undefined`, and `AGENT_DIR` fell back to the placeholder at line 23,
   which only happens when `A.paths` is absent too. Round, docs, and paths were all unset: the
   workflow received no argument object at all.

**The environment was ready; only the invocation was not.** The pinned ground-truth worktree is
present and sits at `2c02843ec`, exactly the SHA the R60 setup commit pinned. The corrected role map
`audit/integrated/depth_rolemap.json` is present and populated. Nothing about the substrate failed.

**Fix**: re-invoke with the payload the header at lines 12-16 specifies:
`{ round: 60, docs: [{path, label, klass}, ...], paths: {agentDir, parent, dev, rolemap} }`.
A cheap guard worth adding first: **abort the workflow when `DOCS.length === 0` or `R` is undefined**,
rather than letting it run to completion and emit an authoritative-looking all-zero matrix. This run
cost a synthesizer invocation and produced an artifact that, filed under the canonical name, would
have been actively misleading for as long as anyone cited it.

---

## 3. The decision rule's "2026-06-29 wide-net 9.52 pass" is a non-measurement

The GO criterion handed to this synthesizer (hard-coded at
`audit/tools/doc_depth_audit.workflow.js:241`) asks whether a finding "survived the 2026-06-29
wide-net 9.52 pass". **There is no such pass to survive, in the sense the criterion needs.**
Re-derived this session with `rg -n "9\.52"` over the repo:

- The figure enters the corpus exactly once as a prose sentence, and `audit/BACKLOG.md:88` records
  the `git log -S"9.52"` trace across all history confirming it: commit `65e32ce` (2026-06-29),
  written by the session that ran the sweep, on the day it ran. **No score sheet, no per-document
  scores, no arithmetic.** No round in `audit/validation_rounds.json` is dated 2026-06-29 or carries
  that mean. Every other occurrence in this repo is a citation of that one sentence.
- The three commits usually cited as its evidence (`ec119a9`, `bb8d543`, `2763330`) contain only fix
  diffs.

So "what the 9.52 pass missed" is **not computable against a score sheet that does not exist.** What
*is* computable is what its fix diffs caught versus what later depth rounds found in the same docs,
and the answer on record is: that pass caught 2 confirmed Major attribution bugs plus 17 Minors
corpus-wide, while R55 later found 28 findings including 1 Critical in **three** of those same docs.
The defensible statement is the one R55 already made: **9.52 measured "few bugs found at that
depth / at that false-negative rate", never "few bugs exist."**

Two corrections to the surrounding record, both re-derived this session:

- R55's own provenance flag (`audit/archive/rounds/round55_depth/MEASUREMENT.md:16`) claims
  `rg "9.52"` over `audit/` returns nothing. **That is false** — it returns matches in
  `audit/validation_rounds.json`, `audit/BACKLOG.md`, `audit/doc_accuracy_plan.md`,
  `audit/seeded_bug_benchmark_2026-07-20.md` and elsewhere. R55 reached the right conclusion by a
  wrong check. `audit/BACKLOG.md:88` already flags this; it is repeated here because the decision
  rule still cites the phantom pass as if it were an instrument.
- The criterion should be rewritten or deleted before the next depth round. As written it invites
  every future synthesizer to treat an anecdote as a baseline.

---

## 4. The decision rule's centrality premise is contradicted by this project's own data

The brief states the premise plainly: *"the hubs are highest-centrality → an UPPER-BOUND sample of
corpus bug density"*, and the NO_GO branch is built on it (*"even the densest docs are clean at
depth"*). **The record does not support that premise.** Two depth rounds, same instrument family,
n=3 docs each:

| Round | Targets | Selection | Claims | Confirmed | **Criticals** | Defect rate |
|---|---|---|---:|---:|---:|---:|
| R55 (2026-07-16) | module_10, module_52, module_56 | 3 **most-audited** highest-centrality hubs | 498 | 28 | **1** | 5.6% |
| R58 (2026-07-17) | module_11, module_29, module_70 | centrality **x audit recency** (stale) | 595 | 46 | **7** | 7.7% |

The less-audited set measured **7x the Criticals** and 1.4x the overall defect rate. R58's own record
flags that the comparison is not clean (R55 imposed a bug taxonomy, R58 was open-ended, so an unknown
share of the delta is method rather than corpus) and argues **the Critical ratio is the more robust
half of it, because both rounds shared severity triggers.** Independently, R58's QA arm found a
Critical in `modules/module_59.md` (dependency set at :1034 omitting both M45 and M52), a module that
round never audited.

The mechanism is not mysterious: **centrality predicts audit attention, and audit attention is what
drives residual density down.** The hubs are the *most-inspected* docs, which makes them a **lower**
bound on corpus density, not an upper one. Any NO_GO reasoned as "the densest docs are clean, so the
rest are cleaner" inverts the actual gradient.

**Consequence for the NO_GO action itself** ("run mechanical-only corpus-wide, reserve semantic depth
for the top-centrality quartile"): R58's structural finding is that the machine-checkable surface is
already clean and defects have migrated to layers checkers cannot parse. Its M29 auditor states the
consequence directly: an audit reading `equations.gms` + `declarations.gms` + `input.gms` and scoring
per-claim **would find zero of that round's Criticals** and would be justified writing the clean-bill
banner. Mechanical-only is cheap and worth running, but it is on record as unable to see the class
that matters most. Reserving depth for the top-centrality quartile compounds the error in §4: it
would spend the depth budget on precisely the docs already measured cleanest.

---

## 5. Extrapolation to the corpus

**None of this comes from this run.** Every input is inherited from R55/R58 and is labeled as such.
Provided because the brief asks for it, at the confidence it actually carries.

**Corpus claim-count basis** (measured this session; re-derivable by
`cat $(ls modules/module_*.md | grep -v notes) | wc -l` and `wc -l` on the audited docs):

- 46 module docs, 48,259 lines total (mean 1,049 lines/doc).
- R55 hubs: 498 claims over 3,303 lines = 0.151 claims/line. R58 targets: 595 claims over 4,338
  lines = 0.137 claims/line. Pooled: 1,093 claims / 7,641 lines = **0.143 claims/line**.
- Corpus module docs ≈ 48,259 × 0.143 ≈ **6,900 code-checkable claims** (bracket 6,600 to 7,300 using
  the two rates separately). Excluding the six docs already depth-audited: ≈ **5,800 un-audited claims**.
- Attribution share, R55's taxonomy only (R58 was open-ended and has no comparable split):
  88/498 = 17.7% → ≈ **1,220 corpus attribution claims** (≈ 1,030 un-audited).

**Expected corpus Criticals** = hub_density x corpus_attribution_claim_count, as the brief specifies,
plus the alternative bases:

| Basis | Rate | x corpus | Point estimate | Exact Poisson 95% CI on the count, rescaled |
|---|---|---|---:|---|
| R55 hubs, attribution-scoped (the brief's formula) | 1 Crit / 88 attribution claims = 1.14 per 100 | 1,220 attribution claims | **≈ 14** | k=1 → [0.025, 5.57] events → **[0.4, 77]** |
| R55 hubs, all claims | 1 / 498 = 0.20 per 100 | 6,900 claims | ≈ 14 | as above |
| R58 stale-but-central, all claims | 7 / 595 = 1.18 per 100 | 6,900 claims | **≈ 81** | k=7 → [2.81, 14.42] events → **[33, 167]** |

**How to hold these numbers.** The two point estimates differ by ~6x and their 95% intervals overlap
only over roughly 33 to 77. The honest summary is **"order 10 to 90 corpus Criticals, most plausibly
a few dozen"**, with three caveats that each matter more than the point estimate:

1. **The hub basis rests on a single event.** A rate built on k=1 cannot discriminate anything; its
   interval spans two orders of magnitude.
2. **The R55 attribution numerator is downranked.** Commit `8ea74a6` records that 9 of R55's 28
   findings, including 3 of 7 Majors and 6 of the 12 attribution findings, name a variable the role
   map had wrong at the time, and that the old map's blankness biased toward reporting omissions that
   were not omissions. It also establishes the delta was **checker improvement, not code drift**
   (0 vars differ between `0d7ebeb90` and `2c02843ec` under the same checker; MAgPIE's interface
   topology has not moved). R55's Critical is not among the affected findings, so the Critical-rate
   basis survives, but the Major-attribution rate does not.
3. **Linear scaling assumes claim density is the only thing that varies across docs.** §4 shows audit
   history varies too, and dominates.

---

## 6. Attribution-class residual, reported separately

**This run produced no attribution measurement.** Confirmed attribution findings: 0. Attribution
claims checked: 0. Residual: **undefined**.

The standing attribution figures are R55's (`0/22` declare, `3/28` populate, `9/38` read; 12 of 28
findings on 18% of claims, a 3.4x enrichment), and per §5 caveat 2 half of them are now
confidence-downranked by the role-map correction. R55's own dedup analysis further reduced its
Major-attribution numerator from 4 to 2 events, giving 2.27 per 100 against a ~2 bar, a
threshold-straddling number whose Poisson interval [0.27, 8.2] swallows the threshold entirely.
**Nothing in the attribution class is currently measured cleanly.** The R60 within-module arm drawn
at random against the corrected map, which is exactly what this void invocation was supposed to
produce, would be the first clean within-module attribution baseline.

> 🚫 **NEVER relay any figure in this section, or any residual density in this report, as an
> answer-quality score.** These are doc-vs-code claim-level measurements. They are not, and cannot be
> converted into, a statement about how well the agent answers questions. The two have been conflated
> before in this project and the conflation is the origin of the 9.52 error. A QA mean over a handful
> of questions is structurally incapable of detecting a 5-8% claim-level defect rate: R58 scored
> 8.375 on the same corpus where its depth arm found 46 defects in 595 claims.

---

## 7. Verdict and recommendation

**Verdict: TARGETED_ONLY** — and the label means only this: *the standing R55 verdict is carried
forward because this run produced nothing capable of moving it.*

Why not the alternatives:

- **GO** is unsupported. Not refuted, **unsupported**: both criteria are inevaluable against a zero
  denominator. Launching a full-corpus semantic campaign on a void measurement would be spending a
  large budget on no evidence.
- **NO_GO** would be worse than unsupported, it would be affirmatively contradicted. Its stated
  rationale is "even the densest docs are clean at depth", which requires the centrality premise §4
  refutes, and its prescribed action (mechanical-only corpus-wide) targets the surface R58 measured
  as already clean while the Criticals live outside it.

**Recommended sequence:**

1. **Re-run R60 with a valid payload.** Add the `DOCS.length === 0 || R === undefined` abort guard
   first, so the next misinvocation fails loudly instead of emitting a confident all-zero matrix.
2. **Select targets by audit recency, not centrality.** §4's gradient says the never-depth-audited
   docs carry the density. The random within-module arm `8ea74a6` planned is the right instrument;
   keep it random, and keep at least one already-audited hub in as a calibration anchor so the two
   arms are comparable.
3. **Rewrite or delete the "9.52 pass" clause** in the GO criterion at
   `audit/tools/doc_depth_audit.workflow.js:241`. It cites an artifact that does not exist (§3).
4. **Re-express the decision rule in intervals, not point thresholds.** Both prior rounds produced
   numerators (1 and 7 events) whose Poisson intervals straddle the "~1 Critical / 2 docs" bar from
   opposite sides. A bar that a 3-doc round structurally cannot resolve will keep producing verdicts
   that flip on a single re-count. Either raise n per round or state the rule as "the campaign is
   warranted unless the upper CI bound falls below X".
5. **Run the free mechanical corpus pass regardless.** It is cheap and it is not in tension with any
   of the above. Just do not let a green mechanical result be recorded as evidence of corpus
   cleanliness; §4 documents exactly why it cannot be.

---

## 8. Provenance

| Claim | Status |
|---|---|
| The run audited zero docs; `DOCS` was empty | **Re-derived this session** from `audit/tools/doc_depth_audit.workflow.js:19, 282-293, 337-353` |
| Ground-truth worktree present at `2c02843ec`; role map present and populated | **Verified this session** |
| `rg "9.52"` returns matches in `audit/`; R55's provenance flag is false | **Re-derived this session** |
| Corpus line counts, claims-per-line rates, corpus claim estimate | **Measured this session**, commands given in §5 |
| Poisson intervals | **Computed this session** (exact chi-square method; k=2 reproduces R55's published [0.24, 7.22], which cross-checks the method) |
| R55 findings, densities, dedup analysis | **Inherited** from `audit/archive/rounds/round55_depth/MEASUREMENT.md` and `audit/validation_rounds.json` R55. Not re-verified. |
| R58 findings (46/595, 7 Criticals), structural finding, QA caveat | **Inherited** from `audit/validation_rounds.json` R58. Not re-verified. |
| Role-map delta and its effect on R55's attribution findings | **Inherited** from commit `8ea74a6`. Not re-verified. |
| "Corpus has ~14 to ~81 Criticals" | **Estimate built on inherited numerators**, one of which is a single event. Not a measurement. Do not cite as one. |
