# Audit Report: Q1 (2nd-gen lignocellulosic bioenergy: demand → land allocation → cost objective)

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 7/10

Auditor: Opus (R28). All FACTUAL claims verified against the clean origin/develop worktree at
`/tmp/magpie-develop-r28/` (commit ee98739fd). Doc-vs-code latent checks against
`magpie-agent/modules/module_60.md`, `module_16.md`, `module_21.md`.

---

### Mechanical checks (M1-M6)

| Check | Result | Note |
|---|---|---|
| M1 file:line citations present | PASS | Many `realization/file.gms:NN` citations throughout. |
| M2 active realization stated | PASS | Every module's default realization named (M60 `1st2ndgen_priced_feb24`, M16 `sector_may15`, M17 `flexreg_apr16`, M21 `selfsuff_reduced`, M30 `simple_apr24`, M14 `managementcalib_aug19`, M38 `sticky_feb18`, M11 `default`) — all confirmed against default.cfg. |
| M3 variable prefixes valid | PASS | `vm_`, `v60_`, `i60_`, `s60_`, `c60_`, `q60_` etc. all consistent with code. |
| M4 epistemic badges present | PASS | §11 supplies per-module 🟡/🟢 badges. |
| M5 confidence tier matches depth | PASS | Answer honestly tags itself 🟡 Documented (docs-only test) and 🟢 only for config values; explicitly states no .gms read this session. |
| M6 closing source statement | PASS | §11 closes with documentation-source statement. |

---

### Verified Claims (correct against worktree)

