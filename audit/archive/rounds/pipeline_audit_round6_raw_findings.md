# Pipeline Audit — Round 6 (R6) Raw Findings

**Date**: 2026-05-25
**Round type**: Doc-surface drift audit (Stale and Remnant)
**Lens count**: 7 (L1-L7) — see `audit/pipeline_audit_round6_design.md` for prompts
**Auditor**: 7 parallel `claude-opus-4-7` sub-agents
**Status**: raw findings before synthesis (0d pending)

---

## Topline

| Lens | Findings | Headline |
|---|---|---|
| L1 — Staleness | 8 | CURRENT_STATE.json + 7 helpers/docs with stale `Last updated` headers while mtime is fresh |
| L2 — Dead conventions | 11 | "all updates go in CURRENT_STATE.json" + 10 other unfollowed rules including "Layer 1 syntactic validation runs every session" |
| L3 — Half-deployed patterns | 3 | 8/18 empty `module_XX_notes.md` (52-word scaffolds) + 6 helpers with stalled `Lessons Learned` sections |
| L4 — Cross-doc inconsistency | 7 | ~290K vs ~342K vs actual 347K words; bootstrap.md "6 command files" vs actual 10; schema v1.1 vs v1.2 |
| L5 — Misplaced outputs | 7 | validation_report_*.txt in parent + same defect class in current script + parent .gitignore exposure risk |
| L6 — Reference-graph integrity | 15 | 5 READMEs → stale SSOT; 8+ pointers → stale cross_module/ from 2025-10-22; pointer to nonexistent `## Requested Helpers` section |
| L7 — Surface bloat + workflow gaps | 19 | AGENT.md 846/46KB confirmed; magpie4 missing from 5 workflow-scaffold sections (not just 1); 3 HIGH hoist candidates would save ~180 lines |
| **Total** | **70** | |

**Severity rollup** (approximate — synthesis will normalize):
- CRITICAL: 0
- HIGH: 13
- MEDIUM: 28
- LOW: 29

