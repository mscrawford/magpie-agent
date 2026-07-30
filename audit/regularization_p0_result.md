# P0 — gated regularization pilot: RESULT

**Date**: 2026-07-19
**Branch**: `regularize-p0` (**DO NOT MERGE** — see verdict)
**Design**: followups §H (3 docs, Pass A only, deterministic invariance gate, adversarial audit)
**Baseline**: `audit/regularization_p0_baseline.json`

## Verdict: DO NOT PROCEED to the full corpus

The design pre-registered four criteria and the rule "proceed to the full 53 only if **all four** hold." Three hold. Criterion 3 does not.

| # | Criterion | Result |
|---|---|---|
| 1 | Invariance gate: 0 violations across all 3 docs | ✅ **PASS** — 0 violations |
| 2 | At least one checker's doc-coverage rises ≥50% relative on the pilot docs | ✅ **PASS** — 0/3 → 3/3 docs; corpus 62 → 98 rows, 4/46 → 7/46 docs |
| 3 | 0 confirmed injected errors | ❌ **FAIL** — 4 confirmed |
| 4 | Gate stays 48 checks / 0 errors | ✅ **PASS** — 48 checks, 46 passed, 2 warnings, 0 errors |

Coverage numbers are per-doc measurements through the real `scan_doc`, not a reimplementation. The gate run and all four error confirmations were re-derived independently against the GAMS source, not accepted from the agents' self-reports.

## The four confirmed injected errors

`module_13.md` was **clean**. All four errors are in `module_14.md` (3) and `module_16.md` (1).

**1. `module_16.md` — a hedge was deleted, turning a non-exhaustive list into an enumeration.** *(most serious)*
Original: `fm_attributes` ... **is read by many modules** (18_residues, 20_processing, 53_methane, 55_awms, 50_nr_soil_budget). The rewrite dropped "is read by many modules" (`grep -c "many modules"`: 1 before → 0 after) and promoted the five parenthesised modules into the Module column of a "Provides To" table. Actual readers are eight: `15_food`, `60_bioenergy`, `70_livestock` are omitted, and `60_bioenergy` is an equation-level reader (`modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:17,74,75`). The table now reads as the complete consumer set. It is not.

**2. `module_14.md` — a declared domain signature was lost doc-wide.**
`pm_yields_semi_calib(j,kve,w)` → `pm_yields_semi_calib`; occurrences went 1 → 0, so the dimensionality now appears nowhere in the doc. Ground truth: declared over `(j,kve,w)` at `modules/14_yields/managementcalib_aug19/declarations.gms:19`. `kve` includes pasture, so a reader now infers a crop-only parameter. Asymmetric with the other three §7.1 outputs, which each retain a `**Dimensions:**` line — so this reads as accidental.

**3. `module_14.md` — a net-new realization qualifier.**
Row: `| M 17 | pm_yields_semi_calib | sole consumer of this variable (Production realization flexreg_apr16) |`. The original asserted sole-consumership unconditionally. `flexreg_apr16` occurrences: 3 → 4. Vacuous in fact (`modules/17_production/` has exactly one realization) but it is net-new asserted text — the mirror image of a lost qualifier, and out of scope for Pass A.

**4. `module_14.md` — §16.3 hardened an ambiguous parenthetical into a false pairing.** *(weakest)*
Original prose: `**Module 52 (Carbon):** Plantation, secondary forest, and other natural land carbon density (pm_carbon_density_other_ac) → timber yields`, where the parenthetical attaches by proximity to the last item. As a `Module | Variable | Notes` row, the Variable cell reads as *the* identifier carrying the Notes relationship, asserting all three densities travel via `pm_carbon_density_other_ac`. They are three separately declared parameters (`modules/52_carbon/normal_dec17/declarations.gms:9`, `:11`, `:12`). The original was already sloppy; the table forecloses the reading that was correct.

## Root cause: one gap, not four

All four errors share a single mechanism. **The gate's invariants are token-identity-based**, so anything that is not a prefixed identifier, a numeral, a fence body, or a citation is invisible to it. Three of the four classes are mechanically closeable:

| Class | Error | Closeable? |
|---|---|---|
| Domain signatures — set names inside `(...)` are not identifiers | 2 | **Yes** — track `ident(domain)` pairs as a fifth invariant |
| Hedge / quantifier words adjacent to enumerations ("many", "including", "e.g.", "among others") | 1 | **Yes** — track a hedge-word multiset |
| Net-new prose tokens with no numeral and no identifier prefix — realization names, `NN_name` module directories | 3 | **Yes** — track realization and module-directory tokens |
| Structural promotion (prose → table) changing a claim's scope | 4 | **Not obviously** — genuinely semantic |

