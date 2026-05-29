# R28 Q7 / regression G4: How does magpie4::getReport organize its reporting?

**Question**: How does magpie4::getReport organize its reporting? Describe the dispatch pattern, how many unique report* functions it calls, and cite the file:line range from the pinned clone.

---

## Dispatch Pattern

`magpie4::getReport(gdx, ...)` is the central entry point that produces the IAMC-format `report.mif` / `report.rds`. It is invoked by `scripts/output/rds_report.R:37` in MAgPIE proper.

The dispatch mechanism is a **flat, unconditional `tryList(...)` call**. All `report*` functions are passed as character strings to `tryList`, which evaluates them sequentially and catches per-function failures so that one broken `report*` function does not crash the entire reporting run. There is NO `control` argument and NO conditional dispatch (e.g., no `if (any(grepl(...)))` branching) — every listed call runs unconditionally.

The function signature is:

```r
getReport <- function(gdx, file = NULL, scenario = NULL, filter = c(1, 2, 7),
                      detail = TRUE, level = "regglo", ...)
```

Key parameters:
- `filter = c(1, 2, 7)` — keeps only modelstat values "optimal", "locally optimal", and "feasible"; NA-fills all other time-steps.
- `detail = TRUE` — reports per-crop disaggregation; `FALSE` aggregates groups (e.g., "oilcrops" instead of "soybean").
- `level = "regglo"` — produces both regional and global aggregations; `"iso"` produces per-country output.

After the `tryList` block, `getReport` unifies regions, filters incomplete timesteps, validates units, and either returns or writes the output depending on whether `file` is provided.

## Count of Unique report* Functions

`getReport` makes **117 total call lines** to **106 unique `report*` functions** within the `tryList(...)` block. (The difference of 11 arises from functions called more than once with different arguments.)

Note on a known discrepancy: an earlier planning document cited 108 unique functions; the authoritative count from the documentation is **106 unique** report* functions. Do not cite 108.

## File:Line Range (Pinned Clone)

`.cache/sources/magpie4/R/getReport.R:62-181`

Version pin: **magpie4 v2.70.0 @ a360d8c9ec** (resolved via exact SHA from `renv.lock`).

Full pinned path: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/.cache/sources/magpie4/R/getReport.R:62-181`

Pin metadata source: `project/version_pins.json` (captured 2026-05-25; `lock_file_sha256: de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba`).

## Thematic Coverage

The 106 unique `report*` functions span 11 thematic areas as documented in `agent/helpers/magpie4_reference.md`:

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

Notable function name exception: `reportharvested_area_timber` uses a snake_case suffix (unusual — most functions use camelCase). This is not a typo and should not be "corrected" to `reportHarvestedAreaTimber`.

## Important Caution on Version

The workspace clone at `~/Documents/Work/Workspace/magpie4/` is at HEAD (v2.75.1 as of 2026-05-24), which is ahead of the renv-pinned version by 5 minor versions. Line numbers, variable definitions, and function names in the HEAD clone may differ from those in the pinned clone. All citations above apply to **v2.70.0 @ a360d8c9ec** only.

---

**Source (epistemic hierarchy)**: 🟡 Documented — `agent/helpers/magpie4_reference.md` (read this session), with version pin from `project/version_pins.json` (read this session). Raw source file `.cache/sources/magpie4/R/getReport.R` was NOT read per test constraints; line range `62-181` and counts (117 call lines, 106 unique functions) are taken as stated in the helper documentation.
