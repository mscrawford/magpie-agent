# Audit Report: Q5 (Bioenergy-demand IAMC variable trace — magpie4 → GAMS)

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10

Round 42 semantic-validation audit. Ground truth: SHA-pinned magpie4 clone `v2.70.0 @ a360d8c9ec` (`.cache/sources/magpie4/`) and live GAMS at HEAD `ee98739fd` (`modules/`).

---

### Mechanical checks (M1–M6)

| # | Check | Result |
|---|---|---|
| M1 | File:line citations present | ✅ Pass — both magpie4 source (`getReport.R:79`, `reportDemandBioenergy.R:47/101`, `demand.R:48/121-123`) and GAMS (`declarations.gms:20`, `presolve.gms:17-18`) cited concretely. |
| M2 | Active realization stated | ✅ Pass (soft) — names M60 realization `1st2ndgen_priced_feb24` (which IS the default; confirmed from `config/default.cfg:1982`). Does not explicitly write "this matches default," but the named realization is the default, so the reader is correctly oriented. Note, not a bug. |
| M3 | Variable prefixes valid | ✅ Pass — `vm_dem_bioen`, `ov_dem_bioen`, `v60_2ndgen_*`, `i60_1stgen_*`, `vm_dem_material`, `fm_attributes` all prefix-correct. |
| M4 | Epistemic badges present | ✅ Pass — 🟢/🟡 badges on every substantive claim and in the source-citation table. |
| M5 | Confidence tier matches depth | ✅ Pass — 🟢 used for source-read magpie4 lines (all verified to match exactly this session); 🟡 used for the GAMS-declaration claims that the answerer sourced via `module_60.md`/`module_62.md` rather than reading the .gms directly. Tier honestly reflects that the GAMS facts came from docs. (They are nonetheless code-correct — see below.) |
| M6 | Closing source statement | ✅ Pass — explicit "Source citations" table mapping each claim to a pinned path + tag; satisfies the "Verified against … file:NN" intent. |

---

### Verified Claims (correct)

**(a) magpie4 report function + source file**
- `reportDemandBioenergy` exists at `.cache/sources/magpie4/R/reportDemandBioenergy.R` (v2.70.0 @ a360d8c9ec). ✅ Confirmed (file present, 106 lines).
- Called unconditionally from `getReport.R:79`: `"reportDemandBioenergy(gdx, detail = detail, level = level)"`. ✅ **Exact match** — verified `getReport.R:79`.
- IAMC variable table (`Demand|Bioenergy`, `…|++|2nd generation`, `…|++|1st generation`, `…|++|Traditional Burning`, plus `Overproduction`, `Biochar`) — ✅ confirmed: roxygen `@section` at `reportDemandBioenergy.R:22-26` lists the first four; `Overproduction` constructed at L92-93, `Biochar` at L96-98 (conditional). The `++` summationhelper grouping explanation is correct (`summationhelper(round(out, 8), sep = "++")` at L101).

