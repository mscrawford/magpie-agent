# High-centrality doc-centric audit sweep — magpie-agent — 2026-05-30

**Autonomous run** (user opted: fully autonomous, per plan). Adaptive test→sweep: Round 1 = 12 high-centrality hub modules; continue to sweep the remaining 23 un-audited modules **iff** Round 1 confirmed-doc-bug rate ≥ 2.0/doc OR ≥ 2 Critical. Doc-centric mode (no question-probes — the cap-resilient, high-yield config). Opus audits / Sonnet fixes. **NOTHING PUSHED** until user review.

Plan source: handoff plan "high-centrality doc-centric audit sweep" (executed after /clear).
Prior push: R30-R32 (2026-05-29 overnight) audited 30 docs, fixed 111 confirmed bugs (8C/55Ma/48Mi); committed + pushed to mscrawford/main (`ac06848`). Thesis — wrong consumer/populator sets + citation drift — held and was NOT exhausted. Only 11 of 46 module docs had ever been doc-centric-audited; this push tests the 12 highest-centrality of the remaining 35.

## Setup / preconditions (2026-05-30)
- Sleep guard: `caffeinate -dimsu -t 28800` (bg id bsxkd84db).
- Engine persisted (STEP 0): `audit/tools/doc_audit_round.workflow.js`, committed `bf06670`. (args-string JSON.parse + per-subagent .catch + disk-first all verified by read.)
- Develop worktree (verification truth): `/tmp/magpie_develop_ro` @ `ee98739fd`. **Develop has NOT advanced since R30-R32** (origin/develop still ee98739fd; module_32/21/14/56 dirs unchanged) → reused existing worktree; the plan's drift-risk framing for module_32/21 is moot (audit them as never-audited, not as drifted).
- magpie-agent start HEAD: `ac06848` (= origin/main, in sync) → `bf06670` after STEP 0.
- Lock: `/tmp/magpie_docpush2.lock`.

## Baseline gate (pre-run) — GREEN
- `validate_consistency.sh`: **0 errors**, 2 warnings (42 checks, 40 passed).
- `check_units.py` advisories (auditor leads): module_60:557 vm_dem_bioen; module_57:373 s57_step_length; module_12:868 pm_interest ('TC' = **known FP**, refuted last push); module_56:1031 vm_cdr_aff; module_39:578 vm_cost_landcon.
- `check_consumer_attribution.py` advisories: Pattern D (listed, no grep-hit) — module_16:568 vm_supply lists M18; module_52:4 pm_carbon_density_plantation_ac lists M35 + pm_carbon_density_secdforest_ac lists M32; module_52:291 (M35 = **confirmed FP** last push, co-located-name mode); module_35 (sweep target). D2 omission — module_16:568 vm_supply omits M70 (grep-hits in 70_livestock).

## Round 1 (R33) — high-centrality test (12 docs, doc-centric)
module_11, 14, 15, 16, 17, 29, 30, 32, 50, 52, 56, 70. Anchors: G1 (M14 default realization + equation list) + G2 (vm_carbon_stock M52 read / M56 declare+price chain).

| Round | docs | confirmed bugs (C/Ma/Mi) | edits | dropped | anchors | gate | commit |
|-------|------|--------------------------|-------|---------|---------|------|--------|
| R33 (Round 1) | 12 | **4C / 33Ma / 33Mi** (74 conf, +4 Info) | 204 | 0 | G1=9, G2=9, no drift | clean (0 err) | _local_ |

**R33 cap-probe: UNCAPPED** — max inter-message gap 1.85 min (<< 5 min), 3420 msgs / 29 agents / 40.7 min wall-clock (driven by large hub docs, not capping). 2.77M subagent tokens. Window has ample headroom.

