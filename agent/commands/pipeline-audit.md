# /pipeline-audit — Multi-lens structural audit of the agent's machinery

**Use when**: periodically hardening the agent's own machinery — module docs, validator scripts, instruction docs, cross-document consistency. Finds bugs and inefficiencies systematically rather than ad hoc.

**Trigger phrases**: "/pipeline-audit", "audit the pipeline", "pipeline audit", "audit the agent's machinery", "structural audit".

**Cost**: 6 parallel Opus sub-agents, one per lens. Substantial — a deep audit, heavier than `/validate-semantic`. Reserve for periodic hardening rounds.

**Out of scope**: behavioral answer-quality — that is the semantic flywheel (`feedback/validation_rounds.json` + `/validate-semantic`). This audits the *machinery*, not the *answers*.

**Companion docs**: see `feedback/flywheel_rubric.md` for severity scoring; `agent/helpers/verifiers.md` for the 16 anti-confabulation MANDATEs that Lens 4 audits as a target surface.

---

## Why six lenses, not six copies

Decorrelation is engineered, not hoped for. Give N sub-agents the identical prompt and their blind spots correlate — you get N near-identical audits, N-1 of them redundant. So each agent gets a distinct **lens** = a failure mode + a method + a ground-truth anchor.

The **proven hot spot for magpie-agent is doc↔code drift** (445 catalogued bugs across 21 flywheel rounds as of 2026-05-16, mostly doc-vs-GAMS mismatches; see `feedback/validation_rounds.json.cumulative_stats` for current totals). Lenses 1 and 2 double on this with deliberately decorrelated methods (doc-first code-reading vs code-first empirical grep), which fail differently.

Lens 5 is magpie-specific — it replaces preproc-agent's R→GAMS-boundary lens, which has no analog here. Instead it audits the rich cross-document consistency surface (module↔module cross-references, cross_module/*.md vs underlying modules, Module_Dependencies.md aggregate counts vs grep).

---

## The six lenses

| # | Lens | Scope | Hunts | Method | Ground truth |
|---|------|-------|-------|--------|--------------|
| 1 | **Doc↔code fidelity (code-reading)** | `modules/module_*.md`, `module_*_notes.md`, a sampled subset of `cross_module/*.md` | Doc claims contradicting GAMS source: wrong variable names, equation names, realization names, default values, set members, file:line citations | Adversarial code-reading of a random module sample (target 6-8 modules); trace every concrete claim in the doc to `../modules/XX_name/realization/*.gms` | Parent `../modules/*/realization/*.gms` |
| 2 | **Doc↔code fidelity (empirical-grep)** | Same as Lens 1 but DIFFERENT modules to avoid sample correlation | Same failure class | Do NOT read Lens 1's targets — instead grep `../modules/*/declarations.gms` for `vm_*`/`pm_*`/`q*_*`/`s*_*` declarations, then cross-check from the OTHER direction (code→doc): does the declared variable appear in its module's doc? Is the prefix/type described correctly? Does the doc cite the right declaration line? | Same |
| 3 | **Validator soundness** | `scripts/validate_consistency.sh`, `scripts/check_gams_variables.sh`, `scripts/check_gams_equations.sh`, `scripts/check_gams_realizations.sh`, `scripts/check_gams_citations.sh`, `scripts/check_default_realizations.py`, `scripts/check_gams_citations_impl.py` | False positives (validator flags a correct doc) AND false negatives (validator passes a doc with a deliberate bug of class X from `core_docs/Bug_Taxonomy.md`) | Hand-construct fixture docs that inject one bug per Bug_Taxonomy pattern; run each validator; verify each catches its target class. Also: run validators against the actual current doc tree and inspect any flag for false positives | Hand-constructed known-answer cases + the 14 Bug_Taxonomy patterns |
| 4 | **Instruction-surface integrity** | `AGENT.md` (source), deployed copies `../AGENT.md` + `../CLAUDE.md`, `agent/helpers/*` (including the new `verifiers.md`), `agent/commands/*`, `reference/*`, `core_docs/*` | Stale file paths, contradictory or unenforceable rules, source-vs-deployed drift, broken cross-references between AGENT.md and helpers/commands, rule-numbering inconsistencies between AGENT.md and the hoisted verifiers.md | Cross-reference every concrete claim (file path, name, command name, rule number) against the actual tree and against `verifiers.md` | The tree + `verifiers.md` after the 2026-05-23 hoist |
| 5 | **Cross-document consistency** | `modules/module_X.md` ↔ `module_Y.md` (where X cites Y); `cross_module/*.md` ↔ underlying modules; `core_docs/Module_Dependencies.md` counts ↔ actual `grep` | Conflicting claims across docs; dependency counts that don't match real `grep`; conservation-law claims in `cross_module/*.md` not reflected in the underlying module equations; `Module_Dependencies.md` aggregate counts off by N from `grep` | Spot-check N cross-references (sample 4-6 module pairs); recompute 3-4 dependency counts via `grep -l 'vm_<x>' ../modules/*/declarations.gms` and compare to `Module_Dependencies.md` | Cross-referenced docs + `grep` on `../modules/` |
| 6 | **Efficiency / redundancy** | Whole doc surface | Doc-helper overlap, oversized helpers (>5k tokens or excessive duplication of module-doc content), stale archived material, AGENT.md bloat (should be smaller after the 2026-05-23 MANDATE hoist — verify), slow validators, redundant validator checks | Profiling-minded review: doc sizes (`wc -w`), helper trigger overlap, AGENT.md word count vs prior, validator wall-clock (`time bash scripts/validate_consistency.sh`) | Measured sizes + run times |

