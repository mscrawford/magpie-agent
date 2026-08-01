# Corpus investigation — master plan, priority-ordered

**Written 2026-08-01. Supersedes the ordering in `other_falsehoods_mining_plan.md`,
which remains the detailed spec for track 2.** Every gate and threshold here is fixed
*before* the corresponding run.

**Amended 2026-08-01 evening, before Sprint X dispatch — no Sprint X data existed when
these changes were made.** Four changes, all from re-deriving the R55 artifact rather than
re-reading the prior summary of it: (1) shares replaced by **rates per claim**, which
halves the apparent process signal; (2) the R55 per-class numerators are **pre-dedup** and
the top of that table is inflated — R55's own verification pass had already retired the
double count; (3) the **lens ablation is replaced** by a battery-vs-LLM diff, because 26 of
28 R55 findings were single-lens and the ablation was therefore near-vacuous; (4) the
Critical census is recorded, along with the rubric property that makes it **partly
definitional** and disqualifies it as a decision variable.

## The reordering, and what caused it

The 2026-08-01 session fixed 25 doc defects. **Every one was a pointer error** — a
citation pointing at the wrong line, or a path naming the wrong realization. Every
checker built that day binds a pointer. Then a free re-analysis of R55's depth audit
(`audit/integrated/depth_residual_density.json`, 3 hub docs, 5 decorrelated lenses, every
Critical/Major adversarially refuted) put that layer in proportion:

```
                share of defects        rate per claim        of 8 Crit+Major
POINTER          1 / 27    3.7%          1 / 89    1.1%             0
BINDABLE FACT   21 / 27   77.8%         21 / 221   9.5%             6
PROCESS          5 / 27   18.5%          5 / 128   3.9%             2
```

**Pointer errors are ~4% of confirmed defects and zero of the serious ones.** A day of
work had been spent hardening the layer that carries almost none of the harm. (Lead, not
result: n=27, one round, the most-audited hub docs, and the lens set determines what is
found. The 1-item gap against 28 reported confirmed is unreconciled and flagged.)

**The rate column was added 2026-08-01 and it moves the conclusion.** The share column
divides by *findings*; the rate column divides by *claims of that kind*, which is the
denominator that exists. On shares, PROCESS looks 5x the pointer layer. On rates it is
3.5x — same direction, half the size — and BINDABLE dominates on both. **Any threshold
stated as a share of findings is measuring how many claims of each kind the doc happens to
make, not how wrong they are.** The pre-registered rules in this plan were rewritten on
that basis (see *Pre-registered decision rules*).

Per class, from the same artifact:

```
attribution_read       9 / 38   23.7%    the only Critical + 3 of 7 Majors
set_membership         7 / 44   15.9%
attribution_populate   3 / 28   10.7%
data_flow_direction    3 / 47    6.4%
formula                2 / 50    4.0%
mechanism              2 / 81    2.5%
citation               1 / 89    1.1%    largest claim class, lowest yield
attribution_declare    0 / 22 | default_value 0 / 36 | realization 0 / 3 | other 1 / 60
                      ----------------
TOTAL                 28 / 498   5.6%
```

⚠️ **These numerators are PRE-DEDUP and the top of the table is inflated.** R55's own
verification pass retired a double count that this JSON still carries:
`round55_depth/MEASUREMENT.md:65-79` merges M52 bugs 1/5/10 into one defect ("three views
of one defect" at `module_52.md:458`) and merges M52-4 with M56-7 (one code fact, two doc
sites). Deduped, the attribution numerator is **2 events, not 4**, on a Crit+Major basis —
so `attribution_read` sits somewhere in **5.3%-23.7%**, not at 23.7%. The five Minors in
that class were never dedup-audited.

**What survives the dedup is the ORDERING, not the magnitudes.** Even the floor of the
attribution range is ~5x the citation class, and `citation` is untouched by the merge (it
had one finding). What does NOT survive is any point estimate: MEASUREMENT.md §2.4 already
recorded that a rate built on 2 events has a Poisson 95% CI of roughly [0.27, 8.2] per 100
and "cannot discriminate against a ~2 per 100 bar". Carry the range or carry nothing.

⚠️ **Third caveat, found 2026-08-01 during R60 setup: R55's attribution findings were
produced against a role map with 26 known defects.** The role map is the code-derived
ground truth every lens agent is told to check FIRST for any DECLARED/POPULATED/READ claim
(`doc_depth_audit.workflow.js` ROLEMAP_CLAUSE, billed as "~0-FNR on this class"). It was
regenerated for R60, and the delta was decomposed:

