export const meta = {
  name: 'magpie-doc-audit-round',
  description: 'One hybrid doc-improvement round for magpie-agent: per-doc Opus full-doc audit + (Sonnet answer -> Opus question-audit), then Sonnet gated fixes, then syntactic gate. Disk-first; returns a compact synthesis.',
  phases: [
    { title: 'Audit' },
    { title: 'Verify' },
    { title: 'Fix' },
    { title: 'Gate' },
  ],
}

// ---- args (passed at invocation) ----
// args.round       : int
// args.mode        : 'hybrid' (doc-audit + question-probe) | 'doccentric' (doc-audit only)
// args.verify      : bool -- if true, an adversarial verifier tries to REFUTE each confirmed
//                    consumer/populator-set finding (grepping BOTH NAME( and NAME.) before the fixer applies it
// args.docs        : [{ path, label, klass, probe_question?, baseline_advisory? }]
//                    klass in: module | cross_module | core | reference | helper | magpie4
//                    probe_question required when mode='hybrid'
// args.anchors     : [{ id, question, ground_truth, expected }]
// args.paths       : { agentDir, parent, dev } -- machine-local checkout roots (absolute).
//                    REQUIRED on any clone but this one; defaults are placeholders.
// args arrives as a JSON-encoded STRING from the harness -> parse it
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const R = A.round
const MODE = A.mode || 'hybrid'
const VERIFY = A.verify === true   // adversarial consumer/populator-set refute pass before fixing
const DOCS = A.docs || []
const ANCHORS = A.anchors || []

// Machine-local checkout roots. Pass via args.paths = {agentDir, parent, dev} to run on
// your own clone; the agentDir/parent defaults below are placeholders and MUST be overridden.
const P = A.paths || {}
const AGENT_DIR = P.agentDir || '/path/to/magpie/magpie-agent'
const DEV = P.dev || '/tmp/magpie_develop_ro'   // detached origin/develop worktree (verification truth)
const PARENT = P.parent || '/path/to/magpie'
const ARC = AGENT_DIR + '/audit/archive/rounds'
const RUBRIC = AGENT_DIR + '/audit/flywheel_rubric.md'
const VERIFIERS = AGENT_DIR + '/agent/helpers/verifiers.md'

// ---------- shared guard text ----------
const GREP_GUARD = `CRITICAL grep rules (a verified false-positive source in this repo):
  - A bare 'grep -r' can SILENTLY return empty even when matches exist. Never trust it alone.
  - 'find ... -exec grep {} +' returns EXIT 1 when the final batch has no match, which ABORTS any chained (&&, ';', compound) command and silently TRUNCATES output. Run each grep probe as its OWN standalone command (or append '|| true'); never chain probes so one nonzero exit kills the rest.
  - rg (ripgrep) IS available here; prefer it: rg -n 'PATTERN' ${DEV}/modules/   (rg also exits 1 on no-match -> isolate it).
  - ALWAYS cross-check a zero/absence result with a SECOND method, AND run a POSITIVE CONTROL: grep a known-present sibling token (an adjacent parameter/variable) to prove the search works in that dir before concluding 'X is absent'.
  - Co-located names: a module number cited for an ADJACENT parameter on the same doc line is NOT a consumer of THIS parameter (this exact pattern produced a false advisory on module_52.md:291).
  - SOLUTION-LEVEL reads: a module can consume a variable via its attributes (NAME.l/.lo/.up/.fx/.m) in presolve/postsolve, which a 'NAME(' grep MISSES. Always grep BOTH 'NAME(' AND 'NAME.' (e.g. rg 'vm_area\\.') before concluding a module does/does not consume NAME (R33 near-miss: module 32 reads vm_area.l/.lo in presolve.gms:17 for afforestation potential - invisible to a 'vm_area(' grep, which nearly deleted a correct consumer listing as a phantom).
  - DATA-FLOW DIRECTION (serial vs parallel): for any "M_A hands off / forwards / routes X to M_B", "M_B receives X from M_A", or "X flows A->B->C" claim, open BOTH endpoints - confirm whether M_B reads M_A's OUTPUT variable (genuine serial hand-off) OR M_A and M_B both read the SAME shared interface variable INDEPENDENTLY (PARALLEL readers, NOT a hand-off). DEFAULT to parallel-not-serial until the code proves M_B reads M_A's output; a single-file read cannot settle direction (R51: the soilc 'M52 routes to M56' claim was wrong - M56 reads vm_carbon_stock DIRECTLY in q56_emis_pricing_co2, parallel to M52. See verifiers.md MANDATE 21).
  - FIND THE PRODUCER before calling any input/parameter/data column MISSING, STALE, UNPOPULATED, or SILENTLY ZERO. A file under modules/*/input/ is NOT necessarily an input you were handed: *.cs* files are GITIGNORED and several are RUN-TIME PRODUCTS of the R layer (scripts/). Reading the file's current bytes and its git history tells you what it IS ON DISK NOW, not what it WILL BE when the model actually runs. Before any such claim: (a) grep the WHOLE repo root for the switch name AND the filename - rg -n '<switch>' ${PARENT} - explicitly including scripts/, config/ and the R (.R) layer, NOT just modules/*.gms; (b) read the accused commit's NON-.gms files (git show --stat). The GAMS layer is the CONSUMER; a consumer-only investigation cannot see the producer. R53's Critical came from exactly this: a false bug report against a colleague's merged feature (c32_aff_policy=ndcdelay "silently yields zero policy"), where every premise was TRUE (no GAMS branch; the column really was absent from the on-disk .cs3; GAMS really does zero-fill silently) but the conclusion was FALSE - scripts/start_functions.R REGENERATES that .cs3 at run start, and the guards refuting the claim had been added BY THE VERY COMMITS BEING ACCUSED. Every check came back green and the story got MORE compelling with each one, because the error was in the frame, not the checks.
A "module does NOT consume X" / "zero consumers" claim is the highest-risk false positive: confirm twice + positive control before calling a documented consumer a phantom (and before adding an 'omitted' consumer, confirm it truly references the variable, not a look-alike).`

