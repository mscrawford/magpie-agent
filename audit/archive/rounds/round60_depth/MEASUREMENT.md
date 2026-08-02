# Round 60 (depth) — MEASUREMENT

**Date**: 2026-08-02
**Ground truth**: read-only `develop` worktree @ `2c02843ec`
**Role map**: `audit/integrated/depth_rolemap.json`
**Verdict**: **TARGETED_ONLY** — but on a **materially different rationale and a different target set** than R55's. This is not a re-affirmation. See §7.

---

## 0. Read this first: the scope handed to me is not the scope in the brief

The synthesizer prompt (hard-coded at `audit/tools/doc_depth_audit.workflow.js:239`) describes an audit
of **"3 high-stakes hub docs (M10 land, M52 carbon, M56 ghg_policy)"**. The matrix I was handed
contains **one document, `module_34`** — the *urban* module. It is none of the three named hubs.

| | brief says | matrix contains |
|---|---|---|
| docs | `module_10`, `module_52`, `module_56` | `module_34` |
| n | 3 | **1** |
| centrality | ranks #1 / #3 / #7 of 42 (verified in R55) | peripheral — exogenous urban land, 2 realizations, 608 lines |

This matters more than a bookkeeping note, because **the decision rule's core premise is a claim about
which docs were sampled**: *"the hubs are highest-centrality → an UPPER-BOUND sample of corpus bug
density."* That premise does not transfer to `module_34`. Nothing in this round is an upper bound.

The run is nonetheless **internally valid** for the one doc it covered — 5/5 lenses returned, all 19
Critical/Major findings adjudicated, `droppedNoVerdict == 0` — which is why the workflow's validity
guard (added this morning, `995d747` + `f9f7854`) did not fire and no `!! VALIDITY` warning reached me.

> **Gap in the guard, worth fixing before the next round.** `validity.reportable` checks lens coverage
> and refuter coverage *of whatever `DOCS` contains*. It cannot detect that `DOCS` was reduced from the
> planned 9 to 1. A silently under-scoped run therefore passes every check and produces an
> authoritative-looking matrix — the same class of failure as the void run, one level up. Suggested
> guard: assert the doc set against the round's pre-registered manifest, not just against itself.

**Selection was not random.** `module_34` is the smallest doc in the R60 manifest (114 claims vs 364 for
`module_35` and 594 for `module_56`). It is the cheapest to re-run after the spend-limit halt. Cheapest-first
is not adversarial selection, but it is not random either, and it correlates with doc length.

---

## 1. The matrix as handed

Confirmed = survived adversarial refutation (Critical/Major) or auditor-confirmed (Minor/Info).

| Class | Crit | Major | Minor | Info | **Confirmed** | **Denom** | **per 100** |
|---|---:|---:|---:|---:|---:|---:|---:|
| attribution_declare | 0 | 0 | 2 | 0 | **2** | 1 | *see §3* |
| attribution_populate | 0 | 3 | 2 | 0 | **5** | 2 | *see §3* |
| attribution_read | **1** | 3 | 0 | 0 | **4** | 1 | *see §3* |
| citation | 0 | 0 | 3 | 1 | **4** | 33 | 12.1 |
| formula | **1** | 0 | 1 | 0 | **2** | 7 | 28.6 |
| default_value | 0 | 0 | 0 | 0 | **0** | 7 | 0.00 |
| realization | 0 | 0 | 0 | 0 | **0** | 2 | 0.00 |
| mechanism | **2** | 3 | 2 | 0 | **7** | 27 | 25.9 |
| data_flow_direction | 0 | 2 | 0 | 0 | **2** | 8 | 25.0 |
| set_membership | **2** | 2 | 0 | 0 | **4** | 14 | 28.6 |
| other | 0 | 0 | 4 | 3 | **7** | 12 | 58.3 |
| **TOTAL** | **6** | **13** | **14** | **4** | **37** | **114** | **32.5** |

