# Reader blind spots — when the checker, not the corpus, is the constraint

**Date**: 2026-07-19
**Branch**: `fix-attribution-bare-labels` (2 commits, checker-only, no doc edits)
**Origin**: fell out of the P0 regularization pilot (`audit/regularization_p0_result.md`)

## The finding

`check_attribution_tables` reported coverage of **4/46 module docs** for ~59 audit rounds. That number was read as "the corpus expresses attribution as prose; migrate it to tables." The P0 pilot was designed on that premise.

The premise was substantially wrong. A large share of the gap was that **the checker could not read conventions the docs already use**:

| Blocker | Cost | Fix |
|---|---|---|
| `**70** (Livestock)` — bare module number, no `Module`/`M` prefix, no `NN_name` form | 51 rows / 4 docs | `MODNUM_LABEL_RE` |
| `\| Variable \| Provider \|` — reversed column order | 33 rows / 6 docs | reversed-layout fallback |

```
 62 rows /  4 docs   original baseline
146 rows / 14 docs   after ~90 lines of checker changes, ZERO doc edits
```

For scale, the LLM regularization pilot produced +36 rows / +3 docs for ~790k tokens and 5 injected meaning-changes. The reader fix produced **+84 rows / +10 docs for ~0 tokens and 0 injected errors**.

Reading the reversed layout is semantically safe because this check's membership test is **direction-agnostic** — it asks only whether the claimed module references the variable at all, so which column holds which does not change the question being asked. That property is what makes the relaxation legitimate rather than merely convenient; a direction-sensitive check could not take it.

## Two negative results — do not re-attempt

**Wider heading vocabulary gains exactly zero rows.** Tested `interface variables`, `inputs`, `outputs`, `upstream`, `downstream`, `depends on`, `used by`, `module connections`, `consumed by`. An audit had attributed 67 unread rows to "heading fails SECTION_RE"; that attribution was wrong. Those tables are **double-blocked** — reversed *and* oddly headed — so the heading was never the binding constraint. Adding heading forms is pure surface area for no coverage.

**A coverage number that goes up is not self-validating.** The reversed-column branch initially read module numbers out of citation paths, so a declaration-reference table

```
| `vm_cost_transp` | `modules/40_transport/gtap_nov12/declarations.gms:13` |
```

counted as an M40 attribution row — 36 such rows in `module_11` alone. Every one was code-consistent (M40 genuinely declares it), so **it produced zero findings**, which is what makes it insidious. A citation is a file location, not an attribution claim; counting it inflates the coverage denominator with rows that were never in scope. `CITE_PATH_RE` now masks paths before col-2 is read as a module cell.

## The generalisable lesson

Three separate over-counts occurred while establishing these numbers, all the same shape: **treating a module number found anywhere in a cell as an attribution claim**. Two were in throwaway diagnostics, one reached the checker itself.

> A rising coverage number must be validated by inspecting *which rows* got counted, not by the total moving in the right direction — and especially not by "0 findings", which is equally consistent with "the new rows are correct" and "the new rows were never claims at all".

This is the coverage-denominator analogue of the rule the checkers already print in their own output (*"0 findings within covered rows — NOT a corpus-clean claim"*). The denominator needs the same scepticism as the numerator.

## What this implies for the doc project

"Migrate before automating" was the wrong prescription here; the reader was the bug. Before commissioning any doc migration to satisfy a checker, first ask **what shapes the checker cannot read**, because doc edits are expensive and risky (the pilot injected ~2 meaning-changes per genuinely-prose doc) while reader fixes are cheap and carry no meaning-change risk at all.

Open question worth the same treatment: the bare-label gap went unnoticed across ~59 rounds. Other checks in the 48-check suite report their own coverage denominators, and no one has asked which of those are reader-limited rather than corpus-limited.

## Tier 2 — the same treatment applied to the prose checkers

**Shipped: `check_attribution_prose` no longer requires backticks.** Its var extractor scanned only inside backticks, so recall was hostage to a cosmetic convention — `**Module 52 (Carbon)** - directly reads im_forest_ageclass` was unchecked purely because the identifier was unwrapped.

```
pairs  211 -> 305      docs  37/46 -> 41/46      findings 0
```

Safe because precision never depended on the backticks: candidates still pass `CROSS_IFACE_RE` **and** `is_interface_var()` against real code. Newly covered: `module_28`, `module_34`, `module_41`, `module_50`, spot-verified as genuine and code-consistent.

**NOT shipped: the same widening on `check_attribution_omissions`.** It raises coverage (155 -> 178 triples, 33 -> 38 docs) and surfaces 10 findings where there were 0 — but 2 are **false positives my own change introduced**. Bare extraction pulled this counts-heavy line into scope:

```
2. Update ALL consumer modules to handle new type (10 direct vm_land consumers;
   18 total when including consumers of other Module 10 interface variables ...)
```

`10` and `18` are counts. This checker's multi-module *list* logic reads numerals as module numbers, so a prose line full of counts becomes a phantom attribution claim. `check_attribution_prose` is immune because it requires a trigger verb and handles single-module lines; the list-parsing checker is not. **Prerequisite before widening it: make multi-module list parsing require the `Module NN` / `M NN` / `NN_name` forms rather than bare digits.**

**Excluded by design: `check_role_attribution`.** Its `BACKTICK_VAR_RE` matches any `[a-zA-Z][a-zA-Z0-9_]*`, with no `is_interface_var` gate — the backticks *are* its precision mechanism. Widening it would match ordinary English. The lesson: this dialect fix is safe only where a ground-truth filter sits behind the backticks. `check_attribution_omissions` and `check_consumer_attribution` have that filter; `check_role_attribution` does not.

## Provenance note

The 2026-07-15 coverage-control work that first surfaced "4/46" was correct in its *observation* and correct in its method (instrument the real scan function, never a re-implementation). Its *diagnosis* — that the uncovered docs expressed attribution as prose, hence "the next build is a prose parser" — is what this document corrects, and that inference is what the P0 pilot was designed on. The global memory recording it has been updated in place rather than duplicated here, with the correction and the falsely-large-denominator extension folded in.
