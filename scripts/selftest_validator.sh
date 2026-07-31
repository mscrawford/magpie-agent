#!/bin/bash
# selftest_validator.sh — positive control for validate_consistency.sh
#
# WHY THIS EXISTS:
# A doc validator that reports "0 errors" is worthless unless we can prove it is
# *capable* of reporting errors. From 2025-10-26 to 2026-05-31 the validator
# silently died at check 1 (set -e + ((VAR++))-from-0) while commit messages and
# project/sync_log.json recorded "NN/NN clean" — a green that no completed run
# ever produced. This self-test makes that class of failure impossible to miss
# by asserting six properties on an isolated fixture:
#   1. CLEAN tree         -> verdict=PASS, exit 0                  (no false positive)
#   2. PLANTED defect     -> verdict=FAIL, exit 1, defect named, completed=1
#   3. FORCED early exit   -> exit 99, "ABORTED"                   (death safety net)
#   4. PER-CHECK controls -> each load-bearing check_*.py --self-test prints SELFTEST_OK
#   5. SECTION-COUNT skip  -> stale SECTION_TOTAL -> exit 99       (skip safety net)
#   6. INLINE-CHECK controls -> one planted defect per inline bash check, each
#                               absent from the clean run and named in the planted one
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

# Two filenames this harness must handle are ASSEMBLED rather than spelled out,
# because the checks they belong to scan this repo's own files and would flag this
# harness for containing them -- a linter's positive control tripping the linter.
#   STALE_DOCNAME: the legacy agent-doc filename. Check 7 scans *.md AND *.sh for
#     it, so a literal here becomes a standing gate warning (observed: it did).
#   STALE_PREFIX: the stale self-referential path prefix. Check 12 scans *.md only
#     today, so a literal is harmless now; assembled anyway so a future widening of
#     that check does not silently red-flag its own test.
# Both literals live in their checks' own sections of validate_consistency.sh.
STALE_DOCNAME="CLAUDE.""md"
STALE_PREFIX="magpie-agent""/"

