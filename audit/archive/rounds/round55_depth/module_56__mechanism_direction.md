# Round 55 Depth Audit — module_56.md — lens: mechanism_direction

Target: `modules/module_56.md` (realization `price_aug22`, the only realization — confirmed `ls modules/56_ghg_policy/` shows only `price_aug22` + `input`).
Ground truth: `/private/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`.

## Verdict
The doc is unusually accurate. All 13 default switches, 7 equations, and the interface-variable
attributions (via `depth_rolemap.json` + both-endpoints grep) check out. Two findings survive.

---

## BUG 1 (Major) — mechanism / data_flow_direction: module 52 (LULUCF CO2) is falsely listed as a `vm_emissions_reg` source feeding module 56's annual emission pricing

**Doc quote (module_56.md:66, under Section 2.1 = the ANNUAL pricing equation `q56_emis_pricing`):**
> "**vm_emissions_reg(i,emis_annual,pollutants)**: Actual regional emissions from the emission modules (51 N2O, **52 LULUCF CO2**, 53 CH4, 58 peatland) (Tg/yr)"

Same misattribution recurs at module_56.md:591, :716, :1026, :1068, :1076 ("56 receives / prices emissions from 51 N2O, **52 LULUCF CO2**, 53 CH4, 58 peatland via `vm_emissions_reg`").

**Reality in code (parallel-not-serial; per-slice ownership):**
- `q56_emis_pricing` reads `vm_emissions_reg` ONLY over the `emis_annual` slice:
  `modules/56_ghg_policy/price_aug22/equations.gms:15-17` →
  `v56_emis_pricing(i2,emis_annual,pollutants) =e= vm_emissions_reg(i2,emis_annual,pollutants);`
- Module 52 populates `vm_emissions_reg` ONLY for the `emis_oneoff` × `co2_c` slice:
  `modules/52_carbon/normal_dec17/equations.gms:16-19` (`q52_emis_co2_actual` →
  `vm_emissions_reg(i2,emis_oneoff,"co2_c")`).
- `emis_annual` and `emis_oneoff` are DISJOINT sets (`core/sets.gms:314` emis_oneoff = carbon-pool
  sources; `core/sets.gms:320` emis_annual = {inorg_fert, man_crop, awms, resid, man_past, som, rice,
  ent_ferm, resid_burn, peatland}). Intersection = ∅.
- Therefore module 52 contributes NOTHING to the `emis_annual` read. The annual-pricing sources are
  51 (N pollutants — `modules/51_nitrogen/rescaled_jan21/equations.gms:23,31,43,50,56,66,75`),
  53 (CH4 — `modules/53_methane/ipcc2006_aug22/equations.gms:22,49,60,71`),
  58 (peatland — `modules/58_peatland/v2/equations.gms:92`).
- Module 56 prices LULUCF CO2 via its OWN carbon-stock difference in `q56_emis_pricing_co2`
  (`equations.gms:19-22`), reading `vm_carbon_stock`/`pcm_carbon_stock` directly — PARALLEL to module
  52's `q52_emis_co2_actual`, which reads the same `vm_carbon_stock` independently. Neither hands off
  to the other. The doc's own Section 2.2 (module_56.md:88-92) states this correctly
  ("calculated directly from vm_carbon_stock, intentionally bypassing vm_emissions_reg"), so line 66
  and the interface summaries contradict the doc's own architectural note.
- The two figures even DIFFER: 52 uses stockType `"actual"`; 56 uses `"%c56_carbon_stock_pricing%"`
  = `actualNoAcEst` (default). `realization.gms:13-14` and `preloop`/config confirm. So "56 prices 52's
  emissions" is doubly wrong — different slice AND different quantity.

Caveat (kept for precision, does not rescue the claim): 56's `postsolve.gms:27` dumps the full
`vm_emissions_reg.l` (incl. 52's co2 slice) to the reporting parameter `ov_emissions_reg`. That is a
reporting passthrough, not economic consumption — the doc's claim is about pricing/coupling.

**verify_cmd (results inline):**
- `rg -n "vm_emissions_reg" modules/56_ghg_policy/price_aug22/equations.gms` → only line 17 reads it,
  indexed `(i2,emis_annual,pollutants)`.
- `sed -n '16,19p' modules/52_carbon/normal_dec17/equations.gms` → `vm_emissions_reg(i2,emis_oneoff,"co2_c")` only.
- `sed -n '314,323p' core/sets.gms` → emis_oneoff (carbon pools) vs emis_annual (10 non-pool sources), disjoint.
- Positive control: `rg "vm_emissions_reg\(.*=e=" modules/51_nitrogen/... modules/53_methane/... modules/58_peatland/...`
  confirms 51/53/58 DO populate annual slices 56 reads.

**confirmed:** true

**proposed_fix:** In Section 2.1 (line 66) and the recurring lists (lines 591, 716, 1026, 1068, 1076),
split the attribution: the `emis_annual` `vm_emissions_reg` pricing input comes from **51 (N), 53 (CH4),
58 (peatland)** only. Module **52 (LULUCF CO2) is NOT consumed by module 56's pricing** — 52 computes the
"actual" LULUCF CO2 for reporting, while 56 computes its own priced LULUCF CO2 (`q56_emis_pricing_co2`,
stockType `actualNoAcEst`) directly from `vm_carbon_stock`, in parallel with 52. This is exactly the
distinction the doc already draws in Section 2.2; make the interface summaries consistent with it.

---

## BUG 2 (Minor) — formula: annuity worked example is internally inconsistent by 10×

**Doc quote (module_56.md:199-204):**
> "- Deforestation emits 100 Tg C over 10 years (10 Tg C/yr)
>  - C price = $100/tC, interest rate = 5%
>  - Annual cost = 10 Tg/yr × 10 yr × $100/tC × 0.05/1.05 ≈ **$4,762/yr**
>  - This equals the annual payment on a **$100,000 perpetuity** at 5% interest"

**Reality:** With the stated inputs the expression evaluates to 10 × 10 × 100 × (0.05/1.05) = **476.19**,
on a principal of emis×timestep×price = **$10,000** (annuity-due payment 10,000 × 0.05/1.05 = 476.19).
The doc's "$4,762/yr" and "$100,000 perpetuity" are each 10× too large (they correspond to a $100,000
principal, not the $10,000 the inputs imply). The formula STRUCTURE
(`× m_timestep_length × price × r/(1+r)`, `equations.gms:45-52`) is correct; only the worked number is off.

