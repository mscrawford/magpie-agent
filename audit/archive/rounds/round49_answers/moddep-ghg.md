# Carbon / GHG-Policy Cluster: Dependency Analysis
## Modules 52 (carbon), 56 (ghg_policy), 57 (maccs)

**Sources**: `modules/module_52.md`, `modules/module_56.md`, `modules/module_57.md`, `core_docs/Module_Dependencies.md`

---

## 1. What the Module_Dependencies.md doc says about this cluster

Module_Dependencies.md characterises the cluster in three places:

**Centrality table** (§1.2): module 56 is ranked #3 overall with "16 total connections: 13 provided-to, 3 depends-on". Module 52 is characterised in §7.3 as "Medium Risk — 1 dependency but 4 consumers." Module 57 is not in the top-10 centrality table.

**Architectural layers** (§3.1): module 52 sits in Layer 4 ("Environmental Accounting"), while module 56 and 57 sit together in Layer 5 ("Economic/Policy").

**Degradation-system subsystem table** (§5.1): shows "52_carbon — 5 total connections — depends on 56_ghg_policy."

**Forest-carbon circular dependency** (§4.1): `32_forestry ←→ 30_croparea ←→ 10_land ←→ 35_natveg ←→ 56_ghg_policy` — a 5-module feedback through land competition and carbon pricing. Module 52 appears in the associated §4.2 chain: "56_ghg_policy → 32_forestry (via vm_carbon_stock pricing)".

**Circular dependency in §12** of module_56.md: `56 → 32 → 10 → 52 → 56`.

Module_Dependencies.md makes **no direct mention of module 57** beyond the Layer 5 placement and the §6.2 risk-assessment note. The document makes no explicit statement listing the intra-cluster edges (52↔56 and 56→57).

---

## 2. The actual edges as documented in the module files

### 2.1 Edge: Module 56 → Module 52 (56 declares; 52 reads)

Module 56 **declares** the carbon-stock variables. Module 52 **reads** them.

| Variable | Declared by | Consumed by | Description | Citation |
|----------|------------|-------------|-------------|---------|
| `vm_carbon_stock(j,land,c_pools,stockType)` | M56 `declarations.gms:34` | M52 `equations.gms:16` | Current-timestep carbon stocks (mio. tC) | module_56.md §4.1; module_52.md Interface Variables §Variables Read |
| `pcm_carbon_stock(j,land,c_pools,stockType)` | M56 `declarations.gms` | M52 `equations.gms:16` | Previous-timestep carbon stocks (mio. tC) | module_52.md Interface Variables §Variables Read |

