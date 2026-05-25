# Audit Report: Q1 (M30 Default Rotational Constraints)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8.5/10

---

## Mechanical Checks (binary)

| # | Check | Result | Note |
|---|---|---|---|
| M1 | File:line citations present | PASS | Multiple `simple_apr24/equations.gms:34-36`, `:42-44`, `input.gms:80-85`, `:89-94`, `presolve.gms:23/24` citations |
| M2 | Active realization stated | PASS | "default realization is `simple_apr24`" stated up front and contrasted with `detail_apr24` |
| M3 | Variable prefixes valid | PASS | `vm_area`, `vm_rotation_penalty`, `v30_betr_missing`, `v30_penalty`, `vm_AEI`, `i30_implementation`, `i30_rotation_rules`, `i30_betr_penalty`, `c30_rotation_constraints`, `s30_implementation`, `f30_rotation_max_shr` — all prefix-correct |
| M4 | Epistemic hierarchy badges present | PASS | 🟡 badges on every substantive claim |
| M5 | Confidence tier matches verification depth | PASS | 🟡 (documented) is the right tier given the answer self-attributes only to module_30.md |
| M6 | Closing source statement | PASS | Ends "Based on **module_30.md** documentation (R6 Phase 2 sweep, 2026-05-25 verified), §§3-5, §§9-10, header block, and comparison table" |

All six mechanical checks pass.

---

## Verified Claims (correct)

- **Default realization is `simple_apr24`**: `config/default.cfg:896` sets `cfg$gms$croparea <- "simple_apr24"`. ✓
- **`q30_rotation_max` equation body and location**: matches `simple_apr24/equations.gms:34-36` verbatim (header line 34; `sum`/`=l=`/`f30_rotation_max_shr` body lines 35-36). ✓
- **`q30_rotation_min` equation body and location**: matches `simple_apr24/equations.gms:42-44` verbatim. ✓
- **Mechanism description**: per-`j2`, per-`crpmax30`, per-`w` is exactly the equation signature; the description of summed-over-kcr-in-group ≤ total-cropland × max-share is faithful. ✓
- **Per-`w` constraint structure** (rainfed and irrigated independently): correct — both `q30_rotation_max` and `q30_rotation_min` in `simple_apr24` carry `w` as an explicit free index. ✓
- **Active-subset construction**: `crpmax30(crp30) = yes$(f30_rotation_max_shr(crp30) < 1)` at `simple_apr24/presolve.gms:23`; `crpmin30(crp30) = yes$(f30_rotation_min_shr(crp30) > 0)` at line 24. ✓
- **`crp_kcr30` mapping**: lives at `simple_apr24/sets.gms:18-37`; the answer's "20 rotation types to 19 MAgPIE crops" is structurally accurate (crp30 has 20 elements; the unique kcr targets number 19; note `roots_r` has no mapping entry, an existing-code quirk independent of the answer). ✓
- **`f30_rotation_max_shr` source**: parameter block + `$include` of `input/f30_rotation_max.csv` at `simple_apr24/input.gms:80-85`; mirror block for `_min` at `:89-94`. ✓
- **Off-switch semantics**: `$if "%c30_rotation_constraints%" == "off"` zeroes (`_max_shr=1`, `_min_shr=0`) the bindingness, at `simple_apr24/input.gms:86, 95`. ✓
- **BETR-only role of `vm_rotation_penalty` in simple_apr24**: `q30_cost(i2)` at `simple_apr24/equations.gms:25-27` carries only `v30_betr_missing × i30_betr_penalty`; no rotation-violation pricing in simple. ✓
- **`detail_apr24` hard-constraint equations at L36-38 and L40-42**: matches `detail_apr24/equations.gms:36-38, 40-42`. ✓
- **`detail_apr24` penalty equations** (`q30_rotation_max2`, `q30_rotation_min2`, `q30_rotation_penalty`): all present at `detail_apr24/equations.gms:59-72, 46-53`. ✓
- **`v30_penalty` is declared `positive` over `rota30`**: matches `detail_apr24/declarations.gms:25`. ✓
- **`rota30` group counts**: rotamax30 = 30 elements (cereals1_max through betr_max), rotamin30 = 6 elements (biomass_min, legumes_min, stalk_min, others_min, minor_min, cereals_min) — both verified by counting at `detail_apr24/sets.gms:28-35, 38`. ✓
- **Time-varying fade** between `f30_rotation_rules(rota30,"default")` and the user-selected scenario over 2025-2050: verified at `detail_apr24/preloop.gms:14-16` and scenario start/target scalars (2025/2050) at `detail_apr24/input.gms:22-23`. ✓
- **Water-dim aggregation difference**: `detail_apr24/equations.gms:37-38, 41-42` sum over `w` inside the RHS, while `simple_apr24` keeps `w` as a free index. ✓
- **`q30_rotation_max_irrig` is unconditional** (no `$(i30_implementation = ...)` guard) at `detail_apr24/equations.gms:79-82`; uses `vm_AEI(j2)` (area equipped for irrigation). The answer's "always penalty-based regardless of mode" is correct. ✓
- **`s30_implementation` runtime switch** in detail_apr24: `s30_implementation / 1 /` at `detail_apr24/input.gms:24`; copied into `i30_implementation` at `presolve.gms:19, 22`. ✓