Arithmetic checks out against the per-doc detail: 6+13 = 19 = the Critical/Major count the verifier
adjudicated (`verify__module_34.md`: *"19 bugs adjudicated: 11 UPHELD, 8 CORRECTED, 0 REFUTED,
0 CITATION_FAILED"*). The remaining 18 are Minor/Informational and **carry no adversarial refutation** —
they pass through on auditor confirmation alone (`doc_depth_audit.workflow.js:361`).

**Three separate reasons the bottom-right cell (32.5) must not be quoted.** §2, §3, §4.

---

## 2. The Critical count is inflated ~3x: 6 findings, 2 distinct defects

The matrix counts **prose-key groups** (`normClaim` = doc_line + claim text, `doc_depth_audit.workflow.js:273`).
The workflow computes a second, code-fact grouping precisely to bracket this — and its own comment says
so in terms that this matrix violates:

> `doc_depth_audit.workflow.js:288-289` — *"Carry the range. A point estimate off either key alone is the
> failure mode this exists to prevent."*

**The `dedup` block was computed and then not passed to me.** `measurePrompt()` receives `matrix` and
`perDoc` only (`:454`); `dedup` is returned to the caller (`:470`) but never reaches the synthesizer. I was
handed exactly the endpoint the instrument was designed never to quote alone.

I reconstructed the grouping from the five lens reports on disk. All six Critical findings, with their
matrix classes, resolve exactly:

| # | lens | matrix class | substance |
|---|---|---|---|
| 1 | `citation_formula` BUG-1 | `mechanism` | urban carbon is not all zero |
| 2 | `config_realization` BUG-01 | `set_membership` | urban carbon is not zero |
| 3 | `consumer_read` BUG-1 | `formula` | urban carbon is not zero |
| 4 | `consumer_read` BUG-2 | `attribution_read` | **`vm_land(j,"urban")` consumer set omits M59** |
| 5 | `declare_populate` BUG-1 | `set_membership` | "urban carbon zero" over-generalizes `ag_pools` |
| 6 | `mechanism_direction` BUG-1 | `mechanism` | urban carbon is not all zero |

The class×count match against the matrix is exact (mechanism 2, set_membership 2, formula 1,
attribution_read 1), so the mapping is not a guess.

**Five of the six are one code fact**: `modules/34_urban/exo_nov21/presolve.gms:8` fixes only
`ag_pools` = {vegc, litc}, a proper subset of `c_pools` = {vegc, litc, soilc}; the `soilc` slice is never
fixed and is computed by Module 59. The doc repeats the false blanket claim at **~9 sites** — the
`mechanism_direction` report enumerates `module_34.md:33, :289, :304, :359-368, :473, :474, :545, :585, :593`.

**Why neither dedup key collapses them.** The prose key is keyed on `doc_line`, and the five lenses cited
five *different* doc lines for the same defect. The code-fact key is `path::bug_class`, and the five lenses
assigned the same defect to **three different `bug_class` values** (`mechanism`, `formula`, `set_membership`).
Cross-lens class disagreement defeats both keys simultaneously.

> **Consequence beyond the count: the per-class matrix in §1 is not interpretable.** A single defect
> contributed to three different class rows. Any statement of the form "mechanism errors are the dominant
> class here" is an artifact of how five agents happened to label one error.

**Deduped: 2 distinct Critical defects** — the urban-`soilc` blanket claim, and the `vm_land(j,"urban")`
consumer omission. Applying the same reconstruction to the Majors (the "Upstream Modules: None" claim
appears in 4 lenses; the Module-59 omission in 3; the M39 establishment cost in 2) gives **~13-16 distinct
defects total**, against 37 findings — a **2.3-2.8x** collapse, consistent with the 2.05x the halted run
observed on the `cross_module/` docs.

**Deduped density: ~14/114 ≈ 12.3%** (range 11.4-14.0%), not 32.5%.

**The verifier earned its keep, and shows the auditors' unrefuted claims are not safe.** 0 of 19 were
REFUTED, but **8 were CORRECTED** (42%), and the corrections were substantive: five findings
(`34:1, 34:9, 34:19, 34:24, 34:30`) all asserted urban `soilc` is a *"real, priced CO2 source"*, which
`verify__module_34.md:0.2` shows is **false under the default config** — `c56_emis_policy` defaults to
`reddnatveg_nosoil` (`config/default.cfg:1831`), which excludes urban on both the sector and the `_nosoil`
counts. Applying those five fixes verbatim would have replaced one error with another. The same verifier
downgraded the Critical's M50 half to *"computed but inert"* — only the `"crop"` and `"past"` slices of
`v50_nr_deposition` feed budget equations. **"0 REFUTED" reads as high auditor precision; 42% CORRECTED
with a correlated false sub-claim across five independent lenses is the truer summary.**

---

## 3. The attribution row is a category error, not a rate

**Reported separately, per the standing instruction, and with the standing warning attached:**

> ⚠️ **This is DOC-quality (doc-vs-code) residual density. It is NOT answer quality.** It must never be
> relayed as, alongside, or converted into an answer-quality score. This is the `9.52` failure mode that
> `AGENT.md` § QUALITY GUARD exists to prevent, and the same warning is already carried in
> `audit/integrated/depth_residual_density.json`.

| attribution class | confirmed findings | ledger denominator |
|---|---:|---:|
| `attribution_declare` | 2 | 1 |
| `attribution_populate` | 5 | 2 |
| `attribution_read` | 4 | 1 |
| **total** | **11** | **4** |

**The numerator is 2.75x the denominator.** That is not a high rate; it is evidence the two are not
measuring the same thing. Three contributing causes, all verified:

1. **Omissions have no claim to be counted against.** The ledger counts claims the doc *made*. The largest
   attribution defect here is that **Module 59 is absent from every interaction list in the doc** — a defect
   with no corresponding claim in the ledger, by construction. An enumerator cannot count the claim a doc
   failed to write. Criterion (a) asks specifically about *omissions*, and the denominator structurally
   excludes them.
2. **Numerator and denominator are produced by different agents on different models with no shared
   adjudication** — the ledger is a single `sonnet` pass (`:305`), the findings come from five `opus`
   lenses (`:317`). They share an enum, not a judgment. §2 already showed the opus lenses disagree with
   *each other* on class; agreement with a sonnet enumerator is not to be assumed.
3. **Cross-lens duplication inflates the numerator** (§2) while the ledger is counted once.

**The `attribution_omissions: 11` field in the per-doc detail is mislabeled.**
`doc_depth_audit.workflow.js:390` computes it as `bug_class.startsWith('attribution')` — it counts *all*
attribution-class bugs, phantom and omission alike. It cannot answer criterion (a). Rename or re-derive it.

**Criterion (b)'s attribution arm cannot be resolved at this denominator.** With 4 attribution claims, the
finest resolution available is **25 per 100**. The bar is ~2 per 100. Any doc with a single Major
attribution bug scores 12.5x the bar. The test does not discriminate; it is guaranteed to fire.

---

## 4. The coverage denominator is not reproducible — ±3.8x

This is the finding with the widest blast radius, and it was found by cross-checking this round against the
stored R55 record rather than by anything inside this round.

| | R55 (2026-07-16) | R60 (2026-08-02) | ratio |
|---|---:|---:|---:|
| `module_56.md` ledger | **157** claims | **594** claims | **3.78x** |
| `module_56.md` length | 1162 lines (@ `581e26d`) | 1174 lines | 1.01x |

Sources: `audit/archive/rounds/round55_depth/MEASUREMENT.md:19` (*"498 claims = 135+206+157"*);
`audit/archive/rounds/round60_depth/STATE_R60_INCOMPLETE.md` ledger table.

**The instrument did not change.** `enumeratePrompt()` and its `model: 'sonnet'` were introduced in
`3ddeac4` and are untouched by every subsequent commit to that file (`3cdbbbf` path scrub, `83e54c9` dedup,
`995d747` vacuity guard, `f9f7854` halt record). Same prompt, same model, same document ±1% — **3.8x
different denominator.**

**Every "per 100 claims" figure this program has produced divides by that number.** That includes R55's
headline 5.62/100, R55's corpus extrapolation, this round's 32.5/100, and the per-class rates in §1.
None of them are comparable across rounds.

Counter-evidence, stated because it cuts the other way: `module_34`'s own ledger was re-run within R60 and
moved only 117 → 114 (**2.6%**). So the variance is not uniformly catastrophic — it is *unpredictable*,
which for a denominator is arguably worse than a consistent bias. And this is **one paired cross-round
observation**; it could be an outlier. It is, however, the only paired observation that exists, and 3.8x is
far outside anything a 1% document change explains.

**Practical consequence for the go/no-go**: I do not use per-claim density anywhere in §6-§7. All
extrapolation below is **per-doc**, which needs no claim denominator.

---

## 5. What the prior wide-net pass missed

**First, the criterion's own baseline does not exist.** Criterion (a) asks for findings that "survived the
2026-06-29 wide-net 9.52 pass." There is no such pass to survive. `AGENT.md` § QUALITY GUARD already
records the resolution — the figure *"entered this corpus once, as a single prose sentence, with no
computation behind it,"* then was *"cited 35 times across 14 files."* My own `rg` confirms the citation
spread (16 files today, incl. `audit/BACKLOG.md`, `audit/doc_accuracy_plan.md`,
`audit/archive/rounds/round55_depth/MEASUREMENT.md`). R55 reached the same conclusion at its §0.
*Provenance note: I confirmed the citation spread and read AGENT.md's account this session; I did not
personally re-run the `git log -S` archaeology back to the originating commit.*

**The criterion should be deleted from `doc_depth_audit.workflow.js:263` before the next round.** It has now
consumed synthesizer attention in three consecutive rounds and cannot be satisfied or falsified.

**Second — and this is the real result — there IS a genuine false-negative benchmark for `module_34`, and
depth beat it decisively.** `module_34.md` was audited and cleared by R37 (`ed6324a`, 2026-05-30), whose
commit message reads:

> *"20,34,36,37,40,43,54,80 — completes the 35-module unaudited corpus. **CLEAN: 0 dropped, 0 Critical**,
> max gap 1.48 min. 21 confirmed bugs, 30 edits. … Dominant vein to the end = phantom cost/consumer edges
> (… **M34 omits M56 `vm_carbon_stock` reader**). **Peripheral hubs cleaner than central ones** (0 Critical
> here vs 4 in R33)."*

Depth on the same doc found **2 distinct Criticals**, one of them a categorical false claim repeated at ~9
sites. Three things follow:

1. **The wide-net pass's "0 Critical" was a false negative**, not a clean doc.
2. **It touched the exact variable and missed the error.** R37 fixed M34's `vm_carbon_stock` *reader list* —
   and left standing the doc's blanket claim that the stock those readers read is **zero**. A pass tuned to
   consumer-edge topology stepped over a false statement about the same variable's value.
3. **"Peripheral hubs cleaner than central ones" is an artifact of the wide net's false-negative rate, not a
   property of peripheral docs.** This is the inference that has been steering the program's targeting, and
   the one new doc contradicts it.

---

## 6. Decision-rule evaluation: every criterion is inevaluable or straddling

> **GO if EITHER** (a) ≥1 confirmed Critical-class attribution **omission per hub** surviving the wide-net
> pass, **OR** (b) pooled density > ~1 Critical / 2 docs **OR** > ~2 Major-attribution bugs / 100 attribution
> claims.

| criterion | evaluation | result |
|---|---|---|
| **(a)** ≥1 Critical attribution omission **per hub** | **Zero hubs were audited** (§0). The per-hub quantity does not exist. `module_34` does carry exactly one (the M59 omission from the `vm_land(j,"urban")` consumer set), and it survived R37's "0 Critical" — but it is not a hub, and n=1. The baseline clause is unfalsifiable (§5). | **INEVALUABLE** |
| **(b1)** > ~1 Critical / 2 docs (= 0.5/doc) | `module_34` alone: **2 distinct / 1 doc = 2.0**. Pooled with R55: **3 distinct / 4 docs = 0.75**. Both exceed 0.5. But Poisson exact 95% CI on 3 events over 4 docs = **[0.155, 2.19]/doc** — **the 0.5 bar sits inside the interval.** | **STRADDLES** |
| **(b2)** > ~2 Major-attribution / 100 attribution claims | Not computable here: numerator 6, denominator 4 (§3). On R55's adequate denominator it read 4.55/100 raw, **2.27/100 deduped** — which R55 correctly rejected as undiscriminating on a 2-event numerator. | **INEVALUABLE** |

**No criterion decides.** (b1) trips on the point estimate and fails on its own lower bound. Quoting
"2.0 > 0.5 → GO" would be a label on a threshold-straddling number — the precise failure R55 named at its
§2.4, and the one my standing instructions single out.

---

## 7. Verdict: TARGETED_ONLY — with the targeting rule inverted

**Not GO**, on four grounds: n=1 doc; the pre-registered hub arm never ran, so the round's primary question
(locus: hub vs peripheral) remains unanswered; the deciding interval straddles its bar; and the campaign is
**unfundable as scoped** — R60 halted on a monthly spend limit at 9 docs, while corpus depth is 60 docs
(46 module + 7 `cross_module/` + 7 `core_docs/`) x 5 lenses + verify ≈ **360 Opus agents**. A GO that cannot
be funded is worse than a targeted plan that can.

**Not NO_GO**: the residual is real, adversarially survived, and concentrated in classes no mechanical
checker can see (a false categorical claim about a variable's value; an omitted consumer module).

**But this is emphatically not R55's TARGETED_ONLY.** R55's rested on a specific chain —
*hubs are the upper bound → corpus is 5.5-9.5x below threshold → reserve depth for the top-centrality
quartile*. Every link is now damaged:

1. **The upper-bound premise is falsified in direction.** A peripheral doc returned **2 distinct Criticals**;
   the three top-centrality hubs returned **1 between them**. Per-doc, 2.0 vs 0.33.
2. **The corpus estimate is exceeded by a single doc.** R55 projected ~3-5.5 Criticals corpus-wide.
   `module_34` alone contributed 2.
3. **The independent support for centrality-targeting was a false negative.** R37's "peripheral hubs cleaner
   than central ones" came from declaring this very doc 0-Critical (§5).

**So: keep depth targeted, but stop targeting on centrality.** Centrality is not the predictor the program
assumed, and the evidence that installed it is now retracted.

*Honest weight on this: it rests on one doc. The claim I hold firmly is that the upper-bound premise is no
longer supported — not that peripheral docs are actually worse. Those are different, and only the first is
established.*

---

## 8. Expected corpus Criticals

**Derivation** (per-doc, deliberately avoiding the non-reproducible claim denominator, §4):

```
anchor 1  R55 hubs        1 distinct Critical  / 3 docs  = 0.33 /doc
anchor 2  R60 module_34   2 distinct Criticals / 1 doc   = 2.00 /doc   (6 findings deduped, §2)
                          ------------------------------
pooled                    3 distinct Criticals / 4 docs  = 0.75 /doc

corpus = 46 module + 7 cross_module + 7 core_docs        = 60 docs

point estimate   0.75 x 60  =  ~45 distinct Critical doc-defects
Poisson 95% CI on 3 events  =  [0.62, 8.77] events -> [0.155, 2.19]/doc -> [9, 132]
```

**~45 corpus-wide, 95% CI ≈ 9-132.** The interval spans "a weekend of targeted fixes" to "a campaign larger
than the one just attempted," and I am not able to narrow it at n=4 docs.

Bracketing by anchor rather than pooling: **20** if the hub rate generalizes, **120** if `module_34`'s does.

**This is ~10x R55's projection of 3-5.5**, and the entire difference is the one new document. Two more docs
at `module_34`'s rate would exceed R55's whole-corpus estimate — which is the clearest statement of how much
weight R55's number was putting on the now-falsified upper-bound premise.

**Fragilities, decision-relevant only**: n=4 docs, of which 1 is new; selection was cheapest-first, not
random (§0); the `module_34` distinct-count of 2 is my reconstruction from lens reports, since the
structured records were not passed to the synthesizer (§2) — it is exact on class×count, but it is a
reconstruction; and both anchors count "distinct defects" by different procedures (R55 hand-merged, I
reconstructed).

---

## 9. Recommendation — in reversibility order

1. **Fix the instrument before spending on more measurement.** Three defects, all cheap, all found this
   round, none requiring an Opus agent:
   - Pass `dedup` into `measurePrompt()` (`:454`) so the synthesizer receives the bracket the workflow
     already computes. **This round's headline number was inflated 3x for want of one argument.**
   - Assert the doc set against the round's pre-registered manifest in the validity block, so an
     under-scoped run cannot pass as complete (§0).
   - Delete or rewrite the phantom-9.52 clause at `:263` (§5); rename `attribution_omissions` at `:390`,
     which does not measure omissions (§3).
2. **Measure the denominator before trusting any density again.** Re-run the ledger on 3 docs, 3 times
   each — 9 cheap sonnet calls. If the ±3.8x reproduces, per-claim density must be retired from this
   program's vocabulary in favour of per-doc counts, and the stored
   `audit/integrated/depth_residual_density.json` needs a caveat. This is the highest
   information-per-dollar action available and it costs almost nothing.
3. **Run the pre-registered arm that never ran** — the 3 hubs plus a *randomly selected* module doc — to get
   the locus comparison. Random, not cheapest: this round's selection bias is now a known confound.
4. **Free corpus-wide triage while the above is pending.** The single highest-yield defect here was a
   *categorical absolute* stated doc-wide and false ("carbon set to **ZERO**", "Upstream Modules … **None**").
   That shape is greppable for free. A first pass over 53 docs ranks `module_70` (11 sites),
   `module_22` (11), `module_14` (7), `cross_module/modification_safety_guide.md` (7), `module_30` (6) —
   `module_34` scores 4, i.e. it was **not** the top candidate.
   ⚠️ **This is candidate generation, not verification.** Its only positive control is `module_34` (n=1); it
   has no measured precision and no negative control. Do not report its hits as defects.
5. **Fix `module_34.md` now**, independent of the campaign decision — 37 findings are adjudicated and on
   disk. Apply the verifier's corrections, **not** the auditors' original text: five findings wrongly assert
   urban `soilc` is priced by default, and it is not (§2).

---

## 10. Assumptions that, if wrong, change the conclusion

1. **The distinct-Critical count of 2.** If the five "urban carbon" findings are genuinely independent
   defects (they are not — they are one code fact at five doc sites), `module_34` reads 6 Criticals/doc,
   the corpus estimate goes to ~360, and the verdict flips to GO on magnitude. I weight this very low: the
   five cite one root fact, and the verifier's own §0.1 treats them as one.
2. **The ±3.8x denominator variance is one paired observation.** If `module_56`'s R55 ledger of 157 was the
   anomaly and 594 is correct, then R55's density was overstated ~3.8x, R55's TARGETED_ONLY was reached on
   an inflated numerator-over-understated-denominator, and the corpus is *denser* than either round claimed.
   Either way the comparison is unusable until re-measured; the direction of the error is what changes.
3. **`module_34` is genuinely peripheral.** Verified structurally (exogenous, 2 realizations, smallest doc in
   the manifest), but I did not re-run `audit/tools/compute_module_centrality.py` to place it in the ranking.
   If urban is unexpectedly central, §7's falsification of the upper-bound premise weakens.
4. **0 REFUTED means the numerator is sound.** If the verifier was insufficiently adversarial, the true
   numerator is lower and the case against GO strengthens. The 42% CORRECTED rate argues the verifier was
   working, but "0 refuted across 19" is itself a number worth one skeptical look.
5. **Minor/Informational findings (18 of 37) carry no refutation at all** (`:361`). They are excluded from
   every Critical/Major conclusion above, so this does not affect the verdict — but it does mean the
   32.5% and 12.3% totals are part-unrefuted and should not be quoted as adversarially survived.
