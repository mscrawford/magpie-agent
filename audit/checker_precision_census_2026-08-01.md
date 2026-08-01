# Checker precision census — 2026-08-01

**A census, not a sample.** Both reduced finding sets were small enough to adjudicate
exhaustively (13 + 13), which is strictly better than the stratified random sample the
plan called for: no sampling error at all. Every verdict below was made against the GAMS
source, from a per-finding evidence dump (`audit/tools/dump_finding_evidence.py`), not from
memory of the code.

> **Standard, fixed before adjudicating** (so it could not drift finding-to-finding):
> *if a reader opened the cited file at the cited lines, looking for what the sentence
> attributes to that citation, would they find it?* **TP** = no. **FP** = yes.

---

## Headline

| checker | findings before | findings after | precision |
|---|---:|---:|---:|
| `check_citation_content` | 51 (41 "certain") | **13** (9 "certain") | **7/13 = 54%** |
| `check_default_realization` | 25 | **13** | **9/13 = 69%** |
| `check_answer_identifiers` | 6/105 answers | 6/105 answers | unchanged this pass |

The "before" column is the state at the start of the session, over the same 105 arena
answers. The reduction is **not** a threshold being loosened — it is four extraction
defects being fixed, each with a regression control (below).

### The count that was quoted before this census was wrong by ~4x

The prior record carried **"43 certain-class citation findings / 421 checkable = 10.2%"**
and used it as a corpus defect rate. The true post-fix count is **9**. Nothing was
re-graded and no threshold moved; the 43 was inflated by extraction bugs, the largest of
which alone accounted for ~3.5x.

**Any rate computed off the old count should be discarded, not adjusted.**

---

## What was actually wrong (each fix carries a regression control)

1. **Bulleted source lists leaked identifiers across items.** The lookbehind that decides
   "what is this citation cited *for*" trimmed only at `\n\n`, `. ` and `; `. Assistant
   answers end with source lists that contain none of those:

   ```
   - `.../equations.gms:10-20` (q43_water)
   - `.../preloop.gms:8-12` (surface-only water availability)   <- inherited q43_water
   ```

   so every later bullet inherited the earlier bullet's identifiers and was reported as
   "identifier absent from the cited file". **9 of the first 14 findings adjudicated.**
   Fixed by `magpie_corpus.last_clause` (list items, numbered items and code-fence edges
   are boundaries too).

2. **A set member line cited under the set's name.** `kall` is declared at
   `core/sets.gms:228`; its members run to `:234`. Citing `:231` while naming `kall` is
   correct usage — the exact analogue of citing an equation's body line under the
   equation's name, which was already handled. 4 false positives. Fixed by
   `Tree.set_spans`, mirroring the existing `equation_spans` anchor.

3. **A filename admitted as a claimed identifier.** A file essentially never contains its
   own basename, so `presolve.gms` guaranteed a spurious "identifier absent". Fixed by
   `is_filename`. (This one had been *masked*: it was already being suppressed by an
   incidental "not" 36 characters away — right outcome, wrong mechanism, and a mechanism
   that would have deleted real findings elsewhere.)

4. **Markdown sections were treated as flat, not hierarchical.** A doc that writes

   ```
   ## 3. Alternative Realization: `sticky_labor` (NOT default)
   ### 3.1 CES production function
   ```

   has flagged the realization perfectly well — but splitting on *any* heading level made
   `### 3.1` a fresh section that had lost its parent's flag. Fixed by `_context_of`,
   which adds each **ancestor's preamble** (not its whole subtree — a qualifier in a
   sibling subsection says nothing about this one, and there is a control for that
   direction too).

Plus a counting defect: the citation checker emitted one finding per *occurrence*, so an
answer citing the same wrong line twice contributed 2 to every rate. Now deduplicated on
`(kind, path, cited, claimed)`.

---

## The severity labels are inverted relative to reliability

Precision by class, citation checker:

| class | label the tool gives it | findings | TP | precision |
|---|---|---:|---:|---:|
| `citation_off_by_small` | *minor* | 4 | 4 | **100%** |
| `citation_line_wrong` | *moderate* | 4 | 2 | 50% |
| `citation_identifier_absent` | *major* | 5 | 1 | **20%** |

The class the tool calls **major** is its **least** reliable, and the class it calls
**minor** is perfect. The reason is that "mechanically certain" was only ever a claim about
the *mechanical fact* (the token is not on that line) — never about whether that fact
constitutes a defect. An off-by-one is a defect whenever it fires. An "identifier absent"
usually means the citation supports a *proposition* stated in prose, which the checker
cannot read.

**Consequence: do not gate CI on `citation_identifier_absent`.** At 20% precision it would
fail builds four times out of five. `citation_off_by_small` is the class that has earned
gating, and it is the one currently labelled least important.

---

## Remaining false positives, by class

