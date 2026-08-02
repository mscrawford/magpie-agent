# R60 depth — MEASUREMENT: `cross_module/carbon_balance_conservation.md`

**Docs audited this run: 1.** Lens coverage 5/5. Refuter ran. `CITATION_FAILED = 0`, `REFUTED = 0`.
**Verdict: TARGETED_ONLY.** The instrument works; the *measurement plumbing* has two defects that
make part of the returned matrix uncomputable and inflate its Critical cell 3x. Both are cheap to
fix and must be fixed before any sweep is bought.

Sources re-derived this session: `audit/archive/rounds/round60_depth/_checkpoint_audits.json`
(67 bug records + the 210-claim ledger), `audit/archive/rounds/round60_depth/verify__carbon_balance_conservation.md`
(21 adjudications), `audit/validation_rounds.json` (prior exposure), doc line counts measured directly.

---

## 0. Headline: three numbers, and only one of them is a rate

| quantity | value | 95% CI (Wilson) | refuted? | reportable as a rate? |
|---|---:|---|---|---|
| raw finding records / claims | **67/210 = 31.9%** | [26.0%, 38.5%] | C/M only | **No** — contains 1.97x duplication |
| distinct doc-line anchors / claims | **34/210 = 16.2%** | [11.8%, 21.8%] | C/M only | Partly — Minor/Info half unrefuted |
| **Critical+Major distinct, refuted / claims** | **12/210 = 5.7%** | **[3.3%, 9.7%]** | **yes** | **Yes — this is the round's result** |
| Critical distinct, refuted / claims | **1/210 = 0.5%** | [0.1%, 2.6%] | yes | Yes, but n=1 defect |
| Minor/Info anchors not shared with C/M | 22/210 = 10.5% | [7.0%, 15.4%] | **no** | No — below the project bar |

Denominator for every cell above: **210 checkable claims**, the full ledger, against a **full 5/5 lens
numerator**. This is the one thing that is clean here — unlike the halted run recorded in
`audit/archive/rounds/round60_depth/STATE_R60_INCOMPLETE.md`, there is no partial-numerator /
full-denominator bias in this doc.

---

## 1. The returned matrix reports records, not defects — Critical is inflated 3x

The matrix cell `attribution_read / Critical = 3` is **one defect**, found three times.

Bugs `:15`, `:42`, `:54` all anchor to doc line `:180` and all describe the same omission (module 32
and module 14 missing from the calibrated-`pm_carbon_density_plantation_ac` reader set). The refuter
merged them explicitly. Three lenses — `consumer_read`, `citation_formula`, `mechanism_direction` —
found it independently, which is evidence the *detector* is reliable and is **not** evidence the doc
has three Criticals.

Deduplication across the whole set, by doc-line anchor:

```
raw finding records                 67
distinct doc-line anchors           34        collapse 1.97x
anchors carrying >1 record          19        (51 of the 67 records)

Critical      3 records ->  1 distinct defect     (3.0x)
Major        18 records -> 11 distinct defects    (1.6x)
Crit+Major   21 records -> 12 distinct defects    (1.75x)
Minor+Info   46 records -> 28 anchors, 22 of them not shared with a C/M anchor
```

**Anchor dedup is validated against expert dedup on the subset where both exist.** The refuter
independently merged the 21 Critical/Major records into groups by reading the code facts. Its groups
and the line-anchor partition agree **exactly, 12 for 12**, once `:869-872` and `:870` are recognised
as the same claim block (the refuter merged `:3/:17/:55` across that split). That licenses applying
anchor dedup to the unrefuted Minor/Info half with moderate confidence — the 22 figure above, not
46, is the right order.

Worst duplication: doc line `:734` (the SOM 44%-vs-56% slip) drew **five** records, one from each of
the five lenses.

### Arithmetic defect in the verification artifact

`verify__carbon_balance_conservation.md` states *"Twenty-one bug records describe **thirteen**
distinct defects."* Its own enumerated merge groups give **twelve**:

```
named groups : {1,16,30,56} {2,19} {3,17,55} {15,42,54} {21,31}  = 5 groups, 14 records
singletons   : 4, 18, 20, 22, 43, 44, 57                          = 7
distinct     : 5 + 7 = 12
```

Naive line-anchor dedup also returns 13, but only because `:869-872` and `:870` split — a coincidence,
not corroboration. **Use 12.** Flagged rather than silently corrected because 13 is the kind of number
that gets quoted; this is the failure mode `AGENT.md` Rule 4 exists to catch.

---

## 2. Per-class rates are NOT computable. Refused.

The matrix invites a rate per class. Two cells prove the two taxonomies are not the same partition:

