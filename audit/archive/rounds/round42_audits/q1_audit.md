# Audit Report: Q1 (LUC CO2 → Global Objective Cost Chain)

**Round:** 42 | **Date:** 2026-06-03 | **Auditor:** Opus (semantic-validation flywheel)
**Ground truth:** live GAMS @ develop HEAD `ee98739fd` (clean), `config/default.cfg`, `modules/56_ghg_policy/input/f56_emis_policy.csv`
**Answer audited:** `audit/archive/rounds/round42_answers/q1_answer.md`

---

### Overall Verdict: SIGNIFICANT ERRORS
### Accuracy Score: 4/10

The chain mechanics (a, b, c) are essentially flawless — every equation name, file:line citation, set membership, and the f56_emis_policy gate are verified correct against code. The score is pulled down by sub-question (d), the explicit focus of this round: the answer asserts the **opposite of the truth** about whether `redd+natveg_nosoil` prices agricultural CH4/N2O, and it leans on `module_56.md:662`, which carries the same wrong claim. This is a confirmed **sibling bug** to the one fixed in R41-Q4. One Critical (inverted policy-coverage claim that would cause a user to choose the wrong scenario) plus the latent doc bug it rests on.

---

### Verified Claims (correct)

**(a) f56_emis_policy gate**
- Binary 0/1 matrix `f56_emis_policy(scen56, pollutants, emis_source)`. ✓ Confirmed: every entry in the relevant rows of `f56_emis_policy.csv` is 0 or 1 (the `_CH4GWP20` variants use 3 as a GWP20 scaling, but the default-family rows are 0/1).
- Gate is **multiplicative** (`im_pollutant_prices × f56_emis_policy(...)`), a true 0/1 gate not a scale. ✓ `modules/56_ghg_policy/price_aug22/preloop.gms:84-91`:
  ```gams
  loop(t_all,
   if(m_year(t_all) <= sm_fix_SSP2,
    im_pollutant_prices(t_all,i,pollutants,emis_source) = im_pollutant_prices(...) * f56_emis_policy("reddnatveg_nosoil",pollutants,emis_source);
   else
    im_pollutant_prices(t_all,i,pollutants,emis_source) = im_pollutant_prices(...) * f56_emis_policy("%c56_emis_policy%",pollutants,emis_source);
   );
  );
  ```
  Line numbers **exact** (84-91). The historical-override claim (years ≤ `sm_fix_SSP2` always use the hardcoded `"reddnatveg_nosoil"` row) is correct (preloop.gms:86-87).

**(b) Pricing chain**
- `q52_emis_co2_actual` populating `vm_emissions_reg(i,emis_oneoff,"co2_c")` = (pcm−vm carbon stock)/m_timestep_length. ✓ `modules/52_carbon/normal_dec17/equations.gms:16-19` (answer cited 16-19 — exact).
- `q56_emis_pricing_co2` computes the same stock-change INDEPENDENTLY (does NOT route LUC CO2 through `vm_emissions_reg`), using `vm_carbon_stock(...,"%c56_carbon_stock_pricing%")`. ✓ `modules/56_ghg_policy/price_aug22/equations.gms:19-22` (answer cited 19-22 — exact).
- `%c56_carbon_stock_pricing%` default = `actualNoAcEst`. ✓ `input.gms:90` (`$setglobal c56_carbon_stock_pricing actualNoAcEst`) and `config/default.cfg:1817`. The "excludes afforestation establishment to avoid double-counting CDR" gloss is a reasonable reading of the name.
- Annual emissions (CH4/N2O/annual CO2) DO flow through `vm_emissions_reg` via `q56_emis_pricing`. ✓ `equations.gms:15-17` (answer cited 15-17 — exact).
- `q56_emission_cost_oneoff`: `v56_emis_pricing × m_timestep_length × im_pollutant_prices × pm_interest/(1+pm_interest)`. ✓ `equations.gms:45-52` (answer cited 45-52 — exact). Annuity-factor explanation correct.
- `q56_emission_cost_annual`: `v56_emis_pricing × im_pollutant_prices`. ✓ `equations.gms:29-33` (answer cited 29-33 — exact).
- `q56_emission_costs .. vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source))`. ✓ `equations.gms:56-58` (answer cited 56-58 — exact).
- `vm_carbon_stock` DECLARED in M56, not M52. ✓ `modules/56_ghg_policy/price_aug22/declarations.gms:34`. Matches the G2 calibration anchor.
- `emis_oneoff` = land carbon-pool sources; `emis_annual` = `inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm, resid_burn, peatland`. ✓ `core/sets.gms:314-322`. The oneoff-vs-annual routing the answer describes is correct.

