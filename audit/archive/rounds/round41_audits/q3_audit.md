# Audit Report: Q3 (Age Classes M28, Forest Growth M32, Carbon Accumulation M52)

**Round**: 41
**Auditor**: Opus 4.8 (1M)
**Ground truth**: live GAMS @ develop HEAD ee98739fd (clean)
**Answer audited**: `audit/archive/rounds/round41_answers/q3_answer.md`

---

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10

This is a near-exemplary answer. Every load-bearing claim was verified against the actual `.gms` source and confirmed. The R16 Critical anchor (age-class set extent) is handled exactly right: 62 elements, `ac0`–`ac300` in 5-year steps plus `acx`. The Chapman-Richards + bisection-calibration-to-FRA-2025 machinery — the most confabulation-prone part — is real and reproduced faithfully. No Critical, Major, or Minor code-vs-answer bugs found. Only one informational internal-prose inconsistency (the answer self-corrects it three lines later via the authoritative mapping table).

---

### Mechanical Checks (M1–M6)

| Check | Result | Note |
|---|---|---|
| **M1** File:line citations present | ✅ PASS | Many concrete `file.gms:NN` citations (presolve.gms:83, equations.gms:16–19/108–109/231–232, etc.) |
| **M2** Active realization stated | ✅ PASS | Explicitly states M28=oct24, M32=dynamic_may24, M52=normal_dec17 are sole/default realizations; all three verified in default.cfg:786/976/1556 |
| **M3** Variable prefixes valid | ✅ PASS | `vm_carbon_stock`, `pm_carbon_density_*`, `p32_*`, `s32_shift`, `im_forest_ageclass`, `v32_land` — all prefixes match scope (verified vs declarations) |
| **M4** Epistemic badges present | ✅ PASS | Every substantive claim carries 🟡 (documented) |
| **M5** Confidence tier matches depth | ✅ PASS | All 🟡; answer explicitly states "No raw GAMS .gms files were opened" — honest. (Reality: the docs it relied on were correct, so the 🟡 was warranted and accurate.) |
| **M6** Closing source statement | ✅ PASS | Closes with the three module-doc sources + a line-number-drift caveat |

---

### Verified Claims (correct)

