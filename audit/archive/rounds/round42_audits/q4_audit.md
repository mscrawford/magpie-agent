# Audit Report: Q4 (Water Module Infeasibility + Environmental Flow Requirements)

**Round**: 42 | **Auditor**: Opus | **Date**: 2026-06-03
**Ground truth**: develop @ ee98739fd (clean), live GAMS read this session.
**Answer audited**: `audit/archive/rounds/round42_answers/q4_answer.md`

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

This is an exceptionally accurate answer. Every load-bearing claim — default realizations, the `q43_water` constraint and its `=l=` type, the `vm_watdem.fx("ecosystem",j)` EFR fix, the 1.01 fossil-groundwater infeasibility buffer, the asymmetry between exogenous-fixed sectors and endogenous agriculture, and the M44-has-no-direct-water-pathway claim — was verified against the actual `.gms` files and confirmed correct, frequently to the exact line. No invented variables, no invented equations, no wrong defaults, no wrong realizations.

---

## Mechanical Checks (M1–M6)

| Check | Result | Evidence |
|---|---|---|
| **M1** File:line citations present | ✅ PASS | `equations.gms:10-11`, `presolve.gms:14-16`, `presolve.gms:87-88`, `equations.gms:13-17/22-23/28-29`, many more |
| **M2** Active realization stated | ✅ PASS | States M43 `total_water_aug13` (only realization), M42 `all_sectors_aug13` (confirmed default), M44 `bii_target` (confirmed default); all three cross-checked against `config/default.cfg` |
| **M3** Variable prefixes valid | ✅ PASS | `vm_watdem`, `v43_watavail`, `i42_env_flows`, `ic42_env_flow_policy`, `v44_bii_missing`, `vm_cost_bv_loss`, `vm_bv`, `p42_efp_fader` — all prefixes correct and match declarations |
| **M4** Epistemic badges present | ✅ PASS | 🟡 Documented tags throughout (docs-only mode declared up front) |
| **M5** Confidence tier matches depth | ✅ PASS | Consistently 🟡 (documented), honestly stating no `.gms` opened this session — correct for docs-only mode |
| **M6** Closing source statement | ✅ PASS | Full source statement + per-module realization confirmations + line-number-drift caveat |

All 6 mechanical checks pass.

---

## Verified Claims (correct)

### (a) Default realization + EFR
- **M43 default `total_water_aug13`, only realization**: ✅ `ls modules/43_water_availability/` shows only `total_water_aug13/` (+ `input/`); `config/default.cfg` → `cfg$gms$water_availability <- "total_water_aug13"`.
- **`v43_watavail(wat_src,j)` declared as variable, fixed in presolve**: ✅ declarations.gms:13 (`variables v43_watavail(wat_src,j)`); presolve.gms:8-11 fixes all four sources via `.fx` to `im_wat_avail(t,...,j)`. Exact match to answer's quoted block.
- **Only "surface" active; ground/ren_ground/technical zeroed in preloop**: ✅ preloop.gms:8-12 — `im_wat_avail(t,"surface",j)=f43_wat_avail(t,j)`, the other three `= 0`. Exact match (answer cited preloop.gms:8-12 correctly).
- **EFR = "ecosystem" slot of `vm_watdem`, `.fx`-fixed**: ✅ M42 presolve.gms:87-88:
  ```
  vm_watdem.fx("ecosystem",j) = sum(cell(i,j), i42_env_flows_base(t,j) * (1 - ic42_env_flow_policy(i)) +
                                               i42_env_flows(t,j) * ic42_env_flow_policy(i));
  ```
  The answer reproduces this fix verbatim (with the blend `i42_env_flows_base*(1-policy) + i42_env_flows*policy`) and cites presolve.gms:87-88 — **exact line match**.
