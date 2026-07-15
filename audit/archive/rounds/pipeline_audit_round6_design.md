# Pipeline Audit — Round 6 (R6) Design: "Stale and Remnant"

**Date**: 2026-05-25
**Round type**: Doc-surface drift audit (NOT doc↔code fidelity)
**Trigger**: Phase 0 of `audit/get_under_control_plan.md`
**Auditor model**: `claude-opus-4-7` × 7 parallel, one per lens (user upgraded from Sonnet 2026-05-25 — judgment-heavy lenses L2/L6 in particular benefit; cost calculus accepts higher per-agent spend in exchange for skipping 0c re-run)
**Synthesis model**: `claude-opus-4-7` (single call, after lens agents return)

---

## Why this round is differently-shaped from R1–R5

R1–R5 ran the standard 6-lens template baked into `agent/commands/pipeline-audit.md`. Those lenses
hunt **doc↔code drift** (`vm_*` names, equation names, realization names, file:line citations,
default values). They are saturating: R4 dropped to 0 CRITICAL, R5 held at 0 CRITICAL.

R6 hunts a different failure class entirely: **doc-surface drift**. R24 surfaced seven instances
while debugging — none would have been caught by R1–R5's lenses, because no GAMS code was wrong;
the agent's own scaffolding had silently rotted. Examples:

- `project/CURRENT_STATE.json` declared "SINGLE SOURCE OF TRUTH" but `last_updated: 2026-03-07` (78 days)
- README routes four times to that stale SSOT
- ~10 `module_XX_notes.md` files are empty templates
- `validation_report_20260517_*.txt` and `validation_report_20260524_*.txt` sit in `/magpie/` root (parent), not gitignored
- AGENT.md is 46KB / 846 lines (Claude warning threshold)
- magpie4 is missing from MANDATORY WORKFLOW despite being a load-bearing layer
- README claims "~290K words" while AGENT.md claims "~342K words"

Each of these became the **calibration anchor** for one of seven lenses below. The audit's job is
to find the **siblings** of each anchor systematically — not whack-a-mole on each instance as it
happens to surface.

### Lens-count change vs `/pipeline-audit` default

7 lenses (not 6). The standard template's six lenses are split between code-fidelity (L1–L2),
validator soundness (L3), instruction surface (L4), cross-doc (L5), efficiency (L6). For R6 we
deliberately drop code-fidelity (saturated) and validator soundness (separate Phase 1) and expand
the instruction-surface/cross-doc/efficiency surface into seven decorrelated sub-lenses, each
calibrated by a concrete R24 anchor.

### Decorrelation by method (engineered, not hoped for — per [[template_multi_agent_audit]])

| Lens | Distinct method |
|---|---|
| L1 | `stat` + parse `"last_updated"` / `"as of"` claims; flag mtime ≠ semantic-date drift |
| L2 | Extract rule sentences (must/never/always); audit compliance via `git log` + actual file edits |
| L3 | `wc -w` + pattern-match for template placeholders / "no X recorded yet" / `<!-- TODO -->` |
| L4 | Extract numeric/path/date tokens; tabulate occurrences across files; diff |
| L5 | `ls` parent repo + `magpie-agent/` root; check `.gitignore` coverage |
| L6 | Follow "see X" / "authoritative" links graph-style; check freshness of each target |
| L7 | `wc -w`; helper trigger overlap; coverage check of MANDATORY WORKFLOW vs load-bearing layers |

---

## Shared brief template

Each agent is spawned with the `Agent` tool, `subagent_type: general-purpose`, `model: opus`,
all 7 in parallel (single message, 7 tool calls). The per-lens slots `<...>` below get filled per
prompt.