Verified empirically, not inferred: `compare()` on `pm_yields_semi_calib(j,kve,w)` → `pm_yields_semi_calib` returns **no violations**. `22_land_conservation` yields zero identifiers and zero numerals, so the entire Module column of a migrated table is new claim surface the gate never sees.

## Two secondary findings

**`check_attribution_tables.py` silently drops any data row whose column 1 begins with "Module".** `HEADER_CELL_RE` matches the literal word `module`, so `| Module 14 | vm_tau |` is treated as a second header row and never evaluated. Probe:

```
col1='Module 14'  -> rows_evaluated=0
col1='M14'        -> rows_evaluated=1
col1='M 14'       -> rows_evaluated=1
col1='14_yields'  -> rows_evaluated=1
```

All three regularizers hit this independently and worked around it. **Hypothesis tested and DISCONFIRMED**: patching the regex adds **0 rows across the corpus**, so this is not a hidden coverage suppressor — the 4/46 baseline is genuine, not an artifact. Still worth fixing defensively: it is a silent trap for future doc authors, and "Module 14" is the most natural way to write the cell.

**A gate bug found by one of the regularizers.** `main()` called `compare(before, after)` without `label=`, so the own-module-number carve-out never fired in real CLI use and violation messages lacked the doc prefix. Fixed. Consequence for this pilot: all three docs were gated under a **stricter** regime than designed, which makes the criterion-1 pass stronger evidence, not weaker.

## What this does and does not establish

- ✅ The gate works. It caught every planted error in 18 synthetic cases and accepted 18/21 docs of a real historical pure-form commit (`e982a76`), with all 3 rejections verified correct.
- ✅ Coverage headroom is real: 36 new machine-checkable rows from 3 docs, 0 phantom findings among them.
- ❌ It does **not** establish that Sonnet regularization is safe to batch. 4 errors in 3 docs is a rate that would put ~60 meaning changes into a 46-doc corpus.
- ⚠️ "0 findings" on the 36 new rows is a **weak** signal. `check_attribution_tables` only asks whether the claimed module references the variable *at all* — it cannot detect a direction flip or a wrong pairing. Error 4 sits in a row that the checker reports as clean.

## Gate v2 — the three blind spots, closed and validated (same day)

Added invariants (e) domain signatures, (f) hedges/quantifiers, (g) module-directory and realization tokens. Each is pinned in the self-test to the **real pilot error it closes**, not to a fixture (the R56 discipline).

Run against the actual pilot diffs (`--git-diff da8e198`), gate v2 catches **3 of 3** mechanizable errors:

| Pilot error | Caught by |
|---|---|
| 1. hedge "many" dropped | `HEDGES/QUANTIFIERS: - many` (`module_16`) |
| 2. `pm_yields_semi_calib(j,kve,w)` domain lost | `DOMAIN SIGNATURES` (`module_14`) |
| 3. net-new `flexreg_apr16` | `MODULE-DIR / REALIZATION` (`module_14`) |

Error 4 (structural promotion changing scope) remains uncaught, as predicted — it is genuinely semantic.

**Correction to this document's own earlier finding.** `module_13.md` was reported clean above. It was not. Gate v2 shows all **7** domain signatures stripped from its migrated table, and for `pcm_land` and `pm_land_conservation` those were the doc's only indexed mentions, so their dimensionality is now recorded nowhere. Its auditor did flag this; it was filed as a benign gate-blind observation and should have been counted. The corrected error tally is **5, across all three docs** — criterion 3 fails either way, but "module_13 was clean" was too generous.

**Reviewed-additions mode** (H.7): token *removals* are fatal; token *additions* are surfaced for sign-off and block only under `--strict`. Pilot error 3 was an addition, so additions are never silent. Without this split the gate would reject every legitimate migration and stop measuring safety.

**False-positive regression: zero.** Gate v2 on commit `e982a76` accepts the same 18/21 docs as v1, with the same 3 rejections (all previously verified correct). The three new invariants add no noise on a real pure-form corpus.

Self-test: **22 cases, PASS**.

## Recommended next step

Not a full-corpus run. Close the three mechanizable blind spots in the gate (est. a few hours, deterministic, self-testable against these four errors as real historical positives — the R56 pattern), then re-run this identical 3-doc pilot. If the strengthened gate catches errors 1-3 on the current diffs, that is a real result and the batch question can be re-asked with a gate that has been sharpened by a known failure rather than by a fixture.

The pilot cost ~5% of a full-corpus pass and returned a precise, actionable diagnosis. That is the outcome it was bought for.