**(c) Entry into M11 objective**
- `q11_cost_reg` includes `+ vm_emission_costs(i2)`. ✓ `modules/11_costs/default/equations.gms:26` (answer cited :26 — exact).
- `- vm_reward_cdr_aff(i2)` immediately after, negative sign. ✓ `equations.gms:27` (answer cited :27 — exact).
- `q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2))`. ✓ `equations.gms:10` (answer cited :10 — exact). `vm_cost_glo` is the minimand.

**(d) — partially correct**
- The **default** `reddnatveg_nosoil` DOES price ag CH4/N2O. ✓ CONFIRMED from `f56_emis_policy.csv:114-129`: ch4 nonzero on `{awms, resid_burn, rice, ent_ferm, peatland}`; n2o_n_direct nonzero on `{inorg_fert, man_crop, awms, resid, resid_burn, man_past, som, rice, peatland}`; n2o_n_indirect nonzero on `{inorg_fert, man_crop, awms, resid, resid_burn, man_past, som}`. The answer's default-row CH4/N2O source lists are exactly right.

---

### Bugs Found

#### Bug Q1-B1 — `redd+natveg_nosoil` claimed to NOT price ag CH4/N2O (it does)
- **Bug ID:** Q1-B1
- **Severity:** 🔴 **Critical**
- **Class:** 13 (Wrong parameter default/value) — here, wrong policy-matrix content claimed as authoritative
- **Trigger:** "Active mechanism claimed when actually OFF by default" / inverted Boolean — the answer claims ag CH4/N2O pricing is OFF for this scenario when the matrix has it ON. A user choosing `redd+natveg_nosoil` to "price forestry CO2 but exclude ag non-CO2" would get the opposite of the documented behavior — a load-bearing scenario-selection error.
- **Claim in answer:** *(d)* "**No.** … `redd+natveg_nosoil` covers only CO2 from deforestation and reforestation. It does **not** price agricultural CH4 or N2O. This is in contrast to the default `reddnatveg_nosoil` (no `+`), which does price agricultural non-CO2 gases. The `+` in the name signals an expanded forestry CO2 coverage … but at the same time the policy does not extend to non-CO2 agricultural sources." (answer lines 196-202)
- **Reality in code:** `redd+natveg_nosoil` and the default `reddnatveg_nosoil` are **byte-identical on every non-CO2 pollutant row**. The ONLY difference between the two policies is in the `co2_c` row, at two cells: `forestry_vegc` and `forestry_litc` flip 0→1 (i.e. the `+` adds *forestry/plantation* CO2 — not "reforestation" in the loose sense the answer uses, and nothing to do with non-CO2). Ag CH4/N2O pricing is **identical** to the default.
- **File evidence:** `modules/56_ghg_policy/input/f56_emis_policy.csv`
  - `reddnatveg_nosoil,ch4` (line 115): `…awms=1, resid_burn=1, …rice=1, ent_ferm=1, …peatland=1`
  - `redd+natveg_nosoil,ch4` (line 243): **identical** — `…awms=1, resid_burn=1, …rice=1, ent_ferm=1, …peatland=1`
  - `reddnatveg_nosoil,n2o_n_direct` (line 116) vs `redd+natveg_nosoil,n2o_n_direct` (line 244): **identical**
  - `reddnatveg_nosoil,n2o_n_indirect` (line 120) vs `redd+natveg_nosoil,n2o_n_indirect` (line 248): **identical**
  - Row-by-row Python comparison of all 16 pollutant rows: only `co2_c` DIFFERS, at `forestry_vegc` (0→1) and `forestry_litc` (0→1). All 15 other pollutant rows IDENTICAL.
- **Anchor reference:** Resembles the R41-Q4 fixed bug (sibling). The mechanism by which the answer was misled — trusting `module_56.md:662` — is the §1.5 "answerer trusted a wrong doc" pattern (R20 anchor): the doc's policy-coverage table was wrong and the answerer reproduced it.