- **M60 default realization** = `1st2ndgen_priced_feb24`: `config/default.cfg:1982` (`cfg$gms$bioenergy <- "1st2ndgen_priced_feb24"`). ✓
- **`kbe60(kall) = / betr, begr /`**: `modules/60_bioenergy/1st2ndgen_priced_feb24/sets.gms:111-112`. ✓ (answer's one-line rendering of a 2-line decl is cosmetic.)
- **`k1st60 = / oils, ethanol /`**: sets.gms:114-115. ✓
- **`q60_bioenergy` (16-21)**: `vm_dem_bioen(i2,kall)*fm_attributes("ge",kall) =g= sum(ct,i60_1stgen_bioenergy_dem(ct,i2,kall)) + v60_2ndgen_bioenergy_dem_dedicated(i2,kall) + v60_2ndgen_bioenergy_dem_residues(i2,kall)`. equations.gms:16-21. ✓ exact.
- **`q60_bioenergy_glo` (43-44)** and **`q60_bioenergy_reg` (46-47)**: exact; RHS gating by `c60_biodem_level` / `(1-c60_biodem_level)` correctly described; default `c60_biodem_level=1` (regional) makes glo RHS zero. equations.gms:43-47; `input.gms:37` (`/ 1 /`); `default.cfg:2086`. ✓
- **`q60_res_2ndgenBE` (61-64)**: exact. ✓ Residue default scenario `ssp2`: `input.gms:69`, `default.cfg:2081`. ✓
- **`q60_bioenergy_incentive` (73-75)**: exact, including 1st- and 2nd-gen subsidy terms with `(-i60_..._subsidy)` sign. equations.gms:73-75. ✓
- **`vm_dem_bioen(i,kall)` declared declarations.gms:20** (mio. tDM/yr); **`vm_bioenergy_utility(i)` declarations.gms:26** (USD17MER/yr). ✓
- **`c60_2ndgen_biodem` default `R34M410-SSP2-NPi2025`**: `input.gms:45`, `default.cfg:2061`; blending with `c60_2ndgen_biodem_noselect` in `preloop.gms:30-31`. ✓
- **`i60_bioenergy_dem` blending in `preloop.gms:30-31`**: confirmed (`$else` branch, population-share weighting via `p60_region_BE_shr`). ✓
- **`s60_bioenergy_1st_subsidy = 6.5` (input.gms:38)** and **`s60_2ndgen_bioenergy_dem_min = 1` (input.gms:41)**. ✓
- **`s60_bioenergy_2nd_price = 0` "config/default.cfg"**: confirmed at `default.cfg:2110` (also `input.gms:40`). The answer's claim that this zeroes `i60_2ndgen_bioenergy_subsidy` post-baseline (so `vm_bioenergy_utility` for `kbe60` = 0 by default) is correct — `presolve.gms:54-55` scales the 2nd-gen subsidy by `s60_bioenergy_2nd_price`, which is 0. ✓
- **begr/betr ∈ `kcr`**: `modules/14_yields/managementcalib_aug19/sets.gms:23-26` (`kcr(kve)` list includes begr, betr). ✓ Hence cost sums over `kcr` include them.
- **begr/betr ∈ `k_notrade` (non-tradable)**: `modules/21_trade/selfsuff_reduced/sets.gms:12` (`/ oilpalm, foddr, pasture, res_cereals, res_fibrous, res_nonfibrous,begr,betr /`), rationale at sets.gms:16 (`* begr and betr are not traded because biomass is traded in REMIND`). ✓
- **`q21_trade_glo(k_trade)` (12-14)** exact; **`q21_notrade(h2,k_notrade)` (18-19)** exists. equations.gms:12-19. ✓
- **`q16_supply_crops` (19-29)** with `vm_dem_bioen(i2,kcr)` at line 25; **`q16_supply_residues` (51-58)** with `vm_dem_bioen(i2,kres)`. ✓ exact. `vm_supply(i,kall)` decl declarations.gms:11. ✓
- **`q17_prod_reg(i2,k)` (10-11)**: `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))`. ✓ exact.
- **`q30_prod(j2,kcr)` (14-15)**: `vm_prod(j2,kcr) =e= sum(w, vm_area(j2,kcr,w)*vm_yld(j2,kcr,w))`. ✓ exact. `q30_rotation_max`/`q30_rotation_min` (34, 42) exist. ✓ `q30_betr_missing` (21-23) correctly flagged in §10 as a special betr land-target/penalty rule.
- **`q14_yield_crop(j2,kcr,w)` (14-16)**: `vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) * vm_tau(j2,"crop") / sum((cell(i2,j2),supreg(h2,i2)),fm_tau1995(h2))`. ✓ exact.
- **`q38_cost_prod_labor(i2)` (15-17)**: `vm_cost_prod_crop(i2,"labor") =e= sum(kcr, vm_prod_reg(i2,kcr)*sum(ct, p38_labor_need(ct,i2,kcr)*...))`. ✓ structure exact; `vm_cost_prod_crop` correctly attributed to M38.
- **`q11_cost_glo` (10)**: `vm_cost_glo =e= sum(i2, v11_cost_reg(i2))`. ✓ exact. **`q11_cost_reg(i2)` (15-47)**: range correct; all five §8.3 table terms present and correctly module-attributed — crop factor costs (line 15), land conversion `vm_cost_landcon` (line 20, M39), tech `vm_tech_cost` (line 22, M13), transport `vm_cost_transp` (line 21, M40), `vm_bioenergy_utility` (line 38, M60). ✓

The entire demand→supply→trade→production→land→yield→cost spine is correct, with correct variables, equations, default realizations, and (mostly) correct citations.

---

### Bugs Found

#### Q1-B1 — minimum-demand-floor citation drift (inherited from doc)
- **Severity**: Major  (`tier_uncertainty: true` — mechanism is described correctly; only the line citation is wrong and the harm is bounded)
- **Class**: 10 (Stale file:line citation)
- **Trigger**: §1 Major — "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different (citation drift to wrong content)."
- **Claim in answer** (§3.1): "A minimum demand floor `s60_2ndgen_bioenergy_dem_min = 1` (mio. GJ/yr, `input.gms:41`) is enforced per region in **`presolve.gms:56-57`** to prevent numerical degeneration."
- **Reality in code**: In develop, the demand floor is at **`presolve.gms:64`**: `i60_bioenergy_dem(t,i)$(i60_bioenergy_dem(t,i) < s60_2ndgen_bioenergy_dem_min) = s60_2ndgen_bioenergy_dem_min;`. Lines 56-57 hold materially different content — the 2nd-gen subsidy lin-interpolation (`$else` price block): line 56 `i60_2ndgen_bioenergy_subsidy(t) = s60_bioenergy_2nd_price / (2100 - sm_fix_SSP2) * (m_year(t) - sm_fix_SSP2);`, line 57 `);`. (`s60_2ndgen_bioenergy_dem_min = 1` value and `input.gms:41` are both correct.)
- **File evidence**: `/tmp/magpie-develop-r28/modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:54-57` (subsidy interpolation) vs `:64` (demand floor). presolve.gms is 65 lines total.
- **Root cause**: `doc_error` — the answerer inherited the wrong citation verbatim from `module_60.md` (see latent doc bug LDB-1). The answer did NOT beat the doc here; it reproduced the error, so the penalty applies to the answer.
- **Anchor reference**: R20 citation-drift anchor (line numbers drifted 5-20 lines to different content → Major). This is a 7-line drift onto materially different content.

#### Q1-B2 — q21_notrade balancing level: "regional" stated, code is superregional
- **Severity**: Minor  (`tier_uncertainty: true`)
- **Class**: 4 (Conceptual imprecision) / framing
- **Trigger**: §1 Minor — "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding." (A reader who opens `q21_notrade` immediately sees the `supreg` sum.)
- **Claim in answer** (§5, §9): "`q21_notrade` ... requires **each region** to produce at least as much as its own demand for non-tradable goods. The domestic constraint is effectively: **regional** production of `begr`/`betr` >= **regional** supply requirement" / flow box: "begr/betr non-tradable: each region self-sufficient ... forces vm_prod_reg(i,begr) >= regional requirement".
- **Reality in code**: `q21_notrade(h2,k_notrade)` balances at the **super-region** `h2` level: `sum(supreg(h2,i2),vm_prod_reg(i2,k_notrade)) =g= sum(supreg(h2,i2), vm_supply(i2,k_notrade))` — production may be reallocated among regions within a super-region, so it is NOT strictly per-region self-sufficiency.
- **File evidence**: `/tmp/magpie-develop-r28/modules/21_trade/selfsuff_reduced/equations.gms:18-19`.
- **Root cause**: `ambiguous` — partly induced by doc framing (`module_21.md:125` "Enforces regional self-sufficiency for non-tradable commodities" and :127 "8 commodities in k_notrade"); `module_21.md:119-123` does carry the correct superregional formula and the gloss "Superregional production ≥ superregional supply", so the doc is not strictly wrong, just loosely worded. The answer over-collapsed it to "region".

#### Non-bug noted (no score impact)
- §2 presents `begr, betr  - Bioenergy (biomass traded in REMIND, not MAgPIE)` as a quote attributed to `sets.gms:11-21`. That exact string is the editorial gloss in `module_21.md:67`, not the code comment (code at sets.gms:16 reads `* begr and betr are not traded because biomass is traded in REMIND`). Not scored: the cited range (11-21) DOES contain both the begr/betr membership (line 12) and the REMIND rationale (line 16), and the substance is correct. Informational at most.

---

### Latent Doc Bugs (recorded per rubric §1.5; fix this session; do NOT change answer score)

#### LDB-1 — module_60.md cites the minimum-demand floor (and the whole presolve back-half) at stale lines
- **Severity (future-reader harm)**: Major (citation drift; bounded harm — the quoted code block is correct, only line numbers are stale).
- **Doc lines**: `magpie-agent/modules/module_60.md:516` (`### Minimum Demand Floor (`presolve.gms:56-57`)`), repeated at `:864` (`**Conditional Override** (`presolve.gms:56-57`)`) and `:890` (`- Enforce minimum demand floor (`presolve.gms:56-57`)`).
- **Contradicting code**: floor is at `/tmp/magpie-develop-r28/modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:64`.
- **Corrected text**: change `presolve.gms:56-57` → `presolve.gms:64` at doc lines 516, 864, 890.
- **Related drift (same root, fix together)**: the doc's other presolve back-half citations are also ~6-8 lines low vs develop:
  - `module_60.md:465` "Enforcement (`presolve.gms:52-54`)" and `:889` "Enforce 1st generation subsidy floor (`presolve.gms:52-54`)" → actual 1st-gen subsidy floor is **presolve.gms:60-61**.
  - `module_60.md:194` energy-based subsidy "(`presolve.gms:33-34, 40-41, 47-48`)" → develop has the three price-implementation blocks at exp `38-41`, const `45-48`, lin (`$else`) `51-56`; the lin pair the answer relied on for §8.2 is `presolve.gms:54-55`. (Verify each against develop when fixing; the doc was last verified 2025-10-13 and presolve.gms has grown since.)
- **Note**: This is the root cause of answer bug Q1-B1. Because the answerer reproduced (did not beat) the error, Q1-B1 already carries the score penalty with root_cause=doc_error; LDB-1 is the mandated doc fix, not an additional `doc_error_answerer_beat_it`.

---

### Missing Nuances (not scored)
- §7 says betr/begr are "subject to the same land allocation logic as any other crop." Mostly true, but betr additionally carries a special target/penalty via `q30_betr_missing` / `vm_rotation_penalty` (`modules/30_croparea/simple_apr24/equations.gms:21-27`). The answer does flag `q30_betr_missing` in §10, so this is acknowledged rather than missed.
- The answer correctly notes (§8.2) the default 2nd-gen subsidy is zero, so under default config the cost-objective effect of 2nd-gen bioenergy is dominated by induced production/land/factor/transport costs, with `vm_bioenergy_utility` contributing only the 1st-gen floor subsidy for oils/ethanol. Good.

---

### Summary
The answer is a strong, well-sourced end-to-end trace. The default realization of M60 and every cross-module default realization are correct; all named variables and equations exist with the right prefixes and correct module attribution; and the bulk of file:line citations land exactly on the cited content (verified against develop ee98739fd). Two defects: (Q1-B1, Major) the minimum-demand-floor citation `presolve.gms:56-57` is stale — develop has it at line 64, and 56-57 holds the 2nd-gen subsidy interpolation; this was inherited from a stale `module_60.md` (LDB-1), so root cause is the doc. (Q1-B2, Minor) `q21_notrade` is described as per-region self-sufficiency when it actually balances at the super-region `h2` level. The substance of the trace — including the begr/betr non-tradable + regional-demand-level consistency argument, the `q60_bioenergy` mass-energy conversion, and the q11 cost assembly — is correct.

**Score** = max(0, 10 − [4·0 + 2·1(Major) + 1·1(Minor)]) = **7/10**.

doc_quality note: Q1's only Major bug roots in a doc error (not pure answerer confabulation), so Q1 stays IN the round's `doc_quality_mean` per rubric §4.
