export const meta = {
  name: 'magpie-pipeline-audit-round',
  description: 'One structural/consolidation audit round for magpie-agent machinery: N decorrelated lens agents fan out (find), each finding is adversarially verified (defects reproduced, removals refuted via live-dependent search), then one synthesis agent clusters survivors by root cause. READ-ONLY: finds + verifies + reports; does NOT fix or mutate the rounds log (fixes are user-reviewed per pipeline-audit.md).',
  phases: [
    { title: 'Lenses' },
    { title: 'Verify' },
    { title: 'Synthesize' },
  ],
}

// ---- args (passed at invocation) ----
// args.round    : int
// args.preset   : 'consolidation' (default) | 'standard'    -- baked-in faithful lens sets
// args.lenses   : [{key,title,failure_class,method,ground_truth,scope?,guidance?,standing_bias?}]
//                 -- explicit override; takes precedence over preset
// args.verify   : bool (default true) -- run the per-finding adversarial verify stage
// args.seeds    : { <lensKey>: "orchestrator-spotted seed anchor to VERIFY + EXTEND" }  (optional, R8 pattern)
// args.verifySeverities : [..] (default ['CRITICAL','HIGH','MEDIUM']) -- which severities get a dedicated verifier
// args arrives as a JSON-encoded STRING from some harness paths -> parse defensively
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const R = A.round
const PRESET = A.preset || 'consolidation'
const VERIFY = A.verify !== false
const SEEDS = A.seeds || {}
const VSEV = A.verifySeverities || ['CRITICAL', 'HIGH', 'MEDIUM']
const VERIFY_CAP = 60   // hard ceiling on dedicated verifiers; overflow logged, not silently dropped

const AGENT_DIR = '/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent'
const DEV = '/tmp/magpie_develop_ro'        // detached origin/develop worktree (code ground truth)
const PARENT = '/Users/turnip/Documents/Work/Workspace/magpie'
const ARC = AGENT_DIR + '/audit/archive/rounds'
const RUBRIC = AGENT_DIR + '/audit/flywheel_rubric.md'
const VERIFIERS = AGENT_DIR + '/agent/helpers/verifiers.md'
const BUGTAX = AGENT_DIR + '/core_docs/Bug_Taxonomy.md'

// the 46 real MAgPIE module numbers (sparse numbering; verified against ../modules/ @ee98739fd)
const MODULES = ['09','10','11','12','13','14','15','16','17','18','20','21','22','28','29','30','31','32','34','35','36','37','38','39','40','41','42','43','44','45','50','51','52','53','54','55','56','57','58','59','60','62','70','71','73','80']

// ---------- shared guard text (load-bearing; mirrors doc_audit_round.workflow.js) ----------
const GREP_GUARD = `CRITICAL grep rules (a verified false-positive source in this repo):
  - A bare 'grep -r' can SILENTLY return empty even when matches exist. Never trust it alone.
  - 'find ... -exec grep {} +' returns EXIT 1 when the final batch has no match, which ABORTS any chained (&&, ';', compound) command and silently TRUNCATES output. Run each grep probe as its OWN standalone command (or append '|| true'); never chain probes so one nonzero exit kills the rest.
  - rg (ripgrep) IS available here; prefer it: rg -n 'PATTERN' ${DEV}/modules/   (rg also exits 1 on no-match -> isolate it).
  - ALWAYS cross-check a zero/absence result with a SECOND method, AND run a POSITIVE CONTROL: grep a known-present sibling token to prove the search works in that dir before concluding 'X is absent'.
  - Co-located names: a module number cited for an ADJACENT parameter on the same doc line is NOT a consumer of THIS parameter.
  - SOLUTION-LEVEL reads: a module can consume a variable via its attributes (NAME.l/.lo/.up/.fx/.m) in presolve/postsolve, which a 'NAME(' grep MISSES. Always grep BOTH 'NAME(' AND 'NAME.' before concluding a module does/does not consume NAME.
A "X is dead / never invoked / has no live dependent" claim is the highest-risk false positive in a CONSOLIDATION audit: confirm twice + positive control before recommending any deletion/merge.`