build_clean_fixture() {
    rm -rf "$FIXTURE"
    # Check 10 compares the fixture's AGENT.md against the two deployed copies one
    # level up, i.e. files in $BASE rather than in $FIXTURE. Clearing them here keeps
    # every sub-test hermetic no matter what an earlier one deposited beside the
    # fixture (a no-op on a fresh base).
    rm -f "$BASE/AGENT.md" "$BASE/$STALE_DOCNAME"
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
echo "[1/6] clean fixture should PASS"
build_clean_fixture
run validate_consistency.sh
if [ "$RC" -eq 0 ] && grep -q "verdict=PASS" <<<"$OUT" && grep -q "completed=1" <<<"$OUT"; then
    pass "clean tree -> exit 0, verdict=PASS, completed=1"
else
    fail "clean tree expected exit 0 / PASS / completed=1; got exit $RC"
    grep "VALIDATOR_RESULT\|FATAL" <<<"$OUT" | sed 's/^/        /'
fi

# ---- 2: planted unclosed code block must be DETECTED (FAIL) ----
echo "[2/6] planted defect should be DETECTED (FAIL)"
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
echo "[3/6] premature death should ABORT loudly (exit 99)"
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
echo "[4/6] per-check positive controls (--self-test)"
SELFTEST_SCRIPTS=(check_gams_citations_impl check_default_realizations check_gams_variables \
                  check_doc_var_existence check_scaling check_consumer_attribution \
                  check_hedged_claims check_module_realizations probe_dedup_check \
                  check_gams_equations check_gams_realizations check_no_bare_cites \
                  check_param_defaults check_renames check_set_members \
                  check_intra_doc_contradiction check_role_attribution \
                  check_attribution_tables check_attribution_prose \
                  check_attribution_omissions check_dependent_counts \
                  gams_slices check_dependent_direction check_bindability \
                  check_rolemap_completeness check_cfg_gams_wiring \
                  check_fenced_identifiers check_module_set_claims \
                  check_local_paths check_semantic_invariance)
# ASSERTION COUNTS (2026-07-31). The sentinel above proves a --self-test RAN.
# It cannot prove the self-test ASSERTED anything: a self_test() whose body was
# gutted still prints its sentinel and exits 0. Measured case from the session
# that added this: a positive control passed while being structurally blind to
# the distinction it was cited for, because the anchor module happened to give
# the same answer under both definitions.
#
# So the sentinel MAY carry a trailing count -- "SELFTEST_OK <name> <n>" -- and
# when it does, the harness enforces:
#   n > 0                  a self-test that asserts nothing cannot pass
#   n >= registered count  assertions cannot be quietly deleted (a ratchet)
# The registry is audit/selftest_assertion_counts.json. Checkers not yet
# migrated print the bare sentinel and are counted as LEGACY and reported, so
# the size of the unmigrated set stays visible instead of being assumed small.
#
# The registry is read ONCE, here, and a malformed or unreadable-but-present
# file is a hard FAIL rather than an empty lookup: silently degrading to "no
# pins" would turn the ratchet off without telling anyone, which is the same
# silent-green failure the counts exist to prevent.
COUNT_REGISTRY="$SCRIPT_DIR/../audit/selftest_assertion_counts.json"
COUNT_PINS="$BASE/selftest_count_pins.txt"
if [ -f "$COUNT_REGISTRY" ]; then
    if ! python3 -c "
import json,sys
d = json.load(open(sys.argv[1]))
for k, v in sorted(d.get('counts', {}).items()):
    if not isinstance(v, int) or v < 1:
        raise SystemExit(f'bad pin for {k}: {v!r} (want a positive integer)')
    print(f'{k} {v}')
" "$COUNT_REGISTRY" > "$COUNT_PINS" 2>"$BASE/count_pin_err.txt"; then
        fail "assertion-count registry unreadable: $(cat "$BASE/count_pin_err.txt" | tail -1)"
        : > "$COUNT_PINS"
    fi
else
    : > "$COUNT_PINS"
fi
# GENERATORS outside scripts/ that carry a --self-test. They are not gate checks,
# so they are not in SELFTEST_SCRIPTS, but their output IS consumed: the module
# centrality table in core_docs/Module_Dependencies.md 1.2 and Appendix A of
# cross_module/modification_safety_guide.md are generated from
# compute_module_centrality.py. Nothing else re-runs it, so without this the
# published table could go stale silently whenever the role map moves.
# Paths are relative to the repo root; the sentinel name is the file stem.
SELFTEST_TOOLS=(audit/tools/compute_module_centrality.py)

st_counted=0; st_legacy=0; st_legacy_names=""
for spec in "${SELFTEST_SCRIPTS[@]}" "${SELFTEST_TOOLS[@]}"; do
    case "$spec" in
        */*) s="$(basename "$spec" .py)"; st_path="$SCRIPT_DIR/../$spec" ;;
        *)   s="$spec";                   st_path="$SCRIPT_DIR/$s.py"    ;;
    esac
    if [ ! -f "$st_path" ]; then
        fail "$s.py missing (expected a --self-test)"
        continue
    fi
    st_out="$(python3 "$st_path" --self-test 2>&1)"; st_rc=$?
    # The sentinel must be its OWN line so "SELFTEST_OK foo" cannot be satisfied
    # by a substring of "SELFTEST_OK foo_bar" (prefix-name collision). The count,
    # when present, is a single trailing integer.
    st_line="$(grep -E "^SELFTEST_OK $s( [0-9]+)?$" <<<"$st_out" | head -1)"
    if [ "$st_rc" -ne 0 ]; then
        fail "$s --self-test FAILED (exit $st_rc; positive control did not hold)"
        printf '%s\n' "$st_out" | sed 's/^/          | /'
        continue
    fi
    if [ -z "$st_line" ]; then
        fail "$s --self-test exited 0 but printed no 'SELFTEST_OK $s' sentinel (check may be ignoring --self-test)"
        printf '%s\n' "$st_out" | sed 's/^/          | /'
        continue
    fi

    st_n="$(awk '{print ($3 == "" ? "" : $3)}' <<<"$st_line")"
    st_want="$(awk -v k="$s" '$1 == k {print $2}' "$COUNT_PINS")"
    st_how="declared"

    # No explicit count on the sentinel: DERIVE one by counting the assertion
    # outcome lines the check already prints. Most checks print one line per
    # assertion, in one of three house styles, so deriving covers them with no
    # edit. A check whose style prints only a SUMMARY derives 0 and must declare
    # its count explicitly -- that is reported below, not silently tolerated.
    if [ -z "$st_n" ]; then
        st_n="$(grep -cE 'SELF-?TEST[^:]*(PASS|FAIL)|SELF-?TEST \[[^]]*\]: *(PASS|FAIL)' <<<"$st_out")"
        st_how="derived"
    fi

    if [ "$st_n" -le 0 ]; then
        if [ -n "$st_want" ]; then
            fail "$s --self-test lost its assertion count (registry pins >= $st_want; it must print 'SELFTEST_OK $s <n>')"
        else
            st_legacy=$((st_legacy + 1)); st_legacy_names="$st_legacy_names $s"
            pass "$s --self-test (summary-only output; no countable assertions -- declare a count)"
        fi
        continue
    fi
    if [ -n "$st_want" ] && [ "$st_n" -lt "$st_want" ]; then
        fail "$s --self-test asserts $st_n but the registry pins >= $st_want (assertions were removed)"
        continue
    fi
    st_counted=$((st_counted + 1))
    pass "$s --self-test ($st_n assertions, $st_how)"
done
if [ "$st_legacy" -eq 0 ]; then
    echo "      assertion counts: $st_counted/$st_counted checkers counted; none uncounted"
else
    echo "      assertion counts: $st_counted/$((st_counted + st_legacy)) counted; $st_legacy uncounted (summary-only, must declare) —$st_legacy_names"
fi

# ---- 5: a silently-skipped section must ABORT (exit 99) ----
# Regression test for the "completed=1 proves REACHED, not RAN" gap (R8 I2): make
# SECTION_TOTAL disagree with the sections that actually run; the structural guard
# must fire rather than report a green that verified fewer sections than it claims.
echo "[5/6] section-count mismatch should ABORT (exit 99)"
build_clean_fixture
sed 's/^SECTION_TOTAL=.*/SECTION_TOTAL=999/' "$VALIDATOR" > "$FIXTURE/scripts/validate_skip.sh"
run validate_skip.sh
if [ "$RC" -eq 99 ] && grep -q "section-count mismatch" <<<"$OUT"; then
    pass "section mismatch -> exit 99, structural guard fires"
else
    fail "section mismatch expected exit 99 + 'section-count mismatch'; got exit $RC"
    grep "VALIDATOR_RESULT\|section-count\|FATAL" <<<"$OUT" | sed 's/^/        /'
fi

# ---- 6: planted-defect controls for the INLINE bash checks (Plan C item C2) ----
# Sub-test 4 binds the extracted check_*.py checkers through their own --self-test.
# The checks written INLINE in validate_consistency.sh had no equivalent control:
# nothing proved they were still capable of firing, so a silent run from them was
# unfalsifiable -- indistinguishable between "corpus clean" and "check blind".
# These eight are the set worth covering: Checks 1, 2 and 6 are slated for removal,
# 4/23/26 are retired tombstones, and 13 is already covered by sub-test 2 above.
#
# Each case asserts BOTH directions, which is what makes it a control rather than a
# coincidence:
#   * the message is ABSENT from the clean run  -> the plant is what causes it
#   * the message is PRESENT in the planted run -> the check still fires
#   * plus the exit code / verdict / counter movement the check's severity implies
# So a check fails here if its detection breaks, and equally if it still logs but
# stops counting. When a check's wording legitimately changes, update the needle --
# do not drop the case.
echo "[6/6] planted-defect controls for the inline bash checks"

# STALE_DOCNAME and STALE_PREFIX are defined near build_clean_fixture above; see
# the note there for why they are assembled rather than written out.
plant_inline_defect() {  # $1 = check id; mutates the freshly built clean fixture
    case "$1" in
      03) printf 'This doc refers to module_99.md, which does not exist.\n' \
              > "$FIXTURE/core_docs/BrokenRef.md" ;;
      05) rm -f "$FIXTURE/project/sync_log.json" ;;
      07) printf 'Legacy pointer: see %s for setup.\n' "$STALE_DOCNAME" \
              > "$FIXTURE/core_docs/StaleName.md" ;;
      08) printf '# Broken\n\n[missing target](no_such_file.md)\n' \
              > "$FIXTURE/core_docs/BrokenLink.md" ;;
      09) printf '# Orphan helper\n\nRegistered in no routing table.\n' \
              > "$FIXTURE/agent/helpers/orphan_helper.md" ;;
      10) printf '# AGENT\n\nDeployed copy has diverged.\n' > "$BASE/AGENT.md" ;;
      11) printf '# Startup\n\nPinned at 0123456789abcdef0123456789abcdef01234567.\n' \
              > "$FIXTURE/agent/helpers/session_startup.md" ;;
      12) printf 'Run `%sscripts/foo.sh` to start.\n' "$STALE_PREFIX" \
              > "$FIXTURE/core_docs/StalePrefix.md" ;;
      43) # Push AGENT.md past the 40 KiB always-loaded budget. Only the source
          # copy is grown: the clean fixture ships no deployed copies, so Check 10
          # stays at warnings and this case isolates Check 43.
          python3 -c "
