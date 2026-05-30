# Round 32 Doc Audit — module_53.md (Methane, ipcc2006_aug22)

**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30
**Target**: `modules/module_53.md`
**Ground truth**: `/tmp/magpie_develop_ro` develop worktree + `config/default.cfg`
**Realization audited**: `ipcc2006_aug22` (confirmed default), alt `off`.

---

## Overall Verdict: MOSTLY ACCURATE (with one incomplete prior fix)

The doc is well-verified on its core: all 4 equations match code verbatim, all set counts are correct, the residue-burn scalar (0.0027) is correct, and (most importantly) the **R27 GWP fix held in the primary sections** (lines 443/860/866 correctly state AR5 GWP=28, verified in code). However R27 was **incomplete**: the Key Insights section (lines 1031/1034) still carries the pre-R27 AR4/GWP=25 framing and now *contradicts* the corrected sections and the code. Plus three count/name errors and three minor mis-attributions.

**Claims verified**: ~55 load-bearing claims checked.
**Bugs found**: 7 (4 Major, 3 Minor).

---

## R27 advisory check (GWP) — VERDICT: FIX HELD IN PRIMARY SECTIONS, BUT INCOMPLETE

The pre-run advisory asked: confirm R27's CH4-GWP=28 fix held and all GWP refs are consistent with develop.

**Code ground truth** (`modules/56_ghg_policy/price_aug22/preloop.gms`):
- L78 comment: "*28 and 265 Global Warming Potentials from AR5 WG1 CH08 Table 8.7*"
- L80: `... > s56_limit_ch4_n2o_price*12/44*28` (CH4 GWP=28)
- L81-82: N2O uses `*12/44*265*44/28` (GWP=265)
- M56 default realization = `price_aug22` (only realization). M53→M56 link is real: M56 reads `vm_emissions_reg` at `price_aug22/equations.gms:17`.

**Doc consistency**:
- L443 ✅ "CH4 GWP = 28, IPCC AR5 ... preloop.gms:78,80" — CORRECT, verified.
- L860 ✅ "GWP = 28 ... preloop.gms:78,80 ... N2O uses GWP = 265 (both AR5 ...)" — CORRECT.
- L861 ✅ "Reference values: AR4 CH4 GWP = 25; AR5 = 28 ..." — correct as a *reference* list.
- L866 ✅ "100-year GWP = 28 (AR5, as used by Module 56)" — CORRECT.
- **L1031 ❌ "CH4 GWP = 25 (AR4 100-year) vs. 84 (AR4 20-year)"** — stale pre-R27 framing.
- **L1034 ❌ "MAgPIE uses 100-year GWP (AR4)"** — FALSE. Contradicts L443/860/866 and code (AR5/28).

→ R27 corrected the M56-cited lines but left the Key Insights bullets stale (classic MANDATE-15 post-rename-grep miss: primary sections fixed, secondary section not). Recorded as **53-B1 (Major)**.

---

## Bugs Found

### 53-B1 — GWP vintage wrong in Key Insights (Major)
- **Class**: 6 (hardcoded value drift) / 12 (content mismatch)
- **Trigger**: §1 Major — "Right concept, wrong number" (GWP vintage AR4/25 vs actual AR5/28).
- **Doc**: module_53.md:1034 — "MAgPIE uses 100-year GWP (AR4), may undervalue near-term CH4 mitigation"; supporting L1031 "CH4 GWP = 25 (AR4 100-year) vs. 84 (AR4 20-year)".
- **Reality**: M56 `price_aug22/preloop.gms:78,80` applies CH4 GWP=**28** from **AR5** WG1 Ch08 Table 8.7. The doc itself states this correctly at L443/860/866. L1031/1034 contradict the code and the rest of the doc.
- **Evidence**: `modules/56_ghg_policy/price_aug22/preloop.gms:78` (comment "AR5") + `:80` (`*12/44*28`).
- **verify_cmd**: `rg -n "28|265|12/44|gwp|GWP" .../56_ghg_policy/price_aug22/preloop.gms` → L78 "AR5 WG1 CH08 Table 8.7", L80 `*12/44*28`, L81-82 `*12/44*265*44/28`.
- **Confirmed**: yes.
- **Fix**: L1031 → "CH4 100-year GWP = 28 (AR5, as used by MAgPIE; AR4 value was 25) vs. 84 (20-year)". L1034 → "MAgPIE uses the 100-year GWP = 28 (AR5 WG1 Ch08 Table 8.7; `modules/56_ghg_policy/price_aug22/preloop.gms:78,80`), which may undervalue near-term CH4 mitigation relative to the 20-year horizon." (Align with L866.)

