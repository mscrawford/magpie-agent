# Round 39 Adversarial Verification — Infeasibility_Debugging_Guide.md

**Verifier**: Opus 4.8 (1M), adversarial.
**Target doc**: `reference/Infeasibility_Debugging_Guide.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ `5ea394f`; official GAMS docs (gams.com/latest/docs/UG_GAMSOutput.html).
**Method**: mechanical citation check (test -f / wc -l / read exact line) for every file_evidence + every modules/.../file.gms:LINE in proposed_fix, then adversarial adjudication of realization-structure / producer / consumer claims with isolated grep + positive control.

Summary: 9 bugs reviewed. **6 UPHELD, 3 CORRECTED, 0 REFUTED, 0 CITATION_FAILED.** All 9 bugs are REAL doc errors and all 9 proposed fixes are SAFE (the fixes' own file:line citations all resolve to the claimed content). Three corrections are to the auditor's *supporting evidence* (line numbers / characterizations), not to the fix payload.

---

## INFEAS-B1 — modelstat 7 mislabeled "Intermediate infeasible" — UPHELD (Major)

**Class**: other (GAMS-language semantics + internal contradiction).

Mechanical citation check:
- `solve.gms` exists, 109 lines. Auditor cites :102 as the abort guard.
- Line 102 = `if ((p80_modelstat(t) > 2 and p80_modelstat(t) ne 7),` — contains `p80_modelstat`, `> 2`, `ne 7`. MATCHES claim. citation_ok=true.
- (Doc itself cites :103-106 for the abort body; lines 103-106 = gmszip / mv / Execute_Unload / abort. Consistent.)

Ground-truth GAMS semantics (WebFetch gams.com/latest/docs/UG_GAMSOutput.html):
- Code 6 = **INTERMEDIATE INFEASIBLE** ("current solution is not feasible, but the solver stopped...").
- Code 7 = **FEASIBLE SOLUTION** ("a feasible solution to a problem without discrete variables has been found").

Doc line 39 labels code 7 "Intermediate infeasible" — that label belongs to code **6**. Doc line 54 repeats. The doc's own line 637 says "Modelstat 7 (feasible but not optimal) tolerated" — direct self-contradiction. 7 is tolerated *because* it is feasible.

Verdict **UPHELD**. Proposed fix (relabel row to "Feasible (not proven optimal)"; amend line 54) is correct.

---

## INFEAS-B2 — config/default.cfg:1613 → :1648 (PkBudg650 "not feasible for SSP3"), cited 3x — UPHELD (Major)

**Class**: other (citation drift).

Mechanical citation check:
- `config/default.cfg` exists, 2423 lines.
- Doc claim site :1613 = `# * Switch for scaling GHG price with development state (1=on 0=off)` — devstate-scaling comment, NOT the SSP3-feasibility note. Doc's "config/default.cfg:1613" is wrong content.
- Proposed fix site :1648 = `# *   PkBudg650:  Peak Budget with 650 GtCO2 ... (not feasible for SSP3)` — contains "not feasible for SSP3". citation_ok=true.
- (Auditor also notes :1998 = same string; confirmed identical text at 1998.)

Off by 35. Claim is real; only the line number was wrong, repeated at doc lines 328, 374, 530. Verdict **UPHELD**. Replace all three `:1613` with `:1648`.

---

## INFEAS-B3 — config/default.cfg:1414 → :1440-1443 (BII threshold) + paraphrase fix — UPHELD (Major)

**Class**: other (citation drift + threshold paraphrase).

Mechanical citation check:
- :1414 = `# * (bv_btc_mar21): Global optimization of range-rarity weighted biodiversity stocks ...` — realization-description comment, not BII-threshold guidance. Doc's "config/default.cfg:1414" is wrong content.
- Proposed fix cites :1440-1443. Read:
  - 1440 = `# *   < 0.7:  continued decrease of global BII`
  - 1441 = `# *   0.74: no further decrease of global BII`
  - 1442 = `# *   0.76: moderate increase of global BII`
  - 1443 = `# *   >= 0.78: (very) strong increase of global BII accomplished by high conversion of pasture to non-forest natural land`
  - citation_ok=true (1443 contains ">= 0.78", "high conversion of pasture").

Doc's prose error: it says values ~0.7 cause "very strong land-use changes". Per code, < 0.7 => *continued decrease* (mild); it is >= 0.78 that drives strong pasture→natveg conversion. The doc's own Tier-1 dangerous-value `>= 0.78` (line 311 right column) is itself correct; only the "~0.7" prose is wrong. Verdict **UPHELD**. Proposed fix (rewrite to ">= 0.78 ... high conversion of pasture to non-forest natural land; < 0.7 still permits continued BII decrease", cite :1443) is correct.

---

## INFEAS-B4 — "Default: 50% water reserved for manufacturing (s42_reserved_fraction=0.5)" is a NON-DEFAULT-realization mechanism — UPHELD (Major)

**Class**: realization_structure (which realization defines/uses the mechanism).

Mechanical citation check:
- Default water_demand realization = `all_sectors_aug13` (config/default.cfg:1317: `cfg$gms$water_demand<- "all_sectors_aug13"`). citation_ok=true.
- agr_sector_aug13/input.gms exists (118 ln); :9 = `s42_reserved_fraction ... / 0.5 /`. MATCHES.
- agr_sector_aug13/presolve.gms exists (77 ln); :37 = comment `* (assign s42_reserved_fraction to manufacturing...)`, :38 = `vm_watdem.fx("manufacturing",j) = sum(wat_src, im_wat_avail(t,wat_src,j)) * s42_reserved_fraction;`. MATCHES (the hack is at :38; auditor's 37-38 spans the comment+code).
- all_sectors_aug13/realization.gms exists (74 ln); :45 = `*'   activities (in addition to \`s42_reserved_fraction\`).` — a doc-COMMENT (`*'` prefix), not code.

Adversarial usage re-derivation (isolated grep, both methods, + positive control):
- `rg s42_reserved_fraction modules/42_water_demand/all_sectors_aug13/` → ONLY realization.gms:45 (comment). `grep -rn` → identical single comment hit. The scalar is never declared or used in default-realization code.
- POSITIVE CONTROL: `rg s42_env_flow_fraction all_sectors_aug13/` → input.gms:38 = `s42_env_flow_fraction ... / 0.2 /` (declared with a value) + 4 comment refs. Search works in that dir; absence of a *code* use of s42_reserved_fraction is genuine.
- agr_sector_aug13 genuinely USES it: input.gms:9 (decl 0.5), presolve.gms:38 (.fx hack), presolve.gms:44.

So the flat 50%-manufacturing reserve is an agr_sector_aug13-only mechanism, presented in the doc (line 175, Rank-2 q43_water "Why critical") as the DEFAULT. Verdict **UPHELD**. Proposed fix (default reads per-sector input data; the 50% rule is non-default agr_sector_aug13, cite input.gms:9 + presolve.gms:37-38) is correct.

---

## INFEAS-B5 — q32_establishment_hvarea citation 204-208 → 213-217 (points at wrong equation) — UPHELD (Major)

**Class**: realization_structure (which equation sits at which line).

Mechanical citation check:
- forestry/dynamic_may24/equations.gms exists, 260 lines.
- Doc cites :204-208. Read: 205 = `q32_establishment_demand(i2)$s32_establishment_dynamic ..` → `v32_prod_forestry_future(i2) =g= ...demand_future...`. This is a DIFFERENT equation (future production >= future demand).
- Proposed fix :213-217. Read: 213 = `q32_establishment_hvarea(j2)$s32_establishment_dynamic ..` → `sum(ac_est, v32_land(j2,"plant",ac_est)) =g= sum(ac_sub, v32_hvarea_forestry(j2,ac_sub)) * ...`. This IS replanting (plant establishment) >= harvest area. citation_ok=true.
- Declaration cross-check: declarations.gms:102 = `q32_establishment_hvarea(j) ... Establishment in current time step for future demand`; :101 = `q32_establishment_demand(i)`. Confirms the two are distinct equations and the doc's "Replanting >= Harvest" gloss matches :213, not :205.

Verdict **UPHELD**. Change `equations.gms:204-208` → `:213-217`.

---

## INFEAS-B6 — q35_min_forest citation 75-77 → 78-80 — UPHELD (Minor)

**Class**: realization_structure (equation location).

Mechanical citation check:
- natveg/pot_forest_may24/equations.gms exists, 233 lines.
- Doc cites :75-77. Read: 75-76 = NPI/NDC descriptive comment ("...specifically formulated for forest and / other land stocks."), 77 = blank. NOT the equation.
- Proposed fix :78-80. Read: 78 = `q35_min_forest(j2) .. sum(land_forest, vm_land(j2,land_forest))`, 79 = `=g=`, 80 = `sum(ct, p35_min_forest(ct,j2));`. grep confirms `q35_min_forest` appears only at line 78. citation_ok=true.
- Context: lines 73-76 are the NPI/NDC comment block (auditor said 73-77; 77 is blank — immaterial). The doc's cited 75-77 lands inside the comment, off by ~3 from the equation.

Verdict **UPHELD**. Change `equations.gms:75-77` → `:78-80`.

---

## INFEAS-B7 — 2nd-gen bioenergy floor citation 62 → 64 — CORRECTED (Minor)

**Class**: realization_structure (which mechanism at which line).

Mechanical citation check:
- bioenergy/1st2ndgen_priced_feb24/presolve.gms exists, 64 lines.
- Doc claim site :62 = BLANK (`awk NR==62` → empty). So the doc citation does not point at the claimed floor (it points at nothing).
- Proposed fix :64 = `i60_bioenergy_dem(t,i)$(i60_bioenergy_dem(t,i) < s60_2ndgen_bioenergy_dem_min) = s60_2ndgen_bioenergy_dem_min;` — the 2nd-gen demand floor. citation_ok=true.
- Magnitude check: input.gms:41 = `s60_2ndgen_bioenergy_dem_min ... (mio. GJ per yr) / 1 /`. Doc's "1 mio GJ/yr" is correct.

CORRECTION to auditor's reasoning (not to the fix): the auditor's reality_in_code says "Line 62 is the first-gen subsidy floor". Line 62 is actually BLANK; the 1st-gen subsidy floor is at presolve.gms:60-61 (`i60_1stgen_bioenergy_subsidy(t)$(... < s60_bioenergy_1st_subsidy) = s60_bioenergy_1st_subsidy;`). The core claim (doc :62 is wrong, correct line is :64) holds and the fix is safe.

Verdict **CORRECTED**. Corrected set: doc citation `presolve.gms:62` (blank) → `:64`; note the adjacent 1st-gen subsidy floor is at :60-61, not :62.

---

## INFEAS-B8 — v71_additional_mon(j) → v71_additional_mon(j,kli_mon) (dimension truncation) — UPHELD (Minor)

**Class**: producer_declaration (variable declaration dimensions).

Mechanical citation check:
- disagg_lvst/foragebased_jul23/equations.gms exists, 72 lines.
- Proposed fix cites :58 and :68. Read: 58 = `+ v71_additional_mon(j2,kli_mon)`; 68 = `sum((cell(i2,j2),kli_mon), v71_additional_mon(j2,kli_mon)) * s71_punish_additional_mon`. Both 2-dimensional. citation_ok=true.
- DECLARED check (declarations.gms): :10 = `v71_additional_mon(j, kli_mon)   Additional punished production of monogastric livestock`. Two-dimensional (cluster x monogastric livestock type). The `ov` reported form :40 = `ov71_additional_mon(t,j,kli_mon,type)`.

Doc occurrences (grep on the doc): line 270 (Section 4 table) = `v71_additional_mon(j)` — truncated to 1 dim. Line 437 = `ov71_additional_mon` (the gdx/output prefix used in a readGDX call — correct as-is, the `ov`+`(t,...)` form does not need the fix). The proposed fix targets only Section 4 line 270, which is the right and only place needing the dimension correction.

Verdict **UPHELD**. Change Section-4-table `v71_additional_mon(j)` → `v71_additional_mon(j,kli_mon)`.

---

## INFEAS-B9 — non-default aborts (13_tc/exo, 38_factor_costs/per_ton_fao_may22) lack default caveat — CORRECTED (Minor)

**Class**: realization_structure (which realization is default).

Mechanical citation check:
- 13_tc/exo/presolve.gms exists, 78 lines; :43 = `abort "tau value of 0 detected in at least one region!";`. MATCHES doc.
- 38_factor_costs/per_ton_fao_may22/presolve.gms exists, 22 lines; :9 = `abort "This factor cost realization cannot handle labor productivities != 1"`. MATCHES doc.
- factor_costs default: config/default.cfg:1233 = `cfg$gms$factor_costs <- "sticky_feb18"` (auditor correct; `grep gms$factor_costs` returns only this assignment).
- tc default: auditor file_evidence says **config/default.cfg:2293 (tc=endo_jan22)**. MECHANICAL FAILURE on that line: :2293 = `cfg$gms$s80_optfile <- 1 # def = 1` — does NOT contain `tc` or `endo_jan22`. The real assignment is at **line 293**: `cfg$gms$tc <- "endo_jan22"   # def = endo_jan22` (verified by both rg and grep, single hit). Digit transposition 293→2293 in the auditor's evidence.

Adjudication: the substantive CLAIM (13_tc default is endo_jan22 not exo; 38_factor_costs default is sticky_feb18 not per_ton_fao_may22; a default run reaches neither abort) is TRUE and verified. The proposed_fix payload is pure prose ("(non-default; default is endo_jan22)" / "(non-default; default is sticky_feb18)") with NO module file:line citation, so the fix itself is safe and correct. Only the auditor's supporting tc-default line number is wrong.

Verdict **CORRECTED**. Corrected set: the bug + the prose fix stand; the tc-default citation is `config/default.cfg:293`, not `:2293`. (sticky_feb18 @ :1233 and both abort citations are correct as written.)

---

## Cross-cutting notes
- No phantom-consumer or cross-realization-confabulation pattern (the R33 failure class) appeared: every realization-structure claim was checked against the cited realization's OWN files, and no equation/variable was attributed to a sibling realization.
- The doc's footer ("All file:line references verified against codebase") is over-claimed given B2/B3/B5/B6/B7 citation drift, but that is cosmetic.
- Two auditor file_evidence line numbers are themselves off (B7: line 62 is blank not 1st-gen-floor; B9: tc default is :293 not :2293). Neither affects fix safety because both fixes' *payload* citations are correct. Flagged as CORRECTED so the fixer applies the right supporting line.
