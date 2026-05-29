# Audit Report: R30 (CO2 stock-difference accounting — module 52)

**Question**: How does MAgPIE compute CO2 emissions from carbon-stock changes over time (stock-difference accounting)? Which modules' carbon stocks enter, and which equation in module 52 produces the actual CO2 emissions?

**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree). Config: `/tmp/magpie_develop_ro/config/default.cfg`.

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 7/10

Computation: raw = 4·0 (crit) + 2·1 (major) + 1·1 (minor) = 3 → score = max(0, 10 − 3) = 7.

The answer's spine is essentially perfect: the single equation `q52_emis_co2_actual`, its exact text, the stock-difference logic, the sign convention, the populator set (matches G2 anchor), the sets (7 land × 3 pools = 21 emis_oneoff), the macro/citation lines, the FRA-2025 bisection calibration, and "module 52 declares no variables" are ALL verified correct against code. Two attribution errors in the supporting tables drag the score: one Major (subsoil provisioning attributed to M52; it's M59's), one Minor (urban-soilc placeholder placed in the M34 populator row when M59 populates it).

---

## Verified Claims (correct)

1. **Single equation `q52_emis_co2_actual`** — exact text match. `modules/52_carbon/normal_dec17/equations.gms:16-19`. Equation declared at `declarations.gms:30`. It is the ONLY equation in module 52 (decl block has parameters + one equation, no others). ✓
2. **Realization `normal_dec17` is default for module 52** — `config/default.cfg:1556` `cfg$gms$carbon <- "normal_dec17"`; it is also the only non-input realization dir. ✓
3. **`vm_carbon_stock` DECLARED in Module 56** — `modules/56_ghg_policy/price_aug22/declarations.gms:34` (matches G2 anchor: declared in M56, NOT M52). ✓
4. **Populator set 29/31/32/34/35/59** — matches G2 expected set exactly:
   - M29 `detail_apr24/equations.gms:39` (`crop`, ag_pools) + `simple_apr24/equations.gms:30`; folds in M30 `vm_carbon_stock_croparea` (declared `30_croparea/detail_apr24/declarations.gms`). ✓
   - M31 `endo_jun13/equations.gms:23` (`past`, ag_pools). ✓
   - M32 `dynamic_may24/equations.gms:108` (`forestry`, ag_pools), `q32_carbon`. ✓
   - M35 `pot_forest_may24/equations.gms:43,50,54` (`primforest`/`secdforest`/`other`, ag_pools). ✓
   - M34 `exo_nov21/presolve.gms:8` and `static/presolve.gms:10`: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` — populates urban ag_pools by FIXING them to 0 (population via `.fx`, not an equation; the answer correctly notes "vegc/litc fixed to 0"). ✓
   - M59 `cellpool_jan23/equations.gms:62` (`q59_carbon_soil`, soilc, all land); default `cfg$gms$som <- "cellpool_jan23"` (`default.cfg:1916`). ✓
5. **M58 (Peatland) does NOT populate `vm_carbon_stock`** — confirmed (rg exit 1; positive control: `q58_*`/`peatland` abundant in M58). M58 emits via its own `vm_emissions_reg(i2,"ln",poll58)` path (`q58_ln_emis`). ✓
6. **Stock-difference logic & sign** — `(pcm_carbon_stock - vm_carbon_stock)/m_timestep_length`; deforestation (prev > current) → positive emission. Matches code. ✓
7. **`pcm_carbon_stock` carried forward by Module 56** — declared `price_aug22/declarations.gms:19`; assigned `price_aug22/postsolve.gms:8` (`pcm_carbon_stock(...) = vm_carbon_stock.l(...)`). ✓ (Nuance: M56 postsolve carries forward only `ag_pools`; the soilc component of `pcm_carbon_stock` is initialized in M59 preloop — see Missing Nuances. Not a stated error.)
8. **Sets** — `land` = 7 types (`core/sets.gms:251`), `c_pools` = vegc/litc/soilc (`sets.gms:325`), `emis_oneoff` = 21 elements (`sets.gms:314-318`), `emis_land` maps 21 → (land,c_pools) (`sets.gms:332-354`). "21 source combinations (7×3)" correct; labels `crop_vegc … other_soilc` correct. ✓
9. **Macro citations** — `m_timestep_length` at `core/macros.gms:51` ✓; `m_growth_vegc` at `macros.gms:18` (`S + (A-S)*(1-exp(-k*(ac*5)))**m`, the answer's `^m` ≡ code `**m`) ✓; litter convergence macro `m_growth_litc_soilc` at `macros.gms:20` (linear over 20 yr) ✓.
10. **Density-parameter start.gms citations** — `pm_carbon_density_plantation_ac` 17,20 ✓; `pm_carbon_density_secdforest_ac` 28,31 ✓; `pm_carbon_density_other_ac` 48,51 ✓. All three exact (notably MORE precise than `module_52.md:864`, which cites the litc line as 35).
11. **`s52_growingstock_calib = 1` default + FRA-2025 bisection** — scalar defined `input.gms:46` `/ 1 /`; bisection calibration of secdforest k (`preloop.gms:33,71`) and plantation k (`preloop.gms:76,114`) to FRA 2025 growing stock (`preloop.gms:106`). Only the `vegc` pool of secdforest+plantation is overwritten. ✓
12. **other-land NOT FRA-calibrated** — `pm_carbon_density_other_ac` is NOT reassigned in preloop (no hit). ✓
13. **soilc NOT age-class-specific in M52** — start.gms sets only vegc/litc for the `_ac` params; never soilc. ✓
14. **Module 52 declares no optimization variables** — `declarations.gms` has only `parameters` + `equations` blocks; no `variables` block. ✓
15. **`fm_carbon_density` table** at `input.gms:16-20`, source `lpj_carbon_stocks.cs3` (`input.gms:18`). ✓
16. **Units** — `vm_carbon_stock` "(mio. tC)" (`56/declarations.gms:34`), `q52_emis_co2_actual` "(Tg per yr)" (`52/declarations.gms:30`); 1 mio tC = 1 Tg C identity correct. ✓
17. **Output consumed by M56** — M56 reads `vm_emissions_reg` (`price_aug22/equations.gms:17`). ✓ (Answer doesn't claim 56 is the sole consumer; 51/52/53/57/58 also write it.)

---

## Bugs Found

### Bug R30-B1 — "Module 52 provides static subsoil component"
- **Severity**: Major
- **Class**: 12 (content-level attribution mismatch) — also recorded as latent doc bug (class 15)
- **Trigger** (§1 Major): "The claim is wrong in a way that misleads about behavior, but won't directly cause damaging action." A user wanting to change subsoil-carbon behavior would edit module 52, where no subsoil logic exists.
- **Claim in answer**: M59 row — "Dynamic topsoil C (IPCC 2019 convergence); **Module 52 provides static subsoil component**."
- **Reality in code**: Module 52 provides ONLY the total `fm_carbon_density(t_all,j,land,c_pools)` (LPJmL densities). The topsoil/subsoil SPLIT is computed entirely inside Module 59:
  - `modules/59_som/cellpool_jan23/preloop.gms`: `i59_subsoilc_density(t_all,j) = fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j);`
  - subsoil added to the stock in `q59_carbon_soil` (`cellpool_jan23/equations.gms:62`: `... + vm_land(j2,land)*sum(ct,i59_subsoilc_density(ct,j2))`).
  - The token "subsoil" does NOT appear anywhere in `modules/52_carbon/` (positive control: `rg subsoil` exit 1 in M52 while other M52 tokens match). `f59_topsoilc_density` is a Module-59 input (`59_som/cellpool_jan23/input.gms`, source `lpj_carbon_topsoil.cs2b`), not from M52.
- **Root cause**: `doc_error` (answer reproduced the doc, did NOT beat it). Source: `cross_module/carbon_balance_conservation.md:94-96` — "**Subsoil** (Module 52): Static (fixed from LPJmL); Not affected by land use." This contradicts the code AND the doc's own line 99 ("Module 52 provides **total** soil carbon densities (topsoil + subsoil)") AND `module_59.md:169,324` (which correctly attribute `i59_subsoilc_density` to Module 59). Because the answer propagated the bad framing, it scores against the answer AND is recorded as a latent doc bug to fix.
- **Anchor reference**: resembles the R24 Q4-B3 one-hop / mis-attribution pattern (MANDATE 17): the doc shorthand "Module 52 provides subsoil" mis-locates a sub-mechanism that actually lives in M59.

### Bug R30-B2 — Urban soilc "other-land placeholder" placed in the M34 populator row
- **Severity**: Minor
- **Class**: 12 (attribution placement)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action." The placeholder behavior is real and correctly cited elsewhere; only its table placement mis-suggests M34 sets urban soilc.
- **Claim in answer**: M34 row — "vegc/litc fixed to 0; **soilc = other-land placeholder**."
- **Reality in code**: M34 only fixes the ag_pools (`vm_carbon_stock.fx(j,"urban",ag_pools,stockType)=0`, `34_urban/exo_nov21/presolve.gms:8`); it NEVER touches soilc (positive control: `rg soilc` exit 1 across all of `modules/34_urban/`). Urban soilc in `vm_carbon_stock` is POPULATED by Module 59 (`q59_carbon_soil`, over all `land`; in `static_jan19`, `regularland59` explicitly includes `urban`, `59_som/static_jan19/sets.gms:10`). The "other-land placeholder" itself is a Module-52 INPUT operation: `fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")` (`52_carbon/normal_dec17/input.gms:35`). So the placeholder belongs to M52-input + M59-population, not to M34.
- **Root cause**: `answerer_style_or_framing`. The docs locate the placeholder correctly at M52 input.gms:35 (`module_52.md:857`); the answer's own table grouped it under the M34 populator row. Not a doc error.
- **Note**: Listing M34 *as a populator* is itself CORRECT (it writes ag_pools via `.fx`, and M34 is in the G2 expected set). Only the soilc annotation is misplaced.

