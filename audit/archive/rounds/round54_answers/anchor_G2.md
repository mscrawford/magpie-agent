# Anchor G2: How is `vm_carbon_stock` computed in Module 52, and where does it enter GHG-policy cost in Module 56?

**Method note**: Answered from magpie-agent documentation only (`modules/module_52.md`, `modules/module_56.md`, `modules/module_56_notes.md`, `cross_module/carbon_balance_conservation.md`). `modules/module_52_notes.md` does not exist (Read returned "File does not exist"). No raw `.gms` code was read this session; all file:line citations below are copied verbatim from the documentation files, not independently re-verified against source in this session.

---

## 0. Correcting the premise

**`vm_carbon_stock` is not computed in Module 52.** This is flagged explicitly as a recurring confusion in `modules/module_56_notes.md:9-16`:

> "A persistent answerer-side confusion: `vm_carbon_stock` looks like it should belong to M52 (Carbon), but it is **declared in M56** (`modules/56_ghg_policy/price_aug22/declarations.gms`). M52 only **reads** it."

Consistent with this, `modules/module_52.md`'s own interface-variable section lists `vm_carbon_stock` under **"Variables Read by Module 52"** (not "Written by"), sourced from "Module 56 declarations.gms" (`module_52.md:413-424`). `cross_module/carbon_balance_conservation.md:101` gives the declaration site precisely: `vm_carbon_stock(j,land,c_pools,stockType)` — 4-D, **declared at `modules/56_ghg_policy/price_aug22/declarations.gms:34`**.

