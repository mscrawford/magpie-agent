# Pipeline audit — Round 6 (R6)

**Date**: 2026-05-25
**Commit**: ad583d2 (HEAD at synthesis time)
**Auditor**: 7 parallel Opus 4.7 sub-agents, one per lens (`/pipeline-audit` with R6 design overrides)
**Synthesis**: single Opus 4.7 call
**Round type**: **Doc-surface drift** (NOT doc↔code fidelity — see R6 design doc §2)
**Context**: Phase 0d of `audit/get_under_control_plan.md`. Hunts the **siblings** of seven R24-surfaced doc-rot anchors (CURRENT_STATE.json SSOT staleness, dead SSOT convention, empty `module_XX_notes.md`, ~290K vs ~342K word drift, validation_report orphans in parent, README → stale SSOT, AGENT.md 46KB / magpie4 missing from MANDATORY WORKFLOW).
**Status**: triaged + clustered; **awaiting user decisions on standing items before fix phase 0f**.

---

## Topline

**Total findings (deduplicated)**: **58** (from 70 raw — 12 collapsed via cross-lens corroboration).

| Severity | Count | Note |
|---|---|---|
| CRITICAL | 0 | Consistent with R4/R5 — no answer-level damage class in doc-surface drift |
| HIGH | 16 | Up from R5's 6; doc-surface drift produces more HIGH/MEDIUM hits than doc↔code drift does (different failure profile) |
| MEDIUM | 25 | |
| LOW | 17 | |

**By lens** (deduplicated; corroborated findings counted once at their highest-corroborating lens):

