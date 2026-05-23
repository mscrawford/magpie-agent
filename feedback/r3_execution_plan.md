# R3 Pipeline-Audit — Autonomous Execution Plan

**Status**: READY TO EXECUTE
**Mode**: autonomous (user is away; make reasonable calls and keep going)
**Written**: 2026-05-23, end of follow-up session that landed commits `9b58fa8..66f2833`

> **Future-self note**: this file is self-contained. If you read this with no prior context, that's expected — execute it as written. The "Why R3 over R22" decision is already made; do not relitigate.

---

## What you are doing

Running **round 3 of the pipeline-audit lens flywheel** — 6 parallel Opus sub-agents, each with a distinct lens, auditing the magpie-agent's own machinery. Then triaging findings and fixing what's fixable, autonomously.

This is the STRUCTURAL flywheel (audits machinery), not the BEHAVIORAL one (which would be `/validate-semantic` R22). See `agent/commands/pipeline-audit.md` for the full spec.

---

## Why R3 (not R22)

- Recent session shipped substantial infrastructure changes (M18 rewrite, Pattern 13 validator, Python validator rewrite, citation resolver fix, Pattern 12 heuristic tightening, marker refresh system). R3 stress-tests this surface.
- Per `[[feedback_confabulation_relocates]]`, R2 closed surfaces 1, 2, 3, 5, 6, 7 — bugs typically relocate to unguarded surfaces. R3 measures where.
- R3 produces actionable concrete findings; R22 might mostly confirm stable behavioral scores since the recent changes didn't directly target answer-shape.

---

## Pre-flight checks (do these first)

```bash
cd /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent
git log --oneline -6                              # should show 66f2833 at HEAD (or later if more landed)
git status -s                                     # should be clean
bash scripts/validate_consistency.sh 2>&1 | tail -5  # 34 passed, 1 advisory warning
python3 scripts/check_gams_variables.py 2>&1 | tail -3  # 944/944 verified
```

If validator fails or working tree is dirty: STOP and ask the user.

---

## Phase 1: Context loading (read these in order)

1. `agent/commands/pipeline-audit.md` — full lens spec, agent brief template, synthesis steps. **Critical read** — this defines the 6 lenses precisely.
2. `feedback/pipeline_audit_round1.md` — R1 baseline (71 findings, broken down by lens). Skim to know what was found before.
3. `feedback/pipeline_audit_rounds.json` — R1 + R2 JSON entries. R3 must mirror R1's schema (R2 used a fix+mechanize schema, different).
4. `feedback/next_session_plan.md` — progress log of what landed in the follow-up session (4 commits). Cross-check your work against the "Won't fix" list so you don't re-flag deliberately-deferred items.

Optional (skim if uncertain):
- `core_docs/Bug_Taxonomy.md` — 14 patterns Lens 3 should probe against
- `agent/helpers/verifiers.md` — 16 MANDATEs Lens 4 audits as a target surface
- `feedback/flywheel_rubric.md` — severity scoring

---

## Phase 2: Spawn 6 sub-agents in parallel

Use the **Agent** tool, `subagent_type: general-purpose`, `model: opus`, all 6 in a **single message with 6 Agent tool calls** (parallel execution — critical for wall-clock).

Each agent gets the shared brief template (in `pipeline-audit.md` line ~68) filled with that lens's slots. **Augment with R3-specific context** so agents don't redundantly find R2-fixed material:

> **R3 context (add to each agent's brief)**:
>
> Since R1+R2 (same calendar day), these infrastructure changes have landed (commits `8932040..66f2833`):
> 1. **M18 body rewrite** — now leads with default `flexreg_apr16` (9 regional equations); `flexcluster_jul23` moved to Alternative Realization section
> 2. **Check 20 (Pattern 13)** — `scripts/check_param_defaults.py` flags `(default N)` doc claims vs `config/default.cfg` + `input.gms`
> 3. **GAMS regex extension** — `check_gams_variables.{sh,py}` now covers `c<N>_`, `sm_`, `cm_` prefixes
> 4. **Python validator rewrite** — `check_gams_variables.py` replaces bash (~50x faster, tighter wildcard filter)
> 5. **Citation resolver fix** — `check_gams_citations_impl.py` now honors realization-prefix paths (e.g., `flexreg_apr16/equations.gms`) instead of walk-order
> 6. **Pattern 12 heuristic tightened** — `nearby_ids` window scoped to (prev_cite, +/-40/10 chars)
> 7. **Aggregate-count refresh** — `scripts/refresh_aggregate_counts.py` + HTML `<!--count:KEY-->...<!--/count-->` markers in AGENT.md, verifiers.md, validate-semantic.md, pipeline-audit.md
> 8. **Per-doc allowlist** — `<!-- check-gams-vars: allow NAME -->` marker for legitimate placeholders
>
> **Bias your hunt toward**:
> - Defects in the above NEW infrastructure (validators with FPs/FNs; resolver edge cases; marker system gaps; M18 doc-internal consistency)
> - Surfaces R2 did NOT close (per `feedback/next_session_plan.md` "Won't fix" list): unbacktiked-prose variables, 766 remaining bare-basename advisories, M13 internal cleanup
> - Confabulation relocation: with stronger guards on var names + realizations + citations, where did the next bugs surface? (Bug_Taxonomy patterns NOT yet mechanized are the natural targets.)
>
> **De-prioritize** (already fixed; if found, note as "R2-fixed, regression"):
> - M18 walks the wrong realization (FIXED)
> - `sm_cdr_target` confabulation in M56 (FIXED)
> - Pattern 12 advisories from 25 down to 2 (mostly FIXED)
> - Aggregate-count drift in headers of audit docs (FIXED — markers now)

Per-lens guidance is in `pipeline-audit.md`. Use it verbatim except for the augmentation above.

---

## Phase 3: Aggregate findings

Each agent returns a JSON array of findings plus a 2-3 line summary. Process:

1. **Collect** all findings into one list (Python dict or in-memory)
2. **Dedupe** by `(location, failure_mode)` — multiple lenses finding the same defect is corroboration; record but don't double-count
3. **Sort** by severity (CRITICAL > HIGH > MEDIUM > LOW)
4. **Cluster** by shared root cause (per `[[feedback_synthetic_interventions]]`): N findings often collapse to far fewer interventions

---

## Phase 4: Log R3 entry

### File A: `feedback/pipeline_audit_round3.md` (mirror R1 format)

Sections to include:
- Header: round, date, status, auditor model
- Top-line numbers table (per lens + severity distribution)
- Corroborated findings (where ≥2 lenses agree)
- Root-cause clusters (the synthetic interventions)
- Per-lens summary (1-2 paragraphs each, with key findings cited as `file:line`)
- Comparison to R1 (which categories shrank, where bugs relocated)
- Recommended next mechanization candidates (which Bug_Taxonomy pattern still has 0% validator coverage?)
- Status section (what was fixed in this session, what's deferred)

### File B: append to `feedback/pipeline_audit_rounds.json` (R1 schema)

Schema keys (copy from R1 entry):
```
{
  "round": 3,
  "date": "2026-05-23",  // or today's date
  "commit": "<HEAD sha after fixes>",
  "auditor_model": "claude-opus-4-7",
  "round_type": "lens audit",
  "lenses_run": 6,
  "findings_total": <count>,
  "by_severity": {"CRITICAL": N, "HIGH": N, "MEDIUM": N, "LOW": N},
  "by_lens": {"1": N, "2": N, "3": N, "4": N, "5": N, "6": N},
  "corroborated": [...],
  "root_cause_clusters": [...],
  "recurring_classes_for_mechanization": [...],
  "report_path": "feedback/pipeline_audit_round3.md",
  "guards_added": [<list of validators or markers added in this round>],
  "status": "<Triaged; partial fixes applied; X deferred>",
  "notes": "<1-2 paragraph synthesis>"
}
```

---

## Phase 5: Triage and fix (autonomously)

For each finding, decision rule:
- **CRITICAL / HIGH**: fix directly. These are real defects.
- **MEDIUM**: fix if mechanical (line-number drift, missing realization prefix, marker key typo); document if it needs judgment.
- **LOW**: document only, don't fix unless trivial (≤1 minute).
- **Style preferences disguised as findings**: ignore.

**Per `[[feedback_synthetic_interventions]]`**: group findings by shared root cause and fix the root. If 8 findings all stem from "doc cites bare basename, walk-order picks wrong realization", the intervention is a single regex/script change, not 8 individual citation patches.

**Per `[[feedback_verifier_layer_coupling]]`**: if you fix a validator's detection layer, re-validate its evaluation layer (worked examples, calibration). Audit every output flip.

**Where you'd need to ask the user**: document the question + your best-guess answer in the R3 report's "deferred" section, mark the finding `status: deferred`, and continue.

---

## Phase 6: Verify

After fixes:

```bash
bash scripts/validate_consistency.sh 2>&1 | tail -5
# Expect: 34 (or 35) passed; the s59_nitrogen_uptake advisory may still be there
python3 scripts/check_module_realizations.py 2>&1 | tail -3
# Expect: 0 errors
python3 scripts/check_gams_variables.py 2>&1 | tail -3
# Expect: 100% verified
python3 scripts/refresh_aggregate_counts.py --dry-run
# Expect: "All markers already up to date" OR a small set of drift updates from new validator counts
```

If anything regressed: investigate before committing.

After running validators, the cumulative_stats in `validation_rounds.json` likely needs a refresh (validator counts shift). Update `cumulative_stats` to current values, then `python3 scripts/refresh_aggregate_counts.py` to propagate to docs.

---

## Phase 7: Commit + push

Commit strategy:
- **One commit per root-cause cluster of fixes** (clusters typically 3-10 findings each)
- **Final commit**: R3 audit log + JSON entry + any housekeeping (next_session_plan.md update)
- **Push at the end** when everything passes

Commit message format (mirror today's commits in `git log --oneline`):
```
<verb>: <one-line summary>

<2-3 sentence context>

== Findings addressed (R3) ==
- <finding 1> (Lens N, severity)
- ...

== Verification ==
- validators: <result>
- ...

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

(Use a heredoc to file to avoid shell escaping bugs with backticks in body; see today's `tier2_commit_msg.txt` pattern.)

---

## Update `feedback/next_session_plan.md`

After R3 lands:
- Mark Tier 3 item 7 as done
- Add R3 progress section (mirror the Tier 1+2 progress sections)
- Update "Won't fix" list with anything R3 surfaced but you chose not to fix
- Keep item 8 (R22) as the next tier-3 candidate

---

## Anticipated findings (don't be surprised by these)

Educated guesses based on what we shipped:
- **Pattern 12 heuristic possibly too tight** — Lens 3 may flag false negatives (real bugs the tighter window now misses). Re-tune if so.
- **Citation resolver fix shifted resolution** — Lens 1 or 2 may find new drift in docs that previously relied on walk-order picking a specific realization.
- **Marker system gaps** — any aggregate count NOT yet covered by a marker that's still drifting?
- **M13 still likely walks non-default realization content** (similar to M18 pre-rewrite) — Lens 1 may catch.
- **M09 dependency-count claim** changed from `im_gdp_pc_ppp Used by 4 modules` to `im_gdp_pc_mer Used by 1 module` — Lens 5 may verify the count is right.
- **Unbacktiked prose variables** (82% of references per R1) still unenforced — Lens 3 will likely re-flag as `Pattern 13.5` or whatever the right name is.
- **Pattern 13 advisory cleanup** still has 1 case (s59_nitrogen_uptake unit conversion) — Lens 3 may have opinion on whether the script should detect "kg N/ha" → "tN/ha" automatically.
- **AGENT.md size after marker additions** — Lens 6 may flag the markers as bloat (they're ~30 chars per occurrence).
- **Hoist completion regression** — Lens 4 may find that the CRITICAL WARNINGS section in AGENT.md (lines 606-635 in R1) is *still* duplicating verifiers.md content. (R1 noted this but R2 may not have cleaned it.)

If R3 surfaces ZERO of these, that's also useful signal — would indicate the audit is missing things in those areas.

---

## Stopping criteria

- All CRITICAL and HIGH findings either FIXED or DOCUMENTED in R3 report's deferred section with reason
- Validator passes cleanly (or only known-good advisories remain)
- R3 log committed + pushed
- `feedback/next_session_plan.md` updated

If you've spent ~3 hours and aren't done: commit what you have, push, and note remaining work in next_session_plan.md. Don't leave a dirty tree.

---

## What to NOT do

- Don't relitigate the R3 vs R22 decision. R3 is chosen.
- Don't run `/validate-semantic` (that's R22 territory; the user will trigger it separately).
- Don't push to `pik-piam/*` remotes — only `mscrawford` fork via `origin/main` (per `~/.claude/CLAUDE.md` Code Conventions).
- Don't skip pre-commit hooks (`--no-verify`).
- Don't rewrite next_session_plan.md from scratch — append/edit the progress section.
- Don't run the magpie model or anything that uses GAMS (this is a doc-only round).

---

## Memory linkages worth checking when relevant

- `[[feedback_confabulation_relocates]]` — guides where to look for new bugs
- `[[template_verifier_mandate_flywheel]]` — the 4-step cycle (measure → mechanize → bind → re-measure); R3 is the "re-measure" after the recent "bind" round
- `[[feedback_synthetic_interventions]]` — group fixes by root cause
- `[[feedback_verifier_layer_coupling]]` — re-validate worked examples when you change a verifier
- `[[template_multi_agent_audit]]` — pipeline-audit IS this template; you're just running another iteration
- `[[bash-grep-r-unreliable-magpie]]` — verify absence with Read or a subagent, not grep -r