```
You are auditing the magpie-agent's own pipeline. This is /pipeline-audit Round 6,
focused on doc-surface drift (NOT doc↔code fidelity). You are one of 7 parallel
Opus sub-agents with decorrelated lenses — do your lens, don't drift into others'.

Working directory: <magpie-agent>
This is a READ-ONLY audit. Do NOT edit, write, commit, or push anything.

Your lens: <name>
Anchor (R24 ground truth — the seed you are looking for siblings of):
  <one or two concrete examples with file:line and the exact evidence>

Scope: <files / directories — list them precisely>
Hunt for: <failure mode>
Method: <how to find them — concrete, operational steps>
Ground truth: <what the agent checks claims against>

<per-lens specifics — extra guidance, gotchas, things to NOT do>

Rules:
- Read-only. No edits, no writes, no commits.
- Cite file:line for every finding.
- Each finding MUST carry reproducible evidence: a command someone can run, or
  a concrete excerpt — so the finding is verifiable without re-trusting you.
- Propose a fix per finding; do NOT apply it.
- Distinguish a real defect from a style preference; rate severity honestly.
- If a category is genuinely clean, say so plainly — do not pad.
- Do NOT drift into lenses owned by your siblings (listed at the bottom).
- Confidence levels: HIGH = independently re-derivable; MEDIUM = depends on your
  interpretation; LOW = pattern-match without verification.

Return a JSON array of findings, each:
  {lens, location, failure_mode, severity (CRITICAL|HIGH|MEDIUM|LOW),
   evidence, suggested_fix, confidence (HIGH|MEDIUM|LOW)}
followed by a 2-3 line free-text summary.

Sibling lenses you should NOT duplicate:
  L1 Staleness | L2 Dead conventions | L3 Half-deployed patterns
  L4 Cross-doc inconsistency | L5 Misplaced outputs | L6 Reference-graph integrity
  L7 Surface bloat + workflow gaps
```

---

## Lens prompts

### L1 — Staleness (currency claims vs actual content age)

```
Your lens: L1 — Staleness

Anchor (R24 ground truth):
  project/CURRENT_STATE.json declares itself "🚨 THE SINGLE SOURCE OF TRUTH FOR
  ALL PROJECT STATUS 🚨" (line 2) and instructs "Update this file after completing
  work" (line 3). But line 5: `"last_updated": "2026-03-07"` — 78 days before
  this audit. File mtime is recent (2026-05-24) but content has not been
  semantically updated. KEY DISTINCTION: mtime-fresh ≠ content-fresh.

Scope:
  - project/CURRENT_STATE.json + any other project/*.json
  - audit/*.json (validation_rounds.json, pipeline_audit_rounds.json, etc.)
  - All README.md files (./README.md, modules/README.md, agent/helpers/README.md,
    audit/README.md, reference/README.md, scripts/README.md if present)
  - AGENT.md (`Last updated: ...` footers)
  - All agent/helpers/*.md (some have "Lessons Learned" sections with dated entries)
  - audit/global/agent_lessons.md
  - project/sync_log.json
  - reference/dependency_analysis/* (claims to be living docs per plan; check)

Hunt for: files that CLAIM currency (via wording like "current", "latest",
  "up to date", "as of DATE", "last updated DATE", "living document", "SSOT",
  "source of truth", "today", "this week", "recent") but whose internal evidence
  (last_updated field, latest dated entry, latest commit affecting the file's
  semantic content) is >60 days old.

Method (operational):
  1. For each file in scope, look for "currency-claim" wording. List the file
     and the line where it claims currency.
  2. Find the file's internal "as-of" evidence:
     - JSON: look for "last_updated" / "as_of" / "date" fields
     - MD: look for "Last updated: YYYY-MM-DD", footers, or dated entries
     - For dated-log files (validation_rounds.json), find the latest entry date
  3. Compute age: today (2026-05-25) minus internal-evidence date.
  4. Cross-check mtime via `stat -f "%Sm %N" -t "%Y-%m-%d" <file>` — note when
     mtime is fresh but content is stale (THIS is the high-value finding;
     a file that was touched yesterday but whose data is from March is worse
     than one openly admitting it's an October snapshot).
  5. Flag as a finding when age >60 days AND the file claims currency.

Ground truth: today (2026-05-25); file mtimes via `stat`; internal date fields.

Specifics:
  - The anchor (CURRENT_STATE.json) is itself a finding — log it as anchor=true.
  - reference/dependency_analysis/ was flagged in the plan as "presented as
    living docs but Oct-2025 snapshot" — verify and report concrete evidence.
  - Dated-log files (validation_rounds.json) are not "stale" if append-only logs
    that explicitly log dated history — distinguish "history log" from
    "current-state claim".
  - Files explicitly labeled "snapshot YYYY-MM-DD" are NOT findings —
    they're honestly dated.

Do NOT (sibling-lens fences):
  - Do NOT audit "X is authoritative" pointers from other files (that is L6).
  - Do NOT audit oversize files (that is L7).
```