| Lens | Raw | Dedup | HIGH | Corroborated outwards into |
|---|---|---|---|---|
| L1 — Staleness | 8 | 6 | 1 | L2, L4, L6 (CURRENT_STATE; cross_module 2025-10-22 footers; helper 2025-07 dates) |
| L2 — Dead conventions | 11 | 9 | 3 | L1, L4, L6 (CURRENT_STATE SSOT; multi-realization list; bootstrap "6 commands") |
| L3 — Half-deployed patterns | 3 | 3 | 0 | (own surface — no overlap) |
| L4 — Cross-doc inconsistency | 7 | 5 | 3 | L2, L6 (bootstrap counts; schema version; lens/agent count) |
| L5 — Misplaced outputs | 7 | 7 | 3 | (own surface — no overlap; gitignore class is L5-unique) |
| L6 — Reference-graph integrity | 15 | 11 | 2 | L1, L2 (4 of L6's hub-pointer hits subsumed by L1 staleness anchor) |
| L7 — Surface bloat + workflow gaps | 19 | 17 | 4 | (own surface — no overlap; AGENT.md bloat + magpie4 are L7-unique) |
| **Total** | **70** | **58** | **16** | |

**Surface verified clean** (no R6 findings — useful negative results):
- `diff AGENT.md ../AGENT.md` and `diff AGENT.md ../CLAUDE.md` both empty (846 lines / 46,041 bytes byte-identical across all three). Deploy hook is working.
- No helper exceeds the 5,000-word anchor (verifiers.md largest at 2,285 words).
- `audit/archive/` and `reference/archive/` are properly contained (archive material per L3); no orphan references into live workflow.
- `<!--count:...-->` marker mechanism: 0 drift in marker-managed counts (Cluster E below is about coverage, not correctness).
- `agent/helpers/magpie4_reference.md` is current and live (its absence from the workflow scaffold is the gap — see Cluster F).

---

## Corroborated findings (high-confidence cross-lens hits)

These are the findings where ≥2 independent lenses (with engineered method decorrelation per `template_multi_agent_audit`) flagged the same defect. Each is a more reliable signal than a single-lens hit.

| # | Finding | Lenses | Severity | Cluster |
|---|---|---|---|---|
| C1 | **`project/CURRENT_STATE.json` declared "SINGLE SOURCE OF TRUTH" but `last_updated: 2026-03-07` (79 days) with multiple stale internal counts (10 helpers / 6 commands / 24 rounds vs actual 14 / 10 / 24)** | L1, L2, L4, L6 (4 lenses) | HIGH | A |
| C2 | **`cross_module/{land,water,carbon}_balance_conservation.md` footer `Last Updated: 2025-10-22` (215 days) while files modified 2026-05-24 (Phase 3 cleanup substantive on carbon)** | L1, L6 | MEDIUM | B |
| C3 | **`agent/commands/bootstrap.md:110` "Expected: 6 command files" — actual 10** | L2, L4, L6 (3 lenses) | HIGH | E |
| C4 | **`pipeline-audit.md` and `AGENT.md:202` hardcode "6 lenses / 6 parallel Opus agents" — current R6 runs 7** | L2, L4 | MEDIUM | E |
| C5 | **`agent/helpers/{adding_new_scenario,comparing_model_runs,water_scarcity_scenarios}.md` headers stamp 2025-07-15/18 — file first commit is 2026-03-07 (impossible old date)** | L1, L6 | MEDIUM | B |
| C6 | **`agent/helpers/maintenance_protocol.md` self-claims authority for staleness/sync questions while own `Last updated: 2026-03-07` (79 days) and own `Lessons count: 0`** | L1, L2, L6 (3 lenses) | MEDIUM | B |
| C7 | **`core_docs/Tool_Usage_Patterns.md` header `Last Updated: 2025-11-29` (178 days), modified 2026-05-24** | L1, L6 | MEDIUM | B |
| C8 | **AGENT.md "Modules with multiple realizations" list omits 18 of 40 actual cases (including hubs 10, 14, 52, 56)** | L2 (L4 lists count drift adjacent but on different facets) | HIGH | E |
| C9 | **`validation_rounds.json` schema_version drift: validate-semantic.md says v1.1; JSON header is v1.2; audit/README.md is v1.2** | L4 (L2-adjacent) | HIGH | E |
| C10 | **`project/README.md` says "2 essential files" — actual project/ has 4 (CURRENT_STATE.json, README.md, sync_log.json, version_pins.json)** | L2, L6 | MEDIUM | A |
| C11 | **README.md "~290K words" vs AGENT.md "~342K words" vs actual ~347K words** | L4 (own); README is not in `refresh_aggregate_counts.py` TARGET_FILES — verified in script source | HIGH | E |
| C12 | **`validation_report_*.txt` orphans in parent `/magpie/` root (2 files) + same defect class still in current `validate_consistency.sh` (mkdir-before-cd) + stale .bak file with original bug + parent `.gitignore` missing entries for entire installed agent surface** | L5 (own; 4 sub-findings of one root cause) | HIGH | D |

Pattern: **all 4 of the audit's calibration anchors corroborate across multiple lenses**, confirming the decorrelation engineering worked — the anchors are not lens-specific quirks, they're real structural defects with surface in multiple measurement methods.

**Single-lens HIGH findings** (no corroboration, but lens-specific surface justifies the rating):
- L2-H1: `maintenance_protocol.md` declares "Layer 1 — Syntactic Validation (automated, every session)" but `session_startup.md` does NOT invoke `validate_consistency.sh` — convention is hollow.
- L5-H1: parent `.gitignore` missing entries → parent `origin` is `git@github.com:magpiemodel/magpie.git` (real upstream), so a careless `git add -A` would push agent infrastructure + Claude session data to public MAgPIE repo. (Real exposure risk.)
- L7-H1: AGENT.md 846 lines / 46KB exceeds Claude's deployed-surface warning threshold (~600 lines / ~40KB).
- L7-H2: magpie4 missing from FIVE workflow-scaffold sections in AGENT.md (not just MANDATORY WORKFLOW — also QUICK MODULE FINDER, QUALITY GUARD, DOCUMENT HIERARCHY, QUICK RESPONSE CHECKLIST).
- L7-H3: LINK DON'T DUPLICATE (lines 721-800) is ~80 lines of editorial policy in always-loaded surface — fires on every session including pure Q&A.
- L7-H4: SESSION CLEANUP (lines 122-176) is ~55 lines of end-of-session playbook in always-loaded surface, partially redundant with the `session-close` skill.

---

## Root-cause clusters

Per [[feedback_synthetic_interventions]]: the 58 findings collapse into **8 clusters** with one intervention per cluster. K=8 vs N=58 — synthesis-to-intervention ratio ≈ 7×, consistent with R3's "62 findings → 7 commits" precedent.

### Cluster A — "CURRENT_STATE.json is a dead SSOT; project/ is a confused directory" (~9 findings)

**Root cause**: `project/CURRENT_STATE.json` was the SSOT in v1.0 (March 2026) and the convention is documented in **5 places** (README.md, project/README.md, modules/README.md, cross_module/README.md, AGENT.md). After v1.0 the agent's state-tracking moved to `audit/*.json` + commit log + `audit/global/agent_lessons.md`. The SSOT convention was never retired; the 5 pointers + the per-module Quick Quality Checklist item are now dead. **The directory `project/` itself drifted**: was "2 essential files" (CURRENT_STATE.json + README.md), now contains 4 (added sync_log.json 2025-11-29 and version_pins.json 2026-05-24), but the README still says 2.

**Findings**: L1-1, L2-1, L2-2, L2-11 (project/README "2 files"), L4-6 (phase totals), L6-1 (5 pointers to stale SSOT), L6-9 (project/README "User feedback system" — dead concept), L6-10 (project/README "2 essential files"), L6-15 (R3 fix re-occurrence: subordinate-README inventories drift).

**Proposed intervention** (resolves **Standing Decision (i)**): **retire CURRENT_STATE.json as SSOT**. Two sub-actions:
- (A1) Replace the 5 SSOT pointers with `→ audit/validation_rounds.json + audit/pipeline_audit_rounds.json + project/sync_log.json + commit log + audit/global/agent_lessons.md`.
- (A2) Archive `CURRENT_STATE.json` (move to `audit/archive/CURRENT_STATE_v1.0_snapshot.json` with a one-line README disclaimer) OR keep in place as a v1.0 release snapshot with a single-line header demoting it from "SSOT" to "v1.0 release snapshot (frozen 2026-03-07)".
- (A3) Either move `sync_log.json` to `audit/` (so `project/` reverts to the 2-file framing) OR update `project/README.md` to list all 4 current files. **Recommendation**: move to `audit/` — sync_log is state-tracking, same class as validation_rounds.json.
- (A4) Remove the "[ ] Updated CURRENT_STATE.json" line from `README.md` Quick Quality Checklist (every module-doc commit since 2026-04-01 violated it).

**Effort**: 1.5h. **Risk**: low (4-5 file edits, all in retire-the-pointer direction). **Order**: do FIRST — unblocks Cluster B & E by reducing the pointer graph that needs auditing.

### Cluster B — "Static 'Last updated' headers everywhere drift" (~13 findings)

**Root cause**: header convention `**Last updated**: YYYY-MM-DD` was deployed across helpers, cross_module conservation docs, core_docs, project README, AGENT.md tail. Convention treats the field as **text-to-write-once** rather than **state-to-maintain**. mtime-fresh files (touched by sed-sweeps like 1c7df77 feedback→audit and e982a76 Phase 2 prep) are the rule; content-fresh is rare; the eye is drawn to the stale claim, not the mtime. 3 helpers carry physically-impossible 2025-07 dates (older than file creation). cross_module 2025-10-22 footers route 5+ inbound pointers to claimed-stale targets. maintenance_protocol.md is the protocol-owner and itself violates its protocol.

**Findings**: L1-2 (3 helpers with 2025-07 impossible dates), L1-3 (water_scarcity_scenarios specifically), L1-4 (8 helpers ~80 days), L1-5 (EXECUTIVE_SUMMARY half-updated), L1-6 (Tool_Usage_Patterns), L1-7 (3 cross_module conservation files), L1-8 (AGENT.md has no footer at all), L6-2 (cross_module → hub asymmetry), L6-3 (Tool_Usage_Patterns hub asymmetry), L6-4 (maintenance_protocol.md self-staleness), L6-5 (3 helpers hub-asymmetry from 2025-07), L6-16 (hub back-reference asymmetry — meta).

**Proposed intervention**: **drop the static "Last updated" convention** in favour of one of:
- (B1) **Preferred**: remove all "Last updated" / "Last Updated" fields; replace with a single line at file top: "_Last semantic edit: run `git log -1 --format=%ad -- <file>`_". Honest, never wrong. **Cost**: ~30 sweep edits, 15 min.
- (B2) **Alternative**: keep the convention but wire it via a pre-commit hook that bumps the field whenever the file's non-mtime content changes. **Cost**: 1h hook + 30 sweep edits to baseline.
- (B3) Add a Cluster G-related "Hub status: pointed at by N+ docs; re-verify on major MAgPIE syncs" footer to high-in-degree files (CURRENT_STATE.json [resolves if A retires it], the 4 cross_module conservation docs, Tool_Usage_Patterns.md, maintenance_protocol.md, verifiers.md). **Cost**: 30 min.

**Recommendation**: (B1) + (B3) together. (B2) is too much infra for too little payoff.

**Effort**: 2h. **Risk**: low. **Order**: do AFTER Cluster A (so CURRENT_STATE.json is decided before we sweep its date field).

### Cluster C — "Empty scaffolds without backfill: notes files + Lessons Learned" (3 findings)

**Root cause**: proactive scaffolding of feedback surfaces before content exists, with no forcing function to backfill. 8 of 18 `module_XX_notes.md` are 52-word byte-equivalent stubs ("No warnings recorded yet" / "No lessons recorded yet" / "No examples recorded yet") for high-centrality modules (10, 11, 17, 21, 32, 52, 56, 70). 6 helpers have `Lessons count: 0` `<!-- APPEND-ONLY -->` sections >2.5 months old. `verifiers.md` (largest helper, 16 binding MANDATEs) lacks the Lessons-count header entirely. **Workflow-step theatre**: AGENT.md instructs "always read notes files when answering about a module" — for these 8 modules the read returns nothing.

**Findings**: L3-1 (8 empty notes), L3-2 (6 stalled Lessons), L3-3 (verifiers.md missing header — also flagged by L2-10).

**Proposed intervention** (resolves **Standing Decision (iv)**): **keep sidecar pattern; delete empties; promote ~3-5 load-bearing warnings from validation rounds**:
- (C1) DELETE all 8 empty `module_XX_notes.md` files (52-word stubs). Re-creation is on-demand per AGENT.md's notes-file template — absence is the correct signal that notes don't exist.
- (C2) Backfill modules 10, 56, 70 from `audit/validation_rounds.json` (multiple R-series findings exist for each that should be summarized into notes). Modules 11/17/21/32/52 stay deleted unless future use surfaces warnings worth recording.
- (C3) Add `**Lessons count**: 0 entries` header to `verifiers.md` (one-line fix; L2-10 says trivially fixable).
- (C4) Either lower the "5+ entries triggers promotion review" threshold to 2 (achievable) or downgrade the prescriptive language to descriptive — L2-5 says the rule has never fired because no helper has ≥5 entries.

**Effort**: 1.5h (mostly the C2 backfill from validation_rounds). **Risk**: low. **Order**: can parallelize with B.

### Cluster D — "Misplaced outputs + .gitignore exposure: real security risk" (~5 findings)

**Root cause**: a CWD-before-cd bug in `validate_consistency.sh` (and worse in its .bak) caused validator outputs to land in caller's CWD instead of `magpie-agent/.cache/validation_reports/`. When the user invokes from the parent magpie/ repo, the output lands in MAgPIE's root. **Parent `.gitignore` does not cover any of the installed agent surface** (`AGENT.md`, `CLAUDE.md`, `PREPROC_AGENT.md`, `magpie-agent/`, `magpie-preproc-agent/`, `.claude/`, `.copilot/` all show as `??` in parent `git status`). Parent's `origin` is `git@github.com:magpiemodel/magpie.git` (the real upstream) — a careless `git add -A && git commit && git push` from parent would publish agent infrastructure + Claude session data to public MAgPIE. **add_timestamps.py** lives at agent root instead of scripts/ (sole non-canonical entry at agent root). **R6 design doc itself** is untracked (sibling tracked rounds are committed).

**Findings**: L5-1 (2 validation_report orphans in parent), L5-2 (current script still has same defect class), L5-3 (stale .bak with original bug), L5-4 (add_timestamps.py at wrong location), L5-5 (parent .gitignore gap — HIGH exposure), L5-6 (.gitignore `*.cs*` accidentally catches .csv — fragile), L5-7 (R6 design doc untracked).

**Proposed intervention**: bundle of small but security-critical fixes:
- (D1) Add to parent `/magpie/.gitignore`: `AGENT.md`, `CLAUDE.md`, `PREPROC_AGENT.md`, `/magpie-agent/`, `/magpie-preproc-agent/`, `.claude/`, `.copilot/`, `validation_report_*.txt`, `.cache/`. **THIS IS THE HIGHEST-URGENCY FIX IN R6**.
- (D2) Move/delete the 2 existing `validation_report_*.txt` orphans in parent root.
- (D3) Fix `scripts/validate_consistency.sh`: move the `cd "$AGENT_DIR"` block to BEFORE line 22 (currently fires at line 80 — too late). Or set `REPORT_DIR="${AGENT_DIR}/.cache/validation_reports"` explicitly after computing AGENT_DIR.
- (D4) DELETE `scripts/validate_consistency.sh.bak` (footgun; git history preserves prior versions).
- (D5) `git mv add_timestamps.py scripts/add_timestamps.py` + anchor `modules_dir` explicitly with `Path(__file__).resolve().parent.parent / 'modules'`.
- (D6) Tighten `magpie-agent/.gitignore` `*.cs*` to explicit `*.cs2`, `*.cs3`, `*.cs4` (the accidental .csv catch is fragile).
- (D7) Commit `audit/pipeline_audit_round6_design.md` (sibling pattern; R1-R5 design files are tracked).

**Effort**: 1h total. **Risk**: low (D1-D2 are pure additions). **Order**: **D1 first, before any other work** — closes the security exposure. Rest can follow with B/C.

### Cluster E — "Aggregate counts hardcoded, not markered" (~8 findings)

**Root cause**: the `<!--count:foo-->N<!--/count-->` marker mechanism exists and works (R5 verified 0 drift in marker-managed counts), but coverage is sparse. `scripts/refresh_aggregate_counts.py` `TARGET_FILES` lists 8 files; `README.md` and `agent/commands/bootstrap.md` are NOT in it. So:
- `bootstrap.md:110` "6 command files" — drifted from 10 (per C3).
- `pipeline-audit.md` + `AGENT.md:202` "6 lenses / 6 parallel Opus" — drifted from current 7 (per C4).
- `validate-semantic.md` "schema v1.1" — drifted from v1.2 (per C9).
- README "~290K words" / "~64K lines" + AGENT.md "~342K words" vs actual ~347K (per C11).
- `realization_selection.md` "75 active realizations" vs `next_session_plan.md` "77/77" — 2-count drift.
- AGENT.md "Modules with multiple realizations" list (22 modules) vs actual 40 modules (per C8).
- `cross_module/circular_dependency_resolution.md:5` "26+" vs ":11" "26" — internal contradiction.
- README phase totals (Phase 0 "~70K words", Phase 1 "~20K lines", Phase 2 "~5,400 lines") drifted from actual.

**Findings**: L2-6 (bootstrap), L2-7 (lens count), L2-8 (multi-realization list, hub-critical), L4-1 (word counts), L4-2 (command count), L4-3 (schema version), L4-4 (lens count), L4-5 (realization count), L4-6 (phase totals), L4-7 (26+ vs 26).

**Proposed intervention**: extend the marker system + refresh script:
- (E1) Add markers for: `n_commands` (sourced from `ls agent/commands/*.md | wc -l`), `n_helpers`, `n_lenses_current_round` (sourced from `audit/pipeline_audit_rounds.json`), `total_doc_words` + `total_doc_lines` (sourced from `wc -w` / `wc -l` over all doc dirs), `gams_realizations_verified` (sourced from `cumulative_stats`), `n_modules_multi_realization` (sourced from a new helper `count_multi_realization_modules.py`), `validation_schema_version` (sourced from `validation_rounds.json` `.metadata.schema_version`).
- (E2) Extend `scripts/refresh_aggregate_counts.py` `TARGET_FILES` to include: `README.md`, `agent/commands/bootstrap.md`, `agent/helpers/realization_selection.md`, `cross_module/circular_dependency_resolution.md`, and any other file currently carrying a hardcoded count.
- (E3) Replace the static "Modules with multiple realizations" list in AGENT.md (Step 1c, line 322-324) with dynamic instruction: "Before answering about ANY module: check `ls ../modules/XX_*/` to see if there are >1 realizations. If yes, run Step 1c."
- (E4) Reconcile lens count — either canonize 7 (R6 standard) and update `pipeline-audit.md` text, or keep 6 as canonical default and explicitly document R6 as a per-round override.

**Effort**: 2.5h (E1 + E2 are the bulk; E3 is a trivial edit; E4 is a documentation decision). **Risk**: low. **Order**: AFTER Cluster A and B (so the new pointer graph and date convention are settled first).

### Cluster F — "AGENT.md bloat + magpie4/preproc workflow gaps" (~9 findings, all L7)

**Root cause** — TWO ROOT CAUSES, one cluster:
- **F-bloat**: AGENT.md ships into every session's system prompt via deployed copies (846 lines / 46KB / 41% over the 600-line warning threshold). Multiple oversized sections are conditional ("when editing docs", "on session end", "during fresh installation") but always loaded. Three HIGH-confidence hoist candidates (SESSION CLEANUP, LINK DON'T DUPLICATE, DIRECTORY STRUCTURE) clear ~180 lines without information loss.
- **F-gap**: `magpie4_reference.md` was deployed 2026-05-24 as the magpie4 helper, but the workflow scaffolding around it was never updated. magpie4 surfaces ONLY in the auto-load trigger table (line 437). Missing from FIVE scaffold sections: MANDATORY WORKFLOW Step 1, QUICK MODULE FINDER, QUALITY GUARD (no magpie4 bug class), DOCUMENT HIERARCHY (no output-interpretation reading branch), QUICK RESPONSE CHECKLIST (no magpie4 source-cite check). PREPROC layer has the same gap in QUICK MODULE FINDER and QUICK RESPONSE CHECKLIST. Also 4 MEDIUM-severity overly-broad triggers ('GAMS', bare 'modify', bare 'water', bare 'scenario') burn ~5KB of helper load per session unnecessarily.

