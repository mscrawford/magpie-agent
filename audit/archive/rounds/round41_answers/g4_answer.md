# G4 Answer: magpie4::getReport dispatch pattern

**Question**: How does magpie4::getReport organize its reporting? Describe the dispatch
pattern, how many unique report* functions it calls, and cite the file:line range from the
pinned clone.

**Source**: `agent/helpers/magpie4_reference.md` (docs-only answer; pinned source NOT opened directly)
**Pin**: magpie4 v2.70.0 @ SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355` (`resolution: "sha"`)
**Pin file**: `project/version_pins.json` (captured 2026-05-25)

---

## Dispatch pattern

🟡 `magpie4::getReport` organises its reporting through a **flat, unconditional `tryList(...)`
call** that enumerates every `report*` function as a quoted string. There is no `control`
argument, no `if (any(grepl(...)))` branching, and no theme-based dispatch — every call runs
regardless of scenario configuration.

`tryList` provides fault isolation: if an individual `report*` function errors (e.g. because
the run's GDX lacks a particular variable), that function's failure is caught and logged
without aborting the remaining calls. The full report is assembled from whichever calls
succeed.

After the `tryList` block, `getReport` unifies regions, NA-fills timesteps excluded by the
`filter` argument (default `c(1, 2, 7)` — modelstat "optimal", "locally optimal",
"feasible"), and either writes the result to `file` (if provided) or returns it as an object.

The `detail` argument (`TRUE` by default) controls per-crop vs. aggregate-group disaggregation.
The `level` argument (`"regglo"` by default) controls spatial aggregation: `"regglo"` produces
both regional and global aggregates; `"iso"` produces per-country.

---

## Number of unique report* functions

🟡 The helper states the `tryList(...)` contains **117 unconditional calls to 106 unique
`report*` functions** (the 11-call difference arises from functions called more than once,
e.g. with different arguments).

**Pitfall recorded in the helper**: An earlier plan document cited 108 unique functions. The
helper explicitly flags this discrepancy at Common Pitfall 5: "Plan said 108 unique report*
functions — actual count is 106. Don't cite the plan's number when answering." The authoritative
figure from the helper is **106 unique report* functions** across **117 total calls**.

---

## File:line range (pinned clone)

🟡 From `agent/helpers/magpie4_reference.md` §"Central entry point: getReport":

> `.cache/sources/magpie4/R/getReport.R:62-181 (v2.70.0 @ a360d8c9ec)`

The function signature begins at line 62 and the closing brace / return logic ends at line 181.
The `tryList(...)` body spans the interior of that range (lines ~63–178 per the helper's
illustrative excerpt, which shows `"reportPopulation(...)"` as the first call and
`"reportBiochar(...)"` as the last).

**Caveat** (per helper Common Pitfall 3): "Line numbers in this helper's tables (e.g.,
`getReport.R:62-181`) are for v2.70.0. If the pin advances, they will drift. Re-verify on the
version under inspection."

The pin's `resolution` field is `"sha"` (exact SHA checkout), so the clone at
`.cache/sources/magpie4/` is aligned to the exact commit recorded in `renv.lock` — not a tag
fallback or HEAD.

---

## MAgPIE invocation point

🟡 `getReport` is invoked from the MAgPIE model itself at
`scripts/output/rds_report.R:37` (per the helper), which produces `report.mif` / `report.rds`
as post-run outputs.

---

## What the helper does NOT cover

The helper explicitly declines to curate function-level docs for all 106+ functions ("Curation
would be a treadmill"). Instead, it teaches a grep-then-read-on-demand workflow against the
SHA-pinned clone. Consequently:

- The exact argument signatures for most of the 106 functions are not documented in the helper.
- The exact line number of each individual `report*` call within `getReport.R:62-181` is not
  listed.
- The helper does not describe what happens inside `tryList` (its implementation is in the
  magpie4 package source, which was not opened per task instructions).

---

## Closing source statement

This answer is drawn **exclusively** from:

1. `agent/helpers/magpie4_reference.md` — §"Central entry point: getReport", §"Common Pitfalls"
   (pitfall 5 on the 106 vs. 108 discrepancy), §"Version pinning"
2. `project/version_pins.json` — version `2.70.0`, SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355`,
   resolution `"sha"`, captured 2026-05-25

All claims are tagged 🟡 (documented in helper). No magpie4 R source was opened directly.
