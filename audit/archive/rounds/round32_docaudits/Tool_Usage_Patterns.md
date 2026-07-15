# Round 32 Doc Audit — `core_docs/Tool_Usage_Patterns.md`

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target**: `<magpie-agent>/core_docs/Tool_Usage_Patterns.md` (715 lines)
**Ground truth**: MAgPIE develop worktree `/tmp/magpie_develop_ro` + magpie-agent repo (for agent-internal path claims)

---

## Overall Verdict: MOSTLY ACCURATE
**Score: 9/10** (one Minor bug)

This is a meta-doc about *AI-agent tool usage* (path explicitness, Bash/Read/Write/Edit/Grep/Glob conventions, directory disambiguation). The pre-run advisory ("Never validated, 715 lines, meta-doc … most content is not GAMS-code-checkable; verify only concrete code-checkable claims") is **CONFIRMED**: the overwhelming majority of the doc is tool-usage advice with no GAMS interface variables, equations, consumer/populator sets, realizations, or parameter defaults to check. The handful of concrete, code-checkable claims (repo structure, the example variable `vm_nr_eff`, the M50 realization path, referenced audit/related files) all verify **except** a single non-existent path used repeatedly in examples.

There are **no** cross-module consumer/populator/dependency claims, **no** `file.gms:NN` citations, and **no** parameter/scalar default claims in this doc — so the Critical-prone classes (R20 anchor: wrong consumer set / inverted default; Major: citation drift) have **no surface area here**. MANDATEs 13/16/17/3 are not exercised by this doc.

---

## Code-checkable claims enumerated + verdicts

| # | Claim (doc line) | Verdict | Evidence |
|---|---|---|---|
| 1 | Directory diagram (453-468): `magpie/` parent has `AGENT.md` + `modules/50_nr_soil_budget/`; `magpie-agent/` has `AGENT.md` (SOURCE), `agent/commands/`, `modules/module_50.md` (AI doc), `core_docs/Tool_Usage_Patterns.md` | ✅ CORRECT | All paths exist (see verify cmds). AGENT.md correctly placed at magpie-agent ROOT (line 460), not in core_docs. |
| 2 | Realization path `modules/50_nr_soil_budget/macceff_aug22/equations.gms` (lines 210, 438, 502) | ✅ CORRECT | `ls` confirms dir + file. M50 has exactly one realization `macceff_aug22`, which is also the default (`config/default.cfg:1479`). |
| 3 | Example variable `vm_nr_eff` (8×: Grep/Glob examples lines 348-384) | ✅ CORRECT (real) | Declared `modules/50_nr_soil_budget/macceff_aug22/declarations.gms:12`; used in M50 equations/presolve/postsolve and M51. Used only as a search-pattern example — no consumer-set claim made. |
| 4 | Referenced incident file `audit/integrated/20251024_220843_global_bash_directory_navigation.md` (lines 679, 708) | ✅ CORRECT | File exists (10272 bytes). |
| 5 | "Related Documentation" refs: `AGENT.md`, `Response_Guidelines.md` (lines 706-708) | ✅ CORRECT | `magpie-agent/AGENT.md` and `core_docs/Response_Guidelines.md` both exist. |
| 6 | Parent deployed copy `../AGENT.md` = `/magpie/AGENT.md` (line 455, 485) | ✅ CORRECT | `/Users/.../magpie/AGENT.md` exists. |
| 7 | Path `core_docs/AGENT.md` used in command examples + "Learning From Real Examples" (lines 44, 58, 82, 648, 652, 665, 673) | ❌ **BUG (Minor)** | No such file. AGENT.md is at the magpie-agent root. The path was never tracked in git history. The real historical incident concerned `core_docs/AI_Agent_Behavior_Guide.md` (deleted commit a87b5f6). See TUP-B1. |
| 8 | No `file.gms:NN` citations | ✅ N/A | `grep -nE '\.gms:[0-9]+'` → zero hits. Nothing to drift-check. |
| 9 | No GAMS identifiers other than `vm_nr_eff` | ✅ verified | Full scan returned only `vm_nr_eff`. No equation/scalar/parameter names to verify. |

---

## Bugs Found

### TUP-B1 — Non-existent path `core_docs/AGENT.md` (7 occurrences); contradicts the doc's own directory diagram and misrepresents the real incident