- **"ecosystem" is a real `wat_dem` set member**: ✅ `core/sets.gms:247` — `wat_dem ... / agriculture, domestic, manufacturing, electricity, ecosystem /`.
- **`i42_env_flows` (Smakhtin/full) and `i42_env_flows_base` (5% base) parameter names**: ✅ both real; `i42_env_flows_base(t,j) = s42_env_flow_base_fraction * sum(wat_src, im_wat_avail(...))` (presolve.gms:58). Answer's "Base EFR = 5% × available water" is exactly this.
- **`i42_env_flows` from `lpj_envflow_grper.cs2`, Smakhtin 2004**: ✅ input.gms:111-114 (`f42_env_flows ... lpj_envflow_grper.cs2`, description "from LPJ and Smakhtin algorithm"); preloop.gms:9 maps `i42_env_flows(t,j)=f42_env_flows(t,j)`.
- **Parameter defaults table** — every value verified against M42 input.gms:
  - `s42_env_flow_scenario = 2` (Smakhtin) ✅ input.gms:22
  - `s42_env_flow_base_fraction = 0.05` ✅ input.gms:37
  - `s42_env_flow_fraction = 0.20` (answer wrote 0.20; code `/ 0.2 /`) ✅ input.gms:38
  - `c42_env_flow_policy = "off"` ✅ input.gms:122 (`$setglobal c42_env_flow_policy off`)
  - `s42_efp_startyear = 2025` ✅ input.gms:35
  - `s42_efp_targetyear = 2040` ✅ input.gms:36
- **EFP fader `m_linear_time_interpol(p42_efp_fader, s42_efp_startyear, s42_efp_targetyear, 0, 1)`**: ✅ preloop.gms:16 (answer cited preloop.gms:13-17 — the macro is on line 16; 13-17 is the EFP-trajectory comment+block; acceptable block citation, see Informational note).

### (b) Supply-demand constraint + buffer
- **`q43_water(j2)` at equations.gms:10-11, `=l=`**: ✅ EXACT:
  ```
  q43_water(j2) .. sum(wat_dem,vm_watdem(wat_dem,j2)) =l= sum(wat_src,v43_watavail(wat_src,j2));
  ```
  Matches the answer's stated form `Σ vm_watdem ≤ Σ v43_watavail` and the cited line range.
- **Cell-level, no inter-cell transfer, inequality, growing-period**: ✅ consistent with equation (per-`j2` constraint) and the @description block (equations.gms:13-20).
- **Exogenous sectors fixed via `.fx`; agriculture endogenous**: ✅ `watdem_exo = {domestic, manufacturing, electricity, ecosystem}` (sets.gms:9-10); `vm_watdem.fx(watdem_ineldo,j)` set by scenario (presolve.gms:41-52) and `vm_watdem.fx("ecosystem",j)` (presolve.gms:87-88); agriculture demand is determined by equation `q42_water_demand("agriculture",j)` (equations.gms:10-11) = `vm_watdem("agriculture",j)*v42_irrig_eff(j) =e= [water req]`, i.e. endogenous, NOT `.fx`. Answer's asymmetry claim is correct.
- **Infeasibility buffer = fossil-groundwater × 1.01 on watdem_exo in presolve; agriculture has none**: ✅ EXACT — presolve.gms:14-16:
  ```
  v43_watavail.fx("ground",j) = v43_watavail.up("ground",j)
       + (((sum(watdem_exo, vm_watdem.lo(watdem_exo,j))-sum(wat_src,v43_watavail.up(wat_src,j)))*1.01))
       $(sum(watdem_exo, vm_watdem.lo(watdem_exo,j))-sum(wat_src,v43_watavail.up(wat_src,j))>0);
  ```
  This is precisely the mechanism the round prompt flagged (R29 finding). The answer reproduces it verbatim, cites presolve.gms:14-16, correctly scopes it to `watdem_exo` only, correctly notes agriculture has no slack, and correctly interprets the added groundwater as unsustainable fossil extraction. Fully correct.