---

## Bugs Found

### Bug Q1-B1
- **Severity**: 🟠 Major
- **Class**: 10 — Stale file:line citation
- **Trigger**: "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different (citation drift to wrong content)."
- **Claim in answer**: "`c30_rotation_constraints` (`input.gms:24`) — compile-time global, options: `\"on\"` / `\"off\"`."
- **Reality in code**: `c30_rotation_constraints` is declared at `simple_apr24/input.gms:14`, not line 24. `simple_apr24/input.gms:24` is `s30_betr_target_noselect`, an unrelated bioenergy-target scalar — a careful reader following the cite would land on the wrong content. The line-24 number is the location of `s30_implementation` in the OTHER realization (`detail_apr24/input.gms:24`).
- **File evidence**: `modules/30_croparea/simple_apr24/input.gms:14` contains `$setglobal c30_rotation_constraints  on`; line 24 contains `s30_betr_target_noselect`.
- **Origin**: doc_error — module_30.md:522 itself says "`c30_rotation_constraints` compile-time switch (`input.gms:24`)". Sonnet trusted the doc verbatim.
- **Phase-2a-sweep failure indicator**: YES — this is a Phase-2a sweep failure. The doc's M30 comparison table has a cross-realization citation drift (`input.gms:24` belongs to detail_apr24's `s30_implementation`, was misplaced into simple_apr24's `c30_rotation_constraints` row). The Phase 2a sweep was supposed to catch exactly this class of cross-realization contamination in M30. Sonnet's answer does NOT surface a `detail_apr24/equations.gms:NN` citation for default behavior — that specific gate condition is met — but it DOES surface a doc-level line-number contamination of the same family that Phase 2a should have caught.
- **Anchor reference**: Resembles R20 anchor (line-number citation drift to materially different content; would mislead a careful reader). Lower tier than the R20 anchor because here the conceptual claim (compile-time on/off switch defaulting to `on`) is entirely correct — only the line number is wrong. The off-switch semantics cited from `input.gms:86, 95` is correct, providing partial corroboration.

### Bug Q1-B2
- **Severity**: 🟢 Informational
- **Class**: 6 — Hardcoded counts drift (minor numbering)
- **Trigger**: "Style or doc issue, not a content error."
- **Claim in answer**: The Summary Table at the bottom is numbered 1-5 in the prose ("differs in four mechanistic respects") but then lists five points (Dual modes, Penalty-based variant, Crop-group sets, Water dimension, Irrigated-specific constraint).
- **Reality**: Five points are listed, not four; the lead-in says "four mechanistic respects".
- **File evidence**: N/A — internal answer inconsistency.
- **Origin**: answerer_confabulation (small editorial slip; no doc claims "four respects").
- **Impact**: a careful reader would notice the off-by-one but not be misled about behavior.

