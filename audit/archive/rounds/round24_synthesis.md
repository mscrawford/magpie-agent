# R24 synthesis

**Date**: 2026-05-24
**Mean score**: 7.5/10 (sharp drop from R23's 9.0 — first 5/10 question since R8/R10 cluster)
**Bugs found**: 18 raw (1 auditor false-positive ⇒ 17 net) — 0 Critical (after auditor correction), 5 Major, 5 Minor, 7 Informational

## Per-question table

| ID | Topic | Score | C | M | Mn | I | Root cause cluster |
|----|-------|-------|---|---|----|---|---|
| Q1 | M53 CH4-rice → M56 pricing | 5/10 | 0 | 1 | 3 | 3 | mostly answerer; 1 cross-doc unit drift |
| Q2 | M60 bioenergy switches | 10/10 | 0 | 0 | 0 | 1 | trivial line drift |
| Q3 | M13 tau cost → vm_cost_glo | 8/10 | 0 | 1 | 1 | 2 | M13 GDP-cap line drift (R3 era) |
| Q4 | M30 croparea infeasibility | 4/10 (corrected from auditor; audit said 4/10 with 1C; the 1C was an auditor error) | 0 | 3 | 1 | 1 | M30 consumer/usage attribution drift; answerer cross-realization confusion |
| G3 | magpie4 version pin | 10/10 | 0 | 0 | 0 | 0 | regression anchor stable |
| G4 | getReport dispatch | 8/10 | 0 | 1 | 0 | 0 | answerer regex confabulation (helper is correct) |

## Auditor false positive (must record)

**Q4-B2 (Critical → withdrawn)**: Opus auditor claimed `s30_implementation` doesn't exist anywhere; flagged as fabricated-variable Critical. **Verification**: `modules/30_croparea/detail_apr24/input.gms:24` declares `s30_implementation              Switch for rule-based (1) or penalty-based (0) implementation of rotation scenarios / 1 /`. Sonnet correctly described switching from `simple_apr24` to `detail_apr24` + `s30_implementation = 0` as a diagnostic step. **No doc fix; audit was wrong.**

This is the first auditor false-positive recorded across R22–R24. Worth noting in the round log because it affects the score and signals an auditor calibration risk on uncommon switches.

## Real doc bugs to fix

### Critical: none (after Q4-B2 correction)

### Major

1. **Q1-B3** — `module_56.md` unit-string drift (4 lines):
   - L152: `im_pollutant_prices(...)  GHG prices (USD17MER/Tg)` → should be `(USD17MER/Mg)` per declarations.gms:9
   - L158: `Prices: USD17MER per Tg` → `per Mg`
   - L627: `f56_pollutant_prices(...)  GHG price scenarios (USD17MER/Tg)` → `(USD17MER/Mg)`
   - L675: `im_pollutant_prices(...)  Configured GHG prices (USD17MER/Tg)` → `(USD17MER/Mg)`
   - **Why this matters**: per Tg vs per Mg is 6 orders of magnitude. A user converting numbers between these units would be off by a million.

2. **Q3-B1** — `module_13.md` GDP-cap citation drift:
   - L196: `presolve.gms:30-42` → actual `presolve.gms:21-33` (block starts at line 21, ends ~33)
   - L274: `### GDP Constraint (presolve.gms:30-42)` → `:21-33`
   - L345: `presolve.gms:21-42` → `:21-33`
   - L256 (also drift): need to verify
   - Lines 30-42 of presolve.gms now contain the cropland-conservation block, not the GDP cap. A reader following the citation would read unrelated code.

3. **Q4-B3** — `module_30.md` L360 wrong consumer attribution for `vm_carbon_stock_croparea`:
   - Current text: "is used by Module 52 (Carbon) for emissions accounting and Module 56 (GHG Policy) for carbon pricing."
   - Reality: M29 (cropland) reads `vm_carbon_stock_croparea` and aggregates it into `vm_carbon_stock(j,"crop",ag_pools)` via `q29_carbon`; M52 and M56 read the aggregated `vm_carbon_stock`, NOT `vm_carbon_stock_croparea` directly.
   - Anchor pattern: same as G2 declarer-vs-aggregator-vs-reader pattern.

4. **Q4-B4** — `module_30.md` `vm_area` consumer list (L22 and L1713):
   - L22 lists: residues (18), factor costs (38), irrigation (41), water demand (42), nitrogen (50), methane (53), soil organic matter (59) — i.e., **38 is wrong** (M38 has 0 references to `vm_area`), and **29 is missing** (M29's `q29_cropland` consumes `vm_area`).
   - L1713: `**Key Output**: vm_area(j,kcr,w) - used by 8+ modules` — fine as fuzzy claim, but the L22 enumeration is the load-bearing one.
   - Correct consumer set (grep-verified): {18, 29, 41, 42, 50, 53, 59}.

### Minor (fix in same session)

5. **Q3-B2** — `module_13.md` L262: `### Initial Values (presolve.gms:74-78)` → off by 1; the `if(ord(t) = 1, …)` block is `presolve.gms:73-77`. Also the actual `pc13_tau ← fm_tau1995` assignment lives in `preloop.gms:18`, not presolve. Two-fold drift.

### Info / answerer-side (no doc fix)

- Q1-B1 (Major in raw count, but root cause is answerer's default-state inversion despite the doc being correct at L499 — Sonnet hedged where it shouldn't have)
- Q1-B2: Sonnet conflated `f56_pollutant_prices.cs3` (prices) with `f56_emis_policy.csv` (on/off mask). Doc distinguishes them at L490–492. No doc fix.
- Q1-B4: Fabricated MACC tech names. Answerer confabulation.
- Q1-B5/B6/B7: Style / framing / verification-date freshness. No fix.
- Q2-B1: presolve.gms line drift but content correct. Auditor rated Info; no fix worth doing.
- Q3-B3/B4: Style / 32-vs-31-additive framing. No fix.
- Q4-B1: Sonnet conflated M30 default (simple_apr24) with M29 default (detail_apr24) and quoted simple_apr24 form of `q29_cropland`. The doc clearly distinguishes both at L79–92. Answerer confabulation amplified by M30 doc's R3 header warning (which trains the reader to focus on simple_apr24 — Sonnet over-applied this to M29).
- Q4-B5/B6: Stale caveat date + missing 🟢 badges. Minor, no fix.
- G4-B1: Sonnet's regex `report[a-zA-Z_]*` excluded digits, missing 6 SDG functions. Helper says 106 (correct); Sonnet claimed 100 (wrong). No doc fix.

## Root-cause clusters

| Cluster | Bugs | Notes |
|---------|------|-------|
| **doc_error: unit-string drift** | 1 (4 occurrences in module_56.md) | Tg vs Mg — single conceptual error duplicated 4x |
| **doc_error: line citation drift (post-R3)** | 1 (3 occurrences in module_13.md) | GDP cap moved from :30-42 to :21-33 |
| **doc_error: consumer/usage attribution** | 2 (M30 L22 + L360) | M38 vs M29 misattribution for vm_area; one-hop error for vm_carbon_stock_croparea |
| **answerer: cross-realization conflation** | 1 (Q4-B1) | M30 default vs M29 default |
| **answerer: confabulation under measurement** | 2 (G4 regex; Q1 MACC techs) | Sonnet's regex/domain knowledge tripped |
| **answerer: default-state hedging** | 1 (Q1-B1) | Hedged where doc was unambiguous |

## Calibration anchors

- **G1 + G2**: not run this round (rotation: G3 + G4 were both unused before R24).
- **G3 (magpie4 version pin)**: 10/10, no drift. First scoring round for this anchor. Established baseline.
- **G4 (getReport dispatch)**: 8/10, no doc drift. Sonnet's regex error (Major answerer-side, not doc) is the only finding. **Establishes baseline at 8 — a clean read should hit 10.** Helper count of 106 is verified correct.

## Comparison to recent trajectory

| Round | Mean | Notes |
|-------|------|-------|
| R22 | 8.67 | First v1.1 schema round; G1+G2 |
| R23 | 9.00 | Migration-touched docs validated; G1+G2 |
| **R24** | **7.50** | First G3+G4 use; bugs surfaced in modules previously untouched (M13 GDP cap, M30 consumer attribution, M56 units) |

R24's drop matches the pre-validation pattern: each new doc category had errors when first validated. The 4 doc-fix candidates (M56 units, M13 lines, M30 consumer list, M30 carbon attribution) are exactly the kind of latent drift the flywheel exists to find.

## Lessons

1. **Auditor false-positive on uncommon scalar** (Q4-B2): The Opus auditor missed that `s30_implementation` exists in `detail_apr24/input.gms:24`. This is the first known auditor confabulation in 24 rounds. **Mitigation**: when an auditor flags a fabricated-variable Critical, the round synthesizer should cross-verify with `grep -r` before accepting. Adding to lessons.
2. **`per Tg` vs `per Mg`** in module_56.md was a 4-line repeat of a single conceptual error — exactly the kind of drift `check_param_defaults.py`-style unit-checking could detect (candidate for future check).
3. **M30 doc has a known R3 header-warning region** about citation drift (line 14 of module_30.md). The vm_area consumer list and vm_carbon_stock_croparea attribution were OUT OF SCOPE of that warning but in the same doc — suggesting the R3 cleanup didn't sweep widely enough.
