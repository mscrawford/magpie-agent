export const meta = {
  name: 'magpie-phase1a-propagation',
  description: 'Phase 1A: does a corpus error reach the user answer, and do the verifiers.md MANDATEs change that? 2x2 (naive|trigger phrasing) x (real|placebo verifiers.md) over 8 traps.',
  phases: [
    { title: 'Answer', detail: '8 traps x 4 cells, Sonnet magpie-helper answerers' },
    { title: 'Grade', detail: '1 Opus grader per trap, blinded to arm, sees all 4 answers' },
  ],
}

// ---------------------------------------------------------------------------
// Cells. `arm` selects which arena the answerer is pointed at; `phrasing`
// selects which of the two authored questions it is asked.
//   C1 naive   + real     - mimics reality (no trigger keyword -> no MANDATE load)
//   C2 naive   + placebo  - control for the control
//   C3 trigger + real     - MANDATEs actually load
//   C4 trigger + placebo  - isolates rule TEXT from trigger-y phrasing
// ---------------------------------------------------------------------------
const CELLS = [
  { id: 'C1', arm: 'real',    phrasing: 'naive' },
  { id: 'C2', arm: 'placebo', phrasing: 'naive' },
  { id: 'C3', arm: 'real',    phrasing: 'trigger' },
  { id: 'C4', arm: 'placebo', phrasing: 'trigger' },
]

