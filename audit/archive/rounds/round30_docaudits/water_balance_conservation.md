# Doc Audit: water_balance_conservation.md (Round 30)

**Target**: `cross_module/water_balance_conservation.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree @ `ee98739fd`, Merge PR #887)
**Auditor**: adversarial doc auditor (Opus), 2026-05-29
**Modules covered by doc**: 42 (water demand), 43 (water availability)

---

## Overall Verdict: MOSTLY ACCURATE (lower band)

This is a high-quality doc. The core conservation law, the equation `q43_water`, the set definitions, the buffer mechanism, the cross-module producer/consumer sets, and the vast majority of file:line citations all check out against develop. Three code-verifiable bugs found: two Major (a wrong default-state number for irrigation efficiency, and a citation that attributes uncoded justification claims to a specific source line) and one Minor (wrong country count). No fabricated variables, no fabricated equation names, no wrong realizations, no inverted Boolean defaults, no phantom/omitted cross-module consumers.

**Accuracy score**: 10 − 2(Major) − 2(Major) − 1(Minor) = **5/10** on the strict weighting; but note both Majors are localized prose/citation issues against an otherwise correct doc whose authoritative sections (6.1, 5.2) state the right thing. Verdict text "MOSTLY ACCURATE (lower band)".

---

## Mechanical / set-level claims VERIFIED correct

| Claim (doc) | Code evidence | Verdict |
|---|---|---|
| Default realization M42 = `all_sectors_aug13` | `config/default.cfg:1319` `cfg$gms$water_demand<- "all_sectors_aug13"` | ✅ |
| Default realization M43 = `total_water_aug13` | `config/default.cfg:1406` `cfg$gms$water_availability <- "total_water_aug13"` | ✅ |
| q43_water at `equations.gms:10-11`; `sum(wat_dem,vm_watdem)=l=sum(wat_src,v43_watavail)` | `modules/43_water_availability/total_water_aug13/equations.gms:10-11` exact | ✅ |
| 5 water demand sectors (agriculture, manufacturing, electricity, domestic, ecosystem) | `core/sets.gms:247` `wat_dem / agriculture, domestic, manufacturing, electricity, ecosystem /` | ✅ (5) |
| 4 water sources (surface, ground, ren_ground, technical) | `core/sets.gms:244` `wat_src / surface, ground, technical, ren_ground /` | ✅ (4) |
| `watdem_exo` = manufacturing, electricity, domestic, ecosystem | `modules/42_.../all_sectors_aug13/sets.gms:9-10` `/ domestic, manufacturing, electricity, ecosystem /` | ✅ (4) |
| Buffer applies to `watdem_exo`, not agriculture | `presolve.gms:14-16` uses `vm_watdem.lo(watdem_exo,j)` | ✅ |
| Agricultural demand eq at `42/all_sectors_aug13/equations.gms:10-14` | lines 10-14 `q42_water_demand("agriculture",j2)` formula matches | ✅ (eq name `q42_water_demand` not stated by doc, formula correct) |
| Pumping cost eq at `equations.gms:16-17`, `vm_water_cost(i)` | lines 16-17 `q42_water_cost(i2) .. vm_water_cost(i2) =e= ...` | ✅ |
| Exogenous fixation at `presolve.gms:40-54` `vm_watdem.fx(watdem_ineldo,j)=f42_watdem_ineldo(...)` | lines 40-54 (SSP if-block) | ✅ |
| Ecosystem fixation at `presolve.gms:87-88` | lines 87-88 exact | ✅ |
| `s42_watdem_nonagr_scenario` default SSP2 (cites `input.gms:9`) | `input.gms:9` `/ 2 /` (2=SSP2) | ✅ |
| `s42_env_flow_scenario` default = 2 (Smakhtin) (cites `input.gms:22`) | `input.gms:22` `/ 2 /` | ✅ |
| EFP ramp 2025→2040 (cites `input.gms:35-36`) | `input.gms:35` `s42_efp_startyear / 2025 /`, `:36` `s42_efp_targetyear / 2040 /` | ✅ |
| Surface fixation `preloop.gms:8` `im_wat_avail(t,"surface",j)=f43_wat_avail(t,j)` | `preloop.gms:8` exact | ✅ |
| Inactive sources zeroed `preloop.gms:10-12` | `preloop.gms:10-12` exact (ground, ren_ground, technical = 0) | ✅ |
| Buffer mechanism `presolve.gms:14-16` with ×1.01 | `presolve.gms:14-16` exact | ✅ |
| Surface fixation `presolve.gms:8-11` | `presolve.gms:8-11` (4 `.fx` lines) | ✅ |
| Irrigation efficiency block `presolve.gms:12-22` | code block lines 11-22 | ✅ |
| Climate switch `c43_watavail_scenario` (cc/nocc/nocc_hist), default cc | `43/.../input.gms:9` `$setglobal c43_watavail_scenario cc` (verified via sed+grep; rg gave a spurious `%n%` rendering — false-positive, discarded) | ✅ |
| EFP policy switch `c42_env_flow_policy` (off/on/mixed), default off (cites `input.gms:122`) | `42/.../input.gms:122` `$setglobal c42_env_flow_policy off`; presolve.gms:77 checks `"mixed"`; scen42 set `/off,on/` | ✅ |
| `mixed` = development-state dependent (HIC) | `presolve.gms:78` uses `im_development_state` | ✅ |
| `s42_irrig_eff_scenario`, `s42_irrigation_efficiency`, `s42_efp_startyear/targetyear`, `s42_pumping`, `s42_multiplier` (Section 10.2) | `input.gms:14,19,35,36,39,41` all present | ✅ |
| `vm_AEI(j)` real variable, M41 (Sections 9.1, 11.3) | `modules/41_.../static/declarations.gms:13`, `endo_apr13/declarations.gms:19` | ✅ (M41 default = `endo_apr13`, endogenous — doc's "invests/over-invests" narrative valid) |
| `oq43_water`, `ov43_watavail` output vars (R-code Sections 8.3, 9.2) | `43/.../declarations.gms:22-23` | ✅ |
| `vm_prod` from Module 17 (Section 6.5) | declared `modules/17_production/flexreg_apr16/declarations.gms` | ✅ |
| Module 30 (croparea), responds via `vm_area` | dirs `simple_apr24`(default)/`detail_apr24`; `vm_area` used in q42 | ✅ |
| `im_wat_avail` provided by M43, read by M42 for env flows | declared `43/.../declarations.gms`; read `42/.../presolve.gms:58,64` | ✅ |
| `vm_watdem` produced by M42, consumed by M43 | declared M42 only; read in M42+M43 equations.gms ONLY (no phantom/omitted consumers) | ✅ |
| "~200 MAgPIE cells" (Sections 4.3, 8.1) | default cellular input `c200` (`config/default.cfg:26`) | ✅ |
| Irrigation efficiency range ~64%→~90% (Section 6.1) | sigmoid `1/(1+e^((-22160-gdp)/37767))`: gdp=0→0.643, gdp=50k→0.871, →~0.96 | ✅ |
| 7 land types, all endogenous except urban (Section 11.4) | `core/sets.gms:250-251` land = 7 pools | ✅ |

---

## Bugs Found

### Bug WB-1 — "66% default" irrigation efficiency contradicts default config
- **Severity**: Major
- **Trigger**: "Missing default-state caveat (mechanism described as if always active when it's OFF by default)" + "Right concept, wrong number (default value off)".
- **Class**: 13 (wrong parameter default value) / default-state.
- **Doc line**: water_balance_conservation.md:55 — "**Irrigation efficiency**: Accounts for conveyance losses (66% default)".
- **Claim**: 66% is the default irrigation efficiency.
- **Reality**: The default config is `s42_irrig_eff_scenario = 2` (`input.gms:14` `/ 2 /` = "regional static values from CS"), under which efficiency `v42_irrig_eff` is the GDP-based sigmoid (`presolve.gms:13,18`), ranging ≈64-96% — NOT a flat 66%. The 0.66 value (`s42_irrigation_efficiency`, `input.gms:19` `/ 0.66 /`) is applied ONLY when `s42_irrig_eff_scenario = 1` (global static, NON-default; `presolve.gms:15-16`). Section 6.1 of the same doc correctly describes the default as "GDP-based sigmoidal function ... ~64% to ~90%", contradicting Section 2.1.
- **File evidence**: `modules/42_water_demand/all_sectors_aug13/input.gms:14` (scenario default=2), `:19` (s42_irrigation_efficiency=0.66), `modules/42_water_demand/all_sectors_aug13/presolve.gms:13,15-16,18`.
- **verify_cmd**: `grep -n "s42_irrig_eff_scenario\|s42_irrigation_efficiency" /tmp/.../all_sectors_aug13/input.gms` → `14: ... / 2 /`, `19: ... / 0.66 /`; `sed -n '11,22p' .../presolve.gms` → 0.66 used only under `s42_irrig_eff_scenario = 1`.
- **Confirmed**: true.
- **Proposed fix**: Replace "Accounts for conveyance losses (66% default)" with "Accounts for conveyance losses (default: GDP-based sigmoidal efficiency, ~64-90%, via `s42_irrig_eff_scenario = 2`; the flat 0.66 value applies only under the non-default global-static scenario `s42_irrig_eff_scenario = 1`)".

### Bug WB-2 — Section 5.3 "Justification" citation points at unrelated buffer-interface lines
- **Severity**: Major
- **Trigger**: "Citation points at content ... AND the actual cited content says something materially different (citation drift to wrong content)" / "File:line citation drift to adjacent but different content (would mislead a careful reader)".
- **Class**: 10/12 (stale/content-level citation mismatch).
- **Doc line**: water_balance_conservation.md:311 — "**Justification** (Module 43, `modules/43_water_availability/total_water_aug13/realization.gms:40-42`): - Non-agricultural sectors typically have higher economic value - Politically difficult to cut manufacturing/domestic water - Agricultural water use is more elastic (can switch to rainfed, import food)".
- **Claim**: realization.gms:40-42 is the source/justification for the asymmetric (ag-only-constrained) treatment, framed with three economic/political reasons.
- **Reality**: realization.gms:40-42 contains ONLY: "There is an interface to the [42_water_demand] module. If exogenous non-agricultural water demand exceeds available water the missing amount is available from groundwater to avoid infeasibility." The three justification claims (higher economic value / politically difficult / agricultural elasticity) appear NOWHERE in module 43's code or comments. The citation falsely implies code provenance for domain reasoning the code does not state.
- **File evidence**: `modules/43_water_availability/total_water_aug13/realization.gms:40-42`.
- **verify_cmd**: `sed -n '40,42p' .../realization.gms` → buffer-interface text only; `rg -rn "economic value|politically|political|elastic|higher value" /tmp/.../modules/43_water_availability/` → NO_MATCH.
- **Confirmed**: true.
- **Proposed fix**: Either (a) drop the `realization.gms:40-42` citation and reframe as the doc author's interpretation: "**Interpretation** (not stated in code): the asymmetry likely reflects that non-agricultural sectors ...", or (b) keep the citation only for the factual buffer-interface statement and move the three reasons into an explicitly-unsourced "Rationale (domain reasoning, 🔵 general knowledge)" note. Recommended replacement: change the header to "**Rationale** (domain reasoning — NOT in code; the code at `realization.gms:40-42` only documents the buffer interface):" and keep the three bullets.

### Bug WB-3 — "all 195 countries" undercounts the default EFP_countries set
- **Severity**: Minor
- **Trigger**: "Fabricated count for a set/parameter/realization list" (pulled down by tie-breaker: conceptual claim "all countries" is correct; no action depends on the exact number; advisory prose).
- **Class**: 6 (hardcoded counts drift).
- **Doc line**: water_balance_conservation.md:104 — "Country-specific targeting (default: all 195 countries)".
- **Claim**: default EFP applies to all 195 countries.
- **Reality**: The default `EFP_countries(iso)` set lists all 249 ISO codes (the full MAgPIE `iso` set, including territories like AIA, ALA, BES). "All countries" is correct conceptually; the number 195 (UN-member colloquial count) does not match the 249-member iso set.
- **File evidence**: `modules/42_water_demand/all_sectors_aug13/input.gms:52-76` (EFP_countries list); `core/sets.gms:37` iso set (249 members).
- **verify_cmd**: `python3` regex `\b[A-Z]{3}\b` over input.gms lines 51-77 → 249 unique ISO3 tokens; same count for `core/sets.gms` iso set.
- **Confirmed**: true.
- **Proposed fix**: Replace "(default: all 195 countries)" with "(default: all ISO countries/territories — the full 249-member `iso` set)".

---

## Deferred (not code-verifiable / out of scope)

- magpie4 R functions in Sections 8-10 (`water_demand()`, `water_avail()`, `readGDX(...)` syntax/args): downstream R reporting layer; not verifiable against the GAMS worktree. R-code argument correctness (e.g., `field="level"` on a `select=list(type="marginal")` call in Section 8.3) is plausibly imperfect but is illustrative R, not a GAMS claim.
- "cell" vs "cluster" terminology: doc uses "cell" throughout; code/comments say "cluster" (`j2`, equations.gms:13). Standard MAgPIE shorthand; doc's "~200 cells" matches the 200-cluster default. Not flagged as a bug.
- Section 6.4 "No feedback from Module 43 water constraint to Module 41 investment" / "stranded AEI": behavioral/economic interpretation; the variable `vm_AEI` and the area≤AEI constraint (`41/.../equations.gms:11`) are real, but the no-feedback claim is a modeling-judgment statement not directly falsifiable by a single grep. Plausible and consistent with the endo_apr13 cost structure; not flagged.
- Section 7.3 climate-change runoff regional patterns ("+10-30% monsoon Asia" etc.): explicitly labeled "from LPJmL literature", illustrative.
- All "(illustrative)" numbered examples (Sections 5.1, 7.1, 7.2, 7.5, 8.x): explicitly labeled made-up.

---

## Notes on grep reliability during this audit
- `rg` returned a spurious rendering for `43/.../input.gms` showing `$setglobal n cc` when the file actually contains `$setglobal c43_watavail_scenario cc` (confirmed by `sed -n '8,12p'` AND `grep -c` = 3). This is exactly the documented "bare grep -r can silently mislead" hazard. Every absence/identity claim in this report was cross-checked with a second method (sed/Read + grep) and positive controls.
- `EFP_countries` was initially mis-located in sets.gms (it lives in input.gms:52-76); corrected before counting.
