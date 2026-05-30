# Round 35 Doc Audit — module_60.md (Bioenergy)

**Auditor**: Opus (adversarial doc auditor)
**Date**: 2026-05-30
**Target**: `magpie-agent/modules/module_60.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Realization audited**: `1st2ndgen_priced_feb24` (default — confirmed)

---

## Verdict: MOSTLY ACCURATE (high quality)

This is a strong doc. The equation formulas, equation names, variable names, set definitions, consumer/producer sets, defaults, and the bulk of file:line citations all verify against current develop code. Found **2 confirmed bugs** (1 Major, 1 Minor) plus **1 Minor internal count inconsistency**. The pre-run CHECKER LEAD (vm_dem_bioen unit "GJ" at line 557) is **REFUTED** — the doc is correct there.

---

## CHECKER LEAD verification (REFUTED)

> Lead: "vm_dem_bioen at module_60.md:557 claims unit 'GJ' but canonical is 'mio. tDM per yr'."

**Refuted.** module_60.md:553-557 reads:
```
**1. Gross Energy Content** (from data):
fm_attributes("ge",kall)  // GJ per tDM
- Converts mass-based demand (vm_dem_bioen, tDM) to energy-based demand (GJ)
```
Line 557 describes `vm_dem_bioen` as **tDM** (correct). The "GJ per tDM" on line 555 is the unit of `fm_attributes("ge",...)`, not of `vm_dem_bioen`. The doc consistently and correctly states `vm_dem_bioen` is `mio. tDM per yr` (lines 50, 538). Canonical declaration: `declarations.gms:20` = `vm_dem_bioen(i,kall) Regional bioenergy demand (mio. tDM per yr)`. No bug.

**verify_cmd**: `Read declarations.gms:20` → `vm_dem_bioen(i,kall) ... (mio. tDM per yr)`; doc lines 50/538/557 all consistent with tDM.

---

## Consumer/producer set verification (MANDATE 13 + 17) — both CORRECT

**`vm_dem_bioen`** — doc claims sole external consumer is Module 16 (Demand). Confirmed.
- `rg -ln 'vm_dem_bioen' modules/ --glob '*.gms'` → outside module 60, only `16_demand/sector_may15/equations.gms`.
- Positive control: same grep returns module-60's own files (declarations/equations/presolve/postsolve) → grep works.
- Module 16 default realization = `sector_may15` (config:608) → cited file path correct.
- `.` (attribute) form: no `vm_dem_bioen.` reads outside module 60 (presolve `.fx` are module-60-internal). No hidden solution-level consumer.

**`vm_bioenergy_utility`** — doc claims sole external consumer is Module 11 (Costs). Confirmed.
- `rg -ln 'vm_bioenergy_utility' modules/ --glob '*.gms'` → outside module 60, only `11_costs/default/equations.gms`.
- `.` form (`scaling.gms`) is module-60-internal.

**Upstream inputs** — `im_pop_iso` declared `09_drivers/aug17/declarations.gms:10` (doc's Module 09 attribution correct). `fm_attributes` loaded `16_demand/sector_may15/input.gms:20-22` (module.gms:12-13 says 16_demand provides gross energy content; doc calling it "from data" is acceptable since it is an `fm_` data parameter).

---

## Count verifications

- **scen2nd60 = 88 scenarios**: CORRECT at doc line 279. Family breakdown verified exactly: PIK 7, R21M42 20, R2M41 5, R32M46 15, R34BC 4, R34M410 15, SSPDB 22 (sum 88). Matches doc lines 282-288. (Verified by Python parse of sets.gms:16-103.)
- **scen_countries60 = 249 countries**: CORRECT at doc lines 372/822/1042. Regex extraction between the set's slashes → 249 codes, 249 unique, 0 duplicates. Matches core `iso` set (249). (My first naive line-slice gave 240 — a slicing artifact that excluded line 33; cross-checked with regex + core iso set to confirm 249.)
- **"90+" scenario count** (lines 592, 780, 1033, 1040): see BUG-3 below — inconsistent with the precise 88 the same doc establishes.

## Default / scalar verifications (MANDATE 3) — all CORRECT

| Claim | Doc | Code | Verdict |
|---|---|---|---|
| Default realization `1st2ndgen_priced_feb24` | 4,12 | `config:1982` | ✓ |
| `c60_biodem_level` default 1 (regional) | 86,576 | `input.gms:37` scalar `/ 1 /` | ✓ |
| `s60_bioenergy_1st_subsidy = 6.5` | 192,471,478,640 | `input.gms:38` `/ 6.5 /`; `config:2101` | ✓ |
| `s60_bioenergy_1st_price = 0` | 479,641 | `input.gms:39` `/ 0 /`; `config:2109` | ✓ |
| `s60_bioenergy_2nd_price = 0` | 482,644 | `input.gms:40` `/ 0 /`; `config:2110` | ✓ |
| `s60_2ndgen_bioenergy_dem_min = 1` | 524,647 | `input.gms:41` `/ 1 /`; `config:2091` | ✓ |
| `c60_price_implementation = "lin"` default | 405,627 | `input.gms:44` `$setglobal ... lin` | ✓ |
| `c60_2ndgen_biodem = "R34M410-SSP2-NPi2025"` | 301,588 | `input.gms:45` | ✓ |
| `c60_res_2ndgenBE_dem = "ssp2"` | 325,605 | `input.gms:69` | ✓ |
| `c60_1stgen_biodem = "const2020"` | 316,616 | `input.gms:79` | ✓ |
| `sm_fix_SSP2` (typically 2020-2025) | 417,484,741 | `config:225` = 2025 | ✓ (default 2025; illustrative 2020 examples are explicitly labelled hypothetical) |

## Equation / formula / citation verifications — all CORRECT

- `q60_bioenergy` formula (doc 39-43, cite `equations.gms:16-21`) → matches lines 16-21 exactly.
- `q60_bioenergy_glo` (doc cite 43-44) / `q60_bioenergy_reg` (doc cite 46-47) / `q60_res_2ndgenBE` (doc cite 61-64) / `q60_bioenergy_incentive` (doc cite 73-75) → all match exactly, including the dimension `(i2)` on reg/res/incentive and the bare `q60_bioenergy_glo` (no index).
- Equation set in `declarations.gms:29-35`: exactly 5 (`q60_bioenergy`, `q60_bioenergy_glo`, `q60_bioenergy_reg`, `q60_res_2ndgenBE`, `q60_bioenergy_incentive`). Doc "5 equations" correct.
- Sets `kbe60` (`sets.gms:111-112` = betr,begr), `k1st60` (`114-115` = oils,ethanol), `scen1st60` (`117-118`), `scen2ndres60` (`120-121`) — all cited lines exact.
- Subsidy params `i60_1stgen_bioenergy_subsidy` (`declarations.gms:13`), `i60_2ndgen_bioenergy_subsidy` (`declarations.gms:14`) — exact. (Code line 14 has an in-code typo "GHJ"; doc correctly writes "USD17MER per GJ" — not a doc bug.)
- Comment-line citations `equations.gms:23-28, 33-41, 49-53, 57-58, 58-59, 66-71, 68-69, 70-71` — all verified within range.
- input.gms data-table citations (`63-67`, `72-76`, `82-86`) and presolve subsidy-mode citations (exp `37-41`, const `44-48`, lin `51-55`, floor `60-61`, min-floor `64`) — all verified.
- `presolve.gms:23` (2nd gen subsidy = 0 in SSP2-fix branch) — correct.

---

## Bugs Found

### BUG module_60:836 — wrong scale value + citation drift to different content (MAJOR)

- **Class**: 13/12 (wrong numerical value presented as code's implementation + content-level citation mismatch)
- **Severity**: Major — "Right concept, wrong number" + "Citation points at content … materially different". Not Critical (a scale factor is solver conditioning, not a model-behavior default; a wrong value harms numerics but not a silent result flip).
- **Doc (lines 834-838)**:
  ```
  **Bioenergy Utility** (`scaling.gms:8`):
  vm_bioenergy_utility.scale(i) = 10e4
  Scale factor of 10^5 improves solver numerics ...
  ```
- **Reality**: `scaling.gms:9` → `vm_bioenergy_utility.scale(i) = 1e2;` (= 100 = 10^2). The cited **line 8** holds a *different* variable: `v60_2ndgen_bioenergy_dem_residues.scale(i,kall) = 1e3;`. The doc value `10e4` (=100,000=10^5) is wrong by 1000×; the "10^5" text is wrong (actual 10^2); the line number is off by one and points at a different variable; and scaling.gms actually scales **5** variables (lines 8-12: residues 1e3, utility 1e2, q60_bioenergy_glo 1e4, q60_bioenergy_reg 1e2, q60_res_2ndgenBE 1e3), not just one.
- **File evidence**: `modules/60_bioenergy/1st2ndgen_priced_feb24/scaling.gms:9`
- **verify_cmd**: `awk '{printf "%d: %s\n",NR,$0}' scaling.gms` → `8: v60_2ndgen_bioenergy_dem_residues.scale(i,kall) = 1e3;` / `9: vm_bioenergy_utility.scale(i) = 1e2;`
- **confirmed**: true
- **proposed_fix**: Replace the doc block (lines 834-838) with:
  ```
  **Variable & Equation Scaling** (`scaling.gms:8-12`):
  - v60_2ndgen_bioenergy_dem_residues.scale(i,kall) = 1e3
  - vm_bioenergy_utility.scale(i) = 1e2
  - q60_bioenergy_glo.scale = 1e4
  - q60_bioenergy_reg.scale(i) = 1e2
  - q60_res_2ndgenBE.scale(i) = 1e3
  Scale factors improve solver numerics (bioenergy demands/utility can be large in absolute terms).
  ```
  At minimum, change `scaling.gms:8` → `scaling.gms:9` and `= 10e4` / "10^5" → `= 1e2` / "10^2".

### BUG module_60:494 — presolve fix-block mislabeled + incomplete (MINOR)

- **Class**: 3/12 (suffix/list truncation + content mismatch)
- **Severity**: Minor (tie-break down) — incomplete and mislabeled, but the conceptual point ("non-bioenergy product types fixed to zero bioen demand") is right; would not drive a wrong code action.
- **Doc (lines 492-498, echoed at 885)**:
  ```
  ### Variable Fixing (`presolve.gms:8-14`)
  **Non-bioenergy products** (food, feed, material):
  vm_dem_bioen.fx(i,kap) = 0
  All livestock products (kap) have zero bioenergy demand (fixed).
  ```
  Line 885: "Fix non-bioenergy products to zero demand (`presolve.gms:8-10`)".
- **Reality**: `presolve.gms:8-10` fixes THREE product groups, not one:
  ```
  vm_dem_bioen.fx(i,"pasture") = 0;   (line 8)
  vm_dem_bioen.fx(i,kap) = 0;          (line 9)  -- kap = livestock products
  vm_dem_bioen.fx(i,kforestry) = 0;    (line 10) -- forestry products
  ```
  The parenthetical "(food, feed, material)" is wrong: none of pasture / livestock(`kap`) / forestry(`kforestry`) are "food, feed, material" in the MAgPIE product taxonomy. The doc shows only the `kap` line and omits the explicit `"pasture"` and `kforestry` fixes.
- **File evidence**: `modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:8-10`
- **verify_cmd**: `awk 'NR>=8&&NR<=10' presolve.gms` → lines 8/9/10 as above.
- **confirmed**: true
- **proposed_fix**: Replace lines 494-498 with:
  ```
  **Non-bioenergy products** (pasture, livestock, forestry) are fixed to zero bioenergy demand:
  vm_dem_bioen.fx(i,"pasture") = 0
  vm_dem_bioen.fx(i,kap)       = 0   // livestock products
  vm_dem_bioen.fx(i,kforestry) = 0   // forestry products
  ```
  And on line 885 keep `presolve.gms:8-10` but reword to "Fix pasture, livestock (kap), and forestry (kforestry) demand to zero".

### BUG module_60:592 — "90+" scenario count inconsistent with verified 88 (MINOR)

- **Class**: 6 (hardcoded counts drift)
- **Severity**: Minor — the doc elsewhere (line 279) states the precise, correct count 88; "90+" is loose and ~2 high, but a careful reader has the exact figure and won't be misled into action.
- **Doc**: "90+ scenarios" at lines 592, 780, 1033, 1040 (and "90+" at 780). Contradicts the doc's own verified "**88 scenarios**" at line 279.
- **Reality**: `scen2nd60` has exactly **88** members (sets.gms:16-103). 88 is not "90+".
- **File evidence**: `modules/60_bioenergy/1st2ndgen_priced_feb24/sets.gms:16-103` (88 members)
- **verify_cmd**: Python parse of sets.gms:16-103 → `scen2nd60 count = 88`.
- **confirmed**: true
- **proposed_fix**: Replace each "90+" (lines 592, 780, 1033, 1040) with "88" for internal consistency with line 279.

---

## Deferred (not code-verifiable / out of scope — NOT edited)

- module.gms says 16_demand "provides" gross energy content; doc says "from data". Both defensible (`fm_attributes` is an `fm_` data table loaded inside 16_demand). Not flagged as a bug — semantic shading, not a factual error.
- config comment (`config:2116`) describes exp price as "0.25 * target price in the first sm_fix_SSP2 year" whereas code (presolve:39) uses `price/8`. This is a CONFIG-COMMENT vs CODE discrepancy, not a module_60.md doc bug; the doc correctly follows the code (price/8, factor of 8). Out of scope for this doc audit.
- `kres`/`kap`/`kforestry` set membership is defined outside module 60 (not in core/sets.gms by simple grep). Doc correctly says `kres` is "defined elsewhere". Not pursued — not a module-60-owned set claim.
- declarations.gms:14 in-code typo "GHJ" — code defect, not a doc defect.