// args arrives as a JSON-encoded STRING from the harness -> parse it.
// (Same pattern, and same comment, as audit/tools/doc_audit_round.workflow.js:23.)
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const REP = A.rep || 1
// Traps are inlined so a replicate needs only {rep: N} and the run is reproducible
// from this file alone. Every code_truth below was re-derived by hand against the
// mirrored GAMS source before it was written down; see audit/arena_1a_prereg.md.
const DEFAULT_TRAPS = [
  { id: 'T1', class: 'set_member_label', doc: 'modules/module_60.md:59',
    doc_claim: "'Variable demand for bioenergy grasses (betr) and trees (begr)' - betr and begr are swapped.",
    code_truth: "betr = bioenergy TREE, begr = bioenergy GRASS. Verified: modules/30_croparea/simple_apr24/equations.gms:17 says 'bioenergy tree (betr)'; config/default.cfg:931 says 'bioenergy trees (betr)'. The same doc is CORRECT at :96 and :126.",
    q_naive: "I'm looking at MAgPIE's bioenergy sector. The model seems to distinguish two kinds of dedicated second-generation bioenergy crops. What are the two crop types called in the model, and what does each one actually represent?",
    q_trigger: 'What are the exact set members of `kbe60` in MAgPIE, and what does each of `betr` and `begr` denote where it is used as a variable name index in `vm_area`?' },
  { id: 'T2', class: 'phantom_identifier', doc: 'cross_module/water_balance_conservation.md:71',
    doc_claim: 'A GAMS-fenced code quote presents `f42_watdem_ineldo(t,j,ssp_scenario,watdem_ineldo,"withdrawal")`. The symbol `ssp_scenario` exists nowhere in modules/, core/ or config/.',
    code_truth: 'The real switch is `s42_watdem_nonagr_scenario`, declared at modules/42_water_demand/all_sectors_aug13/input.gms:9 with default / 2 /, confirmed at the cfg layer (config/default.cfg:1357). There is no `ssp_scenario` symbol anywhere in the model.',
    q_naive: 'How does MAgPIE decide how much water households and industry withdraw, and is that assumption something a user can change between scenarios?',
    q_trigger: 'Which switch selects the non-agricultural water demand scenario in module 42 - what is the exact variable name, and its default value?' },
  { id: 'T3', class: 'capability_vs_default', doc: 'cross_module/water_balance_conservation.md:101,534,552',
    doc_claim: "Section 7.4 presents the EFP ramp-up as model behaviour ('EFP policy ramps up 2025-2040 (linear increase from 0% to 100%)', '2040: Ecosystem demand = 20% (full EFP enforcement)'), and the Policy Modes block cites input.gms:122 but never states which mode is the default.",
    code_truth: '$setglobal c42_env_flow_policy off (modules/42_water_demand/all_sectors_aug13/input.gms:122) AND config/default.cfg:1373 cfg$gms$c42_env_flow_policy <- "off"  # def = "off". So in a DEFAULT run EFP is OFF: no ramp occurs and only the base protection applies. An answer describing the 2025-2040 ramp as what happens in a default run is asserting the falsehood.',
    q_naive: 'If I run MAgPIE out of the box without changing any settings, does the model hold back river water to protect ecosystems? Does that change over the century?',
    q_trigger: 'What is the default value of `c42_env_flow_policy`, and what does environmental flow protection do in a default MAgPIE run?' },
  { id: 'T4', class: 'mechanism', doc: 'modules/module_29_notes.md:11',
    doc_claim: "'Fallow land: The `simple_apr24` realization includes fallow land dynamics. Fallow area appears as a separate land pool within cropland.' - this is inverted.",
    code_truth: 'detail_apr24 is the DEFAULT cropland realization (config/default.cfg:814) and it MODELS fallow: vm_fallow enters q29_cropland (modules/29_cropland/detail_apr24/equations.gms:12) with a minimum-fallow penalty q29_fallow_min (:66-68). simple_apr24 FIXES fallow to zero: vm_fallow.fx(j)=0 (modules/29_cropland/simple_apr24/preloop.gms:9).',
    q_naive: 'Does MAgPIE keep track of fallow land, or does it assume all cropland is in production every year?',
    q_trigger: 'Which cropland realization represents fallow land through `vm_fallow`, which one fixes it to zero, and which is the default realization?' },
  { id: 'T5', class: 'attribution_role', doc: 'modules/module_40.md:53',
    doc_claim: 'Lists Module 18 (residues) and Module 30 (croparea) among the modules that CONSUME vm_prod.',
    code_truth: "Module 30 is the PRODUCER of vm_prod, not a consumer: vm_prod appears only on the LHS of q30_prod (modules/30_croparea/simple_apr24/equations.gms:15, 'vm_prod(j2,kcr) =e= sum(w, vm_area*vm_yld)'). Module 18's DEFAULT realization is flexreg_apr16 (config/default.cfg:625), which reads REGIONAL vm_prod_reg (equations.gms:18,27,73,81), not cellular vm_prod; the doc cited the non-default flexcluster_jul23. The genuine consumers are M31 (31_past/endo_jun13/equations.gms:32), M38 (:35,:43), M42 (:14), M71 (foragebased_jul23/equations.gms:23) and M73 (:26).",
    q_naive: 'Once MAgPIE has determined how much of each crop a grid cell produces, which other parts of the model use that quantity?',
    q_trigger: 'Which modules consume the interface variable `vm_prod` in MAgPIE?' },
  { id: 'T6', class: 'attribution_role', doc: 'modules/module_58.md:35-36',
    doc_claim: "Attributes vm_land_forestry / vm_landexpansion_forestry / vm_landreduction_forestry to 10_land, and states 'Dependencies: 5 total'.",
    code_truth: 'Those three variables are declared in modules/32_forestry/dynamic_may24/declarations.gms:74-76 (module 32 Forestry), NOT in 10_land. Module 58 reads them at modules/58_peatland/v2/equations.gms:23,28,31. Module 10 supplies only vm_land, vm_landexpansion, vm_landreduction. The correct dependency count is 6, not 5.',
    q_naive: 'Module 58 deals with peatlands. Which other parts of the model does it take its inputs from - and in particular, where does its information about forestry land come from?',
    q_trigger: 'Which module declares `vm_land_forestry`, and which modules does module 58 take as inputs?' },
  { id: 'T7', class: 'citation', doc: 'modules/module_80.md:667',
    doc_claim: "Cites `magpie.solprint` as '(solve.gms:16, 174)' - a bare basename with no realization.",
    code_truth: "Module 80 has FOUR realizations and magpie.solprint appears in ALL FOUR solve.gms files at DIFFERENT lines: lp_nlp_apr17 @16,174 | nlp_apr17 @18,80 | nlp_ipopt @54,84 | nlp_par @20. So a bare 'solve.gms:16, 174' cannot be resolved; those particular line numbers exist only in lp_nlp_apr17, which is NOT the default. The default realization is nlp_apr17 (config/default.cfg:2303), and module_80.md itself says so at :9-10. PROPAGATED = repeats a bare solve.gms citation with no realization qualifier anywhere. CORRECT = names a specific realization's solve.gms. Naming the default nlp_apr17 (solprint at :18,:80) is CORRECT, as is correctly identifying :16/:174 as lp_nlp_apr17.",
    q_naive: "Where in MAgPIE's model code is the solver's print/output verbosity for the optimization step configured?",
    q_trigger: 'In module 80, where is `magpie.solprint` set, and what is its default value?' },
  { id: 'T8', class: 'citation', doc: 'modules/module_80.md:814-816',
    doc_claim: "Cites `s80_secondsolve` behaviour as '(solve.gms:66, 77, 131, 140, 190, etc.)' and '(solve.gms:62-63)' - bare basenames with no realization.",
    code_truth: "s80_secondsolve appears in solve.gms of lp_nlp_apr17 @66,77,131,140,150,159,190,197 | nlp_apr17 @36,71 | nlp_par @84 | nlp_ipopt: absent entirely. The doc's line numbers therefore exist only in lp_nlp_apr17, the NON-default realization (default is nlp_apr17, config/default.cfg:2303). Default value s80_secondsolve = 0, confirmed at BOTH layers (input.gms:11 and config/default.cfg:2324). PROPAGATED = repeats a bare solve.gms citation with no realization qualifier anywhere. CORRECT = names a specific realization's solve.gms.",
    q_naive: 'MAgPIE can apparently run each solve statement twice in a row. Where is that behaviour implemented, and what is it for?',
    q_trigger: 'Where is `s80_secondsolve` implemented in module 80, and what is its default value?' },
]
// Rep 1 measured 0/31 propagation in every cell -- a FLOOR, not a null: with the
// baseline at zero, C3-C4 cannot be non-zero, so the MANDATE question was never
// actually put. Answerers averaged 28.8 tool uses and verified essentially
// everything against code.
//
// EFFORT is the range-restoring knob, and it is deliberately the ONLY thing that
// changes: same arenas, same traps, same prompt, same controls, so the delta is
// attributable to effort alone. Lowering it makes verification a choice rather
// than a reflex, which is the only regime in which a grep-procedure MANDATE has
// room to change an outcome. Prompt-level de-priming was rejected as the knob
// because AGENT.md is genuinely auto-loaded in a real session -- stripping it
// would model a product that does not exist, and would also disable the canary.
const EFFORT = A.effort || null                       // null => inherit session default
const DROP = new Set(A.drop || [])                    // pre-registered drop order: T7,T8 first
const TRAPS = (A.traps || DEFAULT_TRAPS).filter((t) => !DROP.has(t.id))

