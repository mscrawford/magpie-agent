# Audit Report: Q4 (Are GHG emissions priced in MAgPIE's default config?)

**Round**: 41
**Ground truth**: live GAMS @ develop HEAD ee98739fd (clean working tree)
**Auditor**: Opus 4.8 (1M)

### Overall Verdict: MOSTLY ACCURATE (lower band)
### Accuracy Score: 7/10

`score = max(0, 10 − 4·0 − 2·1 − 1·1) = 7`

The Critical-tier **default-state call is CORRECT**: GHG emissions are not effectively priced in the default config. The headline and the entire (a)/(b) mechanism (NPi2025 ~$0, historical zeroing at `sm_fix_SSP2`, muting until `y2030`, `vm_emission_costs` → objective = 0, M57 `im_maccs_mitigation = 0` at zero price) are verified correct in code. Two errors in the SPECIFICS drop it to 7: one Major (CH4/N2O wrongly said to be unpriced under the default `reddnatveg_nosoil` policy — this is also a latent doc error the answer reproduced) and one Minor (inverted tC↔tCO2 conversion giving a wrong $13.4/tCO2 figure).

---

### Mechanical checks (M1–M6)

| # | Check | Result | Note |
|---|---|---|---|
| M1 | File:line citations present | PASS | Many (`equations.gms:54-58`, `preloop.gms:69-74`, `preloop.gms:16-25`, etc.) — doc-sourced, line caveat stated |
| M2 | Active realization stated | PASS | States `price_aug22` is the only realization AND default (default.cfg:1613); M57 `on_aug22` named |
| M3 | Variable prefixes valid | PASS | `c56_*`, `s56_*`, `im_pollutant_prices`, `vm_emission_costs`, `i57_mac_step_*`, `im_maccs_mitigation` all valid |
| M4 | Epistemic badges present | WEAK PASS | 🟡 on header + source statement; most body claims lack per-claim badges (Informational, not counted) |
| M5 | Confidence tier matches depth | PASS | Tagged 🟡 throughout; explicitly states "No raw .gms files were read" — honest docs-only framing |
| M6 | Closing source statement | PASS | Source Statement block in required form (module_XX.md + config) |

---

### Verified Claims (correct)

- **Headline — GHG NOT priced by default**: ✅ CORRECT. `c56_pollutant_prices = "R34M410-SSP2-NPi2025"` (NPi2025 column present in `f56_pollutant_prices.cs3`, documented ~$0/tC); historical zeroing `im_pollutant_prices(...)$(m_year <= sm_fix_SSP2)=0` (`preloop.gms:70`, `sm_fix_SSP2 = 2025` default.cfg:225) and muting until `c56_mute_ghgprices_until` (`preloop.gms:72`). Mechanism verified directly in code, not just docs.
- **`c56_pollutant_prices = "R34M410-SSP2-NPi2025"`**: ✅ EXACT string verified — `config/default.cfg:1713`.
- **`c56_mute_ghgprices_until = "y2030"`**: ✅ EXACT verified — `config/default.cfg:1726` and `input.gms:88` (`$setglobal c56_mute_ghgprices_until y2030`).
- **`c56_emis_policy = "reddnatveg_nosoil"`**: ✅ EXACT verified — `config/default.cfg:1810`.
- **`s56_minimum_cprice = 3.67 USD17MER/tC` floor**: ✅ value verified — `config/default.cfg:1729`, `input.gms:67` (`/ 3.67 /`), applied at `preloop.gms:74` to `co2_c` only. Cited line `preloop.gms:74` is exactly correct.
- **M56 default realization `price_aug22`, only realization**: ✅ — `ls modules/56_ghg_policy/` → only `price_aug22/` (+ `input/`).
- **M57 default realization `on_aug22`, only realization**: ✅ — only `on_aug22/` (+ `input/`).
- **`vm_emission_costs` = output of `q56_emission_costs` → M11 → objective**: ✅ — `equations.gms:56-58` `q56_emission_costs(i2).. vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source))`. (Answer cited 54-58; eq body at 56-58, 54-55 is the preceding `*'` comment — acceptable doc-style range.)
- **CO2 priced via carbon-stock change (`q56_emis_pricing_co2`), CH4/N2O via `vm_emissions_reg` (`q56_emis_pricing`)**: ✅ — `equations.gms:15-22`.
- **M57 MACC formula transcription**: ✅ EXACT. Answer: `i57_mac_step_n2o = min(201, ceil(Price_N2O/298*28/44*44/12/Step_length)+1)` and `..._ch4 = min(201, ceil(Price_CH4/25*44/12/Step_length)+1)`. Code `preloop.gms:24-25` is character-for-character identical.
- **`ord(maccs_steps) > 1` guard → `im_maccs_mitigation = 0` at step 1 (zero price)**: ✅ — `preloop.gms:46-66`; base init `im_maccs_mitigation(...) = 0` then each source's mitigation summed only over `ord(maccs_steps) > 1`. Comment at `preloop.gms:42-44` matches the answer's "Zero Price Exception". M57 abatement → 0 at default conclusion is correct.
- **`s57_maxmac_*` override scalars all default -1 (inactive)**: ✅ — `config/default.cfg:1840-1844` (all `<- -1`). (Answer hedged "implicitly … default.cfg"; they are in fact explicit — minor self-underrating, Informational only.)
- **CO2 sources priced under `reddnatveg_nosoil` (primforest vegc+litc, secdforest vegc+litc, other vegc+litc, peatland)**: ✅ — `f56_emis_policy.csv:114` (`reddnatveg_nosoil,co2_c`) → 1s at exactly those 7 columns.