import sys
p = sys.argv[1]
with open(p, 'a') as f:
    f.write('\\n<!-- padding -->\\n' + ('x' * 41000))
" "$FIXTURE/AGENT.md" ;;
      *)  echo "        (no plant defined for check $1)"; return 1 ;;
    esac
}

vr_num() {  # $1 = validator output, $2 = counter name -> its integer value
    grep -o 'VALIDATOR_RESULT:.*' <<<"$1" | tail -1 | grep -oE "$2=[0-9]+" | cut -d= -f2
}

# One clean run, reused as the "absent before" reference for every case below.
build_clean_fixture
run validate_consistency.sh
CLEAN_OUT="$OUT"
CLEAN_WARNINGS="$(vr_num "$CLEAN_OUT" warnings)"; CLEAN_WARNINGS="${CLEAN_WARNINGS:-0}"

# id | severity | the message the check must emit when it fires
INLINE_CASES=(
  "03|error|Broken reference: module_99.md referenced but doesn't exist"
  "05|error|project/sync_log.json missing (run sync command)"
  "07|warn|files still reference ${STALE_DOCNAME} (should be AGENT.md)"
  "08|error|broken markdown links found (see above)"
  "09|warn|trigger sync issues found (see above)"
  "10|error|AGENT.md differs from ../AGENT.md"
  "11|warn|files contain hardcoded commit hashes (may become stale)"
  "12|error|backtick-quoted paths use stale '${STALE_PREFIX}' prefix"
  "43|error|over the 40960 B budget"
)