**All 4 Criticals independently spot-checked vs develop — CONFIRMED:**
- module_16 `vm_supply`: equation-consumer = M21 only (phantoms M18/20/55/50/32/53 removed). ✓
- module_30 `vm_area`: 7 equation-consumers (18,29,41,42,50,53,59); phantom M17/M38 removed, M29 added; M32 correctly kept as a `.l/.lo` presolve reader (`32_forestry/dynamic_may24/presolve.gms:17`). ✓
- module_30 `vm_carbon_stock_croparea`: direct consumer = M29 only (false-direct M52/M56 removed). ✓
- _Near-miss / lesson:_ a paren-restricted `vm_area(` grep misses `.l/.lo` reads — I nearly flagged M32 as a phantom; broadening the pattern confirmed the read. Recorded in round33_record.json (extends [[bash-grep-r-unreliable-magpie]]).

**DECISION RULE: TRIGGERED** (6.17 confirmed bugs/doc ≫ 2.0; 4 Critical ≥ 2). Hypothesis confirmed hard — the dominant vein (wrong consumer/populator sets + citation drift) is pervasive in the high-centrality hubs, at a rate exceeding the prior push's ~3.7/doc. → Proceed to sweep the 23 remaining un-audited modules (pacing/scope per user steer, this session).

Anchors stable (G1=9, G2=9, no drift) → Round 1 fixes are trustworthy. Fixer discipline good (module_32 refused invalid 'affexp' option; several advisories correctly refuted).

## Engine enhancement (between rounds) — commit `231ac2e`
Per user steer (broaden toward quality + agent-performance), added an **adversarial consumer-set VERIFIER** to the engine (gated by `args.verify`): per doc, after the audit, an independent Opus verifier tries to REFUTE each confirmed consumer/populator/dependency-set finding before the fixer applies it (verdicts UPHELD / REFUTED / CORRECTED / NOT_CONSUMER_SET; fixer obeys — REFUTED→skip, CORRECTED→use corrected_set). Also hardened GREP_GUARD: grep BOTH `NAME(` AND `NAME.` (`.l/.lo/.up/.fx/.m` solution-level reads) before concluding consume/not-consume — root-cause fix for the R33 M32 near-miss. Syntax verified (async-wrapped node --check).

## Round 2 (R34) — sweep batch 1 (11 docs, HYBRID + VERIFY)
Highest-centrality first: module_21, 35, 38, 59, 31, 22, 60, 73, 71, 41, 42. Anchors: **G3** (magpie4 version pin) + **G4** (getReport dispatch) — overdue, rotated in. Mode = hybrid (re-adds question-probes for agent-Q&A performance) + verify (adversarial consumer-set refute pass).
**R34 run:** task `wjw4rvcys`, run `wf_d43cec53-75c`. Transcript dir (cap-probe): `.../subagents/workflows/wf_d43cec53-75c`. This is the **measured batch** — probe its token cost + max gap on completion, then size batch 2 (12 docs: 18,20,34,36,37,39,40,43,44,51,54,80) to glide under the rolling wall.
Sweep-doc leads fed: module_60:557 vm_dem_bioen unit (GJ→mio.tDM/yr); module_35:9/:917 consumer advisories (co-located-FP caveat); module_39:578 vm_cost_landcon unit (batch 2).

| Round | docs | confirmed bugs (C/Ma/Mi) | verify (refuted/corrected) | edits | dropped | anchors | gate | commit |
|-------|------|--------------------------|----------------------------|-------|---------|---------|------|--------|
| R34 (batch 1) | 11 → **3 done / 8 dropped** | m38: 0/1/0, m59: 0/1/4 (kept); m21 REVERTED (auditor regression) | verify: **never ran (cap)** | 7 kept | 8 | G3=10, G4=8 (**drift**) | clean (0 err; reverted m21) | _local_ |

