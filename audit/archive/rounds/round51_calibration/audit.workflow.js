export const meta = {
  name: 'r51-calibration-audit',
  description: 'R51 Phase 0: each of 37 planted/clean fixtures audited by ONE isolated Opus auditor (code-only ground truth) to measure the production auditor false-negative + false-positive rate.',
  phases: [{ title: 'Audit' }],
}

// args: { ids: ["fixture_01", ...] }
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const IDS = A.ids || []
const CAL = '/tmp/r51_cal'
const DEV = '/tmp/magpie_develop_ro'

const SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['fixture_id', 'verdict', 'n_findings', 'findings', 'paths_consulted', 'notes'],
  properties: {
    fixture_id: { type: 'string' },
    verdict: { type: 'string', enum: ['ACCURATE', 'MINOR_ISSUES', 'SIGNIFICANT_ERRORS', 'FUNDAMENTALLY_FLAWED'] },
    n_findings: { type: 'integer' },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['flagged_claim', 'severity', 'bug_class', 'code_evidence', 'verify_cmd'],
        properties: {
          flagged_claim: { type: 'string', description: 'the exact claim in the answer you judge wrong' },
          severity: { type: 'string', enum: ['Critical', 'Major', 'Minor', 'Informational'] },
          bug_class: { type: 'string' },
          code_evidence: { type: 'string', description: 'develop file:line that proves it wrong, with the actual code content' },
          verify_cmd: { type: 'string', description: 'exact command run against the code worktree + its result' },
        },
      },
    },
    paths_consulted: { type: 'array', items: { type: 'string' }, description: 'every file/dir you read or grepped (for isolation audit)' },
    notes: { type: 'string', description: '<=300 chars' },
  },
}

function auditPrompt(id) {
  return `You are an expert MAgPIE documentation auditor. Audit ONE answer for any claim that contradicts the GAMS code. This is a BLIND audit: you do NOT know whether this answer is fully correct or contains an error. Many answers ARE fully correct.

ANSWER TO AUDIT: read ${CAL}/fixtures/${id}.md (it contains a Question and an Answer). Audit the ANSWER's claims.

GROUND TRUTH = CODE ONLY: the detached origin/develop worktree at ${DEV}. Verify every code-checkable claim against it:
  - realization names + which is DEFAULT -> ${DEV}/config/default.cfg (grep cfg$gms$<module>)
  - variable/equation EXISTENCE + which module DECLARES (declarations.gms) / POPULATES (equation LHS, =e=) / READS (RHS) it
  - scalar / switch defaults (s*_*) -> ${DEV}/config/default.cfg
  - consumer / producer sets, index domains, file:line citations, and mechanism-vs-parameterization claims -> read the actual .gms files
Severity tiers + bug classes: read ${CAL}/rubric.md and assign each finding a tier (Critical/Major/Minor/Informational).

STRICT ISOLATION (calibration integrity — a violation invalidates this audit):
- Use ONLY ${CAL}/ (the fixture + rubric) and ${DEV}/ (code). Nothing else.
- Do NOT read anything under any directory named 'magpie-agent'; do NOT run git log / git show / git blame; do NOT open AI documentation files (module_*.md, core_docs/, cross_module/). Those are an answer key and using them invalidates the measurement.
- Ground EVERY finding in code you read THIS run: code_evidence must be a ${DEV} file:line with the real content, and verify_cmd the exact command you ran plus its result.

GREP DISCIPLINE (a verified false-positive source here): rg/grep can exit 1 or return empty even when matches exist. Isolate each grep as its own step; cross-check any absence a SECOND way; and run a POSITIVE CONTROL (grep a known-present sibling token in the same dir) before concluding something is absent. To test "does module X consume variable V", grep BOTH 'V(' AND 'V.' (solution-level .l/.lo/.fx/.up). To test "is the default Y", read config/default.cfg, do not guess.

REPORT DISCIPLINE: report a finding ONLY where the answer genuinely contradicts code. If the answer is fully correct, return n_findings=0 and verdict ACCURATE. Do NOT invent or pad findings — false positives are scored against you exactly like misses. List every path you consulted in paths_consulted. Write nothing to disk.

Return the schema object (notes <= 300 chars).`
}

phase('Audit')
log(`R51 calibration: ${IDS.length} fixtures, 1 isolated Opus auditor each (code-only ground truth).`)
const results = await parallel(IDS.map((id) => () =>
  agent(auditPrompt(id), { label: `audit:${id}`, phase: 'Audit', model: 'opus', schema: SCHEMA }).catch(() => null)
))

const ok = results.filter(Boolean)
return {
  round: 51, phase: '0_calibration', n_requested: IDS.length, n_returned: ok.length,
  dropped: IDS.filter((id, i) => !results[i]),
  results: ok,
}
