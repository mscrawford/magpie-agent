# Round 39 Adversarial Verification — Verification_Protocol.md

Target doc: `reference/Verification_Protocol.md` (332 lines)
Ground truth: `/tmp/magpie_develop_ro` (MAgPIE develop, read-only)
Verifier posture: mechanical-first, default-skeptical. Every cited file/line re-read; every existence/absence claim cross-checked with a second method + positive control.

## Summary

| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| VP-1 | realization_structure | true | UPHELD |
| VP-2 | producer_declaration | true | UPHELD |
| VP-3 | other (content/citation mismatch) | true | UPHELD |
| VP-4 | other (doc-internal xref) | true | UPHELD |
| VP-5 | producer_declaration | true | UPHELD |

All five UPHELD. Every proposed-fix citation also mechanically verified to exist, be in range, and contain the claimed token. The fixes are safe to apply.

---

## VP-1 — Wrong module/realization name `22_biodiversity` (UPHELD)

Doc lines 199, 200, 218 cite `modules/22_biodiversity/bv_btc_mar21/equations.gms:NN`.

STEP A — mechanical citation check:
- `test -d /tmp/magpie_develop_ro/modules/22_biodiversity` -> DOES NOT EXIST.
- `ls modules/22_land_conservation/*/` -> only `area_based_apr22/` (+ `input/`). Module 22 = land_conservation.
- `test -f modules/44_biodiversity/bv_btc_mar21/equations.gms` -> EXISTS, 25 lines. The `bv_btc_mar21` realization lives under module 44.
- Proposed fix cites `44_biodiversity/bv_btc_mar21/equations.gms:11-13`; `sed -n '11,13p'` returns:
  `q44_cost_bv_loss(j2) .. vm_cost_bv_loss(j2) =e= v44_bv_loss(j2) * sum(ct, p44_price_bv_loss(ct));` — real equation, in range.
- Doc self-contradiction confirmed: line 232 correctly writes `22_land_conservation/area_based_apr22`. Config `config/default.cfg:711,714` confirms `22_land_conservation`, default realization `area_based_apr22`.

STEP B/C — realization_structure: the file `bv_btc_mar21/equations.gms` belongs to module 44, NOT module 22. The auditor's reality reproduces exactly. UPHELD. Fix path `modules/44_biodiversity/bv_btc_mar21/equations.gms` is correct; `:11-13` is the verified line range for q44_cost_bv_loss (note: VP-5 separately replaces the q22_bii placeholder, so VP-1 and VP-5 must be applied together to make the exemplar self-consistent).

---

## VP-2 — Stale `vm_land` declaration citation (UPHELD)

Doc line 258: "declared in `modules/10_land/*/declarations.gms:67`".

STEP A — mechanical citation check:
- `test -f modules/10_land/landmatrix_dec18/declarations.gms` -> EXISTS, `wc -l` = 52.
- Line 67 is OUT OF RANGE (file is 52 lines); `sed -n '67p'` returns empty.
- `rg -n 'vm_land' .../declarations.gms` -> `19: vm_land(j,land)  Land area of the different land types (mio. ha)`. `sed -n '19p'` confirms the exact token `vm_land(j,land)` is on line 19.
- Module 10 has exactly one code realization: `ls modules/10_land/*/` -> `landmatrix_dec18/` (+ `input/`). The `*` glob resolves to a single dir, so the doc's own full-path rule (line 198) is violated by the `*`.

STEP B/C — producer_declaration: `vm_land(j,land)` is DECLARED at `landmatrix_dec18/declarations.gms:19`. UPHELD.
corrected citation = `modules/10_land/landmatrix_dec18/declarations.gms:19`.

---

## VP-3 — Content mismatch at input.gms:34 + hallucinated `f22_bii` (UPHELD)

Doc line 232: "`f22_bii(land)` ... Source: `input/f22_bii.csv`, loaded in `modules/22_land_conservation/area_based_apr22/input.gms:34`".

STEP A — mechanical citation check:
- `test -f modules/22_land_conservation/area_based_apr22/input.gms` -> EXISTS, 70 lines.
- `sed -n '30,38p'` -> ISO-3166 country codes (line 34 = `GRD,GRL,GTM,GUF,GUM,GUY,HKG,HMD,HND,HRV,`). NOT a BII load. Content mismatch confirmed.
- `rg -n 'f22_bii' modules/` (recursive, ripgrep) -> NO MATCHES. Cross-checked second method below.
- Positive control: `rg -n 'f22_' .../area_based_apr22/input.gms` -> matches `f22_wdpa_baseline`, `f22_consv_prio` (search works in that dir; absence of f22_bii is real, not a silent-empty grep).
- Proposed fix target: `rg -n 'f44_bii_coeff' modules/44_biodiversity/bv_btc_mar21/input.gms` -> `17:$include "./modules/44_biodiversity/bv_btc_mar21/input/f44_bii_coeff.cs3"`. `sed -n '17p'` confirms token on line 17; file is 27 lines (in range).

