# Pipeline Audit Round 9 — Lens C6: COHERENCE (horizontal: surface vs surface)

**Failure class hunted**: the same value stated differently across surfaces RIGHT NOW (MANDATE count, check count, Check-N numbering, schema version, rubric version) across AGENT.md / verifiers.md / commands / rubric / schema / ledgers.

**Method (decorrelation axis)**: cross-surface agreement. For each cross-stated value, read it on EVERY surface that states it; they must agree. Counts derived by grep, never trusting a hardcoded literal as ground truth.

**Surfaces examined**: `AGENT.md`, `../AGENT.md` + `../CLAUDE.md` (deployed copies), `agent/helpers/verifiers.md`, `audit/flywheel_rubric.md`, `audit/validation_rounds.json` (metadata + cumulative_stats), `agent/commands/{validate-semantic,validate,pipeline-audit}.md`, `scripts/validate_consistency.sh`, `core_docs/Bug_Taxonomy.md`, `modules/module_70.md`, plus `/tmp/magpie_develop_ro/config/default.cfg` + `modules/70_livestock/` as code ground truth.

**Verdict**: 5 findings (1 CRITICAL, 3 MEDIUM, 1 LOW). The precedent drift classes from prior rounds (MANDATE-count 20/17, check-count) are NOW CLEAN — fixed via the "derive by grep / print the live count, don't hardcode" pattern. Two of the three orchestrator seed anchors still hold uncorrected; one (schema version) is extended with a second inaccuracy.

---

## ORCHESTRATOR SEED ANCHOR — verified + extended

### (a) flywheel_rubric.md:30 M70-default anchor INVERTED — STILL HOLDS → finding C6-1

VERIFIED. flywheel_rubric.md:30 (an "immutable" §1 Critical-tier anchor):
> "2026-03-07 (R3): agent described livestock feed as using non-default `fbask_jan16` mechanics when default config has been `fbask_jul23` for years."

Code ground truth:
- `config/default.cfg:2146` → `cfg$gms$livestock <- "fbask_jan16"` (default IS fbask_jan16).
- `ls /tmp/magpie_develop_ro/modules/70_livestock/` → only `fbask_jan16/`, `fbask_jan16_sticky/`. `fbask_jul23` does NOT exist (confirmed two methods: glob + `rg`, with positive control — same probe found `fbask_jan16` fine, `fbask_jul23` nowhere).

The anchor labels the ACTUAL default (`fbask_jan16`) as "non-default" and a never-existent realization (`fbask_jul23`) as "the default for years". INVERTED.

**Cross-surface contradiction (the coherence violation)** — the M70 default is stated on multiple surfaces; rubric:30 is the SOLE outlier:
- verifiers.md:131 — "only `fbask_jan16` and `fbask_jan16_sticky` exist; default is `fbask_jan16`".
- module_70.md:1,4,12-13 — "Default Realization: `fbask_jan16`. Confirmed in config/default.cfg".
- pipeline-audit.md:151 (R1 log) — "MANDATE 8 worked example itself contained a fabricated realization (`fbask_jul23` — actual default is `fbask_jan16`)".
- validation_rounds.json:5584 (R47 phase_gate) — "fbask_jan16 verified DEFAULT (config/default.cfg:2146; ... no fbask_jul23 on develop)".

So FIVE surfaces incl. code agree on `fbask_jan16`; ONE ("immutable" anchor) says `fbask_jul23`. Found in round 901 (`pipeline_round901_lenses/C6-coherence.md`, `pipeline_audit_round901_findings.md`) and NOT fixed since — it persists into round 9. The rubric's own §1 policy ("if reality contradicts an anchor, fix the underlying issue or bump the major version; do not silently re-interpret") is itself being violated.

### (b) schema-version drift AGENT.md:436 vs JSON 1.4 — VERIFIED + EXTENDED → finding C6-2

VERIFIED and SHARPENED. `validation_rounds.json` metadata.schema_version = **"1.4"** (history confirms 1.3→1.4 added 2026-05-30). AGENT.md:436 (and both deployed copies) says present-tense "schema v1.3". Two errors, not one:
- (i) Current schema is 1.4, not v1.3 — stale pointer.
- (ii) G3+G4 were added in schema **v1.2** (2026-05-24 history entry), NOT v1.3. v1.3 (2026-05-29) added `doc_errors_latent`, unrelated to G3/G4. So the line attaches G3/G4 to a version that is neither current nor the one that introduced them.

(The seed also named validate-semantic.md:184 — that is a DATED changelog entry "Schema v1.3 changes (2026-05-29)", correct as history; it does not make a present-tense current-version claim, and line 175 defers to the JSON for the live value. So validate-semantic.md is NOT live drift; AGENT.md:436 is the single live schema-version drift.)