const MANDATES = `Apply the verifiers.md MANDATEs (read ${VERIFIERS} if unsure), especially:
  - 13 interface-consumer grep (verify producer/consumer SETS against code, list every module);
  - 17 direct vs transitive consumer (a module that reads a var that reads X is NOT a direct consumer of X);
  - 16 citations: full path modules/NN_name/realization/file.gms:LINE, line numbers verified in CURRENT develop (post-merge), not from old diffs;
  - 8 realization-name verification (ls ${DEV}/modules/NN_*/ for the real dir names);
  - 3 default-parameter verification (grep the scalar/parameter default in code + config/default.cfg);
  - Distinguish DECLARED vs POPULATED vs READ for interface variables (the G2 carbon-stock distinction).`

function groundTruthClause(doc) {
  if (doc.klass === 'reference') {
    return `GROUND TRUTH: real MAgPIE code in the develop worktree ${DEV}. OFFLINE ROUND - NO WEB ACCESS: do NOT use WebFetch/WebSearch, and do NOT fetch gams.com (AGENT.md Core Principle 7 + core_docs/Tool_Usage_Patterns.md: the agent answers and audits from LOCAL sources only; a fetched page is neither version-pinned nor reproducible). Verify every MAgPIE-symbol / convention / example claim (identifier names, arities, file:line, which realization) against ${DEV}. For a claim about GAMS *language* semantics that local code cannot settle, do NOT guess from recall and do NOT fetch: put it in "deferred" with a one-line note. Note that pedagogical placeholder identifiers (vm_varname, pm_param1, ...) in the GAMS-teaching docs are DELIBERATE and are NOT bugs; a module-attributed example ("Module 17: ...") that cites a non-existent symbol IS a bug.`
  }
  if (doc.klass === 'magpie4') {
    return `GROUND TRUTH: the SHA-pinned magpie4 clone. Read ${AGENT_DIR}/project/version_pins.json for the pinned version+SHA, then verify claims against ${AGENT_DIR}/.cache/sources/magpie4/ (NOT the workspace clone). Cite version-pinned source paths.`
  }
  if (doc.klass === 'helper') {
    return `GROUND TRUTH: ${DEV} GAMS code + ${DEV}/config/default.cfg for scenario switches / realization behavior / defaults. Verify any cfg$gms$* default, switch value, or realization claim against config/default.cfg and the realization code.`
  }
  // module | cross_module | core
  return `GROUND TRUTH: MAgPIE code in the develop worktree ${DEV} (NEVER the working tree). For defaults/realizations also read ${DEV}/config/default.cfg. ${doc.klass === 'module' ? '' : 'This doc makes CROSS-MODULE claims (consumer/populator/dependency sets) -> whole-tree greps required; the grep guard below is load-bearing.'}`
}

