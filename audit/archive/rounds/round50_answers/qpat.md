# Query Patterns Reference — Worked Example Accuracy Check

**Question**: Pick two worked query patterns from `core_docs/Query_Patterns_Reference.md` that trace a concrete variable or mechanism. Verify every concrete identifier, equation name, realization, and file:line against AI documentation. Are the examples still code-accurate, or has any drifted?

**Source**: AI docs only — `modules/module_29.md`, `modules/module_29_notes.md`, `modules/module_52.md`, `modules/module_59.md`, `cross_module/carbon_balance_conservation.md`.

---

## Example 1 — Pattern 2 "Response Pattern": Tree Cover → SOM → CO2 Emission Chain

Pattern 2 gives a concrete three-step walkthrough. I examine each step's identifiers and citations.

### Step 1 (Module 29 claim)

Pattern 2 states:
> "Variable: `v29_treecover(j,ac)` by age class  
> Equation: `q29_treecover` aggregates to `vm_treecover(j)`  
> Location: `modules/29_cropland/detail_apr24/equations.gms:83-84`"

**Identifier check:**

- `v29_treecover(j,ac)` — confirmed as a declared internal variable in `module_29.md` (Internal Variables table: "Tree cover by age class (j,ac), Mio. ha").
- `q29_treecover` — confirmed; module_29.md Section 10 gives the exact formula:
  ```gams
  q29_treecover(j2)..
    vm_treecover(j2) =e= sum(ac, v29_treecover(j2,ac));
  ```
- `vm_treecover(j)` — confirmed as an interface variable provided by Module 29 (`module_29.md` Interface Variables table: "vm_treecover: Tree cover area (j), Mio. ha, used by Modules 22 and 59").
- Realization `detail_apr24` — confirmed as the default (`module_29.md`: "Default Realization: detail_apr24, confirmed in config/default.cfg").

**Line number `equations.gms:83-84` — CANNOT CONFIRM.**

The module_29.md lists the `q29_treecover` entry (Section 10) with the source note "Source: `equations.gms`" — the exact line number is omitted. Earlier equations do carry explicit line numbers in the doc (e.g., `q29_cropland` at `equations.gms:11-12`, `q29_avl_cropland` at `equations.gms:22-23`, `q29_carbon` at `equations.gms:38-42`, `q29_land_snv` at `equations.gms:49-52`), but `q29_treecover` is one of several later equations where the doc does not record a line number. The total length of `equations.gms` is stated as 124 lines; 83-84 is plausible for the 10th of 16 equations, but this is inference, not verification. The AI docs do not confirm line 83-84 for `q29_treecover`. This is a potential drift point: line numbers shift as code evolves, and this line number was never captured in the module doc.

**Status: identifiers correct, line number unverified by docs.**

---

### Step 2 (Module 59 SOM claim)

Pattern 2 states:
> "Uses: `vm_treecover` in cropland SOM target  
> Formula: `vm_treecover × i59_cratio_treecover × f59_topsoilc_density`  
> Where: `i59_cratio_treecover = 1.0` (100% of natural carbon)"

**Identifier check:**

- `vm_treecover` appears in `q59_som_target_cropland` — confirmed. `module_59.md` Section 3.1 shows:
  ```gams
  q59_som_target_cropland(j2) ..
    v59_som_target(j2,"crop") =e=
      (...
       + vm_treecover(j2) * i59_cratio_treecover)
      * sum(ct,f59_topsoilc_density(ct,j2));
  ```
  and Interface section confirms `vm_fallow(j)` and `vm_treecover(j)` are received from Module 29 (`module_59.md` Section 9.2).
- `i59_cratio_treecover = 1.0` — confirmed. `module_59.md` Section 3.1 key parameters: "`i59_cratio_treecover`: Set to 1.0 (natural soil carbon) (`preloop.gms:82`)."
- `f59_topsoilc_density` — confirmed in the equation.

**Formula accuracy — partial drift in framing.**

