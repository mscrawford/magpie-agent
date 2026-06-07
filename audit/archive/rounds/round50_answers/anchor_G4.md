# Anchor G4: magpie4::getReport — dispatch pattern, report* count, file:line

**Source**: `agent/helpers/magpie4_reference.md` (§ "Central entry point: getReport")
**Pin**: v2.70.0 @ a360d8c9ec

---

## Dispatch pattern

`magpie4::getReport(gdx, ...)` is the single entry point invoked by
`scripts/output/rds_report.R:37` (in the MAgPIE repository) to produce
`report.mif` / `report.rds` in IAMC format.

Its internal organisation is a **flat, unconditional `tryList(...)` call**.
There is NO control argument, no `if (any(grepl(...)))` branching, and no
theme-based dispatch. Every `report*` function in the list runs on every
`getReport()` call. The `tryList` wrapper catches per-function failures
individually, so one broken `report*` does not abort the entire report.

Selected additional parameters:

| Parameter | Default | Effect |
|---|---|---|
| `filter` | `c(1, 2, 7)` | Keeps modelstat values "optimal", "locally optimal", "feasible"; NA-fills others |
| `detail` | `TRUE` | `TRUE` = per-crop disaggregation; `FALSE` = aggregated commodity groups |
| `level` | `"regglo"` | `"regglo"` = regional + global; `"iso"` = per-country |

---

## Unique report* function count

The `tryList` dispatch block contains **117 unconditional calls to 106 unique
`report*` functions** (some functions are called more than once with different
arguments; the unique count is 106).

Note: the magpie4_reference.md explicitly flags that an earlier plan document
cited 108 unique functions — "don't cite the plan's number when answering,
count from `getReport.R` if precision matters." The number from the docs
describing the actual pinned source code is **106**.

---

## File and line range (pinned clone)

From `magpie4_reference.md` §"Central entry point: getReport":

```
.cache/sources/magpie4/R/getReport.R
  getReport() function:  L56–L235   (v2.70.0 @ a360d8c9ec)
  tryList dispatch block: L62–L182  (v2.70.0 @ a360d8c9ec)
```

Canonical cite form (per helper rule 3):
`.cache/sources/magpie4/R/getReport.R:56-235` (pin: v2.70.0 @ a360d8c9ec)

---

## Summary

| Property | Value |
|---|---|
| Entry point | `magpie4::getReport` |
| Called by (MAgPIE) | `scripts/output/rds_report.R:37` |
| Dispatch mechanism | Flat, unconditional `tryList(...)` — no branching |
| Total calls in tryList | 117 |
| Unique `report*` functions | 106 |
| Function span (pinned) | `getReport.R` L56–235 |
| Dispatch block span (pinned) | `getReport.R` L62–182 |
| Pin | v2.70.0 @ a360d8c9ec |
| Pinned clone path | `.cache/sources/magpie4/R/getReport.R` |

---

*Written 2026-06-07. Source: `agent/helpers/magpie4_reference.md` (read this session). No raw GAMS code or magpie4 source files were read; all counts and line numbers are cited verbatim from the helper documentation.*