---

### Bugs Found

#### Bug Q4-B1 — CH4 and N2O wrongly claimed unpriced under `reddnatveg_nosoil`
- **Severity**: Major
- **Class**: 12 (content-level citation mismatch) + 15 (latent doc error reproduced)
- **Trigger** (§1 Major): "The claim is wrong in a way that misleads about behavior, but won't directly cause damaging action." Also matches "Missing default-state caveat" adjacent — here it's an inverted source-set, not a missing caveat.
- **Claim in answer**:
  > "Under `reddnatveg_nosoil`, the matrix has entries = 1 for CO2 from natural vegetation carbon stocks … but entries = 0 for CH4 and N2O sources … So even if `c56_pollutant_prices` were switched to a mitigation scenario, CH4 and N2O would remain unpriced under the default emission policy."
  and table: `| CH4 | None | All ... |` / `| N2O | None | All ... |`.
- **Reality in code**: `f56_emis_policy.csv` rows for `reddnatveg_nosoil` DO price CH4 and N2O for agricultural sources:
  - `reddnatveg_nosoil,ch4` (`f56_emis_policy.csv:115`) = 1 for: **awms, resid_burn, rice, ent_ferm, peatland** (5 sources).
  - `reddnatveg_nosoil,n2o_n_direct` (`:116`) = 1 for: **inorg_fert, man_crop, awms, resid, resid_burn, man_past, som, rice, peatland** (9 sources).
  - `reddnatveg_nosoil,n2o_n_indirect` (`:120`) = 1 for: inorg_fert, man_crop, awms, resid, resid_burn, man_past, som (7 sources).
  Only CO2 is restricted to natveg-loss pools; agricultural CH4/N2O are fully in. (Header `f56_emis_policy.csv:1`; column→value mapping verified with a CSV parser.)
- **File evidence**: `modules/56_ghg_policy/input/f56_emis_policy.csv:114-120`.
- **Impact / why Major not Critical**: A user who sets a price scenario but leaves the default policy would be told (wrongly) that ag CH4/N2O are not priced; in reality they are. This misleads about model behavior and would surprise the user at output time, but it does not point them at a wrong file or cause a model-breaking edit, so it is Major, not Critical. The CO2 half of the claim is correct, so it is "right concept, wrong on the CH4/N2O sub-matrix."
- **Root cause**: `doc_error` reproduced by the answerer. The answer faithfully copied `module_56.md`'s wrong policy table (line 661 marks CH4 ✗, N2O ✗ for `reddnatveg_nosoil`). Because the answer is itself WRONG here, this scores against the answer (Major) **and** the doc must be fixed (below). This is NOT `doc_error_answerer_beat_it` (the answerer did not beat the doc — it trusted and reproduced it).

#### Bug Q4-B2 — $3.67/tC stated as "~$13.4/tCO2 equivalent" (inverted conversion)
- **Severity**: Minor
- **Class**: 4 (conceptual pseudo-math) — wrong illustrative arithmetic.
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action." Parenthetical illustrative figure.
- **Claim in answer**: "it is extremely small (~$13.4/tCO2 equivalent)".
- **Reality**: tC → tCO2 conversion is **×12/44** (a tonne of C oxidizes to 44/12 t CO2, so the same $/t payment spread over more CO2 tonnes is a LOWER per-tCO2 price). $3.67/tC = 3.67 × 12/44 = **~$1.00/tCO2**. The answer used ×44/12 (3.67 × 44/12 = 13.46), the inverse.
- **File evidence**: code documents the correct direction — `modules/56_ghg_policy/price_aug22/preloop.gms:77` "12/44 conversion from USD17MER per tC to USD17MER per tCO2"; doc `module_56.md:464` "12/44 (C to CO2)". The $13.4 figure appears nowhere in the doc.
- **Root cause**: `answerer_confabulation` (arithmetic error introduced by the answerer; contradicts both code and doc). Off by ~13×, but on an illustrative parenthetical → Minor.

