# Audit Report: Q2 (Water supply/demand balance)

**Round**: R29
**Auditor**: Opus adversarial auditor
**Verification worktree**: `/tmp/magpie-develop-r29/` @ `ee98739fd` (origin/develop)
**Answer audited**: `audit/archive/rounds/round29_answers/q2_answer.md`

### Overall Verdict: MOSTLY ACCURATE (upper band)
### Accuracy Score: 8/10

The answer's load-bearing GAMS content — the inequality constraint, the supply/demand variables, the 5-sector / 4-source set membership, every cited equation, every cited default, and the infeasibility-buffer mechanism (the question's hardest part) — is verified **exact** against code. The two bugs are both citation-precision issues on a config-file line and a module.gms path; neither touches a substantive claim and both land within 2 lines / one directory level of content that confirms the same fact. No latent doc bug was propagated.

---

### Verified Claims (correct)

**Defaults / realizations**
- M42 default `all_sectors_aug13` — `config/default.cfg:1319` (`cfg$gms$water_demand<- "all_sectors_aug13"`). ✓ (realization name correct; line cited was 1317 — see Bug Q2-B1)
- M41 default `endo_apr13` — `config/default.cfg:1301`. ✓
- M43 `total_water_aug13` is the only realization — `ls modules/43_water_availability/` shows only `total_water_aug13` (+ `input/`). ✓