// ---------- schemas ----------
const SEV = { type: 'string', enum: ['Critical', 'Major', 'Minor', 'Informational'] }
const DOC_AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['doc', 'claims_verified', 'bugs', 'deferred', 'report_file', 'summary'],
  properties: {
    doc: { type: 'string' },
    realization_checked: { type: 'string' },
    claims_verified: { type: 'integer' },
    bugs: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'severity', 'bug_class', 'doc_line', 'claim_in_doc', 'reality_in_code', 'file_evidence', 'verify_cmd', 'confirmed', 'proposed_fix'],
        properties: {
          id: { type: 'string' }, severity: SEV, bug_class: { type: 'string' },
          doc_line: { type: 'string', description: 'e.g. module_10.md:315' },
          claim_in_doc: { type: 'string' }, reality_in_code: { type: 'string' },
          file_evidence: { type: 'string', description: 'develop file:line' },
          verify_cmd: { type: 'string', description: 'exact command run, with its result' },
          confirmed: { type: 'boolean', description: 'true only if reproducible code evidence supports the fix' },
          proposed_fix: { type: 'string', description: 'exact replacement text or precise instruction' }
        }
      }
    },
    deferred: { type: 'array', items: { type: 'string' }, description: 'uncertain / non-code-verifiable -> NOT to be edited' },
    report_file: { type: 'string' },
    summary: { type: 'string', description: 'short, <=300 chars; full detail goes in report_file' }
  }
}
const QAUDIT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['doc', 'score', 'bugs_critical', 'bugs_major', 'bugs_minor', 'bugs_informational', 'doc_errors_latent', 'root_causes', 'notes', 'report_file'],
  properties: {
    doc: { type: 'string' }, score: { type: 'number' },
    bugs_critical: { type: 'integer' }, bugs_major: { type: 'integer' },
    bugs_minor: { type: 'integer' }, bugs_informational: { type: 'integer' },
    doc_errors_latent: { type: 'array', items: { type: 'string' }, description: 'load-bearing doc claims the answer relied on that are WRONG vs code (with file:line); fixed regardless of score' },
    root_causes: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string', description: 'short, <=300 chars' },
    report_file: { type: 'string' }
  }
}
const ANCHOR_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['id', 'score', 'drift_observed', 'notes', 'report_file'],
  properties: {
    id: { type: 'string' }, score: { type: 'number' },
    drift_observed: { type: 'boolean' }, notes: { type: 'string' }, report_file: { type: 'string' }
  }
}
const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['doc', 'verdicts', 'notes', 'report_file'],
  properties: {
    doc: { type: 'string' },
    verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['bug_id', 'class', 'citation_ok', 'verdict', 'corrected_set', 'evidence'],
        properties: {
          bug_id: { type: 'string', description: 'the audit bug id this verdict refers to' },
          class: { type: 'string', enum: ['consumer_set', 'producer_declaration', 'realization_structure', 'other'], description: 'what kind of claim the bug makes' },
          citation_ok: { type: 'boolean', description: 'MECHANICAL check: file_evidence (and any file:line in proposed_fix) exists, line is in range, AND the line contains the claimed token' },
          verdict: { type: 'string', enum: ['UPHELD', 'REFUTED', 'CORRECTED', 'CITATION_FAILED', 'NOT_REVIEWABLE'] },
          corrected_set: { type: 'string', description: 'if CORRECTED: the precise corrected claim/set to apply instead; else ""' },
          evidence: { type: 'string', description: 'exact cmds: the citation check (test -f / wc -l / read the line) AND, for attribution/realization claims, BOTH NAME( and NAME. greps + positive control, with results' }
        }
      }
    },
    notes: { type: 'string', description: 'short, <=300 chars' },
    report_file: { type: 'string' }
  }
}
const FIX_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['doc', 'files_fixed', 'n_edits', 'deferred', 'self_check_ok', 'notes'],
  properties: {
    doc: { type: 'string' },
    files_fixed: { type: 'array', items: { type: 'string' }, description: 'paths relative to magpie-agent/' },
    n_edits: { type: 'integer' },
    applied: { type: 'array', items: { type: 'object', additionalProperties: true } },
    deferred: { type: 'array', items: { type: 'string' } },
    self_check_ok: { type: 'boolean', description: 'each edit re-read and confirmed to have landed' },
    notes: { type: 'string' }
  }
}
const GATE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['clean', 'validate_consistency_errors', 'new_errors', 'reverted_files', 'notes'],
  properties: {
    clean: { type: 'boolean', description: 'validate_consistency.sh shows 0 errors after any reverts' },
    validate_consistency_errors: { type: 'integer' },
    new_errors: { type: 'array', items: { type: 'string' } },
    reverted_files: { type: 'array', items: { type: 'string' } },
    check_units_advisories: { type: 'integer' },
    check_consumer_advisories: { type: 'integer' },
    notes: { type: 'string' }
  }
}

