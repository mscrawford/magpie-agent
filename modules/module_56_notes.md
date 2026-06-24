# Module 56 (GHG Policy) — Notes

**Backfilled 2026-05-25** from `audit/validation_rounds.json` R1-R3, R22-R24 findings (R6 Cluster C2).

---

## ⚠️ Warnings & Common Mistakes

### `vm_carbon_stock` is DECLARED in M56, not M52

A persistent answerer-side confusion: `vm_carbon_stock` looks like it should belong to M52 (Carbon), but it is **declared in M56** (`modules/56_ghg_policy/price_aug22/declarations.gms`). M52 only **reads** it. The producer/consumer roles:
- **M56** declares + does the GHG pricing math against it.
- **M52** computes carbon densities and reads `vm_carbon_stock` for the actual stock values.
- **M59** (SOM) is a populator (often missed in the producer list).

When citing the producer, cite M56. When citing the carbon-density math, cite M52. Don't merge.

### Default behavior: rice CH4 IS priced under `reddnatveg_nosoil`

Common hedging error: claiming rice CH4 might NOT be priced under the `reddnatveg_nosoil` policy realization. It IS priced by default. See `module_56.md:499` for the correct statement. Don't hedge on this — answer directly.

### MACC tech names: don't fabricate

Don't invent specific MACC technology names like "AWD" (alternate wetting/drying), "mid-season drainage", "improved cultivars". These are real real-world technologies but they're **not named individually in MAgPIE's MACC structure**. MAgPIE's MACCs are parameterized by abatement-cost curves, not by named techs. Cite the curve, not invented tech labels. (Source: R24 Q1-B4 answerer confabulation.)

### Unit drift: `USD17MER per Mg`, NOT `per Tg`

`im_pollutant_prices` and `f56_pollutant_prices` use **USD17MER per Mg** (megagram = tonne). Older documentation had `per Tg` (teragram = million tonnes) — a 6-orders-of-magnitude error. Fixed at `module_56.md:152, 158, 627, 675` in R24. If you see "per Tg" anywhere new, it's a regression.

### C-price-induced afforestation is reward-driven (keyed on `secdforest_vegc`), NOT on `forestry_vegc`

Common misconception: that endogenous (C-price-induced) afforestation/reforestation only fires — or only "counts" — when `forestry_vegc` is in the priced emission scope (`c56_emis_policy`). It does **not** work that way.

- The incentive is the afforestation reward `vm_reward_cdr_aff` (enters the objective as negative cost via M11), which values the projected sequestration `vm_cdr_aff` at the C price `p56_c_price_aff` (`price_aug22/equations.gms:74-77`).
- `p56_c_price_aff` is the CO2 price of the **single source named by `c56_cprice_aff`**, whose default is **`secdforest_vegc`** (`price_aug22/input.gms:87`; `price_aug22/preloop.gms:115`) — *not* `forestry_vegc`.
- `vm_cdr_aff` is the sequestration of the `"aff"` age-classes, computed in M32 (`modules/32_forestry/dynamic_may24/equations.gms:36-38`).

Consequences for answering:
- Endo A/R is triggered whenever the `secdforest_vegc` CO2 price is non-zero — and `secdforest_vegc` **is** priced under the default `reddnatveg_nosoil` policy — regardless of whether `forestry_vegc` is priced.
- `forestry_vegc` is merely the *realized* carbon stock of forestry land. It is deliberately left OUT of the default `reddnatveg_nosoil` priced scope for two reasons:
  1. **Perverse timber incentives** — pricing plantation carbon would over-incentivize timber-plantation *expansion* (to bank priced carbon) and would *penalize harvesting* plantations (harvest releases the priced stock). The model would then avoid harvesting plantations and shift timber-harvest pressure onto **natural forest** — the opposite of the intended land-use outcome.
  2. **Double-counting** — the A/R sequestration is already credited via the `vm_reward_cdr_aff` reward, so pricing the realized `forestry_vegc` uptake on top would count it twice.
- So to reason about whether A/R is incentivized, look at `c56_cprice_aff` and the `vm_reward_cdr_aff` chain — not at whether `forestry_vegc` appears in `c56_emis_policy`.

---

## 💡 Lessons Learned

- 2026-05-25: M56 cost chain is `q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emis_pricing` → `vm_emissions_reg`. Cite this chain when explaining GHG cost entry into the objective. (Source: R23 G2 audit.)
- 2026-05-25: M56 is one of the top-4 modification-safety hubs (alongside M10, M11, M17). Changes ripple via `vm_carbon_stock` declaration and the GHG pricing chain. (Source: R23 G1.)
- 2026-05-25: The unit-drift class (Tg vs Mg, mio vs '000) was a recurring R24 finding. When reading or writing M56 docs, double-check unit prose against `declarations.gms` parenthetical comments.
- 2026-06-24: C-price-induced A/R is driven by the reward `vm_reward_cdr_aff`, keyed on the `c56_cprice_aff` source (default `secdforest_vegc`) — NOT by pricing or capping `forestry_vegc`. `forestry_vegc` (realized forestry carbon stock) is intentionally excluded from the default priced scope: pricing it would (a) over-expand timber plantations and discourage harvesting them, shifting harvest onto natural forest, and (b) double-count the A/R reward credit. (Source: user correction.)

---

## 🧪 Real-World Examples

- **Carbon-pricing scenario routing**: see `agent/helpers/scenario_carbon_pricing.md` for `s56_*` switch combinations.

---

## See also

- `module_56.md` — primary documentation
- `module_52.md` — carbon densities (READS vm_carbon_stock from M56)
- `module_32.md` — forestry; `vm_cdr_aff` (afforestation sequestration) feeds the M56 reward
- `cross_module/carbon_balance_conservation.md` — carbon-pool accounting
- `agent/helpers/scenario_carbon_pricing.md` — scenario setup
