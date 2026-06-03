## Audit Report: Q2 (Feed Demand Cascade — Module 70 to Crop/Pasture Land)

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10

Verified against live GAMS code at develop HEAD `ee98739fd` (tracked code clean).

---

### TOP-PRIORITY FINDING (R3 Critical anchor — default feed-basket realization)

**`fbask_jan16` IS the verified default.** The answer is CORRECT and does NOT reproduce the R3 anchor bug.

Evidence:
```
config/default.cfg:2146:  cfg$gms$livestock <- "fbask_jan16"   # def = fbask_jan16
```
(Confirmed via fixed-string grep — exactly one match; line number 2146 exact.)
`ls modules/70_livestock/` → `fbask_jan16/` and `fbask_jan16_sticky/` only. The answer's alternative-realization name `fbask_jan16_sticky` is correct, and its characterization ("adds sticky capital-stock mechanism, does not change feed-basket structure, not the default") is accurate.

Note on the R3 anchor: the R3 Critical bug was the agent describing feed mechanics as if a NON-default realization were active. The R3 anchor text in the rubric (§1) references a `fbask_jan16` vs `fbask_jul23` flip; on the CURRENT develop tree there is no `fbask_jul23` realization and the default genuinely IS `fbask_jan16`. The answer matched current ground truth on both the directory listing and the config line. No cascade triggered.

---

### Verified Claims (correct)

**(a) Default realization + location**
- `cfg$gms$livestock <- "fbask_jan16"` at `config/default.cfg:2146` — EXACT (name + line). ✓
- Alternative `fbask_jan16_sticky` exists and is non-default. ✓

**(b) Feed-basket parameter + feed-demand variable**
- Working parameter `im_feed_baskets` — DECLARED `im_feed_baskets(t_all,i,kap,kall)` at `modules/70_livestock/fbask_jan16/declarations.gms:36`. Name correct. ✓ (dimension-label nuance below — not a bug)
- Raw input `f70_feed_baskets(t_all,i,kap,kall,feed_scen70)` — `modules/70_livestock/fbask_jan16/input.gms:36` (table). Set name `feed_scen70` correct. ✓
- Scenario slice selection in preloop (`%c70_feed_scen%`, historical ≤ `sm_fix_SSP2` forced to `"ssp2"`) — `preloop.gms:14-22`. ✓ Answer cited `c70_feed_scen` default `"ssp2"` → confirmed `config/default.cfg:2152: cfg$gms$c70_feed_scen <- "ssp2"`. ✓
- Interface variable `vm_dem_feed(i,kap,kall)` — DECLARED `declarations.gms:11`; DEFINED by `q70_feed`. ✓
- `q70_feed` formula (`equations.gms:17-20`):
  ```
  vm_dem_feed(i2,kap,kall) =g= vm_prod_reg(i2,kap)*sum(ct,im_feed_baskets(ct,i2,kap,kall)) + sum(ct,vm_feed_balanceflow(i2,kap,kall))
  ```
  Reproduced EXACTLY, including `=g=` (≥) constraint type and the balance-flow term. ✓
- "vm_dem_feed leaves M70 and enters M16 (Demand)" — corroborated by M16 consuming it (below) and module_70.md note. ✓

**(c) Routing to M30/M31 and M14 yield mediation**
- M16 (`sector_may15`, only realization) `q16_supply_crops(i2,kcr)` at `equations.gms:19-29` includes `+ sum(kap4, vm_dem_feed(i2,kap4,kcr))`. Snippet faithful. ✓
- `q16_supply_pasture(i2)` at `equations.gms:62-63`: `vm_supply(i2,"pasture") =e= sum(kap4, vm_dem_feed(i2,kap4,"pasture"))`. EXACT. Answer's claim "no food/seed/waste/balanceflow terms" — CORRECT (verified the full equation has only the feed term). ✓
- Circular dependency M70→M16→M21→M17→M70: verified. `vm_supply` (M16 output) is consumed in M21 trade equations; M21 constrains `vm_prod_reg ≥ vm_supply (± trade)`; `vm_prod_reg` is DEFINED in M17 `q17_prod_reg`: `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))` (`modules/17_production/flexreg_apr16/equations.gms:11`); `vm_prod_reg` feeds back into `q70_feed`. ✓
- M30 (`simple_apr24`, `config/default.cfg:896`) `q30_prod(j2,kcr)` at `equations.gms:14-15`: `vm_prod(j2,kcr) =e= sum(w, vm_area(j2,kcr,w) * vm_yld(j2,kcr,w))`. EXACT. ✓
- M31 (`endo_jun13`, `config/default.cfg:969`) `q31_prod(j2)` at `equations.gms:16-18`: `vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed")`. EXACT, including `=l=` (≤) constraint and `vm_land(j2,"past")`. ✓
- M14 (`managementcalib_aug19`, `config/default.cfg:354`) `q14_yield_crop(j2,kcr,w)` at `equations.gms:14-16`: matches answer's snippet exactly (`sum(ct,i14_yields_calib(...)) * vm_tau(j2,"crop") / sum((cell(i2,j2),supreg(h2,i2)), fm_tau1995(h2))`). ✓
- `q14_yield_past(j2,w)` at `equations.gms:35-39`: matches answer's snippet (`i14_yields_calib × sum(cell, pm_past_mngmnt_factor(ct,i2)) × (1 + s14_yld_past_switch*(... pcm_tau ... -1))`). ✓
- `s14_yld_past_switch` default `0.25` — `modules/14_yields/managementcalib_aug19/input.gms:20: / 0.25 /`. Answer's "default 0.25 = 25% spillover" CORRECT. ✓