const MANDATES = `Apply the verifiers.md MANDATEs (read ${VERIFIERS} if unsure), especially: 13 interface-consumer grep; 17 direct vs transitive consumer; 16 citations as full path file.gms:LINE verified in CURRENT develop; 8 realization-name verification (ls ${DEV}/modules/NN_*/); 3 default-parameter verification (grep the default in code + ${DEV}/config/default.cfg). Distinguish DECLARED vs POPULATED vs READ for interface variables.`

// ---------- lens presets ----------
const PRESETS = {
  // CONSOLIDATION (C1-C6) -- faithful to pipeline_audit_round7_design.md. Standing bias: DELETE/MERGE/SIMPLIFY.
  consolidation: [
    { key: 'C1-dead', title: 'DEAD / no-op machinery', standing_bias: true,
      failure_class: 'artifacts (scripts, MANDATEs, ledgers, markers, helpers) that are never invoked or never catch anything',
      method: 'static liveness trace: for each artifact, follow its invocation path and PROVE it is LIVE (something calls/reads it) or DEAD (nothing does). A grep for the artifact name across the tree + the gate scripts is the start, not the end.',
      ground_truth: 'precedent: probe_dedup_check.py was a multi-round no-op; pr_*.py trio was ~1192 LOC with 0 lifetime catches' },
    { key: 'C2-redundant', title: 'REDUNDANT / overlapping (-> merge)', standing_bias: true,
      failure_class: 'two+ artifacts covering the same property (duplicate validators, overlapping helpers, dual .sh/.py checkers)',
      method: 'static cross-comparison: build a {validator/MANDATE/command -> property checked} matrix; find cells covered more than once; propose the merge.',
      ground_truth: 'precedent: 3 realization validators overlapped; dual GAMS .sh/.py checkers' },
    { key: 'C3-drift', title: 'DRIFT (vertical: derived value vs its source)',
      failure_class: 'a generated/derived value (a count, SECTION_TOTAL, cumulative_stats field, version pin, freshness anchor, "Check N" reference) that has drifted from its source with NO check enforcing agreement',
      method: 'enumerate every derived/generated value across the machinery; for each, name the enforcing check OR prove its ABSENCE (then the value is free to drift). Recompute the value from source and compare to what is stated.',
      ground_truth: 'precedent: aggregate-count markers drifted ~3 rounds unchecked; cumulative_stats vs rounds[]; SECTION_TOTAL vs printed checks; version_pins vs renv.lock' },
    { key: 'C4-untested-testers', title: 'UNTESTED testers (positive-control census)',
      failure_class: 'a check_*.py/.sh that has no positive control proving it still catches its target bug class -- especially freshly-changed or brand-new testers',
      method: 'census every scripts/check_*.{py,sh} and validate_consistency.sh check; for each, does a self-test / positive control exist (selftest_validator.sh or a --self-test) that injects the target bug and asserts it is caught? Flag every load-bearing or recently-modified check with no control.',
      ground_truth: 'precedent: a self-test caught a regex bug; the d6e7376 set -e bug silently killed validate_consistency.sh at check 1' },
    { key: 'C5-overcomplexity', title: 'OVER-COMPLEXITY (cost > catch rate)',
      failure_class: 'machinery whose cost (wall-time, advisory-noise, maintenance) exceeds its lifetime real catches',
      method: 'EMPIRICAL: run the gate (time bash scripts/validate_consistency.sh); count advisory-noise lines; for each check cross-reference its lifetime REAL catches (search the rounds logs). Flag checks/scripts where cost clearly exceeds catch.',
      ground_truth: 'precedent: ~874 advisory noise lines; checks with vacuous-pass histories' },
    { key: 'C6-coherence', title: 'COHERENCE (horizontal: surface vs surface)',
      failure_class: 'the same value stated differently across surfaces RIGHT NOW (MANDATE count, check count, Check-N numbering, schema version, rubric version) across AGENT.md / verifiers.md / commands / rubric / schema / ledgers',
      method: 'cross-surface agreement: pick each cross-stated value and read it on EVERY surface that states it; they must agree. Derive counts by grep, never trust a hardcoded literal as ground truth.',
      ground_truth: 'precedent: MANDATE count drift (AGENT.md 20 / pipeline-audit.md 17 / verifiers.md 16+20); schema v1.1-vs-v1.2 drift' },
  ],
  // STANDARD (doc<->code fidelity 6-lens) -- faithful to agent/commands/pipeline-audit.md.
  standard: [
    { key: 'L1-doccode-read', title: 'Doc<->code fidelity (code-reading)', samples_modules: true,
      failure_class: 'doc claims contradicting GAMS source: wrong variable/equation/realization names, wrong default values, wrong set members, stale file:line citations',
      method: 'adversarial doc->code reading. For each assigned module, read modules/module_XX.md end-to-end asking "what would be wrong here that I would miss at a glance?", then trace every concrete claim to ' + DEV + '/modules/XX_name/realization/*.gms.',
      ground_truth: DEV + '/modules/*/realization/*.gms',
      guidance: 'Hunt Bug_Taxonomy patterns 1 (wrong prefix), 2 (invented name), 3 (suffix truncation), 8 (stale realization footer), 9 (wrong equation name), 10 (stale file:line), 11 (wrong filename), 12 (content-level citation mismatch), 13 (wrong default value). Read ' + BUGTAX + ' for the pattern definitions.' },
    { key: 'L2-doccode-grep', title: 'Doc<->code fidelity (empirical-grep)', samples_modules: true,
      failure_class: 'same class as L1, found from the code->doc direction',
      method: 'do NOT read L1\'s modules. Walk ' + DEV + '/modules/*/declarations.gms and equations.gms for your assigned modules; sample 30-50 declared vars/eqs; for each, check modules/module_XX.md documents it with the correct prefix, dimensions, and a citation line that actually points at the declaration.',
      ground_truth: DEV + '/modules/*/declarations.gms + equations.gms' },
    { key: 'L3-validator-soundness', title: 'Validator soundness (FP + FN)',
      failure_class: 'false positives (validator flags a correct doc) AND false negatives (validator passes a doc with a known bug class)',
      method: '(1) FP: run bash scripts/validate_consistency.sh; inspect every WARN/ERROR -- real bug or over-fire? (2) FN: construct fixture docs injecting one bug per Bug_Taxonomy pattern; run the relevant validator; does it catch its class? Note any pattern covered by NO validator.',
      ground_truth: 'hand-constructed known-answer fixtures + the Bug_Taxonomy patterns in ' + BUGTAX },
    { key: 'L4-instruction-surface', title: 'Instruction-surface integrity',
      failure_class: 'stale paths, contradictory/unenforceable rules, source-vs-deployed drift, broken cross-references, rule-numbering inconsistencies',
      method: 'diff AGENT.md ../AGENT.md and diff AGENT.md ../CLAUDE.md (any drift is a Check-10 failure). Reconcile the AGENT.md MANDATE index against the ## MANDATE headers in ' + VERIFIERS + ' (derive the count by grep; do not trust a hardcoded literal). Resolve every file-path/section/command cross-reference in AGENT.md + agent/helpers/* + agent/commands/* to a real target.',
      ground_truth: 'the magpie-agent tree + verifiers.md' },
    { key: 'L5-cross-doc', title: 'Cross-document consistency',
      failure_class: 'conflicting claims across docs; dependency counts off vs grep; conservation-law claims not reflected in the underlying equations',
      method: 'spot-check 4-6 module pairs where X cites Y (do both docs agree on the connecting variable/mechanism?); recompute 3-4 Module_Dependencies.md counts via rg -l on ' + DEV + '/modules/*/declarations.gms + equations.gms; check 2-3 conservation-law statements in cross_module/*_balance_conservation.md against the real equations.',
      ground_truth: 'cross-referenced docs + rg on ' + DEV + '/modules/' },
    { key: 'L6-efficiency', title: 'Efficiency / redundancy',
      failure_class: 'doc-helper overlap, oversized helpers, stale archives, AGENT.md bloat, slow or redundant validators',
      method: 'wc -w AGENT.md agent/helpers/*.md (flag any helper >5k words); helper trigger-keyword overlap; AGENT.md size vs the 40KB CLAUDE.md threshold; time bash scripts/validate_consistency.sh (flag >30s); redundant checks.',
      ground_truth: 'measured sizes + run times' },
  ],
}

