export const meta = {
  name: 'r51-longdoc-findrate',
  description: 'R51 Phase B-prime: audit each FULL injected doc with no pointing question; measure whether the auditor FINDS the one planted bug among all the doc claims (production-relevant find-rate).',
  phases: [{ title: 'FullDocAudit' }],
}

const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const DOCS = A.docs || []   // [{id, file}]
const ROOT = A.root || '/tmp/r51_longdoc'
const RUBRIC = ROOT + '/rubric.md'
const DEV = '/tmp/magpie_develop_ro'

const SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['doc_id', 'verdict', 'n_findings', 'findings', 'paths_consulted', 'notes'],
  properties: {
    doc_id: { type: 'string' },
    verdict: { type: 'string', enum: ['CLEAN', 'MINOR_ISSUES', 'SIGNIFICANT_ERRORS', 'FUNDAMENTALLY_FLAWED'] },
    n_findings: { type: 'integer' },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['flagged_claim', 'doc_location', 'severity', 'bug_class', 'code_evidence', 'verify_cmd'],
        properties: {
          flagged_claim: { type: 'string' },
          doc_location: { type: 'string', description: 'line or section in the doc where the wrong claim is' },
          severity: { type: 'string', enum: ['Critical', 'Major', 'Minor', 'Informational'] },
          bug_class: { type: 'string' },
          code_evidence: { type: 'string', description: 'develop file:line proving it wrong + the real content' },
          verify_cmd: { type: 'string', description: 'exact command run against the code worktree + result' },
        },
      },
    },
    paths_consulted: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string', description: '<=300 chars' },
  },
}

function prompt(d) {
  return `You are an expert MAgPIE documentation auditor doing a FULL-DOCUMENT audit. Read the entire document and find EVERY claim that contradicts the GAMS code. You do NOT know how many errors it has — it may contain zero, one, or several. Many real docs are mostly correct.

DOCUMENT TO AUDIT (read the whole file): ${ROOT}/${d.id}/${d.file}

GROUND TRUTH = CODE ONLY: the detached origin/develop worktree at ${DEV}. For EACH load-bearing claim in the doc, verify it against code:
  - realization names + which is DEFAULT -> ${DEV}/config/default.cfg (grep cfg$gms$<module>)
  - variable/equation EXISTENCE + which module DECLARES (declarations.gms) / POPULATES (equation LHS =e=) / READS (RHS) / CONSUMES it
  - scalar/switch defaults; consumer/producer sets; variable index domains; file:line citations; mechanism-vs-parameterization claims
You will not be able to verify every sentence — prioritize the load-bearing, code-checkable claims (interface variables, equations, realizations/defaults, attributions, citations, data-flow arrows). Assign each finding a severity tier per ${RUBRIC}.

STRICT ISOLATION (integrity — a violation invalidates this audit):
- Use ONLY ${ROOT}/ (the doc + rubric) and ${DEV}/ (code). Nothing else.
- Do NOT read anything under any 'magpie-agent' directory; do NOT run git log/show/blame; do NOT open the ORIGINAL/canonical copy of this doc or any other AI doc. Those would be an answer key.
- Ground EVERY finding in code read THIS run: code_evidence = a ${DEV} file:line with real content; verify_cmd = the exact command + its result.

GREP DISCIPLINE: rg/grep can exit 1 or return empty even with matches. Isolate each grep; cross-check absence a second way; run a POSITIVE CONTROL (a known-present sibling token) before concluding absence. For "does X consume V", grep BOTH 'V(' AND 'V.' (.l/.lo/.fx). For "is the default Y", read config/default.cfg.

REPORT DISCIPLINE: report a finding ONLY where the doc genuinely contradicts code; if the doc is fully correct, n_findings=0 / verdict CLEAN. Do NOT pad. List every path consulted. Write nothing to disk. Return the schema (notes <= 300 chars).`
}

phase('FullDocAudit')
log(`R51 B-prime: ${DOCS.length} full injected docs, 1 isolated Opus auditor each (find-in-long-doc).`)
const results = await parallel(DOCS.map((d) => () =>
  agent(prompt(d), { label: `longdoc:${d.id}`, phase: 'FullDocAudit', model: 'opus', schema: SCHEMA }).catch(() => null)
))
const ok = results.filter(Boolean)
return { round: 51, phase: 'B-prime', n_requested: DOCS.length, n_returned: ok.length,
         dropped: DOCS.filter((d, i) => !results[i]).map(d => d.id), results: ok }