// VACUITY GUARD. The first invocation of this script returned {"results":[]} in
// 49 ms having spawned ZERO agents, because args was a string and TRAPS was []. A
// workflow that measures nothing must not report as a completed run - that is the
// same failure shape as the arena that injected 0 of 5 hunks and still built.
if (!Array.isArray(TRAPS) || TRAPS.length === 0) {
  throw new Error(`Phase 1A: TRAPS is empty (typeof args=${typeof args}). Refusing to `
    + `run a workflow that would measure nothing.`)
}
log(`rep${REP}: ${TRAPS.length} traps x ${CELLS.length} cells = ${TRAPS.length * CELLS.length} answerers`)

// Relative paths only - never an absolute working directory in a subagent prompt.
const corpusOf = (arm) => `.arena/${arm}/magpie/magpie-agent`
const gamsOf   = (arm) => `.arena/${arm}/magpie`

// DOCS_ONLY removes the GAMS mirror from the answerer's world. Rep 1 (normal
// effort + code) propagated 0%, rep 2 (low effort + code) 17%; this is the third
// point on a dose-response over VERIFICATION OPPORTUNITY, and it is the regime in
// which doc accuracy is actually load-bearing. It is also the flywheel's own
// long-standing answerer shape (doc_audit_round.workflow.js: "you read only the
// AI docs"), so it is a realistic product mode, not a strawman.
const DOCS_ONLY = A.docs_only === true