// ---------- prompt builders ----------
function docAuditPrompt(doc) {
  return `You are an adversarial documentation auditor for the MAgPIE-agent (model: highest capability). Audit ONE whole doc against code and report every code-verifiable error.

TARGET DOC: ${AGENT_DIR}/${doc.path}
${groundTruthClause(doc)}

Read the rubric ${RUBRIC} for severity tiers (Critical/Major/Minor/Informational), the immutable anchor examples, and the bug-class list. Score-relevant: wrong consumer/populator SETS and inverted/false defaults are Critical-prone (R20 anchor); citation drift to materially-different content is Major.

${MANDATES}

${GREP_GUARD}

METHOD:
1. Read the full target doc. Enumerate its LOAD-BEARING, code-checkable claims: interface variable/parameter/equation names (vm_*, pm_*, q*, s*, etc.), file:line citations, consumer/populator/dependency SETS ("modules X,Y,Z consume vm_FOO"), realization names + which is default, parameter/scalar default values, set counts/ranges, and equation formulas. Skip pure prose/advice that is not code-checkable.
2. Verify EACH against ground truth. For consumer/dependency sets, enumerate the ACTUAL set from code (reliable grep, cross-checked) and diff against the doc's list — flag both phantom members (listed, no code ref) and omissions (in code, not listed).
3. For every discrepancy, record a bug: severity (rubric tier + which trigger), bug_class, exact doc quote + doc_line (e.g. ${doc.label}:NN), reality_in_code, file_evidence (develop file:line), the exact verify_cmd you ran WITH its result, confirmed (true ONLY with reproducible evidence), and a precise proposed_fix (exact replacement string or instruction).
4. Anything you cannot verify against code, or are unsure about -> put a one-line note in "deferred" (do NOT invent a bug, do NOT propose an edit). False positives are worse than misses here.
${doc.baseline_advisory ? `5. A pre-run advisory checker already flagged this doc: "${doc.baseline_advisory}". Verify it specifically (confirm or refute with code).` : ''}

OUTPUT:
- Write your FULL audit report (all claims checked, evidence, verdicts) to ${ARC}/round${R}_docaudits/${doc.label}.md
- Return the schema object. Keep "summary" under 300 chars (full detail lives in the report file). report_file = the path you wrote.`
}

function answerPrompt(doc) {
  return `You are answering an expert-level question about MAgPIE's inner workings, as a normal user of the magpie-agent would receive it.
Answer using ONLY the magpie-agent AI documentation files under ${AGENT_DIR} (modules/, core_docs/, cross_module/, reference/, agent/helpers/). Do NOT read raw GAMS source code or the develop worktree.
You have NO tools in this mode - you read only the AI docs. NEVER fabricate a command output (no "grep gives N", no invented counts or greps). If a doc states a count or value, cite it VERBATIM and do NOT recompute or override it; if the docs are silent or you are unsure, say so explicitly rather than inventing a number. (Guards the G4-class confabulation: an answerer once overrode the correct documented count of 106 with a fabricated "grep gives 101".)
Cite specific variable names (vm_*, pm_*), equation names (q*), realization names, and doc file references. End with the epistemic-hierarchy closing per AGENT.md.
Write your answer to ${ARC}/round${R}_answers/${doc.label}.md as well as returning it.

QUESTION: ${doc.probe_question}`
}