#### Bug Q1-B2 (latent doc bug) — `module_56.md:662` marks `redd+natveg_nosoil` CH4/N2O as ✗
- **Bug ID:** Q1-B2
- **Severity:** 🔴 **Critical** (by future-reader harm — R20 anchor; a reader trusting this row would mis-select the scenario)
- **Class:** 15 (Latent doc error — answer did NOT beat it; the answer reproduced it, so this is the *root* of Q1-B1)
- **Root cause:** `doc_error` (the doc is wrong; here the answer also failed, so it is both a doc bug AND the source of the answer bug, not a `doc_error_answerer_beat_it`).
- **Doc claim:** `magpie-agent/modules/module_56.md:662`:
  `| **redd+natveg_nosoil** | ✓ (deforestation + reforestation) | ✗ | ✗ | ✗ | REDD+ with forestry emission pricing |`
  (columns: CO2 LULUCF | CO2 Soil | CH4 | N2O | Use Case)
- **Reality in code:** CH4 and N2O columns must be ✓ (ag sources priced, identical to the default row 661). The CO2 LULUCF cell's gloss "(deforestation + reforestation)" is also imprecise: the `+` adds **forestry_vegc + forestry_litc** (plantation/managed-forest vegetation+litter CO2) on top of the natveg coverage; it is NOT "reforestation."
- **File evidence:** same CSV rows as Q1-B1 (lines 242-257 vs 114-129).
- **Verdict on the line 662 question (explicit ask):** **`module_56.md:662` is WRONG.** It is a sibling of the R41-fixed bug. It must be fixed this session (validate-semantic Step 5).

#### Bug Q1-B3 (Minor) — (d) scenario list framed as the set, but is a small non-exhaustive sample
- **Bug ID:** Q1-B3
- **Severity:** 🟡 **Minor**
- **Class:** 6 (Hardcoded counts / set incompleteness) — descriptive incompleteness, careful reader not misled into a wrong action
- **Trigger:** Tie-broken DOWN from Major. The sub-question asks "which non-default scenarios additionally price ag CH4/N2O." The answer's table lists only `{all, all_nosoil, reddnatveg_nosoil(default), sdp_all}` and says "The following non-default scenarios price agricultural CH4 and/or N2O." In fact **33 of 44** scenarios price ag CH4/N2O, including the entire `redd*`, `reddnatveg*`, `redd+*`, `redd+natveg*`, `ecoSysProt*`, `sdp_*`, `gcs_res` families. The answer's own headline scenario (`redd+natveg_nosoil`) is itself a member of that 33 — which is precisely why the (d) "No" is wrong. Kept Minor (not Major) because the answer doesn't claim the list is exhaustive count-wise and the question's operative clause is the redd+natveg_nosoil verdict (covered by B1); but a reader could under-estimate how broadly ag non-CO2 is priced across the scenario menu.
- **File evidence:** `f56_emis_policy.csv` — Python enumeration over all scenario keys: 33/44 have ≥1 ag non-CO2 source priced. The `sdp_all` row is correctly ✓/✓ but with a *narrower* ag set (ch4: awms, rice, ent_ferm; n2o_dir: awms only) than the answer's generic "✓ ✓" implies — a minor imprecision folded into this bug.

---

### Mechanical Checks (M1–M6)

| # | Check | Result | Note |
|---|---|---|---|
| **M1** | File:line citations present | ✅ PASS | Many exact `modules/XX/realization/file.gms:NN` cites; all (a)(b)(c) line numbers verified exact. |
| **M2** | Active realization stated | ✅ PASS | States M56 single realization `price_aug22`; confirms default. |
| **M3** | Variable prefixes valid | ✅ PASS | `vm_*`, `pm_*`, `v56_*`, `q56_*`, `im_*`, `f56_*`, `c56_*` all correct prefix/scope. |
| **M4** | Epistemic badges present | ⚠️ PARTIAL | Every block tagged 🟡; but 🟡 ("documented, no code opened") was claimed for content that — for sub-question (d) — turned out to contradict code. Badge present but mis-calibrated (see M5). |
| **M5** | Confidence tier matches depth | ❌ FAIL | The answer self-declares "No raw GAMS source was opened" and tags everything 🟡. For (d) it relied entirely on `module_56.md:662` without checking `f56_emis_policy.csv` — exactly the doc-trust failure that produced B1. A 🟡 tag is honest about depth, but the depth was insufficient for a policy-matrix claim the CSV would have settled in one grep. (Informational-level for scoring; not double-counted as a content bug.) |
| **M6** | Closing source statement | ✅ PASS | Has a "Source Statement" enumerating module docs + default.cfg. |