**(b) Underlying GAMS variable + module**
- `vm_dem_bioen(i,kall)` DECLARED in M60 `1st2ndgen_priced_feb24/declarations.gms:20`, unit "mio. tDM per yr". ✅ **Exact match** (line 20, exact unit string).
- M60 default realization `1st2ndgen_priced_feb24`. ✅ Confirmed via `config/default.cfg:1982` (`cfg$gms$bioenergy <- "1st2ndgen_priced_feb24"`) and `ls modules/60_bioenergy/` (only `1st2ndgen_priced_feb24` + `1stgen_priced_dec18`).
- `ov_dem_bioen` = GDX output form of `vm_dem_bioen`. ✅ Confirmed: `declarations.gms:39` `ov_dem_bioen(t,i,kall,type)` in the R-SECTION output block. `demand.R:48` reads `readGDX(gdx, "ov_dem_bioen", select = list(type = "level"))`.
- "ONLY module that constrains and writes `vm_dem_bioen`; M16 reads it as downstream consumer." ✅ **Verified by full grep** (`grep -rn vm_dem_bioen modules/`): appears only in M60 (both realizations) and `16_demand/sector_may15/equations.gms`. M60 writes via `q60_bioenergy`; M16 is the sole external reader. MANDATE 13/18 satisfied.
- Sub-category vars: `v60_2ndgen_bioenergy_dem_residues(i,kall)` / `v60_2ndgen_bioenergy_dem_dedicated(i,kall)` ✅ confirmed at `declarations.gms:21-22`; GDX forms `ov60_2ndgen_bioenergy_dem_*` at L40-41. `i60_1stgen_bioenergy_dem(t,i,kall)` ✅ confirmed as a **parameter** (`declarations.gms:12`), populated at `presolve.gms:17` (and L25, conditional branch). Answer's "presolve.gms:17-18" and "parameter, not variable" both correct.
- **M62 uninvolved claim**: `vm_dem_material(i,kall)` DECLARED in M62 `exo_flexreg_apr16/declarations.gms:25` (✅ exact line + unit "mio. tDM per yr"); M62 default realization `exo_flexreg_apr16` confirmed (`config/default.cfg:2123`). `vm_dem_material` does NOT appear in `reportDemandBioenergy.R` (it is read separately in `demand.R:47` under the "other_util" dimension, → `reportDemand`, not `reportDemandBioenergy`). ✅ Answer's separation claim correct.

**(c) Aggregation + unit conversion**
- Chain mio tDM/yr × `fm_attributes("ge", kall)` GJ/tDM → mio GJ/yr (=PJ/yr) → /1000 → EJ/yr. ✅ Verified:
  - `demand.R:120-123`: `if (any(attributes != "dm")) { att <- readGDX(gdx, "fm_attributes")[,,products][,,attributes]; out <- out * att }`. Answer cites "121-123" — the load-bearing read (121) + multiply (122) are in range; the `if` guard is at 120 and the close brace at 123. Acceptable.
  - `reportDemandBioenergy.R:47`: `… demand(gdx, level="regglo", attributes="ge")[,,"bioenergy"]) / 1000`. ✅ exact.
  - `/1000` on the three sub-category reads at L50, L53, L54. ✅ exact.
  - `superAggregateX(..., aggr_type="sum", level="regglo")` for spatial aggregation to regions + global. ✅ confirmed (`reportDemandBioenergy.R:48-54`; `demand.R:131-133`).
  - `summationhelper(round(out, 8), sep = "++")` at `reportDemandBioenergy.R:101`. ✅ exact.
- The full unit-chain box (answer L96-106) is internally consistent and matches code.

---

### Bugs Found

**None at Minor or above.** Two Informational observations:

- **Bug ID**: Q5-I1
- **Severity**: Informational
- **Class**: (style/imprecision; no Bug_Taxonomy class)
- **Trigger**: §1 Informational — "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding."
- **Claim in answer**: Table row (L55): "`ov60_2ndgen_bioenergy_dem_residues` … 2nd gen residue demand (mio. GJ/yr in GAMS, **read in mass-level from GDX**)".
- **Reality in code**: These sub-variables are in GJ/yr both in GAMS (`declarations.gms:22`) and as read from GDX (`reportDemandBioenergy.R:48-50` reads `ov60_…residues` directly with `select=list(type="level")` and divides by 1000 → EJ). There is no mass-unit step for the sub-vars; "read in mass-level" is a slip that contradicts the same parenthetical's "mio. GJ/yr in GAMS". Net unit treatment (GJ → /1000 → EJ) is described correctly elsewhere, and the correct GJ unit is stated in the same cell, so a careful reader is not misled. → Informational (internally self-correcting phrase).

