# Anchor G4: magpie4::getReport dispatch pattern

**Pin**: magpie4 v2.70.0 @ a360d8c9ec  
**Source file**: `.cache/sources/magpie4/R/getReport.R` (235 lines total)  
**Doc source**: `agent/helpers/magpie4_reference.md`

---

## Signature and parameters

```r
# .cache/sources/magpie4/R/getReport.R:56-57
getReport <- function(gdx, file = NULL, scenario = NULL, filter = c(1, 2, 7),
                      detail = TRUE, level = "regglo", ...)
```

Key parameters:
- `filter = c(1, 2, 7)` — keeps modelstat values "optimal", "locally optimal", "feasible"; NA-fills others
- `detail = TRUE` — per-crop disaggregation; `FALSE` aggregates (e.g., "oilcrops" instead of "soybean")
- `level = "regglo"` — both regional and global; `"iso"` = per-country

---

## Dispatch pattern: flat `tryList` of quoted strings

The entire dispatch is a single flat `tryList(...)` call (lines 62-182). Each entry is a **quoted string** containing one `report*` call; `tryList` evaluates them sequentially and catches per-function failures so one broken call does not abort the whole report.

There is NO conditional dispatch — no `if (any(grepl(...)))`, no `switch()`, no `control` argument. Every call runs unconditionally on every invocation.

```r
# .cache/sources/magpie4/R/getReport.R:61-183
t <- system.time(
  output <- tryList(
    "reportPopulation(gdx, level = level)",
    "reportWorkingAgePopulation(gdx, level = level)",
    ...
    "reportBiochar(gdx, level = level)",
    gdx = gdx,
    level = level
  )
)
```

---

## Call counts (verified from pinned source)

| Metric | Count |
|---|---|
| Total quoted call strings in `tryList` | 117 |
| Unique `report*` function names | 101 |
| Functions called >1x (different arg variants) | 9 |

Functions called multiple times with different arguments:
- `reportWageDevelopment` — 3x (baseYear 2000 / 2010 / 2020)
- `reportFactorCostShares` — 3x (type = 'requirements' / 'optimization' / 'accounting')
- `reportYields` — 2x (physical = TRUE / FALSE)
- `reportProcessing` — 2x (indicator = 'primary_to_process' / 'secondary_from_primary')
- `reportPriceFoodIndex` — 2x (baseyear = 'y2010' / 'y2020')
- `reportIncome` — 2x (type = 'ppp' / 'mer')
- `reportGrowingStock` — 2x (indicator = 'relative' / 'absolute')
- `reportFit` — 2x (level = 'grid' / 'cell')
- `reportAgEmployment` — 2x (type = 'absolute' / 'share')

Note: `agent/helpers/magpie4_reference.md` states "106 unique report* functions." The direct grep of the pinned source yields 101. The same helper's pitfalls section flags a prior plan-vs-actual discrepancy ("Plan said 108... actual count is 106") — a similar overcount applies here. The authoritative number is **101 unique function names from the pinned source**.

---

## Post-dispatch assembly (lines 184-235)

After `tryList` returns:
1. NULL results filtered out (`Filter(Negate(is.null), ...)`)
2. Region sets unified across all outputs (union of all region items; missing regions filled with `add_columns`)
3. `mbind` to a single magclass object; incomplete timesteps NA-filled via `.filtermagpie(..., filter = filter)`
4. Third dimension relabeled to `"variable"`
5. `scenario` and `"MAgPIE"` model dimensions added if requested
6. Unit-format validation (warns on missing `(unit)` suffix)
7. Written to file via `write.report2` if `file != NULL`; otherwise returned as magclass object

---

## Entry point in MAgPIE proper

`magpie4::getReport` is called by `scripts/output/rds_report.R:37` (in the parent MAgPIE repo), which produces `report.mif` / `report.rds` during postprocessing.

---

## Citation

`.cache/sources/magpie4/R/getReport.R:56-235` (v2.70.0 @ a360d8c9ec, resolution = "sha")  
Doc: `agent/helpers/magpie4_reference.md` §"Central entry point: getReport"
