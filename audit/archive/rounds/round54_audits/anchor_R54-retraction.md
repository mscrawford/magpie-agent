# Audit Report: R54-retraction (c32_aff_policy = ndcdelay — works or silently broken?)

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: FALSE

This is the R53-retraction calibration anchor. It guards against the flywheel
resurrecting the retracted "ndcdelay is silently broken" false-bug report (the
R53 Critical: every premise TRUE, conclusion FALSE, because the frame stopped
at the GAMS consumer layer and never found the R producer that regenerates the
.cs3 at run start).

The audited answer matches the expected ground-truth summary on every
load-bearing dimension and does NOT resurrect the retracted claim. It opens
"It works, under the default configuration," explicitly flags the retraction,
and cleanly separates "works by default" from the one narrow non-default
footgun. No bugs (0 Critical, 0 Major, 0 Minor).

---

## Verified Claims (all confirmed against read-only develop tree /tmp/magpie_develop_ro)

| # | Claim in answer | Code evidence | Status |
|---|---|---|---|
| 1 | Works by default; "ndcdelay silently broken" verdict superseded | (anchor) — regeneration mechanism below | ✓ core anchor |
| 2 | `pol32 = none, npi, ndc, affexp, ndcdelay` | `modules/32_forestry/dynamic_may24/sets.gms:19-20` | ✓ exact |
| 3 | Pure data lookup, zero GAMS branch: `p32_aff_pol(t,j) = round(f32_aff_pol(t,j,"%c32_aff_policy%"),6);` at preloop.gms:182 | `.../dynamic_may24/preloop.gms:182` | ✓ EXACT string |
| 4 | Default `c32_aff_policy = npi` | `.../dynamic_may24/input.gms:9` (`$setglobal c32_aff_policy npi`); `config/default.cfg:1026` | ✓ exact |
| 5 | `.cs3` gitignored, regenerated at run start under default `cfg$recalc_npi_ndc <- "ifneeded"` (config/default.cfg:123) | `config/default.cfg:123` (`cfg$recalc_npi_ndc <- "ifneeded"`) | ✓ exact line |
| 6 | Regeneration guards `affexp_missing`, `ndcdelay_missing` in `scripts/start_functions.R` | `scripts/start_functions.R:380-388` | ✓ exact names |
| 7 | Guard fires when all-zero (`all(aff_pol==0) && c32_aff_policy!="none"`) OR selected column missing | `scripts/start_functions.R:385-388`, sets `cfg$recalc_npi_ndc <- TRUE` at :390 | ✓ exact logic |
| 8 | FOOTGUN: override `cfg$recalc_npi_ndc <- FALSE` skips regeneration → every policy (incl. default npi) reads zero = `none`, no error/warning | `start_functions.R:375` guard block only entered when =="ifneeded"; FALSE bypasses it | ✓ core anchor footgun |
| 9 | ndcdelay lands in `"ndc"` type32 slot | q32_aff_pol uses `v32_land(j2,"ndc",ac_est)` (equations.gms:75); `type32 / aff, ndc, plant /` (sets.gms:16-17) | ✓ |
| 10 | Unreachable target → no infeasibility; residual in `v32_ndc_area_missing` slack priced at `s32_free_land_cost` (~$1M/ha) | `equations.gms:75` (=e= slack term), `equations.gms:26` (× s32_free_land_cost), `input.gms:33` (/ 1e+06 /) | ✓ |
| 11 | Check `ov32_ndc_area_missing` post-run | `postsolve.gms:29,78,127,176` | ✓ |
| 12 | 3%/yr `s32_annual_aff_limit` constrains ONLY the `"aff"` carbon-price type, not ndc-type | `q32_co2p_aff_limit` constrains `vm_landexpansion_forestry(j2,"aff")` (equations.gms:84-86); default 0.03 (input.gms:50); q32_aff_pol has no such cap | ✓ |
| 13 | `q32_ndc_aff_limit` ties non-zero policy flow to zero natforest reduction | `equations.gms:79-80`: `sum(ct,p32_aff_pol_timestep)*vm_natforest_reduction =e= 0` | ✓ |
| 14 | `s32_npi_ndc_reversal` default `Inf` (never), separate from ndcdelay | `input.gms:48` (`/ Inf /`) | ✓ |
| 15 | affexp + ndcdelay wired into scenario presets at `config/scenario_config.csv:51` | line 51 `gms$c32_aff_policy;...;none;npi;npi;ndc;affexp;ndcdelay;...` | ✓ EXACT |
| 16 | Cross-ref: separate channel from carbon-price `vm_reward_cdr_aff` reward | `vm_reward_cdr_aff` present in modules/56_ghg_policy/price_aug22/{equations,declarations,postsolve}.gms | ✓ exists |
| 17 | ndcdelay derived in R from ndc rows (start_npi_ndc.R) | file exists at `scripts/npi_ndc/start_npi_ndc.R` | ✓ exists (answer cited bare filename) |

## Mechanical checks
- M1 (file:line citations present): PASS (preloop.gms:182, config/default.cfg:123, scenario_config.csv:51, etc.)
- M2 (active realization): N/A — module 32 has a SINGLE realization `dynamic_may24`; no ambiguity/cascade risk. Answer cites its files. Satisfied.
- M3 (variable prefixes valid): PASS (vm_, v32_, s32_, p32_, q32_, f32_, ov32_ all consistent)
- M4 (epistemic badges): PASS (🟡 Documented; 🔴 on retracted-claim framing)
- M5 (tier matches depth): PASS — claims labeled 🟡 documented, does NOT overclaim 🟢; footer honestly states no code read this session
- M6 (closing source statement): PASS ("🟡 Documented — modules/module_32.md ...")

## Bugs Found
None. Zero Critical, zero Major, zero Minor.

## Non-scoring nuances (not bugs)
- "(default is `npi` — you must set it explicitly)" is awkwardly worded; read in
  context it means "to select a non-default policy set it explicitly," which is
  correct for the user's ndcdelay goal. A careful reader is not misled (they know
  they must set `c32_aff_policy=ndcdelay`). Not recordable.
- Commit SHAs `a54cd02c6`, `58bde5788` (attributed as adding the guards) are
  historical claims not re-verified this audit; not load-bearing for
  current-behavior guidance and not flagged wrong. The guard NAMES they reference
  are verified present.
- The retraction-narrative specifics about the shipped dummy ("3-column",
  "6405 lines", "ndcdelay appears 0 times") describe the gitignored file (in the
  parent tree, not the worktree). They are internally consistent with ground
  truth: an all-zero 3-column dummy (npi/ndc/affexp filled with zeros, ndcdelay
  column absent) fires BOTH the `all(aff_pol==0)` and `ndcdelay_missing` triggers
  — exactly the duality the answer describes. Consistent, not independently
  re-verified here, not a bug.

## Summary
A near-exemplary anchor answer. It reproduces the corrected R53 understanding in
full: (1) c32_aff_policy is a pure data lookup with no GAMS branch; (2) the
policy's substance is a column of the run-time-regenerated npi_ndc_aff_pol.cs3;
(3) regeneration is forced by the default `ifneeded` guard on all-zero or
missing-column; (4) the ONLY footgun is the non-default `recalc_npi_ndc<-FALSE`
override, which zeroes EVERY policy including default npi. It does not resurrect
the retracted "broken" claim — it names and explains the retraction. Every
file:line citation I spot-checked against code was exact. Score 10/10,
drift_observed=FALSE. The anchor is holding; nothing near it appears broken this
round.
