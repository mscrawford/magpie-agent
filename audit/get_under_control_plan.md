# Plan: get the bomb rate under control + clean up the doc surface

**Created**: 2026-05-24 (post-R24 conversation)
**Status**: ☑ Phase 0 (2026-05-25)  ☑ Phase 1 (2026-05-25)  ☑ Phase 2 (2026-05-25)  ◐ Phase 3 (R25 done, R26 pending)  ☐ Phase 4
**Target completion (Phases 0-3)**: ~3-4 focused sessions over 1-2 weeks

## Executive summary

R24 surfaced two structural problems:

1. **Semantic bug-rate problem**: R24 mean 7.5/10 with two bombs (Q4 4/10, Q1 5/10), driven by uncovered validator classes (unit drift, prose consumer attribution, one-hop attribution) and known-fragile docs (M30/M80/M11) with deferred R3-era sweeps.

2. **Doc-surface drift problem**: while debugging R24, surfaced that AGENT.md is over Claude's size warning threshold, magpie4 is missing from the main workflow, `project/CURRENT_STATE.json` is 78 days stale despite being declared SSOT, four READMEs route to that stale SSOT, `reference/dependency_analysis/` is presented as living docs but is an Oct-2025 snapshot, ~10 `module_XX_notes.md` files are empty templates, and validation outputs land in the wrong directory.

This plan fixes both. **Phase 0** runs a multi-lens `/pipeline-audit R6` to find all instances of the doc-surface drift class (not whack-a-mole), then synthesizes fixes. **Phases 1-3** close the semantic bomb sources via mechanization + targeted sweeps + re-measure. **Phase 4** deploys prospective prevention (PR-time doc updates).

## Goal + success criteria

| Metric | Current (R24) | Target |
|--------|---------------|--------|
| Mean flywheel score | 7.5/10 | ≥8.5/10 sustained |
| Per-round bomb rate (≤5/10) | ~30% (2 of 6) | <10% |
| Validators covering R24-class bugs | ~50% | ≥80% |
| AGENT.md size | 46KB / 846 lines | <40KB / ~600 lines |
| Empty/stale doc files | ~15-20 (estimate) | 0 |
| PR-time drift prevention | manual only | 5c auto-runs on every MAgPIE PR merge |

Verification gates: R25 mean ≥8.0 (recover); R26 mean ≥8.5 (post-sweep stable); validator suite count grows from 40 → ~44 checks; quarterly mean ≥8.5 sustained once Phase 4 lands.

## Phase 0 — `/pipeline-audit R6: Stale-and-Remnant` (~6-8h, 1 session)

**Goal**: catalog and fix doc-surface drift in one synthetic pass, instead of whack-a-mole as new instances surface.

**Approach**: hybrid Sonnet/Opus. 7 parallel Sonnet lens agents scan the magpie-agent tree; 1 Opus synthesis call clusters findings into root causes; fixes go in as cluster-level interventions (R3 pattern: 62 findings → 7 clusters → 7 commits).

### Lens set

Each lens has at least one R24-found example pre-loaded as a calibration anchor.

| Lens | Question | R24 ground truth |
|------|----------|------------------|
| **L1: Staleness** | Files claiming currency but >60 days untouched | `CURRENT_STATE.json` (78 days, declared SSOT) |
| **L2: Dead conventions** | Rules documented in AGENT.md / READMEs that nobody follows in practice | "all updates go in CURRENT_STATE.json" |
| **L3: Half-deployed patterns** | Empty templates, stub scaffolds, "no X recorded yet" placeholders | ~10 empty `module_XX_notes.md` files |
| **L4: Cross-doc consistency** | Same fact stated differently across files (counts, paths, dates) | README "~290K words" vs AGENT.md "~342K words" |
| **L5: Misplaced outputs** | Files in wrong directories, `.gitignore` gaps | `/magpie/validation_report_*.txt` in parent repo root |
| **L6: Reference-graph integrity** | "X is authoritative" claims vs X's actual freshness | README → stale `CURRENT_STATE.json` |
| **L7: Surface bloat + workflow gaps** | Always-loaded docs over threshold; load-bearing layers missing from workflow sections | AGENT.md 46KB; magpie4 missing from MANDATORY WORKFLOW |

### Sequence