let LENSES = (A.lenses && A.lenses.length) ? A.lenses : PRESETS[PRESET]
if (!LENSES) throw new Error('unknown preset: ' + PRESET)
// args.lensKeys: optional subset of a preset by key (e.g. ['C3-drift','C4-untested-testers','C6-coherence'] = the R8 targeted triad)
if (A.lensKeys && A.lensKeys.length) LENSES = LENSES.filter(l => A.lensKeys.includes(l.key))

// deterministic per-round module sampling for the doc<->code lenses (no Math.random in workflows)
function moduleSlice(lensIndex, n) {
  const off = ((R || 0) * 16 + lensIndex * n) % MODULES.length
  const out = []
  for (let i = 0; i < n; i++) out.push(MODULES[(off + i) % MODULES.length])
  return out
}

// ---------- schemas ----------
const SEV = { type: 'string', enum: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] }
const KIND = { type: 'string', enum: ['defect', 'drift', 'coherence', 'removal', 'merge', 'inefficiency', 'untested'] }
const CONF = { type: 'string', enum: ['HIGH', 'MEDIUM', 'LOW'] }

const LENS_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['lens', 'surfaces_examined', 'findings', 'clean_categories', 'summary', 'report_file'],
  properties: {
    lens: { type: 'string' },
    surfaces_examined: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'severity', 'kind', 'location', 'failure_mode', 'evidence', 'verify_cmd', 'suggested_fix', 'confidence'],
        properties: {
          id: { type: 'string', description: 'lens-local id, e.g. C3-1' },
          severity: SEV, kind: KIND, confidence: CONF,
          location: { type: 'string', description: 'file:line or named surface' },
          failure_mode: { type: 'string' },
          evidence: { type: 'string', description: 'a command someone can run (with its result) OR a concrete excerpt/diff -- verifiable without re-trusting you' },
          verify_cmd: { type: 'string', description: 'the single exact command that reproduces this finding' },
          suggested_fix: { type: 'string', description: 'proposed fix; do NOT apply it' },
          // blast-radius fields -- REQUIRED-in-spirit for removal/merge findings (state "n/a" otherwise)
          what_it_protects: { type: 'string', description: 'for removal/merge: what this artifact guards; else n/a' },
          who_else_needs_it: { type: 'string', description: 'for removal/merge: live dependents you found; else n/a' },
          blast_radius: { type: 'string', description: 'for removal/merge: what breaks if removed; else n/a' }
        }
      }
    },
    clean_categories: { type: 'array', items: { type: 'string' }, description: 'categories you checked and found genuinely clean (do NOT pad findings; report clean plainly)' },
    summary: { type: 'string', description: '<=300 chars; full detail in report_file' },
    report_file: { type: 'string' }
  }
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['finding_id', 'kind', 'citation_ok', 'reproduced', 'verdict', 'corrected', 'evidence'],
  properties: {
    finding_id: { type: 'string' },
    kind: { type: 'string' },
    citation_ok: { type: 'boolean', description: 'MECHANICAL: the cited file:line exists, line is in range, and contains the claimed token/content' },
    reproduced: { type: 'boolean', description: 'the claimed defect/drift/redundancy actually reproduces when you run verify_cmd' },
    live_dependent_found: { type: 'boolean', description: 'for removal/merge ONLY: a live dependent exists (so the removal is unsafe). false for non-removal kinds.' },
    verdict: { type: 'string', enum: ['UPHELD', 'REFUTED', 'CORRECTED', 'CITATION_FAILED', 'NOT_REVIEWABLE'], description: 'UPHELD=reproduces & safe; REFUTED=did not reproduce OR (removal) a live dependent exists; CORRECTED=real but the fix/scope is wrong; CITATION_FAILED=cited location does not resolve; NOT_REVIEWABLE=needs human judgement' },
    corrected: { type: 'string', description: 'if CORRECTED: the precise corrected finding/scope; else ""' },
    evidence: { type: 'string', description: 'exact commands + results: the citation check AND the reproduction (or, for removal, the live-dependent search with positive control)' }
  }
}