### L2 — Dead conventions (documented rules nobody follows)

```
Your lens: L2 — Dead conventions

Anchor (R24 ground truth):
  README.md and project/CURRENT_STATE.json both prescribe "all updates go in
  CURRENT_STATE.json" / "Do NOT update README.md or modules/README.md with status
  information" (CURRENT_STATE.json line 3). In practice CURRENT_STATE.json has
  not been updated since 2026-03-07; status updates have happened in audit/*.json
  and commit messages instead. The convention is documented but dead.

Scope:
  - AGENT.md (rules / "always" / "never" / "must" statements)
  - README.md (project-level conventions)
  - modules/README.md, agent/helpers/README.md, audit/README.md
  - agent/helpers/maintenance_protocol.md
  - agent/helpers/session_startup.md (session-start rituals)
  - agent/commands/*.md (workflow prescriptions)

Hunt for: rules that are stated as binding ("ALWAYS X", "NEVER Y", "All updates
  go in Z", "Run X after every Y") but actually NOT followed in recent practice.
  Practice evidence comes from: `git log --since=2026-04-01 -- <referenced-target>`,
  inspecting the latest content of the file the rule prescribes editing, and
  checking whether the prescribed location has fresh entries.

Method (operational):
  1. Grep each scoped file for rule-language: "ALWAYS", "NEVER", "MUST", "SHOULD",
     "DO NOT", "all updates", "every session", "after every", "before every",
     "single source of truth", and similar.
  2. For each rule, identify what it prescribes (an action + a target file/location).
  3. Verify the rule is followed:
     - If "all X go in Y", check `git log --since=2026-04-01 -- Y` and recent
       contents of Y. Does Y show evidence of being maintained as prescribed?
     - If "always run X", check recent run artifacts / log entries.
     - If "always check X first", inspect helper trigger tables / AGENT.md
       workflow sections — is X actually first in the routing?
  4. Flag rules where prescribed action is not happening in practice.

Ground truth: recent git log + actual content of the prescribed targets.

Specifics:
  - The anchor (CURRENT_STATE.json update rule) is itself a finding.
  - The rule "all updates go in CURRENT_STATE.json" appears in multiple files
    per the plan — report each instance separately if found.
  - A rule that USED to be followed but isn't anymore is the bug class.
  - Distinguish "rule never enforced" from "rule recently broken" — both
    findings but different severity.

Do NOT (sibling-lens fences):
  - Do NOT flag stale FILES (that is L1).
  - Do NOT audit broken cross-doc references (that is L6).
  - Do NOT flag rule REDUNDANCY (the same rule in multiple places is L4).
```

### L3 — Half-deployed patterns (empty templates, stub scaffolds)

```
Your lens: L3 — Half-deployed patterns

Anchor (R24 ground truth):
  ~10 module_XX_notes.md files exist as empty templates (only frontmatter +
  section headers + "No notes recorded yet" placeholders, no real content).
  Evidence: `wc -w modules/module_*_notes.md` shows several files with very low
  word counts; sample command for the user to corroborate:
    for f in modules/module_*_notes.md; do
      echo "$(wc -w < "$f") $f"
    done | sort -n | head -15

Scope:
  - All modules/module_*_notes.md files (18 exist as of 2026-05-25)
  - audit/global/*.md (agent_lessons.md, etc.)
  - reference/dependency_analysis/* (per plan: presented as living but Oct snapshot)
  - reference/archive/, audit/archive/ (potential remnants)
  - Any other directory containing template-style scaffolds (commands/, helpers/)
  - project/ — any stub config / template files

Hunt for: files / sections that are SCAFFOLDED but EMPTY. Patterns include:
  - "No X recorded yet" / "No entries yet" / "TODO" / "TBD"
  - Files containing only headers + "(append-only)" + nothing
  - Files at <50 words that are listed as deployed (not snapshots)
  - HTML/markdown comments like "<!-- TODO -->", "<!-- placeholder -->"
  - Stub commands (agent/commands/*.md with <100 words and no real workflow)
  - "Lessons Learned" sections in helpers with 0 entries despite the helper
    being old enough to have accumulated some

Method (operational):
  1. Build a size inventory:
       for f in modules/module_*_notes.md audit/global/*.md reference/dependency_analysis/*; do
         echo "$(wc -w < "$f") $f"
       done | sort -n
  2. For files with low word counts, read them and classify:
     EMPTY-TEMPLATE: only headers + placeholder text (real bug)
     HONEST-SNAPSHOT: dated and marked as a snapshot (not a bug)
     LIVING-EMPTY: declared as living/append-only but no entries (bug)
  3. Grep for placeholder patterns in larger files too:
       grep -nrI -E "TODO|TBD|placeholder|to be filled|no entries yet|no .* recorded" \
         modules/ agent/ audit/ reference/ project/
  4. For "Lessons Learned" sections, check if helper is >30 days old AND has
     zero appended entries → flag as stalled append-pattern.

Ground truth: file word count + grep for placeholder patterns; helper age via
  git log to see if the file has been alive long enough to expect content.

Specifics:
  - The anchor (~10 empty notes files) is itself a finding cluster.
  - Distinguish: (a) intentionally-stub commands (e.g., new command not yet
    implemented) — note as such if creation date is recent (<14 days);
    (b) abandoned/forgotten scaffolds (older).
  - Report TOTAL count of empties per directory, not 18 individual findings —
    each cluster is one finding with a list inside.

Do NOT (sibling-lens fences):
  - Do NOT audit cross-doc reference targets (that is L6).
  - Do NOT flag oversized files (that is L7).
  - Do NOT flag stale-by-content files that DO have content (that is L1).
```