| class | finding records | distinct anchors | ledger denominator | rec/den |
|---|---:|---:|---:|---:|
| `citation` | 8 | 5 | **2** | **400%** |
| `formula` | 16 | 9 | **12** | **133%** |

`citation` survives dedup at 5 distinct anchors against a denominator of 2 — so duplication does not
explain it. The lens agents assign `bug_class` per finding; the enumerate agent assigns a class per
ledger claim; **they disagree about which class a given claim belongs to.** Mass has therefore moved
between classes, which means *every* per-class pairing is suspect — not only the two that happened to
overflow and expose themselves.

Full table, reported as **counts with their denominators, not as rates**:

| class | records | distinct anchors | ledger claims |
|---|---:|---:|---:|
| `attribution_declare` | 1 | 1 | 3 |
| `attribution_populate` | 5 | 3 | 30 |
| `attribution_read` | 11 | 5 | 19 |
| `citation` | 8 | 5 | 2 ⚠ |
| `formula` | 16 | 9 | 12 ⚠ |
| `default_value` | 5 | 4 | 15 |
| `realization` | 0 | 0 | 1 |
| `mechanism` | 9 | 5 | 45 |
| `data_flow_direction` | 1 | 1 | 20 |
| `set_membership` | 10 | 7 | 25 |
| `other` | 1 | 1 | 38 |
| **total** | **67** | **34** | **210** |

**What would decide it — n is not the binding constraint here, structure is.** The ledger stores only
`by_class` *counts*; it carries no claim identifiers. No sample size fixes that. The fix is one schema
change: emit the ledger as a list of claim records with IDs, and require each finding to name the claim
ID it falsifies. Then numerator and denominator bind per claim and per-class rates become computable at
the n already collected. Until then, per-class rates on this corpus are **UNDECIDED at any n**.

---

## 2b. The denominator is itself an unmeasured detector — ledger coverage

Everything above conditions on **210 being the doc's checkable-claim population.** It is not ground
truth; it is the output of the enumerate agent. Precision and recall of the *lenses* are visible in this
round (0 REFUTED, 0 CITATION_FAILED). **Coverage of the ledger — the fraction of the doc's real
checkable claims it enumerated at all — was never measured, and a claim the enumerator silently
declined leaves no artifact to grep.**

This is not hypothetical for the comparisons in §6 and §7. Claims-per-line across the 9 ledgers:

```
water_balance        0.096      <- thinnest
circular_dependency  0.106
modification_safety  0.139
module_34            0.188
carbon_balance       0.209      <- this doc
land_balance         0.219
module_35            0.297
nitrogen_food        0.366
module_56            0.506      <- 5.3x the thinnest
```

A 5.3x spread is consistent with genuine variation in claim density **or** with variation in enumerator
recall, and this round cannot separate them. The direction of the risk is unfavourable: a thinner ledger
is a **smaller denominator**, which **inflates** that doc's measured rate. So part of the cross-doc
gradient in §6 may be an enumerator artifact rather than a doc-quality signal, and the corpus
extrapolation in §7 — which scales by *line count* — assumes a per-line claim density that varies 2.7x
across the only three module ledgers that exist.

**How to measure it, cheaply, before the sweep:** mutate real, already-correct claims in the live doc
(not synthetic fixtures — hand-written seeds inherit the shapes the enumerator already handles), verify
each mutant is genuinely a defect, re-run the enumerator, and report the fraction of seeded claims its
ledger contains. Include a delta-0 control: run the unmutated doc and confirm the ledger is unchanged.
Report coverage next to the rate, and classify the declined population before trying to widen anything —
some prose ("see the module docs for details") asserts nothing enumerable, and that ceiling is a real
answer, not a gap to close.

Until that exists, every rate in this report should be read as **"per enumerated claim"**, not "per
claim", and cross-doc rate comparisons carry an unquantified denominator confound.

---

## 3. Attribution classes — reported separately

**These are defect counts against a claim ledger. They are not an answer-quality score, they do not
convert into one, and they must never be relayed as one or alongside one.** A doc-claim defect rate and
a flywheel Q&A score measure different objects; the R55 record already carries an unreconciled 1-item
gap from conflating adjacent quantities.

| class | records | severity mix | distinct anchors | ledger claims |
|---|---:|---|---:|---:|
| `attribution_declare` | 1 | 1 Minor | 1 — `:512` | 3 |
| `attribution_populate` | 5 | 5 Minor | 3 — `:101, :263, :547` | 30 |
| `attribution_read` | 11 | 3 Critical, 4 Major, 4 Minor | 5 — `:180, :518, :547, :573, :593` | 19 |
| pooled attribution | 17 | | 8 | 52 |