```
CHECKER effect  (same SHA 0d7ebeb90, R55 checker vs current):  26 vars differ
CODE    effect  (same checker, 0d7ebeb90 vs 2c02843ec):         0 vars differ
```

**All of it is checker improvement; MAgPIE's interface topology did not move at all.**
Mostly 13 `fm_*` vars plus `pm_climate_class` that R55's map carried as
`declared_in: None`, and several wrong `populated_by` entries. The old map was *blanker*,
which biases toward reporting omissions that were not omissions.

**9 of R55's 28 findings — including 3 of the 7 Majors — name a variable the map had wrong
at the time.** Six of those are attribution-class, i.e. half the attribution findings.
The Critical is **not** among them (`pm_carbon_density_secdforest_ac_uncalib` was mapped
correctly), so it stands on this axis.

This downranks confidence; it does not void the findings — the map is a first reference
that agents must confirm with a both-endpoints grep, and the Majors survived adversarial
refutation. But stacked on the dedup caveat, **R55 is no longer a clean baseline for the
attribution classes.** R60's within-module arm, drawn at random against the corrected map,
becomes the first clean within-module baseline this project has, and should be quoted as
the comparator rather than R55 once it exists.

At the same time, the arena's only two significant effects both point the same way:

```
class = attribution_role   28.1%  vs  4.2% all other classes   p = 0.0012
regime = docs-only         29.2%  vs  3.1% normal              p = 0.0157
```

**Attribution-role IS a cross-module claim** — who declares vs. populates vs. reads a
variable across module boundaries. The class effect and the process layer are the same
finding reached from two directions, and nothing else in the arena exceeds ~4%.

## The Critical census, and why it proves less than it looks

Classified 2026-08-01 by reading every Critical in the last three rounds that ran an
adversarial LLM doc audit — **R55** (depth-first, most-audited hubs), **R58** (open-ended
taxonomy, stale hubs), **R59** (split QA; both its Criticals are *latent*, rubric §1.5).
R56 was mechanization-only and R57 was instrument integrity; neither graded findings.

**10 Criticals across 3 rounds. All 10 are structural — wrong module topology, a
fabricated entity, or wrong mechanism semantics. None is a pointer error.**

| round | n | what they are |
|---|---:|---|
| R55 | 1 | `module_52.md:458` consumer set {29,32}; true {14,29,32,35} |
| R58 | 7 | M11-F3/F4 (urban costs → M10, cropland costs → M30; both wrong owner, while the doc's own machine-checkable catalog was correct) · M11-F5 (`vm_cost_trade_feasibility` claimed fixed at 0 in `selfsuff_reduced_bilateral22`; live equation there) · M29-F1 (`pm_carbon_density_soilc` exists nowhere and is the closing arrow of a **fabricated feedback loop**) · M29-F9 ("Provides To" names 5 + a hedge; true set ≈11, M22 arrow reversed) · M70-F1 (`vm_feed_balanceflow` documented "internal"; M71's *default* realization reads it twice) · M70-F3 (M36 missing from the `vm_cost_prod_livst` consumer set; the 70→36→70 cycle is real and unlisted) |
| R59 | 2 | `module_70_notes.md` asserts M70 *reads* `vm_costs_additional_mon`, in the entry written to prevent that misattribution · `module_52.md` never received R58's `stockType` correction (`m_carbon_stock_ac` as additive sum vs. mutually-exclusive dispatch) |

Under a stricter reading — the reader's *causal* model is wrong, not just an edge
misassigned — it is 6 of 10 (M29-F1, M29-F9, M70-F1, M70-F3, M11-F5, stockType).

**⚠️ It is substantially definitional, and must never be quoted without this.**
`flywheel_rubric.md:18-27` lists nine Critical triggers; seven are topology / existence /
mechanism-shaped, and **citation drift is routed to Major by fiat** (`:40-41`), off-by-few
to Minor (`:56`). A pointer error *cannot reach Critical* under this rubric. So "0 of the
Criticals were pointer errors" is closer to a rubric property than a discovery — **and
that weakens the "0 of 8 Criticals+Majors" line above for its Critical half.** (The Major
half is empirical: citation drift IS an explicit Major trigger and none of R55's 7 Majors
was one.)

