# Plan — can the no-scoreboard bug classes be made auditable?

**Status: run 1 complete (2026-07-31), see `audit/arena_run_2026-07-31.md`. Phase 3 not
started.** Renamed from `PLAN_fable_auditability_assessment.md` on 2026-07-31: the design
was built around a Fable-vs-Opus comparison, Fable failed its gate, and the tier question
is now answered with an explicit dispatch-parameter ladder instead.

---

## The question

Four bug classes were structurally invisible to the deterministic gate across two
seeded-bug benchmark runs eleven days apart and a checker-list correction:
`attribution_role`, `citation`, `data_source`, `mechanism` — all at zero.

They are blind for a **diagnosed** reason: the claims name **no interface variable**, and
every attribution checker is var-anchored, so there is nothing to bind. `check_bindability`
sizes the class corpus-wide (the ratio is banned from being quoted as a statistic — treat
it as direction).

**The question**: per class, is the fix a **mechanism**, a **corpus convention**, or
**neither**?

---

## What the Fable design cost, recorded so it is not repeated

The original plan was built on a project memory that turned out to be wrong about both its
cause and its remedy. It attributed a tier failure in this workspace to nitrogen content
and concluded that *"a Fable vs Opus comparison would need a workspace without the nitrogen
trigger."* Acting on that, the arena was built with a nitrogen-term filter on control
selection and with `modules/module_58.md` excluded as too nitrogen-dense to present.

Then the gate was run, and Fable failed on *"what does `vm_land` represent and which module
declares it?"* — no nitrogen, no biology term. The trigger was never what the memory said.

Two costs, both now paid back:

- **Removed** the term filter and the default exclusion. An unused filter that silently
  shapes which files an auditor sees is worse than no filter.
- **Recovered coverage.** `module_58.md` carries the *second* `attribution_role` hunk. That
  class had exactly one answerable item in run 1 and was caught once in four deep runs —
  the thinnest and most decision-relevant class in the ladder. Dropping the exclusion
  doubles it: the arena now offers **5 answerable injections** (mechanism 1,
  attribution_role 2, citation 2) rather than 4.

The generalisable lesson lives in the memory correction, not here: a remembered *remedy* is
a claim to re-derive, not a constraint to design around. Weeks of design followed from one
unverified sentence.

---

## Phase 2 — detection arm (run once; the scoreboard exists)

`audit/tools/prepare_audit_arena.py` builds a blind arena from real historical doc bugs and
scores an auditor against a sealed key. Blindness, controls, findability and answerability
are all enforced mechanically; 45 assertions under the self-test ratchet. The tool docstring
records what each control exists to stop and which of them failed silently on first build.

**Run 1**: Haiku 4.5 0/4 across four runs; Sonnet 5 1/4 twice; Opus 5 2/4 and 1/4. Per class
over the four deep runs: `mechanism` 4/4, `attribution_role` 1/4, `citation` 0/8.

**Run 2 is blocked on a known instrument defect, not on compute.** The brief asks for claims
that CONTRADICT the source; a bare-basename citation is *ambiguous*, not false, so
`citation` was never askable as posed. Ordered next steps:

1. **Fix the brief** — name citation ambiguity as in-scope, and separate "contradicts the
   code" from "cannot be resolved against the code". Re-run on the 5-injection arena.
2. **Verify the ~20 uncounted citation-drift leads** from run 1. Cheap, mechanical, and
   decisive: if most are real, that class is both the highest-volume LLM finding *and* the
   most mechanizable thing in the corpus, which argues for building the checker rather than
   paying for audits at all.
3. **Drop Haiku 4.5.** 0/8 on unconfounded items, and three of four runs returned nothing
   while asserting "excellent fidelity to the actual code implementation". A confident
   empty result is worse than a miss.

---

## Phase 3 — design arm (not started)

Per class, force one verdict — not an essay:

1. **Mechanisable as-is** — a checker can bind the current text. Precedent: Check 41 moved
   `attribution_set` off zero by resolving bare module lists against the role map.
2. **Mechanisable with a corpus convention** — e.g. *"every module-level attribution claim
   must name at least one interface variable."* A writing rule plus a migration, with an
   estimated migration size (`check_bindability` measures it).
3. **Not mechanisable** — genuinely needs semantic judgment. Then the move is to make the
   audit cheaper and more reliable, not to mechanise it.

Every verdict must carry a number we can check ourselves: a predicted finding count for (1),
a migration line count for (2), a concrete cheapening proposal for (3).

### Pre-registered predictions

| class | prediction | status after run 1 |
|---|---|---|
| `citation` | class 1 — Check 25 exempts module docs, unsafe for the 23 multi-realization modules; M80 has four realizations each with its own `solve.gms` | **untested** — the brief was confounded |
| `attribution_role` | class 2 — var-anchored checkers exist but the claims name no variable | 1/4; now 2 items per run, retest |
| ~~`data_source`~~ | ~~class 2~~ | **withdrawn** — see below |
| `mechanism` | class 3 — "models X" vs "applies a historical rate" is judgment | caught 4/4 by LLM auditors; a checker still looks hard |

**`data_source` is withdrawn from the class question, and run 1 showed why in the strongest
possible form.** Its one hunk is the LUH3 -> LUH2 fix, anchored in the R preprocessing.
Sonnet A *found* the injected inconsistency, investigated properly, and concluded LUH3 was
the error — citing, correctly, that `LUH3` appears nowhere in `modules/10_land/` and that
the only LUH tag there is `luh2_side_layers10 side layers from LUH2`. A careful auditor
reasoning correctly from the available evidence reached a confident **inversion**, because
the deciding evidence is in another repo. This class cannot be adjudicated from a GAMS-only
arena; it belongs to the preproc agent, or needs the preproc corpus mirrored in.

---

## Non-mechanization levers (the other half of the question)

Prompt and protocol design, ordered by how well run 1 supports them rather than by
plausibility.

**Supported by measurement:**

- **Union across runs may beat height of tier.** The five verified real bugs were found by
  *different* arms with almost no overlap — Haiku found one, Sonnet two, Opus one, and the
  only cross-run agreement was within a tier. Three cheap runs unioned may dominate one
  expensive run. Directly testable and currently untested.
- **Per-file verdicts plus an audit trail.** "0 findings" is indistinguishable from "did not
  look". Requiring a clean/defective verdict per file, plus the commands actually run, would
  have made Haiku's 13-tool-use runs self-evidently shallow rather than confidently empty.
- **Separate "contradicts" from "cannot be resolved against the code".** The measured
  `citation` 0/8 and the `data_source` inversion are the same defect twice.

**Plausible, unmeasured — labelled as such:**

- One file per agent rather than ten, for bounded context and depth.
- Two-pass: enumerate checkable claims, then verify each. Shallow runs fail at enumeration.
- Mechanical claim extraction feeding LLM verification — the hybrid, and the highest ceiling.
- Require a verbatim source quote per finding, not just `file:line`.
- Independent refutation per finding (already the standing rule for model-bug claims).

**The consideration against investing here:** run 1's largest yield came from auditors
roaming *control* files freely, not from better targeting — and the highest-volume finding
class was also the most mechanizable one. Prompt work may have a lower ceiling than simply
building the citation-line checker.

---

## Rejected approaches, with reasons

**Rewriting or keyword-filtering the corpus to keep a safeguard from firing.** Rejected in
the original plan and reaffirmed: it measures the sanitiser, creates a second source of
truth that drifts, and may not clear the threshold anyway. Separately, engineering around a
model's safety routing is not something to do regardless of whether it would work. The
trigger boundary was deliberately not probed — mapping what gets through is the same
activity as evading it.