function qAuditPrompt(doc, answer) {
  return `You are the Opus auditor in the magpie-agent semantic-validation flywheel. Audit the ANSWER below against actual code, AND verify the load-bearing DOC claims the answer relied on.

QUESTION (anchored on ${doc.path}): ${doc.probe_question}

ANSWER TO AUDIT:
${(answer || '(no answer returned)').slice(0, 12000)}

${groundTruthClause(doc)}
Read the rubric ${RUBRIC} for the severity tiers, the per-question scoring formula (score = max(0, 10 - 4*crit - 2*major - 1*minor)), and the audit report format. ${MANDATES}
${GREP_GUARD}

Do BOTH:
(a) Score the ANSWER: find its bugs vs code, assign severities, compute the 0-10 score by the formula.
(b) LATENT doc bugs (rubric 1.5): even where the answer is CORRECT, if it relied on a load-bearing doc claim (interface var, equation, populator/consumer set, realization, default) that is WRONG vs code, record it in doc_errors_latent[] with the doc file:line and the code reality. These are fixed regardless of the answer's score (this is the blind spot that let G2 regress R22->R23->R26).
Classify each bug's root cause: doc_error | doc_error_answerer_beat_it | answerer_confabulation | answerer_style_or_framing | ambiguous.

OUTPUT: write the full audit to ${ARC}/round${R}_audits/${doc.label}.md; return the schema (notes <=300 chars).`
}

function verifyPrompt(doc, confirmedBugs) {
  return `You are an ADVERSARIAL VERIFIER (model: highest capability) in the magpie-agent doc flywheel. For EVERY confirmed bug below you FIRST run a MECHANICAL citation check; then you adversarially adjudicate the ATTRIBUTION and REALIZATION-STRUCTURE claims. Default to skepticism. Auditors over/under-count consumer AND producer sets, and they CONFABULATE non-default realization structure by pattern-completing the realization family (R33: an auditor claimed the bilateral22 trade realization had an active q21_cost_trade_feasibility equation that in fact only the sibling selfsuff_reduced defines - and a fresh agent independently reproduced the same error). These confabulations are CORRELATED across LLM agents, so your only reliable tool is MECHANICAL verification (test -f, wc -l, read the exact line, isolated grep + positive control) - NOT your own recall.

TARGET DOC: ${AGENT_DIR}/${doc.path}
${groundTruthClause(doc)}

${GREP_GUARD}

CONFIRMED BUGS TO VERIFY (from the auditor):
${JSON.stringify(confirmedBugs.map(b => ({ id: b.id, severity: b.severity, bug_class: b.bug_class, doc_line: b.doc_line, claim_in_doc: b.claim_in_doc, reality_in_code: b.reality_in_code, file_evidence: b.file_evidence, proposed_fix: b.proposed_fix })), null, 1)}

For EACH bug:
STEP A - MECHANICAL CITATION CHECK (ALL bugs, whatever the class): for the bug's file_evidence AND any modules/.../file.gms:LINE inside proposed_fix, run test -f <file> (exists?), wc -l <file> (is LINE in range?), and read that exact line (does it contain the claimed identifier/token?). If the file does NOT exist, the line is OUT OF RANGE, or the line does NOT contain the claimed content -> citation_ok=false, verdict=CITATION_FAILED (fabricated or mis-sourced; the fix is unsafe). Record the exact commands + results in evidence. This is the defense against the cross-realization confabulation class.
STEP B - CLASSIFY 'class': consumer_set (which modules CONSUME/read a var/param); producer_declaration (which module DECLARES it = appears in that module's declarations.gms, or POPULATES it = equation LHS / .fx / assignment; READ = equation RHS); realization_structure (a realization's equation COUNT / which equations it defines / a file's existence); other (formula/value/prose/count).
STEP C - ADJUDICATE (only if citation_ok=true):
  - consumer_set OR producer_declaration: INDEPENDENTLY re-derive the true set from ${DEV}. grep BOTH 'NAME(' AND 'NAME.' (.l/.lo/.up/.fx/.m) + positive control + co-located-name caveat + DIRECT-vs-TRANSITIVE (MANDATE 17); for producer/declaration explicitly grep declarations.gms (DECLARED) and equation LHS/.fx (POPULATED). Verdict UPHELD / REFUTED / CORRECTED (corrected_set = the precise claim to apply).
  - realization_structure: read the SPECIFIC realization's ACTUAL files (ls the dir; wc -l + read the cited equations.gms) and confirm eq count / eq presence / file existence MECHANICALLY against THAT realization, NEVER the sibling. Verdict UPHELD / REFUTED / CORRECTED.
  - other: verdict NOT_REVIEWABLE (citation already validated in Step A; pass to fixer unchanged).
Default to REFUTED / CORRECTED / CITATION_FAILED whenever the auditor's evidence does not reproduce. A false fix that looks freshly-verified is worse than leaving the doc unchanged.

OUTPUT: write your full verification to ${ARC}/round${R}_verify/${doc.label}.md; return the schema (notes <=300 chars).`
}

