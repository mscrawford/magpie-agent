# Round 54 — Adversarial Verification: `modules/module_32_notes.md`

**Verifier**: Opus 4.8 (adversarial, mechanical-first)
**Date**: 2026-07-14
**Ground truth**: `/tmp/magpie_develop_ro` @ `0d7ebeb90` (git-tracked code, config, R layer)
**Secondary ground truth (unavoidable)**: the working tree `/Users/turnip/Documents/Work/Workspace/magpie` for the **gitignored** `*.cs*` artifacts. `.gitignore:7` = `*.cs*`, so `npi_ndc_aff_pol.cs3` and `policy_definitions.csv` **cannot** exist in the RO worktree (verified: `MISSING` there, present in the working tree). Any claim about the *content* of a downloaded input is only checkable on disk. This is stated explicitly because the whole bug cluster turns on it.

**Bottom line**: 3 UPHELD, 1 CORRECTED (prose miscount only; its fix text is safe). All 4 pass the mechanical citation check. The auditor's central empirical claim — **the shipped `.cs3` is an all-zero dummy** — reproduced under two independent methods with a passing positive control.

---

## STEP A — Mechanical citation check (all bugs)

| Cited location | exists? | in range? | line contains claimed token? |
|---|---|---|---|
| `modules/32_forestry/input/files:5` | ✅ (9 lines) | ✅ | ✅ `npi_ndc_aff_pol.cs3`; line 1 = `* list of files that are required here` |
| `scripts/start_functions.R:192` | ✅ (674 lines) | ✅ | ✅ `filemap <- gms::download_distribute(files        = cfg$input,` |
| `config/default.cfg:119` | ✅ (2443 lines) | ✅ | ✅ `# * (ifneeded): NPI/NDC recalculation will only be executed if current input files are zero` |
| `config/default.cfg:1026` | ✅ | ✅ | ✅ `cfg$gms$c32_aff_policy <- "npi"              # def = "npi"` |
| `scripts/start_functions.R:366-369` | ✅ | ✅ | ✅ `if(!setequal(cfg$input, input_old) | cfg$force_download) { download_and_update(cfg) }` |
| `scripts/start_functions.R:375` | ✅ | ✅ | ✅ `if(cfg$recalc_npi_ndc=="ifneeded") {` |
| `scripts/start_functions.R:385-388` | ✅ | ✅ | ✅ the disjunction; :385 = `if((all(aff_pol == 0)  && (cfg$gms$c32_aff_policy != "none"))  ||` |
| `scripts/npi_ndc/start_npi_ndc.R:351` | ✅ (533 lines) | ✅ | ✅ `write.magpie(round(aff_pol, 6), afffiles[1])` — **no `comment=` argument** |
| `modules/32_forestry/dynamic_may24/sets.gms:19-20` | ✅ (51 lines) | ✅ | ✅ `pol32 afforestation policy type` / `/ none, npi, ndc, affexp, ndcdelay /` |
| `config/scenario_config.csv:51` | ✅ (82 lines) | ✅ | ✅ `gms$c32_aff_policy;…;none;npi;npi;ndc;affexp;ndcdelay;…` |
| `.gitignore:7` | ✅ (43 lines) | ✅ | ✅ `*.cs*` |
| on-disk `modules/32_forestry/input/npi_ndc_aff_pol.cs3:1-3` | ✅ (6405 lines, working tree) | ✅ | ✅ exact — see below |
| on-disk `scripts/npi_ndc/policies/npi_ndc_aff_pol.cs3:1` | ✅ (6401 lines, working tree) | ✅ | ✅ `dummy,dummy,none,npi,ndc` (no comment block) |

**citation_ok = true for all four bugs.** No fabricated path, no out-of-range line, no missing token.

The on-disk input header, verbatim (lines 1-5):

```
* description: Dummy file for NPI/INDC policies
* unit: dummy (none)
* origin: calcOutput(type = "NpiNdcAffPol", aggregate = "cluster", file = "npi_ndc_aff_pol_c200.mz", round = 5, outputStatistics = c("summary", "sum"), cells = "lpjcell") (madrat 3.35.1 | mrmagpie 1.64.2)
* creation date: Sun Mar 15 18:40:25 2026
dummy,dummy,none,npi,ndc
```

---

## STEP C — Independent re-derivation of the shared empirical crux

Everything in this cluster rests on one factual claim: **what the input download actually ships.** I re-derived it from scratch rather than trusting the auditor.

### 1. The on-disk input IS the current default download (not a leftover)

- `input/info.txt` → `Used data set: rev4.131_h12_magpie.tgz`, which is exactly `cfg$input` regional in `config/default.cfg:25`.
- It carries a madrat/mrmagpie provenance comment block (`* origin: calcOutput(type = "NpiNdcAffPol"…)`), which only `download_distribute` places.
- It is in the git-tracked per-module download manifest `modules/32_forestry/input/files:5`.

