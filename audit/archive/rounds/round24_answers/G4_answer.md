# R24-G4 Sonnet answer (magpie4 getReport dispatch)

## `magpie4::getReport` — Dispatch Pattern and Function Inventory

**Version**: magpie4 v2.70.0 @ SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355` (resolution: exact SHA, aligned with parent `input/renv.lock`).
**File**: `.cache/sources/magpie4/R/getReport.R`, 235 lines total.

---

### Signature and parameters

`.cache/sources/magpie4/R/getReport.R:56-57`:

```r
getReport <- function(gdx, file = NULL, scenario = NULL, filter = c(1, 2, 7),
                      detail = TRUE, level = "regglo", ...)
```

Parameters of note:

- `filter = c(1, 2, 7)`: keeps only timesteps where the GAMS modelstat is 1 (optimal), 2 (locally optimal), or 7 (feasible); all others are NA-filled.
- `detail = TRUE`: passes per-crop disaggregation into every function that accepts a `detail` argument; `FALSE` returns aggregated groups (e.g., "oilcrops" instead of individual crops).
- `level = "regglo"`: produces both regional and global aggregation by default; `"iso"` switches to per-country output. Some functions ignore this (e.g., `reportRuralDemandShares` has no `level` argument; `reportFeedConversion` omits it entirely).
- `file = NULL`: when non-NULL, calls `write.report2()` to write a `.mif`; otherwise returns a MAgPIE object.

---

### Dispatch pattern: flat `tryList`

The entire report generation is a single flat `tryList(...)` call, lines 62-182:

```r
output <- tryList(
  "reportPopulation(gdx, level = level)",
  "reportWorkingAgePopulation(gdx, level = level)",
  ...117 strings total...
  "reportBiochar(gdx, level = level)",
  gdx = gdx,
  level = level
)
```

`tryList` evaluates each string argument as an expression via `eval(parse(text = ...))` within a `tryCatch` block. If any individual `report*` call throws an error or warning-as-error, that entry returns `NULL` and execution continues with the next. The surviving (non-NULL) results are collected into a list.

There is **no conditional dispatch**. There are no `if`/`switch` branches, no config flags, no per-module guard clauses. Every entry runs unconditionally on every call to `getReport`, regardless of which MAgPIE modules were active in the run. Functions that read gdx variables not present in the output simply fail silently and return NULL (caught by `tryList`).

---

### Call counts: 117 total calls, 100 unique functions

Counting from `.cache/sources/magpie4/R/getReport.R:63-179`:

- **117 total string entries** in the `tryList` (verified with `grep -c '"report' getReport.R`).
- **100 unique `report*` function names** (verified with `grep -o '"report[a-zA-Z_]*(' ... | sort -u | wc -l`).

The 17 repeated calls arise from multi-argument variants of the same function:

| Function | Calls | Argument variants |
|---|---|---|
| `reportIncome` | 2 | `type='ppp'` / `type='mer'` |
| `reportYields` | 2 | `physical=TRUE` / `physical=FALSE` |
| `reportYieldsCropCalib` + `reportYieldsCropRaw` | 1 each | (separate functions, not repeated) |
| `reportGrowingStock` | 2 | `indicator='relative'` / `indicator='absolute'` |
| `reportPriceFoodIndex` | 2 | `baseyear='y2010'` / `baseyear='y2020'` |
| `reportAgEmployment` | 2 | `type='absolute'` / `type='share'` |
| `reportFactorCostShares` | 3 | `type='requirements'` / `type='optimization'` / `type='accounting'` |
| `reportWageDevelopment` | 3 | `baseYear=2000` / `2010` / `2020` |
| `reportFit` | 2 | `level='grid'` / `level='cell'` |
| `reportProcessing` | 2 | `indicator='primary_to_process'` / `indicator='secondary_from_primary'` |

**Correction to helper**: `agent/helpers/magpie4_reference.md` states 106 unique functions and 117 total calls. The actual count from the pinned file is **100 unique functions**. The helper's count is off by 6 and should be updated.

---

### Post-collection processing (lines 185-234)

After `tryList` returns:

1. `Filter(Negate(is.null), output)` drops any NULL entries from failed calls.
2. Region unification: all surviving magpie objects have `add_columns()` called to fill in any missing regions, so they can be `mbind()`-ed into a single object.
3. `.filtermagpie(mbind(output), gdx, filter = filter)` applies the modelstat filter — timesteps failing the filter criterion are NA-filled across all variables simultaneously.
4. The third set-dimension is renamed to `"variable"`.
5. Optional `scenario` and `"MAgPIE"` model dimensions are added.
6. A unit-format validation check warns if any variable name lacks a `(unit)` suffix in the required `name (unit)` format.
7. Output: written to file via `write.report2()` (from `magclass`) if `file` is non-NULL, otherwise returned as a MAgPIE object.

---

### Calling context

`magpie4::getReport` is invoked from MAgPIE proper at `scripts/output/rds_report.R:37` (per `agent/helpers/magpie4_reference.md`). It reads `fulldata.gdx` and produces the `report.mif` / `report.rds` consumed by downstream reporting pipelines.

---

**Source statement**:
- Primary: `.cache/sources/magpie4/R/getReport.R` (SHA-pinned clone, v2.70.0 @ `a360d8c9ec`, resolution: exact SHA). All call counts and line ranges verified by direct read this session.
- Secondary: `agent/helpers/magpie4_reference.md` (magpie4_reference helper, last updated 2026-05-24). Note: the helper's stated unique-function count (106) does not match the pinned source (100); the pinned source takes precedence.
- Not consulted: workspace clone at `~/Documents/Work/Workspace/magpie4/` (HEAD, v2.75.1, excluded per flywheel rules); raw GAMS modules (excluded per R24 rules).
