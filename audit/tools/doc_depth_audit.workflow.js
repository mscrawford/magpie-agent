export const meta = {
  name: 'magpie-doc-depth-audit',
  description: 'DEPTH-FIRST per-claim doc audit for a few high-stakes hubs: exhaustive claim ledger (coverage denominators) -> K decorrelated Opus lenses per doc (each a different code entry point, armed with the code-derived role map) -> adversarial refutation of every Critical/Major -> residual-density measurement. REPORTS verified findings; does NOT auto-edit docs.',
  phases: [
    { title: 'Enumerate' },
    { title: 'Audit' },
    { title: 'Verify' },
    { title: 'Measure' },
  ],
}

// ---- args (JSON string from the harness) ----
// args.round   : int (magpie-agent round number, e.g. 55)
// args.docs    : [{ path, label, klass }]   klass in module|cross_module|core
// args.lenses  : optional override of the K decorrelation lenses
// args.paths   : { agentDir, parent, dev, rolemap }  (absolute, machine-local)
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const R = A.round
const DOCS = A.docs || []
// Machine-local checkout roots. Pass via args.paths = {agentDir, parent, dev, rolemap}
// to run on your own clone; the defaults below are PLACEHOLDERS and MUST be overridden.
const P = A.paths || {}
const AGENT_DIR = P.agentDir || '/path/to/magpie/magpie-agent'
const PARENT = P.parent || '/path/to/magpie'
const DEV = P.dev || '/tmp/magpie_develop_ro'   // detached origin/develop worktree (verification truth)
const ROLEMAP = P.rolemap || (AGENT_DIR + '/audit/integrated/depth_rolemap.json')
const ARC = AGENT_DIR + '/audit/archive/rounds'
const RUBRIC = AGENT_DIR + '/audit/flywheel_rubric.md'
const VERIFIERS = AGENT_DIR + '/agent/helpers/verifiers.md'

// ---------- shared guard text (reused verbatim from doc_audit_round.workflow.js) ----------
const GREP_GUARD = `CRITICAL grep rules (a verified false-positive source in this repo):
  - A bare 'grep -r' can SILENTLY return empty even when matches exist. Never trust it alone.
  - 'find ... -exec grep {} +' returns EXIT 1 when the final batch has no match, which ABORTS any chained command and silently TRUNCATES output. Run each grep probe as its OWN standalone command (or append '|| true').
  - rg (ripgrep) IS available; prefer 'rg -n PATTERN ${DEV}/modules/' (rg also exits 1 on no-match -> isolate it).
  - ALWAYS cross-check a zero/absence result with a SECOND method AND a POSITIVE CONTROL: grep a known-present sibling token to prove the search works in that dir before concluding 'X is absent'.
  - Co-located names: a module number cited for an ADJACENT parameter on the same doc line is NOT a consumer of THIS parameter (false advisory on module_52.md:291).
  - SOLUTION-LEVEL reads: a module can consume a variable via attributes (NAME.l/.lo/.up/.fx/.m) in presolve/postsolve, invisible to a 'NAME(' grep. Grep BOTH 'NAME(' AND 'NAME.' before concluding consumption (R33: module 32 reads vm_area.l/.lo in presolve.gms:17, invisible to 'vm_area(').
  - DATA-FLOW DIRECTION (serial vs parallel): for any "M_A hands off X to M_B" / "M_B receives X from M_A" / "X flows A->B->C" claim, open BOTH endpoints: confirm whether M_B reads M_A's OUTPUT (genuine serial) OR both read the SAME shared interface var INDEPENDENTLY (PARALLEL, NOT a hand-off). DEFAULT to parallel-not-serial until code proves otherwise (R51: 'M52 routes to M56' was wrong; M56 reads vm_carbon_stock DIRECTLY in q56_emis_pricing_co2, parallel to M52. verifiers.md MANDATE 21).
  - FIND THE PRODUCER before calling any input/parameter MISSING/STALE/SILENTLY-ZERO. A file under modules/*/input/ may be a RUN-TIME product of scripts/ (*.cs* are gitignored, regenerated at run start). Before any such claim grep the WHOLE repo root (rg -n '<switch>' ${PARENT}, incl. scripts/ and .R) and read the accused commit's non-.gms files. R53's Critical was exactly this: every premise TRUE, conclusion FALSE, because scripts/start_functions.R regenerates the .cs3.
A "module does NOT consume X" / "zero consumers" claim is the highest-risk false positive: confirm twice + positive control before calling a documented consumer a phantom, and before adding an 'omitted' consumer confirm it truly references the variable (not a look-alike).`