The residual empirical content is thin but real: two Critical triggers are value-shaped
(inverted Boolean default; mechanism claimed active when off by default) and **none of the
10 fired on those**. Also mine, single-pass, n=10, by a classifier who already knew this
plan's thesis. Treat as a lead.

**What it does license for Sprint X:** the harm concentrates in *interface attribution* —
who reads what, in which direction, whether the edge exists at all. All 10 Criticals are
that. `attribution_read` (5.3%-23.7%) and the arena's `attribution_role` (28.1%) are the
same class measured by two instruments that share no code.

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
| **lens** | all 5 from `doc_depth_audit.workflow.js`, reported per lens | a lens is an ENTRY POINT, not a taxonomy — see below |

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
4. **Report the two axes separately: lens (entry point) and class (what the defect is).**
   They do not agree, and conflating them is what made the original ablation design wrong.
   R55 per lens (a finding may be credited to more than one):

   ```
   mechanism_direction   8 findings   Crit 1, Maj 1     highest-yield lens
   declare_populate      7            Crit 1, Maj 1
   config_realization    7            Maj 2, Info 1
   consumer_read         5            Crit 1, Maj 1
   citation_formula      5            Maj 2             but 3 of its 5 were attribution_read
   ```

   `mechanism` is the second-*cleanest* class (2.5%) while `mechanism_direction` is the
   highest-yield *lens*. Both are true: the lens brief tells the agent to open both
   endpoints and walk causal direction, so it finds attribution, set-membership and
   formula defects — not "mechanism" defects. Symmetrically, **the pointer lens is mostly
   a delivery vehicle for non-pointer findings** (3 of 5). That is the sharpest available
   statement of what the deterministic battery lacks: not a process lens, **the traversal**.
   A checker that validates a citation finds citation drift; an agent that *walks* the
   citation to its endpoint finds the attribution error at the other end.

5. **ABLATION REPLACED — the pre-registered lens ablation is near-vacuous.** In R55, **26
   of 28 findings were credited to exactly ONE lens**; only 2 had multi-lens overlap. With
   near-zero redundancy, dropping lens L loses ~exactly L's findings, so the ablation
   re-reports the per-lens counts and resolves nothing. The per-lens spread (5-8 findings)
   is inside Poisson noise anyway.

   **Run instead: a battery-vs-LLM diff on the same claim ledger.** Execute the standing
   deterministic checkers over the identical docs and set-difference their findings against
   the lens agents'. That answers the question the ablation was *for* ("what is the standing
   battery blind to?") directly, costs no model calls on the battery side, and yields a
   per-class blind-spot map instead of a single number. Keep the per-lens report as a
   descriptive byproduct, not as an arm.

   Recorded as a rejected option, with its reason, so the next session does not re-derive it.

6. **Adversarially refute every Critical/Major** before counting, as R55 did. Process
   claims are the most confabulation-prone to audit precisely because they need reasoning.

7. **Dedup before any rate is quoted.** R55's headline artifact still carries a double
   count its own verification pass retired (three views of one defect at one doc line).
   One defect = one code fact, however many doc sites or lenses surfaced it. Report
   `findings`, `distinct defects`, and `doc sites` as three separate numbers.

## Reuse, do not rebuild

`audit/tools/doc_depth_audit.workflow.js` already builds a per-claim ledger with a
coverage denominator (`total_checkable`) and already runs the 5 lenses
(`workflow.js:71-75`). The semantic flywheel (`/validate-semantic`) already exists. This
is a targeted variant, not new machinery.

It already records `bug_class` and `lenses` per finding (`workflow.js:108-111,342`) and
already dedups — but **on the wrong key, and at the wrong scope**, which is exactly why
R55's retired double count is still live in the JSON:

```
workflow.js:251-253   normClaim(b) = doc_line :: first 80 chars of claim text, lowercased
workflow.js:277-287   dedup is PER DOC, across lenses
```

Two failure modes follow directly, and both are the ones MEASUREMENT.md retired by hand:

- **Same defect, different phrasings, same doc line.** M52 bugs 1/5/10 are one defect at
  `module_52.md:458`; the claim strings differ, so three keys survive. Keying on claim
  *text* cannot collapse them.
- **Same code fact, two doc sites, two docs.** M52-4 ≅ M56-7 is one parallel-not-serial
  error verified from both ends. The dedup is per-doc, so a cross-doc duplicate is
  **structurally uncatchable** — no amount of key tuning reaches it.

