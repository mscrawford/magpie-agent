# Pattern D2 omission backlog (R25 follow-up)

**Status (2026-05-25)**: 85 advisory findings remain after R25's validator hardening (down from 154 pre-R25, then 126 after producer-self-exclusion fix). Each is a candidate doc-attribution gap — a real consumer of an interface variable that the producer-side doc doesn't enumerate.

**Run to refresh**:
```bash
python3 scripts/check_consumer_attribution.py --summary-only | grep "Pattern D2" -A 100
```

## Why these aren't fixed yet

Each finding requires reading the producer-side doc context, deciding the right place to add the omitted consumer (with a citation to the consumer-side equation), and editing the doc. Estimated effort: 2-5 min per finding, 85 × ~3 min = ~4 hours of editorial work. Out of scope for the R25 wrap-up session.

## Triage priorities (descending)

Clusters with the most repeated omissions are the highest-leverage to fix (one doc edit closes multiple advisories). From the 2026-05-25 baseline:

| Cluster | Count | Variable | Producer | Omitted consumers (verified real) |
|---|---|---|---|---|
| `modules/module_18.md` `vm_prod_reg` | 10 | vm_prod_reg | M17 (production) | M20 (processing), M38 (factor_costs), M50 (nr_soil_budget), M70 (livestock), M71 (disagg_lvst) |
| `modules/module_52.md` `im_growing_stock` | 4 | im_growing_stock | M14 (yields) | M32 (forestry), M35 (natveg) |
| `modules/module_52.md` `pm_carbon_density_plantation_ac` | 3 | pm_carbon_density_plantation_ac | M52 (carbon) | M14 (yields), M32 (forestry) |
| `modules/module_52.md` `pm_carbon_density_secdforest_ac` | 3 | pm_carbon_density_secdforest_ac | M52 (carbon) | M14 (yields), M35 (natveg) |
| `modules/module_15.md` `vm_dem_food` | 4 | vm_dem_food | M15 (food) | M20 (processing), M62 (material) |
| `modules/module_73.md` `pm_climate_class` | 4 | pm_climate_class | M73 (timber) | M14 (yields), M45 (climate) |

## What's already filtered (false positives suppressed)

The validator now skips:
- **Producer self-references** (e.g., M52 producing pm_X listed as omitting M52)
- **Current-doc module self-references** (a doc about M52 doesn't need to list M52 as a consumer of its own variable)
- **Hyphen-compound trigger words** (`land-use`, `water-use` no longer falsely trigger via `\buses?\b`)
- **Subset hedges** (`primary`, `main`, `most important`, `key consumer`, `principal`, `e.g.`, `such as`, `etc`, `among others`, `including but not limited to`, `may be affected`, `broader`, `wider`, `touched by`, `set of`)
- **Bullet-list aggregation** across adjacent bullets at the same indent

If a future bug shows up that one of these filters should not have suppressed, tighten the filter rather than removing it — the FP rate without these is severe (154 → 85 = 45% noise even after filtering).

## How to do a fix pass when ready

```bash
# 1. List all findings
python3 scripts/check_consumer_attribution.py 2>&1 | grep "Pattern D2" -A 200

# 2. For each (doc, var, omitted) tuple:
#    a. Open the producer-side doc
#    b. Find the line(s) where the variable's consumers are enumerated
#    c. Add the omitted module with a citation:
#       `modules/<NN_xxx>/<realization>/<file>.gms:<line>`
#    d. Re-run check_consumer_attribution.py to confirm the finding is closed

# 3. After fixes, commit with a `fix(R25 follow-up): pattern D2 consumer attribution sweep` message
```