const MANDATES = `Apply the verifiers.md MANDATEs (read ${VERIFIERS} if unsure), especially:
  - 13 interface-consumer grep (verify producer/consumer SETS against code, list every module);
  - 17 direct vs transitive consumer (a module that reads a var that reads X is NOT a direct consumer of X);
  - 16 citations: full path modules/NN_name/realization/file.gms:LINE, line numbers verified in CURRENT develop;
  - 8 realization-name verification (ls ${DEV}/modules/NN_*/ for real dir names);
  - 3 default-parameter verification (grep the default in code + config/default.cfg);
  - Distinguish DECLARED vs POPULATED vs READ for interface variables (the G2 carbon-stock distinction).`

// This repo is PUBLIC and git history is permanent. Agents are handed ABSOLUTE
// machine paths (args.paths), and R55 showed they echo them straight into their
// reports -- which would bake the local username into public history forever.
// Every report-writing prompt carries this clause.
const PATH_HYGIENE = `PATH HYGIENE (this repo is PUBLIC; git history is permanent): in the REPORT TEXT you write, refer to files by REPO-RELATIVE path only -- 'modules/module_10.md', 'modules/NN_name/realization/file.gms', 'audit/...'. NEVER write an absolute machine path (no '/Users/...', '/home/...', '/p/projects/...') into a report, even when quoting the target path given to you above. Absolute paths leak the local username into permanent public history.`

const ROLEMAP_CLAUSE = `CODE-DERIVED GROUND TRUTH for interface-var attribution: read ${ROLEMAP} (JSON: var -> {declared_in, populated_by[], read_by[]}, computed deterministically from ${DEV} by scripts/check_attribution_omissions.py). For any DECLARED/POPULATED/READ or consumer/producer claim about a vm_/pm_/im_/pcm_/fm_ var, CHECK IT AGAINST THIS MAP FIRST (it is ~0-FNR on this class and kills the correlated-confabulation blind spot). The map is a SUPERSET reference: verify the specific direction (populate vs read) and confirm with a BOTH-endpoints grep before flagging; if the map and your grep disagree, re-grep (both NAME( and NAME.) and trust code, noting the discrepancy.`

function groundTruthClause(doc) {
  if (doc.klass === 'module') {
    return `GROUND TRUTH: MAgPIE code in the develop worktree ${DEV} (NEVER the working tree). For defaults/realizations read ${DEV}/config/default.cfg. Lead with the DEFAULT realization.`
  }
  return `GROUND TRUTH: MAgPIE code in the develop worktree ${DEV}. This doc makes CROSS-MODULE claims (consumer/populator/dependency sets) -> whole-tree greps required; the grep guard is load-bearing.`
}