**Fix before dispatch (small, and it is the difference between a rate and an artifact):**
key on the *code fact* — `file_evidence` normalized to file+identifier, plus `bug_class` —
not on claim prose; and run a second dedup pass **across docs** after the per-doc one.
Then emit `findings`, `distinct defects` and `doc sites` as three separate counts, because
they are three different numbers and only the middle one belongs in a rate.

## Pre-registered decision rules

**Rewritten 2026-08-01, before any Sprint X data exists.** The prior rules were stated as
*shares of findings* ("PROCESS > 20%"); a share divides by the finding count, so it moves
when the doc simply makes more claims of one kind. All rules below are **defect rate per
claim of that class, with an interval**, and the interval is part of the rule.

**Power first, so a null is interpretable.** At a ~6% corpus rate, an exhaustive
`cross_module/` ledger yielding ~500 claims produces ~30 findings. Split three ways that
is ~1-20 events per layer; the Poisson 95% CI on 6 events is roughly [2.2, 13.1], i.e.
7%-44% of 30. **A share-based 5%-vs-20% threshold is not decidable at this n — the old
rules could not have fired correctly in either direction.** Rates fix this because the
denominator is claims (hundreds), not findings (tens).

- **Decide on the interval, never the point.** A rule fires only if the 95% interval
  excludes the threshold. If it straddles, the recorded result is **UNDECIDED at this n**,
  with the n needed to decide it. That is a real outcome and must be reported as one, not
  rounded to the nearer branch. (`MEASUREMENT.md:88-90` is the anchor: "a label on a
  threshold-straddling number ... flips under any reasonable re-count".)
- **PROCESS rate ≤ pointer rate (both ~1-2 / 100 claims), interval-separated from
  BINDABLE** → pointer/fact mechanization was the right investment. Stop. *(This is what
  R55 actually shows once rates replace shares: PROCESS 3.9% vs POINTER 1.1% vs BINDABLE
  9.5%.)*
- **PROCESS rate reaches BINDABLE's, or carries Criticals that survive refutation** → the
  battery addresses the minority layer and the docs-only 29.2% has a mechanism. Process
  becomes top priority; the answer is an LLM-audit cadence, not more checkers.
- **BINDABLE FACT dominates by rate (the R55 signal — and the Critical census points the
  same way)** → the expected result. Highest-value work is neither extreme: finish the
  role-map / set-index mechanization, which is partly built. **Prioritise by class within
  it: `attribution_read` first** (the only class carrying Criticals in both R55 and the
  arena), then `set_membership`.
- **Cross-module ≈ within-module** → the locus hypothesis is wrong, a real result worth
  recording; re-target on class (`attribution_role`) instead of locus.
- **Battery-vs-LLM diff finds the battery blind in classes it nominally covers** →
  the problem is checker FNR, not coverage. `check_consumer_attribution` is the standing
  suspect: R58 measured it the *worst* checker at 74.8% mutation survival despite being
  retrofitted first. Fixing an existing checker beats adding an LLM cadence.

**A Critical count is a weak instrument here and is not a decision variable.** The rubric
makes pointer errors ineligible for Critical by construction, so "Criticals are structural"
cannot discriminate between hypotheses. Report Criticals; decide on rates.

## Cost

~40-60 agents, ~15-20M tokens, ~1 window. The ablation subset is dropped; the
battery-vs-LLM diff that replaces it costs no model calls, so the freed budget goes to the
claim ledger — which is where the denominators come from, and denominators are what the
rewritten decision rules run on.

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
- **A share of findings is not a rate.** Dividing by the finding count measures how many
  claims of each kind the doc makes, not how wrong they are. Always divide by the claims of
  that class. This flipped the apparent size of the process signal by 2x.
- **Re-derive from the artifact, not from the prior summary of the artifact.** The
  pre-dedup inflation, the near-vacuous ablation and the lens-vs-class conflation all
  survived a full session inside a summary that read as settled, and all three fell out of
  one pass over `depth_residual_density.json` and `MEASUREMENT.md`. A summary carries the
  conclusions and drops the caveats that would have qualified them.
- **A lens is an entry point; a class is what the defect is.** They are different axes and
  they disagree. `mechanism_direction` is the highest-yield lens and `mechanism` is nearly
  the lowest-yield class, simultaneously and without contradiction.
- **Check whether a severity tier can even express the hypothesis before testing it on
  severity.** The rubric routes pointer errors away from Critical by fiat, so "Criticals
  are structural" was ~unfalsifiable. Read the rubric's triggers before using its tiers as
  evidence.