The Pattern 2 text writes the formula as `vm_treecover × i59_cratio_treecover × f59_topsoilc_density`, implying three-way multiplication on the treecover term alone. The actual equation in module_59.md shows the multiplication by `f59_topsoilc_density` applies to the *entire parenthesized sum* (all cropland components), not just treecover:
```gams
(...crop terms... + vm_fallow * i59_cratio_fallow
 + vm_treecover * i59_cratio_treecover)
* sum(ct,f59_topsoilc_density(ct,j2))
```
The Pattern 2 shorthand collapses this to a three-way product on treecover alone, which is mathematically correct for the treecover contribution (since it is indeed `vm_treecover * i59_cratio_treecover * f59_topsoilc_density`) but omits the structural context that `f59_topsoilc_density` is a common factor applying to all terms. This is not a factual error — the treecover contribution to the target is exactly `vm_treecover * 1.0 * f59_topsoilc_density` — but it understates the equation's scope.

**Status: identifiers and values correct; formula shorthand accurate for treecover component but omits the shared-factor structure.**

---

### Step 3 (Module 59 → Module 52 handoff)

Pattern 2 states:
> "Module 59 writes the soil-carbon pool of the interface variable: `vm_carbon_stock(j,land,'soilc',stockType)` (modules/59_som/cellpool_jan23/equations.gms:62)  
> Module 52 READS `vm_carbon_stock` in `q52_emis_co2_actual` to compute CO2 emissions (modules/52_carbon/normal_dec17/equations.gms:16-19); it does not aggregate SOM into the stock"

**Identifier check:**

- `vm_carbon_stock(j,land,"soilc",stockType)` written by Module 59 — confirmed. `module_59.md` Section 3.4 gives `q59_carbon_soil` at `equations.gms:61-64`:
  ```gams
  q59_carbon_soil(j2,land,stockType) ..
    vm_carbon_stock(j2, land,"soilc",stockType) =e=
      v59_som_pool(j2, land) +
      vm_land(j2, land) * sum(ct,i59_subsoilc_density(ct,j2));
  ```
  The pattern cites line 62 (within the 61-64 range). ✅ Confirmed.

- `q52_emis_co2_actual` at `modules/52_carbon/normal_dec17/equations.gms:16-19` — confirmed. `module_52.md` Section 3 and "Key Equations Explained" both give the equation at `equations.gms:16-19` with the exact formula verified against source. The Verification Summary also states "q52_emis_co2_actual: Formula matches source code exactly (equations.gms:16-19)." ✅ Confirmed.

- The claim that "Module 52 READS `vm_carbon_stock`" and does not aggregate SOM — confirmed. `module_52.md` Interface Variables section states `vm_carbon_stock` is "Read by Module 52" from Module 56 declarations. The equation computes `pcm_carbon_stock - vm_carbon_stock` (a stock difference) and emits. It does not re-aggregate soil carbon. ✅ Confirmed.

- Realization `cellpool_jan23` for Module 59 — confirmed as default (`module_59.md`: "Default Realization: cellpool_jan23, confirmed in config/default.cfg"). ✅ Confirmed.

- Realization `normal_dec17` for Module 52 — confirmed (`module_52.md`: "Realization: normal_dec17"). ✅ Confirmed.

**Step 3 net effect claim:**
> "Trees restore SOM to 100% of natural levels (vs. typical cropland at 60-80%)."

This is a summary claim, not directly a GAMS identifier. The 100% figure follows from `i59_cratio_treecover = 1.0` (confirmed). The "60-80%" typical cropland range is described as "typical" without citing a specific GAMS parameter — it is a characterization of what IPCC stock change factors yield in practice, and is labeled as a "Net Effect" summary. This is not a code claim, so drift is not applicable here.

**Step 3 status: all identifiers, equation names, realizations, and file:line citations confirmed accurate against AI docs. No drift detected.**

---

### Pattern 2 Summary