function anchorAnswerPrompt(a) {
  return `Answer using ONLY the magpie-agent AI documentation files under ${AGENT_DIR}. Do NOT read raw GAMS code. You have NO tools in this mode - NEVER fabricate a command output (no "grep gives N", no invented counts); if a doc states a count or value, cite it VERBATIM and do not recompute/override it; if unsure, say so. (Guards the G4-class confabulation.) Cite variable/equation/realization names and doc files. Write to ${ARC}/round${R}_answers/anchor_${a.id}.md and return the answer.

QUESTION (${a.id}): ${a.question}`
}

function anchorAuditPrompt(a, answer) {
  return `You are auditing a CALIBRATION-ANCHOR answer in the magpie-agent flywheel (${a.id}). This anchor recurs every round to detect drift.

QUESTION: ${a.question}
EXPECTED (ground truth summary): ${a.expected}
GROUND TRUTH SOURCE: ${a.ground_truth}  (verify against ${DEV}; for magpie4 anchors read ${AGENT_DIR}/project/version_pins.json + ${AGENT_DIR}/.cache/sources/magpie4/ and do NOT hardcode the version).

ANSWER TO AUDIT:
${(answer || '(no answer)').slice(0, 10000)}

Read ${RUBRIC}. ${GREP_GUARD}
Score 0-10 by the formula (max(0,10-4c-2M-1m)). Set drift_observed=true if the answer departs from the expected summary in any load-bearing way (this signals something near the anchor broke -> investigate before trusting this round's other fixes). Write full audit to ${ARC}/round${R}_audits/anchor_${a.id}.md; return schema (notes <=300 chars).`
}

function fixPrompt(r) {
  const da = r.docAudit || {}
  const confirmed = (da.bugs || []).filter(b => b && b.confirmed)
  const latent = (r.qProbe && r.qProbe.doc_errors_latent) || []
  const verdicts = (r.verify && r.verify.verdicts) || []
  const vmap = {}
  verdicts.forEach(v => { if (v && v.bug_id) vmap[v.bug_id] = v })
  const annotated = confirmed.map(b => {
    const v = vmap[b.id] || null
    return {
      bug_id: b.id, doc_line: b.doc_line, claim: b.claim_in_doc, reality: b.reality_in_code,
      evidence: b.file_evidence, proposed_fix: b.proposed_fix,
      adversarial_verdict: v ? v.verdict : (verdicts.length ? 'NOT_REVIEWED' : 'NO_VERIFY_PASS'),
      corrected_set: (v && v.verdict === 'CORRECTED') ? v.corrected_set : null
    }
  })
  return `You are a careful documentation FIXER (Sonnet). Apply ONLY verified fixes to ONE doc. Do not re-audit; the evidence is given.

TARGET DOC: ${AGENT_DIR}/${r.doc}

Each bug carries an adversarial_verdict from an independent verifier. OBEY it:
  - UPHELD / NOT_REVIEWABLE / NO_VERIFY_PASS -> apply proposed_fix as given (citation already mechanically validated where a verifier ran).
  - CORRECTED -> apply the corrected_set (verifier's corrected claim) INSTEAD of proposed_fix.
  - REFUTED -> DO NOT APPLY; add to deferred (the auditor was likely wrong; do not introduce the change).
  - CITATION_FAILED -> DO NOT APPLY; add to deferred (the cited file:line does not resolve to the claimed content -> the finding is unsafe, likely a fabricated/mis-sourced citation).
  - NOT_REVIEWED -> apply proposed_fix ONLY if it has concrete file:line/code evidence; else defer.

CONFIRMED DOC BUGS (with verdicts):
${JSON.stringify(annotated, null, 1)}

LATENT DOC ERRORS (from the question-probe; apply ONLY if the entry includes a concrete file:line/code reality — otherwise defer):
${JSON.stringify(latent, null, 1)}

RULES:
- Apply each applicable fix as a minimal, exact edit (correct the wrong name/citation/consumer-set/default; keep surrounding prose intact). Match MAgPIE doc conventions; no em-dashes; preserve any conceptual-form labels.
- After each edit, RE-READ the changed lines to confirm the edit landed and is internally consistent. Set self_check_ok accordingly.
- REFUTED items, and anything lacking concrete code evidence or ambiguous -> "deferred", do NOT edit.
- Do NOT touch other docs. Do NOT run git.
RETURN the schema: files_fixed (relative to magpie-agent/), n_edits, applied (doc_line+change), deferred, self_check_ok, notes.`
}

