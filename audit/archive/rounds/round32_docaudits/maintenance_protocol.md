# Round 32 Doc Audit — agent/helpers/maintenance_protocol.md

**Auditor**: adversarial doc auditor (Opus 4.8, 1M ctx)
**Date**: 2026-05-30
**Target**: `<magpie-agent>/agent/helpers/maintenance_protocol.md`
**Ground truth**: `/tmp/magpie_develop_ro` (GAMS code + config/default.cfg) + the live magpie-agent repo (this doc is largely about the agent's OWN machinery, so the repo itself is the relevant ground truth for script names, file paths, allowlist contents).

---

## Overall Verdict: ACCURATE

### Accuracy Score: 10/10

This is a process/workflow doc. It contains **no GAMS interface-variable, equation, populator/consumer-set, or parameter-default claims** — the high-risk classes that produce Critical bugs (R20 anchor) are absent here. Its load-bearing, code-checkable claims are: (a) script names, (b) command names + backing files, (c) repo file paths (JSON state files, helper/command cross-refs), (d) the advisory_allowlist.json contents + functional behavior, (e) the recovery-procedure shell commands, (f) the R6 G1 historical anecdote, (g) the "46 modules" example count. **Every one of these verified correct against current code/repo.** No bugs confirmed.

The pre-run advisory ("Never semantically validated. Verify any file paths, script names, cfg references, and module-count/realization claims") is **REFUTED** for this doc — all such claims check out.

---

## Verified Claims (correct)

### Scripts (all exist)
- `scripts/validate_consistency.sh` — EXISTS (44205 bytes, executable). `ls` confirmed.
- `scripts/check_gams_variables.py`, `check_gams_realizations.py`, `check_gams_equations.py`, `check_gams_citations.sh`, `check_default_realizations.py` — all EXIST. (Referenced indirectly via Layer-1/Layer-3 descriptions and bug-class mapping.)
- `scripts/check_param_defaults.py`, `scripts/check_multi_section_consistency.py` (named in the allowlist consumers) — both EXIST.

### Commands + backing files (all exist)
- `/validate` → `agent/commands/validate.md` EXISTS.
- `/sync` → `agent/commands/sync.md` EXISTS.
- `/validate-semantic` → `agent/commands/validate-semantic.md` EXISTS. (Doc line 317 hedges "(if exists)" — harmless; it does exist.)

### State / data files (all exist)
- `audit/advisory_allowlist.json` — EXISTS.
- `project/sync_log.json` — EXISTS.
- `audit/validation_rounds.json` — EXISTS.
- `audit/pipeline_audit_rounds.json` — EXISTS (referenced via allowlist review cadence).

### Cross-reference targets (Module Cross-References + Related Helpers tables, lines 312-330) — all exist
- `agent/helpers/session_startup.md` ✓
- `agent/commands/sync.md` ✓
- `agent/commands/validate.md` ✓
- `agent/commands/validate-semantic.md` ✓
- `project/sync_log.json` ✓
- `audit/validation_rounds.json` ✓
- `agent/helpers/modification_impact_analysis.md` ✓
- `core_docs/Core_Architecture.md` ✓
- `core_docs/Module_Dependencies.md` ✓
- `agent/helpers/realization_selection.md` ✓ (referenced in Drift table + decision tree)
- `agent/helpers/scenario_carbon_pricing.md` ✓
- `cross_module/land_balance_conservation.md` ✓ (referenced in decision tree)

### advisory_allowlist.json claim (line 37) — VERIFIED CORRECT, including functional behavior
Doc: "`audit/advisory_allowlist.json` suppresses known false-positives from advisory checks (currently `check_param_defaults` for unit-rendering FPs, `check_multi_section_consistency` for prose-shorthand FPs)... To add a new suppression, append an `{check, file, key, reason, added, added_in_round}` object to the `allowlist` array."

- File read: 5 entries. 2 under `check_param_defaults` (module_38 s38_immobile percent-rendering; module_59 s59_nitrogen_uptake unit-conversion), 3 under `check_multi_section_consistency` (module_29 vm_land prose-shorthand; module_35 pm_carbon_density_secdforest_ac; module_80 p80_modelstat). Both checks are represented → doc's two-check characterization is accurate.
- **Append-format schema matches exactly**: the JSON `_schema.fields` defines `check, file, key, reason, added, added_in_round` — identical to the doc's stated tuple.
- **Functional behavior verified**: both checkers actually READ the file. `check_param_defaults.py:35` `ALLOWLIST_PATH = os.path.join(AGENT_DIR, "audit", "advisory_allowlist.json")` + `load_allowlist()` + applied at line 274. `check_multi_section_consistency.py:44` `ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"` + applied at line 204. Cross-checked with `grep -rln` AND `rg -l` (both methods returned exactly these two scripts; positive — the validator wires both via `PARAM_DEFAULT_SCRIPT` line 823 and `CONSISTENCY_SCRIPT` line 913).
- Minor prose imprecision (NOT a bug): "unit-rendering FPs" for `check_param_defaults` — one of its two entries (s38_immobile) is a *percent*-rendering FP (100% = 1.0 share), the other (s59) is a *unit-conversion* FP. "Unit-rendering" loosely covers both; this is prose characterization, not a code-checkable name/path/value. Not flagged.

### R6 G1 anecdote (line 238) — VERIFIED CORRECT
- "a prose helper inventory in helpers/README.md was one helper behind AGENT.md (missing `magpie4_reference` added 2026-05-24)": `git show -s d44823f` → commit date `2026-05-24 18:43:01 +0200`. The "added 2026-05-24" date is exact. `agent/helpers/magpie4_reference.md` EXISTS and is wired into AGENT.md (lines 207, 363, 485, 584, 646). helpers/README.md:23 corroborates the historical "5+ helpers behind" narration. Past-tense framing ("was one helper behind") correctly describes the now-fixed R6 state.
- "`project/README.md` claimed '2 essential files' while the directory had 4": current `project/README.md:16` now reads "This directory contains **4 files**" and lists 4 (README, sync_log.json, version_pins.json, archive/CURRENT_STATE...). Past-tense "claimed" correctly narrates the historical bug; current state (4 files) is consistent.
- "In R3 the agent's `helpers/README.md` had a duplicated routing table that drifted... by 5+ helpers": matches helpers/README.md:23 self-narration. (R3 historical claim, not code-verifiable against develop, but internally consistent.)

### Recovery-procedure shell commands — VERIFIED CORRECT
- §6 AGENT.md recovery: `cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md` then `diff AGENT.md ../AGENT.md` / `diff AGENT.md ../CLAUDE.md`. Both deploy targets EXIST (`../AGENT.md`, `../CLAUDE.md`, both 44932 bytes, identical mtime → currently in sync). Commands are well-formed.
- §6 "Sync Way Behind" uses `git -C ..`: `git -C <magpie-agent>/.. rev-parse --show-toplevel` → `<magpie-root>` (the parent MAgPIE repo). The `git -C ..` pattern correctly targets the MAgPIE repo when run from magpie-agent/. Verified the parent is a valid git repo with MAgPIE history.

### "46 modules" example (line 25) — VERIFIED CORRECT
Doc cites "46 modules" as the example stale-count target. `ls -d /tmp/magpie_develop_ro/modules/[0-9]*/ | wc -l` → **46**. Current develop has exactly 46 numbered module directories. The example count is accurate (and it is an *illustrative* example of a stale-count check, not a hard assertion, but it happens to be current).

### validate_consistency.sh structural description — VERIFIED CONSISTENT
Doc (line 20) describes the validator as "a suite of top-level structural checks (with sub-checks)... the run's summary prints the live counts" — deliberately NOT hardcoding a number. This matches validate.md:15 ("a suite of top-level structural checks (each with sub-checks)... the run's `=== Summary ===` prints the live counts"). The doc correctly avoids the hardcoded-count drift trap. The "What it catches" bullets (broken cross-refs, wrong names, stale counts, deployment drift, missing sections) all map to real validator categories listed in validate.md (checks 3/8, 14/15/16, 1/6, 10, and module-section coverage).

---

## Bugs Found

**None confirmed.**

---

## Deferred (uncertain / not code-verifiable / borderline — NOT to be edited)

1. **Line 236 — `core_docs/README.md` listed as an "e.g." subordinate-README example, but that file does not exist** (`ls` → No such file or directory; the other three in the list — agent/helpers/README.md, modules/README.md, cross_module/README.md — all exist). The reference is inside a parenthetical "e.g." enumeration of the *class* of non-top-level READMEs, and the rule is **prescriptive** ("MUST NOT contain inventories"), not a descriptive claim that the file exists. The rule would correctly apply to `core_docs/README.md` if it were created. I judge this below the flagging threshold (illustrative class-member, not a load-bearing existence claim) and defer rather than propose an edit. A maintainer *could* drop `core_docs/README.md` from the example list for tidiness, but it is not a code-behavior error and false-positive cost outweighs the cosmetic gain.

2. **R3/R6 "5+ helpers behind" / "one helper behind" drift magnitudes** — historical states from prior audit rounds; corroborated by helpers/README.md self-narration but not independently verifiable against develop. Internally consistent; no action.

3. **"unit-rendering FPs" characterization of check_param_defaults (line 37)** — mild prose imprecision (one of two entries is percent-rendering, not unit). Prose, not a code-checkable token. No edit warranted.

4. **Cadence/time-budget figures** (e.g., "~2 minutes", "15-30 minutes for 5-10 commits", "30-60 minutes per round", semantic-score thresholds like ≥8.0/≥9.0) — operational estimates and policy thresholds, not code-derivable. Out of scope.

5. **Decision-tree and priority-rules prose** (§4) — workflow advice; the GAMS-file-name references it uses (equations.gms, declarations.gms, presolve.gms, postsolve.gms, input.gms, core/sets.gms, main.gms, config/default.cfg) are all real MAgPIE conventional filenames, but the tree is advisory, not a code-behavior claim. No verification needed beyond confirming the filenames are MAgPIE-standard (they are).

---

## Summary

maintenance_protocol.md is a process/workflow helper with no GAMS-semantic claims. All code-checkable references — 6 scripts, 3 commands + backing files, ~12 cross-ref paths, the advisory_allowlist.json contents AND its functional wiring (both checkers read it; append-schema matches), the R6 G1 anecdote (magpie4_reference add-date 2026-05-24 exact; project/README now 4 files), all recovery shell commands (git -C .. → parent repo; cp targets exist), and the "46 modules" example (develop has 46) — verified correct. Pre-run advisory REFUTED. Zero confirmed bugs. One sub-threshold cosmetic note (core_docs/README.md in an "e.g." list does not exist) left in deferred per the false-positive-aversion mandate.