### 53-B2 — `vm_manure` awms set element count wrong (Major)
- **Class**: 6 (hardcoded count drift)
- **Trigger**: §1 Major — "Fabricated count for a set/parameter/realization list."
- **Doc**: module_53.md:404 — "the set is `awms` (animal waste management systems, **11 elements**)."
- **Reality**: `awms` has **4 elements** (`grazing, stubble_grazing, fuel, confinement`). The 9-element set is `awms_conf` (`lagoon, liquid_slurry, solid_storage, drylot, daily_spread, digester, other, pit_short, pit_long`). 11 matches neither.
- **Evidence**: `modules/55_awms/ipcc2006_aug16/sets.gms:10-11` (`awms / grazing, stubble_grazing, fuel, confinement /`); `:16-17` (`awms_conf` = 9 elements). `vm_manure(i, kli, awms, npk)` at `55_awms/ipcc2006_aug16/declarations.gms:19`.
- **verify_cmd**: `sed -n '8,17p' .../55_awms/ipcc2006_aug16/sets.gms` → awms = 4 members; awms_conf = 9 members.
- **Confirmed**: yes.
- **Fix**: change "11 elements" → "4 elements (grazing, stubble_grazing, fuel, confinement)". (The doc's own L733 correctly says "Module 55 tracks 9 confinement systems" = awms_conf.)

### 53-B3 — "Both have 4 equations" claim about Module 51 wrong (Major)
- **Class**: 6 (hardcoded count drift)
- **Trigger**: §1 Major — "Fabricated count" (parallels R6 anchor: claimed m15 has 22 eq, actual 17 → Major).
- **Doc**: module_53.md:953 — under "## 10. Comparison with Module 51 (Nitrogen) / Similarities": "Both have 4 equations".
- **Reality**: M51 default realization `rescaled_jan21` has **8** equations: q51_emissions_man_crop, q51_emissions_inorg_fert, q51_emissions_resid, q51_emissions_resid_burn, q51_emissions_som, q51_emissionbal_awms, q51_emissionbal_man_past, q51_emissions_indirect_n2o. (M53 has 4; M51 has 8.)
- **Evidence**: `modules/51_nitrogen/rescaled_jan21/equations.gms` lines 22,30,42,49,55,65,74,83.
- **verify_cmd**: `grep -nE '^\s*q51_' .../51_nitrogen/rescaled_jan21/equations.gms` → 8 equation headers.
- **Confirmed**: yes.
- **Fix**: remove "Both have 4 equations" from the Similarities list, OR replace with "Module 53 has 4 equations; Module 51 (rescaled_jan21) has 8." (Note: moving it to Differences is more accurate.)

### 53-B4 — Wrong residue-burn equation name (Major; tier_uncertainty)
- **Class**: 9 (wrong equation name)
- **Trigger**: between §1 Critical ("Invented equation name presented as authoritative") and Major ("wrong equation name"). Tie-breaker → Major: the correct name appears 4× elsewhere in the same doc and the line self-cross-references §326 where the correct name is given.
- **Doc**: module_53.md:57 — "Residue burning (q53_emissionbal_ch4_resid_burn) is the exception". (Not backticked, so the equation-name checker does not catch it.)
- **Reality**: the equation is `q53_emissions_resid_burn`. The pattern `q53_emissionbal_ch4_*` is the form of the OTHER three equations (ent_ferm/awms/rice), so this is a plausible-but-nonexistent construction. Doc uses the correct `q53_emissions_resid_burn` at L326, L376, L669, L1054.
- **Evidence**: `modules/53_methane/ipcc2006_aug22/equations.gms:70` (`q53_emissions_resid_burn(i2) ..`); also declarations.gms:13, postsolve.gms:14,18,22,26.
- **verify_cmd**: `rg -n "resid_burn" .../53_methane/ipcc2006_aug22/*.gms` → only `q53_emissions_resid_burn`; no `q53_emissionbal_ch4_resid_burn` anywhere in code.
- **Confirmed**: yes.
- **Fix**: L57 "(q53_emissionbal_ch4_resid_burn)" → "(`q53_emissions_resid_burn`)".

### 53-B5 — `vm_area` provider "or Module 17" wrong (Minor)
- **Class**: 6/15 (mis-attribution)
- **Trigger**: §1 Minor — wrong detail; doc leads with correct M30, so a careful reader is not misled.
- **Doc**: module_53.md:557 "Module 30 (Croparea) or Module 17 (Production): `vm_area(j,"rice_pro",w)`"; mirrored at L1057.
- **Reality**: `vm_area` is DECLARED only in Module 30 (`simple_apr24/declarations.gms:18`, `detail_apr24/declarations.gms:21`). Module 17 is a *consumer*, not a provider. The doc's primary Interface entry (L409) and L277 correctly attribute it to M30.
- **verify_cmd**: `grep -rln "vm_area(" .../modules/*/*/declarations.gms` → only the two M30 realizations.
- **Confirmed**: yes.
- **Fix**: L557 and L1057 → drop "or Module 17 (Production)". Provider is Module 30 only.

### 53-B6 — Module 11 listed as direct consumer of `vm_emissions_reg` (Minor)
- **Class**: 15 (one-hop / transitive consumer — MANDATE 17)
- **Trigger**: §1 Minor — the doc's Downstream Dependencies (L581) correctly says "Module 11 (Costs): Indirectly via Module 56", so a careful reader gets the right picture; only the Interface-Variables "Consumers" line (L438) conflates direct+indirect. (Resembles R24 Q4-B3 anchor, which was Major; downgraded here because the doc states the indirection correctly elsewhere.)
- **Doc**: module_53.md:438 — "**Consumers**: Module 56 (GHG Policy) ..., Module 11 (Costs) for GHG cost in objective function".
- **Reality**: M11 does NOT directly read `vm_emissions_reg`. Path: M56 reads `vm_emissions_reg` (`price_aug22/equations.gms:17`) → produces `vm_emission_costs` → M11 reads `vm_emission_costs` (`11_costs/default/equations.gms:26`). One-hop transitive.
- **verify_cmd**: `grep -rn "vm_emissions_reg" .../modules/11_costs/` → exit 1 (no match). Positive control: `grep -rln "vm_cost_glo" .../modules/11_costs/` → 5 files (grep works in that dir). Direct consumers of vm_emissions_reg: M51, M52, M53, M57, M58 (populate) + M56 (reads).
- **Confirmed**: yes.
- **Fix**: L438 → "**Consumers**: Module 56 (GHG Policy), which reads `vm_emissions_reg` for carbon pricing. Module 11 (Costs) is a *transitive* consumer via Module 56's `vm_emission_costs` (it does not read `vm_emissions_reg` directly)."

### 53-B7 — `fm_attributes` provider mis-attributed (Minor)
- **Class**: 6/15 (mis-attribution)
- **Trigger**: §1 Minor — heavily hedged in doc ("potentially", "or Core"); recoverable.
- **Doc**: module_53.md:397 "(Core declarations or Module 09)"; L401 "Provider: Core data files, potentially Module 09 (Drivers)"; L569 "Module 09 (Drivers) or Core: `fm_attributes(...)`".
- **Reality**: `fm_attributes(attributes,kall)` is declared (as a `table`) ONLY in Module 16 (`16_demand/sector_may15/input.gms:20`). It is NOT in `core/` and NOT in Module 09. Both offered options are wrong (though it functions as shared file data, consistent with the `fm_` interface-file prefix).
- **verify_cmd**: `grep -rn "table fm_attributes" /tmp/magpie_develop_ro/` → only `16_demand/sector_may15/input.gms:20`. `grep -rln "fm_attributes" .../core/ .../modules/09_drivers/` → exit 1 (absent in both). Positive cross-check: dim `(attributes,kall)` matches doc L397.
- **Confirmed**: yes.
- **Fix**: replace "Core declarations or Module 09 (Drivers)" with "Module 16 (Demand): `fm_attributes(attributes,kall)` (`modules/16_demand/sector_may15/input.gms:20`) — an `fm_` file-interface table read model-wide". (Low priority given the hedge.)

---

## Verified Correct (high-value confirmations)

- **All 4 equations verbatim** vs `ipcc2006_aug22/equations.gms`:
  - q53_emissionbal_ch4_ent_ferm L21-29 ✅ (1/55.65; Ym 0.03 livst_rum-conc, 0.065 livst_milk-conc, 0.065 noconc; MACC term).
  - q53_emissionbal_ch4_awms L48-52 ✅ (`vm_manure(...,"confinement","nr")` × `f53_ef_ch4_awms` × MACC).
  - q53_emissionbal_ch4_rice L59-63 ✅ (`vm_area(j2,"rice_pro",w)` × `f53_ef_ch4_rice` × MACC).
  - q53_emissions_resid_burn L70-72 ✅ (`sum(kcr, vm_res_ag_burn(i2,kcr,"dm")) * s53_ef_ch4_res_ag_burn`; NO MACC term — correctly noted).
- **Default realization** `ipcc2006_aug22` ✅ (`config/default.cfg:1583`). Alt `off` ✅ (only 2 realizations). off/preloop.gms:11 `vm_emissions_reg.fx(...,"ch4")=0` ✅ (doc L537 "Likely fixes ...=0" correct).
- **s53_ef_ch4_res_ag_burn = 0.0027** ✅ (`input.gms:25`).
- **Set counts** all correct: k_conc53=27 (sets.gms:11-14, counted), k_noconc53=5 (16-17), k_ruminants53=2 (19-20), emis_source_methane53=4 (22-23). k_conc53 member list (incl. livst_rum/pig/chick/egg/fish, excl. livst_milk) ✅.
- **Interface variable declarations** (all dims + sites confirmed):
  - `vm_emissions_reg(i,emis_source,pollutants)` — M56 `price_aug22/declarations.gms:40` (unit "Tg per yr"; doc's unit-mismatch note is fair). Sole declarer.
  - `vm_feed_intake(i,kap,kall)` — M70 `fbask_jan16/declarations.gms:18` (default `fbask_jan16` ✅; doc L391 `kap`-not-`kli` note correct).
  - `vm_manure(i,kli,awms,npk)` — M55 `ipcc2006_aug16/declarations.gms:19` (default `ipcc2006_aug16` ✅). `npk /nr,p,k/`, `awms` incl. `confinement` ✅.
  - `vm_area(j,kcr,w)` — M30 simple_apr24:18 / detail_apr24:21 ✅ (default `simple_apr24`).
  - `vm_res_ag_burn(i,kcr,attributes)` — M18 (default `flexreg_apr16`; decl confirmed flexcluster_jul23:18) ✅.
  - `im_maccs_mitigation(t,i,emis_source,pollutants)` — M57 `on_aug22/declarations.gms:13` (default `on_aug22` ✅; PBL_2022 — doc L862 PBL hedge correct).
- **Module structure file line-ranges** (module.gms 8-20, realization.gms 8-25, sets.gms 8-25, input.gms 8-27, equations.gms 8-72, preloop.gms 8-10, postsolve.gms 8-28) all within actual EOFs ✅. Author B.L. Bodirsky module.gms:15 ✅.
- **GWP=28 / AR5** at L443/860/866 ✅ (the R27-fixed lines).
- **M52 is CO2-only** (doc L942) ✅ — M52 writes only `"co2_c"` (`normal_dec17/equations.gms:17`).
- **3-of-4 MACC** (doc L13/57) ✅ — mitigation term present at eq L29/52/63, absent at L70-72.
- Arithmetic in illustrative examples checks out (1328/55.65=23.9; 350000×0.0027=945).

---

## Deferred (not code-verified / out of scope — NOT to be edited)

- module_53.md:955 "Module 51 tracks 7 N emission sources" — plausibly off (M51 has 8 equations and an `emis_source_n51` set), but counting distinct *sources* vs *equations* needs deeper M51 set analysis; comparative/tangential; left unverified to avoid a false positive.
- The "Tg per yr vs tCH4" unit-mismatch discussion (L437/442) — interpretive commentary on M56's declaration label; not a discrete code-checkable claim.
- Various "% of agricultural CH4" figures (L972, 985, 992, 998, 1007-1008 etc.) and real-world Ym/mitigation efficacy ranges — domain/literature claims, not MAgPIE-code claims (correctly framed as such in doc).

---

## Notes for the fixer
- 53-B1 is the priority: it's an internal contradiction that re-opens the exact bug R27 closed. Fix L1031+L1034 to match L866. Run `grep -n "GWP\|AR4\|AR5" modules/module_53.md` afterward to confirm no remaining AR4-as-model-behavior claim.
- 53-B4 escapes the equation-name checker only because the name is not backticked; backticking the corrected name also restores checker coverage.
- None of the 7 bugs are caught by `scripts/validate_consistency.sh` (ran clean on module_53: 40/42, 2 unrelated advisories) — all are prose-level semantic/count/attribution errors.
