# Plan: get the bomb rate under control + clean up the doc surface

**Created**: 2026-05-24 (post-R24 conversation)
**Status**: ☑ Phase 0 (2026-05-25)  ☐ Phase 1  ☐ Phase 2  ☐ Phase 3  ☐ Phase 4
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
