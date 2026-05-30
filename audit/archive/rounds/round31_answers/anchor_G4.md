# Anchor G4: magpie4::getReport dispatch pattern

**Source**: verified directly against pinned clone  
**Pin**: magpie4 v2.70.0 @ `a360d8c9ec1ee7af6c9287791e8b182bf391d355`  
**Clone path**: `.cache/sources/magpie4/R/getReport.R`  
**Pin file**: `project/version_pins.json` (lock_file_sha256: `de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba`)

---

## Dispatch pattern

`magpie4::getReport` uses a **flat, unconditional `tryList()` dispatch**. There is no `control` parameter, no `if/switch` branching, and no topic-based filtering at the dispatch level. Every call in the list runs unconditionally on every invocation. `tryList` catches per-function failures individually — one broken `report*` function does not abort the rest.

Function signature (`.cache/sources/magpie4/R/getReport.R:56-57`):

```r
getReport <- function(gdx, file = NULL, scenario = NULL, filter = c(1, 2, 7),
                      detail = TRUE, level = "regglo", ...)
```

The `tryList(...)` call spans lines 62-182 of the pinned file. Each string argument is a quoted call expression that `tryList` evaluates, forwarding `gdx` and `level` from the enclosing environment.

Key behavioral switches passed through to the `report*` calls:
- `detail = TRUE/FALSE` — passed to crop-disaggregated functions (e.g., `reportYields`, `reportDemand`, `reportFeed`); controls whether per-crop or aggregated groups are returned.
- `level = "regglo"` (default) — produces both regional and global outputs; `"iso"` produces per-country.
- `filter = c(1, 2, 7)` — post-collection filter that NA-fills any timestep whose modelstat is not in {1=optimal, 2=locally optimal, 7=feasible}.
- Some calls hard-code `level = 'regglo'` regardless of the argument (e.g., `reportPBwater`, `reportPBnitrogen`) — noted in their call strings at lines 142 and 145.

After `tryList` completes, `getReport` (lines 186-235):
1. Removes NULL entries (failed calls).
2. Unions region sets across all outputs and `add_columns` pads missing regions.
3. `mbind`s everything into a single magclass object and applies `.filtermagpie` (modelstat filter).
4. Sets the third-dimension set name to `"variable"`.
5. Optionally prepends `scenario` and `model = "MAgPIE"` dimensions.
6. Validates that all variable names include a `(unit)` suffix; warns on violations.
7. Writes to `file` via `write.report2` or returns the magclass object.

---

## Unique report* function count

**117 total call strings** in the `tryList` block (lines 63-179), resolving to **106 unique `report*` function names**.

The gap (117 - 106 = 11) arises from functions called multiple times with different argument values:
- `reportIncome` x2 (type = 'ppp' and 'mer')
- `reportPriceFoodIndex` x2 (baseyear = 'y2010' and 'y2020')
- `reportYields` x2 (physical = TRUE and FALSE)
- `reportGrowingStock` x2 (indicator = 'relative' and 'absolute')
- `reportAgEmployment` x2 (type = 'absolute' and 'share')
- `reportFactorCostShares` x3 (type = 'requirements', 'optimization', 'accounting')
- `reportWageDevelopment` x3 (baseYear = 2000, 2010, 2020)
- `reportProcessing` x2 (indicator = 'primary_to_process' and 'secondary_from_primary')
- `reportFit` x2 (level = 'grid' and level = 'cell')

Total multi-call functions: 9 functions accounting for 11 extra calls (9 × 2 calls + 2 × 3 calls - 2 base = 11 surplus calls ... check: 2+2+2+2+2+3+3+2+2 = 20 calls from 9 functions = 11 surplus). Confirmed: 117 - 11 = 106.

### Complete list of 106 unique function names

```
reportAAI                        reportAEI
reportAgEmployment               reportAgGDP
reportAgriResearchIntensity      reportAnthropometrics
reportBII                        reportBiochar
reportBioplasticDemand           reportCarbonstock
reportConsumVal                  reportCostCapitalInvestment
reportCostCapitalStocks          reportCostOverall
reportCosts                      reportCostsAccounting
reportCostsFertilizer            reportCostsInputFactors
reportCostsMACCS                 reportCostsPresolve
reportCostsWholesale             reportCostsWithoutIncentives
reportCostTransport              reportCroparea
reportCropDiversity              reportDemand
reportDemandBioenergy            reportEmissions
reportEmissionsBeforeTechnicalMitigation
reportExpenditureFoodIndex       reportExtraResidueEmissions
reportFactorCostShares           reportFeed
reportFeedConversion             reportFireEmissions
reportFit                        reportFoodExpenditure
reportForestYield                reportGrowingStock
reportharvested_area_timber      reportHourlyLaborCosts
reportIncome                     reportIntakeDetailed
reportKcal                       reportLaborCostsEmpl
reportLaborProductivity          reportLandConservation
reportLandTransitionMatrix       reportLandUse
reportLandUseChange              reportLivestockDemStructure
reportLivestockShare             reportManure
reportNetForestChange            reportNitrogenBudgetCropland
reportNitrogenBudgetPasture      reportNitrogenEfficiencies
reportNitrogenPollution          reportOutputPerWorker
reportPBbiosphere                reportPBland
reportPBnitrogen                 reportPBwater
reportPeatland                   reportPlantationEstablishment
reportPopulation                 reportPriceAgriculture
reportPriceBioenergy             reportPriceElasticities
reportPriceFoodIndex             reportPriceGHG
reportPriceLand                  reportPriceShock
reportPriceWater                 reportPriceWoodyBiomass
reportProcessing                 reportProducerPriceIndex
reportProduction                 reportProductionBioenergy
reportProtein                    reportRelativeHourlyLaborCosts
reportRotationLength             reportRuralDemandShares
reportSDG1                       reportSDG12
reportSDG15                      reportSDG2
reportSDG3                       reportSDG6
reportSOM                        reportTau
reportTc                         reportTimber
reportTotalHoursWorked           reportTrade
reportValueMaterialDemand        reportValueTrade
reportVegfruitShare              reportWageDevelopment
reportWaterAvailability          reportWaterIndicators
reportWaterUsage                 reportWorkingAgePopulation
reportYields                     reportYieldsCropCalib
reportYieldsCropRaw
```

Note: `reportharvested_area_timber` uses a snake_case suffix (unusual — all others are camelCase). Do not autocorrect to `reportHarvestedAreaTimber`.

---

## File:line range (pinned clone)

| Element | File | Lines |
|---|---|---|
| Roxygen header / signature | `.cache/sources/magpie4/R/getReport.R` | 1-57 |
| `tryList(...)` dispatch block | `.cache/sources/magpie4/R/getReport.R` | 62-182 |
| Post-collection processing (filter, bind, validate, write) | `.cache/sources/magpie4/R/getReport.R` | 185-235 |
| Full file | `.cache/sources/magpie4/R/getReport.R` | 1-235 |

Pin: magpie4 v2.70.0 @ `a360d8c9ec` (resolution = "sha" — exact RemoteSha match from `input/renv.lock`).

---

## Documentation source

- Primary: `agent/helpers/magpie4_reference.md` (§ "Central entry point: getReport")
- Verified against: `.cache/sources/magpie4/R/getReport.R` (full read this session)
- Version confirmation: `project/version_pins.json`

Status: 🟢 Verified — read from pinned clone this session.
