# Audit Report: R28 Q7 (G4 — magpie4 getReport dispatch structure)

**Regression anchor**: G4 (R-package structural anchor, rubric §6)
**Auditor**: Opus adversarial auditor, Round 28
**Date**: 2026-05-29
**Verification source**: `.cache/sources/magpie4/R/getReport.R` (read directly this session) — magpie4 v2.70.0 @ a360d8c9ec
**Latent-doc-bug target**: `agent/helpers/magpie4_reference.md` (read directly this session)

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10

---

## Computed Ground Truth (from the actual pinned file)

All numbers below were computed THIS session from `.cache/sources/magpie4/R/getReport.R`, not taken from any doc.

| Metric | Value | How computed |
|---|---|---|
| **Total `report*(` call lines** | **117** | `sed -n '62,181p' getReport.R \| grep -cE 'report[A-Za-z0-9_]+\('` |
| **Unique `report*` functions** | **106** | `sed -n '62,181p' getReport.R \| grep -oE 'report[A-Za-z0-9_]+\(' \| sort -u \| wc -l` |
| **tryList line range** | **62–181** (open `tryList(` at 62; calls 63–179; positional terminator args `gdx=gdx`, `level=level` at 180–181; `)` at 182) | direct read |
| **File length** | **235 lines** | `wc -l` |
| **Difference (117 − 106)** | **11**, fully reconciled | 9 functions called >1×: 7 called twice (+7), 2 called 3× (+4) → +11 |

**Reconciliation of repeats** (within tryList block 62–181):
- `reportFactorCostShares` ×3 (type ∈ requirements/optimization/accounting)
- `reportWageDevelopment` ×3 (baseYear 2000/2010/2020)
- `reportAgEmployment` ×2 (type absolute/share)
- `reportFit` ×2 (level grid/cell)
- `reportGrowingStock` ×2 (indicator relative/absolute)
- `reportIncome` ×2 (type ppp/mer)
- `reportPriceFoodIndex` ×2 (baseyear 2010/2020)
- `reportProcessing` ×2 (indicator primary_to_process/secondary_from_primary)
- `reportYields` ×2 (physical TRUE/FALSE)

Sum of (count−1) = (3−1)+(3−1)+(2−1)×7 = 2+2+7 = 11 = 117 − 106. ✓ Internally consistent.

### Note on the 108-vs-106 discrepancy (latent-doc-bug check)

The answerer flagged that the helper mentions a "108-vs-106 discrepancy." I investigated whether the helper states a stale/wrong count.

- **Naive (wrong) count = 108**: `grep -oE 'report[A-Za-z0-9_]+' getReport.R | sort -u | wc -l` (NO `(` anchor, whole file) returns 108. This is wrong because it captures `report2` (from `write.report2` on lines 49 and 231) and counts it as a "report function," and scans outside the tryList block.
- **Correct count = 106**: anchoring on the open paren `report[...]+\(` and restricting to the tryList block (62–181) yields 106.