**Cross-lens overlaps** (expected — L1 finds stale targets, L6 finds pointers to them):
- CURRENT_STATE.json appears in L1, L2, L4, L6 (4 lenses)
- cross_module/* 2025-10-22 footers appear in L1, L6 (2 lenses)
- bootstrap.md "6 command files" appears in L2, L4, L6 (3 lenses)
- magpie4 workflow gaps appear in L7 only (no overlap — L7 owns)
- AGENT.md size appears in L7 only (no overlap — L7 owns)

---

## L1 — Staleness (currency claims vs actual content age)

**Agent summary**: L1 lens shows a real pattern, not just the anchor. CURRENT_STATE.json is the headline finding (HIGH): self-labeled SSOT, 79 days unbumped, multiple May 2026 events not reflected. The pattern repeats across helpers (8 files with 80-day-old "Last updated" claims despite May 2026 mtime touches, plus 3 helpers carrying physically-impossible 2025-07-15/18 dates ~311 days old), cross_module conservation footers (Oct-22 claims with May-24 edits), Tool_Usage_Patterns.md (Nov-29 claim, multiple May edits), and EXECUTIVE_SUMMARY.md (Oct-10 header with April-2026 in-body insert). AGENT.md is itself missing a Last-updated signal entirely.

Root pattern: header "Last updated" fields are treated as text-to-write-once rather than fields-to-maintain. mtime-fresh files are the rule (touched by sweeping renames/migrations) but content-fresh is rare; the eye is drawn to the stale claim, not the mtime. Recommended single fix: drop static date fields and standardize on `git log -1` for last-semantic-edit, or add a pre-commit hook that bumps them whenever the file's body changes.

```json
[
  {
    "lens": "L1",
    "location": "project/CURRENT_STATE.json:5",
    "failure_mode": "ANCHOR. File self-declares as '🚨 THE SINGLE SOURCE OF TRUTH FOR ALL PROJECT STATUS 🚨' (line 2) and the instructions field says 'Update this file after completing work' (line 3), but last_updated='2026-03-07' (line 5) — 79 days before today (2026-05-25). File mtime is 2026-05-24 (fresh) because the audit/ rename touched it, but content has NOT been semantically updated. Recent activity NOT reflected: /feedback machinery removal (327116c, 2026-05-24); feedback/ → audit/ rename (1c7df77, 2026-05-24); R23 + R24 validation rounds; pipeline_audit rounds R1-R5 (2026-05-23 to 2026-05-24); magpie4 lean-scaffolding initiative (d44823f, 2026-05-24). The known_issues array (lines 69-73) does NOT mention CURRENT_STATE.json's own staleness as an issue. The release.highlights claim (lines 132-141) is also stale: '6 slash commands' but actual count is 10; '10 auto-loading context helpers' but actual count is 14; '32-check syntactic validator' but AGENT.md uses live placeholders showing 25 main / 40 sub-checks. These are arguably v1.0.0-frozen but presented in the JSON without a 'release_snapshot' label so a reader treats them as current. mtime-fresh ≠ content-fresh.",
    "severity": "HIGH",
    "evidence": "stat -f '%Sm' -t '%Y-%m-%d' project/CURRENT_STATE.json → 2026-05-24; jq '.last_updated' project/CURRENT_STATE.json → '2026-03-07'; (today - 2026-03-07) = 79 days. Cross-check: AGENT.md line 328 says 24 validation rounds / 474 bugs; CURRENT_STATE.json audit_angles totals = ~212 bugs. Release-highlights drift: ls agent/commands/*.md | wc -l = 10 (JSON line 139 claims 6); ls agent/helpers/*.md | grep -v README | wc -l = 14 (JSON line 138 claims 10).",
    "suggested_fix": "Two-part fix. (a) Refresh CURRENT_STATE.json content: bump last_updated to today, replace current_phase with the actual current state (post-Phase-4: R23/R24 audits done, /feedback removed, audit/ rename done, magpie4 scaffolding live, R6 pipeline audit in flight), refresh known_issues, update audit_angles counts from validation_rounds.json's cumulative_stats. (b) Either move the release.highlights block to a separate 'release_history' array clearly labelled as v1.0.0-frozen snapshot, OR refresh those numbers to current state. Add a self-audit hook (e.g. session-close skill check) that warns when last_updated > 30 days old.",
    "confidence": "HIGH"
  },
  {
    "lens": "L1",
    "location": "agent/helpers/adding_new_scenario.md:4",
    "failure_mode": "Header claims 'Last updated: 2025-07-15' but the file's first-and-only git commit is 2026-03-07 (commit e1017b4). The 2025-07-15 date is physically impossible relative to the file's existence (~8 months before it was created). Mtime is 2026-05-24 (touched by the feedback/→audit/ rename sweep). Same pattern in comparing_model_runs.md:4 ('2025-07-18', first commit 2026-03-07) and water_scarcity_scenarios.md:4 ('2025-07-18', first commit 2026-03-07).",
    "severity": "MEDIUM",
    "evidence": "git log --format='%ad' --date=short -- agent/helpers/adding_new_scenario.md → 2026-03-07 (single entry); head -5 of file → '**Last updated**: 2025-07-15'; v1.0.0 tag is 2026-03-07.",
    "suggested_fix": "Bulk-correct the three impossibly-old dates in helpers (adding_new_scenario, comparing_model_runs, water_scarcity_scenarios) to either (a) their actual creation date 2026-03-07, or (b) the date of last semantic content change. Treat header 'Last updated' as a discipline issue: either auto-bump via a pre-commit hook on the helpers dir, or drop the field and rely on `git log -1 --format='%ad'`.",
    "confidence": "HIGH"
  },
  {
    "lens": "L1",
    "location": "agent/helpers/water_scarcity_scenarios.md:4",
    "failure_mode": "Header 'Last updated: 2025-07-18' but actually edited 2026-05-24 (commit e982a76 'infra(Phase 2 prep): migrate bare-basename cites + Check 25'). Same pattern as adding_new_scenario.md but more egregious because content actually changed in May and the date was not bumped.",
    "severity": "MEDIUM",
    "evidence": "git log --format='%ad %h' --date=short -- agent/helpers/water_scarcity_scenarios.md → 2026-05-24 e982a76 + 2026-03-07 e1017b4; head -5 of file → '**Last updated**: 2025-07-18'.",
    "suggested_fix": "Same bulk-correction as above. Policy: any commit that modifies a helper file MUST bump its Last updated header. Either policy or pre-commit hook.",
    "confidence": "HIGH"
  },
  {
    "lens": "L1",
    "location": "agent/helpers/scenario_carbon_pricing.md:4, scenario_diet_change.md:4, debugging_infeasibility.md:4, interpreting_outputs.md:4, adding_new_crop.md:4, session_startup.md:4, modification_impact_analysis.md:4 (all '2026-03-06'); maintenance_protocol.md:4 ('2026-03-07')",
    "failure_mode": "Eight helpers carry header dates ~80 days old. mtimes are all 2026-05-24 because the feedback/→audit/ rename sed-swept these files; that was a mechanical change. The Lessons Learned sections are static; each carries 'Lessons count: N entries' from March values, with no entries added since despite 11 weeks of validation activity (R14–R24). Either (a) the Lessons-Learned feedback loop is broken, or (b) lessons are being added elsewhere (audit/global/agent_lessons.md). Either way the 'Last updated' field misleads about helper currency.",
    "severity": "MEDIUM",
    "evidence": "for f in agent/helpers/*.md; do grep -H 'Last updated' $f; done shows 8 helpers stuck at 2026-03-06/07; git log --since=2026-03-08 shows commits in May (1c7df77, e982a76) that modified content; Lessons count in headers all match pre-March-7 values.",
    "suggested_fix": "Decide whether 'Last updated' tracks (a) semantic-content change only — current dates are arguably correct and Lessons Learned dead-loop is the real finding, or (b) any-touch, in which case bump via hook. Prefer (a) but add a 'Last semantic edit' label and verify the lesson-capture path is alive.",
    "confidence": "HIGH"
  },
  {
    "lens": "L1",
    "location": "reference/dependency_analysis/EXECUTIVE_SUMMARY.md:3",
    "failure_mode": "Document header: 'Analysis Date: 2025-10-10' (~227 days old) and 'MAgPIE Version: develop branch (commit beb125fe0)'. Honest snapshot per L1 rules — BUT line 180 of the same EXECUTIVE_SUMMARY has a 2026-04-20 insert ('im_growing_stock — Forest productivity (14 → 32, 35; renamed 2026-04-20 from pm_timber_yield in PR #869...)'), proving the document HAS been semantically edited since the 2025-10-10 header date claim. mtime is 2026-05-24. Half-updated currency: header still claims Oct-10 even though body has post-header inserts dated April 2026.",
    "severity": "MEDIUM",
    "evidence": "head -3 reference/dependency_analysis/EXECUTIVE_SUMMARY.md → 'Analysis Date: 2025-10-10'; grep -n '2026-04-20' → line 180; stat → mtime 2026-05-24. Supporting .dot/.txt files mostly carry Oct-10 2025 mtimes (genuine Oct snapshots).",
    "suggested_fix": "Either (a) make the snapshot honestly Oct-10 only: revert the April 2026 in-body insert and put rename-aware content in a 'Post-snapshot updates' addendum, or (b) re-run the analysis and replace EXECUTIVE_SUMMARY with a current snapshot — preferred. The dependency model has churned per sync_log (49-commit sync in Apr/May with renames).",
    "confidence": "HIGH"
  },
  {
    "lens": "L1",
    "location": "core_docs/Tool_Usage_Patterns.md:5",
    "failure_mode": "Header 'Last Updated: 2025-11-29' (~177 days old). File has been modified since (commits e982a76 on 2026-05-24 'infra(Phase 2 prep): migrate bare-basename cites + Check 25' and 1c7df77 on 2026-05-24 'rename: feedback/ -> audit/'). At minimum a path migration and a rename sweep changed content. Same pattern as the helpers.",
    "severity": "MEDIUM",
    "evidence": "head -10 core_docs/Tool_Usage_Patterns.md → '**Last Updated**: 2025-11-29'; git log --format='%ad %s' --date=short -- core_docs/Tool_Usage_Patterns.md → 2026-05-24 (rename), 2026-05-24 (Phase 2 prep), 2026-03-06 (genericize paths).",
    "suggested_fix": "Either bump to a date that reflects the substantive 2026-03-06 'genericize user-specific paths' edit (last real content change), or drop the field. The Nov-2025 date is dishonestly old.",
    "confidence": "HIGH"
  },
  {
    "lens": "L1",
    "location": "cross_module/water_balance_conservation.md:972, cross_module/carbon_balance_conservation.md:977, cross_module/land_balance_conservation.md:822",
    "failure_mode": "All three carry footer 'Last Updated: 2025-10-22' (~215 days old). All three modified subsequently — land_balance_conservation.md as recently as 2026-05-24 (e982a76 + 1c7df77), carbon_balance_conservation.md on 2026-05-24 (e385758 'infra(Phase 3): opportunistic cleanup' + e982a76), water_balance_conservation.md on 2026-05-24 (e982a76). The Phase 3 cleanup commit (e385758) for carbon was substantive.",
    "severity": "MEDIUM",
    "evidence": "grep -n 'Last Updated' cross_module/*.md → all 2025-10-22; git log -2 --format='%ad %h %s' --date=short -- cross_module/carbon_balance_conservation.md → 2026-05-24 e982a76 / 2026-05-24 e385758 (Phase 3 cleanup).",
    "suggested_fix": "Bump footers to reflect each file's last semantic content commit. Better: replace static date with `git log -1 --format=%ad -- <file>` (would need a build step) or drop the static date field entirely.",
    "confidence": "HIGH"
  },
  {
    "lens": "L1",
    "location": "AGENT.md (entire file, no 'Last updated' footer)",
    "failure_mode": "AGENT.md is the single most important file in the agent (it's the SSOT for agent behavior). It carries NO Last updated footer despite project conventions in other helpers/docs. The note at the bottom of ~/.claude/CLAUDE.md has '*Last updated: 2026-05-15*' — that convention does not propagate to AGENT.md. Risk: reader cannot tell which behavioral rules are current.",
    "severity": "LOW",
    "evidence": "grep -n 'last.updated\\|^\\*Last updated' AGENT.md → no matches; tail -30 AGENT.md → no footer. mtime: 2026-05-24. Other key docs all carry Last Updated footers; AGENT.md is the odd one out.",
    "suggested_fix": "Add a footer 'Last semantic edit: <date>' bumped whenever non-mechanical changes land. Alternative: instruct readers to use `git log -1 --format=%ad -- AGENT.md` and remove footer dates everywhere (no-static-dates policy).",
    "confidence": "MEDIUM"
  }
]
```

---

## L2 — Dead conventions (documented rules nobody follows)

**Agent summary**: Found 11 dead-convention findings ranging from the anchor (CURRENT_STATE.json SSOT rule dead since 2026-03-07, repeated across 4 files) to smaller drift (bootstrap.md "6 command files" actually 10, pipeline-audit.md "6 lenses" actually 7 in R6, verifiers.md missing template fields). Two HIGH-severity rules beyond the anchor: (a) maintenance_protocol.md's "Layer 1 syntactic validation runs automatically every session" — session_startup.md never invokes the validator, and (b) AGENT.md's list of "modules with multiple realizations" omits 18 of the 40 actual cases including hubs (10, 14, 52, 56) where Step 1c is most needed.

Pattern: bottom-up state-tracking artifacts (audit/validation_rounds.json, sync_log.json, audit/global/agent_lessons.md, commit messages) are alive and actively maintained, while top-down convention docs (README cluster, CURRENT_STATE.json, project/README.md, hardcoded counts) are dead.

```json
[
  {
    "lens": "L2",
    "location": "README.md:21-23, 254-266, 376-398; project/CURRENT_STATE.json:3; project/README.md:18-25, 58, 82-83; modules/README.md:3-5, 18-20, 162; AGENT.md:111, 117",
    "failure_mode": "DEAD CONVENTION (anchor — repeats across 4 files): 'All updates go in project/CURRENT_STATE.json' / 'project/CURRENT_STATE.json is the SINGLE source of truth' / 'After EVERY session, update project/CURRENT_STATE.json'. Practice: CURRENT_STATE.json has not been touched since 2026-03-07. 47+ commits since then have happened; status tracking moved to audit/*.json and commit messages. The 'SSOT' framing is contradicted by reality — there are multiple living sources of truth (sync_log.json, validation_rounds.json, pipeline_audit_rounds.json, audit/global/agent_lessons.md) and one dead one (CURRENT_STATE.json).",
    "severity": "HIGH",
    "evidence": "git log --since=2026-01-01 -- project/CURRENT_STATE.json | head -5 → last commit 06746f4 2026-03-07. README.md:21 says 'CRITICAL: When working on the project, update ONLY project/CURRENT_STATE.json'; README.md:395 says 'After EVERY session: 1. Update project/CURRENT_STATE.json with ALL progress/plans/status'. Practice clearly shows this is not done.",
    "suggested_fix": "Either (a) honestly retire the CURRENT_STATE.json SSOT story across all four files — replace with a pointer to where status actually lives (audit/validation_rounds.json + audit/pipeline_audit_rounds.json + sync_log.json + audit/global/agent_lessons.md + commit log); or (b) actually update CURRENT_STATE.json at end of every multi-session initiative and reinstate the rule. The audit/get_under_control_plan.md already names this as a Phase 0 finding — choice (a) appears to be the de-facto convention.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "README.md:283-294",
    "failure_mode": "DEAD CONVENTION inside the anchor cluster: README.md Quick Quality Checklist last item is '[ ] Updated CURRENT_STATE.json'. Practice: 18+ module doc commits since 2026-04-01 (e.g., docs(m38) 4a07b88, docs(module_14) 9b58fa8, R3 cluster fixes ecad717/49cc6f0/ae3763f/7a0ab02, R24 audit fixes ad583d2) none of which touched CURRENT_STATE.json.",
    "severity": "MEDIUM",
    "evidence": "Read README.md:283-294 — last checkbox is 'Updated CURRENT_STATE.json'. git log --since=2026-04-01 -- modules/*.md | wc -l → 22 module-doc commits. git log --since=2026-04-01 -- project/CURRENT_STATE.json → 0 commits. Every single module-doc commit violated the rule.",
    "suggested_fix": "Remove the 'Updated CURRENT_STATE.json' line from the per-module Quick Quality Checklist (it conflates per-module work with project-level state-tracking). Replace with an item that reflects actual practice: '[ ] Ran scripts/validate_consistency.sh'.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "agent/helpers/maintenance_protocol.md:19-37 (Layer 1)",
    "failure_mode": "DEAD CONVENTION (recently broken): maintenance_protocol.md declares 'Layer 1 — Syntactic Validation (automated, every session)' with the cadence 'Run at session start if docs were modified in a previous session. Always run after any documentation edit.' Practice: the only file that runs at session start is session_startup.md, and it does NOT invoke scripts/validate_consistency.sh — it only references the validator in a table that prescribes when the user should run /validate manually (Step 6). 'Automated, every session' is therefore false.",
    "severity": "HIGH",
    "evidence": "Read agent/helpers/maintenance_protocol.md:19-23: 'Layer 1 — Syntactic Validation (automated, every session)'. Then: grep -n 'validate_consistency\\|/validate' agent/helpers/session_startup.md → only line 164 ('| Syntactic validator | ✅/❌ | Run /validate |') is a 'what to suggest if status is bad' table cell, NOT an automated execution step.",
    "suggested_fix": "Either (a) add an automated `bash scripts/validate_consistency.sh` call to session_startup.md Step 0/Step 6, or (b) downgrade the maintenance_protocol.md cadence text from 'automated, every session' to 'run manually after any doc edit; auto-run via /validate command'. (a) is preferable because the cost is small (~2 min) and the value is real for catching regressions.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "AGENT.md:713-714 (DO NOT read README) vs README.md:174 + README.md:303 (Read this README first)",
    "failure_mode": "DEAD CONVENTION via contradiction: AGENT.md explicitly tells the agent 'DO NOT read README.md, project/ directory (only for documentation project work)' — binding 'don't' aimed at the MAgPIE-question workflow. But README.md's session-protocol section instructs the agent to 'Read this README' as Step 1 of orientation. README.md is the document that contains the documentation-project-work rules — and AGENT.md tells the agent not to read it.",
    "severity": "MEDIUM",
    "evidence": "Read AGENT.md:713-714: '**DO NOT read** (noise for MAgPIE questions): ❌ README.md, project/ directory (only for documentation project work)'. Read README.md:172-180: '**Step 1: Orient (2 minutes)** 1. Read this README (you're doing it!) 2. Check project/CURRENT_STATE.json...'.",
    "suggested_fix": "Resolve the contradiction by editing README.md to acknowledge it is documentation-project-only and removing the 'Read this README' instruction from the orientation protocol — or move the project-work protocol entirely into project/README.md so the top-level README.md is purely external-facing.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "agent/helpers/README.md:77-83",
    "failure_mode": "DEAD CONVENTION (never enforced): 'Promoting Lessons: Trigger: When a helper's Lessons Learned section reaches 5+ entries, review them during the next session that loads the helper... When N ≥ 5, scan for promotion candidates before answering.' Practice: zero helpers have ≥5 entries (max is 2 for debugging_infeasibility and modification_impact_analysis, but most are 0-1), so the promotion mechanism has never been triggered.",
    "severity": "LOW",
    "evidence": "for f in agent/helpers/*.md; do grep 'Lessons count' \"$f\" | head -1; done → all helpers show 0-2 entries; max is 2. The threshold (5) was set at template creation but has never been hit.",
    "suggested_fix": "Either (a) lower the trigger threshold to 2 (achievable) so the promotion review actually fires, or (b) acknowledge the rule is aspirational and remove the prescriptive 'should check lesson count each time it loads a helper' language.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "agent/commands/bootstrap.md:110",
    "failure_mode": "DEAD CONVENTION: bootstrap.md verification step says 'Expected: AGENT.md deployed, 6 command files present'. Actual count is 10 command files. Anyone actually running this verification would see '10' and not know whether that's correct or a corruption.",
    "severity": "LOW",
    "evidence": "ls agent/commands/*.md | wc -l → 10. grep 'Expected:' agent/commands/bootstrap.md → 'Expected: AGENT.md deployed, 6 command files present'.",
    "suggested_fix": "Replace with a dynamic check or with a count-marker comment like `<!--count:command_files-->10<!--/count-->`. Or remove the count entirely and just say 'Expected: AGENT.md deployed, all command files in agent/commands/'.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "agent/commands/pipeline-audit.md:7 ('6 parallel Opus sub-agents'); :15 ('Why six lenses'); :25 ('## The six lenses'); :66 ('all 6 in parallel (single message, 6 tool calls)')",
    "failure_mode": "DEAD CONVENTION (this round itself violates it): pipeline-audit.md prescribes '6 parallel Opus sub-agents, one per lens' and lists 6 lenses. The current round (R6) is being run with 7 lenses (L1-L7). audit/pipeline_audit_round6_design.md acknowledges 7 lenses, but the command file still says 6. Also visible in AGENT.md Available Commands table (line 202).",
    "severity": "MEDIUM",
    "evidence": "Read agent/commands/pipeline-audit.md:7,15,25,66 — all say 'six lenses'. Read AGENT.md:202 — '(6 parallel Opus agents)'. The current pipeline_audit_round6_design.md uses 7 lenses (L1-L7).",
    "suggested_fix": "Update pipeline-audit.md and AGENT.md to either (a) say 'N lenses (current set listed in audit/pipeline_audit_round{N}_design.md)' to reflect that lens design varies by round, or (b) update the hardcoded '6' to '7' if the new lens set is the new standard. (a) is more robust.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "AGENT.md:323-324 ('Modules with multiple realizations (check these before answering): 13, 18, 21, 29, 30, 31, 34, 37, 38, 40, 41, 42, 44, 51, 53, 55, 58, 59, 60, 70, 71, 80') vs AGENT.md:305 ('20+ modules have them')",
    "failure_mode": "DEAD CONVENTION (rule prescribes a list that materially understates the truth): AGENT.md tells the agent to check active realization 'Before answering about any module with multiple realizations (20+ modules have them)' and gives a list of 22. Actual modules with multiple realizations: 40. Missing from the list: 09, 10, 12, 14, 15, 20, 22, 28, 32, 35, 39, 43, 50, 52, 56, 57, 62, 73. This includes critical hubs like 10_land, 14_yields, 52_carbon — exactly the high-centrality modules where Step 1c is most needed.",
    "severity": "HIGH",
    "evidence": "Listed in AGENT.md: 22 module numbers. Actual count: `for m in $(ls ../modules/ | grep -v include); do count=$(ls -d ../modules/$m/*/ 2>/dev/null | wc -l); if [ \"$count\" -gt 1 ]; then echo \"$m\"; fi; done | wc -l` → 40.",
    "suggested_fix": "Replace the static list with a dynamic instruction: 'Before answering about ANY module: check `ls ../modules/XX_*/` to see if there are >1 realizations. If yes, run Step 1c.' If a static list is preferred, regenerate from the bash one-liner above.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "audit/probe_dedup_ledger.json:14 (rotation_policy: 'next round R22')",
    "failure_mode": "DEAD CONVENTION (recently broken): probe_dedup_ledger.json's rotation_policy says 'Names appearing only in agent rule text... retire after current_round + 3 = 24 (since last round is R21, next round R22)'. Practice: rounds R22, R23, R24 have happened, but the ledger was last touched on 2026-05-24 only by the feedback→audit rename, no content change. The 'retirement_eligible_after' values were never incremented for R22/R23/R24 names.",
    "severity": "MEDIUM",
    "evidence": "git log -- audit/probe_dedup_ledger.json → only 1c7df77 2026-05-24 (rename commit). Read audit/probe_dedup_ledger.json:14: 'next round R22'. validation_rounds.json shows 24 rounds, most recent on 2026-05-24.",
    "suggested_fix": "Either (a) update the ledger after each round (add a probe_dedup_check.py step that auto-appends new names), or (b) downgrade the rotation_policy language from prescriptive to descriptive of intent. The scripts/probe_dedup_check.py exists but appears not to be called as part of /validate-semantic post-processing.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "agent/helpers/verifiers.md:1-7 (helper header missing template fields)",
    "failure_mode": "DEAD CONVENTION: agent/helpers/README.md:38-46 (Helper File Template) prescribes that every helper has '**Last updated**: [date]' and '**Lessons count**: [N entries]' header fields. Practice: verifiers.md has neither field. Hoisted 2026-05-23 — recent convention violation.",
    "severity": "LOW",
    "evidence": "grep -n 'Last updated\\|Lessons count' agent/helpers/verifiers.md → no output. Compare with maintenance_protocol.md:3-5 which has both.",
    "suggested_fix": "Add '**Last updated**: 2026-05-23' and '**Lessons count**: 0 entries' to verifiers.md header. Trivially fixable.",
    "confidence": "HIGH"
  },
  {
    "lens": "L2",
    "location": "project/README.md:14-16 ('This directory contains 2 essential files'); project/README.md:65-68 (directory tree shows 2 files)",
    "failure_mode": "DEAD CONVENTION: project/README.md states twice that the project/ directory 'contains 2 essential files: CURRENT_STATE.json and README.md'. Actual contents: 4 files (CURRENT_STATE.json, README.md, sync_log.json, version_pins.json). sync_log.json has been in project/ since 2025-11-29 and version_pins.json since 2026-05-24. The '2 essential files' framing is not just out of date — it implies that anything else in the directory shouldn't be there.",
    "severity": "MEDIUM",
    "evidence": "Read project/README.md:14-16, :65-68. Run: ls project/ → CURRENT_STATE.json, README.md, sync_log.json, version_pins.json (4 files). Reads from project/sync_log.json happen in session_startup.md:67 and magpie4_reference.md:17 (version_pins.json).",
    "suggested_fix": "Update project/README.md to list all 4 files with a one-line description of each, and replace 'This directory contains 2 essential files' with 'This directory contains project-management files'. Alternatively, move sync_log.json to audit/ (which already hosts validation_rounds.json and pipeline_audit_rounds.json — all 'state tracking' artifacts) so project/ really does revert to the 2-file convention.",
    "confidence": "HIGH"
  }
]
```

---

## L3 — Half-deployed patterns (empty templates, stub scaffolds)

**Agent summary**: 3 findings, dominated by the anchor cluster (R24 ground truth confirmed: 8 — not 10 — empty `module_XX_notes.md` files, all 52-word byte-equivalent scaffolds, oldest 7 months). The same "scaffold without follow-through" pattern recurs in 6 helper `Lessons Learned` sections (5 of which are 2.5+ months old with zero entries despite documented append conventions). Both clusters share a root cause: proactive scaffolding of feedback surfaces before content exists, with no forcing function to backfill. The reference/dependency_analysis snapshot is dated honestly, and archives are properly disclaimed.

```json
[
  {
    "lens": "L3",
    "location": "modules/module_10_notes.md, modules/module_11_notes.md, modules/module_17_notes.md, modules/module_21_notes.md, modules/module_32_notes.md, modules/module_52_notes.md, modules/module_56_notes.md, modules/module_70_notes.md",
    "failure_mode": "Empty-template cluster: 8 of 18 module_XX_notes.md files (44%) contain only the boilerplate scaffold — frontmatter + three section headers (Warnings / Lessons Learned / Real-World Examples) + 'No X recorded yet' placeholder text. All 8 are byte-equivalent (52 words each) and exist for high-centrality modules (10=land, 11=costs, 17=production, 21=trade, 32=forestry, 52=carbon, 56=GHG policy, 70=livestock). Module 10's was created 2025-10-22 (7 months old) and has had zero content added across 7 commits; module 11 was created 2025-11-29 (6 months); newest empty (modules 11/17/21/32/56) is 6 months. AGENT.md instructs the agent to 'always read' notes files when answering about a module — for these 8 modules the read returns nothing useful, so the workflow step is theatre.",
    "severity": "MEDIUM",
    "evidence": "Reproduce: `for f in modules/module_*_notes.md; do echo \"$(wc -w < \"$f\") $f\"; done | sort -n | head -8` shows 8 files at exactly 52 words. Each contains only headers + `*No warnings recorded yet.*` / `*No lessons recorded yet.*` / `*No examples recorded yet.*`. Verified with grep: `grep -nrI 'No .* recorded yet' modules/` returns 24 hits (8 files × 3 placeholder lines). Git age: `git log --diff-filter=A --format='%ci' -- modules/module_10_notes.md | tail -1` → 2025-10-22.",
    "suggested_fix": "Three options, pick one: (a) DELETE the empty notes files — they're created on-demand per AGENT.md's notes-file template anyway, so absence is fine; current presence creates a false-positive 'notes exist' signal. (b) Add a registry-level marker indicating which modules have non-trivial notes vs scaffolds, so the agent skips the read when only a stub exists. (c) Backfill content from the deep-validation rounds (modules 10, 56, 70 have multiple R-series validation findings in audit/validation_rounds.json that should be summarized into these notes files). Option (a) is cheapest; option (c) is highest-value but requires user time.",
    "confidence": "HIGH"
  },
  {
    "lens": "L3",
    "location": "agent/helpers/comparing_model_runs.md:5, agent/helpers/maintenance_protocol.md:5, agent/helpers/session_startup.md:5, agent/helpers/adding_new_scenario.md:5, agent/helpers/water_scarcity_scenarios.md:5, agent/helpers/magpie4_reference.md:5",
    "failure_mode": "Stalled append-pattern: 6 helpers have a `## Lessons Learned` section with `<!-- APPEND-ONLY -->` marker and a self-declared `**Lessons count**: 0 entries` header, but have accumulated zero dated entries despite being 2-5 months old. The append-only convention is documented in `agent/helpers/README.md:78-83`. For comparison, 7 of 15 helpers DO have ≥1 entry (range 1-2), so the pattern works for some helpers — it's specifically stalled for these 6.",
    "severity": "LOW",
    "evidence": "Reproduce: `for f in agent/helpers/*.md; do count=$(awk '/^## .*[Ll]essons [Ll]earned/{flag=1; next} /^## /{flag=0} flag' \"$f\" | grep -cE '^- (20[0-9]{2}-[0-9]{2}-[0-9]{2})'); created=$(git log --diff-filter=A --format='%ci' -- \"$f\" | tail -1 | cut -d' ' -f1); echo \"$count entries | created $created | $f\"; done | sort -n` shows 6 files with 0 entries, of which 5 are 2.5+ months old.",
    "suggested_fix": "(a) For each empty section, write a one-liner explaining why it's still empty (requires tracking load count, which doesn't exist). Simpler: (b) During each session that auto-loads one of these helpers, the agent should explicitly invite the user to record a lesson if any non-trivial workflow detail came up. Don't gold-plate by adding fake entries. The honest read is: the append-pattern depends on user-driven friction, and these workflows have either not been exercised or have worked without friction worth recording.",
    "confidence": "HIGH"
  },
  {
    "lens": "L3",
    "location": "agent/helpers/verifiers.md:1-12 (no Lessons count header)",
    "failure_mode": "Half-deployed convention: `agent/helpers/README.md:40-44` mandates a header template for every helper including `**Lessons count**: [N entries]`. 13 of 15 helpers comply; `verifiers.md` (created 2026-05-23) and `README.md` itself do not. `verifiers.md` is the largest and most consequential helper (2285 words, 16 binding MANDATEs). Its `## Lessons Learned` section exists but lacks the header counter that the README declares as the trigger for the 'when N ≥ 5, scan for promotion candidates' workflow.",
    "severity": "LOW",
    "evidence": "Reproduce: `grep -nE 'Lessons count' agent/helpers/*.md` returns 13 hits across 13 files; `verifiers.md` is absent. `head -12 agent/helpers/verifiers.md` shows no Lessons count field.",
    "suggested_fix": "Add `**Lessons count**: 0 entries` to verifiers.md frontmatter. One-line fix; trivial.",
    "confidence": "HIGH"
  }
]
```

---

## L4 — Cross-doc inconsistency (same fact, different values)

**Agent summary**: 7 cross-doc inconsistencies. Two HIGH-severity load-bearing drifts the marker system was built for but never applied to: (1) the anchor seed (290K vs 342K vs actual 347K words) is unprotected because README.md isn't in refresh_aggregate_counts.py's TARGET_FILES, and (2) bootstrap.md's "6 command files" silently miscalibrates the only post-install verification step. One MEDIUM is unreconciled schema drift (validate-semantic.md says v1.1, JSON is v1.2). The pipeline-audit "6 vs 7 lenses" discrepancy is operational-vs-canonical. Recurring root cause: the marker mechanism works (3 markers, 0 drift in marker-managed counts), but coverage is sparse.

```json
[
  {
    "lens": "L4",
    "location": "AGENT.md:485 vs README.md:90",
    "failure_mode": "Aggregate word count drift: AGENT.md claims '~342,000 words across modules/, core_docs/, cross_module/, reference/, agent/'; README.md claims '~290,000 words / ~64,000 lines'. Same fact, two different values, no <!--count:--> marker linking them. Authoritative `wc -w` returns ~347K words / ~71K lines — both docs stale.",
    "severity": "HIGH",
    "evidence": "Reproduce: `grep -E '290|342' README.md AGENT.md | grep -i word` → README.md:90 'Total: ~290,000 words / ~64,000 lines' vs AGENT.md:485 '~342,000 words'. `wc -w README.md AGENT.md modules/*.md core_docs/*.md cross_module/*.md reference/*.md agent/helpers/*.md agent/commands/*.md` → 346,710 words total.",
    "suggested_fix": "Wrap both with `<!--count:total_doc_words-->347000<!--/count-->` marker and add to scripts/refresh_aggregate_counts.py MARKER_VALUES. Also add README.md to refresh_aggregate_counts.py TARGET_FILES (currently absent). Equivalent for ~64,000 lines via <!--count:total_doc_lines-->71000<!--/count-->.",
    "confidence": "HIGH"
  },
  {
    "lens": "L4",
    "location": "agent/commands/bootstrap.md:110 vs AGENT.md:194-202 vs agent/commands/guide.md:36-47 vs ls agent/commands/*.md",
    "failure_mode": "Command-file count drift: bootstrap.md tells users to expect '6 command files present'; AGENT.md has 10 entries; guide.md has 10; actual `ls agent/commands/*.md | wc -l` returns 10. Bootstrap will report 'success' against the wrong expectation.",
    "severity": "HIGH",
    "evidence": "ls -1 agent/commands/*.md | wc -l → 10 (bootstrap, explain, guide, pipeline-audit, sync, trace, update, validate-module, validate-semantic, validate). bootstrap.md:110 'Expected: AGENT.md deployed, 6 command files present'.",
    "suggested_fix": "Introduce a `<!--count:n_commands-->10<!--/count-->` marker sourced from `ls agent/commands/*.md | wc -l` and reference it in bootstrap.md, AGENT.md, and guide.md. Add bootstrap.md to refresh_aggregate_counts.py TARGET_FILES.",
    "confidence": "HIGH"
  },
  {
    "lens": "L4",
    "location": "agent/commands/validate-semantic.md:170,177 vs audit/validation_rounds.json:4 vs audit/README.md:25",
    "failure_mode": "validation_rounds.json schema version drift: command file documents 'schema v1.1 as of 2026-05-23' and 'Schema v1.1 changes (2026-05-23)'; the actual schema_version field is '1.2' (bumped 2026-05-24 to add G3/G4 magpie4 regression questions). validate-semantic.md is the file that tells future agents what version to write to the JSON.",
    "severity": "HIGH",
    "evidence": "audit/validation_rounds.json line 4: `\"schema_version\": \"1.2\"`. Schema history shows 1.0→1.1→1.2. audit/README.md:25 'schema v1.2' — current. validate-semantic.md:170 '(schema v1.1 as of 2026-05-23)' — stale.",
    "suggested_fix": "Update validate-semantic.md:170 to 'schema v1.2 as of 2026-05-24' and add a 'Schema v1.2 changes (2026-05-24)' note. Better: wrap with a marker sourced from `audit/validation_rounds.json` .metadata.schema_version.",
    "confidence": "HIGH"
  },
  {
    "lens": "L4",
    "location": "AGENT.md:202 + agent/commands/pipeline-audit.md:7,15,25,66,98 vs audit/get_under_control_plan.md:34,55 vs audit/pipeline_audit_round6_design.md:35,58",
    "failure_mode": "Pipeline-audit lens/agent count drift: AGENT.md and pipeline-audit.md hardcode '6 parallel Opus sub-agents'/'6 lenses'; get_under_control_plan.md says '7 parallel Sonnet lens agents'; pipeline_audit_round6_design.md says '7 lenses' and 'Opus'. R6 operational truth is 7 Opus.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:202 `(6 parallel Opus agents)`. pipeline-audit.md:7 '6 parallel Opus sub-agents'. get_under_control_plan.md:34 '7 parallel Sonnet lens agents'. pipeline_audit_round6_design.md:35 '7 lenses (not 6)'.",
    "suggested_fix": "Reconcile: either update pipeline-audit.md and AGENT.md to '7 parallel Opus sub-agents' with the L1-L7 lens breakdown, or keep 6 as canonical default and treat R6's 7-lens split as a per-round override (in which case pipeline_audit_round6_design.md should explicitly say 'overrides /pipeline-audit defaults').",
    "confidence": "HIGH"
  },
  {
    "lens": "L4",
    "location": "agent/helpers/realization_selection.md:30 vs audit/next_session_plan.md:210 vs audit/validation_rounds.json cumulative_stats.gams_realizations_verified",
    "failure_mode": "Active-realization count drift: realization_selection.md L30 '75 active realizations'; validation_rounds.json cumulative_stats: 75; audit/next_session_plan.md:210 'python3 scripts/check_gams_realizations.py # 100% (77/77 realizations)' — 77, stale by 2.",
    "severity": "LOW",
    "evidence": "realization_selection.md:30 '75 active realizations'. validation_rounds.json:3251 '\"gams_realizations_verified\": 75'. next_session_plan.md:210 '77/77'.",
    "suggested_fix": "Either rerun the validator and update next_session_plan.md, or replace the literal with marker `<!--count:gams_realizations_verified-->75<!--/count-->` sourced from cumulative_stats.",
    "confidence": "HIGH"
  },
  {
    "lens": "L4",
    "location": "README.md:75 vs README.md:80 vs README.md:85 (internal) and vs `wc -w` of actual directories",
    "failure_mode": "Phase totals in README are internally inconsistent and stale. Phase 0 'Foundation (~70,000 words)' — current core_docs+reference is ~45K words. Phase 1 'Modules (~20,000+ lines)' — actual is ~47K. Phase 2 'Cross-Module Analysis (~5,400 lines)' — actual 5,253 (close).",
    "severity": "MEDIUM",
    "evidence": "README.md:75 '~70,000 words'. wc -w core_docs/*.md reference/*.md → 45,473. README.md:80 '~20,000+ lines'. wc -l modules/module_*.md → 47,660. README.md:85 '~5,400 lines'. wc -l cross_module/*.md → 5,253.",
    "suggested_fix": "Drop the per-phase word/line counts entirely (frozen marketing claims that drift on every commit) and replace with 'See `wc -l` for current sizes'. If a number must be kept, define each Phase's scope precisely and wrap with markers.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L4",
    "location": "cross_module/circular_dependency_resolution.md:5 vs cross_module/circular_dependency_resolution.md:11 vs core_docs/Module_Dependencies.md:6,150,412 vs AGENT.md:292,517",
    "failure_mode": "Minor internal contradiction: L5 says '26+ circular dependencies' while L11 says '26 circular dependency cycles' and all other docs say '26'. The '26+' on L5 is the only outlier; in isolation it suggests there might be more than 26.",
    "severity": "LOW",
    "evidence": "cross_module/circular_dependency_resolution.md:5 '26+ circular dependencies'; :11 '26 circular dependency cycles'; Module_Dependencies.md:6 '26 circular dependency cycles'; AGENT.md:292 '26 circular dependencies and resolution'.",
    "suggested_fix": "Change L5 from '26+' to '26' to match. Or use marker `<!--count:circular_dependencies-->26<!--/count-->`.",
    "confidence": "HIGH"
  }
]
```

---

## L5 — Misplaced outputs (files in wrong directories + .gitignore gaps)

**Agent summary**: 7 findings. The anchor (validation_report_*.txt in parent root) is real and traces to a CWD-before-cd bug in the .bak script. The current validate_consistency.sh still reproduces the same defect class (creates `.cache/validation_reports/` in caller's CWD before chdir-ing to AGENT_DIR), so the orphan-output bug is not fully fixed — it just changed shape. The .bak file itself is still on disk as a footgun. add_timestamps.py is a tooling script misplaced at agent root. Parent .gitignore is missing entries for all installed agent infrastructure — and parent's `origin` is the upstream MAgPIE repo, so this is a real exposure risk.

```json
[
  {
    "lens": "L5",
    "location": "<magpie-root>/validation_report_20260517_102617.txt and /validation_report_20260524_095554.txt",
    "failure_mode": "Validator OUTPUT from magpie-agent's validate_consistency.sh landed in PARENT magpie/ repo root, not in magpie-agent/.cache/validation_reports/. Both files contain 'Location: <magpie-agent>' as the first line of body. Parent .gitignore does NOT ignore them; parent's `origin` points to git@github.com:magpiemodel/magpie.git, so a stray `git add -A` in parent would commit agent output to upstream MAgPIE. Root cause: older validate_consistency.sh (preserved at scripts/validate_consistency.sh.bak:23) set `REPORT_FILE=\"validation_report_${TIMESTAMP}.txt\"` with no directory prefix AND wrote the file (lines 69-72) BEFORE `cd \"$AGENT_DIR\"` (line 78), so invocation from parent dir created the report there.",
    "severity": "HIGH",
    "evidence": "ls <magpie-root>/validation_report_*.txt → 2 files. head -1 of each shows 'MAgPIE Documentation Consistency Validation'. `cd <magpie-root> && git check-ignore -v validation_report_20260517_102617.txt` exits non-zero (not ignored). `git status --short` shows them as `??`.",
    "suggested_fix": "(a) Move the two existing orphans into magpie-agent/.cache/validation_reports/ or delete them. (b) Delete scripts/validate_consistency.sh.bak — it's the stale, buggy version. (c) Add `validation_report_*.txt` to PARENT <magpie-root>/.gitignore. The agent's own .gitignore has the pattern, but a pattern in magpie-agent/.gitignore CANNOT protect the parent repo.",
    "confidence": "HIGH"
  },
  {
    "lens": "L5",
    "location": "<magpie-agent>/scripts/validate_consistency.sh:22-25 and :80",
    "failure_mode": "Same defect class as the anchor, in a different shape. The current (non-.bak) script still creates its output directory before chdir-ing. Lines 23-25 set `REPORT_DIR=\".cache/validation_reports\"`, call `mkdir -p \"$REPORT_DIR\"`, and define `REPORT_FILE` — ALL relative to the caller's CWD. The `cd \"$AGENT_DIR\"` doesn't happen until line 80. Result: when a user invokes the script from parent magpie/, a stray `.cache/validation_reports/` directory is created in that CWD.",
    "severity": "HIGH",
    "evidence": "scripts/validate_consistency.sh:23-25 (mkdir before cd); :80 (cd happens later). The first `echo ... > \"$REPORT_FILE\"` on line 71 also writes before the cd.",
    "suggested_fix": "Move the `cd \"$AGENT_DIR\"` block (lines 27-29 compute it, line 80 applies it) up to BEFORE line 22. Equivalently: anchor REPORT_DIR explicitly as `REPORT_DIR=\"${AGENT_DIR}/.cache/validation_reports\"` after computing AGENT_DIR.",
    "confidence": "HIGH"
  },
  {
    "lens": "L5",
    "location": "<magpie-agent>/scripts/validate_consistency.sh.bak",
    "failure_mode": "Stale 37 KB backup of the validator with the original buggy CWD-dependent REPORT_FILE behavior, sitting next to the active script. Properly gitignored (matches `*.bak`), but its mere presence in scripts/ is a footgun: someone running it would re-create the orphan-report bug.",
    "severity": "MEDIUM",
    "evidence": "ls -la scripts/ shows validate_consistency.sh (41987 bytes) AND validate_consistency.sh.bak (37530 bytes). `git check-ignore -v scripts/validate_consistency.sh.bak` → `.gitignore:3:*.bak`.",
    "suggested_fix": "Delete the .bak file. Git history already preserves prior versions. If versioned snapshot is wanted, use a tag or `archive/` subdir.",
    "confidence": "HIGH"
  },
  {
    "lens": "L5",
    "location": "<magpie-agent>/add_timestamps.py",
    "failure_mode": "Tooling script located at magpie-agent ROOT instead of in magpie-agent/scripts/ where all 28 other agent scripts live. The script's docstring says 'Add standardized Last Verified timestamps to all module_XX.md files' — exactly the kind of thing in scripts/check_*, scripts/refresh_*.",
    "severity": "MEDIUM",
    "evidence": "find magpie-agent -maxdepth 1 -type f → AGENT.md, README.md, .gitignore, .DS_Store, add_timestamps.py (only non-canonical entry). git ls-files | grep add_timestamps → tracked at root.",
    "suggested_fix": "git mv add_timestamps.py scripts/add_timestamps.py. The script uses `modules_dir = Path('modules')` which assumes CWD = agent root; anchor it explicitly: `modules_dir = Path(__file__).resolve().parent.parent / 'modules'`.",
    "confidence": "HIGH"
  },
  {
    "lens": "L5",
    "location": "<magpie-root>/.gitignore (parent repo)",
    "failure_mode": "Parent .gitignore is missing entries for everything the user has installed at parent root that isn't part of MAgPIE proper: AGENT.md, CLAUDE.md, PREPROC_AGENT.md, magpie-agent/, magpie-preproc-agent/, .claude/, .copilot/. All show as `??` in `git status` from parent. Parent's `origin` is magpiemodel/magpie (the real upstream), so a careless `git add -A && git commit && git push` would push agent infrastructure + Claude session data to the public MAgPIE repo.",
    "severity": "HIGH",
    "evidence": "`cd magpie && git status --short` shows `?? .claude/`, `?? .copilot/`, `?? AGENT.md`, `?? CLAUDE.md`, `?? PREPROC_AGENT.md`, `?? magpie-agent/`, `?? magpie-preproc-agent/`. `git remote -v`: `origin git@github.com:magpiemodel/magpie.git`.",
    "suggested_fix": "Add to PARENT .gitignore: `AGENT.md`, `CLAUDE.md`, `PREPROC_AGENT.md`, `/magpie-agent/`, `/magpie-preproc-agent/`, `.claude/`, `.copilot/`, `validation_report_*.txt`, `.cache/`.",
    "confidence": "HIGH"
  },
  {
    "lens": "L5",
    "location": "<magpie-root>/tc_scenarios_compare_2026051*.csv (5 files)",
    "failure_mode": "Five user-experiment output CSVs at parent magpie root, accidentally ignored by `.gitignore` line 7 `*.cs*` (matches `.csv` because the wildcard after `cs` matches `v`). NOT from magpie-agent — content is tc_scenarios from MAgPIE 'tc_vs_landuse' experiment. The accidental ignore is fragile: anyone fixing the `*.cs*` pattern would unmask 5 untracked CSVs.",
    "severity": "LOW",
    "evidence": "ls .../tc_scenarios_compare_*.csv → 5 files. `git check-ignore -v` → `.gitignore:7:*.cs*`. grep -rn 'tc_scenarios_compare' magpie-agent/ → no matches.",
    "suggested_fix": "Out of L5 scope to redirect MAgPIE-side script. Within scope: fix `*.cs*` to `*.cs2`, `*.cs3`, `*.cs4` (the actual files it was meant to ignore) — `*.cs*` accidentally catches .csv. Add explicit `tc_scenarios_compare_*.csv` entry if intentional.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L5",
    "location": "<magpie-agent>/audit/pipeline_audit_round6_design.md",
    "failure_mode": "Untracked artifact at magpie-agent/audit/ from the round 6 design pass. Sibling round1, round3, round4, round5 markdown files in the same dir are tracked.",
    "severity": "LOW",
    "evidence": "git status (in magpie-agent) → `?? audit/pipeline_audit_round6_design.md`. ls audit/ shows pipeline_audit_round1-5.md all tracked.",
    "suggested_fix": "Commit it (sibling-pattern is to commit). Or add `audit/pipeline_audit_round*_design.md` to .gitignore.",
    "confidence": "HIGH"
  }
]
```

---

## L6 — Reference-graph integrity (pointers vs target health)

**Agent summary**: The anchor (4-5 READMEs → stale CURRENT_STATE.json, 79 days old) is confirmed and recurs in three structural patterns: (1) hub targets with stale self-stamped 'Last Updated' fields that 5+ pointers route to as authoritative (CURRENT_STATE.json, 4 cross_module conservation docs from 2025-10-22, Tool_Usage_Patterns.md from 2025-11-29, maintenance_protocol.md itself); (2) duplicated inventories drifting from canonical source (helpers/README.md prose list now missing magpie4_reference; bootstrap.md saying '6 commands' vs actual 10; project/README.md '2 essential files' vs actual 4; CURRENT_STATE.json's '10 helpers / 6 commands' vs AGENT.md's 14/10); (3) pointer-to-nonexistent-section (AGENT.md and helpers/README.md both route to a `## Requested Helpers` section that has never existed). Root cause: hub-target asymmetry — high-in-degree targets carry no self-marker of their hub status.

