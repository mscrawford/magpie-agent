# Seeded-bug benchmark — what fraction of real doc bugs does the gate actually catch?

**Run** 2026-07-20 · `audit/tools/seed_known_bugs.py` · detail in the run's `--json` output.

## Why this number did not exist before

Every quality figure this project reports is **self-play**: the agent answers, the
agent scores. `validation_rounds.json`'s means and the 9.52 corpus figure both
measure *"few bugs found at that depth/FNR"*, not *"few bugs exist"* — R54/R55
found 9-month-old Criticals that had survived repeated green passes. A checker
battery reporting 0 findings is indistinguishable from one that cannot see.

This benchmark asks the missing question directly: **take bugs that were real,
put them back, count how many the gate catches.**

## Method

Reverse-apply, not replay. Checking out a pre-fix doc and running the checkers
would confound DETECTION with CODE DRIFT — an old doc judged against today's
GAMS source, where a "miss" might only mean the code moved. Instead each fix
commit is split into hunks and **one hunk at a time is reverse-applied to
today's doc**: the exact historical wrong claim, in an otherwise-current corpus,
judged against current code. Drift is eliminated by construction; every finding
is attributable to one hunk.

Controls: a clean baseline (only findings *not* in it count, so advisory noise
cannot inflate the rate); a positive control (the run aborts rather than
reporting a clean 0% if nothing is caught); and a vacuity check (a hunk that
fails to apply is SKIPPED, never silently a miss).

## Headline

| | |
|---|---|
| Real bugs reinjected and measured | **46** |
| Caught by at least one checker | **14** |
| **Detection rate** | **30.4%** |

Raw output was 32.7% (16/49). Three hunks only *added* an explanatory banner, so
reversing them injects no wrong claim; excluding them gives 30.4%. **Note the
correction moved the rate DOWN, not up** — two of those three were being counted
as catches. The bias was predicted in the wrong direction before it was measured.

## By bug class — this is the actionable part

| Class | Caught | Reading |
|---|---|---|
| `attribution_phantom` | **2/2** | mechanized and working |
| `diagram_phantom` | **1/1** | mechanized and working (Check 39) |
| `attribution_read` | 10/26 | partial — the mechanized half fires |
| `set_membership` | 1/2 | partial |
| `attribution_set` | **0/5** | 🔴 blind spot, and the largest |
| `mixed` | **0/4** | 🔴 blind spot |
| `attribution_role` | **0/2** | 🔴 blind spot |
| `citation` | **0/2** | 🔴 blind spot |
| `mechanism` | **0/1** | 🔴 blind spot (known LLM territory by decision) |
| `data_source` | **0/1** | 🔴 blind spot |

Four checkers never fired on any seeded bug: `check_attribution_tables`,
`check_role_attribution`, `check_doc_var_existence`, `check_gams_variables`.
That is not proof they are broken — their classes may simply be absent from this
sample — but it is the first evidence either way.

## The biggest blind spot, diagnosed

`attribution_set` is 0/5, and the mechanism is understood rather than guessed.
The `module_59` R58 **Critical** (wrong dependency set) reads:

```
**Provides to**: Module 52 (carbon stocks for topsoil component)
**Depends on**: Modules 10 (land), 30 (croparea), 29 (cropland).
```

It names **zero interface variables**. Every attribution checker is
*var-anchored*, so there is nothing to bind and nothing to verify. Check 37
already sizes the class: **570 of 960 attribution lines (59%) are unbindable.**

So the single highest-leverage mechanical fix is to make module-level
attribution claims bindable — either by requiring docs to name the interface
variable, or by teaching the checkers to resolve a bare module list against the
declaring module's full interface set.

## How to read 30.4% — and how not to

- It does **not** mean 70% of doc bugs go undetected forever. Every bug in this
  sample *was* eventually found — by expensive, FNR-limited LLM audits
  (R54/R55/R58/R59), not by the gate.
- It **does** mean the deterministic gate, which runs in seconds and gates every
  commit, currently covers about a third of the bug classes that have
  historically mattered. The rest still depend on audits.
- The per-class split matters more than the aggregate: the classes that were
  *deliberately mechanized* score 2/2, 1/1 and 10/26, while the never-mechanized
  ones score 0. That is the same natural experiment R55 found, reproduced from
  the opposite direction — and it is the strongest evidence yet that
  mechanization is the lever.

## Caveats

- **n=46 from 12 commits**, weighted toward recent attribution work, so the class
  mix is not a random sample of all doc bugs.
- A "catch" means *some* checker emitted a new finding on that doc. It is not
  verified that the finding *names the same defect* — a coincidental unrelated
  flag on the same file would count. This inflates the rate; the per-class
  pattern (0/5, 0/4, 0/2 …) suggests the effect is small, but it is unmeasured.
- Skipped hunks (4) are ones that no longer apply to today's text.
