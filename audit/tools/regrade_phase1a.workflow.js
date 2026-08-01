export const meta = {
  name: 'magpie-phase1a-regrade',
  description: 'Re-grade all 104 Phase 1A answers on the written-file substrate with a hardened, un-anchored rubric.',
  phases: [
    { title: 'Grade', detail: '2 independent blind graders per trap group' },
    { title: 'Adjudicate', detail: 'one adjudicator per trap that has disagreements' },
  ],
}

// args arrives as a JSON-encoded STRING from the harness -> parse it.
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const TRAPS = A.traps || ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8']
const N_GRADERS = A.graders || 2
const TRUTH = A.truth || {}

if (!Array.isArray(TRAPS) || TRAPS.length === 0) {
  throw new Error('vacuity guard: no traps to grade')
}

const VERDICTS = ['ASSERTS_FALSEHOOD', 'OMITS_DEFAULT_CAVEAT', 'CORRECT_AND_COMPLETE', 'NOT_ELICITED']

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['code_truth_check', 'verdicts'],
  properties: {
    code_truth_check: {
      type: 'string',
      description: 'State whether you CONFIRMED the code-truth premise yourself against the GAMS source, and say so explicitly if you disagree with it.',
    },
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['label', 'trap_verdict', 'evidence'],
        properties: {
          label: { type: 'string' },
          trap_verdict: { type: 'string', enum: VERDICTS },
          evidence: { type: 'string', description: 'verbatim sentence from the answer that decides it, <=300 chars' },
          other_falsehoods: {
            type: 'array',
            description: 'ANY other assertion in this answer that the code contradicts - names, paths, line numbers, equations. Empty if none.',
            items: {
              type: 'object',
              additionalProperties: false,
              required: ['claim', 'why_wrong'],
              properties: {
                claim: { type: 'string' },
                why_wrong: { type: 'string' },
              },
            },
          },
          note: { type: 'string' },
        },
      },
    },
  },
}

function gradePrompt(trap, truth, seed) {
  return `You are grading assistant answers about the MAgPIE land-use model. Be strict, literal and independent.

STEP 0 - locate your inputs, and STOP if you cannot.
Find the repository root: the directory containing BOTH a \`modules/\` directory AND a \`.regrade/\`
directory. Read \`.regrade/batch_${trap}.md\` relative to that root. If you cannot read it, do NOT
guess and do NOT substitute any other file - return immediately with code_truth_check explaining
what you could not reach. (A previous run had agents silently fall back to a different directory;
that is the failure this step exists to prevent.)

STEP 1 - verify the code truth YOURSELF against the GAMS source under \`modules/\`, \`core/\` and
\`config/default.cfg\`. Do not take it on faith. If you disagree, say so in code_truth_check and
grade according to what the code actually says.

  CLAIMED CODE TRUTH FOR THIS GROUP:
  ${truth}

STEP 2 - for EVERY answer in the batch, give a trap_verdict in exactly one category:

  ASSERTS_FALSEHOOD    - the answer states something the CODE CONTRADICTS.
  OMITS_DEFAULT_CAVEAT - every statement is TRUE of a realization the answer explicitly NAMES,
                         but it fails to flag that this realization is NOT the configured default.
                         This is an incomplete truth, NOT a falsehood. If the answer names NO
                         realization while making the claim, that is ASSERTS_FALSEHOOD instead.
  CORRECT_AND_COMPLETE - states the code truth and handles the default-vs-non-default distinction,
                         or simply never makes a claim that needed the caveat.
  NOT_ELICITED         - never addresses the subject matter at all.

STEP 3 - THE UN-ANCHORED CHECK. This is not optional and is weighted equally with step 2.
Independently of the claim above, list in \`other_falsehoods\` EVERY other assertion the answer
makes that the code contradicts. Check especially:
  - realization names, module directory names, file paths and GAMS identifiers that DO NOT EXIST;
  - cited line numbers that do not contain what is claimed;
  - reported grep/search results that are wrong.
Verify each against the source before listing it. An answer can be CORRECT_AND_COMPLETE on the
trap claim while fabricating elsewhere - that combination is expected and must be reported.
If an answer makes no other false claim, return an empty list. Do not invent findings to fill it.

Rules: judge ONLY against the code, never against your recollection of MAgPIE and never against
any documentation you find. Quote deciding sentences verbatim. The answers are in an arbitrary
order that carries no information - do not speculate about which condition produced which answer.
(grader ${seed})

Return the schema: one verdict per answer label present in the batch.`
}

function adjPrompt(trap, truth, labels) {
  return `You are adjudicating a disagreement between two independent graders of MAgPIE answers.

STEP 0 - find the repository root (contains BOTH \`modules/\` and \`.regrade/\`) and read
\`.regrade/batch_${trap}.md\`. If you cannot read it, STOP and say so in code_truth_check rather
than substituting anything.

STEP 1 - verify this code-truth premise yourself against the GAMS source; disagree if warranted:
  ${truth}

STEP 2 - the two graders disagreed on exactly these answers: ${labels.join(', ')}.
Grade ONLY those, into one of:
  ASSERTS_FALSEHOOD / OMITS_DEFAULT_CAVEAT / CORRECT_AND_COMPLETE / NOT_ELICITED
(definitions: a falsehood is contradicted by the code; OMITS_DEFAULT_CAVEAT means every statement
is true of a realization the answer explicitly NAMES but it fails to flag that realization is not
the default; if no realization is named while making the claim, it is ASSERTS_FALSEHOOD.)

You have not been told what either grader said. Decide from the answer text and the source alone.
Also fill \`other_falsehoods\` for these answers, per the same rule: any OTHER assertion the code
contradicts, verified against the source.

Return the schema, one verdict per adjudicated label.`
}

const norm = (l) => String(l == null ? '' : l).replace(/^\s*ANSWER\s+/i, '').trim()

phase('Grade')
const results = await pipeline(
  TRAPS,
  // stage 1: N independent graders for this trap group
  (trap) => parallel(Array.from({ length: N_GRADERS }, (_, i) => () =>
    agent(gradePrompt(trap, TRUTH[trap] || '(none supplied - derive it yourself from the source)', i + 1), {
      label: `grade:${trap}:g${i + 1}`,
      phase: 'Grade',
      model: 'opus',
      schema: SCHEMA,
    }).catch(() => null)
  )).then((gs) => ({ trap, graders: gs.filter(Boolean) })),

  // stage 2: adjudicate only where the graders disagree
  async ({ trap, graders }) => {
    if (graders.length < 2) return { trap, graders, adjudicated: null, disagreed: [] }
    const byLabel = {}
    for (const g of graders) {
      for (const v of g.verdicts || []) {
        const L = norm(v.label)
        ;(byLabel[L] = byLabel[L] || []).push(v.trap_verdict)
      }
    }
    const disagreed = Object.keys(byLabel)
      .filter((L) => byLabel[L].length >= 2 && new Set(byLabel[L]).size > 1)
      .sort()
    if (disagreed.length === 0) return { trap, graders, adjudicated: null, disagreed }
    const adj = await agent(
      adjPrompt(trap, TRUTH[trap] || '(none supplied - derive it yourself)', disagreed),
      { label: `adj:${trap}`, phase: 'Adjudicate', model: 'opus', schema: SCHEMA }
    ).catch(() => null)
    return { trap, graders, adjudicated: adj, disagreed }
  }
)

return { results: results.filter(Boolean) }
