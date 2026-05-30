# Round 31 Doc Audit — module_55.md (AWMS, ipcc2006_aug16)

**Auditor**: adversarial doc auditor (Opus 4.8, 1M)
**Date**: 2026-05-30
**Target**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_55.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`

---

## Verdict: SIGNIFICANT ERRORS (in the consumer/dependency tables) — otherwise strong

The doc is highly accurate on equations, formulas, citations, sets, defaults, and execution phases. **However, the downstream consumer mapping (both the "Outputs" prose and the "Downstream Dependencies" table) is wrong in three distinct, modification-safety-relevant ways.** All three are the R20-anchor class (wrong consumer set), which the rubric §1.5 latent-doc-bug mandate scores as Critical by future-reader harm. They share one root cause: the author conflated the **generic `vm_manure` variable indexed by AWMS element** (`vm_manure(...,"confinement",...)`, `(...,"grazing",...)`, `(...,"stubble_grazing",...)`) with the **separate `vm_manure_confinement` variable**, and did not grep all consumers of each variable.

---

## Ground-truth consumer map (default realizations only)

Default realizations confirmed in `config/default.cfg`:
- M50 `nr_soil_budget` = `macceff_aug22` (line 1479)
- M51 `nitrogen` = `rescaled_jan21` (line 1550)
- M53 `methane` = `ipcc2006_aug22` (line 1583)

Verified reads (rg + grep, cross-checked, equations.gms sweep + core/ sweep):

| M55 interface variable | M50 (macceff) | M51 (rescaled) | M53 (ipcc2006) |
|---|---|---|---|
| `vm_manure_recycling` | ✅ `equations.gms:27` | ✅ `equations.gms:25` | ❌ |
| `vm_manure_confinement` | ❌ | ✅ `equations.gms:69` | ❌ |
| `vm_manure` | ✅ `equations.gms:28` (stubble_grazing), `:77` (grazing) | ✅ `equations.gms:78` (awms_prp) | ✅ `equations.gms:50` (confinement) |

`vm_manure` is read ONLY by 50/51/53 + M55 itself (no `core/` reads; full `*/*/equations.gms` sweep confirms).

---

## Doc claims (exact quotes)

**Outputs section (lines 256-268):**
- L258-259: "**To Module 50** ... `vm_manure_recycling`" — vm_manure_recycling listed for M50 only.
- L261-264: "**To Module 51** ... `vm_manure_confinement` ... `vm_manure(i,kli,awms_prp,npk)`".
- L266-268: "**To Module 53** ... `vm_manure_confinement(...)`: Manure in confinement (... → CH₄) ... `vm_manure(i,kli,awms,npk)`: ... (for enteric fermentation and manure CH₄ calculations)".

**Downstream Dependencies table (lines 508-511):**
- L508: M50 — `vm_manure_recycling`
- L509: M51 — `vm_manure_confinement`
- L510: M51 — `vm_manure(i,kli,awms_prp,npk)`
- L511: **M53 — `vm_manure_confinement`** (CH₄)

**Critical Hub Status (L516):** "Provides manure flows to 3 downstream modules (50, 51, 53)" — count of 3 is CORRECT (all three genuinely consume some M55 variable). Only the variable↔module mapping is wrong.

---

## Bugs

### BUG 55-B1 — Module 53 phantom consumer of `vm_manure_confinement` (Critical)
- **Class**: 15 (latent doc error) / MANDATE-17 look-alike conflation.
- **Trigger**: §1 Critical "wrong consumer set" (R20 anchor); also resembles MANDATE 17 (transitive/look-alike mis-attribution).
- **Doc**: module_55.md:267 and module_55.md:511 — "To Module 53 (Methane): `vm_manure_confinement(i,kli,awms_conf,npk)`".
- **Reality**: M53 does NOT reference `vm_manure_confinement` anywhere. Its AWMS-CH4 equation `q53_emissionbal_ch4_awms` reads the **`vm_manure` variable** with the `"confinement"` element: `sum(kli, vm_manure(i2, kli, "confinement", "nr") ...)`.
- **File evidence**: `modules/53_methane/ipcc2006_aug22/equations.gms:50`. Absence confirmed twice (rg exit 1, grep -rn exit 1) + positive control (`vm_manure` present at :50).
- **Verify cmds + results**:
  - `rg -n "vm_manure_confinement" /tmp/magpie_develop_ro/modules/53_methane/` → no output, exit 1 (absent).
  - `grep -rn "vm_manure_confinement" /tmp/magpie_develop_ro/modules/53_methane/` → no output, exit 1 (absent).
  - `grep -rn "vm_manure" /tmp/magpie_develop_ro/modules/53_methane/ipcc2006_aug22/` → `equations.gms:50: sum(kli, vm_manure(i2, kli, "confinement", "nr")` (positive control: search works).
- **Harm**: A user refactoring `vm_manure_confinement` would wrongly think M53 depends on it; a user editing `vm_manure`'s confinement handling would NOT realize M53 (methane) breaks. Both directions mislead modification-safety.
- **Fix**: In the table (L511) and prose (L266-268), M53 consumes `vm_manure` (confinement element), NOT `vm_manure_confinement`. See consolidated fix below.

### BUG 55-B2 — Module 50 omitted as consumer of `vm_manure` (Critical)
- **Class**: 15 (latent doc error) — omitted consumer.
- **Trigger**: §1 Critical "wrong consumer set" (R20 anchor).
- **Doc**: module_55.md:258-268 / table 508-511 list `vm_manure` only under M51 and M53; M50's row (L508) lists only `vm_manure_recycling`.
- **Reality**: M50 `q50_nr_inputs` reads `sum(kli, vm_manure(i2, kli, "stubble_grazing","nr"))` and `q50_nr_inputs_pasture` reads `sum(kli,vm_manure(i2, kli, "grazing", "nr"))`.
- **File evidence**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:28` (stubble_grazing) and `:77` (grazing).
- **Verify cmd + result**: `rg -n "vm_manure" /tmp/magpie_develop_ro/modules/50_nr_soil_budget/macceff_aug22/equations.gms` → `27: + vm_manure_recycling(i2,"nr")` / `28: + sum(kli, vm_manure(i2, kli, "stubble_grazing","nr"))` / `77: sum(kli,vm_manure(i2, kli, "grazing", "nr"))`.
- **Harm**: A user refactoring `vm_manure` (e.g., changing its AWMS indexing) would miss that the nitrogen soil budget (M50) reads its grazing/stubble_grazing elements for both cropland and pasture N inputs.
- **Fix**: Add an M50 row for `vm_manure` (grazing + stubble_grazing elements). See consolidated fix.

### BUG 55-B3 — Module 51 omitted as consumer of `vm_manure_recycling` (Critical)
- **Class**: 15 (latent doc error) — omitted consumer.
- **Trigger**: §1 Critical "wrong consumer set" (R20 anchor).
- **Doc**: module_55.md:258-259 / table L508 list `vm_manure_recycling` only under M50.
- **Reality**: M51 `q51_emissions_man_crop` reads `vm_manure_recycling(i2,"nr")` to compute manure-applied-to-cropland N emissions.
- **File evidence**: `modules/51_nitrogen/rescaled_jan21/equations.gms:25`.
- **Verify cmd + result**: `rg -ln "vm_manure_recycling" /tmp/magpie_develop_ro/modules/` → includes `51_nitrogen/rescaled_jan21/equations.gms` and `50_nr_soil_budget/macceff_aug22/equations.gms`; line check `rg -n "vm_manure" .../51_nitrogen/rescaled_jan21/equations.gms` → `25: vm_manure_recycling(i2,"nr")`.
- **Harm**: A user refactoring `vm_manure_recycling` would miss M51 (N emissions from manure on cropland).
- **Fix**: Add an M51 row for `vm_manure_recycling`. See consolidated fix.

### BUG 55-B4 — `vm_manure` "enteric fermentation" purpose mis-attribution (Minor)
- **Class**: 4 (conceptual / mechanism mis-statement). Tie-broken DOWN to Minor (the consumption claim — M53 reads vm_manure — is correct; only the stated purpose is partly wrong, and enteric fermentation is a real M53 equation).
- **Trigger**: §1 Minor "wrong detail; careful reader not misled into action".
- **Doc**: module_55.md:268 — "`vm_manure(...)`: Total manure by AWMS (for enteric fermentation and manure CH₄ calculations)".
- **Reality**: M53's enteric-fermentation equation `q53_emissionbal_ch4_ent_ferm` reads `vm_feed_intake` (from M70), NOT `vm_manure`. `vm_manure` is used by M53 ONLY in the AWMS-CH4 equation `q53_emissionbal_ch4_awms`.
- **File evidence**: `modules/53_methane/ipcc2006_aug22/equations.gms:21-29` (ent_ferm reads `vm_feed_intake`), `:48-52` (AWMS reads `vm_manure`).
- **Verify cmd + result**: `Read equations.gms:21-29` → `q53_emissionbal_ch4_ent_ferm` body sums `vm_feed_intake(i2,"livst_rum",k_conc53)` etc.; no `vm_manure`.
- **Fix**: Drop "enteric fermentation and" — M53 uses `vm_manure` for AWMS (manure) CH₄ only.

---

## Consolidated fix (single intervention — shared root cause)

Replace the **Downstream Dependencies table** (L508-511) with:

```
| **50** (NR Soil Budget) | `vm_manure_recycling(i,npk)`; `vm_manure(i,kli,awms,npk)` (grazing + stubble_grazing elements) | Manure-recycling N to cropland; grazing/stubble manure N to cropland+pasture inputs |
| **50** (NR Soil Budget) | `vm_manure(i,kli,"grazing"/"stubble_grazing",npk)` | N inputs to cropland (stubble_grazing) and pasture (grazing) |
| **51** (Nitrogen) | `vm_manure_recycling(i,npk)` | Manure-on-cropland N emissions (`q51_emissions_man_crop`) |
| **51** (Nitrogen) | `vm_manure_confinement(i,kli,awms_conf,npk)` | AWMS confinement N emissions (`q51_emissionbal_awms`) |
| **51** (Nitrogen) | `vm_manure(i,kli,awms_prp,npk)` | Pasture/stubble (PRP) N emissions (`q51_emissionbal_man_past`) |
| **53** (Methane) | `vm_manure(i,kli,"confinement",npk)` | AWMS confinement CH₄ emissions (`q53_emissionbal_ch4_awms`) |
```

And in the **Outputs** prose, change L266-268 ("To Module 53") to:
```
**To Module 53 (Methane)**:
- `vm_manure(i,kli,"confinement",npk)`: Manure in confinement (anaerobic storage → AWMS CH₄ emissions, `q53_emissionbal_ch4_awms`). NOTE: M53 reads the `vm_manure` variable's confinement element, NOT the separate `vm_manure_confinement` variable. (Enteric-fermentation CH₄ in M53 uses `vm_feed_intake`, not manure.)
```
And add to L258 ("To Module 50") that M50 also reads `vm_manure` (grazing/stubble_grazing), and note (L261) that M51 also reads `vm_manure_recycling`.

(Optionally simplify to one M50 row; the two-row form above is to make the grazing vs stubble_grazing split explicit.)

---

## Verified-correct claims (no action)

- Default realization `ipcc2006_aug16` (config/default.cfg:1593) ✓; alternative `off` fixes vars to 0 (`off/preloop.gms`) ✓.
- 7 equations; names + start lines all exact: q55_bal_intake_confinement(26), grazing_pasture(37), fuel(44), grazing_cropland(52), bal_manure(68), manure_confinement(75), manure_recycling(83) ✓.
- All four feed-intake formulas reproduced faithfully, incl. the dev-state factor `1-(1-dev)*0.25` (eq1, eq.gms:31-32) and stubble `(1-dev)*0.25` (eq4, eq.gms:54-55), and the grazing `(1-fuel_shr)` vs fuel `sum(ct,fuel_shr)` split (eq.gms:40 vs :47) ✓.
- Mass-balance eq `vm_manure = v55_feed_intake * (1-im_slaughter_feed_share)` (eq.gms:68-71) ✓.
- Confinement distribution `vm_manure_confinement = vm_manure(..,"confinement",..) * ic55_awms_shr` (eq.gms:75-78) ✓.
- Recycling `vm_manure_recycling = sum((awms_conf,kli), vm_manure_confinement * i55_manure_recycling_share)` (eq.gms:83-87) ✓.
- Declarations: i55_manure_recycling_share(:10), ic55_manure_fuel_shr(:11), ic55_awms_shr(:12), p55_country_switch(:14) — all exact ✓. Variables vm_manure/v55_feed_intake/vm_manure_recycling/vm_manure_confinement at decl :19-22 ✓.
- Sets: awms(10-11, 4 members), awms_prp(13-14, subset, {grazing,stubble_grazing}), awms_conf(16-17, 9 members, separate set NOT subset), scen_conf55(19-20, 12 members incl `sdp`) — all exact ✓. Doc L350 includes `sdp`; doc L277 options list omits `sdp` but matches the code comment input.gms:11-13 (which also omits it) — acceptable.
- `c55_scen_conf` default `ssp2` (input.gms:9) ✓; `c55_scen_conf_noselect` default `ssp2` (input.gms:10) ✓.
- `scen_countries55`: 249 ISO codes (input.gms:18-42) ✓ — matches doc L330 "All 249".
- presolve citations: country switch :11-12, region share :16, time-update block :19-26, ssp2 baseline :20-21, blending :23-24, fuel-GDP :25 — all exact ✓.
- preloop: N recycling from file (:10), P=1 (:12), K=1 (:13) ✓.
- P/K fixed to 1.0 ("no losses") ✓; N from `f55_awms_recycling_share` (input.gms:45-48 / preloop:10) ✓.
- Upstream: vm_feed_intake declared `70_livestock/fbask_jan16/declarations.gms:18` (M70 default = fbask_jan16, cfg:2146) ✓; im_development_state used at eq.gms:32,55 ✓; im_pop_iso at presolve:16 ✓; im_slaughter_feed_share at eq.gms:71 ✓.
- realization.gms: Bodirsky 2012 (:10), IPCC 2006 (:11-12) ✓; module.gms purpose lines 10-13 ✓.
- nl_fix/nl_release/nl_relax empty (whitespace only at line 8) ✓; postsolve 56 lines (doc "10-55") ✓.
- "3 downstream modules (50,51,53)" hub count — CORRECT.

---

## Deferred (not code-verifiable / out of scope — NOT edited)

- Doc L203 "Sum constraint: `sum(awms_conf, ic55_awms_shr) = 1`": presented as a property of input data, not a coded equation (no such constraint equation exists in M55). Likely true of the `f55_awms_shr.cs4` input but unverifiable without reading the `.cs4` file. Not flagged.
- Illustrative recycling-share / slaughter-share / emission-characteristic numbers (Appendix table L805-817; example calc L725-799): explicitly labeled illustrative; not code-checkable. Not flagged.
- SSP narrative characterizations (L659-689): conceptual, explicitly labeled not-quantitative; the actual trajectories live in `.cs4` input. Not flagged.
- Doc L268 "for enteric fermentation": flagged as BUG-B4 (Minor) since enteric fermentation IS a real M53 equation but reads vm_feed_intake; recorded as a bug, not deferred.