---

## Latent doc bugs (recorded regardless of score)

- **carbon_balance_conservation.md:94-96** (also reinforced at :543, :939): frames subsoil as a Module-52 deliverable ("**Subsoil** (Module 52): Static (fixed from LPJmL)"). Code reality: subsoil density is DERIVED inside Module 59 (`i59_subsoilc_density = fm_carbon_density(...,"other","soilc") − f59_topsoilc_density`, `59_som/cellpool_jan23/preloop.gms`); Module 52 provides only the total `fm_carbon_density`. This is the root cause of Bug R30-B1 — the answer trusted the doc. Self-inconsistent with the same doc's line 99 and with `module_59.md:169,324`. Fix: reframe lines 94-96 to "Subsoil split computed by Module 59 from M52's total density minus M59 topsoil density." Severity by future-reader harm: Major (mis-locates where to edit subsoil behavior).

---

## Missing Nuances (not scored)

- `pcm_carbon_stock` is carried forward in two places: M56 postsolve carries the `ag_pools` slice; the soilc slice of `pcm_carbon_stock` is initialized in M59 preloop (`vm_carbon_stock.l(...,"soilc",...)` and the `pcm`/`n` soilc assignments). The answer's "carried forward by Module 56" is true for ag_pools but understates M59's role for soilc. Minor incompleteness, not an error.
- Module 56's PRICING equation (`q56_emis_pricing_co2`) uses `vm_carbon_stock(...,"%c56_carbon_stock_pricing%")` with default `actualNoAcEst` (`default.cfg:1817`), whereas M52's `q52_emis_co2_actual` uses the `"actual"` slice. The question targets M52's emission equation, so the answer's focus on `"actual"` is appropriate; worth flagging that the priced quantity uses a different stockType slice.
- `i52_land_carbon_sink` (Grassi et al. 2021 land carbon sink adjustment) is a Module-52 parameter not mentioned; the answer scoped to densities used by M32/M35, so this is acceptable.

---

## Mechanical checks

- M1 (file:line citations present): PASS — many full-path citations.
- M2 (active realization stated): PASS — `normal_dec17` named; defaults confirmed.
- M3 (variable prefixes valid): PASS — `vm_`, `pcm_`, `pm_`, `fm_`, `s52_` all consistent.
- M4/M5 (epistemic badges / tier matches depth): PASS — closes 🟡 Documented with correct rationale; the 🟡 (not 🟢) tag is appropriate since the answerer worked from docs.
- M6 (closing source statement): PASS — "Verified against … *.gms" footer present.

## Summary
The answer is strong on the load-bearing mechanism (equation, stock-difference math, populator set, sets, macros, calibration) — all verified exact. Score 7/10 reflects one Major doc-propagated mis-attribution (subsoil = M52; actually M59 computes the split) and one Minor framing slip (urban-soilc placeholder grouped under M34's populator row when M59 populates it / M52-input sets the density). The Major is also a latent doc bug at `carbon_balance_conservation.md:94-96` and should be fixed there regardless of the answer score.