| Claim | Status |
|-------|--------|
| `v29_treecover(j,ac)` — internal variable, detail_apr24 | ✅ Confirmed |
| `q29_treecover` aggregates to `vm_treecover(j)` — formula exact | ✅ Confirmed |
| `equations.gms:83-84` for `q29_treecover` | ⚠️ Not confirmed by docs (line absent from module_29.md; plausible but unverifiable here) |
| `vm_treecover` consumed by `q59_som_target_cropland` | ✅ Confirmed |
| `i59_cratio_treecover = 1.0` at `preloop.gms:82` | ✅ Confirmed |
| Formula `vm_treecover × i59_cratio_treecover × f59_topsoilc_density` | ✅ Correct for treecover component; `f59_topsoilc_density` is a shared factor for all cropland terms |
| `vm_carbon_stock(j,land,"soilc",stockType)` written at `equations.gms:61-64` | ✅ Confirmed (pattern cites :62, within confirmed range) |
| `q52_emis_co2_actual` reads it at `equations.gms:16-19` | ✅ Confirmed |
| Realizations `detail_apr24`, `cellpool_jan23`, `normal_dec17` | ✅ All confirmed as defaults |

**Overall Pattern 2 verdict**: The chain is mechanically correct and all non-line identifiers are verified. The single drift risk is `equations.gms:83-84` for `q29_treecover` — the AI docs omit that line number, so it cannot be confirmed as still accurate.

---

## Example 2 — Pattern 4, "Example 3: MECHANISTIC (Module 52 - Carbon Growth)"

Pattern 4 states:
> "Example 3: MECHANISTIC (Module 52 - Carbon Growth)  
> Equations: `C(age) = A × (1-exp(-k×age))^m` (Chapman-Richards)  
> Parameters: Calibrated growth curve parameters (biological)  
> Feedback: Yes (carbon accumulates with stand age)  
> Correct: 'Mechanistically models carbon growth using Chapman-Richards curves'"

**Identifier and formula check:**

The macro used in Module 52 (`core/macros.gms:18`, confirmed in `module_52.md` Section 2.A):
```
m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m
```

Comparing the Pattern 4 formula `C(age) = A × (1-exp(-k×age))^m` against the actual macro:

1. **Start term S is omitted**: The actual formula is `S + (A-S)*(...)^m`, not `A*(...)^m`. When `S=0` (which is the case for both new plantations and new secondary forests in standard use — confirmed in `module_52.md` Section 2.A: "Start: 0 tC/ha (new plantations)" and "Start: 0 tC/ha (new secondary forest)"), the formula reduces to `(A-0)*(1-exp(-k*age))^m = A*(1-exp(-k*age))^m`, which matches. But the macro supports nonzero S, and S is initialized from "pasture litc" for litter carbon (`start.gms:10`). For the vegc pool in standard use, S=0 and the simplified form is correct.

2. **Age argument**: The actual macro uses `ac*5` (age-class integer × 5 years), not a continuous `age`. This is a notational simplification in the Pattern 4 pseudocode — `age = ac*5` — so the formula is accurate given that clarification.

3. **Shape parameter placement**: The exponent `**m` is on the term `(1-exp(-k*(ac*5)))`, consistent with Pattern 4's `(1-exp(-k×age))^m`. ✅ Correct.

**Parameter source:**

Pattern 4 says "Parameters: Calibrated growth curve parameters (biological)." The `module_52.md` states parameters `f52_growth_par(clcl,chap_par,forest_type)` come from `f52_growth_par.csv` sourced from Humpenöder et al. (2014). As of 2026-04-20, Module 52 also performs a bisection calibration of the `k` parameter to FAO FRA 2025 growing-stock targets (preloop.gms:1-118, switch `s52_growingstock_calib = 1` ON by default). The Pattern 4 description "calibrated growth curve parameters (biological)" is still accurate but incomplete: it omits that a growing-stock calibration layer now adjusts `k` to match observed FAO data, with uncalibrated variants preserved for new-establishment use cases. This is a substantive omission — the word "calibrated" is now doubly true (original literature parameters + new FRA-based bisection), but the nature of the calibration has changed.

**Feedback claim:**

Pattern 4 says "Feedback: Yes (carbon accumulates with stand age)." This is confirmed: age classes advance across timesteps (Module 28 tracks age-class distribution), driving carbon accumulation via the Chapman-Richards curve. `module_52.md` Key Insights Section 2 states: "Chapman-Richards equation provides realistic forest carbon accumulation over time. Allows Modules 32 and 35 to optimize rotation lengths." ✅ Confirmed.