**Findings**: L7-1 (846/46KB bloat), L7-2 (magpie4 missing from 5 scaffold sections — broader than the original anchor stated), L7-3 (GAMS trigger overly broad), L7-4 (modify trigger overly broad), L7-5 (water trigger overly broad), L7-6 (scenario trigger overly broad), L7-7 (Twin-agent disambiguation 26 lines), L7-8 (COMPLETE DOCUMENTATION STRUCTURE 55 lines redundant inventory), L7-9 (LINK DON'T DUPLICATE 80 lines), L7-10 (SESSION CLEANUP 55 lines), L7-11 (DIRECTORY STRUCTURE 46 lines), L7-12 (QUALITY GUARD missing magpie4 row), L7-13 (QUICK MODULE FINDER missing R/preproc layers), L7-14 (QUICK RESPONSE CHECKLIST missing magpie4/preproc checks), L7-15 (DOCUMENT HIERARCHY missing output-interpretation branch), L7-16 (Auto-Loading table needs new rows after hoisting).

**Proposed intervention** (partially resolves **Standing Decision (v)** indirectly — broader audit infrastructure decisions deferred to Phase 4):
- (F1) Hoist 3 sections to dedicated helpers (~180 lines saved):
  - SESSION CLEANUP (L122-176) → `agent/helpers/session_cleanup.md`. Reconcile with the `session-close` skill — pick one canonical source.
  - LINK DON'T DUPLICATE (L721-800) → `agent/helpers/link_dont_duplicate.md`. Auto-load triggers: "update doc", "edit module_XX.md", "doc edit".
  - DIRECTORY STRUCTURE (L217-262) → trim to 8 lines (the AGENT.md vs ../AGENT.md vs ../CLAUDE.md + modules/ vs ../modules/ distinctions); hoist rest to `agent/helpers/directory_structure.md`.
- (F2) Add Auto-Loading table rows for new helpers (L7-16).
- (F3) Add magpie4 + preproc references to 5 scaffold sections:
  - MANDATORY WORKFLOW Step 1 (L282) — add "For report.mif / model-output-provenance questions, also check `agent/helpers/magpie4_reference.md`".
  - QUICK MODULE FINDER (L552) — add **Upstream (R preprocessing)** row + **Downstream (R reporting)** row.
  - QUALITY GUARD (L636) — add "magpie4 source-of-truth citations" to High-Risk content.
  - DOCUMENT HIERARCHY (L704) — insert third reading-order branch for output-interpretation.
  - QUICK RESPONSE CHECKLIST (L815) — add 2 items for magpie4-source-cite and input-data routing.
- (F4) Tighten 4 broad triggers (replace bare 'GAMS' with 'equations.gms / =e=/=l=/=g= / q<N>_ / GAMS syntax'; replace bare 'modify' with 'is it safe to modify / what will break / impact of changing'; replace bare 'water' with 'water scarcity / water constraint'; replace bare 'scenario' with 'create scenario / design scenario / combine policies').
- (F5) Optional: hoist Twin-agent disambiguation (L25-50) and trim COMPLETE DOCUMENTATION STRUCTURE (L483-537). ~67 additional lines. Both are MEDIUM-severity and can be deferred.

**Effort**: 4-5h (F1 hoists are most of the work; F3 is mechanical). **Risk**: medium (touches the most-loaded surface in the agent; need to re-deploy AGENT.md to both parent copies and verify byte-identical post-deploy, and update Auto-Loading table without breaking existing trigger patterns). **Order**: can parallelize with A/B/C/D/E but **the deploy step (`cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md`) must happen LAST in 0g** so the trimmed version ships clean.

### Cluster G — "Reference-graph integrity: hub asymmetry + pointer-to-nonexistent + subordinate-README inventory drift" (~5 findings)

**Root cause**: high in-degree targets (CURRENT_STATE.json, AGENT.md, the 4 cross_module conservation docs, Tool_Usage_Patterns.md, maintenance_protocol.md, verifiers.md) carry **no self-marker of their hub status**. A future agent editing has no in-doc warning about blast radius. Two sub-defects:
- (G-pointer) `AGENT.md:479` + `helpers/README.md:90` both route to a `## Requested Helpers` section that has never existed in helpers/README.md.
- (G-subordinate-inventory) R3 fixed a duplicate routing table in helpers/README.md to defer to AGENT.md (the single source). But the SAME root cause has re-emerged at helpers/README.md L25 (prose list, missing magpie4_reference added 2026-05-24) and project/README.md L10/75 (`audit/ — User feedback system`, stale concept since 2026-05-24 /feedback removal).
- (G-internal) `AGENT.md:300` self-internal pointer to "Auto-Loading Helpers section" — actual section is "Auto-Loading Context Helpers" (L412); badge definitions are in the "Sync freshness badges" subsection (L445).
- (G-self-deposed) `audit/magpie4_scaffolding_plan.md:8` says "§22 is wrong, see helper" but §22 (L18, L27) still contains the original "108 unique report* functions" claim unchanged.
- (G-stale-status) `modules/README.md:147-156` "Next Steps" section says "Current Focus: Phase 2 - Cross-Module Analysis" — Phase 2 was completed 2025-10-22.

**Findings**: L6-6 (pointer to nonexistent ## Requested Helpers), L6-7 (AGENT.md self-internal pointer), L6-8 (bootstrap "6 command files" — same as C3 in Cluster E; cross-listed), L6-11 (helpers/README.md prose list missing magpie4_reference), L6-12 (magpie4_scaffolding_plan §22 self-deposed but not removed), L6-13 (modules/README.md Phase 2 stale), L6-14 (R3 subordinate-README pattern resurfaced — class-level finding), L6-16 (hub back-reference asymmetry — meta finding).

**Proposed intervention**:
- (G1) **Class-level rule** (add to `maintenance_protocol.md`): "Subordinate READMEs MUST NOT include inventories (helper lists, command lists, file lists) that are maintained elsewhere — only pointers. Prose summaries are exempt only if they explicitly cite the canonical source by name on the same line."
- (G2) Audit all `*README.md` files for inventory re-occurrences; fix the helpers/README.md L25 list and project/README.md L10/75 concept names.
- (G3) Fix the 4 specific pointer bugs: add empty `## Requested Helpers` section to helpers/README.md (or remove the convention from AGENT.md); correct AGENT.md:300 section name; either strikethrough or replace text in magpie4_scaffolding_plan.md §22; replace modules/README.md "Next Steps" with completion note.
- (G4) Add a uniform "Hub status: referenced from N+ pointers; if you change names/conventions/counts here, audit the dependents listed in `audit/pointer_graph.json`" footer to high-in-degree files. (Optionally build `pointer_graph.json` extraction into `scripts/refresh_aggregate_counts.py`.)

**Effort**: 1.5h for G1-G3; G4 is +2h if `pointer_graph.json` is automated. **Risk**: low. **Order**: parallelize with B/C/D/E.

### Cluster H — "Dead conventions: hollow automation claims + unenforced trigger thresholds + un-rotated ledgers" (~5 findings)

**Root cause**: documented automation that doesn't actually run, or rules whose triggers have never fired.
- (H-Layer-1) `maintenance_protocol.md` declares Layer 1 syntactic validation "automated, every session" — `session_startup.md` doesn't invoke `validate_consistency.sh`.
- (H-promotion) helpers/README.md "When N ≥ 5, scan for promotion candidates" — no helper has ever had ≥5 entries.
- (H-ledger) `audit/probe_dedup_ledger.json` `rotation_policy` references "next round R22"; current is R24, never auto-incremented. Script `probe_dedup_check.py` exists but isn't part of `/validate-semantic` post-processing.
- (H-readme-don't-read) AGENT.md:713-714 says "DO NOT read README.md" while README.md:174,303 says "Read this README first" as Step 1 of orientation — direct contradiction.
- (H-verifiers-header) `verifiers.md` lacks the `Last updated` / `Lessons count` header fields the README template prescribes (also under Cluster C as C3).

**Findings**: L2-3 (Layer 1 automation hollow), L2-4 (README don't-read contradiction), L2-5 (promotion threshold dead), L2-9 (probe_dedup_ledger un-rotated), L2-10 (verifiers.md missing template fields — also Cluster C).

**Proposed intervention**: per-rule choice between "wire up the automation" and "downgrade the language":
- (H1) Layer 1: either add `bash scripts/validate_consistency.sh` to `session_startup.md` Step 6, OR downgrade the cadence text from "automated, every session" to "run manually after any doc edit; auto-run via `/validate`". **Recommendation**: wire it up (cost ~2 min/session, value is real).
- (H2) Promotion threshold: lower from 5 to 2 (achievable), OR downgrade prescriptive language to descriptive.
- (H3) probe_dedup_ledger: wire `probe_dedup_check.py` into post-`/validate-semantic` hook; have it auto-append new round names and increment retirement_eligible_after.
- (H4) README don't-read contradiction: edit `README.md` to acknowledge it is documentation-project-only and remove the "Read this README" instruction from orientation; OR remove the AGENT.md "DO NOT read README" rule.
- (H5) Add Last-updated + Lessons-count headers to `verifiers.md` (Cluster C — bundle).

**Effort**: 1.5h. **Risk**: low. **Order**: after E (some of H is downstream of the count-marker work).

---

## Recurring classes (candidates for mechanization)

Per `[[template_verifier_mandate_flywheel]]`: closing classes via a new validator check binds the rule and prevents silent re-occurrence. R6's clusters surface 3 mechanizable classes:

| Recurring class | Cluster | Mechanization candidate |
|---|---|---|
| Hardcoded counts drift | E | Extend `<!--count:foo-->N<!--/count-->` marker + `refresh_aggregate_counts.py` TARGET_FILES (precedent: R5 Cluster A had the same recurring class on GAMS-side counts) |
| Static "Last updated" dates drift | B | Either drop convention (preferred), or pre-commit hook bumps automatically |
| Subordinate-README inventory drift (R3 fix resurfaced) | G | Class-level rule in `maintenance_protocol.md` + audit script that flags inventory tables outside their canonical source |

---

## Standing-decision triage

The plan (`audit/get_under_control_plan.md` §"Standing-decision triage") named 5 decisions waiting on Phase 0 data. R6 data resolves 4 of them (i-iv); (v) remains intentionally deferred to Phase 4 design.

### (i) `project/CURRENT_STATE.json` — retire or revive?

**Recommendation: RETIRE.**

**Rationale (R6 data)**: 5 lenses corroborated that the SSOT convention is dead (Cluster A, finding C1). The state-tracking surface migrated to `audit/*.json` + commit log + `audit/global/agent_lessons.md` and that distributed surface is alive (8038db096 R3 work, 49 commits since 2026-03-07, 24 validation rounds, 5 pipeline audits). Reviving would mean wiring 5+ auto-bump paths from disparate sources, vs. retiring which is 5-pointer-replacement work. The user's own plan preamble also recommends retire. The release.highlights block (10 helpers / 6 commands / 13-round) is stale enough to mislead. Solution: archive as v1.0 snapshot OR demote with a single-line header banner; replace the 5 pointers with the actual state-tracking destinations.

### (ii) `reference/dependency_analysis/` — regenerate, mark snapshot, or delete?

**Recommendation: MARK AS OCT-2025 SNAPSHOT (don't delete, don't regenerate now).**

**Rationale (R6 data)**: L1-5 found EXECUTIVE_SUMMARY.md has been semantically edited since its 2025-10-10 header (a 2026-04-20 rename insert at line 180 — `im_growing_stock` renamed from `pm_timber_yield`). The half-updated state is the problem; the existence of the snapshot is fine. Content (`*.dot`, `*.csv`, `dependency_report.txt`, JSON, raw tarball) is a structural snapshot and re-running the analysis is a separate ~4-8h initiative (the user's plan mentioned this). Reverting the April 2026 insert + adding a "Post-snapshot updates" addendum is the cheapest correct move. Marker-as-snapshot also resolves the L6-2-class hub-asymmetry by demoting it from "authoritative" to "snapshot".

**Cost of regenerate**: significant — would need to re-run dependency extraction against current MAgPIE develop (49 commits since the snapshot include renames per `sync_log.json`). Defer to a separate initiative.

**Cost of delete**: low (108KB of files), but the snapshot has historical value — the `.dot` files are reproducible only by re-running the analysis. Don't lose them.

### (iii) `audit/archive/` + `reference/archive/` — keep for history or delete?

**Recommendation: KEEP (with disclaimers already in place).**

**Rationale (R6 data)**: L3 explicitly notes "archives are properly disclaimed" — `audit/archive/` (12 files, ~108KB, documents the removed `/feedback` workflow) and `reference/archive/` (3 files, ~64KB, AI_Instruction_Refinement_Plan + GAMS_Programming_Reference_Plan + a phase-1 completion record) both have README disclaimers (verified during read-only inspection). No live references into either. Storage cost is ~170KB total. R5 Cluster K considered the same question and recommended either delete-or-disclaim; disclaim is already done. **Status quo wins** — these are git-history-redundant but cheap, and the disclaimers prevent stale-routing.

### (iv) `module_XX_notes.md` pattern — keep sidecar (prune empties) + promote ~3-5 load-bearing warnings, OR fold all warnings into main docs?

**Recommendation: KEEP SIDECAR; DELETE THE 8 EMPTIES; BACKFILL 3 (M10, M56, M70) FROM VALIDATION ROUNDS.**

**Rationale (R6 data)**: L3-1 confirmed 8 of 18 notes files are 52-word stubs for high-centrality modules. The sidecar pattern works for the 10 modules that HAVE non-trivial notes (warnings + lessons + examples format is good). The failure is "scaffold before content exists" — the cure is deletion of empties, not abandonment of pattern. Folding all warnings into main docs would (a) bloat 10 already-large module_XX.md files, (b) lose the user-feedback signal that "this is what real users hit, not what the spec says", and (c) require touching every notes-reading code path. Cheaper to keep the sidecar + use absence-of-file as the signal.

**Why 3 (M10, M56, M70) for promotion**: validation_rounds.json has multiple R-series findings against each (M10 cropland-vs-land-area boundaries, M56 GHG-pricing default semantics + Tg/Mg unit drift, M70 livestock feed basket realization drift). These are the modules where users have actually hit issues that recur — backfill is high-value.

### (v) Phase 4 scope — full GitHub Actions CI for 5c, or local pre-merge hook?

**Recommendation: DEFER TO PHASE 4 DESIGN (no R6 data informs this decision).**

**Rationale**: R6 was scoped to doc-surface drift, not CI infrastructure. None of the 58 findings touch the 5c/PR-time-prevention surface. The decision turns on: (a) MAgPIE's existing CI infrastructure access patterns, (b) whether agent fixes should auto-PR-create or comment-only, (c) cost calculus for GH Actions runtime vs. local hook complexity. These are Phase 4 questions; R6 has nothing to say.

---

## Recommended ordering for 0f-0g (the fix phase)

Per [[feedback_synthetic_interventions]]: K=8 interventions for N=58 findings. Ordering takes account of (a) blocking dependencies, (b) security urgency, (c) parallelization opportunity.

| Step | Cluster | Effort | Risk | Blocking? |
|---|---|---|---|---|
| **0f-1** | **D (gitignore + script CWD fix + .bak delete + script move)** | 1h | Low | **HIGHEST URGENCY — closes parent-repo security exposure FIRST** |
| **0f-2** | A (retire CURRENT_STATE.json as SSOT; move sync_log.json to audit/) | 1.5h | Low | Blocks B & E (reduces pointer graph to audit) |
| **0f-3** | C (delete 8 empty notes; backfill M10/M56/M70; fix verifiers.md header) | 1.5h | Low | Independent |
| **0f-4** | B (drop static Last-updated convention; sweep 30 files; add Hub status footer to high-in-degree files) | 2h | Low | After A |
| **0f-5** | G (class-level inventory rule + 4 specific pointer bugs) | 1.5h | Low | Independent (parallelize with B) |
| **0f-6** | H (wire Layer 1 validator; lower promotion threshold to 2; wire probe_dedup_check post-validate-semantic; fix README don't-read contradiction) | 1.5h | Low | After E (some H is count-marker-downstream) |
| **0f-7** | E (extend marker mechanism + TARGET_FILES; dynamic multi-realization instruction; reconcile lens count) | 2.5h | Low | After A, B |
| **0g** | F (AGENT.md hoists + magpie4/preproc scaffold inserts + 4 trigger tightenings + deploy to both parent copies + verify byte-identical) | 4-5h | Medium | **LAST** (the deploy step ships the trimmed version) |

**Total effort**: ~15-17h of focused work. Original plan estimate was 6-8h for Phase 0 fix phase — R6's broader-than-anticipated find ratio (58 dedup, 16 HIGH) bumps this. Recommend splitting across 2 sessions: 0f-1 through 0f-4 in session 1 (~6h), 0f-5 through 0g in session 2 (~10h). Re-validate + record R6 in pipeline_audit_rounds.json after 0g.

**Parallelization**: 0f-3, 0f-4, 0f-5 can run in parallel sub-tasks within a single session. 0f-1 must run FIRST. 0g must run LAST. Everything else has clear dependency graph.

---

## Discovered-during-synthesis meta-findings

Only logging HIGH-confidence reproducible items the 7 lenses did not catch.

### Meta-finding 1: refresh_aggregate_counts.py TARGET_FILES is incomplete in 3 places, not just 2

**Severity**: MEDIUM (mechanically supports Cluster E)

L4 flagged that README.md is missing from `scripts/refresh_aggregate_counts.py:TARGET_FILES` (verified by reading the script — TARGET_FILES contains 8 entries: AGENT.md, 4 commands files, 2 helpers, 1 core_docs). L4 also noted bootstrap.md needs addition. Reading the script directly, I confirm a THIRD missing file: `agent/helpers/realization_selection.md` carries a "75 active realizations" count (L4-5) and is also absent from TARGET_FILES. So the Cluster E intervention should add **3 files** to TARGET_FILES, not 2: README.md + bootstrap.md + realization_selection.md (plus `circular_dependency_resolution.md` for the 26/26+ fix per L4-7).

**Source**: `scripts/refresh_aggregate_counts.py:14-22` (read directly during synthesis to verify L4's claim).

---

## Open questions for the user (synthesis flagged but cannot resolve from data alone)

1. **Cluster B intervention choice (B1 vs B2)**: drop the "Last updated" convention entirely, or keep + pre-commit hook? Both work; B1 is simpler, B2 preserves the human-readable signal. **My recommendation**: B1, but you may prefer the auditable header. **What I'd update on**: if you've ever caught a real bug by reading a "Last updated" field in a code review.

2. **Cluster F session_cleanup reconciliation**: AGENT.md's SESSION CLEANUP section (55 lines) overlaps with the `session-close` skill — which one is canonical going forward? **My recommendation**: keep the `session-close` skill (it's already running as your end-of-session hook per global CLAUDE.md), and replace the SESSION CLEANUP section in AGENT.md with a 5-line pointer. **What I'd update on**: whether you want the agent to fall back to manual git commands if the skill isn't loaded (in which case the AGENT.md section should be condensed-but-kept rather than replaced).

3. **Cluster H choice for Layer 1 validator (H1)**: wire `validate_consistency.sh` into `session_startup.md` (~2 min/session cost) vs. downgrade the "automated, every session" language to "manual after doc edit"? **My recommendation**: wire it up — the value is real (catches regressions before they ship in a session). **What I'd update on**: if `session_startup.md`'s wall-time budget is already tight.

4. **Cluster G hub back-reference (G4)**: build `audit/pointer_graph.json` extraction into `refresh_aggregate_counts.py` (+2h work to support the "Hub status" footer)? Or skip the automation and just hand-write the footer on the 7-8 hub files? **My recommendation**: hand-write for now; revisit automation in Phase 4 if the hub-asymmetry pattern recurs.

5. **Cluster E lens count canonicalization (E4)**: is the 7-lens split the new pipeline-audit default, or a per-round override only for R6 (Stale-and-Remnant)? The R6 design doc explicitly says "7 lenses (not 6)" but `pipeline-audit.md` still hardcodes 6. **My recommendation**: keep 6 as canonical for the standard "doc↔code drift" audit; document R6's 7-lens split as a per-round override pattern (variable lens design is a feature, not drift). **What I'd update on**: if you intend to run more "Stale-and-Remnant"-class audits regularly.

---

## Logging

Round entry appended to `audit/pipeline_audit_rounds.json` (schema mirrors R5).
This report: `audit/pipeline_audit_round6.md`.

**Triage status**: 8 root-cause clusters, 5 standing decisions resolved with recommendations (i-iv), 5 open questions flagged for user. **Fix phase 0f-0g awaits user decisions before execution.**