| Step | Effort | Output |
|------|--------|--------|
| 0a. Design lens prompts (1 per L1-L7) with R24 ground-truth examples baked in | 30min | `audit/pipeline_audit_round6_design.md` |
| 0b. Run 7 parallel Sonnet lens agents | ~45min wall | `audit/pipeline_audit_round6_raw_findings.md` |
| 0c. Optional: re-run L2 + L6 (judgment-heavy) with Opus on Sonnet-not-flagged docs | ~30min | Confidence check |
| 0d. Opus synthesis: cluster findings by root cause | 1h | Cluster table — likely 5-8 clusters |
| 0e. Per-cluster decisions (SSOT, archives, dependency_analysis, notes pattern, etc.) | 15min | Direction per cluster |
| 0f. Apply synthetic interventions | 3-5h | Commits |
| 0g. AGENT.md trim + magpie4 fold-in (catches L7 cluster) | bundled with 0f | |
| 0h. Re-deploy AGENT.md to its two parent-dir copies (per AGENT.md sync instructions), re-validate, record R6 in `pipeline_audit_rounds.json` | 30min | |

### Standing-decision triage (resolved by 0d-0e findings)

These were open coming into Phase 0; the audit findings give concrete data to decide:

- **`project/CURRENT_STATE.json`**: revive (auto-refreshed from `validation_rounds.json`) or retire (point READMEs to `audit/` artifacts). My recommendation: retire.
- **`reference/dependency_analysis/`**: regenerate as living docs, mark as Oct-2025 snapshot, or delete and lean on `Module_Dependencies.md`. My recommendation: delete or downgrade after reading what each file provides.
- **`audit/archive/` + `reference/archive/`** (272KB, R3 deletion candidate per `next_session_plan §12`): delete or keep for history.
- **`module_XX_notes.md` pattern**: keep sidecar with empties pruned + load-bearing warnings promoted to main docs, OR fold all warnings into a standard section in `modules/module_XX.md`. My recommendation: keep sidecar; delete empties; promote ~3-5 load-bearing warnings.
- **Phase 4 scope**: full GitHub Actions CI for 5c, or local pre-merge hook. Defer to Phase 4 design.

### Expected AGENT.md trims (will land in 0f-0g)

| Cut | Target | Lines saved | Risk |
|-----|--------|-------------|------|
| Hoist `LINK DON'T DUPLICATE` → `agent/helpers/maintenance_protocol.md` | L721-802 | ~80 | Low (next_session_plan §13 flag) |
| Condense `SESSION CLEANUP` detailed git steps → new helper auto-loaded on goodbye | L124-179 | ~40 | Low |
| Condense `BOOTSTRAP` greeting template + magpie-agent intro | L69-123 | ~30 | Low |
| `QUICK RESPONSE CHECKLIST` → link to `core_docs/Response_Guidelines.md` | L803-821 | ~15 | Low (already duplicated) |
| `MANDATORY WORKFLOW` redundancy with auto-loaded helpers | L265-411 | ~30-40 | Medium |
| **Add magpie4** to MANDATORY WORKFLOW + QUICK MODULE FINDER + QUALITY GUARD | scattered | -10 (additions) | Low |

Target: 846 → ~600 lines, ~46KB → ~33KB. Clears Claude's warning with headroom.

## Phase 1 — Mechanize uncovered semantic bug classes (~6-10h, 1 session)

**Goal**: catch R24-class doc bugs prospectively, not just when a flywheel round happens to land on them. Applies the verifier+MANDATE flywheel pattern (validated 4× in preproc-agent).

| Check | Catches | Effort | Confidence |
|-------|---------|--------|------------|
| **1a. `check_units.py` (new)** — scan declarations.gms for unit strings in parenthetical comments; cross-reference module_XX.md prose unit claims | Q1-B3 class (e.g., USD17MER/Tg vs /Mg, 6-orders-of-magnitude drift) | 2-3h | High — declarations have well-formed unit comments |
| **1b. Extend `check_consumer_attribution.py` for prose** — parse parenthetical-module-number patterns ("residues (18), factor costs (38), ...") in addition to markdown tables | Q4-B4 class (M38 wrongly listed; M29 omitted) | 3-4h | Medium — prose patterns vary |
| **1c. MANDATE 17 (one-hop reads) in `verifiers.md`** — when claiming "M_X uses vm_*", grep-verify direct consumption; if M_X reads only an aggregate, say "M_X uses [aggregate] populated by M_Y" | Q4-B3 class (vm_carbon_stock_croparea attributed to M52/M56) | 1-2h | High — docs-only, reuses G2 anchor logic |
| **1d. Pattern 10 hardening** — extend `check_gams_citations.sh` to compare cited-line *content fingerprint* (equation-name pattern, comment block, declaration line) against expected, not just file existence | Q3-B1 class (GDP-cap citation `:30-42` resolves but content shifted; actual `:21-33`) | 2-4h | Medium — fingerprint design is the open Q |