### 2. That download is ALL-ZERO — two methods + positive control

```bash
# method 1: field-wise
awk -F',' '/^\*/{next} !h{h=1;next} {n++; if($3+0)a++; if($4+0)b++; if($5+0)c++} END{...}' <input.cs3>
#   -> data rows: 6400 | none nonzero: 0 | npi nonzero: 0 | ndc nonzero: 0

# method 2: line-shape
grep -v '^\*' <input.cs3> | tail -n +2 | grep -v -c ',0,0,0$'
#   -> 0   (zero rows fail to end in ",0,0,0")

# POSITIVE CONTROL — same probe on the regenerated sibling:
awk -F',' '/^\*/{next} !h{h=1;next} {for(i=3;i<=NF;i++) if($i+0) n++} END{print n+0}' \
  scripts/npi_ndc/policies/npi_ndc_aff_pol.cs3
#   -> 8260 nonzero entries   => the probe CAN see nonzeros; "0" on the download is real, not a broken search.
```

### 3. The two files are genuinely distinguishable — and the `policies/` copy is genuinely a regeneration leftover

I did not take the auditor's word for it. `scripts/npi_ndc/policies/files` (git-tracked manifest) lists **only** `country2cell.rds` and `policy_definitions.csv` — `npi_ndc_aff_pol.cs3` is **not** downloaded into that directory. Its only producer is `write.magpie(…, afffiles[1])` at `start_npi_ndc.R:351`, where `outfolder_aff[1] = "policies/"` (`:22`). So it is a run-time product, and it has:

| | `modules/32_forestry/input/…cs3` | `scripts/npi_ndc/policies/…cs3` |
|---|---|---|
| comment block | **4 lines**, `* origin: calcOutput(…)` | **0 lines** |
| lines | 6405 (4 + header + 6400) | 6401 (header + 6400) |
| policy columns | `none,npi,ndc` | `none,npi,ndc` |
| nonzero npi / ndc | **0 / 0** | **3930 / 4330** |
| provenance | the **download** (all-zero dummy) | a **previous regeneration** (real numbers, pre-PRISMA) |
| cell order | sorted (CAZ_1, CAZ_2, …) | scrambled (OAS_125, REF_138, …) |

This is a stronger confirmation than the auditor had: the leftover is not merely comment-less, it holds **real policy data**. Both provenances yield a 3-column header — so column count alone is a useless discriminator, exactly as B2 argues.

### 4. The regenerator overwrites the download in the model dir

`start_npi_ndc.R:352` — `if(length(afffiles) > 1) for (i in 2:length(afffiles)) file.copy(afffiles[1], afffiles[i], overwrite=TRUE)`, with `outfolder_aff = c("policies/", "../../modules/32_forestry/input/")` (`:22`). Called from `start_functions.R:434-439` under `if(cfg$recalc_npi_ndc)`. So the file GAMS `$include`s (`dynamic_may24/input.gms:73`, table `f32_aff_pol(t_all,j,pol32)` at `:71`) is a run-time product **and** a download. Both. Confirmed.

### 5. Ordering: download runs BEFORE the guard

`:366-369` (`download_and_update`) precedes `:375` (`if(cfg$recalc_npi_ndc=="ifneeded")`). With `cfg$recalc_npi_ndc <- FALSE`, the `375` block never executes, so `434` is FALSE and no regeneration occurs — GAMS reads whatever is on disk. On a fresh clone / after any `cfg$input` change / `force_download`, that is the all-zero dummy, for **every** policy including the default `npi`. B3's scope claim is structurally confirmed.

### 6. Supporting facts checked while I was there (fixes depend on them)

- `dynamic_may24/input.gms:9` = `$setglobal c32_aff_policy  npi` (GAMS-side default agrees with `default.cfg:1026`).
- `c32_aff_policy` appears in `modules/` at exactly two places — `input.gms:9` and `preloop.gms:182` (`p32_aff_pol(t,j) = round(f32_aff_pol(t,j,"%c32_aff_policy%"),6);`). Positive control: `f32_aff_pol` grep returns hits in the same dirs. The doc's "zero `$if` branches" claim stands.
- The **downloaded** `policy_definitions.csv` contains **238 `affexp` rows** (e.g. `ZWE,affore,affexp,1,2030,NA,16|0.8`). So the regeneration really can emit an `affexp` column — the fixes' "regenerated with the needed column" is not hypothetical. `ndcdelay` needs no rows (derived in R from `ndc`; `start_npi_ndc.R:346-348`).

---

## Per-bug verdicts