- **Bug ID**: TUP-B1
- **Severity**: **Minor**
- **Trigger (§1 Minor)**: "Broken cross-reference / stale path that's recoverable" — a careful reader cross-checking against the directory diagram *in the same doc* (line 460 places AGENT.md at the magpie-agent root) would catch the inconsistency; it does not drive a wrong code edit or a MAgPIE modeling decision.
- **Class**: 7 (Broken cross-reference) — with a flavor of 5 (stale reference after rename: `AI_Agent_Behavior_Guide.md` → generic `AGENT.md`).
- **Tie-breaker applied**: The factual alteration of the historical "Example 1" narrative (the incident was about `AI_Agent_Behavior_Guide.md`, the doc says `AGENT.md`) nudges toward Major (misleads about a real event), but the path is recoverable and self-contradicted by the doc's own diagram, so the tie-breaker pulls down to Minor. `tier_uncertainty: true`.
- **Claim in doc** (line 648): `**What happened**: Failed to find \`core_docs/AGENT.md\`` — and the same path in command examples at lines 44 (`ls $(pwd)/core_docs/AGENT.md`), 58 (`ls core_docs/AGENT.md  # ✅ Now safe`), 82 (`wc -l core_docs/AGENT.md`), 652, 665 (`wc -l /path/to/magpie-agent/core_docs/AGENT.md`), 673 (`# Shows: ./magpie-agent/core_docs/AGENT.md`).
- **Reality in code/repo**:
  - `core_docs/AGENT.md` does not exist and was **never** git-tracked. AGENT.md lives at the magpie-agent repo root (`magpie-agent/AGENT.md`), exactly as the doc's own diagram states (line 460).
  - The historical incident this section narrates was about `core_docs/AI_Agent_Behavior_Guide.md` (per the source incident doc `audit/integrated/20251024_220843_global_bash_directory_navigation.md:20-26,72`). That file was deleted in commit a87b5f6 ("Complete Phase 1 consolidation"); its content was consolidated into `Response_Guidelines.md` / root `AGENT.md`.
  - Root cause: the 2025-11-29 "model-agnostic refactor" (doc footer) globally substituted `AGENT.md` for the old guide filename inside the example, producing a path that (a) never existed and (b) contradicts the diagram. Ironic failure mode: an agent literally running `ls core_docs/AGENT.md` from the examples gets "No such file or directory" — reproducing the exact "file doesn't exist" confusion the doc exists to prevent.
- **File evidence**:
  - Diagram (correct) `core_docs/Tool_Usage_Patterns.md:460` → `AGENT.md  ← SOURCE (edit this)` under `magpie-agent/`.
  - Actual location: `<magpie-agent>/AGENT.md` (root); `core_docs/AGENT.md` absent.
  - Source incident: `audit/integrated/20251024_220843_global_bash_directory_navigation.md:20` → "needed to check if `core_docs/AI_Agent_Behavior_Guide.md` existed".
- **verify_cmd + result**:
  - `ls /Users/.../magpie-agent/core_docs/AGENT.md` → `No such file or directory`.
  - `ls /Users/.../magpie-agent/AGENT.md` → exists (44932 bytes).
  - `git log --all --diff-filter=A -- 'core_docs/AGENT.md'` → empty (never added).
  - `grep -n 'AGENT.md\|core_docs' audit/integrated/20251024_220843_global_bash_directory_navigation.md` → references `AI_Agent_Behavior_Guide.md`, not `AGENT.md`.
  - `git log --oneline --diff-filter=D --all -- 'core_docs/AI_Agent_Behavior_Guide.md'` → `a87b5f6 Complete Phase 1 consolidation…`.
- **confirmed**: true.
- **Proposed fix**: Replace the example file in all 7 occurrences with a file that actually lives in `core_docs/` so the commands are runnable and consistent with the diagram. Recommended: use `core_docs/Response_Guidelines.md` (a real core_docs file). Specifically:
  - Line 44: `ls $(pwd)/core_docs/Response_Guidelines.md`
  - Line 58: `ls core_docs/Response_Guidelines.md  # ✅ Now safe`
  - Line 82: `wc -l core_docs/Response_Guidelines.md`
  - Lines 648, 652, 665, 673 (the "Example 1" narrative): either (a) rewrite to use `core_docs/Response_Guidelines.md`, or (b) restore historical fidelity by noting the file was the now-removed `core_docs/AI_Agent_Behavior_Guide.md` (consolidated into Response_Guidelines.md). Option (a) is cleaner for a how-to doc.
  - Do NOT change line 460 (diagram) — it is correct.

---

## Deferred (not code-verifiable / out of scope — no edit proposed)

- Generic tool-behavior assertions (Read requires absolute paths; Edit requires prior Read in-session; Read line-prefix format `spaces+line#+tab+content`; Grep/Glob path-parameter semantics; Glob uses glob not regex). These describe the *harness/tool* contract, not MAgPIE code — out of scope for a code audit. (They match this harness's documented behavior, but that is tooling, not GAMS ground truth.)
- All path-discipline advice (absolute paths, `pwd` checks, subshell `(cd …)`, quoting spaces, `&&` vs `;`, multi-method existence checks). Pure best-practice prose; not code-checkable.
- The `/path/to/...` and `/foo/bar` placeholders throughout — intentionally generic, not real-path claims.
- Doc-status footer "Updated 2025-11-29 (model-agnostic refactor)" — metadata, not verifiable against MAgPIE code.

---

## Notes on method / false-positive guards applied

- **Positive controls run**: `vm_nr_` sibling-token grep in M50 declarations confirmed the search worked before relying on any absence result; `vm_nr_eff` cross-checked by two methods (rg + grep -rln) and found in M50 + M51.
- **No phantom-consumer or omitted-consumer claims to assess** — the doc makes none. MANDATE 13/17 not triggered.
- **MANDATE 8/3**: M50 has a single realization `macceff_aug22` = default (`config/default.cfg:1479`); the doc's M50 examples cannot mislead about a non-default realization.
- **git history** used to distinguish "stale-but-once-true" from "fabricated": `core_docs/AGENT.md` was *never* real (fabricated by refactor substitution), whereas `core_docs/AI_Agent_Behavior_Guide.md` was real and is now deleted.