### (c) flywheel_rubric.md "14 classes from §3" vs 15-row table — STILL HOLDS → finding C6-3

VERIFIED. §3 bug-class table (lines 113-128) has **15 numbered rows** (class 15 "Latent doc error" added v1.2, line 130). Two references say "14 classes from §3":
- :233 "[one of the 14 classes from §3]" (audit report format).
- :262 "Finite bug-class list (§3) — 14 classes".

Both point at "§3" (the rubric's own table = 15). The v1.2 changelog (line 272) explicitly says "Added bug class 15" — so the author knew, but missed updating these two "§3 = 14" references.
(Note: line 110 "The 14 patterns in core_docs/Bug_Taxonomy.md" is CORRECT — Bug_Taxonomy.md has exactly 14 patterns, confirmed by grep; class 15 is explicitly flywheel-specific "no Bug_Taxonomy entry". So :110 is not a defect; :233 and :262 are, because they reference §3 not Bug_Taxonomy.)

---

## FINDINGS

### C6-1 — CRITICAL — coherence — flywheel_rubric.md:30
**Inverted "immutable" M70-default anchor; contradicts 5 surfaces incl. code.**
- failure_mode: The Critical-tier calibration anchor (immutable per §1/§8) tells the Opus auditor that M70's default "has been `fbask_jul23` for years" with `fbask_jan16` non-default. INVERTED: `fbask_jan16` is the default and `fbask_jul23` never existed. A broken guard — the very wrong-default-realization failure class the anchor exists to teach against is itself encoded backwards, mis-calibrating every future round's scoring of M70 questions.
- evidence: `sed -n '30p' audit/flywheel_rubric.md` = "...default config has been `fbask_jul23` for years..."; `grep -n 'cfg$gms$livestock <-' /tmp/magpie_develop_ro/config/default.cfg` → `2146:cfg$gms$livestock <- "fbask_jan16"`; `ls /tmp/magpie_develop_ro/modules/70_livestock/` → `fbask_jan16/ fbask_jan16_sticky/` (no jul23); contradicted by verifiers.md:131, module_70.md:12-13, pipeline-audit.md:151, validation_rounds.json:5584.
- verify_cmd: `sed -n '30p' <magpie-agent>/audit/flywheel_rubric.md; grep -n 'cfg$gms$livestock <-' /tmp/magpie_develop_ro/config/default.cfg; ls /tmp/magpie_develop_ro/modules/70_livestock/`
- suggested_fix (DO NOT APPLY): Per §1's own fix-or-major-bump policy, correct the anchor to current develop while preserving the cascading-wrong-realization LESSON, e.g. "...described livestock feed using a NON-default realization's mechanics when the default is `fbask_jan16` (config/default.cfg:2146; only `fbask_jan16` + `fbask_jan16_sticky` exist)." Note in §9 changelog that the anchor's realization names were corrected (lesson unchanged); because §1 calls anchors immutable, this warrants a documented exception (the anchor was authored on a false premise — `fbask_jul23` never existed per pipeline-audit.md:151) or a major bump v1.2→v2.0. Corrected facts already on record in validation_rounds.json R47.
- confidence: HIGH

### C6-2 — MEDIUM — drift — AGENT.md:436 (propagated to ../AGENT.md:436 + ../CLAUDE.md:436)
**Present-tense "schema v1.3" is doubly stale: current schema is 1.4, and G3/G4 were added in v1.2.**
- failure_mode: A cross-stated value (schema version) drifted. AGENT.md:436 asserts "G3 + G4 in validation_rounds.json schema v1.3 specifically guard this." Current schema_version is 1.4; G3/G4 entered at schema v1.2. The functional pointer (G3/G4 guard magpie4 reporting) is correct, so no behavioral guidance breaks — but the version metadata is wrong on two counts, and the line is in the always-loaded deployed agent context (Claude Code reads ../CLAUDE.md).
- evidence: `grep -n 'schema v1.3 specifically guard' AGENT.md` (line 436); `python3 -c "import json;print(json.load(open('audit/validation_rounds.json'))['metadata']['schema_version'])"` → `1.4`; JSON schema_version_history shows G3/G4 added at version "1.2" (2026-05-24), v1.3 (2026-05-29) added doc_errors_latent. Same line present at ../AGENT.md:436 and ../CLAUDE.md:436.
- verify_cmd: `grep -n 'schema v1.3 specifically guard' <magpie-agent>/AGENT.md; python3 -c "import json;print(json.load(open('<magpie-agent>/audit/validation_rounds.json'))['metadata']['schema_version'])"`
- suggested_fix (DO NOT APPLY): Drop the version literal (it drifts) and say "...the G3 + G4 regression questions in validation_rounds.json specifically guard this." — matching the de-drift pattern already used for the check count ("the run's summary prints the live check count"). If a version must be named, use the schema version that introduced them (v1.2). Re-deploy to ../AGENT.md + ../CLAUDE.md in the same commit.
- confidence: HIGH

### C6-3 — MEDIUM — coherence — flywheel_rubric.md:233, :262
**"14 classes from §3" but §3 table has 15 rows (class 15 added v1.2).**
- failure_mode: Self-contradiction within one surface on a cross-stated count. The audit-report-format template (:233) and stability-mechanisms section (:262) both reference "14 classes from §3", but §3's table (lines 113-128) lists 15. An auditor following :233 would pick "one of the 14 classes" from a 15-row table, and class 15 (Latent doc error) — the v1.2 flagship addition — sits outside the stated range.
- evidence: `sed -n '112,131p' audit/flywheel_rubric.md | grep -c '^| [0-9]'` → 15; `grep -n '14 class' audit/flywheel_rubric.md` → lines 110, 233, 262. Line 272 changelog confirms "Added bug class 15". (Line 110 "14 patterns in Bug_Taxonomy.md" is correct — Bug_Taxonomy.md has 14 patterns, verified by grep; class 15 is explicitly flywheel-only.)
- verify_cmd: `sed -n '112,131p' <magpie-agent>/audit/flywheel_rubric.md | grep -c '^| [0-9]'; grep -n '14 class' <magpie-agent>/audit/flywheel_rubric.md`
- suggested_fix (DO NOT APPLY): Change :233 to "[one of the bug classes in §3]" and :262 to "Finite bug-class list (§3) — 15 classes; new classes added only at minor versions". Better still, phrase both to avoid a hardcoded count ("one of the classes enumerated in §3").
- confidence: HIGH

### C6-4 — MEDIUM — drift — verifiers.md:13
**"Lessons count: 0 entries" but the file has 3 dated Lessons Learned entries; suppresses the README-documented N>=2 promotion-scan trigger.**
- failure_mode: Header metadata disagrees with the same file's body. The `Lessons count: N entries` header is functional, not cosmetic: README.md:84 instructs "The agent should check lesson count... When N >= 2, scan for promotion candidates before answering." With verifiers.md stuck at "0 entries" while actual = 3 (>=2), the promotion-scan trigger never fires for verifiers.md. Other helpers maintain this correctly (debugging_infeasibility.md = "2 entries"/2 actual; adding_new_crop.md = "1 entries"/1) — verifiers.md is the outlier (header carried the hoist-time template value while 3 entries were appended later).
- evidence: `grep -n 'Lessons count' agent/helpers/verifiers.md` → `13:**Lessons count**: 0 entries`; `awk '/^## Lessons Learned/{f=1;next}/^---/{if(f)f=0}f&&/^- \*\*2026/' agent/helpers/verifiers.md | wc -l` → 3 (entries dated 2026-05-23, 2026-05-25, 2026-05-30). README.md:84 documents the N>=2 trigger.
- verify_cmd: `grep -n 'Lessons count' <magpie-agent>/agent/helpers/verifiers.md; awk '/^## Lessons Learned/{f=1;next}/^---/{if(f)f=0}f&&/^- \*\*2026/' <magpie-agent>/agent/helpers/verifiers.md | wc -l`
- suggested_fix (DO NOT APPLY): Update verifiers.md:13 to "**Lessons count**: 3 entries". Consider a validate_consistency.sh check that asserts each helper's header count equals its dated-entry count (mechanizes this whole class).
- confidence: HIGH

### C6-5 — LOW — drift — flywheel_rubric.md:120
**Class 7 "Broken cross-reference" mapped to "Check 8", but the broken-cross-reference check is Check 3 (Check 8 is the Markdown Link Validator).**
- failure_mode: Hardcoded Check-NUMBER mapping is imprecise and fragile to renumbering. Rubric §3 maps class 7 (Broken cross-reference) → "validate_consistency.sh Check 8". In the validator, Check 3 is titled "Cross-References" and literally emits "Broken reference: module_XX.md referenced but doesn't exist" (scripts/validate_consistency.sh:242,261); Check 8 is "Markdown Link Validator" for `[text](path)` links in helpers (:494-513) — a related but distinct check. A maintainer chasing a broken-cross-reference failure via the rubric is pointed at the wrong check. (Class 6→Check 1 and class 14→Check 10 mappings on the same surface are CORRECT.) Low because both checks detect broken-link-type issues and the validator has 28 checks, so a maintainer would likely still find it.
- evidence: `grep -n 'Check 8' audit/flywheel_rubric.md` → line 120; `sed -n '242,261p' scripts/validate_consistency.sh` (Check 3 = "Cross-References", emits "Broken reference"); `sed -n '494,496p' scripts/validate_consistency.sh` (Check 8 = "Markdown Link Validator").
- verify_cmd: `grep -n 'Check [0-9]' <magpie-agent>/audit/flywheel_rubric.md; grep -n '^# Check 3:\|^# Check 8:' <magpie-agent>/scripts/validate_consistency.sh`
- suggested_fix (DO NOT APPLY): Change :120 to "Check 3" (the cross-reference check), or de-couple from the number ("validate_consistency.sh cross-reference check"). The validator names checks by title in its output, so a title reference is renumbering-proof.
- confidence: MEDIUM

---

## CLEAN CATEGORIES (checked, genuinely coherent — not padded)

- **MANDATE count = 20, agrees everywhere.** `grep -c '^## MANDATE ' verifiers.md` → 20; verifiers.md:1,3 say "20"; AGENT.md:216,220,288 say "20". The precedent drift (pipeline-audit.md once said 17) is FIXED: pipeline-audit.md:50 now says "count derivable by grep, do not hardcode it on a third surface" and references the `## MANDATE N` headers without a literal. CLEAN.
- **Validator check count = 28, no disagreeing literal.** `validate_consistency.sh` defines Check 1..28 (each prints "N/28"). No doc hardcodes "N checks": AGENT.md:426,450 say "the run's summary prints the live check count"; validate.md:27 defers to the live `VALIDATOR_RESULT` line. CLEAN (precedent check-count drift fixed by the live-count pattern).
- **rubric_version: JSON metadata = 1.2, rubric header (line 1 + line 5) = v1.2.** AGREE. CLEAN.
- **total_rounds: cumulative_stats.total_rounds = 48, rounds[] array length = 48, round numbers contiguous 1..48.** AGREE. CLEAN.
- **regression_questions = G1,G2,G3,G4 across 4 surfaces.** JSON regression_questions[] = [G1,G2,G3,G4]; AGENT.md:81, validate-semantic.md:81, flywheel_rubric.md §6 all list G1/G2/G3/G4. AGREE. CLEAN.
- **pipeline-audit lens count = 6, agrees.** pipeline-audit.md:7 "typically 6 parallel Opus sub-agents", :17 "Why six lenses", :27 "The six lenses", lens table = 6 rows; AGENT.md:112 "typically 6 parallel Opus agents; per-round lens design may vary". The "typically/may vary" hedge correctly covers per-round overrides (this round uses a different set). CLEAN.
- **rubric §9 v1.2 changelog "companion ... schema 1.3" is correct history.** rubric v1.2 dated 2026-05-29; JSON schema 1.3 dated 2026-05-29 — the companion-edit claim accurately records the paired bump. validate-semantic.md:182 (schema v1.1) and :184 (schema v1.3) are likewise correct DATED changelog entries, not present-tense current-version claims (line 175 defers to the JSON for the live value). CLEAN.
- **Deployed-copy coherence (sampled).** ../AGENT.md and ../CLAUDE.md carry the identical MANDATE-count (20) and the identical :436 line as source AGENT.md — i.e. they are in sync with source (the :436 drift is a source-level content bug propagated faithfully, NOT a deploy-sync drift). The deploy mechanism is coherent; the content it deployed is wrong (see C6-2).

---

## METHOD NOTES / CAVEATS
- All absence claims (fbask_jul23) cross-checked by two methods (glob + rg) with a positive control (same probe found fbask_jan16). grep probes isolated per CRITICAL grep rules; no chained probes.
- C6-1 is a content/coherence defect, not a removal/merge — what_it_protects / who_else_needs_it / blast_radius = n/a (no artifact is being removed; the anchor's text is being corrected in place).
- Severity calibration: C6-1 is CRITICAL because it is a broken guard on the Critical-tier's own immutable anchor (mis-calibrates the scoring rubric and violates the rubric's self-policy). C6-2/3/4 are MEDIUM (real cross-stated-value drift, contained, no behavioral guidance broken). C6-5 is LOW (imprecise but recoverable pointer). None are style preferences.
- In-scope-but-found-clean is the bulk of this lens — the agent has clearly internalized the "derive-by-grep / print-the-live-count, don't hardcode" anti-drift pattern for the two precedent classes (MANDATE count, check count). The residual drift is concentrated in (i) the "immutable" rubric anchor that the immutability framing protected from correction, and (ii) hardcoded version/count literals in the rubric and AGENT.md that the live-count pattern has not yet reached.