for case_spec in "${INLINE_CASES[@]}"; do
    IFS='|' read -r cid severity needle <<<"$case_spec"
    build_clean_fixture
    plant_inline_defect "$cid"
    run validate_consistency.sh
    err_n="$(vr_num "$OUT" errors)";     err_n="${err_n:-0}"
    warn_n="$(vr_num "$OUT" warnings)";  warn_n="${warn_n:-0}"

    problems=""
    if grep -qF -- "$needle" <<<"$CLEAN_OUT"; then
        problems="$problems; message ALREADY present in the clean run (vacuous control)"
    fi
    grep -qF -- "$needle" <<<"$OUT" || problems="$problems; planted defect NOT reported"
    grep -q "completed=1" <<<"$OUT"  || problems="$problems; run did not complete"
    if [ "$severity" = "error" ]; then
        [ "$RC" -eq 1 ]                  || problems="$problems; expected exit 1, got $RC"
        grep -q "verdict=FAIL" <<<"$OUT" || problems="$problems; expected verdict=FAIL"
        [ "$err_n" -ge 1 ]               || problems="$problems; error counter did not move"
    else
        [ "$RC" -eq 0 ]                  || problems="$problems; expected exit 0, got $RC"
        grep -q "verdict=PASS" <<<"$OUT" || problems="$problems; expected verdict=PASS"
        [ "$err_n" -eq 0 ]               || problems="$problems; warning-level check raised an error"
        [ "$warn_n" -gt "$CLEAN_WARNINGS" ] \
                                         || problems="$problems; warning counter did not move ($warn_n vs clean $CLEAN_WARNINGS)"
    fi

    if [ -z "$problems" ]; then
        pass "Check $cid ($severity) -> planted defect detected and named"
    else
        fail "Check $cid ($severity) positive control did not hold${problems}"
        grep "VALIDATOR_RESULT" <<<"$OUT" | sed 's/^/          | /'
    fi
done

echo ""
if [ "$FAILURES" -eq 0 ]; then
    echo "SELFTEST_RESULT: PASS — validator detects defects, aborts loudly, and passes clean trees."
    exit 0
else
    echo "SELFTEST_RESULT: FAIL — $FAILURES sub-test(s) failed. Do NOT trust validate_consistency.sh until fixed."
    exit 1
fi
