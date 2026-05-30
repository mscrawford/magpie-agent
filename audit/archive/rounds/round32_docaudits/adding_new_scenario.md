# Round 32 Doc Audit — `agent/helpers/adding_new_scenario.md`

**Auditor**: Opus 4.8 (1M), adversarial doc auditor
**Date**: 2026-05-30
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (Merge PR #887) + `config/default.cfg`
**Advisory pre-flag**: "Never validated, largest helper. Verify cfg$gms switch names, realization names, and any config-file paths/examples against config/default.cfg + develop module code." → **Addressed in full** (see §Advisory verdict).

## Overall verdict: MOSTLY ACCURATE (high quality for a never-validated 366-line helper)

Score-equivalent: ~8/10. One Major fabrication (line 357), two low-severity naming/completeness items. The bulk of the doc — ~50 `cfg$gms$` switch names, every stated default, every realization name, the `setScenario`/`start_run` signatures + `scenario_config` argument, the emulator CSV column list, the climate-consistency switch set, and the "80 rows" count — verifies exactly against develop.

---

## Method notes / grep reliability

- Chained `grep ... || echo` loops **silently truncated** (documented repo failure mode). Switched to **isolated `rg` probes, one per command**, each with `|| true`.
- Every absence claim below is confirmed by a **second method + positive control** (e.g., proved `rg` works in `scenario_config.csv` by hitting the present token `c56_pollutant_prices` on line 71 before concluding `mute_ghgprices` is absent).
- `rg` output rendering mangled some R lines (collapsed `scenario_config = ` → `n ` and `n(cfg` → `ncfg`); I re-read those via `awk`/`Read` to get true text before judging. This is why the `setScenario` signature is judged CORRECT despite the mangled grep display.

---

## Verified-correct claims (sample; all confirmed against code)

### Realization names + defaults (MANDATE 8)
- `cfg$gms$food <- "anthro_iso_jun22"` — default.cfg:410 ✓; dir `modules/15_food/anthro_iso_jun22/` exists ✓ (doc:30, 214).
- `cropland` realizations `simple_apr24`, `detail_apr24`; default `detail_apr24` — default.cfg:795; dirs `modules/30_croparea/{simple,detail}_apr24/` ✓ (doc:74). [Note: module 30 is `30_croparea`, not "Cropland"; see Informational below.]

### Scenario switch defaults (MANDATE 3 — every one grepped in default.cfg)
| Switch | Doc value | default.cfg | Line | Verdict |
|---|---|---|---|---|
| c09_pop_scenario | SSP2 | SSP2 | 211 | ✓ |
| c09_gdp_scenario | SSP2 | SSP2 | 212 | ✓ |
| c09_pal_scenario | SSP2 | SSP2 | 220 | ✓ |
| s15_exo_diet | 0 | 0 | 519 | ✓ |
| c15_EAT_scen | FLX | FLX | 539 | ✓ |
| c15_kcal_scen | healthy_BMI | healthy_BMI | 534 | ✓ |
| s15_exo_waste | 0 | 0 | 495 | ✓ |
| s15_waste_scen | 1.2 | 1.2 | 502 | ✓ |
| c15_food_scenario | SSP2 | SSP2 | 433 | ✓ |
| s15_exo_monogastric/ruminant/fish/fruitvegnut/pulses | 1 | 1 | 546-551 | ✓ |
| s15_food_substitution_start/target | 2025/2050 | 2025/2050 | 485/487 | ✓ |
| s21_trade_tariff | 1 | 1 | 694 | ✓ |
| c21_trade_liberalization | l909090r808080 | l909090r808080 | 670 | ✓ |
| c22_protect_scenario | none | none | 755 | ✓ |
| c22_base_protect | WDPA | WDPA | 723 | ✓ |
| c30_bioen_water | rainfed | rainfed | 903 | ✓ |
| c32_aff_policy | npi | npi | 1008 | ✓ |
| s32_max_aff_area | Inf | Inf | 1016 | ✓ |
| c32_aff_mask | noboreal | noboreal | 1038 | ✓ |
| s32_aff_plantation | 0 | 0 | 992 | ✓ |
| c35_ad_policy | npi | npi | 1141 | ✓ |
| c35_aolc_policy | npi | npi | 1147 | ✓ |
| s42_irrig_eff_scenario | 2 | 2 | 1342 | ✓ |
| c42_env_flow_policy | off | off | 1352 | ✓ |
| s42_watdem_nonagr_scenario | 2 | 2 | 1336 | ✓ |
| s42_efp_targetyear | 2040 | 2040 | 1360 | ✓ |
| c50_scen_neff | baseeff_add3_add5_add10_max65 | (same) | 1522 | ✓ |
| c56_pollutant_prices | R34M410-SSP2-NPi2025 | (same) | 1713 | ✓ |
| c56_emis_policy | reddnatveg_nosoil | reddnatveg_nosoil | 1810 | ✓ |
| s56_c_price_induced_aff | 1 | 1 | 1741 | ✓ |
| s56_cprice_red_factor | 1 | 1 | 1620 | ✓ |
| c56_mute_ghgprices_until | y2030 (doc:357) | y2030 | 1726 | ✓ (default only; see BUG) |
| s58_rewetting_switch | Inf | Inf | 1858 | ✓ |
| s58_rewetting_exo | 0 | 0 | 1871 | ✓ |
| c60_1stgen_biodem | const2020 | const2020 | 1988 | ✓ |
| c60_2ndgen_biodem | R34M410-SSP2-NPi2025 | (same) | 2061 | ✓ |
| c13_tccost | (uses "low"; default medium) | medium | 296 | ✓ exists, valid option |
| s29_snv_shr / s29_snv_scenario_target | 0 / 2050 | 0 / 2050 | 822/828 | ✓ |
| s15_exo_monogastric/ruminant/fish/fruitvegnut/pulses (Combo 2) | 1 | 1 | 546-551 | ✓ |

### Climate-consistency switches (doc:359, "modules 14,42,43,52,59")
`c14_yields_scenario` (360), `c42_watdem_scenario` (1325), `c43_watavail_scenario` (1412), `c52_carbon_scenario` (1569), `c59_som_scenario` (1930) — all exist, all default `"cc"`. ✓

### Option-set validity
- `c56_emis_policy` options include both `reddnatveg_nosoil` (default) and `all_nosoil` (doc:329) — default.cfg:1790-1810 ✓.
- `c15_EAT_scen` doc values (FLX, FLX_hmilk, PSC, VGN, VEG) ⊂ valid set {BMK,FLX,PSC,VEG,VGN,FLX_hmilk,FLX_hredmeat} (default.cfg:539) ✓.
- `c15_kcal_scen` doc values (healthy_BMI, no_underweight) ⊂ valid set (default.cfg:524-533) ✓.

### Functions / files
- `gms::setScenario(cfg, scenario)` is the real function (start_functions.R:242). `setScenario(cfg, c(preset), scenario_config = "config/projects/scenario_config_genie.csv")` is verbatim real (GENIE_0_default.R:41 via awk) → doc:153 argument name `scenario_config` ✓.
- `start_run(cfg, scenario=NULL, codeCheck=TRUE, ...)` (start_functions.R:217); `start_run(cfg, codeCheck = FALSE)` real (GENIE_0_default.R:51) → doc:192,351 ✓.
- Project CSVs `scenario_config_fsec.csv`, `scenario_config_genie.csv` exist (config/projects/) → doc:151 ✓.
- Emulator CSV columns `start;mag_scen;ghgtax_name;mifname;no_ghgprices_land_until` verbatim (scenario_config_emulator.csv header) → doc:156 ✓.
- `scenario_config.csv` "80 rows of switches": 82 lines = 1 header + 80 `gms$...` switch rows + 1 `input['cellular']` row → doc:128 ✓.
- Preset names in doc table (SSP1-5, SDP/SDP-EI/-RC/-MC, cc/nocc/nocc_hist, NPI/NPI-revert/NDC, rcp1p9..8p5, eat_lancet_diet_v1/v2, ForestryEndo/Exo/Off, AR-natveg/AR-plant) all present in the CSV header row ✓.

### Mechanism spot-checks
- `s56_c_price_induced_aff` used in price_aug22/preloop.gms:60 (C-price afforestation fade-in) ✓.
- `s56_cprice_red_factor` applied in price_aug22/preloop.gms:67 (`im_pollutant_prices * s56_cprice_red_factor`) → doc:108 "1=full price, 0=no CO2 pricing" matches code (NB: default.cfg comment line 1618 says "only used in price_jan19" but code shows it IS used in the default price_aug22 — config comment is stale, doc is correct vs code).
- Diet product switches drive `i15_ruminant_fadeout`/`i15_fish_fadeout` in exodietmacro.gms → doc Pitfall #2 advice is mechanism-consistent (switches default 1; "set them to 1" is benign).

---

## BUGS FOUND

### BUG-1 (Major) — fabricated `BASE` preset / `y2150` claim
- **doc_line**: adding_new_scenario.md:357
- **bug_class**: Content-level citation/attribution mismatch (class 12)
- **Trigger** (§1 Major): "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different" / fabricated specific claim about file content.
- **Claim in doc**: "`c56_mute_ghgprices_until` ... defaults to `"y2030"`. ... The scenario CSV sets this to `"y2150"` for the `BASE` preset intentionally."
- **Reality in code**:
  1. `scenario_config.csv`'s `BASE` preset (column 21) sets **only 6 switches**: `s22_base_protect_reversal=Inf`, `c32_aff_policy=none`, `s32_npi_ndc_reversal=Inf`, `c35_ad_policy=none`, `c35_aolc_policy=none`, `s35_npi_ndc_reversal=Inf`. It does **NOT** set `c56_mute_ghgprices_until` at all.
  2. `c56_mute_ghgprices_until` is **not a row** in `scenario_config.csv`. The token `y2150` appears **nowhere** in `scenario_config.csv`.
  3. The `y2150` value actually lives in a **different file**: `scenario_config_emulator.csv`, column `no_ghgprices_land_until`, for rows whose `ghgtax_name` is `Base`/`NDC`. That is the emulator coupling CSV (distinct format, distinct mechanism), not the `scenario_config.csv` `BASE` preset. The doc conflated the two.
  - The default half ("defaults to `y2030`") is correct (default.cfg:1726). Only the "BASE sets y2150" assertion is fabricated.
- **file_evidence**:
  - config/scenario_config.csv (BASE = column 21; 6 switches listed above; no `c56_mute_ghgprices_until`, no `y2150`).
  - config/scenario_config_emulator.csv:2-13 (`no_ghgprices_land_until=y2150` for `Base`/`NDC` ghgtax rows).
  - config/default.cfg:1726 (`cfg$gms$c56_mute_ghgprices_until <- "y2030"   # def = y2030`).
- **verify_cmd** (with results):
  - `awk -F';' 'NR==1{...BASE col...} NR>1 && $col!="" {print $1" = "$col}' config/scenario_config.csv` → BASE is column 21; prints exactly the 6 switches above (no c56_mute / no y2150).
  - `rg -n 'y2150' config/scenario_config.csv` → "no y2150 in scenario_config.csv".
  - `rg -n 'mute_ghgprices' config/scenario_config.csv` → "NO MATCH". Positive control: `rg -n 'c56_pollutant_prices' config/scenario_config.csv` → hit on line 71 (search works in this file).
  - `cat config/scenario_config_emulator.csv` → `y2150` present in `no_ghgprices_land_until` for `Base`/`NDC` rows.
- **confirmed**: true.
- **proposed_fix**: Replace the second sentence of the doc:357 bullet. From:
  "If you set a carbon price but mute until 2150, you effectively have no land-based carbon pricing. The scenario CSV sets this to `\"y2150\"` for the `BASE` preset intentionally."
  To:
  "If you set a carbon price but mute until 2150, you effectively have no land-based carbon pricing. (Note: `c56_mute_ghgprices_until` is NOT set by any preset in `scenario_config.csv`; the `y2150` mute value appears only in the emulator coupling CSV `config/scenario_config_emulator.csv`, column `no_ghgprices_land_until`, for the `Base`/`NDC` ghgtax rows.)"

### BUG-2 (Minor) — non-existent generic `select_countries` name
- **doc_line**: adding_new_scenario.md:218
- **bug_class**: Hallucinated variable name (class 2), low severity (generic config-list name)
- **Claim in doc**: "The `_noselect` variants (e.g., `cfg$gms$c22_protect_scenario_noselect`) apply to countries NOT in the `select_countries` list, enabling country-specific policies"
- **Reality in code**: There is no generic `select_countries` list. The country-selection variable is **module-specific**: module 15 uses `scen_countries15` (default.cfg:577), modules 22/29/30/56/58/59 use `policy_countries22`/`policy_countries29`/`policy_countries56`/etc. (default.cfg:763/812/1738/1868/1948). The only `select_countries*` name in config is `select_countries12` (module 12, default.cfg:278) — unrelated to the `_noselect` policy mechanism described. The `_noselect` half is correct (`c22_protect_scenario_noselect` is real, default.cfg:756); only the "`select_countries` list" referent is wrong.
- **file_evidence**: config/default.cfg:577 (`scen_countries15`), :763 (`policy_countries22`), :278 (`select_countries12` only), :756 (`c22_protect_scenario_noselect`).
- **verify_cmd**: `rg -n 'select_countries' config/default.cfg` → single hit `select_countries12` (278). `rg -n 'scen_countries15|policy_countries' config/default.cfg` → `scen_countries15` (577) + `policy_countries22/29/30/56/58/59`.
- **confirmed**: true.
- **proposed_fix**: Replace "apply to countries NOT in the `select_countries` list" with "apply to countries NOT in that module's policy-country list (the list variable is module-specific: `scen_countries15` for module 15, `policy_countries22`/`policy_countries29`/`policy_countries56`/etc. for other modules; there is no single global `select_countries` list)".

### BUG-3 (Informational) — `s15_exo_diet` inline comment omits option 2
- **doc_line**: adding_new_scenario.md:51
- **bug_class**: Suffix/range truncation (class 3), informational (inline comment, not an exhaustive-options claim)
- **Claim in doc**: "`cfg$gms$s15_exo_diet  <- 0  # 0=off, 1=EAT-Lancet, 3=new EAT-Lancet realization`"
- **Reality in code**: `s15_exo_diet` has **four** documented values: 0 (regression-based), 1 (EAT-Lancet, deprecated), **2 (transition to exogenous diets — NIN for India + EAT for other regions)**, 3 (MAgPIE-specific EAT-Lancet realization). The comment omits value 2. The three values it does list are correctly characterized.
- **file_evidence**: config/default.cfg:505-519 (full option block, including "(2): transition towards exogenous diets (NIN for India and EAT for other regions)").
- **verify_cmd**: `sed -n '505,540p' config/default.cfg` → shows options 0/1/2/3 with descriptions.
- **confirmed**: true.
- **proposed_fix**: Optional. Change the comment to "# 0=off, 1=EAT-Lancet (deprecated), 2=NIN-India+EAT-RoW, 3=new EAT-Lancet realization". Low priority — the comment is illustrative, not exhaustive.

---

## Advisory verdict (pre-flag: verify cfg$gms switches, realization names, config paths/examples)

**Refuted in the main** / one Major confirmed. Specifically:
- **cfg$gms switch names**: all ~50 verified present in default.cfg with stated defaults — clean except the BUG-1 `BASE`/`y2150` fabrication and the BUG-2 `select_countries` generic name.
- **realization names**: `anthro_iso_jun22` (M15), `simple_apr24`/`detail_apr24` (M30) all verified against `ls` of develop module dirs — clean.
- **config-file paths/examples**: `config/scenario_config.csv`, `config/projects/scenario_config_{fsec,genie}.csv`, `config/scenario_config_emulator.csv` all exist; emulator column list verbatim; `setScenario(..., scenario_config=...)` + `start_run(cfg, codeCheck=FALSE)` verbatim against real project scripts — clean.

The advisory's worry was justified for exactly one claim (line 357), which the auditor confirmed and pinned to a file/preset confusion.

---

## Deferred (NOT edited — not code-verifiable from config alone, or general-knowledge)
- doc:105/263/328 — exact validity of REMIND scenario strings `R34M410-SSP2-PkBudg1000`, `R34M410-SSP1-PkBudg650`, `R34M410-SSP2-PkBudg1000`: these are input-data (REMIND coupling) names not enumerated in default.cfg; default `R34M410-SSP2-NPi2025` is confirmed, the `PkBudg*` variants are plausible but I cannot confirm the exact strings against develop without the input `.tgz`. No edit.
- doc:306 — `c50_scen_neff <- "baseeff_add3_add15_add25_max75"`: the `baseeff_add*_max*` family is real (default is `baseeff_add3_add5_add10_max65`) but this exact alternate string is not enumerated in the default.cfg comment block (which lists `maxeff_*` examples). Plausible but unconfirmed. No edit.
- doc:234 — "modelstat should be 1 (optimal) or 2 (locally optimal)": general GAMS convention, not MAgPIE-code-specific. No edit.
- doc:242 — "Total land area stays constant (~13,000 Mha)": sanity-check heuristic, not verifiable from config without a model run. No edit.
- doc:73 — c30_bioen_water options comment "rainfed, all" omits "irrigated" (default.cfg:902 lists rainfed/irrigated/all). Borderline; the doc line is a parenthetical, not an options enumeration. Left as a note, not a bug.
- doc:71 header "Cropland (Module 30)" — module 30 is `30_croparea`; "Cropland" is module 29. The `cfg$gms$cropland` SWITCH name is real and correctly used, so this is a header-label imprecision only. Not flagged as a bug (no false code claim follows from it).