M-check failures are indicators, not scored bugs. M5's failure is the proximate cause of B1: the gate matrix is INPUT DATA (`.csv`), and the answer's docs-only posture meant it never read the one file that decides (d).

---

### Missing Nuances
- The `+` semantics: the answer says the `+` adds "reforestation" CO2. The CSV shows the `+` toggles `forestry_vegc`/`forestry_litc` (managed plantation forest carbon), distinct from `natveg` (primforest/secdforest/other). Worth stating precisely, since the family naming (`redd` vs `redd+` vs `reddnatveg` vs `redd+natveg`) is a 2×2 of {plantation forestry on/off} × {natveg on/off} over the CO2 row, with all four sharing the SAME ag non-CO2 pricing.
- `s56_limit_ch4_n2o_price` (preloop.gms:80-82) caps CH4/N2O prices but does not zero them — irrelevant to the gate, but it is the other place CH4/N2O prices are touched before the gate; not load-bearing for the question.
- The `_CH4GWP20` variants store `3` (not `1`) in the ch4 row — a GWP20 rescaling embedded in the gate matrix, i.e. the matrix is not strictly 0/1 for those rows. The answer's "0/1" generalization is true for the default family but not universally; not penalized (out of scope).

---

### Summary
Sub-questions (a), (b), (c) are model-auditor-grade: equation names, set memberships, the f56 gate, the annuity factor, the M52/M56 declaration split, and all file:line citations are verified exact against develop HEAD. The answer correctly nails the G2-adjacent chain and the default `reddnatveg_nosoil` ag-pricing detail.

The failure is concentrated in (d) and is the round's target: **`redd+natveg_nosoil` DOES price ag CH4/N2O — byte-identically to the default — and the answer claims it does not**, reproducing the wrong row at `module_56.md:662`. The two policies differ in exactly two CO2 cells (`forestry_vegc`, `forestry_litc`); every non-CO2 row is identical. **`module_56.md:662` is WRONG** and is a sibling of the R41-Q4 fixed bug; it must be corrected this session.

**Score:** `10 − 4·1(crit B1) − 2·0 − 1·1(minor B3) = 5`. B2 is a latent/root doc bug at Critical future-reader harm but, per §1.5, it does not further lower the answer score (it is the same defect as B1 viewed doc-side); recorded in `doc_errors_latent[]` and fixed regardless. **Final: 5/10** (tie-break note: B1 is unambiguously Critical via the inverted-mechanism trigger; no downgrade applied).

---

### DOC BUGS TO FIX (this session, validate-semantic Step 5)

**File:** `magpie-agent/modules/module_56.md` **line 662**

WRONG (current):
```
| **redd+natveg_nosoil** | ✓ (deforestation + reforestation) | ✗ | ✗ | ✗ | REDD+ with forestry emission pricing |
```

CORRECT (replace with):
```
| **redd+natveg_nosoil** | ✓ (natveg primforest/secdforest/other vegc+litc, peatland, PLUS forestry_vegc+forestry_litc) | ✗ | ✓ (same ag sources as reddnatveg_nosoil: awms, resid_burn, rice, ent_ferm, peatland) | ✓ (same ag sources as reddnatveg_nosoil: inorg_fert, man_crop, awms, resid, resid_burn, man_past, som, rice + indirect N) | REDD+ natveg CO2 + plantation-forestry CO2 + agricultural non-CO2 |
```

**Code evidence:** `modules/56_ghg_policy/input/f56_emis_policy.csv`, rows `redd+natveg_nosoil` (lines 242-257) vs `reddnatveg_nosoil` (lines 114-129): the two scenarios are identical on all 15 non-CO2 pollutant rows; they differ ONLY in `co2_c` at `forestry_vegc` (0→1) and `forestry_litc` (0→1). Therefore the CH4 and N2O columns for `redd+natveg_nosoil` are ✓ with the same ag source sets as the default `reddnatveg_nosoil` row (line 661), and the `+` denotes added plantation-forestry CO2, not "reforestation," and not any change to non-CO2 coverage.

*(Optional consistency check for the fixer: the same plantation-forestry-vs-natveg-vs-ag-non-CO2 structure should be applied if any sibling `redd*` / `redd+*` rows appear elsewhere in module_56.md or its notes; the R41 fix already corrected the default row 661.)*
