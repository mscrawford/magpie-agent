# Pattern D2 omission backlog (R25 follow-up)

**Status (2026-05-25)**: ✅ **RESOLVED**. 64 unique fixes applied across 14 producer docs via a parallel Sonnet sweep with orchestrator pre-triage and validator-gated review. Pattern D2 dropped from 85 advisories to 1 documented FP. See commit `fix(R25 follow-up): Pattern D2 consumer-attribution sweep` for the per-doc summary.

**Residual D2** (1 advisory, all documented FPs):
- `modules/module_16.md:568` `vm_supply` omits M70 — FP: M70's only grep-hit is a doc-comment in `modules/70_livestock/module.gms:18`, not a real consumer use.

**Residual Pattern D** (9 advisories, all pre-existing or restructure-induced FPs):
- 8 pre-existing FPs at module_13:152, module_16:568, module_35:9 ×2, module_35:917 ×2, module_52:4 ×2 — same FP class as baseline (cross-attribution on long lines with multiple backticked identifiers).
- 1 location-shifted FP at module_52:291 (was `:282` pre-sweep; content unchanged, just shifted by neighboring restructures).
- Net change in Pattern D: -2 (11 baseline → 9 current).

## How the sweep was executed (for future reference)

1. **Orchestrator pre-triage** (~30 min): wrote `scripts/dump_d2.py` + `scripts/triage.py` (one-shot helpers, not committed) to classify each (doc, var, omitted_M) tuple as CONFIRM (real consumer with file:line) or FP (declaration-only or no real grep-hit). Result: 67 CONFIRM, 3 FP (3.5% rate). Per-doc fix-list files written to `$CLAUDE_JOB_DIR/fix_module_*.md`.

2. **Parallel Sonnet agents** (~30 min wall, 14 agents): one Sonnet per producer doc, all parallel in a single message. Each agent received its doc's fix list with a tight prompt: add module + file:line citation only, no interpretive prose, match local format, grep-verify each fix before applying.

3. **Validator gate + spot-review** (~25 min, orchestrator): re-ran Pattern D2 + Pattern D + 41-check. Initial result: Pattern D regressed from 11 to 51 due to long-line cross-attribution FPs at `module_52.md:263` and `module_73.md:318`. Restructured 3 lines (M52:263 split inline-list into separate bullet block; M73:318 split into two bullet blocks; M38:337 added consumer-trigger word to bridge bullet aggregation). Final: Pattern D 11 → 9 (improvement), Pattern D2 85 → 1.

## What's already filtered in the validator (FP suppressions)

- **Producer self-references** (e.g., M52 producing pm_X listed as omitting M52)
- **Current-doc module self-references** (a doc about M52 doesn't need to list M52 as a consumer of its own variable)
- **Hyphen-compound trigger words** (`land-use`, `water-use` no longer falsely trigger via `\buses?\b`)
- **Subset hedges** (`primary`, `main`, `most important`, `key consumer`, `principal`, `e.g.`, `such as`, `etc`, `among others`, `including but not limited to`, `may be affected`, `broader`, `wider`, `touched by`, `set of`)
- **Bullet-list aggregation** across adjacent bullets at the same indent

If a future bug shows up that one of these filters should not have suppressed, tighten the filter rather than removing it.

## Known validator limitations surfaced during the sweep

These are documented as FP-generators; a future validator-hardening pass could address them:

1. **Long lines with multiple backticked variable names produce Pattern D cross-attribution FPs.** When line `L` contains var1, var2, var3 and one consumer-trigger word, the validator assumes all three variables share the same listed consumers, then flags var2/var3 as listing non-real consumers.
2. **The bullet-aggregation can't bridge across `**bold-header**` paragraph breaks.** A variable consumed in one bullet section and re-mentioned in a later prose paragraph triggers a D2 omission if the prose paragraph doesn't repeat the consumer list.
3. **`input.gms` table declarations don't register as the producer.** `pm_climate_class` is declared as a `table` in `modules/45_climate/static/input.gms:10`; the validator's `build_producer_map()` only scans `declarations.gms`, so M45 isn't recognized as the producer and falsely fires as "omitted consumer". One residual FP at `modules/module_73.md` (now suppressed by the sweep's restructure, but the validator gap remains).

These limitations did NOT block the sweep — they were worked around via doc restructuring. They're documented here so future validator work can target them.

## How to refresh the count

```bash
python3 scripts/check_consumer_attribution.py --summary-only | grep "Pattern D2"
```