function answerPrompt(trap, cell) {
  const q = cell.phrasing === 'naive' ? trap.q_naive : trap.q_trigger
  if (DOCS_ONLY) {
    return `You are the magpie-agent, answering a user's question about the MAgPIE land-use model.

Your documentation corpus root is \`${corpusOf(cell.arm)}\` (relative to your working directory).
Read \`AGENT.md\` at that root FIRST and follow its instructions - it is the source of truth for
how you answer. A magpie-agent documentation tree may also exist elsewhere on this machine;
ignore it. \`${corpusOf(cell.arm)}\` is the ONLY corpus you may use.

Answer from the AI documentation only. The raw GAMS model source is NOT available to you in
this mode: do not read, grep or open any \`.gms\` file, \`config/\`, or \`core/\`. If the
documentation does not settle the question, say so rather than guessing.

When you are done, write your complete answer to \`.arena/out/rep${REP}_${trap.id}_${cell.id}.md\`
and ALSO return it as your final text.

Answer the user's question below the way you normally would.

QUESTION: ${q}`
  }
  return `You are the magpie-agent, answering a user's question about the MAgPIE land-use model.

Your documentation corpus root is \`${corpusOf(cell.arm)}\` (relative to your working directory).
Read \`AGENT.md\` at that root FIRST and follow its instructions - it is the source of truth for
how you answer. A magpie-agent documentation tree may also exist elsewhere on this machine;
ignore it. \`${corpusOf(cell.arm)}\` is the ONLY corpus you may use.

The MAgPIE GAMS source, \`config/\` and \`core/\` are mirrored at \`${gamsOf(cell.arm)}\`
(also relative to your working directory). Documentation citations of the form
\`modules/NN_name/realization/file.gms\` resolve under that root. You have full tool access
and may read and grep both trees.

Work ONLY inside those two trees. Do not read, list or grep any path outside them.

When you are done, write your complete answer to \`.arena/out/rep${REP}_${trap.id}_${cell.id}.md\`
and ALSO return it as your final text.

Answer the user's question below the way you normally would.

QUESTION: ${q}`
}

// Deterministic per-trap permutation. Math.random() is unavailable in workflow
// scripts (it would break resume), and a fixed rotation is enough to keep the
// grader from learning arm identity from position.
function shuffleForTrap(items, i) {
  const k = i % items.length
  return items.slice(k).concat(items.slice(0, k))
}

const GRADE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['label', 'outcome', 'evidence'],
        properties: {
          label: { type: 'string' },
          outcome: { type: 'string', enum: ['PROPAGATED', 'CORRECT', 'ABSTAINED', 'NOT_ELICITED'] },
          evidence: { type: 'string', description: 'verbatim quote from the answer that decides the verdict, <=300 chars' },
          note: { type: 'string' },
          used_outside_corpus: { type: 'boolean', description: 'true if the answer shows signs of having read a corpus other than the one described (e.g. it quotes a corrected version of the claim that the given corpus does not contain)' },
        },
      },
    },
  },
}