These two variables appear together in the one equation M52 owns:

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```
(module_52.md `equations.gms:16-19`)

So the edge **56 → 52** means: M56 is the declaration-home (producer) of `vm_carbon_stock` and `pcm_carbon_stock`; M52 is their consumer in its CO2-emission equation.

### 2.2 Edge: Module 52 → Module 56 (52 populates; 56 prices)

Module 52 **writes** `vm_emissions_reg` in the equation above. Module 56 **reads** it for pricing.

| Variable | Populated by | Consumed by | Description | Citation |
|----------|------------|-------------|-------------|---------|
| `vm_emissions_reg(i,emis_source,pollutants)` | M52 (CO2/LULUCF slice) via `q52_emis_co2_actual` | M56 `equations.gms:17` (q56_emis_pricing) | Regional emissions by source and gas (Tg/yr) | module_52.md §Interface Variables Written; module_56.md §4.2 |

Note: M56's equation `q56_emis_pricing_co2` (`equations.gms:19-22`) calculates a **parallel, independent** CO2 pricing term directly from `vm_carbon_stock` — it explicitly bypasses `vm_emissions_reg`. The module_56.md doc notes: "CO2 pricing is calculated directly from `vm_carbon_stock`, intentionally bypassing `vm_emissions_reg`." (module_56.md §2.2, "Architectural Note"). This means the physical emissions from M52's `q52_emis_co2_actual` enter `vm_emissions_reg` and are used by M56's `q56_emis_pricing` for annual-type emissions, but the actual CO2 *pricing* cost in M56 comes from a separate stock-difference equation (`q56_emis_pricing_co2`) that reads the stocks directly from M56-declared variables. This is a nuance that Module_Dependencies.md does not document.

Additionally, M52 provides carbon-density parameters consumed outside the 52↔56 edge:
- `pm_carbon_density_secdforest_ac`, `pm_carbon_density_plantation_ac`, `pm_carbon_density_other_ac` — consumed by M14 and M35 (and M32/M29 for uncalibrated variants) (module_52.md §Parameters Provided)
- `fm_carbon_density` — consumed by M14, M29, M30, M31, M32, M35, M56, M59 (module_52.md §2.C, list at line "Consumers of `fm_carbon_density`")
- `im_vol_conv(i)` — consumed by M73 (module_52.md §5, `im_vol_conv`)

The M52-declared `fm_carbon_density` is also consumed by M56 (`modules/56_ghg_policy/price_aug22/preloop.gms:10`), per module_52.md §2.C consumer list. This is an additional **52 → 56** interface for carbon-density data in M56's preloop, separate from the `vm_emissions_reg` pathway.

### 2.3 Edge: Module 56 → Module 57 (56 provides prices; 57 reads them)

Module 57 reads GHG prices from Module 56.

| Variable | Produced by | Consumed by | Description | Citation |
|----------|------------|-------------|-------------|---------|
| `im_pollutant_prices(t,i,pollutants,emis_source)` | M56 preloop configures and writes | M57 `preloop.gms:24-25` | GHG prices by emission source (USD17/Mg) | module_57.md §Data Flow Inputs; module_56.md §6.1 `declarations.gms:9` |

Module 57 reads `im_pollutant_prices` in its own preloop to map prices to MACC step indices (module_57.md §Step 1: Price to MACC Step Mapping, `preloop.gms:16-25`).

### 2.4 Edge: Module 57 → Module 56 (57 reduces emissions; 56 prices the mitigated remainder)

Module 57 writes `im_maccs_mitigation` to the emission modules (51, 53, 50), which then produce lower `vm_emissions_reg` values that M56 prices. This is **not a direct 57 → 56 edge** — it is mediated through the emission modules. module_56.md §4.1 lists the emission sources feeding `vm_emissions_reg` as "Emission modules (51 N2O, 52 LULUCF CO2, 53 CH4, **57 MACC-adjusted**, 58 peatland)". So module_56.md treats M57-adjusted emissions as an upstream supplier, but the mechanism is indirect (through M51/M53 using `im_maccs_mitigation`).

Module 57 also writes `vm_maccs_costs(i,factors)` to M11 (Costs) and the labor-share component to M36 (Employment) — not to M56.

| Variable | Produced by | Consumed by | Description | Citation |
|----------|------------|-------------|-------------|---------|
| `im_maccs_mitigation(t,i,emis_source,pollutants)` | M57 preloop | M51, M53, M50 (reduce baseline emissions) | Technical mitigation fractions (0-1) | module_57.md §Downstream Dependencies |
| `vm_maccs_costs(i,factors)` | M57 equations | M11 (Costs), M36 (Employment) | Mitigation costs (mio. USD17/yr) | module_57.md §Downstream Dependencies; `declarations.gms:25` |

There is **no direct interface variable flowing from M57 to M56**. The M57 → (M51/M53) → vm_emissions_reg → M56 path is the connection, mediated by two modules.

---

## 3. Summary of all within-cluster edges and directions

| Edge | Direction | Variable(s) | Mechanism |
|------|-----------|------------|-----------|
| 56 → 52 | M56 declares; M52 reads | `vm_carbon_stock`, `pcm_carbon_stock` | M52's sole equation (`q52_emis_co2_actual`) reads M56-declared stocks |
| 52 → 56 | M52 populates; M56 prices (via vm_emissions_reg) | `vm_emissions_reg(...,"co2_c")` | M52 fills CO2-slice; M56 q56_emis_pricing reads it for annual-type pricing |
| 52 → 56 | M52 provides; M56 preloop reads | `fm_carbon_density` | M56 `preloop.gms:10` reads LPJmL base densities from M52 |
| 56 → 52 (bypassed) | M56 computes CO2 pricing directly | `vm_carbon_stock`, `pcm_carbon_stock` in q56_emis_pricing_co2 | M56 calculates its own CO2 pricing flow without routing through `vm_emissions_reg` |
| 56 → 57 | M56 writes; M57 reads | `im_pollutant_prices` | M57 preloop reads prices to set MACC step indices |
| 57 → 56 | Indirect via M51/M53 | `im_maccs_mitigation` → reduced `vm_emissions_reg` | M57 reduces non-CO2 emissions; M56 prices the reduced total |

The M52 ↔ M56 relationship is **bidirectional** across two separate interface pathways:
- M56 declares the carbon-stock variables that M52 uses in its emission equation.
- M52 populates `vm_emissions_reg` (CO2 slice) that M56 reads (indirectly for pricing), and also provides `fm_carbon_density` directly to M56's preloop.

The M56 ↔ M57 relationship is **asymmetric**: M56 sends prices to M57; M57 sends no variable back to M56 directly (only indirectly through reduced `vm_emissions_reg` values from M51/M53).

---

## 4. Accuracy assessment: Is Module_Dependencies.md complete and accurate for this cluster?

### Accurate

- M56's centrality rank of #3 with "13 provides-to" is consistent with module_56.md's summary of 13+ consumers of its cost signal.
- M52's dependency "on 56_ghg_policy" (§5.1 degradation table) is correct: M52 reads `vm_carbon_stock` and `pcm_carbon_stock` from M56.
- M52's "1 dependency but 4 consumers" (§7.3) is consistent with its documented upstream dependencies being primarily M56 (for the carbon stock variables) plus M45 (climate), M28 (age class), M32 (plantation), M14 (IPCC factors) — though the count in §7.3 refers to the simpler pre-2026 state and may undercount the newer dependencies added in PR #869.
- The forest-carbon circular dependency `56 → 32 → 10 → 52 → 56` (§4.1 and §12 of module_56.md) is correctly identified.
- Layer placement (M52 in Layer 4, M56+M57 in Layer 5) is directionally correct: M52 produces environmental accounting quantities that M56 prices in the economic layer.

### Incomplete or imprecise

**1. The M56 → M52 edge is understated in §5.1**: The doc lists M52's dependency simply as "56_ghg_policy" without distinguishing that M56 is the *declaration home* of `vm_carbon_stock` / `pcm_carbon_stock`, meaning M52 in one sense depends on M56 for the variables it reads, while in another sense M52 *populates* `vm_emissions_reg` which M56 then uses. The asymmetric "declared-in vs. populated-by" structure (per AGENT.md verifiers.md MANDATE on DECLARED-POPULATED-READ) is not articulated.

**2. The "4 consumers" count for M52 (§7.3) is stale**: After PR #869 (2026-04-20), M52 now additionally provides `im_vol_conv(i)` to M73, and M52's preloop reads newly-added inputs from M28, M32, and M14 — creating new upstream dependencies. The §7.3 risk table notes only M45 as the prior upstream. module_52.md §Module Dependencies documents 5 distinct upstream modules (M45, M56, M28, M32, M14) and 7 downstream consumers (M14, M29, M32, M35, M56, M73, all land modules via fm_carbon_density).

**3. The `fm_carbon_density` link from M52 to M56 is not mentioned anywhere in Module_Dependencies.md**: module_52.md §2.C explicitly lists M56 as a consumer of `fm_carbon_density` (`modules/56_ghg_policy/price_aug22/preloop.gms:10`). This is a second M52 → M56 interface that Module_Dependencies.md omits entirely.

**4. The bypass in q56_emis_pricing_co2 is not documented**: Module_Dependencies.md implies the flow is M52 → vm_emissions_reg → M56. But module_56.md §2.2 documents a deliberate design choice where M56's CO2 *pricing cost* is computed directly from `vm_carbon_stock` (not from `vm_emissions_reg`). The `vm_emissions_reg` path handles annual-type CO2, while the principal CO2 pricing for deforestation uses M56's own stock-difference equation. This architectural split is not reflected in Module_Dependencies.md.

**5. Module 57 is absent from the cluster description**: Module_Dependencies.md's §4.1 (circular dependencies) and §5.1 (degradation subsystem) do not include M57. The M56 → M57 price signal and M57 → (M51/M53) → M56 feedback are not described in any section of Module_Dependencies.md for this cluster. The only Layer-5 reference to M57 is its Layer placement; no interface variables between M56 and M57 are listed.

**6. The "56_ghg_policy: 13 out, 3 in" summary (§3.2)**: Based on module_56.md's detailed dependency list, the "3 in" figure refers to emission modules, forestry CDR (M32), and carbon stocks (M29/31/32/34/35/59). This is roughly accurate directionally but understates the true upstream count. It also omits M12 (interest rate), which module_56.md §12.5 explicitly lists as coordinating for CDR reward calculation.

---

## 5. Conclusion

The carbon/GHG-policy cluster (M52, M56, M57) is structured as follows per the AI docs:

- **M52 ↔ M56**: True bidirectional dependency. M56 is the declaration home of `vm_carbon_stock` / `pcm_carbon_stock` (consumed by M52 in `q52_emis_co2_actual`). M52 populates the CO2 slice of `vm_emissions_reg` (consumed by M56 in `q56_emis_pricing`) and provides `fm_carbon_density` to M56's preloop. Separately, M56's own `q56_emis_pricing_co2` bypasses `vm_emissions_reg` and prices CO2 directly from carbon stocks.
- **M56 → M57**: M56 provides `im_pollutant_prices` to M57's preloop for MACC step selection. No direct variable flows from M57 back to M56.
- **M57 → M56 (indirect)**: M57 outputs `im_maccs_mitigation` to M51/M53, reducing non-CO2 emissions. The reduced `vm_emissions_reg` values then enter M56's pricing equations. The path is mediated by the emission modules, not a direct interface.

Module_Dependencies.md's description of this cluster is **directionally correct but materially incomplete**: it omits the `fm_carbon_density` M52→M56 interface, does not articulate the bypassed `vm_emissions_reg` pathway in M56's CO2 pricing, understates M52's post-PR-#869 upstream dependency count, and does not describe M57's role or its price-input edge from M56 at all.

---

**Source files consulted (all this session)**:
- `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/core_docs/Module_Dependencies.md`
- `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_52.md`
- `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_56.md`
- `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_57.md`

**Epistemic status**:
- All claims about M52, M56, M57 interface variables: 🟡 Documented — read from AI documentation this session (`module_52.md`, `module_56.md`, `module_57.md`; all three marked as fully verified against GAMS source at their last-verified dates). Line numbers in the AI docs were verified at their last sync dates and may have drifted.
- Claims about Module_Dependencies.md content: 🟢 Verified — read the file this session and cross-referenced against the module docs.
- No raw GAMS source code was read (per task constraint). For high-stakes decisions, verify the `fm_carbon_density` consumer list and the `q56_emis_pricing_co2` bypass directly in `modules/56_ghg_policy/price_aug22/equations.gms` and `modules/52_carbon/normal_dec17/equations.gms`.