### L4 — Cross-doc inconsistency (same fact, different values)

```
Your lens: L4 — Cross-doc inconsistency

Anchor (R24 ground truth):
  README.md line 107 (or similar) states "~290,000 words" of documentation;
  AGENT.md "📚 COMPLETE DOCUMENTATION STRUCTURE" section claims "~342,000 words".
  Same fact, different values, no HTML-comment marker linking them.
  Reproduce: grep -E "290|342" README.md AGENT.md | grep -i word

Scope:
  - AGENT.md (and deployed copies ../AGENT.md, ../CLAUDE.md if they exist)
  - README.md, modules/README.md, agent/helpers/README.md, audit/README.md
  - All agent/helpers/*.md
  - All agent/commands/*.md
  - core_docs/*.md
  - audit/flywheel_rubric.md (cross-referenced from AGENT.md)
  - agent/helpers/verifiers.md (the hoisted MANDATEs — must agree with AGENT.md's
    short index)

Hunt for: the SAME factual claim stated with DIFFERENT values across files.
  Examples of fact-tokens to compare:
  - Aggregate word counts ("~290K words" vs "~342K words")
  - Command counts ("6 commands" vs "10 commands" vs "11 commands")
  - Helper counts ("9 helpers" vs "14 helpers")
  - Module counts (should be 46 everywhere)
  - Validator main-checks count (already tracked via <!--count:validator_main_checks--> marker)
  - Pattern counts (Bug_Taxonomy has 14 patterns — does AGENT.md agree?)
  - MANDATE counts (verifiers.md has 16 — does AGENT.md short index agree?)
  - Dates ("Last updated: ..." that should match a known event)
  - Paths (e.g., AGENT.md citing a file path that has moved)
  - Round counts (validation rounds, pipeline rounds)
  - Realization counts per module

Method (operational):
  1. Extract numeric+noun phrases from each scoped file:
       grep -nE "[0-9]+[KkMm]?\s*(words|modules|helpers|commands|patterns|MANDATEs|checks|rounds|realizations|bugs|fixes|equations)" \
         AGENT.md README.md modules/README.md agent/helpers/README.md \
         agent/helpers/*.md agent/commands/*.md core_docs/*.md audit/*.md
  2. Tabulate the same noun across files. Where the numeric differs, flag.
  3. For paths: grep for "magpie-agent/" and "../modules/" references across docs;
     verify the paths resolve.
  4. For dates: grep "Last updated:" / "as of" / "YYYY-MM-DD" patterns; where
     the same event is dated differently, flag.
  5. For tokens already wrapped in <!--count:NAME--> markers, no finding —
     the marker mechanism handles those. Findings are tokens that SHOULD be
     marker-managed but aren't.

Ground truth: token-by-token diff across files; cross-reference with
  validation_rounds.json `cumulative_stats` where it exists.

Specifics:
  - The anchor (290K vs 342K) is itself a finding.
  - Distinguish "internal contradiction" (two values in one file) from
    "cross-file drift" (value matches within file but differs across files).
  - Some discrepancies are LEGITIMATE (e.g., a count that explicitly says
    "as of October" vs current count). Read context before flagging.
  - For each finding, propose: either a marker (<!--count:foo-->N<!--/count-->)
    + entry in refresh_aggregate_counts.py MARKER_VALUES, or a manual reconciliation.

Do NOT (sibling-lens fences):
  - Do NOT flag stale files per se (that is L1).
  - Do NOT audit broken pointers (that is L6).
  - Do NOT audit oversized files (that is L7).
  - Do NOT chase doc↔code drift — count-against-actual-grep is the standard
    /pipeline-audit lens; this lens is doc↔doc only.
```