```json
[
  {
    "lens": "L6",
    "location": "README.md:7,18,71,94 + modules/README.md:3,16,18,26 + project/README.md:18,53 + cross_module/README.md:24 + AGENT.md:111,117",
    "failure_mode": "Hub pointer to stale target (the R24 anchor). Five documents route readers to `project/CURRENT_STATE.json` as 'SINGLE source of truth' / 'authoritative' for project status. Target's `last_updated` = 2026-03-07 (79 days old). Internal claims in CURRENT_STATE.json disagree with AGENT.md: '10 helpers' (actual 14), '6 commands' (actual 10), '13-round flywheel' (actual 24), '291 bugs' (actual 474). Asymmetric hub-target: 5+ docs depend on it; target acknowledges only the staleness as a 'cosmetic' known_issue without addressing the numbers.",
    "severity": "HIGH",
    "evidence": "grep -rn 'CURRENT_STATE' README.md modules/README.md agent/helpers/README.md audit/README.md project/README.md cross_module/README.md AGENT.md → 5+ pointers. head -10 project/CURRENT_STATE.json → last_updated: 2026-03-07. AGENT.md L328 = 24 rounds vs CURRENT_STATE.json release.highlights = '13-round'.",
    "suggested_fix": "Either (a) refresh CURRENT_STATE.json with current counts + extend the maintenance protocol to require its update whenever AGENT.md helper/command tables change, or (b) demote CURRENT_STATE.json from 'authoritative' to 'archived snapshot through phase 4 (2026-03-07)' and route the 5 pointers to a freshly maintained status block in AGENT.md or a new dated status doc. (b) is simpler.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "AGENT.md:287-292,512-517 + README.md:119-124 + core_docs/Response_Guidelines.md:49,66,105,379 + agent/helpers/scenario_carbon_pricing.md:172-173 + agent/helpers/debugging_infeasibility.md:152-156,166-167 + agent/helpers/interpreting_outputs.md:195 + agent/helpers/comparing_model_runs.md:265 + agent/helpers/scenario_diet_change.md:186,199 + agent/helpers/water_scarcity_scenarios.md:272 + agent/helpers/realization_selection.md (multiple) + agent/helpers/modification_impact_analysis.md:60-64,154 + agent/helpers/adding_new_crop.md:238-239",
    "failure_mode": "Hub-target asymmetry to admitted-stale targets. The four `cross_module/*_balance_conservation.md` + `nitrogen_food_balance.md` files explicitly self-stamp `**Last Updated**: 2025-10-22` (217 days old) yet AGENT.md tabulates them as the 'Use For' source for 'Is land/water/carbon conserved?' (L532), README.md lists them under '✅ Complete' phase 2, and at least 8 helpers route to them as authoritative for conservation/balance mechanics. Targets do NOT acknowledge their hub status or schedule a refresh; magpie develop has had hundreds of commits since 2025-10-22.",
    "severity": "HIGH",
    "evidence": "tail -5 cross_module/{land,carbon,water}_balance_conservation.md → all three end with `**Last Updated**: 2025-10-22`. grep -rnE 'cross_module/(land|water|carbon|nitrogen)' AGENT.md README.md core_docs/*.md agent/helpers/*.md returns 25+ inbound pointers. None of the targets contain a back-reference or `## Pointer back-references` section.",
    "suggested_fix": "Add a 'Verified Against Current MAgPIE at Y-M-D' footer to each cross_module file when its underlying module equations are re-verified. Cheaper interim fix: drop the precise '2025-10-22' date and replace with 'Conservation-law structure verified against MAgPIE 4.x architecture; underlying module equations re-verified as of last GAMS sync (`project/sync_log.json`).'",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "core_docs/Tool_Usage_Patterns.md:5 (target) + AGENT.md:61,497,530 + README.md:132,431 (pointers)",
    "failure_mode": "Pointer to a target with self-admitted 6-month stale 'Last Updated'. AGENT.md and README.md both route users to Tool_Usage_Patterns.md. Target stamps itself `Last Updated: 2025-11-29` (178 days old). Bash directory navigation patterns and tool semantics have likely shifted (the user's MEMORY.md even includes `bash-grep-r-unreliable-magpie.md` which would belong here).",
    "severity": "MEDIUM",
    "evidence": "head -10 core_docs/Tool_Usage_Patterns.md shows `**Last Updated**: 2025-11-29`. grep -nE 'Tool_Usage_Patterns' AGENT.md README.md returns 5 inbound pointers.",
    "suggested_fix": "Either refresh the 'Last Updated' field after a content review or remove the stamp and replace with a section-level provenance pattern.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "agent/helpers/maintenance_protocol.md:4 (target) + AGENT.md:443 + agent/commands/sync.md:13 + agent/commands/update.md:19 (pointers)",
    "failure_mode": "Hub self-claim of authority while own header is stale. maintenance_protocol.md L11 declares 'Use this as the authoritative reference whenever documentation freshness, sync, or validation questions arise' but L4 says `**Last updated**: 2026-03-07` (79 days old) and L5 says `**Lessons count**: 0 entries` — even though the period since 2026-03-07 includes 24 validation rounds, multiple pipeline audits, and a /feedback removal. Two slash commands (/sync, /update) and AGENT.md auto-load to this file as the authority on staleness.",
    "severity": "MEDIUM",
    "evidence": "head -12 agent/helpers/maintenance_protocol.md shows `**Last updated**: 2026-03-07` + L11 'Use this as the authoritative reference'.",
    "suggested_fix": "Bump 'Last updated' to current after a review pass. Also: the helper should incorporate the `/pipeline-audit`-based audit cadence which has emerged since.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "agent/helpers/{adding_new_scenario.md:4,comparing_model_runs.md:4,water_scarcity_scenarios.md:4}",
    "failure_mode": "Stale 'Last updated' headers on auto-loaded helpers. Three helpers stamp themselves 'Last updated: 2025-07-15' or '2025-07-18' (314-317 days old) — yet AGENT.md auto-loads them as authoritative for their domains.",
    "severity": "MEDIUM",
    "evidence": "grep -n 'Last updated' agent/helpers/{adding_new_scenario,comparing_model_runs,water_scarcity_scenarios}.md shows `2025-07-15` and `2025-07-18`. AGENT.md L440-442 routes auto-load triggers to each.",
    "suggested_fix": "(a) Sweep these three helpers, refresh content against current MAgPIE realizations + add an entry to each Lessons Learned, bump dates; or (b) remove the per-helper 'Last updated' header convention entirely.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "AGENT.md:479 + agent/helpers/README.md:90 (pointers to nonexistent section)",
    "failure_mode": "Pointer to a section that doesn't exist in target. AGENT.md L479 instructs: 'If they decline, note the gap in agent/helpers/README.md under a ## Requested Helpers section'. helpers/README.md L90 mirrors that. But `grep -E '^##' agent/helpers/README.md` shows no such section exists.",
    "severity": "LOW",
    "evidence": "grep -E '^##' agent/helpers/README.md returns: Overview, How Auto-Loading Works, Helper File Template, Self-Improvement Mechanism, Design Principles. No 'Requested Helpers'.",
    "suggested_fix": "Either (a) add an empty `## Requested Helpers` section to helpers/README.md (one-line fix), or (b) remove the convention and route helper requests to `audit/global/agent_lessons.md`.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "project/README.md:5,10,75 (pointers to dead concept)",
    "failure_mode": "Pointer using stale concept name + stale file-tree characterization. project/README.md L10 lists `audit/ - User feedback system` and L75 mirrors that. But audit/README.md L3 explicitly states: 'There is no longer an external user-submission inbox (the /feedback command and pending/ were removed in commit 327116c on 2026-05-24)'. The pointer routes a maintainer to think `audit/` is for user-feedback intake.",
    "severity": "MEDIUM",
    "evidence": "grep -n 'audit/\\|feedback' project/README.md shows L10 'audit/ - User feedback system' and L75 mirror. Counter-evidence: audit/README.md says '...removed in commit 327116c on 2026-05-24'. README.md L145 'audit/ ← Internal iteration artifacts' uses correct framing.",
    "suggested_fix": "Replace 'User feedback system' with 'Internal iteration artifacts (validation rounds, pipeline audits, lessons)' in project/README.md.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "AGENT.md:300 (self-internal section pointer)",
    "failure_mode": "Internal section pointer with wrong section name. AGENT.md L300 says 'Apply staleness badge (see Auto-Loading Helpers section for badge definitions)' but the actual section is 'Auto-Loading Context Helpers' at L412. The 'Sync freshness badges' subsection (L445) is the actual definition location.",
    "severity": "LOW",
    "evidence": "grep -n 'Auto-Loading' AGENT.md returns L300 'Auto-Loading Helpers section', L328 'Auto-Loading Context Helpers table', L412 '## 🔄 Auto-Loading Context Helpers'.",
    "suggested_fix": "AGENT.md L300: change 'Auto-Loading Helpers section' → 'Sync freshness badges subsection below'.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "agent/commands/bootstrap.md:110 (assertion about command count)",
    "failure_mode": "Bootstrap routine asserts wrong expected value as a verification gate. L110 says 'Expected: AGENT.md deployed, 6 command files present'. Actual: 10. CURRENT_STATE.json L21 correctly says '10 command files'.",
    "severity": "MEDIUM",
    "evidence": "grep -n '6 command' agent/commands/bootstrap.md → L110. ls agent/commands/*.md | wc -l → 10.",
    "suggested_fix": "Change '6 command files present' → '10 command files present (see AGENT.md Available Commands table for the canonical list)'.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "project/README.md:16 (assertion about file count)",
    "failure_mode": "Document claims '2 essential files' but the actual project/ contents are 4 files. The L16 framing 'This directory contains 2 essential files: CURRENT_STATE.json and README.md' ignores sync_log.json (load-bearing for /sync) and version_pins.json (load-bearing for magpie4 helper).",
    "severity": "MEDIUM",
    "evidence": "ls project/ → CURRENT_STATE.json, README.md, sync_log.json, version_pins.json (4 entries). grep -n '2 essential' project/README.md → L16. README.md L111 and project/README.md L68 both reference only CURRENT_STATE.json.",
    "suggested_fix": "Update project/README.md to list all 4 files. Update tree diagrams. Alternatively, move sync_log.json to audit/ so project/ really does revert to the 2-file convention.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "agent/helpers/README.md:25 (prose helper inventory)",
    "failure_mode": "Prose helper list in helpers/README.md is one helper behind AGENT.md. L25 lists 13 helpers but AGENT.md auto-load table (L424-443) has 14 (missing from L25: magpie4_reference, added 2026-05-24). Same drift pattern that R3 fixed for the duplicate routing table is re-occurring in the prose summary.",
    "severity": "LOW",
    "evidence": "grep -E 'anti-confabulation|verifiers|infeasibility|carbon-pricing|diet|water-scarcity|modification|output|realization|adding|comparing|maintenance|session' agent/helpers/README.md → L25 single-line prose lists 13. AGENT.md L437 includes magpie4_reference.",
    "suggested_fix": "Either (a) add 'magpie4 function reference' to the L25 prose list, or (b) remove the prose list and replace with a pointer: 'For the full helper inventory and triggers, see the Auto-Loading Context Helpers table in AGENT.md.'",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "audit/magpie4_scaffolding_plan.md:8 → §22 (self-deposed but not removed)",
    "failure_mode": "Document contains an explicit 'this section is wrong — see helper instead' note pointing back into itself, but the wrong text in §22 is preserved unchanged. L8 reads: '§22 below states ... Both halves of that claim were wrong... Treat the helper, not §22, as authoritative going forward.' A reader scrolling to §22 finds the original wrong text first.",
    "severity": "LOW",
    "evidence": "head -10 audit/magpie4_scaffolding_plan.md shows the post-execution correction. grep -n '108 unique' audit/magpie4_scaffolding_plan.md → L18 and L27 both still contain the wrong '108 unique report* functions'.",
    "suggested_fix": "Add an inline strikethrough or admonition to §22 (or to L18 and L27). Better: edit the §22 text to match reality and keep the top-of-file note as a historical record.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "modules/README.md:147-156 (stale 'next steps' section)",
    "failure_mode": "Stale-status pointer disguised as forward-looking section. modules/README.md L147-156 'Next Steps' section ends 'Current Focus: Phase 2 - Cross-Module Analysis' and lists conservation laws, common workflows, dependency analysis as upcoming work. But README.md L85 confirms Phase 2 was completed in 2025-10-22.",
    "severity": "MEDIUM",
    "evidence": "grep -n 'Current Focus\\|Phase 2' modules/README.md → L151 'Current Focus: Phase 2'. README.md L85-86 'Phase 2 - Cross-Module Analysis (~5,400 lines) ✅'. CURRENT_STATE.json documents phase_2_completed at 2025-10-22.",
    "suggested_fix": "modules/README.md L147-156: remove or replace 'Next Steps / Phase 2' with 'Phase 2 (cross-module analysis, conservation laws, modification safety) was completed 2025-10-22 — see `../cross_module/` for deliverables.' Point forward-looking work to `audit/get_under_control_plan.md`.",
    "confidence": "HIGH"
  },
  {
    "lens": "L6",
    "location": "audit/pipeline_audit_round3.md:206 → action item from R3 that has resurfaced",
    "failure_mode": "Previously-fixed pointer issue has resurfaced as a recurring class. R3 audit noted 'helpers/README.md L23-32: replace duplicate table with pointer to AGENT.md (single source of truth)'. That fix landed (helpers/README.md L21-25 now correctly defers). BUT the same root cause — duplicated inventory in a subordinate README — has re-emerged at helpers/README.md L25 (prose list) and project/README.md L10/75 (audit/ characterization). Indicates the R3 fix was applied locally rather than as a class-level rule.",
    "severity": "MEDIUM",
    "evidence": "grep -n 'single source of truth' agent/helpers/README.md → L21 confirms R3 fix landed for the routing table. But L25 contains the new drift surface. project/README.md L10 still describes audit/ with the old framing.",
    "suggested_fix": "Class-level rule (add to maintenance_protocol.md): 'Subordinate READMEs must NOT include inventories (helper lists, command lists, file lists) that are maintained elsewhere — only pointers. Prose summaries are exempt only if they explicitly cite the canonical source by name on the same line.' Then audit all *README.md files for re-occurrences.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L6",
    "location": "Multiple — see evidence (orphan finding: hub-target back-reference asymmetry)",
    "failure_mode": "Systematic asymmetry: targets that 5+ docs point at do not back-reference their dependents. AGENT.md (in-degree ~50), CURRENT_STATE.json (in-degree 5+), Module_Dependencies.md (in-degree 15+), agent/helpers/verifiers.md (in-degree ~5 + auto-load), and the four cross_module conservation docs (in-degree 8+ each) are all silently load-bearing. None carry a 'Pointed at by' / 'If you update this, also re-verify' / 'Hub status' marker. A future agent editing has no in-doc warning about the blast radius. Structural cause behind findings F1, F2, F4.",
    "severity": "MEDIUM",
    "evidence": "Pointer graph (re-derivable): for each file in question, `grep -rln '<file>' --include='*.md' . | wc -l`. None include a `## Pointed at by` section.",
    "suggested_fix": "Add a uniform 'Hub status: this file is referenced from N+ pointers. If you change names, conventions, or counts here, also audit the dependents listed in `audit/pointer_graph.json`' footer to high-in-degree files. Build pointer-graph extraction into `scripts/refresh_aggregate_counts.py`.",
    "confidence": "MEDIUM"
  }
]
```

---

## L7 — Surface bloat + workflow gaps

**Agent summary**: BLOAT anchor confirmed — AGENT.md is 846 lines / 46KB (41% over the 600-line anchor); three HIGH-severity hoist candidates (SESSION CLEANUP, LINK DON'T DUPLICATE, DIRECTORY STRUCTURE) would clear ~180 lines without information loss. GAP anchor confirmed and BROADER than stated — magpie4 is missing from FIVE workflow-scaffold sections (MANDATORY WORKFLOW Step 1, QUICK MODULE FINDER, QUALITY GUARD, DOCUMENT HIERARCHY, QUICK RESPONSE CHECKLIST), and a parallel gap exists for the preproc layer in QUICK MODULE FINDER and QUICK RESPONSE CHECKLIST. Deployed-copy drift is CLEAN (all three byte-identical). Four MEDIUM-severity overly-broad triggers ('GAMS'/'equation', bare 'modify', 'water', 'scenario') waste tokens by firing on near-universal words.

```json
[
  {
    "lens": "L7",
    "location": "AGENT.md:1-846",
    "failure_mode": "ALWAYS-LOADED SURFACE EXCEEDS WARNING THRESHOLD (BLOAT anchor confirmed). AGENT.md is 846 lines / 46,041 bytes. Claude's deployed-surface warning is ~600 lines / ~40KB. This file ships into the system prompt of every magpie-agent session via ../CLAUDE.md, so every byte costs every conversation. Current overshoot: ~41% on line count, ~15% on byte count.",
    "severity": "HIGH",
    "evidence": "wc -lc AGENT.md ../AGENT.md ../CLAUDE.md → all three byte-identical at 846 / 46041. Section index (grep -nE '^##' AGENT.md) shows 24 top-level sections.",
    "suggested_fix": "Hoist three large sections to dedicated auto-loaded helpers (target: cut ~200 lines): (1) SESSION CLEANUP (lines 122-176) → `agent/helpers/session_cleanup.md`. (2) LINK DON'T DUPLICATE (lines 721-800) → `agent/helpers/link_dont_duplicate.md`. (3) DIRECTORY STRUCTURE diagram (lines 217-262) → `agent/helpers/directory_structure.md`. Net headroom ~180 lines.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:265-408 (MANDATORY WORKFLOW), AGENT.md:540-554 (QUICK MODULE FINDER), AGENT.md:610-654 (QUALITY GUARD), AGENT.md:691-718 (DOCUMENT HIERARCHY), AGENT.md:803-818 (QUICK RESPONSE CHECKLIST)",
    "failure_mode": "GAP anchor confirmed and broader than stated. magpie4 surfaced ONLY in the auto-load trigger table (line 437). Missing from FIVE scaffold sections that route 'what to check' decisions: MANDATORY WORKFLOW Step 1 'for cross-cutting questions' (no magpie4); QUICK MODULE FINDER (lists 46 GAMS modules and nothing else); QUALITY GUARD (no magpie4-specific bug class); DOCUMENT HIERARCHY READING ORDER (no entry for output-interpretation questions); QUICK RESPONSE CHECKLIST (no 'check magpie4 source for report.mif claims'). Confirmed via `grep -c 'magpie4' core_docs/*.md` → 0 in Response_Guidelines.md AND Query_Patterns_Reference.md. The auto-load trigger fires only on overt keywords — a user asking 'Why does my run show Emissions|N2O|Land = 0?' may not trigger it.",
    "severity": "HIGH",
    "evidence": "grep -nE 'magpie4|report\\.mif|getReport' AGENT.md → only lines 436 and 437. grep -c 'magpie4' core_docs/Response_Guidelines.md core_docs/Query_Patterns_Reference.md → 0/0. magpie4_reference.md exists (1,970 words) and is cited in validate-semantic.md regression questions G3/G4.",
    "suggested_fix": "FIVE insertions: (1) AGENT.md:282 — add 'For report.mif / model-output-provenance questions, also check `agent/helpers/magpie4_reference.md`'. (2) AGENT.md:553 — append to QUICK MODULE FINDER: '**Reporting/Output layer (R)**: magpie4 (see agent/helpers/magpie4_reference.md)'. (3) AGENT.md:636 — add row to High-Risk content for magpie4 source citations. (4) AGENT.md:704 — add reading-order branch for 'User asks about report.mif / IAMC variable'. (5) AGENT.md:815 — add checklist item for magpie4 source.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:431 (helper trigger table row 'Reading/writing/explaining GAMS code')",
    "failure_mode": "OVERLY BROAD TRIGGERS. The GAMS-code helper trigger fires on 'GAMS', 'equation', 'modify code', 'code means', 'what does this do' — all of which appear in many sessions that don't actually need the full reference/GAMS_MAgPIE_Patterns.md (3,000+ lines).",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:431. 'equation' appears 59 times in adding_new_crop.md and 38 in scenario_diet_change.md (where it doesn't mean 'fire GAMS reference docs').",
    "suggested_fix": "Tighten triggers: replace 'equation', 'modify code', 'code means', 'what does this do' with more specific patterns: 'q<N>_', 'equations.gms', '.gms file', '=e=/=l=/=g=', 'GAMS syntax'. Keep 'GAMS' and 'write code'.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:434 (helper trigger row 'Modifying code / impact analysis')",
    "failure_mode": "OVERLY BROAD TRIGGERS. 'modify' and 'change module' will fire on many sessions that aren't doing impact analysis. 'modify' alone is one of the most common verbs in code conversations.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:434. Bare 'modify' is a near-universal verb in code discussions and triggers a ~5KB helper load even when the question is a simple syntax edit.",
    "suggested_fix": "Replace bare 'modify' / 'change module' with intent-shaped triggers: 'is it safe to modify', 'what will break if', 'impact of changing', 'dependencies of', 'before I change'.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:442 (helper trigger row 'Water scarcity analysis')",
    "failure_mode": "OVERLY BROAD TRIGGER. Bare 'water' fires the full water_scarcity_scenarios.md (1,845 words) on any session mentioning water — including non-scarcity contexts.",
    "severity": "LOW",
    "evidence": "AGENT.md:442. 'water' is one of the most common single nouns in a model that includes modules 41/42/43.",
    "suggested_fix": "Replace bare 'water' with scarcity-shaped triggers: 'water scarcity', 'water constraint', 'water-stressed', 'water shortage'.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:440 (helper trigger row 'Creating new scenarios')",
    "failure_mode": "OVERLY BROAD TRIGGER. Bare 'scenario' fires adding_new_scenario.md (1,875 words) on any session mentioning scenarios.",
    "severity": "LOW",
    "evidence": "AGENT.md:440. Many adjacent helpers (scenario_carbon_pricing.md, scenario_diet_change.md, water_scarcity_scenarios.md, comparing_model_runs.md) are scenario-related.",
    "suggested_fix": "Replace bare 'scenario' with creation-shaped triggers: 'create scenario', 'set up scenario', 'design scenario', 'combine policies', 'new policy run'.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:25-50 (Twin-agent disambiguation section, ~26 lines)",
    "failure_mode": "OVERSIZED INCIDENT-RESPONSE SECTION IN ALWAYS-LOADED SURFACE. 26 lines including an inline Python script for recency-checking. Single-incident playbook (2026-05-08 misroute) hoisted into the always-loaded surface.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:25-50, lines 33-39 contain a 7-line inline Python script. Section is conditional ('READ FIRST when terms below appear') yet always loaded.",
    "suggested_fix": "Trim to a 4-line marker pointing to a new helper `agent/helpers/twin_agent_disambiguation.md` (move the Python check, cues table, discipline rules there). Auto-load triggers: 'flywheel', 'round N', 'validation_rounds.json', 'preproc'. Headroom: ~22 lines saved.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:483-537 (COMPLETE DOCUMENTATION STRUCTURE, ~55 lines)",
    "failure_mode": "REDUNDANT INVENTORY IN ALWAYS-LOADED SURFACE. Catalogs ~13 documentation files in three tables PLUS a Quick Reference Table that duplicates the same info. Already discoverable through Step 1 of MANDATORY WORKFLOW.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:483-537 contains three tables + a code block. Many entries (Module_Dependencies, Data_Flow, Query_Patterns_Reference) appear in BOTH Step 1's 'For cross-cutting questions' branch AND this section's tables.",
    "suggested_fix": "Compress to a 10-line pointer: keep the directory layout summary, drop the per-file tables. Replace with 'For full doc inventory with descriptions, see core_docs/README.md / agent/helpers/README.md / cross_module/README.md.' Headroom: ~45 lines saved.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:721-800 (LINK DON'T DUPLICATE section, ~80 lines)",
    "failure_mode": "OVERSIZED EDITORIAL POLICY IN ALWAYS-LOADED SURFACE. The Link Don't Duplicate section is doc-author policy (when to link vs duplicate, examples). It is ~80 lines of authoring guidance that only fires when EDITING docs — but it loads on EVERY session including pure Q&A.",
    "severity": "HIGH",
    "evidence": "AGENT.md:721-800. Section explicitly says 'When updating or creating documentation, follow these rules' — explicitly conditional, but always loaded.",
    "suggested_fix": "Hoist to `agent/helpers/link_dont_duplicate.md`, auto-load triggers: 'update doc', 'edit module_XX.md', 'add to documentation', 'doc edit'. Leave a 3-line marker. Headroom: ~77 lines saved.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:122-176 (SESSION CLEANUP section, ~55 lines)",
    "failure_mode": "OVERSIZED END-OF-SESSION PLAYBOOK IN ALWAYS-LOADED SURFACE. The full pull-rebase / commit / push / conflict-resolution playbook is in always-loaded surface, including a 5-line bash code block. Modern workflow uses the session-close skill, which has its own logic — this section is partially redundant.",
    "severity": "HIGH",
    "evidence": "AGENT.md:122-176. Includes bash block at lines 153-161 (commit instructions) which duplicates session-close skill behavior.",
    "suggested_fix": "Hoist to `agent/helpers/session_cleanup.md`, auto-load on end-of-session triggers. Reconcile with the session-close skill — pick one canonical source. Headroom: ~52 lines saved.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:217-262 (CRITICAL: Directory Structure & Path Resolution, ~46 lines)",
    "failure_mode": "OVERSIZED ORIENTATION DIAGRAM IN ALWAYS-LOADED SURFACE. Contains a 20-line ASCII directory tree + 4 'path resolution rules' + 4 'important distinctions' + 4 'git operations' bullets. Needed during fresh-installation orientation but loads on every session.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:217-262. ASCII tree at lines 222-240 is 19 lines.",
    "suggested_fix": "Trim to 8 lines: keep the 'AGENT.md vs ../AGENT.md vs ../CLAUDE.md' and 'modules/ vs ../modules/' distinctions. Hoist the rest to `agent/helpers/directory_structure.md`. Headroom: ~38 lines saved.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:610-654 (QUALITY GUARD section, ~45 lines, no magpie4-specific row)",
    "failure_mode": "GAP: bug distribution table covers only GAMS-side bug classes. No row for magpie4-specific bugs (wrong magpie4 version, wrong source path citation, GAMS-vs-magpie4 attribution). validate-semantic.md regression Q's G3 and G4 specifically guard magpie4 — those failure classes should appear here.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:621-630 (Bug Distribution table) and 634-640 (High-Risk vs Low-Risk). grep -nE 'magpie4|report.mif' AGENT.md:610-654 → no matches.",
    "suggested_fix": "Add to High-Risk content table: 'magpie4 source-of-truth citations | Output-interpretation answers grounded in GAMS code rather than magpie4 source'. Add brief paragraph after Cascade Effect.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:540-554 (QUICK MODULE FINDER, no R/reporting layer)",
    "failure_mode": "GAP: QUICK MODULE FINDER lists 46 GAMS modules organized by topic but omits the two LAYERS that sit beside the modules: (a) magpie4 (R reporting), (b) PREPROC layer (R packages that produce input.tgz).",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:544-552 enumerates GAMS modules in 8 groups. grep -nE 'magpie4|preproc|R packag|mrcommons' AGENT.md:540-554 → no matches.",
    "suggested_fix": "Append two lines after L552: '**Upstream (R preprocessing)**: madrat, mrcommons, mrmagpie, mrland, mrwater, mrdrivers (see PREPROC_AGENT.md)'. '**Downstream (R reporting)**: magpie4 → report.mif / IAMC variables (see agent/helpers/magpie4_reference.md)'.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:803-818 (QUICK RESPONSE CHECKLIST, no magpie4/preproc layer checks)",
    "failure_mode": "GAP: 10-item checklist covers GAMS verification only. No items for layer-specific verification: 'If answer involves report.mif / IAMC variables, cited magpie4 source path'.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:807-816 (10 checklist items). grep -nE 'magpie4|report.mif|preproc' AGENT.md:803-818 → no matches.",
    "suggested_fix": "Insert two items: '[ ] If report.mif / IAMC variable: cited magpie4 source (not just GAMS module)' and '[ ] If input data origin: routed to preproc-agent or cited mr* package'.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:691-718 (DOCUMENT HIERARCHY & READING ORDER, no output-interpretation branch)",
    "failure_mode": "GAP: reading-order diagram lists branches for 'User asks MAgPIE question' and 'User asks to WRITE or EDIT module documentation'. No branch for 'User asks about model output / report.mif / IAMC variable'.",
    "severity": "MEDIUM",
    "evidence": "AGENT.md:695-711 (two reading-order branches). Neither mentions magpie4 / report.mif / output.",
    "suggested_fix": "Insert a third branch: 'User asks about report.mif / IAMC variable / model output → agent/helpers/magpie4_reference.md → agent/helpers/interpreting_outputs.md → modules/module_XX.md (only if needed)'.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "AGENT.md:412-444 (Auto-Loading Context Helpers table, no 'session-close' or 'doc-edit' trigger rows)",
    "failure_mode": "GAP: triggers for `session_startup.md` exist but there's no trigger row for session-close or doc-edit workflows — yet SESSION CLEANUP and LINK DON'T DUPLICATE are full sections in always-loaded surface (because no helper-based routing exists). If those sections were hoisted, the trigger table would need new rows.",
    "severity": "LOW",
    "evidence": "AGENT.md:420-424 has only `session_startup.md` in always-load. L428-443 has no row for end-of-session or doc-editing intents.",
    "suggested_fix": "After hoisting SESSION CLEANUP and LINK DON'T DUPLICATE, add two rows for session_cleanup.md and link_dont_duplicate.md triggers.",
    "confidence": "MEDIUM"
  },
  {
    "lens": "L7",
    "location": "AGENT.md (drift between deployed copies)",
    "failure_mode": "NEGATIVE finding — drift check is CLEAN. AGENT.md, ../AGENT.md, and ../CLAUDE.md are byte-identical (846 lines / 46,041 bytes each). diff returns empty. Deploy hook is working.",
    "severity": "LOW",
    "evidence": "wc output: 846 46041 AGENT.md / 846 46041 ../AGENT.md / 846 46041 ../CLAUDE.md. diff AGENT.md ../AGENT.md → empty.",
    "suggested_fix": "No fix needed. Maintain the auto-deploy on session start.",
    "confidence": "HIGH"
  },
  {
    "lens": "L7",
    "location": "agent/helpers/*.md (helper sizes)",
    "failure_mode": "NEGATIVE finding — no individual helper exceeds the 5,000-word anchor. Largest is verifiers.md at 2,285 words; total across 14 helpers is 23,442 words. Helper bloat per-file is NOT an issue, but cross-helper trigger overlap means multiple helpers can load simultaneously (~10KB combined).",
    "severity": "LOW",
    "evidence": "wc -w agent/helpers/*.md → max 2,285 (verifiers.md), median ~1,650, total 23,442.",
    "suggested_fix": "No per-file fix. The cross-helper overlap is addressed by the broad-trigger findings above.",
    "confidence": "MEDIUM"
  }
]
```

---

## Next step

Synthesis (0d) — single Opus call to dedup/corroborate/cluster findings by root cause.
