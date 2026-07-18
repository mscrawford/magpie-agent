#!/usr/bin/env bash
# R59 goal-condition sweep.
#
# WHY: each fix agent verified only the files it was assigned. Delegation silently
# narrows verification — a corrected claim can survive in a file nobody owned
# ([[feedback_check_delegated_work_against_goal]]). This checks the GOAL CONDITION
# across the whole corpus, not per-agent scope.
#
# Run from the magpie-agent root, AFTER all fixes are merged and BEFORE the final gate.
# Every probe is isolated (`|| true`) — a no-match grep exits 1 and would otherwise
# truncate the rest of the script under errexit.

cd "$(dirname "$0")/../../../.." || exit 1
echo "sweep root: $(pwd)"
GAMS="$(cd .. && pwd)"   # MAgPIE parent checkout, derived - never hard-code a local path
DOCS="modules cross_module core_docs reference agent"

echo
echo "=== 1. PHANTOM MODULE NUMBERS (F-5 class; generalizes the 'Module 33' bug) ==="
echo "Every 'Module NN' in doc prose must resolve to a real ../modules/NN_*/ directory."
rg -o --no-filename 'Module [0-9]{1,2}' $DOCS --glob '*.md' 2>/dev/null \
  | grep -oE '[0-9]{1,2}$' | sort -u | while read -r n; do
    # 10# forces base-10: a bare leading zero (e.g. "09") is parsed as OCTAL and errors.
    nn=$(printf '%02d' "$((10#$n))")
    if ! ls -d "$GAMS/modules/${nn}_"* >/dev/null 2>&1; then
      echo "  PHANTOM: 'Module $n' referenced in docs but no $GAMS/modules/${nn}_* exists"
      rg -n "Module $n\b" $DOCS --glob '*.md' 2>/dev/null | head -5
    fi
  done || true
echo "  (no PHANTOM lines above = clean)"

echo
echo "=== 2. stockType fabricated members ('planned' / 'potential') ==="
rg -n 'stockType' $DOCS --glob '*.md' 2>/dev/null | rg -i 'planned|potential' || echo "  clean"

echo
echo "=== 3. ac_est wrong membership ({ac0, ac5, ac10}) ==="
rg -n 'ac_est' $DOCS --glob '*.md' 2>/dev/null | rg 'ac10' || echo "  clean"

echo
echo "=== 4. vm_nr_inorg_fert_reg described as a 'free' variable ==="
rg -n -C1 'vm_nr_inorg_fert_reg' $DOCS --glob '*.md' 2>/dev/null | rg -i 'free variable' || echo "  clean"

echo
echo "=== 5. vm_costs_additional_mon attributed to M70 (belongs to M71) ==="
rg -n 'vm_costs_additional_mon' $DOCS --glob '*.md' 2>/dev/null || echo "  no occurrences"

echo
echo "=== 6. surviving 'no feedback loop' absolutes ==="
rg -ni 'no feedback loop' $DOCS --glob '*.md' 2>/dev/null || echo "  clean"

echo
echo "=== 7. citations to the DEAD config line (F-7): config/default.cfg:1835 ==="
rg -n 'default\.cfg:1835' $DOCS --glob '*.md' 2>/dev/null || echo "  clean"

echo
echo "=== sweep complete ==="