### L5 — Misplaced outputs (files in wrong directories + .gitignore gaps)

```
Your lens: L5 — Misplaced outputs

Anchor (R24 ground truth):
  <magpie-root>/validation_report_20260517_102617.txt
  <magpie-root>/validation_report_20260524_095554.txt
  Both files are validator OUTPUT from magpie-agent's scripts but landed in the
  PARENT magpie/ repo root. Neither is in either repo's .gitignore.
  Reproduce: ls <magpie-root>/validation_report_*.txt
             grep -E "validation_report" \
               <magpie-root>/.gitignore \
               <magpie-agent>/.gitignore

Scope:
  - Parent <magpie-root>/ (top-level only,
    NOT magpie-agent/ subtree — that's our home)
  - <magpie-agent>/ root (top-level)
  - .gitignore at both levels
  - scripts/*.py and scripts/*.sh — check where they DEFAULT to writing output

Hunt for:
  1. Files in the parent magpie/ root that look like magpie-agent OUTPUT
     (validation reports, audit JSON, log files, sync logs).
  2. Files in magpie-agent/ root that should live in a subdirectory
     (audit artifacts loose at root, untracked .txt / .json / .log files).
  3. .gitignore gaps: output patterns the scripts generate that aren't ignored.
  4. Scripts whose default-output path is wrong (e.g., writes to ../foo/ when
     it should write to audit/).

Method (operational):
  1. List files in parent magpie/ root (not magpie-agent/):
       ls -la <magpie-root>/ | grep -v "^d"
     Then classify each: belongs (MAgPIE), doesn't belong (agent output), unclear.
  2. List files in magpie-agent/ root:
       ls -la <magpie-agent>/ | grep -v "^d"
     Same classification.
  3. Read both .gitignore files. Cross-reference against the output patterns
     in scripts:
       grep -rhE "(validation_report|with open.*[\"'].*\.(txt|json|log|md)|>\s*[^ ]+\.(txt|json|log))" scripts/ | sort -u | head -50
     For each output pattern, check whether the resulting file (a) lives in
     the right place, (b) is gitignored.
  4. Check git status in both repos — anything `??` (untracked) that fits
     an output pattern is a candidate.

Ground truth: `ls` + `.gitignore` content + script source greps.

Specifics:
  - The anchor (validation_report_*.txt in parent root) is itself a finding.
  - Distinguish "should be in agent/audit/" from "should be in /tmp/" from
    "should not be created at all".
  - .gitignore patterns must live in the REPO that contains the file. Parent
    .gitignore can't ignore something in magpie-agent/ (separate repo).
  - For each finding, propose: (a) move the file, (b) update the script's
    default-output path, (c) add a .gitignore entry, or some combination.

Do NOT (sibling-lens fences):
  - Do NOT audit doc content of any kind (that's L1-L4, L6, L7).
  - Do NOT audit empty scaffold files (that is L3).
```

### L6 — Reference-graph integrity (pointers vs target health)