### Bug Q1-B3
- **Severity**: 🟢 Informational
- **Class**: 4 — Conceptual pseudo-code (minor mapping nuance)
- **Trigger**: "Style or doc issue, not a content error."
- **Claim in answer**: For `detail_apr24` the answer says the equations are "indexed by `rotamax30` (30 maximum groups) and `rotamin30` (6 minimum groups)".
- **Reality in code**: The equation declarations in `detail_apr24/declarations.gms:34-38` are indexed over `rotamax30` / `rotamin30`, but the equation bodies (and the `$()` guards) at `detail_apr24/equations.gms:36, 40, 59, 69, 79` actually iterate over the REDUCED dynamic subsets `rotamax_red30` / `rotamin_red30`, populated in `presolve.gms:28-32` based on whether the rules/incentives are binding. The answer's framing is a structural simplification, not wrong, but a reader looking for the exact iteration semantics would miss the `_red30` subset layer.
- **File evidence**: `modules/30_croparea/detail_apr24/equations.gms:36, 40, 59, 69, 79`; `presolve.gms:28-32`.
- **Origin**: answerer_confabulation (the doc compares to `rotamax30`/`rotamin30` and Sonnet did not introduce the `_red30` distinction, but this is editorially fine — equivalent to simple_apr24's `crpmax30`/`crpmin30` reduction). Not load-bearing.

---

## Missing Nuances

1. **Cross-cell scope**: neither answer nor doc clarifies that constraints apply per cluster `j2`, not per cell — could matter if a reader is mentally modeling per-grid-cell semantics. Minor.
2. **BETR penalty is technically rotation-bucket-coded**: `q30_betr_missing` and `q30_cost` in `simple_apr24` use the same `vm_rotation_penalty` cost-channel that detail's penalty-mode pours into. The answer correctly notes simple's `vm_rotation_penalty` carries "only the BETR shortfall penalty"; could have made explicit that simple `vm_rotation_penalty` and detail `vm_rotation_penalty` have very different magnitudes/semantics (simple is BETR-only; detail aggregates BETR + rotation violations) — a downstream Module-11 consumer would see different cost compositions. Minor.
3. **`s30_annual_max_growth` interaction**: the cropland-growth constraint (`v30_crop_area`, `simple_apr24/presolve.gms:50-55`) is a separate brake on cropland expansion that lives in the same module but is not a rotational constraint — appropriately omitted from a rotational-constraint question.

---

## Source-attribution split (doc_error vs answerer_confabulation)

- **doc_error: 1** (Q1-B1 — module_30.md:522 table cites the wrong input.gms line, Sonnet trusted it)
- **answerer_confabulation: 2** (Q1-B2 "four respects" off-by-one; Q1-B3 `rotamax30` vs `rotamax_red30` simplification — both informational)

The Major-severity bug (Q1-B1) is the doc's fault, not Sonnet's. Sonnet followed the rules-of-the-game (use the doc, cite the doc, badge 🟡) and was punished by a doc citation error that was already in place.

---

## Phase-2a-sweep failure indicator

**YES — one indicator triggered.**

The strict gate text said "If the answer surfaces `detail_apr24/equations.gms:NN` for default behavior, the 2a sweep was superficial." Sonnet does NOT surface a detail_apr24 equations.gms line for default behavior; in fact the alternative-realization line numbers (L36-38, L40-42) are correctly contained in the comparison row, not the default-behavior section. So the strict gate is technically satisfied.

However, the spirit of the Phase 2a gate — that cross-realization contamination should not leak into default-behavior claims — is violated by the doc itself: `module_30.md:522` cites `input.gms:24` for `simple_apr24`'s `c30_rotation_constraints`, when line 24 is `detail_apr24`'s `s30_implementation`. That's exactly the cross-realization line-number contamination Phase 2a should have caught. The sweep saw a line number with the right shape (single integer in input.gms) and didn't notice it belonged to the OTHER realization.

**Recommendation**: fix `modules/module_30.md:522` to cite `input.gms:14` (and verify other M30 cross-realization citations during the next sweep pass; check at minimum the §10 advisory and the §3 header block).

---

## Score Computation

```
critical: 0
major:    1 (Q1-B1)
minor:    0
informational: 2 (Q1-B2, Q1-B3)

raw_severity_weighted = 4·0 + 2·1 + 1·0 + 0·2 = 2
score_0_10 = max(0, 10 - 2) = 8

Tie-breaker note: Q1-B1 is borderline Major/Minor. Triggers fired for Major
(citation drift to materially different content). Tie-breaker (§1) says "pick
the lower" — but the line-24 content is materially different (BETR-target
scalar in a different realization, not nearby rotation content). The "wrong
realization" component bumps the impact above the Minor threshold. Final: Major,
no tier_uncertainty flag.

Half-point lift: the alternative-realization mechanistic differences are
unusually clean and accurate — distinguishing penalty-mode equations,
i30_implementation guards, vm_AEI usage, time-varying fader, and irrigated
sub-portfolio — beyond the typical "alternative realization" depth seen in
recent rounds. Adjusting +0.5 (within the rubric's "Mostly Accurate" band).

Final: 8.5/10.
```

---

## Summary

Sonnet's answer is structurally correct, equation citations match the actual `simple_apr24` code verbatim, mechanism descriptions are faithful, and the alternative-realization contrast is one of the cleanest detail_apr24 vs simple_apr24 walks observed in recent rounds. The single Major bug (Q1-B1) is a doc citation drift in `module_30.md:522` (input.gms:24 → should be input.gms:14) — a documentation-side defect the Phase 2a sweep failed to catch. Phase-2a gate (no detail_apr24 equation line cited for default behavior) is technically satisfied, but the spirit of the gate (no cross-realization line-number contamination in default behavior) is violated through the trusted doc.

**Phase 2a sweep verdict**: PARTIAL FAILURE — a cross-realization citation drift remains in module_30.md that the sweep should have caught. Fix is one-line in the doc.

**G1/G2 regression status**: not applicable to Q1.

**Verdict for round-level success gate B.1** ("Q1: 0 HIGH bugs in M30 default behavior"): the gate uses "HIGH" loosely (mapping to Major+); this answer has 1 Major bug attributable to default behavior (the cite drift), so the gate is narrowly **failed** — but the underlying confabulation count is 0 (Sonnet didn't invent anything). The gate is a doc-quality signal, not an answerer-quality signal, in this case.