### M32N-B1 — UPHELD (Major)
**Class**: producer_declaration (provenance of an input artifact). **citation_ok**: true.

`npi_ndc_aff_pol.cs3` is **both** a downloaded input **and** a run-time-overwritten artifact. The doc's line 22 ("a generated artifact, **not an input you download**") is a false absolute, and it contradicts the doc's own line 32, which correctly says `policy_definitions.csv` is "delivered by the input download" — both files ride the identical `download_distribute` machinery (`modules/32_forestry/input/files:5`; `scripts/npi_ndc/policies/files:2`). Apply the fix as written.

### M32N-B2 — UPHELD (Major)
**Class**: producer_declaration. **citation_ok**: true.

A 3-column `dummy,dummy,none,npi,ndc` header is the **normal freshly-downloaded state**, not a stale previous-run artifact. The doc's conclusion (affexp/ndcdelay are usable) is right; its stated reason is wrong. Fix text is accurate.

**⚠️ Fixer interaction — must apply B2 and B3 together.** The doc's current recipe at line 40 is:
```bash
head -5 modules/32_forestry/input/npi_ndc_aff_pol.cs3 | grep -v '^\*'
```
That `grep -v '^\*'` **strips the very comment block** that B2 tells the reader to use as the discriminator. B3's fix replaces this snippet (plain `head -5`, no filter) — so B2's advice is only actionable if B3's snippet replacement lands too. Applying B2 alone leaves the doc self-defeating.

### M32N-B3 — UPHELD (Major)
**Class**: producer_declaration (what the producer ships + producer/guard execution order). **citation_ok**: true.

The footgun is broader than "an absent column": with `recalc_npi_ndc <- FALSE` and a freshly-downloaded `.cs3`, **every** policy silently reads zero, the default `npi` included, because the dummy's **data** is all-zero — not because a column is missing. The doc's current scoping actively steers an npi/ndc user away from the risk ("my column exists, so I'm fine"). Fix as written; two nits:

1. **The fix's `awk` probe is provenance-fragile.** `NR>5` assumes the 4-line comment block; on a comment-less *regenerated* file it silently skips 4 real data rows, and `$3||$4||$5` ignores columns 6+ (`affexp`/`ndcdelay`). Suggested robust replacement (verified: returns `0` on the download, `8260` on the regenerated leftover):
   ```bash
   awk -F',' '/^\*/{next} !h{h=1;next} {for(i=3;i<=NF;i++) if($i+0) n++} END{print n+0" nonzero policy entries"}' \
     modules/32_forestry/input/npi_ndc_aff_pol.cs3
   ```
2. **Inherited, not re-verified this session**: "GAMS zero-fills an absent table column with no error and no warning" and "GAMS only errors on the converse (unknown label → domain violation)". These are pre-existing doc claims that the fix preserves; I did not run GAMS. The *structural* precondition is confirmed (`f32_aff_pol` is declared over the full 5-label `pol32` set at `input.gms:71` + `sets.gms:19-20`, while the `.cs3` supplies 3 columns). Flagging provenance, not contesting.

### M32N-B4 — CORRECTED (Minor)
**Class**: producer_declaration. **citation_ok**: true.

Substance **upheld**: `all(aff_pol == 0) && c32_aff_policy != "none"` (`:385`) is the trigger that fires on a normal fresh-download run for the default `npi`; the missing-column tests are secondary (they only bite when an *already-regenerated*, nonzero file predates the new columns). The doc's line-27/-67 characterization is genuinely incomplete, and the cited line ranges are correct.

**Correction to the auditor's prose**: the `if` at `:385-388` is a disjunction of **FIVE** disjuncts, not four — `4` `||` operators, so `all(aff_pol==0)&&…` + `all(ad_pol==0)&&…` + `all(aolc_pol==0)&&…` + `affexp_missing` + `ndcdelay_missing`. The miscount lives only in the audit's `reality_in_code`; the **proposed fix text never states a count**, so it is safe to apply verbatim. Do **not** let "four conditions" reach the doc.

---

## Residual risks / what would change these verdicts

- The `.cs3` evidence necessarily comes from the working tree. If that copy had been a regeneration masquerading as a download, B1-B4 would collapse. Three independent signals say it is not: the madrat `* origin: calcOutput` block (only `download_distribute` writes it; `write.magpie` at `:351` passes no `comment=`), the dataset match to `cfg$input` via `input/info.txt`, and the all-zero data (a regeneration for the default `npi` produces 3930 nonzero npi cells, as the sibling proves).
- Not checked: whether `mrmagpie::calcNpiNdcAffPol` *always* emits a dummy, or only for this revision. The doc fixes only claim what **this** shipped dataset (`rev4.131`) contains, so nothing rests on it. If a future input revision ships real numbers, B3's case 1 weakens but does not invert.