```
Your lens: L6 — Reference-graph integrity

Anchor (R24 ground truth):
  README.md and project/README.md and modules/README.md and one other location
  each route to project/CURRENT_STATE.json as the "single source of truth" for
  project status. CURRENT_STATE.json has last_updated 2026-03-07 (78 days old).
  Result: four authoritative pointers route readers to a stale target.
  Reproduce: grep -rn "CURRENT_STATE" README.md modules/README.md \
             agent/helpers/README.md audit/README.md project/README.md 2>/dev/null

Scope:
  - AGENT.md (links / "see X" / "check Y first" pointers)
  - README.md and all subordinate README.md files
  - All agent/helpers/*.md (cross-references between helpers and to module docs)
  - All agent/commands/*.md
  - core_docs/*.md (cross-doc references)
  - cross_module/*.md
  - audit/*.md (round reports often reference other audit artifacts)

Hunt for: "X is authoritative" / "see X for details" / "check X first" / "X is
  the source of truth" / "always consult X" pointers whose TARGET is either
  (a) stale (per L1's findings — but you re-verify independently), or
  (b) does not exist (broken link), or
  (c) is itself a pointer to yet another doc (transitive — note the chain).
  Also: hub-target asymmetry — a target that many docs point at but the target
  doesn't link back / acknowledge those dependencies.

Method (operational):
  1. For each scoped file, grep for pointer-language:
       grep -nE "(see |refer to |consult |source of truth|authoritative|check .* (first|always))" <file>
  2. For each pointer, identify the target file/section.
  3. Check the target:
     - Does the file exist? `ls <target>`
     - If it has a date field or "last updated" / mtime is old, flag age.
     - If the target is itself a pointer, follow the chain. Note depth.
  4. Build the in-degree of each target across the pointer graph:
       For each frequently-pointed-at target (in-degree >=3), inspect target's
       freshness and whether it acknowledges its dependents.
  5. Flag: pointer where target is dead/stale/transitive >=2 hops without
     intermediate value.

Ground truth: file existence (`ls`) + target's internal currency claims +
  the pointer graph you build.

Specifics:
  - The anchor (4 READMEs → stale CURRENT_STATE.json) is itself a finding.
  - Distinguish: (a) routing to a TRULY authoritative target (good) vs
    (b) routing to a target that has been silently deposed (bad).
  - You may overlap with L1 — that is OK. L1 finds stale TARGETS; you find
    POINTERS to stale targets. Both worth recording; synthesis will dedup.
  - Bidirectional check: if `helpers/README.md` says "9 helpers" but
    `AGENT.md` lists 14, the pointer "AGENT.md → helpers/README.md" is
    routing to a stale index. (You may also report this under L4 — that is OK.)

Do NOT (sibling-lens fences):
  - Do NOT flag pure mtime staleness without a pointer (that is L1).
  - Do NOT flag rule-non-compliance (that is L2).
  - Do NOT flag oversize docs (that is L7).
```

### L7 — Surface bloat + workflow gaps (always-loaded weight; missing layers)