- **Diagnostic signals** (`oq43_water.marginal>0`, `ov43_watavail("ground",j).level>0`, `p80_modelstat=4/5`): ✅ `oq43_water(t,j,type)` and `ov43_watavail(t,wat_src,j,type)` are the real R-section output params (declarations.gms:22-23). Reading `.marginal`/`.level` off the GDX is the correct diagnostic approach. `p80_modelstat` is the standard M80 solver-status param.

### (c) M44 biodiversity interaction
- **M44 default `bii_target`** (NOT `bii_target_apr24`): ✅ `config/default.cfg` → `cfg$gms$biodiversity <- "bii_target"`. (Three realizations exist: `bii_target`, `bii_target_apr24`, `bv_btc_mar21`; answer correctly picks `bii_target`.)
- **M44 has NO direct water pathway; interaction is indirect via land/BII**: ✅ VERIFIED BOTH DIRECTIONS via `rg`:
  - No `vm_bv`/`v44_*`/`bii`/`biome44`/`vm_cost_bv_loss` anywhere in `modules/42_water_demand/` or `modules/43_water_availability/`.
  - No `vm_watdem`/`watavail`/`wat_dem`/`wat_src` anywhere in `modules/44_biodiversity/`.
  - `q43_water` references only `vm_watdem` and `v43_watavail`. Confirmed.
- **`v44_bii_missing` EXISTS and is a technical slack**: ✅ declarations.gms:13 (`positive variables ... v44_bii_missing(i,biome44)`); equations.gms:20 comment: "`v44_bii_missing` is a technical variable to maintain feasibility in case `v44_bii` cannot be increased." Answer's "technical slack variable that prevents hard infeasibility from BII targets; it has no water-balance analog" is exactly right. **Not invented.**
- **`q44_bii` at equations.gms:13-17**: ✅ `v44_bii(i2,biome44) =e= sum((cell,landcover44,potnatveg), vm_bv*i44_biome_share)/i44_biome_area_reg`. Matches.
- **`q44_bii_target` at equations.gms:22-23**: ✅ `v44_bii_missing(i2,biome44) =g= sum(ct,p44_bii_target(ct,i2,biome44)) - v44_bii(i2,biome44)`. Answer dropped the `sum(ct,...)` wrapper (see Informational note) but mechanism correct.
- **`q44_cost` at equations.gms:28-29, `s44_cost_bii_missing = 1e6`**: ✅ equations.gms:28-29 `sum(cell) vm_cost_bv_loss =e= sum(biome44, v44_bii_missing)*s44_cost_bii_missing`; input.gms:13 `s44_cost_bii_missing / 1e+06 /`. Answer's "$1,000,000/unit" correct.
- **`vm_bv` declared in M44, populated by land modules 29–35**: ✅ declared declarations.gms:11; the answer's "supplied by land-use modules 29, 30, 31, 32, 34, 35" matches the standard `vm_bv` populator set (consistent with G2-style producer/consumer reasoning; vm_bv appears in those land modules — not re-verified exhaustively here but the M44-side declaration is confirmed and the claim is the documented populator set).
- **`s44_bii_target` default 0 (target inactive by default)**: ✅ input.gms:9 `/ 0 /`. Answer framed the BII pathway conditionally ("if `s44_bii_target > 0`"), correctly implying it's off by default. Good capability-vs-default discipline.

---

## Bugs Found

**None at Minor or above.** Three Informational notes (do not affect score):

