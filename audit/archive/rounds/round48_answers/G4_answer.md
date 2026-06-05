# G4 Answer: `magpie4::getReport` dispatch pattern

**Version pin**: magpie4 v2.70.0 @ SHA `a360d8c9ec`
**Source file**: `.cache/sources/magpie4/R/getReport.R` (all line citations below are for this pin)

---

## Function signature

```r
getReport <- function(gdx, file = NULL, scenario = NULL, filter = c(1, 2, 7),
                      detail = TRUE, level = "regglo", ...)
```

Source: `.cache/sources/magpie4/R/getReport.R:56-57` (v2.70.0 @ a360d8c9ec)

Parameters:

| Argument | Default | Purpose |
|---|---|---|
| `gdx` | (required) | Path to `fulldata.gdx` |
| `file` | `NULL` | If non-NULL, write output to this path via `write.report2()`; if NULL, return as MAgPIE object |
| `scenario` | `NULL` | If non-NULL, add a `scenario` dimension to the output |
| `filter` | `c(1, 2, 7)` | Modelstat values to keep (1 = optimal, 2 = locally optimal, 7 = feasible); timesteps with other modelstats get NA-filled |
| `detail` | `TRUE` | `TRUE` = crop-specific outputs; `FALSE` = aggregated (e.g., "oilcrops" rather than "soybean") |
| `level` | `"regglo"` | Aggregation level: `"regglo"` (regional + global), `"iso"` (per-country), or a mapping name |
| `...` | — | Passed to `write.report2()` only when `file` is non-NULL |

There is **NO `control` argument** of any kind.

---

## Dispatch pattern

`getReport` uses a single flat `tryList(...)` call that wraps **117 string-quoted call expressions** (lines 63-179). Each string is evaluated by `tryList`; failures are caught per-element so one broken `report*` function does not abort the entire report.

The dispatch block spans:

- **`tryList(` open**: line 62
- **first call** (`"reportPopulation(...)"`) : line 63
- **last call** (`"reportBiochar(...)"`) : line 179
- **`tryList` close** (with `gdx = gdx, level = level` positional env args): lines 180-182
- **Full `getReport` function body**: lines 56-235

There is **no `if (any(grepl(...)))` filtering** and no conditional dispatch of any kind. Every `report*` call string is passed to `tryList` unconditionally — the dispatch is purely flat and exhaustive.

---

## Number of unique `report*` functions

- **Total call strings in `tryList`**: 117
- **Unique `report*` function names**: **106**

The 117 vs. 106 discrepancy arises because 11 functions are called more than once with different arguments:

| Function | Call count | Distinguishing argument |
|---|---|---|
| `reportIncome` | 2 | `type='ppp'` / `type='mer'` |
| `reportYields` | 2 | `physical = TRUE` / `physical = FALSE` |
| `reportGrowingStock` | 2 | `indicator='relative'` / `indicator='absolute'` |
| `reportAgEmployment` | 2 | `type = 'absolute'` / `type = 'share'` |
| `reportFactorCostShares` | 3 | `type = 'requirements'` / `'optimization'` / `'accounting'` |
| `reportProcessing` | 2 | `indicator = 'primary_to_process'` / `'secondary_from_primary'` |
| `reportPriceFoodIndex` | 2 | `baseyear = 'y2010'` / `baseyear = 'y2020'` |
| `reportWageDevelopment` | 3 | `baseYear = 2000` / `2010` / `2020` |
| `reportFit` | 2 | `level = 'grid'` / `level = 'cell'` |

Total multi-call inflation: `1+1+1+1+2+1+1+2+1 = 11` extra calls, so `106 + 11 = 117`. Confirmed by grepping with numeric-suffix pattern (required to catch SDG1/SDG2/SDG3/SDG6/SDG12/SDG15):

```bash
grep -o '"report[A-Za-z0-9_]*(' .cache/sources/magpie4/R/getReport.R | sort -u | wc -l
# => 106
```

---

## Post-dispatch processing (lines 185-235)

After `tryList` returns:

1. **NULL-filter**: `Filter(Negate(is.null), output)` removes any failed calls (line 188).
2. **Region unification**: all MAgPIE objects are padded to the union of all regional dimensions so mismatched levels can be bound (lines 189-191).
3. **Modelstat filter**: `.filtermagpie(mbind(output), gdx, filter = filter)` NA-fills timesteps whose modelstat is not in `filter` (line 194). This is where `filter = c(1, 2, 7)` takes effect — it is NOT applied before dispatch, only to the assembled output.
4. **Dimension labeling**: `getSets(output)[3] <- "variable"` (line 196).
5. **Optional `scenario` and `model` dimensions** added (lines 198-205).
6. **Unit validation**: warns if any variable name lacks a `(unit)` suffix (lines 211-224).
7. **Output**: `write.report2()` if `file` non-NULL, else `return(output)` (lines 230-234).

---

## Key negative findings

- **No `control` argument**: the function signature has no such parameter. Every `report*` call runs on every `getReport()` invocation.
- **No `if (any(grepl(...)))` filtering**: there is no conditional dispatch, no keyword gating, no feature-flag mechanism inside `getReport`. The `grepl` pattern does appear in the post-dispatch unit-validation block (line 211: `!grepl("\\(.*\\)", ...)`) but this is a unit-string format check on output variable names, not a dispatch filter.
- **`filter` argument is a post-assembly modelstat filter**, not a pre-dispatch selector of which `report*` functions to call.

---

## Epistemic status

- Source: 🟢 Verified — read `.cache/sources/magpie4/R/getReport.R` (entire file, 235 lines) this session, from the SHA-pinned clone.
- Pin alignment: `project/version_pins.json` records v2.70.0 @ a360d8c9ec; `resolution = "sha"` (exact SHA checkout, not tag fallback).
- Line numbers are valid for v2.70.0 @ a360d8c9ec. If the pin advances, re-verify.
