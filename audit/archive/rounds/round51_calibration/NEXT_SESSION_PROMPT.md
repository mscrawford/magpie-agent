# R51 follow-up — paste this into a fresh session when you have compute

> Reminder stored 2026-06-11. The R51 auditor-calibration round (see this dir + `validation_rounds.json` round 51 + memory `magpie_agent_auditor_calibration_r51`) located the flywheel auditor's one real blind spot: **cross-module causal/data-flow-DIRECTION claims that need non-local inference** (the carbon_balance soilc serial-vs-parallel claim was missed TWICE in find-in-long-doc audits, caught 100% when pointed at it). These are the agreed next steps. Item 1 is the concrete deliverable; the rest are optional / gated.

---

## PASTE-ABLE PROMPT

Continue the R51 auditor-calibration follow-up for the magpie-agent. Context is in `audit/archive/rounds/round51_calibration/` (read `FOLLOWUP_RESULTS.md` and `PHASE_C_coverage_map.md` first) and memory `magpie_agent_auditor_calibration_r51`. Do these in order; stop after item 1 unless I say otherwise.

**1. (PRIMARY) Write the both-endpoints check into `agent/helpers/verifiers.md` as a new MANDATE — the class-B causal-direction mitigation.**
- The rule: when auditing OR writing any cross-module data-flow / producer-consumer claim ("A produces V, consumed by B", "A flows to / hands off to B", "M receives V from N"), open BOTH endpoints in code — the producer's `declarations.gms` + populating equation AND the consumer's equation — and confirm the downstream module reads the upstream's OUTPUT, not a shared interface variable both read independently. **Default to "parallel readers, not a serial hand-off" until the code proves a real hand-off.**
- Worked example (the bug missed twice): soilc CO2. `vm_carbon_stock` is read DIRECTLY by both M52 (`q52_emis_co2_actual`) and M56 (`q56_emis_pricing_co2`, price_aug22/equations.gms:22) — they are PARALLEL readers; M56 does NOT receive M52's emission output. A doc saying "M52 forwards/hands off to M56" is wrong.
- Follow verifiers.md's existing MANDATE format + numbering. After editing: run `bash scripts/validate_consistency.sh` (must stay clean), and if (and only if) you touched AGENT.md, redeploy with `cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md`. verifiers.md itself is auto-loaded, not a deployed copy. Commit to the magpie-agent repo by explicit path. Also consider adding the same both-endpoints line to the `doc_audit_round.workflow.js` GREP_GUARD so live rounds enforce it.

**2. Decide the 2 borderline doc items found in the real-doc direction audit** (`core_docs/Module_Dependencies.md`):
- `:198` — "56_ghg_policy -> 32_forestry (via vm_carbon_stock pricing)": the forestry slice of vm_carbon_stock is populated BY M32 (32 -> 56); M32 reads no direct pricing var from M56. It sits in an explicitly-bidirectional feedback-cycle framing, so it's defensible — either tighten the per-variable direction label or leave with a one-line rationale.
- `:212` — 14_yields lists 70_livestock as a "Key Dependency", but there's no direct interface variable; the manure->yield feedback is indirect (55_awms -> 50_nr_soil_budget). Either relabel as indirect or leave.

**3. (OPTIONAL, compute-heavy) Tighten the class-B find-rate estimate.** The deep find-rate test was n=3 and one injection (Data_Flow) had a self-contradiction flaw, so the clean class-B sample is small. Re-run with ~6-8 internally-CONSISTENT single-statement causal/data-flow-direction injections (verify each is genuinely one wrong statement with no un-edited sibling) to get a tighter find-rate. Reuse `inject_deep.py` + `longdoc.workflow.js` (`root` arg). Prediction: materially below 100%.

**4. (GATED) Fable/Mythos auditor round — only if Fable is actually available.** This workspace downgrades Fable->Opus via the nitrogen safeguard (memory `magpie_workspace_fable_downgrade_nitrogen`); confirm the LIVE model first. If a Fable/Mythos auditor is genuinely available, point it ONLY at (a) class-B causal-direction in long docs without the forced procedure, and (b) the unknown-unknown class via open-ended "what's wrong in this whole doc" auditing — NOT per-claim known bugs (Opus is already ~100% there).

**5. Push decision.** The R51 commits (`12aa462`, `bd680c2`, `5ab03d1`) are local on `develop`, not pushed. Decide whether to push to the mscrawford fork / open a PR (never push to pik-piam).

---

*Standing method reference (global memory): `feedback_calibrate_llm_judge_fnr` — how to calibrate any LLM judge/auditor by measuring its FNR, and the ensemble-with-forced-check way to trust a null.*