**Constraint type & equation**
- `q43_water(j2) .. sum(wat_dem,vm_watdem(wat_dem,j2)) =l= sum(wat_src,v43_watavail(wat_src,j2));` — `modules/43_water_availability/total_water_aug13/equations.gms:10-11`. ✓ EXACT (`=l=` inequality, answer's quote verbatim).
- "Only equation in Module 43" — `declarations.gms:17` equations block contains only `q43_water(j)`. ✓
- Inequality-vs-equality framing (water is a flow, surplus flows downstream) — consistent with realization.gms and standard MAgPIE semantics. ✓

**Supply variable**
- `v43_watavail(wat_src,j)` declared as a **variable** — `declarations.gms:13`. ✓ (Answer cited declarations.gms:9, which is the parameter `im_wat_avail`; the variable is at :13. Minor internal mis-cite, but the variable/type claim is correct and the answer separately lists `im_wat_avail` correctly in §7. Not scored — line is off by 4 but the named object and its type are right and the parameter it points at is a real, correctly-described object. Tie-breaker → not a bug, noted under Missing Nuances.)
- `wat_src` = {surface, ground, technical, ren_ground} (4 members) — `core/sets.gms:244`. ✓
- Only `surface` non-zero by default — `preloop.gms:8` sets surface = `f43_wat_avail`; `:10-12` set ground/ren_ground/technical = 0. ✓ EXACT (answer's snippet matches; "8-12" correctly spans the block, line 9 blank).
- All sources fixed in presolve via `.fx` — `presolve.gms:8-11`. ✓ EXACT.
- Variable-not-parameter "so the solver computes marginals/shadow prices" — standard MAgPIE rationale; mirrors cross_module doc lines 373-376. ✓ (defensible)
- Surface = LPJmL growing-period runoff, full annual runoff in dam cells, file `lpj_watavail_grper.cs2` — `realization.gms:9-38` + `input.gms:16,19`. ✓
- Climate scenario `cc` default; `nocc`/`nocc_hist` freeze at 1995 — `input.gms:9` (`$setglobal c43_watavail_scenario cc`); `config/default.cfg:1325`. ✓

**Demand variable & sectors**
- `vm_watdem(wat_dem,j)` positive variable — `modules/42_water_demand/all_sectors_aug13/declarations.gms:29`. ✓ EXACT.
- `wat_dem` = {agriculture, domestic, manufacturing, electricity, ecosystem} (5 members) — `core/sets.gms:247`. ✓ (Answer cited the module-level subset block sets.gms:9-13 in a multi-source line; the full parent set is core/sets.gms:247. Defensible — sets.gms:9-13 does define the exo/ineldo subsets. Not scored.)
- Agriculture endogenous via `q42_water_demand("agriculture",j2)` — `equations.gms:10-14`. ✓ EXACT (formula verbatim: `vm_watdem("agriculture",j2)*v42_irrig_eff(j2) =e= sum(kcr, vm_area...*ic42_wat_req_k) + sum(kli, vm_prod...*ic42_wat_req_k*v42_irrig_eff)`).
- Components: irrigated area × LPJmL crop water req + livestock × FAO water req, scaled by efficiency — matches eq:10-14 + realization.gms:15-19. ✓
- Manufacturing/electricity/domestic exogenous, fixed `.fx`, WATERGAP SSP2 by default — `presolve.gms:40-54` (ssp2 branch at :48 for `s42_watdem_nonagr_scenario=2`); WATERGAP source **confirmed in code**: `realization.gms:24` ("WATERGAP model provided by @wada_modeling_2016") + `input.gms:9` ("non agricultural water demand from WATERGAP"). ✓ EXACT. `watdem_ineldo` = {domestic, manufacturing, electricity} — `sets.gms:12-13`. ✓
- Ecosystem exogenous, `vm_watdem.fx("ecosystem",j) = sum(cell(i,j), i42_env_flows_base*(1-ic42_env_flow_policy) + i42_env_flows*ic42_env_flow_policy)` — `presolve.gms:87-88`. ✓ EXACT.
- `s42_env_flow_scenario=2` (LPJmL Smakhtin) default — `input.gms:22` (`/ 2 /`); `config/default.cfg:1380`. ✓
- `s42_env_flow_base_fraction=0.05` (5% base protection) — `input.gms:37`; `config/default.cfg:1391`. ✓
- EFP policy default `off` — `input.gms:122` (`$setglobal c42_env_flow_policy off`); `config/default.cfg:1352`. ✓
- EFP ramp 2025→2040 — `s42_efp_startyear /2025/` (input.gms:35), `s42_efp_targetyear /2040/` (input.gms:36). ✓
- `q42_water_cost` (pumping) active only when `s42_pumping=1`, default 0 — `equations.gms:16-17` + `input.gms:39` (`/ 0 /`) + presolve.gms:29 gate. ✓ EXACT.
- alt realization `agr_sector_aug13` keeps non-ag exogenous — `agr_sector_aug13/realization.gms:10` ("while other sectors are kept exogenous"); grep confirms `watdem_ineldo`/`manufacturing` present in agr_sector input/presolve/sets/declarations. ✓

**Infeasibility buffer (the hardest claim — fully verified)**
- Buffer code `v43_watavail.fx("ground",j) = v43_watavail.up("ground",j) + (((sum(watdem_exo,vm_watdem.lo(watdem_exo,j)) - sum(wat_src,v43_watavail.up(wat_src,j)))*1.01)) $(... > 0);` — `presolve.gms:14-16`. ✓ EXACT (answer's quote verbatim).
- Shortfall × 1.01 (1% margin), groundwater else zero — ✓ EXACT.
- Applies only to `watdem_exo` = {domestic, manufacturing, electricity, ecosystem} — `sets.gms:9-10`. ✓ EXACT.
- Agriculture has no buffer / bears all scarcity burden — correct corollary (`watdem_exo` excludes agriculture). ✓
- Zero cost, no depletion penalty, feasibility-only mechanism — `realization.gms:40-42` ("If exogenous non-agricultural water demand exceeds available water the missing amount is available from groundwater to avoid infeasibility"). ✓ EXACT (answer's §5 interpretation is directly supported).

**Module 41**
- `q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);` — `endo_apr13/equations.gms:10-11`. ✓ EXACT.
- `q41_cost_AEI(i2)` annuitized AEI cost — `equations.gms:19-23`. ✓ EXACT name + line range.
- `vm_AEI(j)` (declarations.gms:19), `vm_cost_AEI(i)` (declarations.gms:15). ✓ (answer's inventory names match).
- M41 does not enforce the water balance directly; indirect via vm_AEI → vm_area → vm_watdem → q43_water; stranded-asset limitation — consistent with module.gms:10-13 + cross_module §6.4. ✓

**Unused water**
- No reallocation/storage/inter-cell transfer; surplus flows away; per-cell independent — consistent with q43_water cell-indexed form + cross_module §4.2-4.3. ✓
- Slack diagnostics `oq43_water` level/marginal — `postsolve.gms:11,13` (`oq43_water(t,j,"marginal")=q43_water.m(j)`, `oq43_water(t,j,"level")=q43_water.l(j)`). ✓ (answer wrote informal `oq43_water.level`; the GAMS output param is `oq43_water(t,j,"level")` — notation shorthand, not a bug).

---

### Bugs Found

**Bug Q2-B1**
- **Severity**: Minor
- **Class**: 10 (Stale/wrong file:line citation)
- **Trigger matched**: §1 Minor — "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer**: "confirmed `config/default.cfg` line 1317: `cfg$gms$water_demand <- "all_sectors_aug13"`" (repeated in §Documentation Sources: "`config/default.cfg:1317`").
- **Reality in code**: The assignment `cfg$gms$water_demand<- "all_sectors_aug13"` is at **`config/default.cfg:1319`**. Line 1317 is a comment: `# * (all_sectors_aug13): manufacturing, electricity and domestic demand are`.
- **File evidence**: `config/default.cfg:1319` (assignment); `:1317` (comment describing the same realization).
- **Why Minor not Major**: The realization name claimed as default is **correct**; the drift is 2 lines onto an adjacent comment that names the same realization, so a reader is not misled about the default. Not a default-value error (which would be Critical/Major) — purely a citation-precision slip.

**Bug Q2-B2**
- **Severity**: Minor
- **Class**: 11 (Wrong GAMS filename/path)
- **Trigger matched**: §1 Minor — "Stale ... citation that's recoverable (correct concept, findable in a different location)." (Tie-breaker pulls down from Major: Class 11 tends Major, but content is findable at the correct path with the same line numbers.)
- **Claim in answer**: "Source: `modules/42_water_demand/all_sectors_aug13/module.gms:22-23`; `config/default.cfg:1317`" (§3, alternative-realization note).
- **Reality in code**: There is **no** `module.gms` inside the realization directory. `module.gms` lives at the module level: `modules/42_water_demand/module.gms`. Its lines 22-23 are the realization `$Ifi` includes that name `agr_sector_aug13` and `all_sectors_aug13` — i.e., the cited line numbers are coincidentally correct and the content (both realizations listed) matches the answer's point.
- **File evidence**: `modules/42_water_demand/module.gms:22-23` (`$Ifi "%water_demand%" == "agr_sector_aug13" ...` / `... "all_sectors_aug13" ...`); the realization dir has `realization.gms`, `sets.gms`, etc., but **no** `module.gms`.
- **Why Minor not Major**: Following the bad path yields file-not-found, but the file is one directory up with identical line numbers and confirming content. Recoverable; no wrong-concept propagation. (The same spurious-segment pattern would be Major if the content were absent or different at the real path — here it is not.)

---

### Latent Doc Bugs (§1.5) — none scored

Primary doc under test: `cross_module/water_balance_conservation.md` (+ `modules/module_42.md`, `module_43.md`). Read in full. Findings:

- **No load-bearing doc error the answer rested on.** Every substantive claim the answer makes (inequality, buffer at presolve.gms:14-16, `watdem_exo` membership, ×1.01, surface-only default, WATERGAP, EFP defaults, M41 stranded assets) is present in the cross_module doc AND verified correct against code. Doc and code agree.
- **Minor doc imprecision (NOT scored as latent bug, recorded for awareness)**: cross_module doc line 35 cites `equations.gms:17-18` and line 112 cites `equations.gms:19-20` as the "Verified" source for the 5 demand sectors / 4 water sources. Those lines are inside the `@description` **comment block** (equations.gms:13-20), not the canonical set definitions (`core/sets.gms:244,247`). The comment text does enumerate the sectors/sources, so the citation is defensible and the answerer did not propagate a wrong fact from it. Does not meet the §1.5 bar ("load-bearing doc claim ... WRONG versus code") — the claim (sector/source lists) is correct; only the citation target is a comment rather than the set file. No fix mandated; flagged only so a future maintainer may retarget these two citations to `core/sets.gms` for precision.
- module_42.md corroborates WATERGAP (lines 50-52, 141, 444-446), `s42_pumping=0` (line 385), and equation forms — all code-consistent.

---

### Mechanical Checks

| # | Check | Result |
|---|---|---|
| M1 | File:line citations present | ✓ PASS (dozens, e.g. equations.gms:10-11, presolve.gms:14-16) |
| M2 | Active realization stated | ✓ PASS (states `all_sectors_aug13` default for M42, notes M43 single-realization, M41 `endo_apr13`) |
| M3 | Variable prefixes valid | ✓ PASS (`vm_watdem`, `v43_watavail`, `vm_AEI`, `vm_cost_AEI`, `im_wat_avail`, `s42_*`, `c42_*` all valid per prefix table) |
| M4 | Epistemic hierarchy badges per claim | ⚠ PARTIAL — no inline 🟢/🟡 badges per claim; uses a single "Confidence: High" closing statement instead. (Informational; not separately scored — does not affect content accuracy.) |
| M5 | Confidence tier matches depth | ⚠ PARTIAL — same as M4; closing confidence statement is calibrated and honest about line-number drift risk. |
| M6 | Closing source statement | ✓ PASS (§Documentation Sources lists cross_module + module docs + config; closing "Confidence" note). |

M4/M5 are style-tier (Informational per §1.65 "Missing or malformed closing block"); the answer compensates with a per-section "Source:" line under nearly every claim, which is functionally stronger than badges. Not scored as a content bug.

---

### Missing Nuances

- §2 cites `declarations.gms:9` for the supply variable, but `:9` is the parameter `im_wat_avail`; the **variable** `v43_watavail` is declared at `declarations.gms:13`. The variable's name and type ("declared as a variable, not a parameter") are correct, and `im_wat_avail` is itself correctly described elsewhere (§7), so this is an internal line-target slip on a correct claim, below the bug bar (off-by-4 onto a real, correctly-named adjacent object). Worth tightening if the answer is reused.
- §3's framing that `agr_sector_aug13` has "simpler module structure" while `all_sectors_aug13` "explicitly models all five sectors" slightly understates that **both** realizations carry the non-ag sectors as exogenous; the real distinction is finer (e.g., reserved-fraction handling per default.cfg:1315-1316). The answer makes no false statement, but a reader could infer agr_sector omits non-ag sectors, which it does not. Borderline-informational; not scored.
- The answer does not explicitly note the **growing-period-only** scope of the water balance (cross_module §8.4) — a genuine caveat (MAgPIE water is growing-period, not annual). Omission, not error.

---

### Summary

A strong, code-faithful answer. The two scored bugs (Q2-B1 config line 1317→1319; Q2-B2 spurious `all_sectors_aug13/` segment in a `module.gms` path) are both Minor citation-precision slips that land within 2 lines / one directory of content confirming the same fact — neither would mislead a reader about the default, the equation, or the mechanism. Every load-bearing claim — the `=l=` inequality, `q43_water`, `vm_watdem`/`v43_watavail`, the 5 sectors (agriculture endogenous via `q42_water_demand`, four exogenous), surface-only supply by default, and especially the fossil-groundwater infeasibility buffer (`presolve.gms:14-16`, `watdem_exo` only, ×1.01, zero cost, no agricultural buffer) — is verified **exact**. No latent doc bug propagated; the cross_module doc is code-consistent on all load-bearing points. Score: 10 − 1 − 1 = **8/10**, MOSTLY ACCURATE (upper band).
