# Stable check-ID refactor — sizing only, NOT started

**Plan C item R7.** The backlog has carried this as "the single gate" blocking removal of
three zero-catch tombstones (Checks 4, 23, 26) and the droppable inline Checks 1/2/6, with
the reactivation gate reading *"when someone takes it on."* That is an unpriced estimate.
This prices it. **No code was changed.**

## Measured blast radius

| Surface | by-number `Check N` references | files |
|---|---:|---:|
| `scripts/` (the validator + checkers themselves) | 128 | — |
| `audit/` live (backlog, rounds ledger, tools, lessons) | 154 | — |
| Live docs (`modules/`, `core_docs/`, `cross_module/`, `reference/`, `agent/`, `AGENT.md`) | 75 | — |
| **Live total** | **357** | **95** |
| `audit/archive/` — immutable round history | 327 | 39 |
| **Grand total** | **684** | **134** |

## Why the archive number is the decisive one

327 of the 684 references live in `audit/archive/` — round designs, findings files and
`validation_rounds.json` entries that cite a check *by the number it had at the time*.
Those are a historical record; rewriting them would falsify what a past round actually
reported, and **not** rewriting them means the same numeral means two different checks
depending on which file you are reading. Neither branch is free, and that is the real
cost, not the 357 live edits.

This is why the refactor is genuinely hard rather than merely tedious. A rename with
sed is a two-hour job; deciding what a historical citation *means* after renumbering is
a design decision.

## What it would actually buy

Three inert tombstones and three droppable inline checks:

- `scripts/validate_consistency.sh:320` — Check 4, "Duplicate Equations". Retired
  2026-06-07: it only ever called `check_pass`, so it was structurally incapable of
  failing.
- `:938` — Check 23, multi-section dimension consistency. Retired at **zero lifetime
  catches** with a perpetual false-positive floor.
- `:1010` — Check 26, unit claims. Same: zero lifetime catches, perpetual FP floor.
- Inline Checks 1, 2, 6 — flagged droppable, not zero-catch-verified.

All six are **inert today**. They cost a few lines of stubbed shell and one numbered
comment each. They do not run, do not slow the gate, and do not emit findings.

## Recommendation: DO NOT DO THIS

The benefit is cosmetic — deleting six no-ops — and the cost is 684 references across 134
files, half of them in a record that arguably must not be rewritten at all. The gate does
not get faster, more accurate, or easier to trust.

**A cheaper alternative that captures most of the value:** leave the numbering alone and
add a one-line `RETIRED:` marker to each tombstone comment naming the retirement date and
reason (all three already carry the reason in prose). That makes the dead entries
self-describing to a reader without touching a single reference elsewhere. Roughly ten
minutes.

**If it is ever taken on anyway**, the order that keeps it reversible: (1) introduce
stable string IDs *alongside* the numbers, changing nothing; (2) migrate live surfaces to
the string IDs, leaving numbers as aliases; (3) only then consider whether the archive
needs anything at all — probably not, since by then the numbers are aliases rather than
identity.

## Status

**Sized, recommendation recorded, not started.** The backlog gate should change from
"when someone takes it on" to "not worth doing; see this file" unless a concrete need
appears that the ten-minute alternative cannot serve.
