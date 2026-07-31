# Plan — Fable session: can the no-scoreboard classes be made auditable?

**Written 2026-07-31 for a subsequent session.** Self-contained: a fresh context should be
able to run this without the conversation that produced it.

**Status: Phase 2 tooling BUILT (2026-07-31), nothing run.** Phase 0 is a gate — if it
fails, everything after it is void and the session should stop rather than adapt. The
arena tool was built ahead of the gate because it is the one piece Phase 2 cannot run
without, and because building it is independent of the gate's outcome.

---

## The question

Four bug classes are structurally invisible to the deterministic gate, stable across two
benchmark runs eleven days apart and across a checker-list correction:

| class | seeded bugs | gate detection |
|---|---:|---|
| `attribution_role` | 2 | 0/2 |
| `citation` | 2 | 0/2 |
| `data_source` | 2 | 0/2 |
| `mechanism` | 1 | 0/1 |

They are blind for a **diagnosed** reason, not a mysterious one: the claims name **no
interface variable**, and every attribution checker is var-anchored, so there is nothing to
bind. `check_bindability` sizes the class corpus-wide (most attribution lines are
unbindable; the ratio is banned from being quoted as a statistic — treat it as direction).

**The question for this session**: per class, is the fix a **mechanism**, a **corpus
convention**, or **neither**?

---

## Phase 0 — GATE: does Fable actually run here?

**This is Mike's hands, ~2 minutes, and nothing proceeds without it.**

Confirmed 2026-07-31: a prompt containing the single word "Nitrogen" **bails** in this
workspace. The standing project memory (`magpie_workspace_fable_downgrade_nitrogen`,
2026-06-11) records that Fable-tier requests here silently route to Opus, and that **the
model cannot introspect its own routing** — the session may say "Fable" while Opus is
served. A full round-51 design was built and scrapped over this in June.

**Test**: open a Fable session and ask a pure land-use question with no nitrogen content —
e.g. *"In MAgPIE, what does `vm_land` represent and which module declares it?"*

- **Serves Fable, answers normally** → proceed to Phase 1.
- **Bails, or Mike sees Opus in the UI** → **STOP.** Do not adapt, do not sanitise the
  corpus (see *Rejected approaches*). Report and end the session.

---

## Phase 1 — Model-identity control

The downgrade is **silent** and self-report is unreliable, so the experiment must carry its
own identity evidence. Without this, a null result is uninterpretable: "Fable found
nothing" and "Opus wearing a Fable label found nothing" are indistinguishable.

Build a short probe of items where the tiers measurably differ, run it **inside the same
session as the audit** (not before, not in a sibling session), and record the raw answers
alongside the findings. Mike's UI observation is the primary evidence; the probe is the
artifact that survives into the record.

If the probe is ambiguous, treat the run as **Opus** and label the results accordingly.
Default to the unflattering interpretation.

---

## Phase 2 — Detection arm (calibration, and it comes FIRST)

**Why first**: an assessment of *whether a class can be mechanised* is worth little from a
model that cannot see the class. Phase 2 establishes whether it can, objectively, against
ground truth that already exists.

### The scoreboard already exists

`audit/tools/seed_known_bugs.py` holds 12 curated commits whose hunks are **real historical
doc bugs**, reverse-applied one at a time into today's corpus. For the four blind classes
there are **8 hunks** with known file, known class, and known content.

**Built 2026-07-31: `audit/tools/prepare_audit_arena.py`** — `prepare` an arena, `score` an
auditor's findings. Deliberately not an agent runner, because the Fable arm is opened by
hand and the Opus arm may be a subagent; baking one dispatch mechanism in would have made
the tool usable for only one of them. 32 assertions under the self-test ratchet.

Running it supersedes the hand-measured table this section used to carry (Rule 4 — the
tool is the persisted artifact; the hand count was not re-derivable). Measured output:

| file | class | hunks | avoid-term hits |
|---|---|---:|---:|
| `modules/module_10.md` | data_source | 1 | 1 |
| `modules/module_10_notes.md` | data_source | 1 | 0 |
| `modules/module_29_notes.md` | mechanism | 1 | 0 |
| `modules/module_40.md` | attribution_role | 1 | 1 |
| `modules/module_80.md` | citation | 2 | 1 |
| `modules/module_32.md` | mechanism | — | *hunk no longer applies; SKIPPED* |
| **`modules/module_58.md`** | **attribution_role** | 1 | **held back** |

So the default arena carries **6 injected hunks across 5 files**, none of them
nitrogen-loaded, plus 6 clean controls. `module_58` is held back by default and runs
alone via `--only-hunk modules/module_58.md`, as a calibration probe on where the
safeguard threshold sits. If it bails, that is a datum, not a failure, and the six stand.

### Protocol

1. `prepare` builds the arena: a `git archive` extract of HEAD (**not** a worktree — a
   worktree hands over the answer key via one `git diff`), a lean 606-file `*.gms` mirror
   of the model source at `../modules/` so citations resolve, and the hunks reverse-applied
   in place. Reverse-apply eliminates code drift by construction.
2. **Clean controls** are selected automatically — unmodified docs of comparable length —
   so a flag rate is measurable. Without them, "found 6 bugs" and "flags everything" are
   the same observation.
3. The auditor gets the corpus, the GAMS source, and the brief. It must not see the answer
   key, the class labels, or which files were touched.
4. `score` classifies against ground truth: line-match catch, file-only catch (weak, needs
   triage), miss, and flag-on-a-file-with-no-injection.