const SYNTH_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['clusters', 'recommendation', 'report_file'],
  properties: {
    clusters: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['root_cause', 'finding_ids', 'candidate_intervention', 'severity'],
        properties: {
          root_cause: { type: 'string' },
          finding_ids: { type: 'array', items: { type: 'string' } },
          candidate_intervention: { type: 'string' },
          severity: SEV,
          adds_surface: { type: 'boolean', description: 'true if the intervention ADDS machinery (must be justified vs consolidation)' }
        }
      }
    },
    recommendation: { type: 'string', description: 'ordered next actions, highest-leverage first; <=600 chars' },
    report_file: { type: 'string' }
  }
}

// ---------- prompt builders ----------
function lensPrompt(lens, idx) {
  const slice = lens.samples_modules ? moduleSlice(idx, 8) : null
  const seed = SEEDS[lens.key]
  return `You are auditing the magpie-agent's OWN machinery (a structural/consolidation audit, NOT answer quality). Working dir: ${AGENT_DIR}. Model: highest capability.
This is a READ-ONLY audit: do NOT edit, write (except your one report file), or commit anything. Run validators/greps freely -- they are read-only.

YOUR LENS: ${lens.title}  [key: ${lens.key}]
FAILURE CLASS you hunt: ${lens.failure_class}
METHOD (your decorrelation axis -- stay in it; other lenses cover other axes): ${lens.method}
GROUND TRUTH: ${lens.ground_truth}
${lens.scope ? 'SCOPE: ' + lens.scope : ''}
${lens.guidance ? 'GUIDANCE: ' + lens.guidance : ''}
${slice ? 'ASSIGNED MODULES (examine ONLY these, so you do not overlap the sibling doc<->code lens): ' + slice.join(', ') : ''}
${seed ? 'ORCHESTRATOR SEED ANCHOR (VERIFY this specific claim against source, then EXTEND -- find siblings of the same class): ' + seed : ''}
${lens.standing_bias ? 'STANDING BIAS (consolidation): the default remediation is DELETE / MERGE / SIMPLIFY. Any finding whose fix ADDS machinery must justify why consolidation cannot achieve the same. For EVERY removal/merge finding you MUST fill what_it_protects + who_else_needs_it + blast_radius (do the live-dependent search BEFORE recommending removal -- a missed live dependent is the worst error here).' : 'For any removal/merge-kind finding, fill what_it_protects + who_else_needs_it + blast_radius; for other kinds set them to "n/a".'}

${MANDATES}

${GREP_GUARD}

DISCIPLINE:
- Assume defects exist; a clean bill of health is a WEAK result. Dig. But do NOT pad: a category you checked and found genuinely clean goes in clean_categories, not invented findings.
- Every finding MUST carry reproducible evidence (the exact verify_cmd + its result, or a concrete excerpt). A finding nobody can reproduce is not a finding.
- Cite file:line for every finding. Rate severity honestly (CRITICAL=actively wrong/unsafe guidance or a broken guard; HIGH=load-bearing drift/dead guard; MEDIUM=real but contained; LOW=nit). Distinguish a real defect from a style preference.
- Set kind precisely (defect/drift/coherence/removal/merge/inefficiency/untested) -- the verifier branches on it.

OUTPUT:
- Write your FULL lens report (every check, evidence, verdicts) to ${ARC}/pipeline_round${R}_lenses/${lens.key}.md
- Return the schema object. summary <=300 chars (full detail in the report file). report_file = the path you wrote.`
}