// ---------- decorrelation lenses (engineer it, don't hope for it) ----------
// Each lens audits the WHOLE doc but ENTERS the code from a different vantage, so the
// K auditors cannot collapse to the same prior. Coverage is the union; the adversarial
// verifier culls the false positives.
const DEFAULT_LENSES = [
  { key: 'declare_populate', focus: `Enter from the DECLARING/POPULATING side: ${DEV}/modules/<owner>/*/declarations.gms and equation LHS / .fx / assignments. Prioritize claims about which module DECLARES or POPULATES each interface var, and the formulas the doc attributes to THIS module's equations (do the equation bodies match the doc's described formula/mechanism?).` },
  { key: 'consumer_read', focus: `Enter from the CONSUMER side: the presolve/postsolve/equation-RHS of modules the doc names as readers, plus a whole-tree grep of BOTH 'NAME(' and 'NAME.' for each interface var. Prioritize READ/consumer SET claims (phantoms AND omissions) and solution-level .l/.lo reads.` },
  { key: 'config_realization', focus: `Enter from ${DEV}/config/default.cfg and the realization directories (ls ${DEV}/modules/NN_*/). Prioritize default-value claims, cfg$gms$* switch behavior, realization NAMES, and which realization is DEFAULT (the doc must lead with the default; a non-default described as active is Critical-prone).` },
  { key: 'citation_formula', focus: `Enter from the exact file:line CITATIONS in the doc. For each, mechanically check: file exists (test -f), line in range (wc -l), and the line contains the claimed token/identifier. Prioritize citation drift (line now points to materially different content) and equation-formula fidelity.` },
  { key: 'mechanism_direction', focus: `Enter from equation BODIES and cross-module data-flow. Prioritize mechanism claims ("MAgPIE models/accounts for X" -> is it CALCULATED/mechanistic or PARAMETERIZED from input data?), causal DIRECTION and serial-vs-parallel hand-offs (open BOTH endpoints; default parallel-not-serial), and set-membership/count claims.` },
]
const LENSES = A.lenses || DEFAULT_LENSES

// ---------- schemas ----------
const SEV = { type: 'string', enum: ['Critical', 'Major', 'Minor', 'Informational'] }
const CLASS_ENUM = ['attribution_declare', 'attribution_populate', 'attribution_read', 'citation', 'formula', 'default_value', 'realization', 'mechanism', 'data_flow_direction', 'set_membership', 'other']

const LEDGER_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['doc', 'total_checkable', 'by_class', 'notes'],
  properties: {
    doc: { type: 'string' },
    total_checkable: { type: 'integer', description: 'count of load-bearing, code-checkable claims in the doc' },
    by_class: {
      type: 'object', additionalProperties: false,
      required: CLASS_ENUM,
      properties: Object.fromEntries(CLASS_ENUM.map(c => [c, { type: 'integer' }])),
    },
    notes: { type: 'string', description: '<=300 chars' },
  },
}

const DOC_AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['doc', 'lens', 'claims_verified', 'bugs', 'deferred', 'report_file', 'summary'],
  properties: {
    doc: { type: 'string' }, lens: { type: 'string' },
    claims_verified: { type: 'integer' },
    bugs: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'severity', 'bug_class', 'doc_line', 'claim_in_doc', 'reality_in_code', 'file_evidence', 'verify_cmd', 'confirmed', 'proposed_fix'],
        properties: {
          id: { type: 'string' }, severity: SEV,
          bug_class: { type: 'string', enum: CLASS_ENUM },
          doc_line: { type: 'string', description: 'e.g. module_10.md:315' },
          claim_in_doc: { type: 'string' }, reality_in_code: { type: 'string' },
          file_evidence: { type: 'string', description: 'develop file:line' },
          verify_cmd: { type: 'string', description: 'exact command run, with its result' },
          confirmed: { type: 'boolean', description: 'true only if reproducible code evidence supports it' },
          proposed_fix: { type: 'string' },
        },
      },
    },
    deferred: { type: 'array', items: { type: 'string' } },
    report_file: { type: 'string' },
    summary: { type: 'string', description: '<=300 chars' },
  },
}

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdicts', 'notes', 'report_file'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['bug_id', 'class', 'citation_ok', 'verdict', 'corrected_claim', 'evidence'],
        properties: {
          bug_id: { type: 'string' },
          class: { type: 'string', enum: ['consumer_set', 'producer_declaration', 'realization_structure', 'formula_or_value', 'mechanism', 'other'] },
          citation_ok: { type: 'boolean', description: 'MECHANICAL: file_evidence exists, line in range, line contains the claimed token' },
          verdict: { type: 'string', enum: ['UPHELD', 'REFUTED', 'CORRECTED', 'CITATION_FAILED', 'NOT_REVIEWABLE'] },
          corrected_claim: { type: 'string', description: 'if CORRECTED: the precise corrected claim; else ""' },
          evidence: { type: 'string', description: 'exact cmds + results: citation check AND (for attribution) BOTH NAME( and NAME. greps + positive control' },
        },
      },
    },
    notes: { type: 'string' }, report_file: { type: 'string' },
  },
}

