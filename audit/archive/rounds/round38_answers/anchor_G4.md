# Anchor G4 — magpie4::getReport dispatch pattern

**Source**: `agent/helpers/magpie4_reference.md` (§ "Central entry point: getReport")
**Pin**: v2.70.0 @ a360d8c9ec

---

## Dispatch pattern

`magpie4::getReport(gdx, ...)` organizes its reporting via a **flat, unconditional `tryList(...)` call**. There is no control argument and no `if (any(grepl(...)))` dispatch — every `report*` function in the list runs unconditionally on every invocation.

`tryList` acts as a per-function error barrier: if one `report*` call fails, it is skipped and the rest continue. One broken reporter does not crash the whole report.

After the `tryList` returns, `getReport` unifies regions, filters incomplete timesteps (retaining `modelstat` values 1, 2, 7 — optimal, locally optimal, feasible — and NA-filling others via `filter = c(1, 2, 7)`), validates units, and either returns the combined object or writes it to `file`.

The `detail = TRUE` / `FALSE` argument controls whether individual crops are reported or aggregated into groups (e.g., "soybean" vs. "oilcrops"). The `level = "regglo"` default produces both regional and global aggregates; `level = "iso"` produces per-country.

Downstream entry point in MAgPIE proper: `scripts/output/rds_report.R:37`.

---

## Number of unique report* functions

The `getReport.R` tryList contains **117 total calls** resolving to **106 unique `report*` functions** (some functions are called more than once, e.g., with different arguments).

Verbatim from the helper:

> "Its dispatch is a flat `tryList(...)` of 117 unconditional calls to 106 unique `report*` functions"

Note: an earlier planning document cited 108 unique functions; the helper explicitly corrects this:

> "Plan said 108 unique report* functions — actual count is 106. Minor discrepancy; don't cite the plan's number when answering, count from `getReport.R` if precision matters."

---

## File:line range (pinned clone)

```
.cache/sources/magpie4/R/getReport.R:62-181   (v2.70.0 @ a360d8c9ec)
```

Verbatim citation from the helper's code block header:

```r
# .cache/sources/magpie4/R/getReport.R:62-181 (v2.70.0 @ a360d8c9ec)
```

---

## Thematic structure of the 106 functions

The helper groups them into 11 themes (not a dispatch mechanism — purely for documentation navigation):

1. Demand & Diet
2. Production & Yields
3. Land Use & Cropland
4. Water
5. Nitrogen
6. Emissions & Carbon
7. Costs
8. Prices & Trade
9. Forestry & Timber
10. Labor, Employment & Demographics
11. Sustainability Indicators (SDG, BII, Planetary Boundaries)

---

## Source cited

`agent/helpers/magpie4_reference.md` — §§ "Central entry point: getReport", "Thematic function index", "Common Pitfalls" (pitfall 5).