**verify_cmd:** `python3 -c "r=0.05;print(10*10*100*r/(1+r), 100000*r/(1+r))"` → `476.19 4761.9`.

**confirmed:** true (arithmetic reproducible)

**proposed_fix:** Change "≈ $4,762/yr" → "≈ $476/yr" and "$100,000 perpetuity" → "$10,000 perpetuity"
(or scale inputs up 10×). Since these are toy units, either fix restores internal consistency.

---

## Verified-correct (spot list, so misses are visible)
- Defaults all correct: c56_pollutant_prices=R34M410-SSP2-NPi2025 (cfg:1731), c56_emis_policy=reddnatveg_nosoil
  (cfg:1828, input.gms:86), c56_carbon_stock_pricing=actualNoAcEst (cfg:1835, input.gms:90),
  c56_cprice_aff=secdforest_vegc (cfg:1772), c56_mute_ghgprices_until=y2030 (cfg:1744),
  s56_c_price_induced_aff=1 (input.gms:69), s56_buffer_aff=0.5 (input.gms:71), s56_c_price_exp_aff=50
  (input.gms:70), s56_ghgprice_devstate_scaling=0 (input.gms:68), s56_ghgprice_fader=0 (input.gms:75),
  s56_cprice_red_factor=1 (input.gms:66), s56_minimum_cprice=3.67 (input.gms:67),
  s56_limit_ch4_n2o_price=4920 (input.gms:65).
- Set counts: 44 emission policies (scen56, sets.gms:119-163), 102 price scenarios ("100+", ghgscen56
  sets.gms:15-117), 16 pollutants_all (sets.gms:171-185), 31 emis_source (core/sets.gms:302-312).
  "44 × 16 × 31" matrix dims correct.
- Interface attributions all correct vs role map + both-endpoints grep:
  vm_carbon_stock populated by 29/31/32/34/35/59 (NOT 30 directly — 30→vm_carbon_stock_croparea→29,
  NOT 58), doc line 584 accurate (more accurate than module.gms's stale @description which lists 30 not 29/59).
  vm_reward_cdr_aff negative in module 11 (`11_costs/default/equations.gms:27`).
  vm_emission_costs read post-solve by 15 (`15_food/anthro_iso_jun22/intersolve.gms:23`, .l for tax recycling) — direction correct.
  im_pollutant_prices read by 57 (`57_maccs/on_aug22/preloop.gms:24-25`).
  pcm_carbon_stock ag-pools carried by 56 (`postsolve.gms:8`), soilc by 59 (`59_som/cellpool_jan23/postsolve.gms:13`).
  57 reads (does not populate) vm_emissions_reg — correct.
- Section 2.2 "direct carbon stock pathway / bypasses vm_emissions_reg" — CORRECT (this is why Bug 1's
  interface summaries are self-contradictory).
- CDR reward equation, buffer, discounting, ac.off, annuity factor, sign convention — all match code.

## Deferred (could not verify / not flagged)
- Detailed `f56_emis_policy` set-membership for reddnatveg_nosoil / redd+natveg_nosoil (module_56.md:499,
  662, 663, 666): the CSV `modules/56_ghg_policy/input/f56_emis_policy.csv` is a runtime input (only a
  `files` manifest present in develop) — cannot verify the exact 0/1 pattern here. The claims are
  CONSISTENT with the config comment (default.cfg:1770-1772) that secdforest_vegc is priced under
  reddnatveg_nosoil, but not independently confirmable offline.
- "Dependency Chains → Depends on: Modules 52, 53, 51" (module_56.md:1139): incomplete vs code (56 also
  depends on 58 peatland, 32 forestry vm_cdr_aff, 12 pm_interest, and the carbon-stock land modules), and
  mislabels 52 as "(carbon stocks)". But this block reads as a curated centrality annotation, not an
  exhaustive list, and the doc's own Key Dependencies (line 1076) is complete — deferred to avoid a
  marginal false positive. Worth a maintainer glance.
- Stage 6 snippet (module_56.md:455-456) shows only ch4 + n2o_n_direct caps; code also caps
  n2o_n_indirect (preloop.gms:82). Abbreviated snippet, not a false claim — not flagged.
- "Total Lines of Code: 709" (module_56.md:4) — not independently recounted; non-load-bearing.