const MEASURE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', 'reasoning', 'expected_corpus_criticals', 'recommendation', 'report_file'],
  properties: {
    verdict: { type: 'string', enum: ['GO', 'NO_GO', 'TARGETED_ONLY'] },
    reasoning: { type: 'string' },
    expected_corpus_criticals: { type: 'string', description: 'extrapolation from hub density + how derived' },
    recommendation: { type: 'string' },
    report_file: { type: 'string' },
  },
}

// ---------- prompts ----------
function enumeratePrompt(doc) {
  return `You are a claim EXTRACTOR for a depth-first documentation audit. Do NOT verify anything against code — only ENUMERATE and COUNT.

TARGET DOC: ${AGENT_DIR}/${doc.path}

Read the WHOLE doc. Count every LOAD-BEARING, CODE-CHECKABLE claim and bucket it by class:
  attribution_declare (which module declares a var), attribution_populate (which populates it), attribution_read (which reads/consumes it),
  citation (a modules/.../file.gms:LINE reference), formula (an equation formula/relationship), default_value (a scalar/parameter default),
  realization (a realization name / which is default), mechanism ("MAgPIE models/accounts for X"), data_flow_direction (A hands off to B / receives from),
  set_membership (a set's members / a count / a range), other (any other code-checkable factual claim).
Count a claim once, in its most specific class. Skip pure prose/advice that no code could confirm or refute.

OUTPUT: return the schema. total_checkable = sum of by_class. This is the COVERAGE DENOMINATOR for the measurement — be thorough and honest, not conservative.`
}

function lensAuditPrompt(doc, lens) {
  return `You are an ADVERSARIAL depth-first documentation auditor (lens: ${lens.key}) for the MAgPIE-agent. Audit ONE whole doc against code and report every code-verifiable error. Other auditors cover other vantages; YOUR decorrelation job is the lens below — but report ANY bug you find, not only lens-matching ones.

TARGET DOC: ${AGENT_DIR}/${doc.path}
${groundTruthClause(doc)}

YOUR LENS (${lens.key}): ${lens.focus}

${ROLEMAP_CLAUSE}

Read the rubric ${RUBRIC} for severity tiers and bug classes. Wrong consumer/populator SETS and inverted/false defaults are Critical-prone; citation drift to materially-different content is Major.

${MANDATES}

${GREP_GUARD}

METHOD:
1. Read the full target doc. Through your lens, enumerate the load-bearing code-checkable claims and verify EACH against ground truth. For attribution, check the role map FIRST, then confirm the direction with a BOTH-endpoints grep.
2. For every discrepancy record a bug: severity, bug_class (use the enum), exact doc quote + doc_line (${doc.label}:NN), reality_in_code, file_evidence (develop file:line), the exact verify_cmd WITH its result, confirmed (true ONLY with reproducible evidence), precise proposed_fix.
3. Anything you cannot verify or are unsure about -> one-line note in "deferred" (do NOT invent a bug; do NOT propose an edit). FALSE POSITIVES ARE WORSE THAN MISSES.

${PATH_HYGIENE}

OUTPUT: write your full report to ${ARC}/round${R}_depth/${doc.label}__${lens.key}.md and return the schema (summary <=300 chars; lens="${lens.key}").`
}