function gatePrompt(editedFiles) {
  return `You are the syntactic-gate runner for the magpie-agent docs. The baseline before this round was 0 errors (2 warnings).

1. From ${AGENT_DIR}, run: bash scripts/validate_consistency.sh 2>&1 | tail -25  (note the error count; warnings are OK).
2. Also run: python3 scripts/check_units.py 2>&1 | tail -8  and  python3 scripts/check_consumer_attribution.py 2>&1 | tail -8  (advisory counts only).
3. If validate_consistency.sh reports ANY errors (not warnings): they are new this round. Read the offending file:line from the report. The files edited this round were:
${JSON.stringify(editedFiles)}
   Fix the specific offending line if it is an obvious correction (e.g., a citation typo introduced by a fix). If you cannot trivially fix it, REVERT just that file with: git -C ${AGENT_DIR} checkout -- <relative_path>  (reverting one doc does not affect others), and record it in reverted_files. Re-run validate_consistency.sh until 0 errors.
4. Return the schema: clean (0 errors), validate_consistency_errors (final count), new_errors (descriptions), reverted_files, advisory counts, notes.
Do NOT commit. Do NOT push.`
}

// ---------- run ----------
log(`Round R${R} (${MODE}) starting: ${DOCS.length} docs, ${ANCHORS.length} anchors`)

phase('Audit')
const docResults = await parallel(DOCS.map((doc) => async () => {
  // failure-isolate each sub-agent: a question-probe error must NOT discard the doc-audit
  const daP = agent(docAuditPrompt(doc), { label: `docaudit:${doc.label}`, phase: 'Audit', schema: DOC_AUDIT_SCHEMA }).catch(() => null)
  const qaP = (MODE === 'hybrid')
    ? (async () => {
        try {
          const ans = await agent(answerPrompt(doc), { label: `answer:${doc.label}`, phase: 'Audit', model: 'sonnet', agentType: 'magpie-helper' })
          return await agent(qAuditPrompt(doc, ans), { label: `qaudit:${doc.label}`, phase: 'Audit', schema: QAUDIT_SCHEMA })
        } catch (e) { return null }
      })()
    : Promise.resolve(null)
  const [docAudit, qProbe] = await Promise.all([daP, qaP])
  // adversarial verify: independently try to REFUTE each confirmed consumer/populator-set finding before it is fixed
  let verify = null
  if (VERIFY && docAudit) {
    const conf = (docAudit.bugs || []).filter(b => b && b.confirmed)
    if (conf.length) {
      verify = await agent(verifyPrompt(doc, conf), { label: `verify:${doc.label}`, phase: 'Verify', schema: VERIFY_SCHEMA }).catch(() => null)
    }
  }
  return { doc: doc.path, label: doc.label, klass: doc.klass, docAudit, qProbe, verify }
}))

const anchorResults = await parallel(ANCHORS.map((a) => async () => {
  try {
    const ans = await agent(anchorAnswerPrompt(a), { label: `anchor-ans:${a.id}`, phase: 'Audit', model: 'sonnet', agentType: 'magpie-helper' })
    return await agent(anchorAuditPrompt(a, ans), { label: `anchor-aud:${a.id}`, phase: 'Audit', schema: ANCHOR_SCHEMA })
  } catch (e) { return null }
}))

// docs with confirmed doc bugs or evidenced latent errors -> fix
const toFix = docResults.filter(r => {
  const conf = ((r.docAudit || {}).bugs || []).filter(b => b && b.confirmed)
  const lat = (r.qProbe && r.qProbe.doc_errors_latent) || []
  return conf.length > 0 || lat.length > 0
})
log(`Audit done. ${toFix.length}/${DOCS.length} docs have confirmed doc bugs; ${docResults.filter(r=>!r.docAudit).length} dropped (null).`)