---

### Latent / collateral doc bug to FIX this session (Step 5)

**module_56.md §5.2 policy table (line 661) + §3.7 prose (line 499) understate `reddnatveg_nosoil` for CH4/N2O.**

- **WRONG** (`module_56.md:661`):
  `| **reddnatveg_nosoil** (default) | ✓ (primforest vegc+litc, secdforest vegc+litc, other vegc+litc, peatland) | ✗ | ✗ | ✗ | REDD+ ... |`
  (columns: CO2 LULUCF | CO2 Soil | CH4 | N2O) — marks CH4 and N2O as ✗.
- **CORRECT** (per `f56_emis_policy.csv:114-120`): `reddnatveg_nosoil` prices agricultural CH4 (awms, resid_burn, rice, ent_ferm, peatland) and N2O (inorg_fert, man_crop, awms, resid, resid_burn, man_past, som, rice, peatland; indirect similarly). The CH4 and N2O cells should be ✓ (with a source qualifier), not ✗. Only soil CO2 (and forestry/cropland/pasture vegc) is excluded.
- **WRONG/incomplete** (`module_56.md:499`): the bullet describes ONLY the co2_c entries and says nothing about CH4/N2O, implying (with the table) they are unpriced. Add the CH4/N2O priced-source lists.
- **Severity of the doc bug (future-reader harm)**: Major. A future answerer trusting line 661 reproduces exactly bug Q4-B1 (as this round did). Not Critical by the R20 anchor (it is not a producer/consumer-set error that would derail a refactor; it mis-states which gases a policy prices), but it directly caused this round's Major, so fix unconditionally.
- **Evidence command**: column→value mapping of `f56_emis_policy.csv` rows `reddnatveg_nosoil,{co2_c,ch4,n2o_n_direct,n2o_n_indirect}` against header row 1.

(Note: the doc is internally inconsistent — line 499/661 say CH4/N2O not priced, while the answer's own (c)-section "all_nosoil" discussion and the CDR note at line 665 correctly treat the matrix as gating per source. The fix is to correct the `reddnatveg_nosoil` row/bullet to match the CSV.)

---

### Missing Nuances (not scored)

- **Floor × policy-matrix ordering**: the $3.67/tC floor is applied at `preloop.gms:74`, but the `f56_emis_policy` multiplication (`preloop.gms:85-91`) runs AFTER it. So the floor survives ONLY for co2_c sources where `reddnatveg_nosoil` = 1 (natveg vegc+litc, peatland) and is re-zeroed for forestry/cropland/pasture/soil CO2. The answer says the floor "affects only the CO2 pricing path" (true) but never reconciles it with the matrix zeroing — so "default runs have NO carbon pricing except the floor" is slightly too strong: the floor IS a small non-zero CO2 price on natveg-loss + peatland pools in the default config. Incomplete, not wrong.
- **"NPi" gloss**: answer expands NPi2025 as "No Policy Improvement". In the SSP/REMIND literature NPi = "National Policies implemented" (current policies). The doc itself uses "No additional policy"/"No Policy Improvement" (module_56.md:642, 959), so the answer matches the doc; flag as Informational only.
- Answer did not extract the actual NPi2025 numeric trajectory from the `.cs3` (correctly declined — wide cross-table, hard to parse positionally; the headline does not rest on the exact numbers but on the zeroing/muting mechanics, which were verified).

---

### Summary

The answer nails the high-stakes call (no effective GHG pricing by default) and gets every load-bearing switch string, default, realization, and the M56/M57 zero-price mechanism exactly right against code — including a character-perfect M57 MACC-step formula. It loses 3 points on specifics: (Major) it claims CH4/N2O are unpriced under the default `reddnatveg_nosoil` policy when the CSV prices agricultural CH4/N2O — an error inherited verbatim from a wrong table in `module_56.md` (fix the doc this session); and (Minor) it inverts the tC↔tCO2 conversion, reporting the $3.67/tC floor as ~$13.4/tCO2 when it is ~$1/tCO2. Score 7/10, Mostly Accurate (lower band).

**Doc fixes required**: 1 (module_56.md:661 table + :499 prose — CH4/N2O priced sources under `reddnatveg_nosoil`).