So the question has two separable parts:
- **(A) Who actually populates `vm_carbon_stock`, and what does Module 52 do with it** (Module 52 is a *reader*, not the *producer*).
- **(B) Where `vm_carbon_stock` enters GHG-policy cost in Module 56** (directly — not via Module 52's emissions output).

---

## 1. Who populates `vm_carbon_stock` (per the docs — not verified in code this session)

Per `module_52.md:424` and `carbon_balance_conservation.md` §7.5 (lines 607-632), `vm_carbon_stock(j,land,c_pools,stockType)` is populated by the **land modules**, one land-type slice each:

| Land-type slice | Populating module | Doc-cited detail |
|---|---|---|
| `crop` | Module 29 (Cropland) | `q29_carbon` aggregates the separate `vm_carbon_stock_croparea` (computed by Module 30) into the crop slice — `modules/29_cropland/detail_apr24/equations.gms:39` (citation as given in `carbon_balance_conservation.md:610`) |
| `past` | Module 31 (Pasture) | — |
| `forestry` | Module 32 (Forestry) | — |
| `urban` | Module 34 (Urban) | Fixed to 0: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` — `modules/34_urban/exo_nov21/presolve.gms:8` (as cited in `carbon_balance_conservation.md:622`) |
| `primforest`/`secdforest`/`other` | Module 35 (Natural Vegetation) | — |
| `soilc` pool, **all** land types | Module 59 (SOM) | Assembled via `q59_carbon_soil` = topsoil `v59_som_pool` + subsoil density `i59_subsoilc_density` — `modules/59_som/cellpool_jan23/equations.gms:61-64` (as cited in `carbon_balance_conservation.md:557`); `i59_subsoilc_density` is itself an M59 parameter *derived from* M52's `fm_carbon_density`. |

**Module 58 (Peatland) does NOT populate `vm_carbon_stock`** — peatland emissions enter `vm_emissions_reg` directly via a separate path (`q58_peatland_emis`, `modules/58_peatland/v2/equations.gms:91-92`, per `carbon_balance_conservation.md:876`), bypassing the carbon-stock accounting entirely.

**`stockType` has two members**, `actual` and `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/sets.gms:212-213`, per `carbon_balance_conservation.md:101`). The populating equations are indexed over the free `stockType` set and fill **both** slices — this matters for §3 below.

**Module 52's actual contribution** to this chain is *upstream and indirect*: it is the **carbon-density data provider** consumed by the land modules — `fm_carbon_density(t_all,j,land,c_pools)` (base LPJmL densities, `module_52.md:480-484`) and the age-class parameters `pm_carbon_density_plantation_ac`, `pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac` (Chapman-Richards growth curves, `module_52.md:447-478`). `module_52.md:265-273` lists the consumers of `fm_carbon_density` as Modules 14, 29, 30, 31, 32, 35, 56, 59 — i.e., the land modules that build `vm_carbon_stock` are among the documented consumers of M52's density outputs, though the specific equations inside modules 29/31/32/35 that turn density × area into `vm_carbon_stock` were **not read this session** (they live in those modules' own doc/code files) and are not cited here beyond what `carbon_balance_conservation.md` itself already cites (the M29/M34/M59 lines above).

---

## 2. What Module 52 actually computes: `q52_emis_co2_actual`

Module 52 has exactly **one equation** (`module_52.md:36`, confirmed again in the file's "Verification Summary": `module_52.md:1108-1109`): `q52_emis_co2_actual`, declared at `declarations.gms:30`, defined at `equations.gms:16-19` (`module_52.md:302`).

Verified formula, quoted verbatim from `module_52.md:818-823`:

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
                 sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
                 (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);
```

This is a **stock-difference mass-balance calculation**, not a mechanistic emissions model:
- `pcm_carbon_stock(...,"actual")` = previous-timestep stock, `vm_carbon_stock(...,"actual")` = current-timestep stock — **both read the `"actual"` `stockType` slice specifically** (`module_52.md:901`, `equations.gms:19`).
- Difference divided by `m_timestep_length` annualizes the flow.
- Output: `vm_emissions_reg(i2,emis_oneoff,"co2_c")` — this variable is **declared in Module 56**, written by Module 52 (`module_52.md:435-443`).
- Sign convention: stock loss (`pcm > vm`) → positive emission; stock gain → negative (sequestration) (`module_52.md:326-328`).

**Carry-forward of `pcm_carbon_stock`** (`module_52.md:431`, also `module_56.md:581`): after each solve, realized `vm_carbon_stock` becomes next timestep's `pcm_carbon_stock`, split by pool — above-ground pools (`vegc`,`litc`) carried forward in **Module 56** (`modules/56_ghg_policy/price_aug22/postsolve.gms:8`); soil pool (`soilc`) carried forward in **Module 59** (`modules/59_som/cellpool_jan23/postsolve.gms:13`, or `static_jan19/postsolve.gms:9`). The soil carry-forward was only added in develop commit `931db85c4` (2026-06-25); before that, `soilc` stayed frozen at its preloop-initialized value, so the soil term in `q52_emis_co2_actual` computed a cumulative-since-init change rather than a per-timestep flux. The docs note this was inconsequential for **default** runs because the default policy `c56_emis_policy = reddnatveg_nosoil` excludes soil carbon from pricing anyway.

---

## 3. Where `vm_carbon_stock` enters GHG-policy cost in Module 56

**This is the crux of the question, and the documentation is explicit that this does NOT route through Module 52's `q52_emis_co2_actual` / `vm_emissions_reg` output.** From `cross_module/carbon_balance_conservation.md:583` (§7.3):

> "Both are priced in Module 56 - but by **different paths**: CH₄ flows through `vm_emissions_reg` into `q56_emis_pricing`..., whereas CO₂ is **recomputed inside M56** from `pcm_carbon_stock - vm_carbon_stock` in `q56_emis_pricing_co2`.... M56 does **not** consume M52's `vm_emissions_reg(...,"co2_c")`: M52 and M56 are **parallel readers** of `vm_carbon_stock`, not a serial producer→consumer chain."

`module_56.md` §2.2 (lines 88-92) makes the same point under "Architectural Note — Direct Carbon Stock Pathway":

> "CO2 pricing is calculated **directly from `vm_carbon_stock`**, intentionally **bypassing `vm_emissions_reg`**.... Contrast with annual emissions (Section 2.1): `q56_emis_pricing` routes CH4, N2O, and other recurring gases through `vm_emissions_reg`. `q56_emis_pricing_co2` does NOT."

### 3.1 The equation: `q56_emis_pricing_co2` (`equations.gms:19-22`)

Verbatim from `module_56.md:82-86`:

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
                 sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
                 (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))/m_timestep_length);