### Per-lens guidance

- **Lens 1 (doc-reading)** — pick 6-8 modules at random, biased toward modules NOT in the probe-dedup ledger lock-out (so findings aren't trivially explained by "we recently fixed that"). For each module, read its doc end-to-end with the question "what would be wrong here that I would miss if I just glanced?". Then verify every concrete claim against `../modules/XX_name/realization/*.gms`. Hunt: wrong variable prefix (Bug_Taxonomy Pattern 1), invented variable name (Pattern 2), suffix truncation (Pattern 3), stale realization in footer (Pattern 8), wrong equation name (Pattern 9), stale file:line (Pattern 10), wrong filename (Pattern 11), content-level citation mismatch (Pattern 12), wrong default value (Pattern 13).

- **Lens 2 (empirical-grep)** — do NOT read the docs Lens 1 is reading. Instead, walk `../modules/*/declarations.gms` and `../modules/*/equations.gms` directly. Sample 30-50 declared variables and equations across 6-8 OTHER modules. For each, look at the corresponding `modules/module_XX.md`: is the declaration documented? Is the prefix correct? Are the dimensions correct? Does the file:line citation point at the actual line? This is the code→doc direction; Lens 1 is doc→code. The two together catch bugs each individually misses.

- **Lens 3 (validator soundness)** — work in two passes:
   1. **False-positive check**: run `bash scripts/validate_consistency.sh` on the current tree. Inspect every WARN / ERROR. For each, is the flag actually a bug, or is the validator over-firing (e.g., flagging a deprecated-name *italics* reference as a missing variable)?
   2. **False-negative check**: construct fixture docs by deliberately injecting one bug per pattern in `core_docs/Bug_Taxonomy.md` (14 patterns). For each fixture, run the relevant validator. Does it catch the bug? Bonus: which patterns are NOT covered by any validator?

- **Lens 4 (instruction-surface)** — three angles:
   1. **AGENT.md vs deployed copies**: `diff AGENT.md ../AGENT.md && diff AGENT.md ../CLAUDE.md` — any drift?
   2. **AGENT.md vs verifiers.md**: the AGENT.md short-index table in Step 1d should match the 16 MANDATEs in verifiers.md. Numbering, trigger keywords, and rule names must agree.
   3. **Cross-references**: every link in AGENT.md, helpers/*, commands/* to a file path or section should resolve. Stale `module_XX.md` references, broken anchor links, missing reference docs — all findings.

- **Lens 5 (cross-doc consistency)** — pick:
   - 4-6 module pairs where Module X's doc cites Module Y. Read both docs; do they agree on the connecting variable/equation/mechanism?
   - 3-4 dependency claims in `core_docs/Module_Dependencies.md` (e.g., "Module 10 has 23 dependents"). Recompute via `grep -l "vm_land\|vm_lu_transitions" ../modules/*/declarations.gms ../modules/*/equations.gms` — does the count match?
   - 2-3 conservation-law statements in `cross_module/*_balance_conservation.md`. Read the underlying module equations — does the law actually hold as stated?

- **Lens 6 (efficiency)** — profile-minded:
   - Word counts: `wc -w AGENT.md agent/helpers/*.md` — any helper >5k words is a candidate for splitting/trimming.
   - Helper trigger overlap: do two helpers fire on the same keywords with overlapping content?
   - AGENT.md size: post-2026-05-23 MANDATE hoist should reduce by ~150 lines (~3-4k chars). Verify.
   - Validator wall-clock: `time bash scripts/validate_consistency.sh` — anything >30s is a candidate for optimization or parallelization.

---

## Shared agent brief template

Each agent is spawned with the Agent tool, `subagent_type` **general-purpose**, `model` **opus**, all 6 in parallel (single message, 6 tool calls). Fill the `<...>` slots per lens:

```
You are auditing the magpie-agent's own pipeline. Working directory:
/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent
This is a READ-ONLY audit — do NOT edit, write, or commit anything.

Your lens: <lens name>
Scope: <files>
Hunt for: <failure mode>. Assume defects exist — your job is to find them,
adversarially. A clean bill of health is a weak result; dig.
Method: <method>
Ground truth: <anchor — what you check claims against>

<per-lens guidance>

Rules:
- Read-only. Cite file:line for every finding.
- Every finding MUST carry reproducible evidence: a command someone can run, or
  a concrete diff/excerpt — so the finding is verifiable without re-trusting you.
- Propose a fix for each finding; do NOT apply it.
- Distinguish a real defect from a style preference; rate severity honestly.
- If a category is genuinely clean, say so plainly — do not pad.

Return a JSON array of findings, each:
  {lens, location, failure_mode, severity (CRITICAL|HIGH|MEDIUM|LOW),
   evidence, suggested_fix, confidence (HIGH|MEDIUM|LOW)}
followed by a 2-3 line summary.
```

---

## Synthesis (after the 6 agents return)

1. **Aggregate** every agent's findings into one list.
2. **Dedup / corroborate** — the same defect reported by ≥2 agents is *corroborated*: merge into one finding, raise its confidence. Corroboration is signal, not noise.
3. **Triage by severity** — CRITICAL/HIGH first. For each finding, spot-check the evidence (run the command, read the diff) — do not take a finding on trust.
4. **Cluster by root cause** — group findings by shared mechanism, not by symptom. Per `[[feedback_synthetic_interventions]]`, N findings typically collapse to 2-3 root interventions. A finding corroborated by multiple lenses or agents usually points at one root.
5. **Findings report** — a severity-ordered list: location, failure mode, evidence, proposed fix, confidence, corroboration count, root-cause cluster.
6. **Log the round** to `feedback/pipeline_audit_rounds.json` (see schema below).
7. **Present the report.** Phase "fix + mechanize" is **reviewed with the user before execution** — do NOT proactively fix.

## Fix + mechanize (reviewed with the user first)

For each confirmed bug: fix it. For each *recurring class* (≥2 instances across lenses in this round, OR ≥1 recurrence with a prior class from `core_docs/Bug_Taxonomy.md`): add a mechanical guard — extend `scripts/validate_consistency.sh`, add a Bug_Taxonomy.md pattern, or write a new `scripts/check_*.py` — so the class cannot recur silently.

This is the measure→mechanize→bind→re-measure loop from `[[template_verifier_mandate_flywheel]]`: the audit measures, the guard binds, re-running the audit re-measures.

---

## Round log — `feedback/pipeline_audit_rounds.json`

Mirrors `feedback/validation_rounds.json`. One object per round:

```json
{
  "round": 1,
  "date": "YYYY-MM-DD",
  "commit": "abcdef1",
  "auditor_model": "claude-opus-4-7",
  "lenses_run": ["doc-code-fidelity-reading", "doc-code-fidelity-grep",
                 "validator-soundness", "instruction-surface-integrity",
                 "cross-doc-consistency", "efficiency"],
  "findings_total": N,
  "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
  "by_lens": {"lens-name": count, ...},
  "corroborated": [{"finding": "...", "lenses": ["...", "..."], "severity": "..."}],
  "root_cause_clusters": [{"cluster": "...", "findings": ["..."], "candidate_intervention": "..."}],
  "report_path": "feedback/pipeline_audit_roundN.md",
  "guards_added": [],
  "status": "triaged | fixed | mechanized"
}
```

Create the file on round 1 with `{"rounds": [...]}`.

---

## Lessons Learned

<!-- Append insights as the command is used in practice. -->

- **2026-05-23 (origin)**: created as the structural counterpart to `/validate-semantic` (behavioral). Six lens-differentiated Opus agents; doc↔code fidelity is the proven hot spot (445 bugs across 21 flywheel rounds as of origin) so Lens 1 and Lens 2 are decorrelated copies (doc→code reading vs code→doc grep). Lens 5 (cross-doc consistency) replaces preproc-agent's R→GAMS-boundary lens, which has no analog here. Ported from `magpie-preproc-agent/agent/commands/pipeline-audit.md` (2026-05-17 origin there) with lens adaptation for magpie-agent's surface.
- **2026-05-23 (R1)**: 71 findings, 8 root-cause clusters; CRITICAL Module 18 wrong-realization; 13/46 module-doc footer fabrications (single root cause: no realization-validity validator); MANDATE 8 worked example itself contained a fabricated realization (`fbask_jul23` — actual default is `fbask_jan16`). Findings + triage logged at `feedback/pipeline_audit_round1.md`.