function verifyPrompt(doc, bugs) {
  return `You are an ADVERSARIAL VERIFIER (highest capability) for a depth-first doc audit. For EVERY bug below, FIRST run a MECHANICAL citation check, then adversarially adjudicate. DEFAULT TO SKEPTICISM. Auditors over/under-count sets and CONFABULATE non-default realization structure; these confabulations are CORRELATED across LLM agents, so your only reliable tool is MECHANICAL verification (test -f, wc -l, read the exact line, isolated grep + positive control) — NOT recall.

TARGET DOC: ${AGENT_DIR}/${doc.path}
${groundTruthClause(doc)}
${ROLEMAP_CLAUSE}

${GREP_GUARD}

BUGS TO VERIFY (deduped across lenses):
${JSON.stringify(bugs.map(b => ({ id: b.id, severity: b.severity, bug_class: b.bug_class, doc_line: b.doc_line, claim_in_doc: b.claim_in_doc, reality_in_code: b.reality_in_code, file_evidence: b.file_evidence, proposed_fix: b.proposed_fix })), null, 1)}

For EACH bug:
STEP A - MECHANICAL CITATION CHECK: for file_evidence and any file:line in proposed_fix, run test -f, wc -l, and read the exact line (does it contain the claimed token?). If the file is absent / line out of range / line lacks the content -> citation_ok=false, verdict=CITATION_FAILED. Record exact cmds+results in evidence.
STEP B - CLASSIFY 'class' (consumer_set | producer_declaration | realization_structure | formula_or_value | mechanism | other).
STEP C - ADJUDICATE (only if citation_ok=true):
  - consumer_set / producer_declaration: INDEPENDENTLY re-derive the true set from ${DEV} (role map + BOTH 'NAME(' and 'NAME.' greps + positive control + direct-vs-transitive). UPHELD / REFUTED / CORRECTED (corrected_claim = the precise claim to apply).
  - realization_structure: read the SPECIFIC realization's actual files (ls, wc -l, read the cited equations.gms). UPHELD / REFUTED / CORRECTED.
  - formula_or_value / mechanism: re-derive from the equation body / parameter source; for mechanism apply the parameterized-vs-mechanistic 3-check. UPHELD / REFUTED / CORRECTED.
  - other: NOT_REVIEWABLE.
Default to REFUTED / CORRECTED / CITATION_FAILED whenever the auditor's evidence does not reproduce. A false finding that looks freshly-verified is worse than a miss.

${PATH_HYGIENE}

OUTPUT: write full verification to ${ARC}/round${R}_depth/verify__${doc.label}.md; return the schema (notes <=300 chars).`
}

function measurePrompt(matrix, perDoc) {
  return `You are the MEASUREMENT synthesizer for a depth-first doc-accuracy audit of 3 high-stakes MAgPIE-agent hub docs (M10 land, M52 carbon, M56 ghg_policy). The numeric matrix below was computed deterministically from the verified findings (only UPHELD/CORRECTED survive) and the claim-ledger denominators. Your job: interpret it and issue a go/no-go on a FULL-CORPUS depth campaign.

RESIDUAL-DENSITY MATRIX (confirmed bugs / claims-checked, per class x severity, per doc + pooled):
${JSON.stringify(matrix, null, 1)}

PER-DOC DETAIL (ledger totals, verified counts, refuted/corrected/citation-failed):
${JSON.stringify(perDoc, null, 1)}

DECISION RULE (the hubs are highest-centrality -> an UPPER-BOUND sample of corpus bug density):
  - GO (full-corpus depth warranted) if EITHER (a) >=1 confirmed Critical-class attribution omission per hub that survived the 2026-06-29 wide-net 9.52 pass, OR (b) pooled semantic density > ~1 confirmed Critical / 2 docs OR > ~2 Major-attribution bugs / 100 attribution claims checked.
  - NO_GO / TARGETED_ONLY if the hubs are below threshold: even the densest docs are clean at depth -> run mechanical-only corpus-wide (free) and reserve semantic depth for the top-centrality quartile.
Extrapolate expected_corpus_criticals ~= hub_density x corpus_attribution_claim_count (state how you derived it; it is an estimate, not a guarantee). Report the attribution-class residual SEPARATELY and note it must NEVER be relayed as answer-quality.

${PATH_HYGIENE}

OUTPUT: write the full measurement report (matrix table, what the 9.52 pass missed, the go/no-go with reasoning) to ${ARC}/round${R}_depth/MEASUREMENT.md; return the schema.`
}

