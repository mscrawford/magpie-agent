# R51 Follow-ups #1 + #2 (2026-06-11)

Both run on Opus (Fable still downgraded by the nitrogen safeguard). Isolation verified by tool-call transcripts on every run (0 forbidden-path accesses).

## Follow-up #1 - find-rate on DEEP single-statement Layer-2 claims

B-prime's residual was single-statement deep-Layer-2 claims (no redundancy backstop). This run injected 3 internally-consistent single-statement reversals (one wrong claim each) across the hardest classes and measured the full-doc find-rate.

| Doc | Class | Injected (reversed) claim | Found? | How |
|---|---|---|---|---|
| carbon_balance | B - causal / data-flow direction | soilc flows serial M52 -> M56 (truth: parallel readers) | **MISSED** (CLEAN, 0 findings) | - |
| Module_Dependencies | D - default-state | vm_landdiff consumed by the *default* nlp_apr17 (truth: only non-default lp_nlp_apr17) | FOUND (Major) | grep nlp_apr17/solve.gms -> no vm_landdiff; clean code-grounded catch |
| Data_Flow | C - producer attribution | pm_carbon_density_secdforest_ac owned by M32 (truth: M52) | FOUND (Critical) | BUT my injection left "set in M52" un-edited -> self-contradiction the auditor used; NOT a clean data point |

**Find-rate 2/3, but the clean signal is sharper than the headline:**
- **Class B (causal/data-flow direction) was MISSED again** - the second time the carbon_balance soilc serial-vs-parallel bug survived a thorough full-doc audit (this run: 21 files consulted, everything else verified, verdict CLEAN). Robust blind spot.
- **Class D (default-state) was CAUGHT cleanly** - because falsifying it is LOCAL: grep one realization's solve.gms.
- The distinction is now precise: the auditor's find-in-long-doc blind spot is specifically **causal/data-flow-DIRECTION claims that require NON-LOCAL multi-module inference to falsify** (you must reconstruct that the downstream module reads the shared interface variable *directly*, not the upstream module's output - unverifiable from any single file). Deep-Layer-2 claims that ARE locally checkable (default-state via one solve.gms; producer via one declarations.gms) get caught even in long docs.
- Methodological self-correction: my Data_Flow injection was not fully internally consistent (residual "set in M52"), so it is not a clean test - logged honestly. The robust data points are carbon_balance (missed, clean) and Module_Dependencies (caught, clean).

## Follow-up #2 - real-doc direction audit (3 independent adversarial agents)

Probe: do any GENUINE cross-module direction errors exist live in the real docs? First attempt was a single agent (found none) - but a single same-tier null is exactly the low-confidence case this whole round is about, especially on the class we just showed is a blind spot. So it was re-run as **3 independent agents (one per doc), each forced to do the gap-closing procedure**: for every arrow, open BOTH endpoints and confirm the downstream reads the upstream's OUTPUT (not a shared variable both read), defaulting to "parallel until code proves a hand-off."

**Result: NO genuine direction errors in carbon_balance_conservation.md, Data_Flow.md, or Module_Dependencies.md.** All three agents independently verified the directions hold, including:
- The known-trap soilc/CO2 arrow: the real doc (carbon_balance:615 "All populated slices flow to Module 52 and Module 56") correctly frames M52/M56 as PARALLEL readers of vm_carbon_stock. M56's q56_emis_pricing_co2 re-reads the stock directly (price_aug22/equations.gms:22), differing from M52 only by the stockType slice - so it cannot be a hand-off. Correctly documented.
- The 14 -> 30 -> 17 chain is genuinely serial (M17 reads M30's vm_prod, not M14's output) - verified by both-endpoints check (M17 has zero reads of M14's vm_yld/i14_yields_calib).

**Two borderline minor items surfaced (NOT reversed arrows; recorded for the user, not auto-fixed):**
1. `Module_Dependencies.md:198` - "56_ghg_policy -> 32_forestry (via vm_carbon_stock pricing)": the forestry slice of vm_carbon_stock is populated BY M32 (LHS of q32_carbon), and M32 reads no direct pricing variable from M56, so the named-variable flow is 32 -> 56. Sits inside an explicitly-bidirectional feedback-cycle framing, so defensible, but the per-variable direction label is loose.
2. `Module_Dependencies.md:212` - 14_yields lists 70_livestock as a "Key Dependency", but there is no direct interface variable by which M14 reads from M70; the manure->yield feedback is indirect (55_awms -> 50_nr_soil_budget). Indirect feedback labeled as a direct dependency.

## What #1 + #2 together establish

- The auditor's find-in-long-doc blind spot is **narrow and specific**: causal/data-flow-direction claims requiring non-local inference (class B). Everything else - including locally-checkable deep-Layer-2 claims - is caught.
- The **real corpus is clean on direction**: 3 independent adversarial agents using the gap-closing procedure found no live direction error. So the injection-test residual is a **capability gap, not a known current bug**. Honest caveat: the same gap that misses injected class-B bugs could in principle miss a real one; the forced both-endpoints procedure + 3-agent ensemble is the mitigation that makes this null trustworthy, not a proof of absence.
- **Method lesson (demonstrated in-flight)**: a single same-tier audit's null is low-confidence on a known-blind-spot class; an ensemble of independent agents each running the specific gap-closing check is the right way to trust a null. This is the practical mitigation for the residual - cheaper than a stronger model, and it runs on Opus today.

## Net recommendation

- **Standing practice**: when auditing cross-module data-flow, force the both-endpoints check (open producer AND consumer equations; default to parallel-not-serial). Add this to the auditor's MANDATE set / GREP_GUARD as the class-B mitigation.
- A stronger auditor (Fable/Mythos) still adds value ONLY on (a) class-B causal-direction in long docs without the forced procedure, and (b) the untestable unknown-unknown class. Everything else is covered by mechanical checks + the per-claim/locally-checkable auditor + the ensemble-with-forced-check practice.