```
Your lens: L7 — Surface bloat + workflow gaps

Anchor (R24 ground truth — two anchors, two surfaces):
  1. BLOAT: AGENT.md is 46,041 bytes / 846 lines. Claude's size warning
     threshold is ~40KB / ~600 lines for always-loaded surface (per the plan;
     verify via `wc -lc AGENT.md`).
  2. GAP: magpie4 (the R reporting package) is a load-bearing layer for any
     report.mif or output-interpretation question. It has its own helper
     (agent/helpers/magpie4_reference.md) and auto-load trigger. But it is
     MISSING from AGENT.md's MANDATORY WORKFLOW section, MISSING from the
     QUICK MODULE FINDER, and not surfaced in the QUALITY GUARD lessons.
     Reproduce: grep -nC2 "magpie4" AGENT.md (should show only the helper
     entry; nothing in MANDATORY WORKFLOW Step 1 / 2 / etc.)

Scope:
  - AGENT.md (the source — and its deployed copies ../AGENT.md and ../CLAUDE.md)
  - All agent/helpers/*.md (size + always-loaded behavior)
  - agent/helpers/README.md (helper inventory)
  - agent/helpers/session_startup.md (the auto-loaded startup checklist)
  - agent/commands/pipeline-audit.md, validate-semantic.md, etc. (often
    reference always-loaded surface)

Hunt for: two sub-failure modes.

  A) BLOAT: always-loaded or near-always-loaded files that are oversize.
  - AGENT.md > 40KB or > 600 lines → finding.
  - Any agent/helpers/*.md > 5,000 words → finding (large enough to hurt
    when auto-loaded).
  - Helper trigger lists with broad/generic keywords ("module", "equation",
    "default") that cause many sessions to auto-load the helper without
    needing it → finding.
  - Deployed copies (../AGENT.md, ../CLAUDE.md) that have drifted from
    magpie-agent/AGENT.md → finding (`diff` to verify; CLAUDE.md being the
    one in Claude's system prompt makes drift load-bearing).

  B) GAP: load-bearing layers missing from workflow / index sections.
  - AGENT.md MANDATORY WORKFLOW Step 1 lists check sequences. magpie4 docs
    aren't part of the sequence even though report-question routing needs them.
  - QUICK MODULE FINDER omits load-bearing layers (magpie4, preproc-agent?).
  - QUICK RESPONSE CHECKLIST doesn't cover layer-specific verifications
    (e.g., "check magpie4 vs GAMS attribution for report.mif claims").
  - Auto-load trigger table missing keywords that should route to an
    existing helper (the helper exists but its triggers don't fire).

Method (operational):
  1. Size baseline:
       wc -lc AGENT.md ../AGENT.md ../CLAUDE.md
       wc -w agent/helpers/*.md | sort -n
       wc -w agent/commands/*.md | sort -n
  2. Drift check:
       diff AGENT.md ../AGENT.md
       diff AGENT.md ../CLAUDE.md
  3. Trigger-overlap check: for each helper's auto-load triggers (from
     AGENT.md's "Auto-load rules" table), check how often the trigger
     keywords occur in typical user queries (or just inspect for overly
     broad words like "module"/"code"/"equation").
  4. Workflow coverage check: enumerate the "load-bearing layers" the
     agent uses (module docs, cross_module/, core_docs/, agent/helpers/,
     reference/, magpie4, PREPROC_AGENT). For each, grep AGENT.md and
     confirm it appears in:
       - MANDATORY WORKFLOW Step 1
       - QUICK MODULE FINDER (where applicable)
       - QUICK RESPONSE CHECKLIST (where applicable)
       - Auto-loading helpers table
  5. Identify omissions = gap findings.

Ground truth: `wc`, `diff`, AGENT.md section grep, helper trigger table.

Specifics:
  - Both anchors are themselves findings.
  - For BLOAT, propose specific trim targets (lines / sections) with
    headroom estimates — the plan already names candidates
    (LINK DON'T DUPLICATE → helper, SESSION CLEANUP → helper, etc.); confirm
    each is still oversize and propose any additional trims.
  - For GAP, propose specific insertion points in AGENT.md (section + line).
  - Helper trigger overlap is OK to report as MEDIUM/LOW; the cost is token
    waste, not correctness.

Do NOT (sibling-lens fences):
  - Do NOT flag stale content (that is L1).
  - Do NOT flag cross-doc count mismatches (that is L4).
  - Do NOT audit broken pointers (that is L6).
  - Do NOT audit script output placement (that is L5).
```

---

## After the 7 agents return — 0c through 0e

**0c (Opus re-run)**: SKIPPED — all 7 lens agents are already Opus per user decision 2026-05-25.
The original 0c existed to upgrade L2/L6 specifically; now redundant.

**0d (Opus synthesis)**: single Opus call. Aggregate 7 lens outputs; dedup; corroborate (≥2 lenses
→ raised confidence); cluster by ROOT CAUSE (not symptom) per `[[feedback_synthetic_interventions]]`.
Expected: 5-8 clusters from likely 30-60 findings.

**0e (per-cluster decisions, with user)**: the plan lists 5 standing decisions waiting on Phase 0
data:
- `project/CURRENT_STATE.json` — retire or revive?
- `reference/dependency_analysis/` — regenerate, mark snapshot, or delete?
- `audit/archive/` + `reference/archive/` — keep for history or delete?
- `module_XX_notes.md` pattern — keep sidecar (prune empties) or fold into main docs?
- Phase 4 scope — deferred to Phase 4 design.

Each decision lands once the cluster data is in front of us. **Do not pre-commit; pause with the
user to decide.**

---

## Cost estimate

- 7 × Opus sub-agents in parallel, ~15-25min wall each = ~25-35min wall total
- 1 × Opus synthesis = ~10min
- Total Phase 0a-0d: ~35-45min wall, 8 Opus calls

Comparable to the standard 6-lens Opus `/pipeline-audit` (R1/R3/R4/R5) — one additional lens,
no Sonnet/Opus split, no 0c re-run needed.

---

## Next step — 0b launching (user-approved 2026-05-25)

User approved design + upgraded lens-agent model to Opus. Launching 7 `Agent` calls in a single
message (`subagent_type: general-purpose`, `model: opus`); collecting outputs to
`audit/pipeline_audit_round6_raw_findings.md`; then proceeding to 0d (Opus synthesis).
