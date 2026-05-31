#!/bin/bash
# selftest_validator.sh — positive control for validate_consistency.sh
#
# WHY THIS EXISTS:
# A doc validator that reports "0 errors" is worthless unless we can prove it is
# *capable* of reporting errors. From 2025-10-26 to 2026-05-31 the validator
# silently died at check 1 (set -e + ((VAR++))-from-0) while commit messages and
# project/sync_log.json recorded "NN/NN clean" — a green that no completed run
# ever produced. This self-test makes that class of failure impossible to miss
# by asserting three properties on an isolated fixture:
#   1. CLEAN tree         -> verdict=PASS, exit 0                  (no false positive)
#   2. PLANTED defect     -> verdict=FAIL, exit 1, defect named, completed=1
#   3. FORCED early exit   -> exit 99, "ABORTED"                   (safety net fires)
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
echo "[1/3] clean fixture should PASS"
build_clean_fixture
run validate_consistency.sh
if [ "$RC" -eq 0 ] && grep -q "verdict=PASS" <<<"$OUT" && grep -q "completed=1" <<<"$OUT"; then
    pass "clean tree -> exit 0, verdict=PASS, completed=1"
else
    fail "clean tree expected exit 0 / PASS / completed=1; got exit $RC"
    grep "VALIDATOR_RESULT\|FATAL" <<<"$OUT" | sed 's/^/        /'
fi

# ---- 2: planted unclosed code block must be DETECTED (FAIL) ----
echo "[2/3] planted defect should be DETECTED (FAIL)"
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
echo "[3/3] premature death should ABORT loudly (exit 99)"
build_clean_fixture
sed '/^trap on_exit EXIT$/a echo "[selftest] forcing early exit"; exit 7' \
    "$VALIDATOR" > "$FIXTURE/scripts/validate_aborts.sh"
run validate_aborts.sh
if [ "$RC" -eq 99 ] && grep -q "ABORTED before completion" <<<"$OUT"; then
    pass "early exit -> exit 99, ABORTED message (safety net fires)"
else
    fail "early exit expected exit 99 + ABORTED; got exit $RC"
    tail -5 <<<"$OUT" | sed 's/^/        /'
fi

echo ""
if [ "$FAILURES" -eq 0 ]; then
    echo "SELFTEST_RESULT: PASS — validator detects defects, aborts loudly, and passes clean trees."
    exit 0
else
    echo "SELFTEST_RESULT: FAIL — $FAILURES sub-test(s) failed. Do NOT trust validate_consistency.sh until fixed."
    exit 1
fi