The helper (`magpie4_reference.md`) handles this correctly:
- Line 42: "a flat `tryList(...)` of **117** unconditional calls to **106** unique `report*` functions" ✓
- Line 261 (Common Pitfalls #5): "Plan said **108** unique report* functions — actual count is **106**. ... count from `getReport.R` if precision matters." ✓

**Conclusion: NO latent doc bug.** The helper documents the correct value (106) and explicitly warns against the obsolete 108. The 108 is a deprecated planning-doc figure, correctly retired in both the helper and the answer. No `doc_error_answerer_beat_it` is recorded.

---

## Verified Claims (correct)

1. **Dispatch = flat, unconditional `tryList(...)`** — CONFIRMED. `output <- tryList(` opens at line 62; all calls are passed as positional character strings; terminated by named args `gdx = gdx`, `level = level` (lines 180–181). No branching wraps the calls.
2. **NO `control` argument** — CONFIRMED. Signature (lines 56–57): `getReport <- function(gdx, file = NULL, scenario = NULL, filter = c(1, 2, 7), detail = TRUE, level = "regglo", ...)`. No `control` param. `grep -nE 'control'` on the file returns nothing.
3. **NO `if(any(grepl(...)))` gating** — CONFIRMED. `grep -nE 'grepl'` returns nothing in the dispatch region; the only `grepl` uses are in the post-dispatch unit-validation block (lines 211–224), unrelated to call gating.
4. **117 total call lines** — CONFIRMED (computed above).
5. **106 unique `report*` functions** — CONFIRMED (computed above).
6. **Difference of 11 from multi-arg repeats** — CONFIRMED and reconciled (answer says "difference of 11"; exact).
7. **File:line range `62-181`** — CONFIRMED. tryList opens at 62; last `report*` call (`reportBiochar`) at line 179; the terminator args and close paren at 180–182. `62-181` is an accurate characterization of the tryList block (the rubric expected "~62-181"). Exact match.
8. **File length ~235 lines** — CONFIRMED. `wc -l` = 235.
9. **Signature reproduced exactly** — CONFIRMED against lines 56–57.
10. **`reportharvested_area_timber` snake_case caveat** — CONFIRMED. Line 147: `"reportharvested_area_timber(gdx, level = level)"`. Genuinely snake_case; the "do not auto-correct" note is correct.
11. **Post-dispatch behavior** (unify regions, filter incomplete timesteps via `.filtermagpie`, validate units, return-or-write on `file`) — CONFIRMED against lines 187–234.
12. **Invoked by `scripts/output/rds_report.R:37`** — matches the helper (line 42); not independently re-verified against the MAgPIE-proper script this session, but consistent with the documented entry point and not load-bearing to the G4 question.
13. **Version pin v2.70.0 @ a360d8c9ec** — consistent with the helper's pin and the question's stated pin.

---

## Bugs Found

**None.** No Critical, Major, Minor, or Informational content bugs.

The two anti-confabulation traps this anchor guards against were both avoided:
- The answer did NOT confabulate a `control`-based or `grepl`-filtered dispatch (the magpie4 plan's original-but-wrong description). It correctly states the dispatch is flat and unconditional, and explicitly says there is no control arg / no grepl gating.
- The count is correct (106 unique / 117 total), not the obsolete 108, and the answer explicitly tells the reader not to cite 108.

Per rubric §6 G4: off-by-few count = Minor, off-by-order = Critical. The count is **exact**, so neither applies.

---

## Missing Nuances (non-scoring)

1. **Epistemic tagging is conservative (Informational-only, no score impact).** The answer's closing block (line 67) states the raw source file `getReport.R` "was NOT read per test constraints" and tags the counts/line-range as 🟡 Documented (taken from the helper), not 🟢 Verified. This is honest disclosure and the numbers are correct, so it is not a content error. It is at most a §1 Informational item (conservative tag where the underlying facts are sound) and costs no points. Worth noting only because the question explicitly asks to "cite the file:line range from the pinned clone" — the answer cites the right range but did not itself open the file. The helper, which the answer relied on, IS correct, so the chain is sound.
2. The answer's "Thematic Coverage" (11 areas) and the snake_case caveat are accurate value-adds drawn from the helper; not required by the question but correct.

---

## Summary

R28 Q7 (G4) is **ACCURATE — 10/10, no drift**. Every load-bearing claim was verified directly against the pinned `getReport.R`: the dispatch is a flat unconditional `tryList(...)` (no `control` arg, no `grepl` gating), with **117 total call lines** to **106 unique `report*` functions** (difference of 11 fully reconciled against 9 multi-arg-repeated functions), spanning lines **62–181** in a **235-line** file. The 108-vs-106 discrepancy was investigated: the helper correctly documents 106 and retires the obsolete 108, so **no latent doc bug** is recorded. The answer dodged both G4 confabulation traps (fake control/grepl dispatch; stale 108 count). The only observation is a conservative 🟡 tag where the facts were correct (Informational, no score impact).

`drift_observed: false`. Anchor remains stable at the top of its band.

**Source (epistemic hierarchy)**: 🟢 Verified — `.cache/sources/magpie4/R/getReport.R` (v2.70.0 @ a360d8c9ec) and `agent/helpers/magpie4_reference.md`, both read and computed against this session.