```

Note the structural difference from Module 52's equation in §2 above: `pcm_carbon_stock` still reads the `"actual"` slice, but the **current-period** term reads `vm_carbon_stock(...,"%c56_carbon_stock_pricing%")` — a **configurable** `stockType`, not hardcoded to `"actual"`.

- `c56_carbon_stock_pricing` options (`module_56.md:108,114-116`): `"actual"` (all stock changes, including afforestation establishment) vs. **`"actualNoAcEst"` (default)**, which excludes afforestation establishment from pricing specifically to avoid double-counting with the separate CDR reward (§3.4 below).
- `cross_module/carbon_balance_conservation.md:101` draws out the consequence directly: "Module 52 accounts CO₂ from the **`"actual"`** slice..., while Module 56 **prices** CO₂ from `%c56_carbon_stock_pricing%`, which defaults to **`actualNoAcEst`**.... In a default run the **priced** CO₂ is therefore not computed from the same stock slice as the **reported** CO₂." (Reported = M52's `q52_emis_co2_actual`; priced = M56's `q56_emis_pricing_co2`.) These two numbers can diverge by construction, even though both are ultimately built from `vm_carbon_stock`/`pcm_carbon_stock`.

### 3.2 From `v56_emis_pricing` to cost

For the `emis_oneoff` CO2 slice just computed, cost is `q56_emission_cost_oneoff` (`equations.gms:45-52`), quoted from `module_56.md:170-177`:

```gams
q56_emission_cost_oneoff(i2,emis_oneoff) ..
                 v56_emission_cost(i2,emis_oneoff) =e=
                 sum(pollutants,
                     v56_emis_pricing(i2,emis_oneoff,pollutants)
                     * m_timestep_length
                     * sum(ct,
                       im_pollutant_prices(ct,i2,pollutants,emis_oneoff)
                      * pm_interest(ct,i2)/(1+pm_interest(ct,i2))));
```

This re-multiplies the annualized rate by `m_timestep_length` (recovering total-timestep emissions), then by price `im_pollutant_prices`, then by the infinite-horizon annuity factor `r/(1+r)` (`pm_interest` from Module 12) — converting a one-time stock-change cost into an annualized payment, so deforestation isn't artificially cheap relative to recurring costs (`module_56.md:192-208`).

Total cost aggregation, `q56_emission_costs` (`equations.gms:56-58`, `module_56.md:219-221`):

```gams
q56_emission_costs(i2) ..
                 vm_emission_costs(i2) =e=
                 sum(emis_source, v56_emission_cost(i2,emis_source));