**⚠️ R34 CAPPED — single ~2h rate-limit wait (max inter-message gap 123 min).** The hybrid+verify config (44 agents/11 docs) saturated the rolling 5h window on top of R33. 8 doc-audits dropped to null; the Verify phase never executed (adversarial verifier still UNTESTED). Survivors: module_38 (1 edit, pm_prod_init→M17, spot-checked) + module_59 (6 edits, vm_area producer→M30, spot-checked); module_21 auto-reverted by the gate (auditor regressed bilateral22 eq-count/feasibility-penalty — pre-round doc was correct). Anchors G3=10; G4=8 **drift** (agent confabulated 101 unique report* funcs vs correct 106 — agent-perf miss caught by the q-probe, not a doc bug).
**Binding constraint = 5h rolling RATE, not total budget.** Recovery: 8 dropped docs → fresh leaner round (doc-centric + verify, no q-probes), paced to glide under the rolling rate. Pacing under user discussion (cap hit at the window's edge, 12:30 CEST).

## Round 3 (R35) — recovery probe (4 docs, doc-centric + VERIFY) — CLEAN
User chose "lean + verify, small probe now." 4 consumer-set-rich dropped docs: module_35, 22, 31, 60. doc-centric (no q-probes) + adversarial verify; no anchors.

| Round | docs | confirmed bugs (C/Ma/Mi) | verify (upheld/corrected/refuted) | edits | dropped | gate | commit |
|-------|------|--------------------------|-----------------------------------|-------|---------|------|--------|
| R35 (probe) | 4 | **3C / 7Ma / 7Mi** (17 conf) | 8 / 1 / 0 (4 verified) | 32 | 0 | clean (0 err; self-healed 2 citations) | _local_ |

**Cap-probe: CLEAN** (max gap 1.45 min, 18 min, 0.98M tokens) → rolling window recovered, safe to continue.
**Verifier VALIDATED on first live run:** independently re-derived module_22 `pm_land_conservation` consumers = {M13,M29,M31,M32,M35}, M10 absent → matches a by-hand grep exactly. CORRECTED module_35 B2 (auditor had the right module M73→M32 but the wrong eq name; verifier → `q32_ndc_aff_limit`). 0 refuted (auditors right on consumer-sets this round). → Rely on the verify layer to scale consumer-set checking; periodic meta-checks only.
**Criticals (all validated):** module_22 ×2 (pm_land_conservation M10-phantom + M29/M13-omit, R20-anchor class); module_35 ×1 (age-class ac150→ac300/62-elem, R16-anchor class).
Correctly-refuted leads: module_60 `vm_dem_bioen` 'GJ' (doc right — the in-code `declarations.gms:14` 'GHJ' is the defect); module_35 M52/M22 phantoms.
Continuing the sweep at this lean config; re-probe each batch to glide under the rolling rate.

## Round 4 (R36) — sweep batch (8 docs, doc-centric + VERIFY) — CLEAN
4 R34-dropped (73, 71, 41, 42) + 4 new (18, 39, 44, 51).

| Round | docs | confirmed bugs (C/Ma/Mi) | verify (upheld/corrected/refuted) | edits | dropped | gate | commit |
|-------|------|--------------------------|-----------------------------------|-------|---------|------|--------|
| R36 | 8 | **3C / 13Ma / 17Mi** (33 conf) | 8 / 0 / 0 (8 verified) | 67 | 0 | clean (0 err; self-healed 8 citations) | _local_ |

**Cap-probe: CLEAN** (max gap 1.62 min, 30 min, 1.87M) → lean config sustainable at 8 docs.
**Criticals (verifier-upheld + meta-checked by hand):** module_18 ×2 (`vm_prod_reg(kres)` external consumer = M21-only via k_notrade `selfsuff_reduced/equations.gms:19`; 6 wrongly-listed modules read kcr/kap/kli_rum slices — slice-conflation; `vm_res_biomass_ag/bg` mislabeled Internal though M50 reads them); module_51 ×1 (`im_maccs_mitigation` declared M57 `on_aug22/declarations.gms:13`, doc said M56). Both confirmed against develop.
Recurring vein: **DECLARED-vs-POPULATED-vs-READ** producer/declaration errors (vm_prod_reg "from M70"→M17; im_maccs_mitigation "M56"→M57; vm_carbon_stock "M52"→M56). Refuted leads: module_73 R33-advisory (q73 populate — doc correct); module_51 "M51 reads vm_area" (that was M32).
**Sweep is the sustainable config.** R37 = final 8 (20,34,36,37,40,43,54,80) → then all 35 unaudited module docs covered.

## Round 5 (R37) — final sweep (8 docs, doc-centric + VERIFY) — CLEAN
20, 34, 36, 37, 40, 43, 54, 80. Completes the 35-module unaudited corpus.

| Round | docs | confirmed bugs (C/Ma/Mi) | verify (upheld/corr/refuted) | edits | dropped | gate | commit |
|-------|------|--------------------------|------------------------------|-------|---------|------|--------|
| R37 | 8 | **0C / 9Ma / 10Mi** (+2 Info) | 9 / 0 / 0 (8 verified) | 30 | 0 | clean (0 err, no self-heal) | `ed6324a` |

Cap-probe clean (1.48 min). 0 Critical — peripheral hubs (40,54,80,20) markedly cleaner than central. Residual vein = phantom cost edges (M36/M43/M54 → M11) + M34 omits M56 `vm_carbon_stock` reader (G2 class). Review flags: module_54 D3 populator advisory; module_37 M45 provenance re-label.

---

# FINAL VERDICT — high-centrality doc-centric sweep (R33-R37)

**Hypothesis CONFIRMED, hard.** All **35 previously-unaudited module docs** are now doc-centric-audited → the full 46-module corpus complete (with the 11 prior). Every audited hub carried bugs; the dominant vein is exactly **wrong consumer/populator sets + citation drift**, Critical-prone, and **centrality predicts density** (R33 central hubs: 4 Critical, 6.17 confirmed-bugs/doc; R37 peripheral: 0 Critical, ~2.6/doc).

**Tally (all local, pending review):**
- **151 confirmed doc bugs fixed** (10 Critical, 64 Major, 71 Minor, 6 Info) in **340 edits** across 34 docs (module_21 audited + correctly left unchanged after a gate-reverted auditor regression).
- Anchors G1=9, G2=9, G3=10 (no drift); **G4=8 DRIFT** — the agent confabulated "101 unique report* funcs" vs the correct 106 (agent-performance miss; helper is correct, no doc fix).
- Gate clean every round (0 errors); self-healed bare-path citations 3 rounds; 1 auditor regression auto-reverted (module_21).

**Engine upgrade (durable, committed `231ac2e`):** adversarial consumer-set **verifier** + `.l/.lo` solution-level grep rule. Record: **25 consumer-set findings upheld, 1 corrected, 0 false refutations** (R35-R37); hand-validated twice (pm_land_conservation; module_18/51 Criticals). It caught an auditor eq-name mislabel and re-derived every Critical's consumer set — it scales the by-hand verification.

**Cap event (R34):** heavy hybrid+verify (44 agents) saturated the 5h rolling rate → 2h wait, 8 docs dropped, recovered fully via lean doc-centric+verify (R35-R36), **zero completed work lost**. Lesson: the **5h rolling RATE** (not total budget) is the binding constraint; lean ~8-doc rounds at steady cadence is sustainable.

**Review-worthy items for the user:**
1. module_54 D3 populator advisory (vm_p_fert_costs / vm_nr_inorg_fert_costs list M18/M50 populators, no grep-hit — verify).
2. module_37 M45 provenance (verifier flagged: re-label, not delete).
3. G4 agent-confabulation drift (agent-Q&A signal, not a doc bug).
4. module_21 reverted to its (correct) pre-round state — confirm OK.

**State:** commit stack `ac06848..HEAD` on `main` = **8 commits, NOT pushed**. Lock removed; merge backup removed. Develop worktree `/tmp/magpie_develop_ro` left mounted for review (`git -C ../magpie worktree remove /tmp/magpie_develop_ro` when done). `validation_rounds.json` merged to 37 rounds (schema 1.4), round-trip validated, final gate 0 errors.

**Awaiting explicit go to push to mscrawford** (only mscrawford, never pik-piam).
