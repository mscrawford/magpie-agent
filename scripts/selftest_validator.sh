#!/bin/bash
# selftest_validator.sh — positive control for validate_consistency.sh
#
# WHY THIS EXISTS:
# A doc validator that reports "0 errors" is worthless unless we can prove it is
# *capable* of reporting errors. From 2025-10-26 to 2026-05-31 the validator
# silently died at check 1 (set -e + ((VAR++))-from-0) while commit messages and
# project/sync_log.json recorded "NN/NN clean" — a green that no completed run
# ever produced. This self-test makes that class of failure impossible to miss
# by asserting five properties on an isolated fixture:
#   1. CLEAN tree         -> verdict=PASS, exit 0                  (no false positive)
#   2. PLANTED defect     -> verdict=FAIL, exit 1, defect named, completed=1
#   3. FORCED early exit   -> exit 99, "ABORTED"                   (death safety net)
#   4. PER-CHECK controls -> each load-bearing check_*.py --self-test prints SELFTEST_OK
#   5. SECTION-COUNT skip  -> stale SECTION_TOTAL -> exit 99       (skip safety net)
#
# Run this before trusting any clean validate_consistency.sh result, and in CI.
# Exit 0 = the guard is trustworthy; exit 1 = a property failed, do NOT trust it.
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$SCRIPT_DIR/validate_consistency.sh"
[ -f "$VALIDATOR" ] || { echo "FATAL: validator not found at $VALIDATOR" >&2; exit 2; }

FAILURES=0
pass() { echo "  ok  $1"; }
fail() { echo "  XX  $1"; FAILURES=$((FAILURES + 1)); }

# Fixture lives under a fresh empty base so that the validator's "../AGENT.md"
# deployment check (Check 10) resolves into a controlled, empty parent rather
# than a polluted /tmp.
BASE="$(mktemp -d)"
FIXTURE="$BASE/magpie-agent"
trap 'rm -rf "$BASE"' EXIT

build_clean_fixture() {
    rm -rf "$FIXTURE"
    mkdir -p "$FIXTURE"/{scripts,modules,core_docs,cross_module,reference,agent/helpers,project}
    cp "$VALIDATOR" "$FIXTURE/scripts/validate_consistency.sh"
    printf '# AGENT\n\nNo links here.\n' > "$FIXTURE/AGENT.md"
    printf '# README\n\naudit/validation_rounds.json AGENT.md\n' > "$FIXTURE/README.md"
    printf '{ "sync_status": { "last_sync_commit": "0000000" } }\n' > "$FIXTURE/project/sync_log.json"
}

run() {  # $1 = script basename under fixture/scripts ; sets OUT, RC
    OUT="$(bash "$FIXTURE/scripts/$1" 2>&1)"; RC=$?
}

echo "[selftest] fixture base: $BASE"

# ---- 1: clean fixture must PASS (no false positives) ----
echo "[1/5] clean fixture should PASS"
build_clean_fixture
run validate_consistency.sh
if [ "$RC" -eq 0 ] && grep -q "verdict=PASS" <<<"$OUT" && grep -q "completed=1" <<<"$OUT"; then
    pass "clean tree -> exit 0, verdict=PASS, completed=1"
else
    fail "clean tree expected exit 0 / PASS / completed=1; got exit $RC"
    grep "VALIDATOR_RESULT\|FATAL" <<<"$OUT" | sed 's/^/        /'
fi

# ---- 2: planted unclosed code block must be DETECTED (FAIL) ----
echo "[2/5] planted defect should be DETECTED (FAIL)"
build_clean_fixture
# Odd number of ``` fences -> Check 13 must flag it.
printf '# Planted defect\n```python\nprint("no closing fence")\n' > "$FIXTURE/core_docs/Unclosed.md"
run validate_consistency.sh
if [ "$RC" -eq 1 ] && grep -q "verdict=FAIL" <<<"$OUT" \
        && grep -q "completed=1" <<<"$OUT" && grep -q "Unclosed code block" <<<"$OUT"; then
    pass "planted defect -> exit 1, verdict=FAIL, completed=1, defect named"
else
    fail "planted defect not caught as expected; got exit $RC"
    grep "VALIDATOR_RESULT\|Unclosed\|FATAL" <<<"$OUT" | sed 's/^/        /'
fi