5. **Run an Opus arm on the identical protocol.** Without it there is no tier comparison and
   the session answers a different question than the one asked. One arena serves both arms.

### Three things the first build got wrong, now closed

Recorded because each failed **silently** — every one of them produces output identical to
a correct run, and all three would have yielded a clean-looking Phase 2 number that meant
nothing.

1. **The arena was not blind.** It is the whole repo at HEAD, and this project documents its
   own auditing: `audit/` ships the round archives, the benchmark write-ups and
   `seed_known_bugs.py` itself, which name these exact bugs. An auditor that grepped `audit/`
   had the answer key. Now `audit/` and `project/` are stripped, and — because "strip the
   directories someone thought of" is the reasoning that let it in — a leak scan then greps
   every surviving file for the seed commit SHAs and for verbatim hunk lines, and **aborts
   the build** on a hit. Verified end-to-end: building with `--keep-meta` aborts on real
   data, naming three files.
2. **`ls -lt` sorted the seeded files to the top.** `git archive` stamps everything with the
   commit time; injection then set today's mtime on exactly the touched files. All arena
   mtimes are now normalised after injection.
3. **The control picker optimised length alone** and chose `module_50` (nr_soil_budget) and
   `module_55` (awms) — so the Fable arm would have failed on the *controls* while every
   seeded file ran fine. Controls are now held to the same term bar as the seeds.

### Prompt hygiene — non-negotiable, and it is a repo rule

**Never paste an absolute working directory into an agent prompt.** Agents echo their
environment into their output: R59 leaked 8 local paths into this public repo that way,
every one traceable to the path put *into* 24 prompts. Give a repo-relative brief and let
the agent resolve paths itself. (`AGENT.md` § PUBLIC repo; detail in
`agent/helpers/session_cleanup.md`.)

The arena tool takes this one step further, because a convention that depends on an
agent's discipline is not a control: the generated brief carries an `<ARENA>` token rather
than a literal path, and `score` mechanically scrubs absolute paths out of every artifact
it writes. The scrubber is a self-test assertion, and it was verified to fail when
neutered.

---

## Phase 3 — Design arm (the thing actually asked for)

Only after Phase 2 gives a calibration number. Per class, force a verdict among **three**
outcomes — not an essay:

1. **Mechanisable as-is** — a checker can bind the current text. Precedent: Check 41 moved
   `attribution_set` from 0/5 to 1/5 by resolving bare module lists against the role map.
2. **Mechanisable with a corpus convention** — e.g. *"every module-level attribution claim
   must name at least one interface variable."* A writing rule plus a migration, **not** a
   rewrite. Must come with an estimated migration size.
3. **Not mechanisable** — genuinely needs semantic judgment. Then the move is to make the
   audit cheaper and more reliable, not to mechanise it.

Each verdict must carry the **specific** convention or checker sketch, and for class 2, the
count of doc lines that would need migrating (measurable with `check_bindability`).

### Pre-registered predictions — so this can refute me, not confirm me

Recorded **before** the session runs:

| class | my prediction | basis |
|---|---|---|
| `citation` | **class 1** | The mechanism is already known: Check 25 exempts module docs, and that exemption is unsafe for the 23 multi-realization modules. M80 has four realizations each with its own `solve.gms`. |
| `attribution_role` | class 2 | Var-anchored checkers exist (Check 31) but the claims do not name variables. |
| `data_source` | class 2 | "comes from LUH2/LUH3" names a dataset, not an identifier. |
| `mechanism` | **class 3** | "MAgPIE models X" vs "applies a historical rate" is a semantic distinction; the three-check protocol is judgment. |

**If all four come back class 2, I was wrong and that is the finding.**

---

## Phase 4 — Synthesis

Deliverable: a per-class verdict, the sketches, migration costs, and a recommendation on
whether to build. **Building is a separate decision and a separate session.**

---

## Rejected approaches, with reasons

**Keyword-replacing the corpus to evade the safeguard** (considered 2026-07-31):

1. **It breaks what is being measured.** The audit checks doc claims against GAMS
   identifiers, module numbers and equations. Rename domain terms and either the GAMS source
   is renamed too (enormous, and then it is not MAgPIE), or it is not — and every renamed
   identifier becomes a spurious mismatch. The result would measure the sanitiser.
2. **A parallel sanitised corpus is a second source of truth** that drifts, against this
   project's own link-don't-duplicate principle.
3. **It may not even clear the safeguard**, which plausibly keys on the constellation
   (N₂O, fertiliser, ammonia, soil budgets) rather than one token.

**Selecting a nitrogen-free subset supersedes it** — real content, real code, real bugs,
zero rewriting, and the ground truth already exists.

---

## Stop conditions

- Phase 0 fails → stop, report, do not adapt.
- The identity probe is ambiguous → label everything Opus and say so.
- The Opus arm is skipped → the tier question is unanswered; do not report a tier claim.
- Fable finds 0/7 **and** the identity probe confirms Fable → that is a real and publishable
  negative result about the class, not a reason to loosen the protocol.

## Decisions reserved for Mike

1. Whether to run the `module_58` calibration probe at all (it deliberately pokes the
   safeguard).
2. Whether the Opus arm runs in the same session or a separate one.
3. Whether to proceed to building anything, after Phase 4.

## Cost

Roughly 100-155k tokens per audit pass, per the R59 measurement in
`audit/STATE_2026-07-31.md`. Two arms across seven injections plus controls is the dominant
cost; Phases 0, 1 and 3 are small beside it.
