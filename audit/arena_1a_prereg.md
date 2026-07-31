# Phase 1A pre-registration — does `verifiers.md` change what a user is told?

**Written and committed BEFORE any answerer was dispatched.** That is the whole point of the
file: a prediction recorded after the fact is not a prediction. Results go in a separate
document so this one can be diffed against them.

## The question

The 22 MANDATEs in `agent/helpers/verifiers.md` are evidence-**motivated** (each cites a real
bug) and almost entirely evidence-**unvalidated**. Exactly one has ever been ablated:
`audit/archive/rounds/round51_calibration/ITEM3_findrate_and_mitigation.md` injected
MANDATE-21 into the **auditor** prompt and recovered inter-module direction bugs 0/2 → 2/2.
Nothing has ever tested the **answerer** path — whether any MANDATE changes what an end user
is actually told.

The hypothesis under test:

> The auto-load trigger is evaluated against the user's **input**, while the risk lives in
> the agent's **output**. "How does fallow land work?" contains zero trigger keywords, so
> `verifiers.md` never loads — yet answering it requires `vm_fallow`, realization names and
> `s29_*` defaults.

## Metric — propagation rate, not detection rate

How often a corpus error reaches the user's answer. Four outcomes:

| outcome | meaning |
|---|---|
| `PROPAGATED` | the answer asserts the documentation's false claim |
| `CORRECT` | the answer asserts the code truth |
| `ABSTAINED` | engages the topic but hedges, flags a conflict, or declines — a **distinct and good** outcome, never scored as CORRECT |
| `NOT_ELICITED` | never touches the claim; the question did not reach the defect — **excluded from the denominator** |

`NOT_ELICITED` exists because run 1 taught the lesson on the auditor side: an item whose
ground truth the subject could not reach must leave the denominator, or a vague question
that never approaches the claim silently inflates the good column.

## Design — 2×2, 8 traps, 1 rep this window

| | `verifiers.md` REAL | `verifiers.md` PLACEBO |
|---|---|---|
| **naive** phrasing (no trigger keyword) | C1 — mimics reality | C2 |
| **trigger** phrasing | C3 — MANDATEs load | C4 |

The ablation is a **placebo, not a deletion**: the placebo arena ships a same-named
`verifiers.md` carrying the same framing sentence and *no procedure*. Deleting the file
would instead leave five dangling pointers in `AGENT.md` and make the treatment "a read that
404s". This isolates the procedural content from the mere act of loading a helper.

Answerers: `agentType: magpie-helper`, **pinned `sonnet`**, full tool access, one question per
dispatch. Graders: one Opus per trap, sees all four of that trap's answers in a rotated order
that carries no arm information.

## Pre-registered predictions

- **C1 ≈ C2.** With no trigger keyword, `verifiers.md` is never loaded, so its content on
  disk should not matter. This is the control for the control: **if C1 and C2 differ,
  something is loading that I do not understand and the design needs revisiting before any
  other cell is interpreted.**
- **C3 < C4** in propagation, if the MANDATEs do anything at all.
- **C1 > C3** — the phrasing effect.
- **Most likely outcome, stated so it can be wrong: C3 < C4 but C1 ≈ C2 ≈ C4.** The MANDATEs
  work when loaded and never load in realistic use. If that is what comes back, **the
  intervention is the trigger, not the rule text**, and no MANDATE should be rewritten.
- **All four equal** → the MANDATEs are decoration on this path and the lever is elsewhere.

Per-trap, `mechanism` and `set_member_label` are expected to be the most reliably elicited;
the two `citation` traps are expected to be the weakest discriminators for an *answerer*
(a bare basename is an ambiguity, not a falsehood) and are first in the drop order.

## Traps

Eight defects that **exist in the arena corpus**, each with ground truth in the mirrored GAMS
source, each re-derived by hand this session before being used.

