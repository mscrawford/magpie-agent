# R51 item 3 — tighter class-B find-rate + MANDATE-21 mitigation validation (2026-06-11)

Both runs on Opus; isolation verified by tool-call transcripts (deep2 unmitigated: 205 calls, 0 forbidden; mitigated: 149 calls, 0 forbidden). Injected docs in `/tmp/r51_deep2/`; repo docs untouched.

## A. Tighter find-rate, split by class (UNMITIGATED auditor prompt)

5 internally-consistent single-statement direction injections, one bug per doc:

| Doc | Class | Injected (reversed) | Found? |
|---|---|---|---|
| dataflow_chain | B (serial chain) | "Flow: 14 → 30 → 17" → "17 → 30 → 14" | **MISSED** |
| modsafety_chain | B (serial chain) | "30 → vm_prod → 17 → vm_prod_reg → 21" reversed | **MISSED** |
| circular_costchain | B (abstract causal) | "Prices → Emission costs → Total costs" reversed | **MISSED** |
| dataflow_producer | C (producer) | pm_carbon_density owner M52 → M32 (FULLY consistent) | FOUND (Critical) |
| moddep_forestry | C (producer) | pm_demand_forestry "(73 → 32)" → "(32 → 73)" | FOUND (Major) |

**Class B: 0/3. Class C: 2/2.** Combined with the prior deep run, **class-B find-in-long-doc rate = 0/4 (0%)**, class-C = 3/3 across the session.

Two things this nails down:
- **The B-vs-C split is real and robust.** The blind spot is specifically causal/data-flow DIRECTION (serial-vs-parallel, chain direction), which needs non-local inference and has no single-file ground truth. Producer attribution (class C) is reliably caught — it's a `declarations.gms` grep.
- **The prior "internal-inconsistency confound" is resolved.** The dataflow_producer class-C injection was made FULLY internally consistent this time (owner + both citations flipped to M32, no un-edited sibling) and was STILL caught — so class C is caught by CODE, not by spotting self-contradiction.

## B. Does MANDATE 21 close the gap? (MITIGATED — both-endpoints instruction added to the prompt)

Re-ran the 3 missed class-B docs with the MANDATE-21 both-endpoints instruction injected into the auditor prompt:

| Doc | Class B subtype | Unmitigated | Mitigated |
|---|---|---|---|
| dataflow_chain | inter-module VARIABLE arrow | MISSED | **CAUGHT (Major)** — grepped both endpoints, found 17 is the sink not source |
| modsafety_chain | inter-module VARIABLE arrow | MISSED | **CAUGHT (Major)** — both arrows reversed, verified vm_prod (30→17) + vm_prod_reg (17→21) |
| circular_costchain | ABSTRACT causal/economic chain | MISSED | **STILL MISSED** |

**Verdict: MANDATE 21 works for the dominant subclass.** Inter-module variable data-flow direction recovered from 0/2 to **2/2** — the explicit both-endpoints procedure makes the auditor grep producer + consumer and catch the reversal. The fix is validated for the code-grounded form.

**Bounded residual:** the abstract causal/economic-sequencing claim (`Prices → Emission costs → Total costs` reversed) was still missed even WITH the instruction — because it has no variable endpoints to grep; the both-endpoints procedure does not apply. That subclass needs a different test (which quantity is the exogenous INPUT vs the derived OUTPUT). Added that as a note to MANDATE 21.

## C. Side-finding — 3 real latent doc bugs surfaced + fixed

The unmitigated dataflow_chain auditor missed the planted direction bug but surfaced 3 genuine pre-existing input-filename errors in `core_docs/Data_Flow.md` §1.2 (the validator does not check input-data filenames). All verified by hand against the develop manifests and FIXED:
- `f15_supply2intake_ratio_FAO.cs3` → `f15_supply2intake_ratio_FAO_iso.cs3` (input.gms:250).
- `f09_governance_indicator.cs3` (nonexistent) → `f09_development_state.cs3` (best match for "Development indicators"; 09_drivers manifest).
- `f09_urbanpop_grid.cs3` (nonexistent) → `f09_urban_iso.csv` (the real urban driver, ISO-level not gridded).

## Net

- Class-B (causal-direction) find-in-long-doc rate is ~0% unmitigated — a robust, narrow blind spot.
- MANDATE 21's both-endpoints check closes it for inter-module VARIABLE direction (2/2), the dominant code-grounded form — the committed fix is validated, not just asserted.
- A smaller residual remains for ABSTRACT causal-sequencing claims (input-vs-derived test added to MANDATE 21).
- Bonus: 3 real input-filename doc bugs found and fixed.