# ---- 3: forced early exit must ABORT loudly (exit 99) ----
# This is the direct regression test for the 2025-2026 silent-death bug: inject
# a premature exit after the trap is installed and confirm the safety net fires.
echo "[3/5] premature death should ABORT loudly (exit 99)"
build_clean_fixture
# Portable injection: BSD/macOS `sed` rejects GNU's one-line `/pat/a text`, so use awk.
awk '{ print } /^trap on_exit EXIT$/ { print "echo \"[selftest] forcing early exit\"; exit 7" }' \
    "$VALIDATOR" > "$FIXTURE/scripts/validate_aborts.sh"
run validate_aborts.sh
if [ "$RC" -eq 99 ] && grep -q "ABORTED before completion" <<<"$OUT"; then
    pass "early exit -> exit 99, ABORTED message (safety net fires)"
else
    fail "early exit expected exit 99 + ABORTED; got exit $RC"
    tail -5 <<<"$OUT" | sed 's/^/        /'
fi

# ---- 4: per-check positive controls (each load-bearing check_*.py --self-test) ----
# Binds the load-bearing checks end-to-end (pipeline-audit R8 I2). A check that
# silently stops catching its bug class fails here -- proven: neutering a detector
# makes its --self-test exit non-zero. ADD new --self-test scripts to this list
# ONLY after the check actually implements a real --self-test (registering an
# unimplemented one would mint a false positive control -- finding C4-4).
#
# Sentinel requirement (pipeline-audit R9 C4 / R10 C1): a check that IGNORES
# --self-test falls through to a normal corpus run and exits 0, minting a FALSE
# positive control. So we require each --self-test to print "SELFTEST_OK <name>"
# on stdout, NOT merely exit 0. Exit-0-without-the-sentinel is treated as a FAIL.
echo "[4/5] per-check positive controls (--self-test)"
SELFTEST_SCRIPTS=(check_gams_citations_impl check_default_realizations check_gams_variables \
                  check_doc_var_existence check_scaling check_consumer_attribution \
                  check_hedged_claims check_module_realizations probe_dedup_check \
                  check_gams_equations check_gams_realizations check_no_bare_cites \
                  check_param_defaults check_renames)
for s in "${SELFTEST_SCRIPTS[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$s.py" ]; then
        fail "$s.py missing (expected a --self-test)"
        continue
    fi
    st_out="$(python3 "$SCRIPT_DIR/$s.py" --self-test 2>&1)"; st_rc=$?
    # -qx: the sentinel must be its OWN exact line, so "SELFTEST_OK foo" cannot
    # be satisfied by a substring of "SELFTEST_OK foo_bar" (prefix-name collision).
    if [ "$st_rc" -eq 0 ] && grep -qx "SELFTEST_OK $s" <<<"$st_out"; then
        pass "$s --self-test"
    elif [ "$st_rc" -eq 0 ]; then
        fail "$s --self-test exited 0 but printed no 'SELFTEST_OK $s' sentinel (check may be ignoring --self-test)"
        printf '%s\n' "$st_out" | sed 's/^/          | /'
    else
        fail "$s --self-test FAILED (exit $st_rc; positive control did not hold)"
        printf '%s\n' "$st_out" | sed 's/^/          | /'
    fi
done

# ---- 5: a silently-skipped section must ABORT (exit 99) ----
# Regression test for the "completed=1 proves REACHED, not RAN" gap (R8 I2): make
# SECTION_TOTAL disagree with the sections that actually run; the structural guard
# must fire rather than report a green that verified fewer sections than it claims.
echo "[5/5] section-count mismatch should ABORT (exit 99)"
build_clean_fixture
sed 's/^SECTION_TOTAL=.*/SECTION_TOTAL=999/' "$VALIDATOR" > "$FIXTURE/scripts/validate_skip.sh"
run validate_skip.sh
if [ "$RC" -eq 99 ] && grep -q "section-count mismatch" <<<"$OUT"; then
    pass "section mismatch -> exit 99, structural guard fires"
else
    fail "section mismatch expected exit 99 + 'section-count mismatch'; got exit $RC"
    grep "VALIDATOR_RESULT\|section-count\|FATAL" <<<"$OUT" | sed 's/^/        /'
fi

echo ""
if [ "$FAILURES" -eq 0 ]; then
    echo "SELFTEST_RESULT: PASS — validator detects defects, aborts loudly, and passes clean trees."
    exit 0
else
    echo "SELFTEST_RESULT: FAIL — $FAILURES sub-test(s) failed. Do NOT trust validate_consistency.sh until fixed."
    exit 1
fi