phase('Fix')
const fixes = await parallel(toFix.map((r) => async () => {
  const f = await agent(fixPrompt(r), { label: `fix:${r.label}`, phase: 'Fix', model: 'sonnet', schema: FIX_SCHEMA })
  return f
}))
const editedFiles = [...new Set(fixes.filter(Boolean).flatMap(f => f.files_fixed || []))]

phase('Gate')
const gate = await agent(gatePrompt(editedFiles), { label: 'gate', phase: 'Gate', schema: GATE_SCHEMA })

// ---------- compact synthesis (disk has full detail) ----------
function daCounts(b) {
  const a = (b || []).filter(Boolean)
  const by = (s) => a.filter(x => x.severity === s).length
  return { critical: by('Critical'), major: by('Major'), minor: by('Minor'), informational: by('Informational'), confirmed: a.filter(x => x.confirmed).length, total: a.length }
}
const perDoc = docResults.map(r => {
  const verdicts = (r.verify && r.verify.verdicts) || []
  return {
    label: r.label, klass: r.klass, doc: r.doc,
    dropped: !r.docAudit,
    doc_audit: r.docAudit ? { counts: daCounts(r.docAudit.bugs), deferred: r.docAudit.deferred || [], report_file: r.docAudit.report_file, summary: r.docAudit.summary } : null,
    q_probe: r.qProbe ? { score: r.qProbe.score, c: r.qProbe.bugs_critical, ma: r.qProbe.bugs_major, mi: r.qProbe.bugs_minor, info: r.qProbe.bugs_informational, latent: r.qProbe.doc_errors_latent || [], root_causes: r.qProbe.root_causes || [], notes: r.qProbe.notes, report_file: r.qProbe.report_file } : null,
    verify: r.verify ? {
      refuted: verdicts.filter(v => v && v.verdict === 'REFUTED').map(v => v.bug_id),
      corrected: verdicts.filter(v => v && v.verdict === 'CORRECTED').map(v => ({ bug_id: v.bug_id, corrected_set: v.corrected_set })),
      citation_failed: verdicts.filter(v => v && v.verdict === 'CITATION_FAILED').map(v => v.bug_id),
      upheld: verdicts.filter(v => v && v.verdict === 'UPHELD').length,
      attribution_reviewed: verdicts.filter(v => v && (v.class === 'consumer_set' || v.class === 'producer_declaration' || v.class === 'realization_structure')).length,
      report_file: r.verify.report_file, notes: r.verify.notes
    } : null
  }
})
const verifyAgg = {
  docs_verified: perDoc.filter(d => d.verify).length,
  refuted: perDoc.reduce((n, d) => n + (d.verify ? d.verify.refuted.length : 0), 0),
  corrected: perDoc.reduce((n, d) => n + (d.verify ? d.verify.corrected.length : 0), 0),
  citation_failed: perDoc.reduce((n, d) => n + (d.verify ? d.verify.citation_failed.length : 0), 0),
  upheld: perDoc.reduce((n, d) => n + (d.verify ? d.verify.upheld : 0), 0)
}
const qScores = perDoc.map(d => d.q_probe && d.q_probe.score).filter(s => typeof s === 'number')
const anchorScores = (anchorResults.filter(Boolean)).map(a => ({ id: a.id, score: a.score, drift: a.drift_observed, notes: a.notes }))
const mean_inputs = qScores.concat(anchorScores.map(a => a.score))
const mean_score = mean_inputs.length ? +(mean_inputs.reduce((x, y) => x + y, 0) / mean_inputs.length).toFixed(2) : null

return {
  round: R, mode: MODE, verify: VERIFY,
  n_docs: DOCS.length,
  dropped: perDoc.filter(d => d.dropped).map(d => d.label),
  per_doc: perDoc,
  anchors: anchorScores,
  mean_score,
  verify_summary: VERIFY ? verifyAgg : null,
  fixes: fixes.filter(Boolean).map(f => ({ doc: f.doc, files_fixed: f.files_fixed, n_edits: f.n_edits, deferred: f.deferred, self_check_ok: f.self_check_ok })),
  edited_files: editedFiles,
  gate
}