Two observations that survive the taxonomy problem, because they are within-class comparisons:

1. **All severity concentrates in `attribution_read`.** Every Critical and 4 of 18 Majors are READ-side
   consumer-set omissions. `attribution_declare` and `attribution_populate` produced only Minors. This
   reproduces the direction R55 and the arena both reported, from an instrument that shares no code with
   either — but it is one doc, and it is a *rank* agreement, not a magnitude one.
2. **17 attribution records collapse to 8 anchors** (2.1x), the highest duplication of any group. Read
   the raw attribution counts as roughly half what they appear.

---

## 4. The confirmation bar validates the defect, not the remedy

New this round, and not represented anywhere in the matrix:

| quantity | value | 95% CI |
|---|---:|---|
| C/M records whose **fix text** the refuter had to correct | **5/21 = 23.8%** | [10.6%, 45.1%] |
| Critical records carrying a fix that would introduce a **new** error | **2/3** | [20.8%, 93.9%] |

Bugs `:42` and `:54` both proposed adding `modules/32_forestry/dynamic_may24/preloop.gms:18,56` to the
calibrated-curve reader list. That is wrong on phase ordering (module 32's preloop precedes module 52's
preloop calibration), and `:56` sits in a non-default compile branch. Applying either would have
substituted one attribution error for another. Bug `:15`, the same defect, has the safe fix.

`REFUTED = 0` therefore reads as high auditor precision and **is not**. The correct summary is: *the
defect-detection is accurate; the remedy-generation is wrong about a quarter of the time on
Critical/Major.* The identical pattern was recorded for `module_34` (8 of 19 CORRECTED, 42%) — two docs,
same direction. Any fix pass that applies findings without re-derivation inherits this rate.

---

## 5. Refutation coverage — 46 of 67 records are below the bar

`isConfirmed()` requires a surviving refuter verdict only for Critical/Major. The 21 C/M records were
adjudicated (16 UPHELD, 5 CORRECTED, 0 REFUTED). The **40 Minor and 6 Informational records passed on
auditor confirmation alone.** They are 69% of the record count and 22 of the 34 distinct anchors.

Consequence: the 16.2% distinct-anchor figure is a **mixed-evidence quantity** — its C/M component
cleared an adversarial pass, its larger Minor/Info component did not. Only the 5.7% C/M line clears
this project's stated bar. Given that refutation CORRECTED 24% of what it touched, assume the
unrefuted 22 anchors contain a comparable share of mis-stated findings.

---

## 6. Placing this doc on the gradient — the convention choice dominates

`cross_module/carbon_balance_conservation.md` appears in **9 prior round records** — R7, R30, R46, R48,
R49, R51, R53, R54, R59 — including a targeted rewrite in R54. On audit attention it sits at the
**high-exposure end**, the same end as R55's "most-audited hubs". Its selection this run was as a member
of the cross_module **census arm** (all 6 substantive docs), first in dispatch order — not a random draw
and not a centrality ranking.

| round | docs | claims | measured | Criticals |
|---|---|---:|---|---:|
| R55 | 3 most-audited hubs | 498 | 5.6% | 1 |
| R58 | 3 stale hubs | 595 | 7.7% | 7 |
| R60 | `module_34`, never audited | 114 | 19–32% | 6 (raw records) |
| **R60 here** | `carbon_balance_conservation`, 9 prior rounds | **210** | **5.7% / 16.2% / 31.9%** | **1 distinct (3 raw)** |

**Against a matched convention, this doc measures well above R55's hub density despite comparable prior
attention:** 31.9% vs 5.6% on raw records (5.7x), or 16.2% vs 5.6% if R55's 28 was already deduped
(2.9x). The direction holds across both readings, so it is robust to the one convention ambiguity I
cannot resolve from the R55 record.

**Three caveats that must travel with that ratio, and they are not small:**

1. **Instrument confound, the same one that voids R55-vs-R58.** R55 used a different lens set; R60 uses
   an exhaustive claim ledger plus 5 lenses. `audit/corpus_investigation_plan.md` states the point
   directly — *"a lens is an ENTRY POINT, not a taxonomy"* — and the lens set determines what is found.
   The ratio is confounded with instrument and is **not** a clean measurement that this doc is worse
   than R55's hubs.
2. **The gradient table mixes dedup conventions row-wise.** R55, R58 and the `module_34` row predate the
   dedup introduced this round. `module_34`'s "6 Criticals" is a **raw record** count whose dedup status
   is not stated in its verify artifact — and the earlier measurement for that doc says it carries
   *"exactly one"* Critical attribution omission. If `module_34`'s 6 deflates the way this doc's 3
   deflated to 1, the whole gradient's Critical column shifts. **Do not compare the Critical columns
   across those rows until they are recomputed under one convention.**