**Expected corpus-wide catches when first run**: ~15-30 doc bugs as advisory. Iterate triage before any wired-as-error decision.

## Phase 2 — Sweep known-fragile backlog (~8-12h, 2 sessions)

**Goal**: close the R3-deferred work that's been generating bombs. Pre-sweep with Phase 1 validators first.

| Sweep | Source | Effort |
|-------|--------|--------|
| **2a. M30 `simple_apr24` body rewrite** | `next_session_plan §8` — declarations.gms cites detail_apr24 line numbers but default is simple_apr24 | 3-4h |
| **2b. M80 `nlp_apr17` Parameters table** | `next_session_plan §8` — missing for the default realization | 2-3h |
| **2c. M11 §17.2 deep sweep** | R3 found a Critical 14-variable fabrication; rest of M11 not deeply re-audited | 3-4h |

Order matters: do Phase 1 first so the validators catch mechanical drift before manual rewrites — manual pass then focuses on semantic content only.

## Phase 3 — R25 + R26 re-measure (~3h, 1-2 flywheel rounds)

| Round | Focus | Expected |
|-------|-------|----------|
| **R25** | High-bomb-probability fresh modules: M11, M38, M52, M53, M70. Pre-sweep each target doc with Phase 1 validators before Sonnet probes. Rotate back to G1+G2 anchors. | Mean ≥8.0 (recover from 7.5) |
| **R26** | Re-probe Phase 2's swept modules (M30, M80, M11). Establish post-sweep baseline. | ≥8.5/10 per R13 post-fix-retest precedent |

### What R25 specifically must check (added 2026-05-25 end-of-Phase-2)

The R6 / Phase 0-2 work was structural; Phase 3 is the empirical test. R25 needs to answer these specific questions:

**A. Did the bomb rate drop?**
- Mean score ≥8.0 (R24 was 7.5; gate is "recover")
- 0 CRITICAL bugs (R4/R5 baseline was 0; Phase 0 work shouldn't have introduced any)
- ≤1 HIGH bug per question on average (R24 had 16 HIGH across 6 questions; aim for ~6 HIGH)

**B. Did the Phase 2 sweeps actually work?**
- **NO bombs in M30**: the realization-aware labeling should mean answers about simple_apr24 cite simple_apr24 file:line, not detail_apr24. If a question about default M30 behavior surfaces detail_apr24 line numbers, the sweep was superficial.
- **NO bombs in M80**: questions touching `s80_resolve_option`, `s80_maxiter`, etc. for the default nlp_apr17 realization should answer from the new Parameters table, not from lp_nlp_apr17.
- **NO bombs in M11**: the R3 §17.2 fix held under spot-check; R25 should confirm it holds under adversarial probing too.

**C. Did the new Phase 1 mechanizations actually catch their target classes?**
- **check_units (1a)**: if any new doc edits land between now and R25, run `python3 scripts/check_units.py` first. Should catch any new Tg/Mg-class drift.
- **Pattern D consumer attribution (1b)**: if a question probes "which modules consume vm_X", the answer should be grep-verifiable. Pattern D is now armed to catch wrong-module attribution prospectively.
- **Citation fingerprint (1d)**: any new file:line citation in a doc edit should be verifiable; `check_gams_citations_impl.py` now reports actual occurrence + suggested update target when content shifts.
- **MANDATE 17 (1c)**: questions about variable consumption chains should distinguish direct readers from aggregate-via-intermediary. The R24 Q4-B3 class (M30 → vm_carbon_stock_croparea → M52/M56 attribution error) shouldn't recur.

**D. Did the AGENT.md trim degrade response quality?**
- Watch for answers that miss load-bearing context that USED to be in always-loaded surface but now lives in a hoisted helper (session_cleanup, link_dont_duplicate, directory_structure). If a question that would have benefited from one of these is answered without it, the auto-load trigger may need tightening or the hoist may need partial revert.
- Watch for over-tightened triggers (the 4 trigger tightenings in Cluster F: bare "modify"/"water"/"scenario"/"equation" removed). If a question that SHOULD have loaded the relevant helper doesn't trigger it, the trigger list is now too narrow.

**E. Did the magpie4 + preproc workflow additions route correctly?**
- A question about a report.mif variable should route through `magpie4_reference.md` (G3/G4 regression questions test this directly per validation_rounds.json schema v1.2).
- A question about input data origin should route to `PREPROC_AGENT.md` per the new DOCUMENT HIERARCHY branch.

**F. Validator state at R25 launch**
- Run `bash scripts/validate_consistency.sh` immediately before launching R25 questions. Expected: 39/40 pass + 2 acceptable warnings (the README/helper CLAUDE.md mentions + the units advisory). If state has drifted, fix BEFORE running R25 — otherwise R25 confounds Phase 2 outcomes with subsequent drift.

**Practical R25 protocol**:
1. `bash scripts/validate_consistency.sh` — confirm baseline state.
2. `python3 scripts/check_units.py --summary` — note current count of advisory mismatches.
3. `python3 scripts/check_consumer_attribution.py --summary-only` — note Pattern D state.
4. Run `/validate-semantic` per the standard flow.
5. Compare: any HIGH-severity finding in M30/M80/M11 means Phase 2 was superficial → revisit. Any check_units / Pattern D / fingerprint finding that the question's auditor MISSED (but the validator caught) means the validator is doing its job and is high-leverage to wire as a regression gate.

**Failure-mode flags for R25**:
- Mean <7.5 → Phase 0-2 made things worse (rollback or partial-revert assessment needed)
- Mean 7.5-7.9 → Phase 0-2 didn't help materially (re-strategize before Phase 4)
- Mean 8.0-8.4 → Recovery achieved; Phase 2's swept modules should be probed in R26 to confirm
- Mean ≥8.5 → Recovery + improvement; proceed to Phase 4 design

## Phase 4 — Prospective prevention (1-2 weeks, separate initiative)

**Goal**: catch drift at PR-merge time, not at flywheel-round time.

| Step | Effort |
|------|--------|
| **4a. Extend 5c past `identifier_added`-only MVP** to handle `identifier_removed` and `new_realization` | 4-6h each |
| **4b. Deploy 5c on every MAgPIE PR merge** | Design Qs from `next_session_plan`: GitHub Actions CI vs. local pre-merge hook; auto-PR-create vs. comment-only |

## Effort summary

| Phase | Effort | Cadence |
|-------|--------|---------|
| 0 | 6-8h | 1 focused session |
| 1 | 6-10h | 1 focused session |
| 2 | 8-12h | 2 sessions |
| 3 | ~3h | 1-2 flywheel rounds |
| **Phases 0-3 total** | **~25-35h** | **1-2 weeks of focused work** |
| 4 | 1-2 weeks | Separate initiative |

## Context for future sessions (cold-start)

If you're a future Claude picking this up cold, here's the pointer set:

### What R24 found (the trigger for this plan)
- `audit/round24_design.md` — round design (6 questions: 4 new probes + G3/G4 first-use)
- `audit/round24_answers/{Q1-Q4,G3,G4}_answer.md` — Sonnet answers
- `audit/round24_audits/{Q1-Q4,G3,G4}_audit.md` — Opus audits with bug listings
- `audit/round24_synthesis.md` — synthesis, root-cause clusters, doc-vs-answerer attribution
- `audit/validation_rounds.json` R24 entry — mean 7.5/10, 2 bombs (Q4 4/10, Q1 5/10)

### Doc fixes already applied in R24
- `modules/module_56.md` L152, L158, L627, L675 — units Tg → Mg
- `modules/module_13.md` L196, L262, L274, L345 — presolve.gms line drift `:30-42`→`:21-33`, `:74-78`→`:73-77`
- `modules/module_30.md` L22, L360, L1713 — `vm_area` consumer list + `vm_carbon_stock_croparea` one-hop attribution
- `modules/module_30_notes.md` — appended R24 entries 3 + 4
- `audit/global/agent_lessons.md` — R24-A1 (auditor false-positive on `s30_implementation`)

### Why the doc-surface drift is a "things I happened to notice" list, not a hunt result
The Phase 0 lens audit exists specifically to convert these one-off catches into a systematic sweep. If you find yourself adding new "what about X" entries to this plan instead of running Phase 0, run Phase 0 instead — the audit is designed to find your siblings.

### Twin-agent disambiguation reminder
This is the **magpie-agent** plan. `magpie-preproc-agent` has its own validation_rounds.json and shouldn't be touched as collateral. Round numbers don't compare across agents (see AGENT.md "Twin-agent disambiguation").

## Standing decisions

Currently only one decision is live; the rest are deferred until Phase 0 produces real findings:

1. **Phase order**: Phase 0 first (recommendation: yes — slimmer AGENT.md helps every subsequent session, and the R6 audit will resolve the standing 4-5 decisions in one batch with real data).

Phase 0d resolves: CURRENT_STATE.json fate, dependency_analysis fate, archive directories fate, notes pattern fate. Phase 4 scope decided during Phase 4 design.

## Status tracking

Update the checkbox row at the top as phases complete. Append session-by-session notes here:

### Sessions

**Session 1 — 2026-05-25 — Phase 0 (Stale-and-Remnant pipeline audit R6) — COMPLETE**

- 0a (design): 7 lens prompts with R24 anchors, model upgraded Sonnet → Opus mid-design per user. → `audit/pipeline_audit_round6_design.md`.
- 0b (lens agents): 7 parallel Opus sub-agents, ~15-25min wall each, returned 70 raw findings. → `audit/pipeline_audit_round6_raw_findings.md`.
- 0c (Opus re-run): SKIPPED — Opus already used for all 7 lens agents.
- 0d (synthesis): single Opus call, 70 raw → 58 dedup, 8 root-cause clusters, 4 standing decisions resolved + 1 deferred. → `audit/pipeline_audit_round6.md`.
- 0e (per-cluster decisions): user approved all synthesis recommendations on all 4 standing decisions + 5 open questions in one turn.
- 0f (apply interventions): 7 cluster commits stacked in dependency order — D (security) first, then A, C, B, G, H, E. + 1 parent-repo commit (parent `.gitignore` exposure fix, --no-verify per user authorization for the over-firing pre-commit hook).
- 0g (Cluster F): AGENT.md trim 846 → 724 lines / 46KB → 44KB. 3 new auto-loaded helpers (session_cleanup, link_dont_duplicate, directory_structure). magpie4 + preproc added to 5 scaffold sections. 4 broad triggers tightened. AGENT.md re-deployed to `../AGENT.md` + `../CLAUDE.md`.
- 0h (log): `audit/pipeline_audit_rounds.json` R6 status → "fixed + mechanized", 10 guards recorded.

Effort: actual ~10-12h compute (vs synthesis estimate 15-17h). Below estimate because clustering aggregated effort efficiently.

**Deferred (out of Phase 0 scope, flagged for future)**:
- D6: tighten parent magpie/.gitignore `*.cs*` → `*.cs2/cs3/cs4` (upstream MAgPIE concern, not agent's call).
- F5: hoist Twin-agent disambiguation (~26 lines) + trim COMPLETE DOCUMENTATION STRUCTURE (~55 lines) for further ~80-line AGENT.md reduction. Both MEDIUM-severity. Revisit if AGENT.md still feels too large in Phase 3 re-measure.
- C2-extension: M11/M17/M21/M32/M52 backfill from validation rounds — per synthesis recommendation, these stay deleted unless future use surfaces warnings worth recording.

**Next**: Phase 1 (mechanize uncovered semantic bug classes — units check, prose consumer attribution, one-hop reads, citation content fingerprint). Awaits user direction on when to start.

**Session 2 — 2026-05-25 — Phase 1 (mechanize uncovered semantic bug classes) — COMPLETE**

- 1c (MANDATE 17 one-hop reads): added to verifiers.md + AGENT.md Step 1d short-index. Catches the R24 Q4-B3 class where consumption is attributed to a module that reads only an aggregate (e.g., M30 -> M29 aggregate -> M52/M56, NOT M30 -> M52/M56 direct). Commit 2df4520.

- 1a (check_units.py NEW): scans declarations.gms for canonical `(unit)` parentheticals, cross-references module_XX.md prose unit claims. Catches R24 Q1-B3 class (Tg vs Mg, USD17MER vs USD, etc.). 1301 canonical identifiers indexed; 40 doc claims scanned per run; ~5 advisory mismatches surfaced initially (some legitimate abbreviations, some worth tightening). Wired as advisory Check 26/26 in validate_consistency.sh. Commit e5d4aaa.

- 1b (check_consumer_attribution.py EXTENDED with Pattern D): line-level prose attribution checker. Catches R24 Q4-B4 class ("vm_X consumed by: name (NN), ..." where one of the NN doesn't grep-hit). Filters: consumer-direction trigger words only (excludes "downstream"/"critical for"), historical-marker skip ("R24 correction"/"earlier wording"), producer exclusion. Verified: catches synthesized pre-fix R24 bug; 0 FPs on current corpus. Commit 9b8260a.

- 1d (check_gams_citations_impl.py HARDENED with fingerprint): when a backticked identifier is not within the cited ±5 window, scans ±50 lines, reports actual location + delta, suggests update target. Turned "warn-only" into "warn + suggested fix". Surfaced 4 advisory findings: 2 real drifts (module_52.md s32_aff_plantation off-by-1 in 3 citations — fixed in commit 6f734a4; module_14.md vm_tau contrastive-phrase FP), 2 pedagogical FPs in Bug_Taxonomy.md. Commit 957ef9c.

Phase 1 takeaway: 4 new mechanizations (3 script extensions + 1 MANDATE doc), 1 real doc-drift bug surfaced and fixed (M52 citation off-by-1), validator count 25 -> 26 main checks. The flywheel pattern continues to work — Phase 0 audit findings → Phase 1 mechanizations → ongoing prospective coverage.

**Deferred / open**:
- check_units.py FP rate (~40% on initial run) — could tighten further by adding contrastive-phrase filter or a unit-token denylist. Acceptable for advisory tier.
- Pattern D multi-cite cross-pollination (one citation in a multi-cite line picks up nearby backticked ids meant for sibling cites). Structural limit of the line-level heuristic.
- M14 vm_tau contrastive-phrase finding (acknowledged false positive).

**Next**: Phase 2 (sweep M30/M80/M11 known-fragile docs — pre-sweep with Phase 1 validators first per plan). Awaits user direction.

**Session 3 — 2026-05-25 — Phase 2 (sweep known-fragile backlog) — COMPLETE**

- 2a (M30 simple_apr24 awareness): pre-sweep with Phase 1 validators revealed the scope was smaller than R3 feared — §§1-2 cite line numbers that happen to match BOTH realizations (q30_prod L14-15, q30_betr_missing L21-23), §§6-8 had no cited line numbers, only §§3-5 (rotational constraints) needed realization-explicit attribution. Minimal-disruption rewrite: dropped R3 warning header; replaced "Core Equations (12 Total)" with "9 in simple_apr24 default / 12 in detail_apr24 alternative"; prefixed §§3-5 Locations with `detail_apr24/`; added realization callouts to §3 (detail-only with reference to §10 for simple_apr24 form), §4 (penalty-based detail-only), §5 (irrigated detail-only); labeled §§6-8 as "(both realizations; different line numbers)". Commit 3fe8b68.

- 2b (M80 nlp_apr17 Parameters table): added missing Parameters subsection between §lp_nlp_apr17 and §nlp_apr17 (between "Key Differences" and the nlp_ipopt section). Tables: 2 declarations + 2 scalars + 4 input scalars all verified against `../modules/80_optimization/nlp_apr17/declarations.gms` + `input.gms`. Comparison-with-lp_nlp_apr17 footer notes the 2+4 vs 4+4 difference reflects no-LP-warmstart simplification. Commit 208c001.

- 2c (M11 §17.2 deep sweep): pre-sweep with Phase 1 validators (`check_units`, `check_consumer_attribution`, `check_doc_var_existence`, `check_gams_citations_impl`) returned 0 findings on M11. Spot-checks of §3 cost-component table citations (vm_cost_prod_crop:15, vm_cost_prod_kres:16, vm_cost_prod_past:17, vm_cost_prod_fish:18, vm_cost_prod_livst:19, vm_cost_fore:33, vm_cost_timber:34, vm_cost_hvarea_natveg:35) all match q11_cost_reg L15-47 directly. §17.2 table re-counted: 32 terms in equation = 31 costs + 1 reward; 27 source modules — exact match to doc's claim. The R3 fix held; no further edits needed. (No commit — verification only.)

Phase 2 takeaway: deferred-since-R3 work closed in a single session. The Phase 1 mechanizations did exactly their job — pre-sweeping with validators scoped the manual work down to what was actually broken, instead of forcing a full re-derivation.

**Next**: Phase 3 (R25 + R26 semantic-flywheel re-measure to confirm bomb rate dropped). Awaits user direction on when to start. Phase 3 will use the existing `/validate-semantic` flow; expected effort ~3h per round.

**Session 4 — 2026-05-25 — Phase 3 R25 (re-measure) — COMPLETE**

- Pre-launch baseline: `scripts/validate_consistency.sh` 39/41 + 2 advisory warnings; `check_units.py` 5 advisory; `check_consumer_attribution.py` 0 mismatches + Pattern D clean. magpie4 clone synced (v2.70.0 @ a360d8c9ec).
- R25 design (`audit/round25_design.md`): 5 new probes (Q1 M30 rotation, Q2 M80 solver, Q3 M57 N-MACC chain, Q4 M38 consumer attribution, Q5 magpie4 N2O AWMS provenance) + 2 regression (G1 M14 yields, G2 vm_carbon_stock).
- Answers (`audit/round25_answers/`): 7 parallel Sonnet 4.6 magpie-helper agents, doc-only (Q5 also allowed magpie4 pinned clone). All wrote answer files.
- Audits (`audit/round25_audits/`): 7 parallel Opus 4.6 general-purpose agents, scored per `flywheel_rubric.md`.
- Synthesis (`audit/round25_synthesis.md`): mean **8.93/10** (vs R24 7.5; +1.43 recovery). 0 CRITICAL, 2 Major, 5 Minor, 4 Info. Both regression anchors G1, G2 scored 10/10 with drift=false. Per plan: mean ≥8.5 → "Recovery + improvement; proceed to Phase 4 design."
- Bug fixes (8 doc edits + 1 infra):
  - `modules/module_30.md:522` c30_rotation_constraints input.gms `:24` → `:14`
  - `modules/module_80.md` Parameters table: `:8-13` → `:8-15` range; `s80_counter :13`→`:14`; `s80_resolve_option :14`→`:15`
  - `modules/module_11.md:442` vm_reward_cdr_aff comment `:57` → `:59`; `:452` vm_maccs_costs comment `:58` → `:60`
  - `modules/module_38.md` (5 locations: L33, L121, L336, L357, L617): added M36 (employment, `exo_may22/equations.gms:23-25`) as second consumer of `vm_cost_prod_crop` (labor slice). Asymmetric drift — `module_36.md` already documented M36→M38 from consumer side.
  - `scripts/validate_consistency.sh`: exclude `audit/round*_answers/` and `audit/round*_audits/` from stale-prefix check (immutable captured agent outputs, not authoritative docs)
- Validator gaps surfaced (queued for Phase 1 follow-up / Phase 4):
  - **Pattern D negative-evidence**: `check_consumer_attribution.py` missed the M36 omission. Needs to grep for modules that read a variable and flag those NOT in producer-doc consumer list (currently only checks listed-consumers-grep-positive direction).
  - **Citation fingerprint sensitivity**: `check_gams_citations_impl.py` didn't pre-flag 5 adjacent-line drifts. Heuristic may be too tolerant of similar-content neighbors.
  - **probe_dedup_check.py append-on-completion**: spec (validate-semantic.md Step 5c) says script appends new probe names to ledger; current implementation only warns. Ledger updated manually for R25.
- JSON record: appended R25 entry to `audit/validation_rounds.json` (schema v1.2). Trend now `…7.5→8.93`. G1/G2 `used_in_rounds` advanced to `[22, 23, 25]`.
- Probe-dedup ledger: M11, M30, M36, M51, M55, M57, magpie4_helper added; M38, M51, M80 retire-after advanced to 28.

Effort: ~50 min wall (7 parallel Sonnet ≈ 1-2 min, 7 parallel Opus ≈ 4-7 min, synthesis + fixes ≈ 15-20 min).

**Phase 2 sweep retrospective**: the Phase 2a/2b sweeps were content-correct but had embedded citation-line drift (sweeps added structure without grep-confirming citations). The Phase 3 round caught the drifts within hours. Suggests Phase 2-style sweeps should always be followed by `check_gams_citations_impl.py` on the touched docs before considering the sweep closed.

**Next**: R26 — Re-probe Phase 2 swept modules (M30, M80, M11) to confirm post-fix stability. Awaits user direction. Lower-priority compared to Phase 4 design since R25 already showed strong recovery; but R26 closes the "did the line-fix corrections themselves introduce any regressions" question.
