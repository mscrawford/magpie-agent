#!/usr/bin/env node
/*
 * Positive control for the code-fact dedup grouping in doc_depth_audit.workflow.js.
 *
 * Built BEFORE the grouping was trusted on any corpus, because "0 duplicates found"
 * is ambiguous between "no duplicates" and "grouping broken". The two known-bug cases
 * come from R55's own verification pass, which retired both by hand:
 *
 *   round55_depth/MEASUREMENT.md:65-71  M52 bugs 1/5/10 are "three views of one defect"
 *                                       at module_52.md:458 -> must collapse to ONE.
 *   round55_depth/MEASUREMENT.md:73-75  M52 bug 4 == M56 bug 7, one code fact at two doc
 *                                       sites in two DIFFERENT docs -> must pair. This is
 *                                       the case the per-doc prose key cannot reach at all.
 *
 * The function under test is EXTRACTED FROM THE WORKFLOW SOURCE between its
 * CODEFACT_KEY_BEGIN/END markers, so there is exactly one implementation and this test
 * cannot drift away from the code that actually runs.
 *
 * Usage: node audit/tools/test_codefact_dedup.js     (exit 0 pass, 1 fail)
 */
'use strict'
const fs = require('fs')
const path = require('path')

const HERE = __dirname
const WORKFLOW = path.join(HERE, 'doc_depth_audit.workflow.js')
const FINDINGS = path.join(HERE, '..', 'integrated', 'depth_residual_density.json')

// ---- extract the function under test, verbatim, from the workflow source ----
const src = fs.readFileSync(WORKFLOW, 'utf8')
const m = src.match(/\/\/ CODEFACT_KEY_BEGIN[\s\S]*?\/\/ CODEFACT_KEY_END/)
if (!m) {
  console.error('FAIL: CODEFACT_KEY_BEGIN/END markers not found in doc_depth_audit.workflow.js')
  console.error('      The test extracts the function from the workflow so the two cannot drift.')
  process.exit(1)
}
// new Function (not eval): under 'use strict' an eval'd declaration stays in eval's own
// scope and never reaches this module. new Function builds a non-strict body we can
// return the declaration out of.
const codeFactKey = (new Function(m[0] + '\nreturn codeFactKey'))()  // eslint-disable-line no-new-func

// ---- corpus under test: R55's archived findings ----
const findings = JSON.parse(fs.readFileSync(FINDINGS, 'utf8')).findings
const byId = Object.fromEntries(findings.map(f => [f.id, f]))

let failures = 0
function check(name, cond, detail) {
  console.log(`  ${cond ? 'PASS' : 'FAIL'} [${name}]${cond ? '' : ' -- ' + detail}`)
  if (!cond) failures++
}

// ---- control 1: three phrasings of one defect at one doc line must collapse ----
const g1 = ['module_52:1', 'module_52:5', 'module_52:10']
const g1keys = new Set(g1.map(id => codeFactKey(byId[id])))
check('pos-three-views-one-defect', g1keys.size === 1,
  `expected 1 group for M52 bugs 1/5/10, got ${g1keys.size}: ${[...g1keys].join(' | ')}`)

// ---- control 2: one code fact, two doc sites, TWO DOCS must pair (per-doc key cannot) ----
const g2 = ['module_52:4', 'module_56:7']
const g2keys = new Set(g2.map(id => codeFactKey(byId[id])))
check('pos-cross-doc-pair', g2keys.size === 1,
  `expected 1 group for M52:4 + M56:7, got ${g2keys.size}: ${[...g2keys].join(' | ')}`)

// ---- negative control: the two groups must NOT collapse into each other ----
check('neg-groups-stay-distinct', [...g1keys][0] !== [...g2keys][0],
  'the two independent defect groups collapsed into one key -- the key is too coarse')

// ---- negative control: a grouping that merges everything would pass the positives ----
const allKeys = new Set(findings.map(codeFactKey))
check('neg-not-degenerate', allKeys.size > 1,
  `every finding hashed to one key (${allKeys.size}) -- the key is vacuous`)

// ---- negative control: a grouping that merges nothing would also pass nothing ----
check('neg-not-identity', allKeys.size < findings.length,
  `key produced ${allKeys.size} groups for ${findings.length} findings -- it merges nothing, so it is the identity`)

// ---- report the range this key is FOR ----
const proseKeys = new Set(findings.map(f => `${f.doc_line}::${String(f.claim || '').trim().slice(0, 80).toLowerCase()}`))
console.log('')
console.log(`  R55 archived findings : ${findings.length}`)
console.log(`  prose-key groups      : ${proseKeys.size}   (upper bound, over-counts duplicates)`)
console.log(`  code-fact groups      : ${allKeys.size}   (lower bound, may over-merge)`)
console.log(`  distinct doc sites    : ${new Set(findings.map(f => f.doc_line)).size}`)
console.log('')

if (failures) {
  console.log(`test_codefact_dedup: FAIL (${failures})`)
  process.exit(1)
}
console.log('test_codefact_dedup: PASS')
console.log('SELFTEST_OK test_codefact_dedup')
process.exit(0)