STEP B/C — other (content-level citation mismatch + nonexistent name; f22_bii is on the line-3 allowlist so the name-checker skips it, but the citation-to-content at :34 is independently wrong). Citation already validated in Step A. UPHELD. Real replacement `f44_bii_coeff` ... `modules/44_biodiversity/bv_btc_mar21/input/f44_bii_coeff.cs3`, loaded at `.../input.gms:17` is correct. Note: the real input file is `.cs3`, not `.csv`.

---

## VP-4 — Broken cross-reference to `archive/MODULE_59_ERRORS_FOUND.md` (UPHELD)

Doc line 190: "See: `archive/MODULE_59_ERRORS_FOUND.md` for example".

STEP A — mechanical citation check:
- `find /Users/turnip/.../magpie-agent -iname '*MODULE_59*'` -> returns `modules/module_59.md`, `modules/module_59_notes.md`, `audit/archive/rounds/round34_answers/module_59.md`, `audit/archive/rounds/round34_docaudits/module_59.md`. NONE is `MODULE_59_ERRORS_FOUND.md`.
- Positive control: the same `find` DID return other module_59 files, proving the search works; the specific ERRORS_FOUND file is genuinely absent. Cross-checked: no `archive/MODULE_59_ERRORS_FOUND.md` path anywhere.

STEP B/C — other (doc-internal cross-reference to a magpie-agent repo file, not GAMS structure). The referenced file does not exist. UPHELD. Recoverable replacement `modules/module_59_notes.md` exists (verified above); or remove the line. (Minor severity stands — it is a dangling pointer, not a code-fact error.)

---

## VP-5 — Hallucinated identifiers in gold-standard examples (UPHELD)

Doc lines 212/215 (`q22_bii`/`vm_bii`/`f22_bii`), 248 (`pm_carbon_density(t,j,"forestry",c_pools)`), 253 (`f35_fire_loss(t,j)` cited at `pot_forest_may24/input.gms:45`).

STEP A — mechanical citation checks (existence/absence, each cross-checked + positive control):

(a) Biodiversity:
- `rg -n 'vm_bii|q22_bii' modules/` -> NO MATCHES (neither exists).
- `q44_bii` exists ONLY in non-default `bii_target` (`rg -ln 'q44_bii'` -> `bii_target/{postsolve,declarations,equations}.gms` only; NOT in default `bv_btc_mar21`). Matches auditor.
- Fix target `bv_btc_mar21/equations.gms:21-23` -> `q44_bv_weighted(j2) .. v44_bv_weighted(j2) =e= f44_rr_layer(j2) * sum((potnatveg,landcover44), vm_bv(j2,landcover44,potnatveg));`. Real identifiers `q44_bv_weighted`, `f44_rr_layer`, `vm_bv` all present and in range. (The equation LHS variable is `v44_bv_weighted`; `vm_bv` is the underlying interface var on the RHS — both real, so the auditor's proposed names are sound.)

(b) Carbon density:
- `rg -n 'pm_carbon_density\(' modules/` -> NO MATCHES for the BARE name `pm_carbon_density(`.
- Real names (positive evidence): `52_carbon/normal_dec17/declarations.gms:9` = `pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)` (and `_other_ac`, `_plantation_ac`, etc. on lines 9-13). `32_forestry/dynamic_may24/declarations.gms:20` = `p32_carbon_density_ac_forestry(t_all,j,ac)`. Both fix-target citations verified on the exact lines and in range; `dynamic_may24` is M32's only code realization.

(c) Fire loss:
- `rg -n 'f35_fire_loss' modules/` -> NO MATCHES.
- Real: `35_natveg/pot_forest_may24/input.gms:32` = `table f35_forest_lost_share(i,driver_source) Share of area damaged by forest fires (1)` (and `:34` includes `f35_forest_lost_share.cs3`). The doc's CITED `:45` = `$ondelim` — inside the include/table region, NOT an `f35_fire_loss` definition. Confirms the citation does not support the claimed identifier.

STEP B/C — producer_declaration: the three placeholder identifiers are not declared anywhere in develop; the real declaring modules/files are as the auditor states (M44 bv_btc_mar21 for biodiversity; M52 normal_dec17 / M32 dynamic_may24 for carbon density; M35 pot_forest_may24 for forest-loss share). UPHELD. f22_bii / f35_fire_loss / pm_carbon_density are on the line-3 allowlist (`<!-- check-gams-vars: allow f22_bii,f35_fire_loss,pm_carbon_density -->`), correctly down-tiering this to Minor; vm_bii / q22_bii are NOT allowlisted, so the auditor's note to either replace them with real identifiers or extend the allowlist marker is well-founded. Preferred fix = replace placeholders with the verified real identifiers so the gold-standard examples are themselves verifiable.

---

## Cross-cutting note for the fixer

VP-1, VP-3, VP-5 all touch the same biodiversity exemplar block (doc lines ~199-232). They must be applied together: after fixing, the block should consistently reference module 44 (`44_biodiversity/bv_btc_mar21`), the real equation `q44_bv_weighted` / `q44_cost_bv_loss`, the real variable `vm_bv` / `vm_cost_bv_loss`, and the real input `f44_bii_coeff.cs3`. Leaving any one unfixed reintroduces the self-contradiction (line 232 already correctly says `22_land_conservation`).