**Citation (6 FPs).** All are the checker attaching a citation to an *identifier* when the
sentence attaches it to a *proposition*:
- a citation inside a parenthetical, scoped to the whole sentence (2)
- a comment block that supports the claim without naming the identifier (3)
- an answer citing a wrong line **in order to report that it is wrong** ("one drift caught
  in passing: the doc cites `:2282`; the current line is `:2303`") (1) — the answer is
  correct and the checker flagged it. Same shape as the negation guard, one level up.

**Default-realization (4 FPs).** 3 of 4 are one class: **both** the default and the
non-default realization are cited side by side, so the reader cannot be misdirected. A
suppression for "the default is cited in the same clause" is the obvious next fix.

---

## Verdicts

Citation findings (`TP` = citation fails to support what it is attached to):

| # | answer | kind | cited | verdict |
|---|---|---|---|---|
| 1 | rep1_T1_C1 | identifier_absent | `60_bioenergy/1st2ndgen_priced_feb24/equations.gms:9-14` | TP |
| 2 | rep1_T1_C3 | off_by_small | `30_croparea/simple_apr24/input.gms:23` (is `:24`) | TP |
| 3 | rep1_T1_C4 | line_wrong | `config/default.cfg:357` | FP |
| 4 | rep1_T2_C1 | identifier_absent | `42_water_demand/all_sectors_aug13/realization.gms:30-35` | FP |
| 5 | rep1_T3_C2 | identifier_absent | `43_water_availability/total_water_aug13/realization.gms:16-35` | FP |
| 6 | rep1_T4_C1 | line_wrong | `29_cropland/simple_apr24/preloop.gms:2` (is `:9`) | TP |
| 7 | rep1_T8_C4 | line_wrong | `config/default.cfg:2282` | FP (answer reports it as stale) |
| 8 | rep2_T1_C4 | identifier_absent | `60_bioenergy/1st2ndgen_priced_feb24/equations.gms:31-35` | FP |
| 9 | rep2_T3_C1 | identifier_absent | `config/default.cfg:1340` | FP |
| 10 | rep2_T3_C3 | line_wrong | `config/default.cfg:1367` (is `:1373`) | TP |
| 11 | rep2_T3_C3 | off_by_small | `42_water_demand/all_sectors_aug13/preloop.gms:14` (is `:15`) | TP |
| 12 | rep3_T5_C2 | off_by_small | `30_croparea/simple_apr24/equations.gms:66` (is `:15`) | TP |
| 13 | rep3_T5_C3 | off_by_small | `17_production/flexreg_apr16/equations.gms:12` (is `:10`) | TP |

Finding 12 is worth separate note: the answer wrote *"per module_30.md"* next to the wrong
line number. That is a **doc defect propagating into an answer** — the case this whole
project exists to catch — and it is a triage candidate.

Default-realization findings (`TP` = a non-default realization referenced with nothing in
scope saying so):

| # | doc | module | cites | default | verdict |
|---|---|---|---|---|---|
| 1 | module_11.md:299 | 21_trade | `exo` | `selfsuff_reduced` | TP |
| 2 | module_11.md:299 | 21_trade | `selfsuff_reduced_bilateral22` | `selfsuff_reduced` | TP |
| 3 | module_29.md:847 | 44_biodiversity | `bv_btc_mar21` | `bii_target` | TP |
| 4 | module_29.md:989 | 59_som | `static_jan19` | `cellpool_jan23` | TP |
| 5 | module_29.md:1056 | 31_past | `static` | `endo_jun13` | TP |
| 6 | module_29.md:1056 | 34_urban | `static` | `exo_nov21` | TP |
| 7 | module_37.md:424 | 37_labor_prod | `exo` | `off` | TP |
| 8 | module_41.md:834 | 41_area_equipped… | `static` | `endo_apr13` | FP (both cited) |
| 9 | module_44.md:212 | 30_croparea | `detail_apr24` | `simple_apr24` | TP |
| 10 | module_52.md:432 | 59_som | `static_jan19` | `cellpool_jan23` | FP (both cited) |
| 11 | module_59.md:195 | 59_som | `static_jan19` | `cellpool_jan23` | FP (both cited) |
| 12 | module_59_notes.md:11 | 59_som | `static_jan19` | `cellpool_jan23` | TP |
| 13 | module_71.md:129 | 80_optimization | `lp_nlp_apr17` | `nlp_apr17` | FP |

Finding 7 is the most consequential: module 37's default is `off`, so the doc gives the
input-file location of a realization that a stock run never loads, without saying so.
That is the capability-vs-default class the corpus is measured to be worst at.

---

## Honest limits

- **These verdicts are mine, single-rater.** No independent re-derivation, no second
  adjudicator. Inter-rater agreement is unmeasured, so treat the precision figures as
  one careful pass, not as a validated measurement. The evidence dump is committed
  precisely so a second rater can redo it cheaply.
- The default-realization predicate carries **much more judgment** than the citation one.
  "Does this section establish which realization is configured?" has genuine borderline
  cases (a comparison table listing all four realizations; the word "Alternative" used as
  a label vs. as an adjective). I called those consistently, but a second rater could
  reasonably differ on 3-4 of the 13.
- Precision says nothing about **recall**. Nothing here estimates how many real defects
  the checkers miss, and the fixes in this pass all *reduce* findings, so recall can only
  have gone down or stayed flat. The one place recall was actively protected is the
  negation guard, which has a control asserting an ordinary mis-citation is still caught
  when the sentence merely contains the word "not".
- Denominator caveat unchanged: these are 105 **adversarial** answers, each written to hit
  a known defect. Nothing here is a base rate.

## Reproduce

```
python3 audit/tools/check_citation_content.py    --root <magpie-root> --batch <batch.md> --json cite.json
python3 audit/tools/check_default_realization.py --root <magpie-root> \
    --docs '<agent>/modules/*.md' --docs '<agent>/cross_module/*.md' --json dflt.json
python3 audit/tools/dump_finding_evidence.py     --root <magpie-root> --batch <batch.md> \
    --citations cite.json --defaults dflt.json --out evidence.txt
```

Self-tests, all with positive **and** negative controls, all green at time of writing:
`magpie_corpus` 36, `check_answer_identifiers` 24, `check_citation_content` 20,
`check_default_realization` 15.