| # | source | doc | defect | code truth |
|---|---|---|---|---|
| T1 | native | `modules/module_60.md:59` | "bioenergy grasses (betr) and trees (begr)" — swapped | `betr` = bioenergy **tree** (`30_croparea/simple_apr24/equations.gms:17`; `config/default.cfg:931`). Same doc correct at `:96`, `:126` |
| T2 | native | `cross_module/water_balance_conservation.md:71` | fenced GAMS quote uses `ssp_scenario`, a symbol that exists nowhere | real switch `s42_watdem_nonagr_scenario`, `input.gms:9`, default `/ 2 /`, confirmed at cfg layer (`default.cfg:1357`) |
| T3 | native | same file, `:101`/`:534`/`:552` | presents the EFP ramp 2025→2040 as model behaviour; never says which mode is default | `$setglobal c42_env_flow_policy off` (`input.gms:122`) **and** `cfg$gms$c42_env_flow_policy <- "off"` (`default.cfg:1373`) — EFP is OFF in a default run |
| T4 | seeded `b6afd58` | `modules/module_29_notes.md:11` | "the `simple_apr24` realization includes fallow land dynamics" — inverted | `detail_apr24` (the default, `default.cfg:814`) models fallow; `simple_apr24` sets `vm_fallow.fx(j)=0` (`preloop.gms:9`) |
| T5 | seeded `ec119a9` | `modules/module_40.md:53` | lists M18 and M30 as **consumers** of `vm_prod` | M30 is the **producer** (`vm_prod` only on the LHS of `q30_prod`, `simple_apr24/equations.gms:15`); M18's default realization is `flexreg_apr16` (`default.cfg:625`), which reads **`vm_prod_reg`**, not cellular `vm_prod` — the doc cited non-default `flexcluster_jul23` |
| T6 | seeded `ec119a9` | `modules/module_58.md:35-36` | attributes `vm_land_forestry` & siblings to `10_land`; "5 total" dependencies | declared in `32_forestry/dynamic_may24/declarations.gms:74-76`; M58 reads them at `58_peatland/v2/equations.gms:23,28,31`; count is 6 |
| T7 | seeded `3620958` | `modules/module_80.md:667` | cites `magpie.solprint` as bare `solve.gms:16, 174` | `solprint` is in **all four** M80 realizations at different lines — `lp_nlp_apr17` @16,174 · `nlp_apr17` @18,80 · `nlp_ipopt` @54,84 · `nlp_par` @20. The cite is unresolvable **and** pins to the non-default realization (default `nlp_apr17`, `default.cfg:2303`) |
| T8 | seeded `3620958` | `modules/module_80.md:814-816` | cites `s80_secondsolve` as bare `solve.gms:66, 77, …` | same: those lines exist only in `lp_nlp_apr17`. Default `s80_secondsolve = 0` at both layers (`input.gms:11`, `default.cfg:2324`) |

**A ground-truth correction made during setup, recorded because it would have silently
mis-graded two traps.** T7/T8's "correct" answer was initially taken from the fix commit as
`lp_nlp_apr17/solve.gms`. Checking `config/default.cfg:2303` showed the **default**
realization is `nlp_apr17`, not `lp_nlp_apr17` — so an answerer naming the default would have
been marked wrong. Reading all four `solve.gms` files resolved it: the doc's line numbers
match `lp_nlp_apr17` only. Both traps were re-scoped to the defensible defect — the citation
is unresolvable — with the non-default-realization issue recorded as a second layer. This is
the [[magpie_cfg_overrides_input_defaults]] trap: `input.gms` is not the operative default,
and a ground truth taken from a commit message rather than from the config stack is a
hypothesis, not a fact.

## Controls, and what each is protecting against

| control | protects against |
|---|---|
| **Canary build ID** per arm (`ARENA-9F4T` real / `ARENA-2XQ8` placebo), required in every answer | `magpie-helper`'s own step-1 search resolves `magpie-agent/AGENT.md` **relative to cwd** — i.e. the *real* corpus. An answerer that read the real corpus would see the fixed text and score CORRECT, inflating exactly the cells under test. An answer missing its own arm's ID is **discarded, not counted**. |
| **Arena built git-free**, exposed by symlink | with the arena root inside a git work tree, `git apply -R` silently injected **0 of 5** hunks while still producing a plausible-looking arena. Measured, not assumed: same command, 0 injected inside the tree vs 5 outside. |
| `audit/` + `project/` stripped, leak scan | those directories name the seeded bugs |
| **Two independent scorers** (regex cascade + Opus grader), disagreements reported | a run where both agree everywhere is weak evidence either works; systematic disagreement localises a soft ground truth |
| **Blinded grader**, deterministic rotation per trap | grader inferring arm identity from position |
| Questions authored against code truth, then contamination-checked by a fresh agent | a question that hints the claim is suspect measures nothing |

## Known fidelity gaps — stated, not hidden

- A subagent does not receive the harness's `CLAUDE.md` auto-load. Answerers are told to read
  `AGENT.md` at the corpus root and follow it, which makes the always-loaded layer explicit and
  slightly **favours** the agent — biasing toward finding no effect, the conservative direction.
- Arena confinement is instruction-based. Run 1 is evidence that it holds (all three deep
  auditors reported `not_used.txt` absent, true only inside the arena), and the canary now
  measures it per answer instead of assuming it.
- Trigger-phrased questions load *other* helpers too (e.g. T3's wording reaches the water-scarcity
  helper). That asymmetry is constant across the REAL/PLACEBO arms, so the C3−C4 contrast is
  clean; the C1−C3 contrast confounds phrasing with helper loading generally, and is read as
  "phrasing effect", not "MANDATE effect".
- `magpie-helper`'s definition carries `model: opus`; the dispatch overrides it to `sonnet`,
  which is the project's established flywheel pattern (`doc_audit_round.workflow.js:338`).
  The override is not independently observable from a subagent's output, so it is recorded as
  a residual assumption rather than a verified fact.

## What this design cannot support

- Any corpus-cleanliness verdict. R58 measured that directly: a 4-question QA arm scored 8.375
  while a depth arm found 46 defects in 595 claims. This is a propagation rate on 8 chosen
  traps, and nothing more.
- Any per-trap significance. n = 1 per cell per trap this window; a second replicate is planned.
- Anything about MANDATEs whose subject matter no trap touches — 8 traps cannot speak for 22 rules.
