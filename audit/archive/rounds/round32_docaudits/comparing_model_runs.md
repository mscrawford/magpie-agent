# Doc Audit (Round 32): agent/helpers/comparing_model_runs.md

**Target**: `<magpie-agent>/agent/helpers/comparing_model_runs.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop @ `ee98739fd`, "Merge PR #887 from mishkos/f_affexp_policy") + `config/default.cfg`.
**Auditor**: adversarial doc auditor, model Opus 4.8.
**Date**: 2026-05-30.

## Overall Verdict: MOSTLY ACCURATE (high band)
## Accuracy Score: 8/10

This helper is unusually well-grounded. The develop repo ships the entire post-processing framework (`output.R`, `scripts/output/*`, `scripts/output/extra/*`), so most of the doc's script-level claims are directly verifiable — and nearly all check out, including subtle behaviors (comparison-script dispatch, missing-file handling, dedup, the fulldata.gdx-per-timestep overwrite). One file:line citation drifted to materially different content (Major). One prefix claim is slightly imprecise (Minor). The bulk of unverifiable claims live in R packages (magpie4 / quitte / mip / magclass) that are NOT in the GAMS ground truth and are deferred, not flagged.

The pre-run advisory ("Never validated. Verify output-file names, magpie4/report.mif references, and any script/path claims.") is **largely refuted**: output-file names and script/path claims are overwhelmingly correct against develop. The magpie4/report.mif references cannot be verified against the GAMS repo and are deferred (one — `magclass::write.mif` — is very likely a wrong namespace, but I lack reproducible code evidence in the ground-truth tree).

---

## Verified Claims (correct)

### Quick Reference / file table
- **`cfg$title` default `"default"` at `config/default.cfg:17`** — VERIFIED. `17:cfg$title <- "default"`. (`grep -n 'cfg$title' config/default.cfg`).
- **`cfg$results_folder` default `"output/:title::date:"`** — VALUE VERIFIED at `config/default.cfg:2351` (`cfg$results_folder <- "output/:title::date:"`). The placeholder `:title:` is documented at line 2350. **The cited LINE (2298) is wrong** — see Bug CMR-1.
- **`fulldata.gdx`** = complete model state — VERIFIED. `Execute_Unload "fulldata.gdx";` with no symbol list (unloads all symbols) at `core/calculations.gms:92`.
- **`magpie_y<year>.gdx` = per-timestep solver savepoints** — VERIFIED. `option savepoint = 1` (`main.gms:287`); per-year loadpoints `Execute_Loadpoint "magpie_y2000.gdx"` etc. in `core/load_gdx.gms:9,13-20`. Naming `magpie_y<year>.gdx` matches exactly.
- **`cell.land_0.5.mz` (disaggregated 0.5° land)** — file name VERIFIED as a real output (referenced in `scripts/output/extra/disaggregation.R`, `disaggregation_LUH2.R`, and several `projects/*` scripts).
- **`config.yml` loaded with `gms::loadConfig()`** — VERIFIED. `scripts/output/comparison_validation.R:27-29` (`config <- file.path(outputdir,"config.yml"); cfg <- gms::loadConfig(config)`); also `output.R` Step-1 example mirrors this.
- **`full.log` = GAMS log** — file VERIFIED. Produced via `gams full.gms ... -lf=full.log` (`scripts/run_submit/submit.R:36`). (Minor wording note: "listing" maps to `full.lst`, also real, `submit.R:45`; see Deferred.)

### Comparison-script framework
- **Comparison scripts are "marked `comparison script: TRUE` in their YAML header" and "receive all selected output directories at once, whereas single-run scripts are called once per directory" (`output.R:94-98`)** — VERIFIED PRECISELY.
  - `output.R:93` `header <- read_yaml_header(script)`
  - `output.R:94` `comp <- (!is.null(header[["comparison script"]]) && isTRUE(header[["comparison script"]]))`
  - `output.R:95-99` `if(comp){ loop <- list(alloutputdirs) } else { loop <- alloutputdirs }` — i.e. all dirs at once for comparison scripts, one-per-dir otherwise. The 94-98 citation is on-target.

### Built-in comparison scripts (scripts/output/ and extra/)
- **`merge_report.R`: merges `report.rds` into `output/report_all.rds` and `output/report_all.mif`** — VERIFIED, and the doc is MORE accurate than the script's own YAML header. Body reads `report.rds` (`readRDS`, line 40-43), writes `output/report_all.rds` (line 47) and `output/report_all.mif` (line 48). (Script header line 9 mislabels it "Merges report.mif files"; the doc correctly says `.rds`.)
- **`comparison_validation.R`: side-by-side validation PDF via `mip::validationpdf()` with `style="comparison"`, reads each run's `fulldata.gdx` via `magpie4::getReport()`** — VERIFIED at the call level. `library(mip)`, `library(magpie4)` (lines 13-14); `getReport(gdx, ...)` (line 41); `validationpdf(x=x, hist=hist, file=file, style="comparison")` (line 46); per-run gdx path `.../fulldata.gdx` (line 34). (The script as committed has latent code bugs — undefined `outputdirs`/`outputdir_x` — but the doc describes intended behavior; not a doc bug.)
- **`extra/modelstat.R`: compares `modelstat` across runs; warns if any timestep ≠ 2** — VERIFIED. `modelstat(gdx)` (line 40); warn loop over modelstat values ≠ 2 (lines 50-56). Writes CSV (line 45) — see Minor wording note in Deferred re `<project>`.
- **`extra/runtime.R`: compares solve times via `lucode2::readRuntime()` with plot** — VERIFIED. `print(lucode2::readRuntime(outputdir,plot=TRUE))` (line 24).
- **`extra/runtimePR.R`: runtime comparison formatted for PR reviews** — VERIFIED. Header "Compiles model run time for PR" (line 9); writes `output/runtimePR.csv` (line 128).
- **`extra/aff_area.R`: extracts afforestation area; useful template** — VERIFIED. Header "extracts afforstation area from multiple runs ... (useful template for other variables)" (line 9); `land(gdx,level="glo")[,,"forestry"]` (line 45).
- **`extra/ForestChangeCluster.R`: forest change at cluster level** — VERIFIED. Header "Compares Forest Area Change at Cluster Level" (line 9); `land(gdx,level="cell")[,,c("forestry","primforest","secdforest")]` (line 46).
- **`extra/resubmit.R`: re-submits failed runs (operational)** — VERIFIED. Header "re-submits runs to different queues" (line 9); checks modelstat then `sbatch submit_standby.sh` for failed runs (lines 40-50).

### Common Pitfalls
- **#1 `cfg$gms$c_timesteps`** — switch name VERIFIED, `config/default.cfg:133` (`cfg$gms$c_timesteps <- "coup2100"`).
- **#2 `clustermap_*.rds` documents spatial mapping per output folder** — file name VERIFIED as real (referenced in `scripts/output/validation_cell.R`, `extra/land_cluster.R`, `extra/disaggregation*.R`).
- **#3 `cfg$gms$c_past`** — switch name VERIFIED, `config/default.cfg:136` (`cfg$gms$c_past <- "till_2015"`).
- **#4 `ov_` prefix (variables), `vm_*` only last timestep; `ov_*` have all timesteps via `t`** — VERIFIED for the variable side. `ov_land(t,j,land,"level") = vm_land.l(j,land)` (`modules/10_land/landmatrix_dec18/postsolve.gms:26`), declared with leading `t` dim (`declarations.gms:39`). `ov_*` parameters accumulate every timestep in postsolve; raw `vm_*` retain the loop's current (final) state at unload. The `oq_` half is imprecise — see Bug CMR-2.
- **#6 `comparison_validation.R` auto-deduplicates via `make.unique()` (`comparison_validation.R:37-39`)** — VERIFIED. `if(title %in% scenarios){ title <- tail(make.unique(c(scenarios,title),sep=""),n=1) }` at lines 37-39 (make.unique at line 38).
- **#7 `merge_report.R` silently skips folders lacking `report.rds` and lists them at the end** — VERIFIED. `else missing <- c(missing,outputdir[i])` (line 44); `print(missing)` at end (lines 50-53). Doc correctly cites `report.rds` (the script's own comment text at line 51 erroneously says "report.mif").
- **#8 `fulldata.gdx` is overwritten each timestep during a run (`core/calculations.gms:92`)** — VERIFIED. `Execute_Unload "fulldata.gdx";` sits INSIDE the timestep `loop (t$(...) , ...)` (loop opens `core/calculations.gms:40`, closes line 101), so it is re-written at the end of every timestep iteration. `magpie_y1995.gdx` removal in resubmit.R:47 corroborates the savepoint context.

---

## Bugs Found

### Bug CMR-1 (Major) — file:line citation drift to materially different content
- **Severity**: Major. **Trigger** (§1 Major): "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different (citation drift to wrong content)."
- **Class**: 10 (Stale file:line citation).
- **Doc line**: `comparing_model_runs.md:10`.
- **Claim in doc**: "...configured via `cfg$results_folder` in `config/default.cfg:2298`, which defaults to `"output/:title::date:"`)."
- **Reality in code**: `cfg$results_folder <- "output/:title::date:"` is at `config/default.cfg:2351`, NOT 2298. Line 2298 contains an unrelated solver scalar: `cfg$gms$s80_optfile <- 1 # def = 1`. The DEFAULT VALUE quoted (`"output/:title::date:"`) is correct; only the line number is wrong, and it points at materially different content.
- **File evidence**: `config/default.cfg:2351` (`cfg$results_folder <- "output/:title::date:"`); `config/default.cfg:2298` (`cfg$gms$s80_optfile <- 1 # def = 1`).
- **verify_cmd**: `grep -n 'results_folder' config/default.cfg` → `2351:cfg$results_folder <- "output/:title::date:"` (and `2357:cfg$results_folder_highres <- NULL`); `sed -n '2294,2302p' config/default.cfg` → line 2298 is `cfg$gms$s80_optfile <- 1 # def = 1`.
- **Confirmed**: true.
- **Proposed fix**: Replace `config/default.cfg:2298` with `config/default.cfg:2351` in the sentence on line 10. (The companion `cfg$title` citation `config/default.cfg:17` is correct and needs no change.)

### Bug CMR-2 (Minor) — imprecise output-parameter prefix for equations (`oq_`)
- **Severity**: Minor (tie-breaker pulls down from Major; the prefix-family characterization is substantively correct and the timestep claim is right). **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding" — except a reader who literally `grep`s `oq_` finds nothing, hence Minor rather than Informational.
- **Class**: 3 (Suffix/prefix truncation) / general prefix imprecision.
- **Doc line**: `comparing_model_runs.md:247`.
- **Claim in doc**: "Output parameters use `ov_` prefix (variables) and `oq_` prefix (equations)."
- **Reality in code**: There is NO bare `oq_*` symbol anywhere in the codebase. Equation-output parameters are always module-numbered: `oq<NN>_*` (e.g., `oq21_notrade`, `oq21_trade_reg` at `modules/21_trade/selfsuff_reduced_bilateral22/postsolve.gms:16-18`; families `oq10_`, `oq11_`, `oq13_`, `oq14_`, `oq15_`, `oq16_`, `oq17_`, `oq18_`, `oq20_`, `oq21_`, ... across 52 postsolve files). The variable side is split: bare `ov_*` DOES exist for interface variables (524 occurrences, e.g., `ov_land`), and module-local variable outputs use `ov<NN>_*` (e.g., `ov21_trade`). So the doc's `ov_`/`oq_` is correct as a prefix-*family* gloss, but the literal trailing-underscore form is real only for `ov_` (interface vars); for equations it is `oq<NN>_`.
- **File evidence**: `modules/21_trade/selfsuff_reduced_bilateral22/postsolve.gms:16` (`oq21_notrade(t,h,k_notrade,"marginal") = q21_notrade.m(h,k_notrade);`); `modules/10_land/landmatrix_dec18/postsolve.gms:26` (`ov_land(t,j,land,"level") = vm_land.l(j,land);`).
- **verify_cmd**: `grep -rln "oq_" . --include="*.gms"` → (empty, exit 0); cross-checked `rg -ln "oq_" modules/` → (empty) with positive control `rg -ln "ov_land\b" modules/` → 2 files. Then `grep -rhoE "\boq[0-9]*_[a-z]" modules/*/*/postsolve.gms | sed -E 's/^(oq[0-9]*_).*/\1/' | sort | uniq -c` → `oq10_ oq11_ oq13_ ... oq21_` (all module-numbered, none bare).
- **Confirmed**: true.
- **Proposed fix**: Change the sentence to: "Output parameters use the `ov` prefix for variable snapshots (interface vars as `ov_*`, e.g. `ov_land`; module-local as `ov<NN>_*`) and the `oq` prefix for equation snapshots (always module-local, e.g. `oq21_notrade`). Raw GAMS variables use `vm_` (global), `v_` (local)." (Or, minimally, replace ``and `oq_` prefix (equations)`` with ``and `oq<NN>_` prefix (equations, e.g. `oq21_notrade`)``.)

---

## Deferred (NOT code-verifiable against the GAMS ground truth — do NOT edit on this basis)

These claims live in R packages (magpie4, quitte, mip, magclass, lucode2) whose source is not in `/tmp/magpie_develop_ro`. The develop output scripts *call* some of them, which corroborates existence, but signatures/namespaces/exact strings require the package sources (preproc-agent / magpie4_reference territory).

1. **`merge_report.R` "Uses `magclass::write.mif()`"** (doc line 86). The call is bare `write.mif(out, "output/report_all.mif")` (`merge_report.R:48`), on a quitte object, with `library(quitte)` loaded (line 18). Strong domain signal that `write.mif` is exported by **quitte**, not magclass (cf. `rds_report.R:43` uses `magclass::write.report()` for the magclass-object path). LIKELY a wrong-namespace attribution, but I cannot read the quitte/magclass NAMESPACE in the ground-truth tree (no `renv/library` installed), so NOT flagged as a confirmed bug. If the maintainer wants this fixed: verify `write.mif` is in quitte and change `magclass::write.mif()` → `quitte::write.mif()` on doc line 86.
2. **magpie4 function names/signatures**: `land(gdx, level=...)`, `costs()`, `emissions()`, `demand()`, `production()`, `Kcal()`, `croparea()`, `modelstat()`, `getReport()` (doc lines 87, 129-147, 207-232). `land`, `croparea`, `modelstat`, `getReport`, `Kcal` are *used* in develop output scripts (corroborates existence + `level=` arg for `land`); `costs`/`emissions`/`demand`/`production` are not called in any develop output script, so their names/levels/units are unverified here. Route to `agent/helpers/magpie4_reference.md` if exact verification is needed.
3. **`mip::validationpdf()` signature / `style="comparison"` semantics** (doc lines 87, 160-162) — the develop call confirms the function and the `style="comparison"` argument exist (`comparison_validation.R:46`); deeper semantics are in the `mip` package.
4. **report.mif IAMC variable strings and units** (doc lines 207-235): `Land Cover|Cropland`, `Emissions|CO2|Land` (Mt CO2/yr), `Per-capita calories` (kcal/cap/day), `Total costs` (million USD17MER/yr), `Trade|*`, etc. These are produced by magpie4 `report*` functions, not GAMS; only `million USD17MER` appears in GAMS declarations (e.g., `ov_cost_land_transition ... (mio. USD17MER per yr)`), consistent with the doc. Exact IAMC labels require magpie4.
5. **`full.log` described as "GAMS listing/log output"** (doc line 20): `full.log` is the GAMS *log* (`-lf=full.log`); the *listing* is `full.lst` (both real). Mild wording conflation, not a path error — left as a note, not a bug.
6. **`modelstat_<project>.csv`** (doc line 93): actual code writes `./output/modelstat_<basename(getwd())>.csv` (`modelstat.R:45`). `<project>` is a reasonable gloss for the working-dir basename; not flagged.
7. **`gms::loadConfig()`, `lucode2::readRuntime()`, `lucode2::readArgs()`, submission modes (`direct`/`background`/SLURM via `scripts/slurmOutput.yml`)** — all corroborated by develop usage (`output.R`, the extra scripts); deeper package semantics not audited.

---

## Summary
Strong, well-grounded helper. 1 Major (citation drift: `cfg$results_folder` cited at `config/default.cfg:2298`, actually line 2351 — line 2298 is `s80_optfile`; the default value is correct). 1 Minor (`oq_` prefix is really `oq<NN>_`, e.g. `oq21_notrade`; `ov_` interface form is fine). Every script-behavior, output-filename, GAMS-side prefix, and config-switch claim verified against develop @ ee98739fd. R-package claims (magpie4/quitte/mip namespaces, signatures, IAMC strings) deferred — not verifiable against the GAMS ground truth; the `magclass::write.mif` namespace is the most likely latent error among them.