function verifyPrompt(f) {
  const isRemoval = (f.kind === 'removal' || f.kind === 'merge')
  return `You are an ADVERSARIAL VERIFIER (model: highest capability) for one magpie-agent pipeline-audit finding. Default to SKEPTICISM. Auditor agents confabulate (they pattern-complete dead-code claims, over-count redundancy, and mis-cite); LLM confabulations are CORRELATED across agents, so your ONLY reliable tool is MECHANICAL reproduction -- run the commands, do not trust recall. Working dir: ${AGENT_DIR}; code ground truth: ${DEV}.

FINDING TO VERIFY:
${JSON.stringify({ id: f.id, lens: f.lens, severity: f.severity, kind: f.kind, location: f.location, failure_mode: f.failure_mode, evidence: f.evidence, verify_cmd: f.verify_cmd, suggested_fix: f.suggested_fix, what_it_protects: f.what_it_protects, who_else_needs_it: f.who_else_needs_it, blast_radius: f.blast_radius }, null, 1)}

${GREP_GUARD}

STEP A -- MECHANICAL CITATION CHECK (all kinds): for the finding's location and any file:line in evidence/suggested_fix, run test -f, wc -l (line in range?), and read the exact line(s). If the file is missing, the line is out of range, or it does not contain the claimed content -> citation_ok=false, verdict=CITATION_FAILED. Record exact commands + results.

STEP B -- REPRODUCE (only if citation_ok):
${isRemoval
  ? `  This is a REMOVAL/MERGE finding. Your job is to REFUTE the removal by finding ANY live dependent. Independently search the WHOLE tree (magpie-agent + ../AGENT.md/../CLAUDE.md deployed copies + gate scripts + commands + helpers) for references to the artifact: grep its name/path, check whether validate_consistency.sh or any check_*/selftest invokes it, whether any doc links it, whether any session-startup/command path reads it. Run a POSITIVE CONTROL (grep a known-live sibling artifact to prove your search works). If you find a live dependent -> live_dependent_found=true, verdict=REFUTED (the artifact is still needed; removal is unsafe). Only if you can prove NO live dependent across the whole tree -> live_dependent_found=false, verdict=UPHELD. If the merge is partially right (some overlap, but not full duplication) -> CORRECTED with the precise safe scope.`
  : `  This is a ${f.kind} finding. REPRODUCE it mechanically: run the finding's verify_cmd yourself and an independent second method. For a drift/coherence finding, re-derive the value from source on EVERY surface and confirm they actually disagree. For a defect, confirm the doc/code mismatch reproduces. For an inefficiency, re-run the measurement. If it reproduces -> verdict=UPHELD. If it does not reproduce (or you measure otherwise) -> verdict=REFUTED. If real but the stated scope/fix is wrong -> CORRECTED with the precise corrected finding. If it needs human judgement (genuine style/architecture call) -> NOT_REVIEWABLE.`}

Default to REFUTED / CITATION_FAILED whenever the auditor's evidence does not reproduce. A confirmed-but-wrong finding that drives a deletion is worse than a missed nit.

OUTPUT: write your full verification (commands + results) to ${ARC}/pipeline_round${R}_verify/${f.id}.md; return the schema. evidence <=600 chars in the return (full detail in the file).`
}

function synthPrompt(survivors, refuted, allCounts) {
  return `You are the SYNTHESIS agent for magpie-agent pipeline-audit round ${R}. The lens agents found machinery defects; an adversarial verifier already filtered them. Your job: cluster the SURVIVING (verified) findings by ROOT CAUSE and propose the minimal set of interventions. Do NOT re-audit; do NOT apply fixes (fixes are user-reviewed per pipeline-audit.md).

Per feedback_synthetic_interventions, N findings typically collapse to 2-3 root interventions: group by shared mechanism, not by symptom. A finding corroborated by multiple lenses usually points at one root. Honor the consolidation standing bias: prefer interventions that DELETE/MERGE/SIMPLIFY; flag any intervention that ADDS surface area (adds_surface=true) and justify it.

VERIFIED SURVIVING FINDINGS (verdict UPHELD or CORRECTED -- use the corrected scope where present):
${JSON.stringify(survivors, null, 1).slice(0, 14000)}

REFUTED / CITATION_FAILED (do NOT cluster these as real; they are listed so you can note any auditor false-positive pattern):
${JSON.stringify(refuted.map(r => ({ id: r.finding_id, verdict: r.verdict })), null, 1).slice(0, 2000)}

COUNTS: ${JSON.stringify(allCounts)}

OUTPUT:
- Write the full human-readable findings report (severity-ordered: location, failure mode, evidence, proposed fix, verifier verdict, corroboration, root-cause cluster; then a "verified clean" section; then a "refuted (auditor false-positives)" section) to ${ARC}/pipeline_audit_round${R}_findings.md
- Return the schema: clusters[] (root_cause, finding_ids, candidate_intervention, severity, adds_surface), an ordered recommendation (<=600 chars, highest-leverage first), and report_file.`
}

// ---------- light mechanical dedup across lenses (corroboration) ----------
function filepart(loc) { return String(loc || '').split(':')[0].trim().toLowerCase() }
function dedup(findings) {
  const groups = []
  for (const f of findings) {
    const g = groups.find(x => x.kind === f.kind && filepart(x.location) === filepart(f.location) && filepart(f.location) !== '')
    if (g) {
      g.corroborating_lenses.push(f.lens)
      g.merged_ids.push(f.id)
      // keep the highest severity + the longest evidence
      const order = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 }
      if ((order[f.severity] || 0) > (order[g.severity] || 0)) g.severity = f.severity
      if ((f.evidence || '').length > (g.evidence || '').length) g.evidence = f.evidence
    } else {
      groups.push({ ...f, corroborating_lenses: [f.lens], merged_ids: [f.id] })
    }
  }
  return groups
}

// ---------- run ----------
log(`Pipeline audit R${R} (preset=${PRESET}${A.lenses ? '+override' : ''}, verify=${VERIFY}): ${LENSES.length} lenses`)

phase('Lenses')
const lensResults = await parallel(LENSES.map((lens, i) => async () =>
  agent(lensPrompt(lens, i), { label: `lens:${lens.key}`, phase: 'Lenses', schema: LENS_SCHEMA }).catch(() => null)
))

const lensOk = lensResults.filter(Boolean)
const allFindings = lensOk.flatMap(r => (r.findings || []).map(f => ({ ...f, lens: r.lens })))
const deduped = dedup(allFindings)
const corroborated = deduped.filter(g => new Set(g.corroborating_lenses).size > 1)
log(`Lenses done: ${lensOk.length}/${LENSES.length} returned, ${allFindings.length} raw findings -> ${deduped.length} after dedup (${corroborated.length} corroborated across lenses).`)

// choose verify targets: by severity, capped (no silent truncation)
let verifyTargets = deduped.filter(g => VSEV.includes(g.severity))
const sevOrder = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 }
verifyTargets.sort((a, b) => (sevOrder[b.severity] || 0) - (sevOrder[a.severity] || 0))
let verifyDropped = 0
if (verifyTargets.length > VERIFY_CAP) {
  verifyDropped = verifyTargets.length - VERIFY_CAP
  log(`NOTE: ${verifyTargets.length} findings at ${VSEV.join('/')} exceed the verify cap (${VERIFY_CAP}); verifying the top ${VERIFY_CAP} by severity, ${verifyDropped} carried UNVERIFIED into the report.`)
  verifyTargets = verifyTargets.slice(0, VERIFY_CAP)
}

phase('Verify')
const verdicts = VERIFY
  ? (await parallel(verifyTargets.map(f => async () =>
      agent(verifyPrompt(f), { label: `verify:${f.id}`, phase: 'Verify', schema: VERDICT_SCHEMA }).catch(() => null)
    ))).filter(Boolean)
  : []

const vmap = {}
verdicts.forEach(v => { if (v && v.finding_id) vmap[v.finding_id] = v })
function verdictFor(g) { return vmap[g.id] || (g.merged_ids || []).map(id => vmap[id]).find(Boolean) || null }

// survivors = UPHELD/CORRECTED, plus LOW/unverified findings (reported, flagged unverified). refuted = REFUTED/CITATION_FAILED.
const annotated = deduped.map(g => {
  const v = verdictFor(g)
  return {
    id: g.id, lens: g.lens, kind: g.kind, severity: g.severity, location: g.location,
    failure_mode: g.failure_mode, evidence: g.evidence, suggested_fix: g.suggested_fix,
    corroborating_lenses: [...new Set(g.corroborating_lenses)],
    what_it_protects: g.what_it_protects, who_else_needs_it: g.who_else_needs_it, blast_radius: g.blast_radius,
    verdict: v ? v.verdict : (VERIFY && VSEV.includes(g.severity) ? 'NO_VERDICT' : 'UNVERIFIED'),
    corrected: (v && v.verdict === 'CORRECTED') ? v.corrected : null
  }
})
const survivors = annotated.filter(a => a.verdict === 'UPHELD' || a.verdict === 'CORRECTED' || a.verdict === 'UNVERIFIED' || a.verdict === 'NOT_REVIEWABLE')
const refuted = annotated.filter(a => a.verdict === 'REFUTED' || a.verdict === 'CITATION_FAILED')

const bySev = (arr) => ({ CRITICAL: arr.filter(x => x.severity === 'CRITICAL').length, HIGH: arr.filter(x => x.severity === 'HIGH').length, MEDIUM: arr.filter(x => x.severity === 'MEDIUM').length, LOW: arr.filter(x => x.severity === 'LOW').length })
const byLens = {}
LENSES.forEach(l => { byLens[l.key] = allFindings.filter(f => f.lens === l.title || f.lens === l.key).length })

const counts = { raw: allFindings.length, deduped: deduped.length, corroborated: corroborated.length, verified: verdicts.length, upheld: annotated.filter(a => a.verdict === 'UPHELD').length, corrected: annotated.filter(a => a.verdict === 'CORRECTED').length, refuted: refuted.length, survivors: survivors.length }

phase('Synthesize')
const synth = await agent(synthPrompt(survivors, refuted, counts), { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA }).catch(() => null)

// ---------- round-log object, READY for review-then-record (NOT auto-appended) ----------
const round_log_ready = {
  round: R,
  date: null,          // stamp at record time (Date.now unavailable in workflows)
  commit: null,        // stamp at record time (git rev-parse)
  auditor_model: 'claude-opus (workflow: lens + adversarial-verify + synthesis)',
  round_type: (A.lenses ? 'custom override' : PRESET) + ' (pipeline_audit_round.workflow.js)',
  lenses_run: LENSES.map(l => l.key),
  findings_total: deduped.length,
  by_severity: bySev(deduped),
  by_lens: byLens,
  corroborated: corroborated.map(g => ({ finding: g.failure_mode, location: g.location, lenses: [...new Set(g.corroborating_lenses)], severity: g.severity })),
  root_cause_clusters: synth ? synth.clusters : [],
  verify_stage: VERIFY ? `per-finding adversarial verify: ${verdicts.length} findings verified, ${counts.upheld} UPHELD, ${counts.corrected} CORRECTED, ${refuted.length} REFUTED/CITATION_FAILED${verifyDropped ? `, ${verifyDropped} over-cap unverified` : ''}` : 'SKIPPED (verify=false)',
  report_path: synth ? synth.report_file : null,
  guards_added: [],
  status: 'triaged (workflow) -- fixes pending user review'
}

return {
  round: R, preset: PRESET, verify: VERIFY,
  lenses_run: LENSES.map(l => l.key),
  lenses_dropped: LENSES.filter((l, i) => !lensResults[i]).map(l => l.key),
  counts,
  by_severity: bySev(deduped),
  corroborated: corroborated.map(g => ({ location: g.location, failure_mode: g.failure_mode, lenses: [...new Set(g.corroborating_lenses)], severity: g.severity })),
  survivors: survivors.map(s => ({ id: s.id, severity: s.severity, kind: s.kind, location: s.location, verdict: s.verdict, failure_mode: s.failure_mode.slice(0, 160) })),
  refuted_auditor_fps: refuted.map(r => ({ id: r.id, location: r.location, verdict: r.verdict })),
  clusters: synth ? synth.clusters : [],
  recommendation: synth ? synth.recommendation : '(synthesis agent failed)',
  report_file: synth ? synth.report_file : null,
  round_log_ready
}