- **Bug ID**: Q5-I2
- **Severity**: Informational
- **Class**: (cited-figure provenance; not answerer's own number)
- **Trigger**: §1 Informational.
- **Claim in answer**: L18 "getReport() tryList block is L62–182 … per `magpie4_reference.md`."
- **Reality in code**: The last `report*` call (`reportBiochar`) is at `getReport.R:179`; the `tryList(...)` closing paren is at L182. The G4 rubric summary writes "~62-181". The answer faithfully cites the **helper's** figure (the helper says L62-182) with attribution, so this is not an answerer fabrication — it is a pre-existing ±1 imprecision in the helper that the answer correctly attributed. No action against the answer. (Optional helper polish, not a doc error.)

---

### Latent doc bugs (§1.5)

**None.** The answer's GAMS-side claims are tagged 🟡 (sourced from `module_60.md`/`module_62.md`), and I cross-checked each against live code:
- `module_60.md` → `vm_dem_bioen` at `declarations.gms:20`, unit "mio. tDM per yr": **matches code exactly**.
- `module_62.md` → `vm_dem_material` at `declarations.gms:25`: **matches code exactly**.
No load-bearing doc claim the answer relied on is wrong vs. code → no `doc_error_answerer_beat_it` to record.

---

### Helper coverage (process_gap signal)

`agent/helpers/magpie4_reference.md` does **NOT** name `reportDemandBioenergy`. The "Demand & Diet" theme block (§1) lists `reportDemand`, `reportKcal`, `reportFoodExpenditure`, `reportAnthropometrics`, `reportLivestockShare` only. By the helper's own design ("we do NOT curate function-level docs … grep + read source on demand"), this is expected — the function would be found via the `grep -l "Demand…"` recipe. The answerer correctly went to source: every magpie4 source-line citation (getReport.R:79, reportDemandBioenergy.R:22-26/47/48-54/101, demand.R:48/121-123) **matches the pinned clone exactly**, which is only possible by reading the file, not by paraphrasing the helper.

→ **process_gap (helper gap), NOT a doc_error.** Useful signal: a one-line entry for `reportDemandBioenergy` under §1 (or a note that bioenergy demand has its own dedicated report function distinct from `reportDemand`) would shorten future answers, but the absence did not harm this answer. No correctness obligation.

---

### Missing Nuances

The answer is thorough and even flags its own residuals (the `fm_attributes` numeric values, the `Traditional Burning` = residues-in-1st-gen-parameter subtlety, and the biochar reallocation branch) in a "What the docs leave unclear" section — all three observations are code-accurate (verified: `bioenergyTra` from `bioenergy1stTra[,, kres]` at L60-62; biochar reallocation at L67-84 subtracting biochar feedstock from the 2nd-gen pools at L82-83). No material nuance missing.

One ultra-minor: the answer says `fm_attributes` is "not declared in Module 60's own declarations" — correct; `fm_attributes` is a shared `f`-prefix interface parameter (declared in the core/preprocessing layer), consistent with the answer's framing.

---

### Summary

A clean, fully-verified trace. (a) Correct report function and pinned source path with an exact `getReport.R:79` call-line. (b) Correct GAMS origin `vm_dem_bioen(i,kall)` at the exact declared line in M60's verified-default realization, correct GDX form, correct producer (M60 only) / consumer (M16 only) set verified by full grep, and a correct M62-is-separate claim grounded in `vm_dem_material`. (c) Correct two-step unit conversion (GJ-content multiply + /1000 → EJ + regglo aggregation), every magpie4 line citation matching the pinned clone exactly. The only blemishes are two Informational items (a self-contradicting "mass-level" parenthetical that the same cell corrects, and a ±1 tryList-span figure inherited verbatim from the helper). Neither affects the score.

**Score: max(0, 10 − 4·0 − 2·0 − 1·0) = 10/10.**

- M60 verified default realization: **`1st2ndgen_priced_feb24`** (`config/default.cfg:1982`).
- Helper coverage of `reportDemandBioenergy`: **NOT covered by name** → process_gap (by design; answerer correctly went to source). Not a doc bug.

Root-cause vocabulary: no `answerer_confabulation`, no `doc_error`, no `doc_error_answerer_beat_it`. One `process_gap` (helper does not name the function — informational, by-design).