**"Mechanistically models" claim — partially accurate with important nuance:**

The Pattern 4 example correctly classifies Module 52 as MECHANISTIC (using Chapman-Richards, a biologically-grounded growth equation with stand-age feedback). However, `module_52.md` Limitations Section 1 clarifies: "Carbon densities from LPJmL are exogenous inputs. MAgPIE does NOT dynamically model carbon accumulation processes. Climate impacts on carbon densities pre-computed by LPJmL, not responsive to MAgPIE land-use decisions." The Chapman-Richards equation is used to compute *age-class-specific carbon density parameters* before optimization; during optimization, these are fixed parameters multiplied by area variables. The "mechanistic" label applies to the parameter-computation step (biological growth curve), not to the optimization equations themselves. Pattern 4 describes this correctly when it says "Equations: `C(age) = ...` (Chapman-Richards)" — the growth equation is used in start.gms, not in equations.gms. The equation.gms for Module 52 has only one equation (`q52_emis_co2_actual`), a stock-difference calculation.

Pattern 4's characterization is accurate in intent but could mislead a reader into thinking the Chapman-Richards curve is an *optimization equation* (it is not; it is a parameter-computation step in start.gms).

**Pattern 4 Example 3 summary:**

| Claim | Status |
|-------|--------|
| Chapman-Richards formula `A*(1-exp(-k*age))^m` | ✅ Correct when S=0 (standard vegc case); omits S parameter present in macro |
| "Parameters: calibrated growth curve parameters" | ✅ Correct but now incomplete — FRA 2025 bisection calibration added 2026-04-20 overwrites `k` by default (`s52_growingstock_calib = 1`) |
| "Feedback: Yes (carbon accumulates with stand age)" | ✅ Confirmed |
| "Mechanistically models carbon growth" | ✅ Accurate for the parameter-computation step (start.gms); potentially misleading if read as describing optimization equations |

---

## Cross-Cutting Assessment

**Pattern 2** is mechanically sound. All variable names (`v29_treecover`, `vm_treecover`, `i59_cratio_treecover`, `vm_carbon_stock`, `vm_emissions_reg`), equation names (`q29_treecover`, `q59_som_target_cropland`, `q59_carbon_soil`, `q52_emis_co2_actual`), realizations (`detail_apr24`, `cellpool_jan23`, `normal_dec17`), and most file:line citations are confirmed accurate against the AI docs. The single unverifiable item is the line number `equations.gms:83-84` for `q29_treecover`; the module doc omits this line number, consistent with the AGENT.md caveat that "line numbers may drift between syncs."

**Pattern 4 Example 3** has one substantive gap introduced by the 2026-04-20 Module 52 update (PR #869): the Chapman-Richards `k` parameter is now calibrated by bisection to FAO FRA 2025 growing-stock targets (ON by default via `s52_growingstock_calib = 1`). Pattern 4 says "Parameters: Calibrated growth curve parameters" — this is still literally true, but "calibrated" now has a different and more specific meaning than when the example was written. The FRA calibration overwrites the LPJmL-based `k` for `pm_carbon_density_secdforest_ac` and `pm_carbon_density_plantation_ac`; uncalibrated versions (`_uncalib`) are preserved for new-establishment use cases. The Pattern 4 example does not mention this calibration layer or the uncalibrated vs. calibrated distinction, which matters for users asking "which `k` does the model use?"

---

## Epistemic Status

🟡 **Documented** — All findings based on AI docs read this session:
- `modules/module_29.md` (last verified 2025-10-13)
- `modules/module_29_notes.md` (updated 2026-04-20)
- `modules/module_52.md` (last verified 2026-05-16)
- `modules/module_59.md` (last verified 2026-03-06)
- `core_docs/Query_Patterns_Reference.md`
- `cross_module/carbon_balance_conservation.md`

Raw GAMS source was not read per task constraints. The unverified line number (`equations.gms:83-84` for `q29_treecover`) could only be confirmed by reading `modules/29_cropland/detail_apr24/equations.gms` directly.