3. Prior exposure was measured by mention in round records, not by claim coverage. Nine mentions is not
   nine exhaustive sweeps; most were flywheel Q&A rounds finding 1–6 bugs each.

---

## 7. Extrapolation to the corpus — every inherited numerator named

**This rests on a single event: one doc, one round.** Stated in the same sentence, as required.

**Denominator.** Claim density measured on the 9 ledgers that exist:

```
cross_module (census, 6/6 docs)   874 claims / 5,306 lines = 0.165/line   MEASURED
modules/     (n=3 ledgers)      1,072 claims / 3,009 lines = 0.356/line   spread 0.188-0.506 (2.7x)
core_docs    (n=0 ledgers)                                                UNMEASURED
```

Applying the module range to 48,703 lines of `modules/*.md` and 3,273 lines of `core_docs/`:

```
corpus claims  ~10,600 - 27,200      point ~19,400
```

**Numerator.** This doc's refuted distinct-Critical density: **1/210 = 0.48%, Wilson [0.08%, 2.65%]**.

```
corpus Criticals   point ~92      sampling-only CI  16 - 513
```

**Why that interval is a floor on the real uncertainty, in three independent ways:**

- The Wilson interval is **binomial sampling error within one doc**. Between-doc variance is the
  dominant term for a rare event and is **completely unmeasured at n=1 doc**.
- The denominator itself carries a 2.6x range built from 3 module ledgers.
- Per the measured gradient, a high-attention doc's residual is a **floor**. This doc has 9 prior
  rounds. The corpus contains never-audited docs; `module_34` measured 6-19x this doc's Critical
  density depending on convention.

Under the raw-record convention the earlier rows used, the same arithmetic gives **~277 (CI 52–1,118)** —
a 3x shift from the convention choice alone, which is larger than most of the effects being discussed.

**Verdict on the number: UNDECIDED.** A point estimate spanning 16–513 (or 52–1,118) does not support a
verdict, and the interval straddles every threshold anyone would set. **What would decide it:** ~25
observed distinct Criticals, at ~1 per 210 claims → ~5,250 claims → **~25 docs** sampled to span the
attention gradient rather than by arrival order. At the recorded $30/doc that is **~$750**, versus
~$1,400 for the full sweep — and it buys an actual between-doc variance estimate, which the full sweep's
first 25 docs would buy anyway.

---

## 8. Recommendation

**TARGETED_ONLY.** Do not launch a corpus sweep yet. Three plumbing fixes first, all cheap, all
prerequisites for the sweep producing computable numbers:

1. **Claim IDs in the ledger.** Emit claim records with identifiers; require every finding to name the
   claim ID it falsifies. Without this, per-class rates are uncomputable at any n (§2), and a sweep buys
   25 docs of the same uncomputable cells.
2. **Dedup before the matrix, not after.** Collapse records to distinct defects by claim ID, and report
   record count and defect count as separate columns. Anchor dedup reproduced expert code-fact dedup
   12-for-12 here (§1), so this is mechanisable now and does not wait on fix 1.
3. **Measure ledger coverage** with a seeded-claim harness plus a delta-0 control (§2b). The denominator
   is a detector output with unmeasured recall, and a 5.3x claims-per-line spread across the 9 existing
   ledgers is currently unattributable between real density variation and enumerator misses. Cross-doc
   rate comparison — which is the whole point of the sweep — is not sound until this is separated.

Then: **~25 docs sampled across the attention gradient**, sized to bound corpus Criticals (§7), rather
than a census by arrival order.

Also worth carrying forward, independent of the sweep decision:

3. **Recompute the gradient's Critical column under one convention** before any row of it is quoted
   again (§6, caveat 2). `module_34`'s 6 is the load-bearing one.
4. **Report a remedy-defect rate alongside every finding count** (§4). Two docs now show ~24–42% of
   Critical/Major fix texts needing correction; a fix pass that applies findings verbatim will inject
   errors at that rate.
5. **Do not report Minor/Informational in the same table as refuted Critical/Major** without a coverage
   column (§5). 69% of this doc's records never faced a refuter.

### What this round does establish

The depth instrument works. Five lenses independently converged on the same defects, `CITATION_FAILED`
was zero across 21 adjudications — unusual for this corpus, per the refuter — and nothing was refuted
outright. **12 distinct, adversarially-survived Critical/Major defects, 5.7% [3.3%, 9.7%] per enumerated
claim, in a doc with nine prior audit rounds behind it.** That number is sound *as a within-doc rate*.
What is not yet sound is the matrix built on top of it (§1, §2) and any comparison of it to another
doc's rate (§2b, §6).
