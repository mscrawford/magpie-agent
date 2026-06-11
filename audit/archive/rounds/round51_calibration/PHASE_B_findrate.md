# R51 Phase B-prime — find-in-long-doc find-rate

**Question**: when a bug is NOT pointed at — buried as one wrong claim among hundreds in a full doc — does the auditor FIND it? (Phase 0 measured *verify-when-pointed*; this measures *find-in-context*, the production-relevant number.)

**Method**: 7 real docs, each given exactly one inverted code-fact (injections live only in `/tmp/r51_longdoc/`; repo docs untouched). Each audited whole by 1 isolated Opus auditor, no pointing question. Isolation verified: 232 tool calls, 0 forbidden-path accesses.

## Raw result: 6 / 7 found (86%, Wilson 95% [49%, 97%])

| Doc | Injected bug (class) | Found? | Caught as |
|---|---|---|---|
| module_30 | croparea default = detail_apr24 (wrong-default) | YES | Critical |
| module_42 | water_demand default = agr_sector_aug13 (wrong-default) | YES | Critical |
| module_70 | livestock default = fbask_jan16_sticky (wrong-default) | YES | Minor |
| module_51 | vm_manure_recycling declared by M50 (producer attribution) | YES | Major |
| module_38 | vm_cost_prod_crop consumed by M17 (consumer attribution) | YES | Critical |
| module_13 | vm_tau at super-region h (index domain / scope) | YES | Major |
| **carbon_balance** | **soilc CO2 serial M52->M56 (causal data-flow direction)** | **NO (verdict CLEAN, 0 findings)** | — |

## The miss is genuine, high-quality, and the most informative data point

The carbon_balance auditor was NOT a dropped/errored agent. It did a thorough audit: 30 paths consulted (incl. `52_carbon`, `56_ghg_policy/price_aug22`, `59_som`, all six populator modules), verified the G2 populator set, q52_emis_co2_actual, the vm_carbon_stock declaration, SOM equations and scalars, and explicitly noted "interface arrows all correct" — then returned **CLEAN**. It looked at the data-flow arrows and judged the injected serial one correct. This is the **same bug** the per-claim auditor caught at 100% in Phase 0 (fixture_09).

## Confound I must flag: internal-inconsistency aided the 6 catches

Six of the seven injections left a *sibling* statement of the fact un-edited elsewhere in the doc, so the injected doc **contradicted itself** (e.g. module_30 header said detail_apr24 while the body still said simple_apr24; module_38 line 33 still said "Module 11" while line 121 was flipped to "Module 17"). The auditors' notes explicitly leaned on this ("self-contradicted by the doc's own body"). So those catches were over-determined: code-check AND self-contradiction. For the wrong-default cases the code-check alone (a single `config/default.cfg` read) suffices, so they would likely be caught anyway — but the find-rate is still inflated as a pure code-only-find measurement.

**carbon_balance was the cleanest test**: its single edit was internally *consistent* (the serial framing does not contradict the doc's other statements that M52 reads the stock), so the auditor had NO self-contradiction shortcut — catching it required the multi-file semantic inference that M56 reads `vm_carbon_stock` *directly* (price_aug22/equations.gms:19-22), not via M52. It missed it.

## Interpretation

- **Find-rate < verify-rate is demonstrated.** A thorough full-doc audit (100% verify-when-pointed) missed a real bug it would have caught when pointed.
- **The miss is the deepest Layer-2 class** (Phase C class B: causal / data-flow direction) — the one that is (a) invisible to the mechanical layer, (b) not catchable by a single-file lookup, and (c) not flagged by self-contradiction. The 6 catches were all Layer-1-adjacent (wrong-default / attribution / scope = single grep or default.cfg read) and self-contradicting.
- **So the production residual concentrates in deep Layer-2 claims** (causal direction, multi-module data-flow, multi-file semantic inference) that are NOT pointed at. Everything else (existence, defaults, citations, counts, simple attributions) is caught either mechanically (Layer 1) or by the auditor even in-context.

## Caveat / how to tighten

n=7 gives a wide CI, and the internal-inconsistency confound means the 86% is an *upper bound* on the code-only find-rate. A clean follow-up would: (a) make every injection internally CONSISTENT (edit all sibling statements coherently), and (b) use more injections concentrated in the deep Layer-2 classes (causal direction, default-state, solution-level). Prediction: the find-rate on internally-consistent deep-Layer-2 injections is materially below 100% — i.e. the real residual the carbon_balance miss points to.

## Bottom line (with Phase 0 + C)

The same-tier auditor is **not** blind: per-claim it catches everything (Phase 0), and in-context it catches every Layer-1-adjacent class. The genuine residual is the **deep-Layer-2-claim x not-pointed-at** cell: a causal/data-flow-direction error, internally consistent, buried in a long doc, can survive a thorough audit. That is precisely where a stronger auditor (Fable/Mythos) or a targeted "trace every cross-module data-flow arrow" coverage pass would add value — and precisely the kind of bug the original Fable plan was meant to hunt.
