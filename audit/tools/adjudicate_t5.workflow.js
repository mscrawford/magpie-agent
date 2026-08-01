export const meta = {
  name: 'magpie-t5-adjudication',
  description: 'Independent 3-way blind re-adjudication of the T5/T6 answers that carry the entire Phase 1A propagation signal.',
  phases: [{ title: 'Adjudicate', detail: '3 independent adjudicators, same 21 blind answers' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const N = A.n || 3

const SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdicts', 'code_truth_check'],
  properties: {
    code_truth_check: { type: 'string', description: 'Did you confirm the two code-truth premises against the GAMS source? State agreement or disagreement explicitly.' },
    verdicts: { type: 'array', items: {
      type: 'object', additionalProperties: false, required: ['label', 'category', 'quote'],
      properties: {
        label: { type: 'string' },
        category: { type: 'string', enum: ['ASSERTS_FALSEHOOD', 'OMITS_DEFAULT_CAVEAT', 'CORRECT_AND_COMPLETE', 'NOT_ELICITED'] },
        quote: { type: 'string', description: 'verbatim sentence from the answer that decides it, <=300 chars' },
        note: { type: 'string' },
      } } },
  },
}

const PROMPT = [
'You are adjudicating assistant answers about the MAgPIE land-use model. Be strict, literal, and independent.',
'',
'STEP 0 - locate your inputs, and STOP if you cannot.',
'Find the repository root: the directory containing BOTH a `magpie-agent/` directory AND a `modules/` directory.',
'Read `.adjudication/batch.md` relative to that root. If you cannot read it, do NOT guess or substitute anything -',
'return immediately with code_truth_check explaining what you could not reach. (A previous run had agents silently',
'fall back to the wrong directory; that is the failure this step exists to prevent.)',
'',
'STEP 1 - confirm the two code-truth premises YOURSELF against the GAMS source under `modules/`.',
'Do not take them on faith; if you disagree with either, say so in code_truth_check and grade accordingly.',
'',
'  PREMISE 1 (about the cell-level variable `vm_prod`):',
'   - Module 30 (croparea) PRODUCES vm_prod. It appears only on the LHS of q30_prod',
'     (30_croparea/simple_apr24/equations.gms:15). It is not a consumer.',
'   - Module 18 (residues) has TWO realizations. The DEFAULT is flexreg_apr16 (config/default.cfg:625),',
'     which reads REGIONAL vm_prod_reg, NOT cell-level vm_prod. The non-default flexcluster_jul23 does read',
'     cell-level vm_prod (equations.gms:18).',
'   - Genuine consumers of cell-level vm_prod: modules 31, 38, 42, 71, 73.',
'',
'  PREMISE 2 (about forestry land in module 58 peatland):',
'   - vm_land_forestry / vm_landexpansion_forestry / vm_landreduction_forestry are DECLARED in',
'     32_forestry/dynamic_may24/declarations.gms:74-76 - module 32, NOT module 10.',
'   - Module 10 supplies only vm_land, vm_landexpansion, vm_landreduction.',
'   - Module 58 reads the forestry variables at 58_peatland/v2/equations.gms:23,28,31.',
'',
'STEP 2 - classify EVERY answer in the batch into EXACTLY ONE category.',
'This distinction is the whole point of the exercise, so apply it mechanically:',
'',
'  ASSERTS_FALSEHOOD    - the answer states something the CODE CONTRADICTS. Example shape: it says module 30',
'                         CONSUMES vm_prod, or that module 10 declares vm_land_forestry.',
'',
'  OMITS_DEFAULT_CAVEAT - every statement the answer makes is TRUE of a realization it explicitly NAMES, but it',
'                         fails to flag that the named realization is NOT the default. Example shape: it says',
'                         module 18 reads cell-level vm_prod and cites flexcluster_jul23 - true of that',
'                         realization - without noting the default realization does not.',
'                         This category is NOT a falsehood. It is an incomplete truth.',
'',
'  CORRECT_AND_COMPLETE - states the code truth AND handles the default-vs-non-default distinction, or simply',
'                         never makes a claim that needed the caveat.',
'',
'  NOT_ELICITED         - never addresses the subject matter at all.',
'',
'Rules: judge ONLY against the code, not against your recollection of MAgPIE and not against any documentation.',
'Quote the deciding sentence verbatim. If an answer both asserts a falsehood AND omits a caveat elsewhere,',
'ASSERTS_FALSEHOOD wins. If an answer names NO realization while claiming module 18 reads cell-level vm_prod,',
'that is ASSERTS_FALSEHOOD, not OMITS_DEFAULT_CAVEAT - the caveat category requires the realization be named.',
'The answers are in arbitrary order and their order carries no information. Do not speculate about where they',
'came from or which condition produced them.',
'',
'Return the schema: one verdict per answer label present in the batch.',
].join('\n')

phase('Adjudicate')
const out = await parallel(Array.from({ length: N }, (_, i) => () =>
  agent(PROMPT, { label: `adjudicator-${i + 1}`, phase: 'Adjudicate', model: 'opus', schema: SCHEMA })
    .catch(() => null)))
return { adjudicators: out.filter(Boolean) }