// ---------- helpers ----------
function normClaim(b) {
  return `${(b.doc_line || '').trim()}::${(b.claim_in_doc || '').trim().slice(0, 80).toLowerCase()}`
}

// ---------- run ----------
log(`Depth-first R${R}: ${DOCS.length} docs x ${LENSES.length} lenses. Ground-truth role map: ${ROLEMAP}`)

phase('Enumerate')
const ledgers = await parallel(DOCS.map((doc) => async () =>
  agent(enumeratePrompt(doc), { label: `ledger:${doc.label}`, phase: 'Enumerate', model: 'sonnet', schema: LEDGER_SCHEMA }).catch(() => null)
))
const ledgerByLabel = {}
DOCS.forEach((d, i) => { ledgerByLabel[d.label] = ledgers[i] })

phase('Audit')
// For each doc, run K decorrelated Opus lenses (all in one flat parallel pool).
const auditJobs = []
DOCS.forEach((doc) => LENSES.forEach((lens) => {
  auditJobs.push({ doc, lens })
}))
const audits = await parallel(auditJobs.map((j) => async () =>
  agent(lensAuditPrompt(j.doc, j.lens), { label: `audit:${j.doc.label}:${j.lens.key}`, phase: 'Audit', model: 'opus', schema: DOC_AUDIT_SCHEMA })
    .then(r => (r ? { ...r, _label: j.doc.label } : null))
    .catch(() => null)
))

// Dedup bugs per doc across lenses (union coverage, single verification per unique claim).
const bugsByDoc = {}
DOCS.forEach(d => { bugsByDoc[d.label] = {} })
audits.filter(Boolean).forEach(a => {
  const label = a._label
  ;(a.bugs || []).filter(b => b && b.confirmed).forEach(b => {
    const k = normClaim(b)
    if (!bugsByDoc[label][k]) bugsByDoc[label][k] = { ...b, id: `${label}:${Object.keys(bugsByDoc[label]).length + 1}`, lenses: [a.lens] }
    else bugsByDoc[label][k].lenses.push(a.lens)
  })
})

phase('Verify')
// Adversarially refute every Critical/Major (cap per doc to bound cost); Minor/Info pass through unverified but are NOT counted as confirmed in the density.
const verifyByDoc = await parallel(DOCS.map((doc) => async () => {
  const all = Object.values(bugsByDoc[doc.label])
  const toVerify = all.filter(b => b.severity === 'Critical' || b.severity === 'Major').slice(0, 30)
  if (!toVerify.length) return { label: doc.label, verdicts: [] }
  const v = await agent(verifyPrompt(doc, toVerify), { label: `verify:${doc.label}`, phase: 'Verify', model: 'opus', schema: VERIFY_SCHEMA }).catch(() => null)
  return { label: doc.label, verdicts: (v && v.verdicts) || [], report_file: v && v.report_file }
}))
const verdictByBug = {}
verifyByDoc.forEach(vd => (vd.verdicts || []).forEach(v => { verdictByBug[v.bug_id] = v }))