function gradePrompt(trap, labelled) {
  const blocks = labelled.map(([lab, txt]) =>
    `### ANSWER ${lab}\n${(txt || '(no answer returned)').slice(0, 9000)}`).join('\n\n')
  return `You are grading answers in a documentation-quality experiment. Be strict and literal.

A documentation corpus contains a known DEFECT. Several assistants were each asked a user-style
question whose correct answer is determined by the MAgPIE GAMS source code. Your job is to
classify what each assistant's answer DID with the defective claim.

THE DEFECT (what the documentation says, and it is WRONG):
${trap.doc} - ${trap.doc_claim}

THE CODE TRUTH (what the source actually says):
${trap.code_truth}

CLASSIFY each answer into EXACTLY ONE outcome:
- PROPAGATED  - the answer asserts the documentation's wrong claim (or repeats the unresolvable
                citation) as fact. This includes asserting it implicitly, e.g. describing a
                capability as active when the code default disables it.
- CORRECT     - the answer asserts the code truth.
- ABSTAINED   - the answer engages the topic but hedges, flags uncertainty, notes a conflict
                between sources, or explicitly declines to commit. Abstention is a DISTINCT and
                GOOD outcome - never score it as CORRECT.
- NOT_ELICITED- the answer never touches the claim at all, so the question did not reach the
                defect. This is an instrument outcome, not a performance outcome.

Rules:
- Judge ONLY against the code truth above. Do not use your own recollection of MAgPIE.
- An answer that states BOTH the wrong claim and the right one, without resolving which holds,
  is ABSTAINED, not CORRECT.
- Quote the deciding sentence verbatim in "evidence". If you cannot find one, the outcome is
  almost certainly NOT_ELICITED.
- Set used_outside_corpus=true ONLY if an answer quotes a CORRECTED form of the claim that the
  defective corpus could not have contained. That means the assistant read the wrong corpus and
  its data point must be discarded.
- The answers are in an arbitrary order that carries no information. Do not speculate about
  which condition produced which answer.

${blocks}

Return the schema. One verdict per answer, using the labels exactly as given.`
}

phase('Answer')
const results = await pipeline(
  TRAPS,
  // stage 1: four answerers for this trap, one per cell
  (trap, _orig, i) => parallel(CELLS.map((cell) => () =>
    agent(answerPrompt(trap, cell), Object.assign({
      label: `ans:${trap.id}:${cell.id}`,
      phase: 'Answer',
      model: 'sonnet',
      agentType: 'magpie-helper',
    }, EFFORT ? { effort: EFFORT } : {}))
      .then((txt) => [cell.id, txt]).catch(() => [cell.id, null])
  )),
  // stage 2: one blinded grader for this trap, sees all four
  async (answers, trap, i) => {
    const byCell = Object.fromEntries(answers.filter(Boolean))
    const order = shuffleForTrap(CELLS.map((c) => c.id), i)
    const LABELS = ['A', 'B', 'C', 'D']
    const labelled = order.map((cid, n) => [LABELS[n], byCell[cid]])
    const map = Object.fromEntries(order.map((cid, n) => [LABELS[n], cid]))
    const g = await agent(gradePrompt(trap, labelled), {
      label: `grade:${trap.id}`,
      phase: 'Grade',
      model: 'opus',
      schema: GRADE_SCHEMA,
    })
    const scored = {}
    // Normalise the label. In rep 1, three of eight graders returned "ANSWER A"
    // rather than "A" -- echoing the `### ANSWER A` block headers in this very
    // prompt -- and 12 of 32 verdicts silently became MISSING. The first scoring
    // pass then reported a rate over 5 traps while presenting as a run over 8.
    const norm = (l) => String(l == null ? '' : l).replace(/^\s*ANSWER\s+/i, '').trim()
    for (const v of (g && g.verdicts) || []) {
      const cid = map[norm(v.label)]
      if (cid) scored[cid] = { outcome: v.outcome, evidence: (v.evidence || '').slice(0, 300), note: v.note || '', used_outside_corpus: !!v.used_outside_corpus }
    }
    const missing = CELLS.map((c) => c.id).filter((c) => !byCell[c])
    return { trap: trap.id, class: trap.class, label_map: map, scored, answerer_died: missing }
  }
)

const out = results.filter(Boolean)
log(`graded ${out.length}/${TRAPS.length} traps`)
return { rep: REP, cells: CELLS, results: out }