**(a) Age-class set — R16 Critical anchor:**
- `ac` set = **62 elements**, `ac0,ac5,...,ac300, acx` (61 regular @ 5-year steps + `acx`). **EXACT.** Source: `core/sets.gms:269–275` (NOT M28 sets.gms — see Missing Nuances #1). Python count confirms 61 regular + acx = 62. Last regular = `ac300`, final = `acx`. The answer did NOT truncate (the R16 failure mode where the agent said `ac140,acx`).
- `chap_par / k,m /` confirmed at `core/sets.gms:281` (supports the Chapman-Richards claim).
- GFAD provenance (classes 1–14 → 28 split classes ac5–ac140; class15 → acx) corroborated by `ac_gfad_to_ac` mapping in `modules/28_ageclass/oct24/sets.gms:17–33` (class1→ac5,ac10 … class14→ac135,ac140). Internally consistent.

**(b) M32 aging mechanism:**
- Deterministic presolve shift, not an optimization equation. ✅
- `s32_shift = m_yeardiff_forestry(t)/5` — **EXACT** at `modules/32_forestry/dynamic_may24/presolve.gms:83`.
- Shift logic `p32_land(t,j,type32,ac)$(ord(ac) > s32_shift) = pc32_land(j,type32,ac-s32_shift)` (line 89) and overflow into `acx` via `sum(ac$(ord(ac) > card(ac)-s32_shift), pc32_land(...))` (line 91) — **EXACT** (answer cited 89–91; line 90 is a comment, the two code lines reproduced verbatim).
- `m_yeardiff_forestry(t) = 5$(ord(t)=1) + (m_year(t)-m_year(t-1))$(ord(t)>1)` — **EXACT** at `core/macros.gms:45`. Rate is governed entirely by this macro (calendar timestep length). ✅
- `ac_est(ac) = yes$(ord(ac) <= m_yeardiff_forestry(t)/5)`, `ac_sub(ac) = yes$(ord(ac) > m_yeardiff_forestry(t)/5)` — **EXACT** at M28 `presolve.gms:9–10, 12–13`.
- `v32_hvarea_forestry.fx(j,ac_est) = 0` (presolve.gms:9) and `v32_land_reduction.fx(j,type32,ac_est) = 0` (presolve.gms:10) — **EXACT**. (These are `.fx` fixing assignments, a legitimate part of the presolve mechanism — not `.l`/`.lo` reads.)
- `p32_disturbance_loss_ftype32(t,j,"aff",ac_sub)` at `presolve.gms:75` with redistribution to `ac_est` (line 76) — **EXACT**.
- `q32_forestry_est`: `v32_land(j2,type32,ac_est) =e= sum(ac_est2, v32_land(j2,type32,ac_est2))/card(ac_est2)` — **EXACT** at `equations.gms:231–232`.
- `p32_rotation_cellular_harvesting(t,j)` governs plant-type harvesting in ac_sub (presolve.gms:116–117). ✅

**(c) M52 carbon stock chain:**
- `pm_carbon_density_plantation_ac` and `pm_carbon_density_secdforest_ac` (+ `_uncalib` copies) — **EXACT names** at M52 `declarations.gms:9,10,12,13` (matches answer's table line numbers).
- Chapman-Richards macro `m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m` — **EXACT** at `core/macros.gms:18`. S=0 confirmed (`start.gms:9`); A = `fm_carbon_density(...,"secdforest","vegc")` (LPJmL asymptote) confirmed (start.gms:17,28); k,m climate-weighted from `f52_growth_par(clcl,chap_par,forest_type)` with forest_type ∈ {plantations, natveg} confirmed. The `ac×5` is literally inside the macro; the call passes `(ord(ac)-1)` — the answer's reproduction of the macro is faithful.
- **Bisection calibration to FRA 2025 — FULLY VERIFIED, NOT confabulated.** `preloop.gms:23–118`: `loop(iter52, i52_k_calib = (i52_k_low+i52_k_high)/2; ...; i52_k_low$(gs < target)=k; i52_k_high$(gs >= target)=k)` is a textbook bisection on growth-rate k. Targets `f52_fra_nrf_gs(i)` (secdforest) and `f52_fra_pla_gs(i)` (plantation). Log header literally reads "Growing stock calibration to FRA 2025 (m3/ha)" (preloop.gms:106). Secdforest reads `im_forest_ageclass` (from M28, line 55); plantation reads `pm_land_plantation` (from M32, line 90). Both calibrate the `vegc` pool (lines 71, 114).
- `s52_growingstock_calib` default = **1** (on) — confirmed: `input.gms:46  s52_growingstock_calib ... (1) / 1 /`. The answer's "default" claim is correct.
- `p32_carbon_density_ac` type mapping in M32 `presolve.gms:58–68`: `plant`→`pm_carbon_density_plantation_ac` (calibrated, line 65); `ndc`→`pm_carbon_density_secdforest_ac_uncalib` (line 68); `aff`→`pm_carbon_density_secdforest_ac_uncalib` (line 59, switch=0 default) or `pm_carbon_density_plantation_ac_uncalib` (line 61, switch=1) — **EXACT** match to the answer's bullet list.
- `q32_carbon`: `vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e= m_carbon_stock_ac(v32_land,p32_carbon_density_ac,"type32,ac","type32,ac_sub")` — **EXACT** at `equations.gms:108–109`.
- `q52_emis_co2_actual`: `vm_emissions_reg(i2,emis_oneoff,"co2_c") =e= sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)), (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length)` — **EXACT** at `equations.gms:16–19`. The answer's reproduction matches token-for-token.
- `vm_carbon_stock` declared in M56, populated by M32 (+29,31,34,35,59), read by M52 — consistent with the G2 regression anchor ground truth.
- `im_forest_ageclass(j,ac)` declared at M28 `declarations.gms:9` (unit "mio. ha"; answer's "Mha" is equivalent). ✅
- `p32_carbon_density_ac(t,j,type32,ac,ag_pools)` declared at M32 `declarations.gms:19` (matches answer's table). ✅

---

### Bugs Found

**None at Minor or above.** No Critical, Major, or Minor code-vs-answer discrepancies.

**Informational (not scored):**
- **Q3-I1** | Informational | Internal-prose inconsistency | In section (c), the prose bullet describes `pm_carbon_density_secdforest_ac` as "for `ndc`- and secondary-forest stands (calibrated `vegc` pool)". But M32 `presolve.gms:68` maps `ndc → pm_carbon_density_secdforest_ac_uncalib` (the UNcalibrated copy). The answer's own authoritative mapping table three lines later (and section (c) bullet list) correctly states `ndc → pm_carbon_density_secdforest_ac_uncalib`. So the operative/correct mapping is present; the loose "ndc … (calibrated)" phrasing in the parameter-description line is the only slip. A careful reader is not misled because the explicit per-type mapping is correct. Does not contradict code in a way that would cause wrong action → Informational, not Minor. (Note: the calibrated secdforest curve IS used for actual secondary forest, which lives in M35, outside this question's scope.)

---

### Latent doc bugs (§1.5)

**None.** The answer is docs-only ("No raw GAMS .gms files were opened") yet every load-bearing claim it drew from `module_28.md` / `module_32.md` / `module_52.md` matched the code exactly — including the R16 anchor count (62), the bisection calibration (added by PR #869, 2026-04-20), the s52_growingstock_calib=1 default, the type-specific density mapping, and all reproduced equations. This means the underlying module docs for M28/M32/M52 are currently accurate on all the points this answer relied on. No `doc_error_answerer_beat_it` to record.

---

### Missing Nuances

1. **`ac` set declaration site.** The answer says the set "is defined in `modules/28_ageclass/oct24/sets.gms`". In fact the `ac` set is declared in **`core/sets.gms:269–275`**. The M28 `oct24/sets.gms` defines only `ac_gfad`, `ac_young(ac)`, and the `ac_gfad_to_ac` mapping — it references `ac` but does not declare it. This is a location imprecision, not a content error: the *count and elements* (the load-bearing facts, and the R16 anchor target) are stated exactly right. It does not rise to a citation-drift bug because the answer cited the file as 🟡-documented context for "where the age-class system lives," not as a verified file:line for the set elements, and the M28 sets file genuinely is the age-class-system file (it just imports the core `ac`). Worth a doc-note for precision but not score-affecting. (Flagging here so a future round could tighten the doc to say "declared in core/sets.gms; GFAD mapping in 28_ageclass/oct24/sets.gms".)
2. **ac_est/ac_sub declared vs populated.** The answer's variable table lists ac_est/ac_sub "Source/Set" as M28 `presolve.gms:9–10/12–13`. They are *declared* in `core/sets.gms:277,279` and *populated/assigned* in M28 presolve. The answer's prose ("Module 28's presolve.gms computes two dynamic sets each timestep") uses "computes," which is accurate for the populate step. No misattribution.

---

### Summary

Score: **10/10**, Verdict **ACCURATE**. The answer correctly handles the R16 Critical anchor (62-element `ac` set, last regular `ac300`, plus `acx` — no truncation), correctly identifies all three default realizations, and reproduces every cited equation (`s32_shift`, the shift logic, `m_yeardiff_forestry`, `ac_est`/`ac_sub`, `q32_forestry_est`, `q32_carbon`, `q52_emis_co2_actual`, `m_growth_vegc`) token-for-token against the live code. The Chapman-Richards growth function and the bisection-calibration-to-FRA-2025 mechanism (the highest confabulation risk in the question) are genuine and faithfully described, with the `s52_growingstock_calib=1` default correctly reported. The single informational issue (a loose "ndc … calibrated" phrase) is self-corrected by the answer's own mapping table. No doc fixes required; the M28/M32/M52 docs this answer relied on are accurate on every point checked.

**Verified `ac` element count: 62** (61 regular `ac0`–`ac300` in 5-year steps + `acx`). Source: `core/sets.gms:269–275`.