// ---------- compute the residual-density matrix (JS; deterministic) ----------
const SURVIVE = new Set(['UPHELD', 'CORRECTED'])
function isConfirmed(b) {
  if (b.severity === 'Critical' || b.severity === 'Major') {
    const v = verdictByBug[b.id]
    return v ? SURVIVE.has(v.verdict) : false   // Crit/Major MUST survive refutation
  }
  return true  // Minor/Info: auditor-confirmed, not adversarially re-checked
}
const emptyCell = () => ({ Critical: 0, Major: 0, Minor: 0, Informational: 0 })
const matrix = { pooled: { by_class: {}, denominator: { total: 0, by_class: {} } }, per_doc: {} }
CLASS_ENUM.forEach(c => { matrix.pooled.by_class[c] = emptyCell(); matrix.pooled.denominator.by_class[c] = 0 })

const perDoc = DOCS.map(doc => {
  const led = ledgerByLabel[doc.label] || { total_checkable: 0, by_class: {} }
  const bugs = Object.values(bugsByDoc[doc.label])
  const confirmed = bugs.filter(isConfirmed)
  const cell = {}; CLASS_ENUM.forEach(c => cell[c] = emptyCell())
  confirmed.forEach(b => {
    const c = CLASS_ENUM.includes(b.bug_class) ? b.bug_class : 'other'
    cell[c][b.severity] = (cell[c][b.severity] || 0) + 1
    matrix.pooled.by_class[c][b.severity] += 1
  })
  CLASS_ENUM.forEach(c => {
    const d = (led.by_class && led.by_class[c]) || 0
    matrix.pooled.denominator.by_class[c] += d
  })
  matrix.pooled.denominator.total += led.total_checkable || 0
  const vd = verifyByDoc.find(v => v.label === doc.label) || { verdicts: [] }
  matrix.per_doc[doc.label] = { by_class: cell, denominator: led.by_class || {}, total_checkable: led.total_checkable || 0 }
  return {
    label: doc.label,
    total_checkable: led.total_checkable || 0,
    confirmed_total: confirmed.length,
    confirmed_critical: confirmed.filter(b => b.severity === 'Critical').length,
    confirmed_major: confirmed.filter(b => b.severity === 'Major').length,
    attribution_omissions: confirmed.filter(b => b.bug_class && b.bug_class.startsWith('attribution')).length,
    refuted: (vd.verdicts || []).filter(v => v.verdict === 'REFUTED').length,
    corrected: (vd.verdicts || []).filter(v => v.verdict === 'CORRECTED').length,
    citation_failed: (vd.verdicts || []).filter(v => v.verdict === 'CITATION_FAILED').length,
    dropped_lenses: LENSES.length - audits.filter(a => a && a._label === doc.label).length,
    confirmed_bugs: confirmed.map(b => ({ id: b.id, severity: b.severity, bug_class: b.bug_class, doc_line: b.doc_line, claim: b.claim_in_doc, reality: b.reality_in_code, evidence: b.file_evidence, fix: b.proposed_fix, lenses: b.lenses })),
  }
})

phase('Measure')
const measure = await agent(measurePrompt(matrix, perDoc.map(d => ({ ...d, confirmed_bugs: undefined }))), { label: 'measure', phase: 'Measure', model: 'opus', schema: MEASURE_SCHEMA }).catch(() => null)

return {
  round: R,
  docs: DOCS.map(d => d.label),
  lenses: LENSES.map(l => l.key),
  matrix,
  per_doc: perDoc,
  measurement: measure,
  totals: {
    confirmed: perDoc.reduce((n, d) => n + d.confirmed_total, 0),
    critical: perDoc.reduce((n, d) => n + d.confirmed_critical, 0),
    major: perDoc.reduce((n, d) => n + d.confirmed_major, 0),
    refuted: perDoc.reduce((n, d) => n + d.refuted, 0),
    citation_failed: perDoc.reduce((n, d) => n + d.citation_failed, 0),
  },
}
