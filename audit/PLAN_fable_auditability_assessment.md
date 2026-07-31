# Plan — Fable session: can the no-scoreboard classes be made auditable?

**Written 2026-07-31 for a subsequent session.** Self-contained: a fresh context should be
able to run this without the conversation that produced it.

**Status: NOT STARTED.** Phase 0 is a gate — if it fails, everything after it is void and
the session should stop rather than adapt.

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

**Measured 2026-07-31 — nitrogen-term density in exactly those files:**

| file | class | nitrogen-term hits |
|---|---|---:|
| `modules/module_80.md` (×2 hunks) | citation | 1 |
| `modules/module_10.md` | data_source | 1 |
| `modules/module_10_notes.md` | data_source | 0 |
| `modules/module_29_notes.md` | mechanism | 0 |
| `modules/module_40.md` | attribution_role | 0 |
| `modules/module_32.md` | mechanism | 1 *(hunk currently SKIPPED — no longer applies)* |
| **`modules/module_58.md`** | **attribution_role** | **15 (13 × N₂O)** |

So **7 of 8 hunks sit in essentially nitrogen-free docs.** Run those seven first.
`module_58` is the one loaded file — run it **last, deliberately**, as a calibration probe
on where the safeguard threshold actually sits. If it bails, that is a datum, not a
failure, and the other seven still stand.

### Protocol

1. Build a scratch worktree at HEAD. Inject the 7 hunks **one at a time**, as
   `seed_known_bugs.py` already does (reverse-apply eliminates code drift by construction).
2. Add **clean controls** — unmodified files from the same modules — in the same batch, so
   false positives are measurable. Without these, "found 7 bugs" and "flags everything" are
   the same observation.
3. The auditor gets the corpus and the GAMS source and is asked for findings. **It must not
   see the answer key**, the class labels, or which files were touched.
4. Score afterward against the known ground truth: caught / missed / false positive.
5. **Run an Opus arm on the identical protocol.** Without it there is no tier comparison and
   the session answers a different question than the one asked.

### Prompt hygiene — non-negotiable, and it is a repo rule

**Never paste an absolute working directory into an agent prompt.** Agents echo their
environment into their output: R59 leaked 8 local paths into this public repo that way,
every one traceable to the path put *into* 24 prompts. Give a repo-relative brief and let
the agent resolve paths itself. (`AGENT.md` § PUBLIC repo; detail in
`agent/helpers/session_cleanup.md`.)

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