**M70→M14 side channel (`pm_past_mngmnt_factor`) — SPECIAL SCRUTINY, fully verified, NOT confabulation**
- PRODUCER: `pm_past_mngmnt_factor(t,i)` is ASSIGNED only in M70 presolve — `modules/70_livestock/fbask_jan16/presolve.gms:64,66-67` (and the `fbask_jan16_sticky` twin). Open-paren/RHS sweep via `rg` confirms NO other module assigns it.
- DECLARED: `modules/70_livestock/fbask_jan16/declarations.gms:41: pm_past_mngmnt_factor(t,i) Regional pasture management intensification factor (1)`.
- CONSUMER (read-only): Module 14 only — `equations.gms:38` (`q14_yield_past`) and `nl_fix.gms:11`.
- The presolve header comment (`presolve.gms:23-26`) explicitly states the factor "is used to scale biophysical pasture yields in the module [14_yields]", and the M14 comment (`equations.gms:24-28`) reciprocally says it is computed "in module 70". The cattle-stock-proxy → intensification mechanism (`presolve.gms:32-68`) matches the answer's description. The answer's `(ct,i)` indexing matches how M14 reads the `(t,i)` parameter inside `sum(ct,...)`.
→ The "one direct M70→M14 interface" claim is GROUND-TRUTH CORRECT.

**Doc-claim cross-check (latent-doc-bug sweep, §1.5)**
Load-bearing doc claims the answer relied on were checked against code and are ACCURATE:
- `module_70.md:12-13` (default `fbask_jan16`, alt `fbask_jan16_sticky`) — matches config. ✓
- `module_70.md` q70_feed formula block — matches `equations.gms:17-20`. ✓
- `module_14.md:107-111` (`pm_past_mngmnt_factor(ct,i)` from M70; `s14_yld_past_switch` default 0.25, range 0-1; 25% interpretation) — matches code. ✓
- `module_16.md:190-200` (q16_supply_pasture) — matches `equations.gms:62-63`. ✓
**No `doc_error_answerer_beat_it` found.** Docs were correct; the answer did not have to beat any wrong doc.

---

### Mechanical Checks (M1–M6)

| Check | Result | Note |
|---|---|---|
| M1 file:line citations present | PASS | Every concrete claim carries a `realization/file.gms:NN` cite |
| M2 active realization stated | PASS | M70 fbask_jan16, M16 sector_may15, M30 simple_apr24, M31 endo_jun13, M14 managementcalib_aug19 — all named + matched to default with cfg line |
| M3 variable prefixes valid | PASS | `vm_*`, `im_*`, `pm_*`, `i14_*`, `s14_*`, `c70_*` all consistent with code |
| M4 epistemic badges present | PASS | 🟡 on documented claims throughout; appropriate given docs-only mode |
| M5 confidence tier matches depth | PASS | All claims 🟡 (documented); answer explicitly states no .gms read this session — correct self-labeling |
| M6 closing source statement | PASS | Closing block lists module docs + config with verification dates |

---

### Bugs Found

None at Minor or above.

**Non-scoring observation (Informational, not counted):** Part-(b)'s section header writes the parameter as `im_feed_baskets(ct,i,kap,kall)` and the prose later as `im_feed_baskets(t,i,kap,kall)`, whereas the DECLARED signature is `im_feed_baskets(t_all,i,kap,kall)` (`declarations.gms:36`). The `ct`/`t` forms reflect how the parameter is INDEXED inside `sum(ct,...)` in `q70_feed`, not its declared dimension. The parameter NAME is correct and a reader is not misled about what the parameter is. Per §1 tie-breaker (pull down), this is Informational — it does not affect the score.

**Non-scoring observation (Informational):** Step 2 says Module 21 "creates `vm_prod_reg`". Strictly, M17 DEFINES `vm_prod_reg` (`q17_prod_reg`, `flexreg_apr16/equations.gms:11`); M21 only CONSTRAINS it against `vm_supply`. The answer's Step 3 then correctly attributes the `vm_prod_reg` definition (`vm_prod → vm_prod_reg`) to M17, so the load-bearing attribution is right and the loose Step-2 verb does not mislead the overall chain. Not counted.

---

### Missing Nuances
- The answer omits that `vm_feed_balanceflow` for ruminant pasture is itself endogenized in some regions via `q70_feed_balanceflow` + `p70_endo_scavenging_flag` (`equations.gms:25-29`, `presolve.gms:14-20`) — i.e., the "negative scavenging adjustment" the answer mentions can be a decision variable, not just a fixed flow. This is a refinement, not an error; the question did not ask for the balance-flow internals.
- The answer does not mention that M30's `q30_prod` is one realization (`simple_apr24`) vs `detail_apr24`; it correctly named and cited the default, so this is complete for the question.

### Summary
A clean, fully accurate trace. The top-priority default-realization claim (`fbask_jan16` @ `config/default.cfg:2146`) is verified correct — the answer does NOT reproduce the R3 cascading-wrong-realization bug. All six equations (`q70_feed`, `q16_supply_crops`, `q16_supply_pasture`, `q30_prod`, `q31_prod`, `q14_yield_crop`, `q14_yield_past`) match the live code verbatim in name, formula, constraint type, and cited line range. All four interface objects (`im_feed_baskets`, `vm_dem_feed`, `vm_prod_reg`, `pm_past_mngmnt_factor`) are correctly named, dimensioned, and attributed. The specially-scrutinized M70→M14 side channel is real: `pm_past_mngmnt_factor` is produced solely in M70 presolve and read solely by M14 — verified by exhaustive assignment sweep. Load-bearing doc claims were cross-checked and are accurate (no latent doc bug). Two minor verb/dimension-label imprecisions are Informational and do not affect the score. **10/10.**