```

This sums over **all** `emis_source` (both `emis_annual` and `emis_oneoff` members), so the carbon-stock-derived CO2 cost and the vm_emissions_reg-derived CH4/N2O costs are combined into one regional total here. `vm_emission_costs(i)` is then **provided to Module 11 (Costs)**, entering the objective function (`module_56.md:564-568`, `1019`); it is also read post-solve by Module 15 (food) for GHG-tax revenue recycling (`modules/15_food/anthro_iso_jun22/intersolve.gms:23`, per `module_56.md:566`).

### 3.3 What is actually priced by default

The price `im_pollutant_prices(ct,i2,pollutants,emis_oneoff)` used in §3.2 is constructed in `preloop.gms:35-123` through the multi-stage process documented in `module_56.md` §3 (scenario selection → dev-state scaling → temporal fader → CO2 reduction factor → historical zeroing/floor → CH4/N2O caps → **emission-policy-matrix multiplication**). The last stage, `f56_emis_policy`, determines *which* `emis_land` sources actually carry a non-zero CO2 price. Under the **default** policy `reddnatveg_nosoil` (`module_56.md:499,662`): CO2 is priced for `vegc`+`litc` of `primforest`, `secdforest`, and `other` land, plus peatland — **not** `soilc`, and **not** `crop`/`past`/`forestry` carbon stocks. So although `q56_emis_pricing_co2` sums over all `emis_land(emis_oneoff,land,c_pools)` combinations, most of that sum is zeroed out by price for the non-natural-vegetation, non-CO2-priced pools under the default policy.

Also note the price floor: `s56_minimum_cprice = 3.67` USD17MER/tC applied unconditionally (`price_aug22/preloop.gms:74`, per `module_56.md:961`), and zeroing for years ≤ `sm_fix_SSP2` (default 2025) and until `c56_mute_ghgprices_until` (default 2030) — so **default reference runs carry an economically negligible CO2 price** despite the equation chain above being live in every run.

### 3.4 A separate, non-`vm_carbon_stock` pathway: the CDR/afforestation reward

For completeness, Module 56 has a **second, independent** cost-adjacent mechanism that is easy to conflate with the `vm_carbon_stock` pricing pathway but is **not** driven by `vm_carbon_stock`: `q56_reward_cdr_aff_reg` / `q56_reward_cdr_aff` (`equations.gms:67-79`, `module_56.md:246-260`). This rewards **`vm_cdr_aff(j,ac,aff_effect)`** — expected carbon removal by age class, computed in **Module 32** (Forestry), not Module 52 — valued at the age-class-specific future price `p56_c_price_aff`, itself keyed on the single source named by `c56_cprice_aff` (default `secdforest_vegc`, per `module_56_notes.md:30-43`). The result `vm_reward_cdr_aff(i)` enters Module 11 with a **negative** sign (reduces cost), separately from `vm_emission_costs`. `module_56.md` §7.2 (line 722) is explicit: Module 56 "**DOES reward** CDR calculated by Module 32 (Forestry) via `vm_cdr_aff`" — this is carbon-*flow* accounting from the forestry module, not a read of the `vm_carbon_stock` interface variable. `module_56_notes.md` warns specifically against assuming this reward is gated on `forestry_vegc` pricing status — it isn't; it fires whenever the `secdforest_vegc` CO2 price is non-zero, independent of `c56_emis_policy`.

---

## 4. A documentation-internal inconsistency worth flagging

`modules/module_56_notes.md:49` (Lessons Learned, dated 2026-05-25) states:

> "M56 cost chain is `q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emis_pricing` → `vm_emissions_reg`. Cite this chain when explaining GHG cost entry into the objective."

Read literally as a directional data-flow chain, this is in tension with the more detailed, explicitly-verified text in `module_56.md` §2.1-2.2 (✅ "Fully Verified 2025-10-12" per the file header) and with `carbon_balance_conservation.md`'s explicit "parallel readers, not a serial producer→consumer chain" statement quoted in §3 above. Per the primary equations (§2.1/§2.2 of `module_56.md`):
- `q56_emis_pricing_co2` writes `v56_emis_pricing` for the `emis_oneoff`/`co2_c` slice, reading `vm_carbon_stock`/`pcm_carbon_stock` directly — it does **not** feed into or from `q56_emis_pricing`.
- `q56_emis_pricing` is a **separate** equation that writes a **different domain slice** of `v56_emis_pricing` (the `emis_annual` gases), reading `vm_emissions_reg` as its RHS.

I'm reporting both because I have not independently re-verified either against source this session (no `.gms` reads permitted for this task) — flagging the discrepancy rather than silently picking one, per the anti-confabulation instruction for this task. The equations quoted verbatim in `module_56.md` §2.1/§2.2, marked "Fully Verified," are the more load-bearing citation for describing the actual cost-entry mechanism; the notes-file bullet reads more like a compressed list of the entities involved in "the CO2 cost chain" than a literal sequential pipeline.

---

## 5. Summary answer

1. **`vm_carbon_stock` is not computed by Module 52.** It's declared in Module 56 (`price_aug22/declarations.gms:34`) and populated by the land modules — M29 (crop, folding in M30's `vm_carbon_stock_croparea`), M31 (pasture), M32 (forestry), M34 (urban, fixed to 0), M35 (primforest/secdforest/other), M59 (soilc, all land types). M58 (peatland) does not populate it.
2. **Module 52 reads `vm_carbon_stock`** (and `pcm_carbon_stock`, both `"actual"` `stockType`) in its one equation, `q52_emis_co2_actual` (`normal_dec17/equations.gms:16-19`), to compute `vm_emissions_reg(i,emis_oneoff,"co2_c")` as an annualized stock-difference. Module 52's own contribution to the *stock* itself is upstream and indirect: it supplies the carbon-density inputs (`fm_carbon_density`, `pm_carbon_density_plantation_ac`, `pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac`) that the land modules consume when building `vm_carbon_stock`.
3. **`vm_carbon_stock` enters GHG-policy cost in Module 56 directly, not via Module 52's `vm_emissions_reg` output.** `q56_emis_pricing_co2` (`price_aug22/equations.gms:19-22`) independently recomputes `pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"%c56_carbon_stock_pricing%")` (default slice `actualNoAcEst`, differing from M52's hardcoded `"actual"`), writing `v56_emis_pricing`. That feeds `q56_emission_cost_oneoff` (`:45-52`, annuitized via `pm_interest`), which feeds `q56_emission_costs` (`:56-58`) → `vm_emission_costs(i)` → Module 11 → the objective function. A separate, `vm_carbon_stock`-independent mechanism (`q56_reward_cdr_aff`, keyed on Module 32's `vm_cdr_aff`) rewards afforestation and should not be conflated with this pathway.

---

## Sources

- 🟡 `modules/module_52.md` (magpie-agent docs; last verified 2026-05-16 per file footer)
- 🟡 `modules/module_56.md` (magpie-agent docs; "✅ Fully Verified 2025-10-12" per file header/footer)
- 🟡 `modules/module_56_notes.md` (backfilled 2026-05-25 from `audit/validation_rounds.json` R1-R3, R22-R24)
- 🟡 `cross_module/carbon_balance_conservation.md` (created 2025-10-22; conservation-law structure "verified against MAgPIE 4.x architecture")
- `modules/module_52_notes.md` — does not exist (checked this session, Read tool returned "File does not exist")
- No raw `.gms` files were read this session (excluded by task instructions); all `file:line` citations above are copied verbatim from the four documentation files, not independently re-verified against source code this session.