- **Q4-I1** — *Informational* — Class 10 (citation, trivial). The EFP fader macro `m_linear_time_interpol(p42_efp_fader, ...)` is on **preloop.gms:16**; the answer cites `preloop.gms:13-17`. Lines 13-17 are the "Trajectory for environmental flow policy" comment + the `p42_efp` setup block that contains the macro on line 16, so the range is defensible as a block citation. A careful reader lands on the right code. No misdirection.
- **Q4-I2** — *Informational* — Class 4 (structural simplification, mild). In `q44_bii_target` the answer wrote `v44_bii_missing >= p44_bii_target - v44_bii`, dropping the `sum(ct, ...)` collapse around `p44_bii_target(ct,i2,biome44)` (equations.gms:23). This is a single-element time-index sum on a presolve-interpolated target, not a set enumeration that misrepresents structure; the mechanism (slack ≥ target − achieved) is conveyed correctly. Tie-break DOWN from Minor → Informational. (Distinguished from the R16 set-sum-expansion Major anchor: that anchor *expanded* a multi-member land sum into a misleading enumeration; this merely omits a `ct` collapse, which does not mislead about how the equation reads.)
- **Q4-I3** — *Informational* — In the diagnostic table the output params are written as `oq43_water.marginal` and `ov43_watavail("ground",j).level` without the full `(t,j[,type])` indexing shown in declarations.gms:22-23. Informal but unambiguous; the indices appear correctly elsewhere in the answer.

`raw_severity_weighted = 4·0 + 2·0 + 1·0 + 0·3 = 0` → **score = 10 − 0 = 10**.

---

## Latent Doc Bugs (§1.5)

**None found.** The answer is docs-only and correct; I spot-checked the load-bearing doc-derived facts (the buffer formula, the ecosystem `.fx` fix, the `=l=` constraint, `v44_bii_missing` as slack, the M44↔water absence, all six M42 parameter defaults) directly against code and every one matched. There is no doc claim the answer leaned on that contradicts the code, so no `doc_error_answerer_beat_it` is recorded. The cited doc sections (module_42.md, module_43.md, module_44.md, water_balance_conservation.md, debugging_infeasibility.md) appear to be accurate on every fact reproduced here.

(Caveat: I verified the *facts the answer reproduced*, not every line of those doc files. The latent-bug mandate is about doc claims the answer *relied on*; those are clean.)

---

## Missing Nuances (non-scoring, optional improvements)

- **`watdem_ineldo` vs `watdem_exo`**: The answer treats all four exogenous sectors uniformly, which is correct for the buffer (`watdem_exo` = all four). Worth noting that the SSP-scenario fix in presolve.gms:41-52 uses the narrower `watdem_ineldo` = {domestic, manufacturing, electricity} (sets.gms:12-13) — ecosystem is fixed separately at presolve.gms:87-88. The answer's buffer scoping (`watdem_exo`, including ecosystem) is the one that matters and is correct; the ineldo/exo distinction is a refinement, not an error.
- **`v42_irrig_eff` divides agricultural demand**: The agriculture equation is `vm_watdem("agriculture",j) * v42_irrig_eff(j) =e= [water req]`, i.e. withdrawal = requirement / efficiency. The answer's point 4 ("irrigation efficiency too low → higher withdrawals") is directionally correct and consistent with this; could cite equations.gms:10-11 for the exact mechanism.
- The answer's "in practice" infeasibility list (SSP3 demands, EFP-on in arid cells, cc + irrigation expansion, low irrigation efficiency, hard cap) is well-reasoned and consistent with the code structure; these are plausible operational scenarios rather than code-stated facts, and the answer appropriately frames them as such.

---

## Summary

A model answer. The three priority traps the round flagged were all handled correctly:
1. **EFR representation** — correctly identified as the `"ecosystem"` slot of `vm_watdem`, `.fx`-fixed to a blend of `i42_env_flows_base` (5% floor) and `i42_env_flows` (Smakhtin), cited to the exact line (presolve.gms:87-88). "ecosystem" confirmed a real `wat_dem` member.
2. **Infeasibility buffer** — correctly identified as the 1.01 fossil-groundwater valve on `watdem_exo` in presolve.gms:14-16, with agriculture explicitly having no equivalent slack. Reproduced verbatim. This is exactly the R29 finding.
3. **M44 interaction** — correctly stated as NO direct water pathway (verified absent both directions via `rg`), indirect only via land/BII, with `v44_bii_missing` correctly cited as a real BII slack (declarations.gms:13), not invented.

No Critical/Major/Minor bugs; three Informational nitpicks. **Score: 10/10, ACCURATE.**
