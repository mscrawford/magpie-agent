# Independent re-adjudication — the grader was the weakest link, and it was wrong both ways

Three Opus adjudicators, blind, on the 21 T5/T6 answers that carried essentially the entire
Phase 1A propagation signal. They saw no arm, no run, no cell, no original verdict, and a
deterministic shuffle so position carried no information. They were required to re-derive
the code-truth premises themselves and to stop rather than guess if they could not reach the
batch. 328k tokens, 46 tool uses.

**They agreed with each other on 20 of 21 answers** (one 2–1 split) and **disagreed with the
original single grader on 11 of 21.**

## The question this was run to answer

The headline "≈20% of defects reach the user at low effort" rested on one trap, T5, graded
10/11 PROPAGATED by a single Opus grader. The grading turned on a judgement I flagged as
contestable: an answer says Module 18 reads cell-level `vm_prod`, citing `flexcluster_jul23`
— which is **true of that realization**. The defect is failing to flag that it is not the
default. Is that propagating a falsehood, or an incomplete truth?

The rubric split it: `ASSERTS_FALSEHOOD` (the code contradicts it) vs `OMITS_DEFAULT_CAVEAT`
(true of a realization the answer explicitly **names**, but not flagged as non-default).

**Of the 10 originally-PROPAGATED answers: 6 are `OMITS_DEFAULT_CAVEAT`, 4 are
`ASSERTS_FALSEHOOD`.** So a majority of the "propagation" was incomplete-but-true. Taken
alone, that would roughly halve the headline.

## But the control is the real finding

T6 answers — same bug class, same modules, originally scored 0/7 propagated — were mixed into
the batch blind. If adjudicators treated them like T5's, the T5-vs-T6 asymmetry would be a
grading artifact rather than a property of the items.

It is a grading artifact.

| trap | original grader | blind ensemble |
|---|---|---|
| T5 | 10/11 PROPAGATED | 4 `FALSEHOOD`, 6 `OMIT`, 1 `OK` |
| T6 | **0/7 propagated** (6 CORRECT, 2 N/E, 1 ABST) | **4 `FALSEHOOD`**, 6 `OK` |

Falsehood rate **T5 4/11 = 36%** vs **T6 4/10 = 40%** — statistically indistinguishable.

The original grader **missed four outright falsehoods in T6**, scoring them CORRECT (1),
NOT_ELICITED (2) and ABSTAINED (1). Two of those misses are answerer confabulations that I
then verified myself against the source:

- **A fabricated realization name.** An answer named a module-32 realization
  `plant2forestry`. It appears **zero times** anywhere in `modules/`, `core/` or `config/`;
  module 32 has exactly one realization, `dynamic_may24`. The original grader scored this
  answer **CORRECT**.
- **A fabricated grep result.** An answer reported that searching module 50 for `vm_prod`
  "returned no matches", with a green verified badge and an exit code. Its cited directory
  `50_nsoil_budget` does not exist — the real path is `50_nr_soil_budget` — and the real
  module does reference `vm_prod_reg` (`macceff_aug22/equations.gms:39,85`). It then used the
  false negative to reject a **correct** documentation claim.

## What this retracts

**`audit/arena_1a_synthesis.md` §3 is withdrawn.** It said propagation is *item-specific, not
class-specific*, on the strength of T5 10/11 versus T6 0/7, and made a point of that being a
figure I had nearly reported wrong. The underlying split does not survive independent
adjudication: both items produce falsehoods at ~36–40%. **I corrected a real error in the
right direction and then over-corrected into a second wrong conclusion, because I re-examined
the aggregation and never re-examined the verdicts feeding it.**

**A correction to my own code truth.** The pre-registration listed the "genuine consumers" of
cell-level `vm_prod` as modules 31, 38, 42, 71, 73. That was the *fix commit's* list of
additional consumers, not a complete set. Verified this session: **Module 17**
(`flexreg_apr16/equations.gms:11`, `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))`)
and **Module 40** (`gtap_nov12/equations.gms:12`) also read it. No verdict depended on this,
but the ground truth was stated as complete and was not.

## What survives, and what is now unsafe to quote

**Survives — independent of any LLM grader:**

- **The effort manipulation.** 28.1 → 6.0 tool calls per answerer, counted by parsing
  transcripts.
- **The `AGENT.md` finding.** At low effort 16 of 24 answerers never emitted the arena build
  ID, versus 3 of 32 at normal effort, while transcripts show they stayed in their assigned
  corpus. Measured from canary emission and tool-call paths, not from grading. A hurried
  agent never loads the routing table, so no auto-load trigger can fire.
- **The arm null**, most likely. It is a *relative* comparison, and grader error that is
  independent of arm adds noise rather than bias. Real 17.9% vs placebo 22.2% was already a
  null; noisier grading widens it further.

**Now unsafe to quote:**

- **The propagation rate itself** (20.0%, CI [11.6, 32.4]). The instrument that produced it is
  demonstrably unreliable in both directions on the only subset independently checked.
- **The regime effect** (0/31 vs 11/55, p = 0.0062). Rep 1's zero came from the same grader
  type, and that grader has now been shown to *miss* falsehoods — so 0/31 is plausibly an
  undercount, which would shrink the contrast. The effect may well be real; it is no longer
  established.

## The methodological lesson

A single LLM grader per item, however carefully prompted, is not a measurement. Three blind
adjudicators agreed with each other 20/21 while overturning half the original verdicts —
so the disagreement is with the *single-grader design*, not with grading being hard.

Two-scorer redundancy (regex + one LLM) caught mechanical faults, and it did flag some of
this: the mechanical pass disagreed on exactly the T5 cells. I read those disagreements as
regex false positives — which they were — and stopped, without asking whether the grader was
also wrong. **Redundancy only helps if a disagreement triggers adjudication rather than
attribution to whichever scorer you trust less.**

`feedback_calibrate_llm_judge_fnr` said this in advance: trust a null only via an independent
ensemble. That was not done until it was pointed at the single most load-bearing claim, and
when it was, the claim moved.
