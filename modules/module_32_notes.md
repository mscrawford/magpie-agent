# Module 32 (Forestry) — Notes

**Created 2026-07-14** during the `/sync` to MAgPIE develop `0d7ebeb90`.

---

## ⚠️ Warnings & Common Mistakes

### `npi_ndc_aff_pol.cs3` is REGENERATED at run start — it is not a fixed download

This is the single most misleading thing about `c32_aff_policy`, and it is easy to get exactly backwards. Read this before reasoning about any afforestation-policy input.

**The GAMS side has no code branch at all.** The entire policy selection is one table lookup:

```gams
p32_aff_pol(t,j) = round(f32_aff_pol(t,j,"%c32_aff_policy%"),6);
```
(`modules/32_forestry/dynamic_may24/preloop.gms:182`)

`c32_aff_policy` appears in GAMS *only* at `input.gms:9` (`$setglobal`) and that line. There are **zero** `$if` / `$ifthen` branches on the policy name anywhere. So a policy's whole substance is a **column** of `npi_ndc_aff_pol.cs3` (`input.gms:73`).

**That `.cs3` is BOTH: an input you download AND a run-time artifact.** The download ships an **all-zero dummy** — its own header says `description: Dummy file for NPI/INDC policies`, it is listed in the download manifest `modules/32_forestry/input/files`, and `gms::download_distribute` (`scripts/start_functions.R:192`) places it. The **real** numbers — for *every* policy, `npi` included — are written at run start by the R layer, which overwrites the very file GAMS `$include`s. It is gitignored (`.gitignore:7`, `*.cs*`).

| Step | Where |
|---|---|
| Default config enables the check | `config/default.cfg:123` — `cfg$recalc_npi_ndc <- "ifneeded"` (**this is the default**) |
| All-zero-input guard (**primary**) | `scripts/start_functions.R:385` — `all(aff_pol == 0) && c32_aff_policy != "none"`; the shipped `.cs3` is an all-zero dummy, so this fires for **every** non-`none` policy, `npi` included |
| Missing-column guard (**secondary** — catches an already-regenerated file that predates the new columns) | `scripts/start_functions.R:380-383` — `affexp_missing`, `ndcdelay_missing` test whether the selected policy has a column in the current file |
| Guard forces regeneration | `scripts/start_functions.R:385-391` — sets `cfg$recalc_npi_ndc <- TRUE` |
| Regenerator overwrites the file GAMS includes | `scripts/npi_ndc/start_npi_ndc.R:22` — `outfolder_aff` includes `../../modules/32_forestry/input/` |

Where each policy's substance actually lives:
- **`affexp`** — rows in `scripts/npi_ndc/policies/policy_definitions.csv` (delivered by the input download).
- **`ndcdelay`** — needs no input rows at all; it is **derived in R** from the existing `ndc` rows by shifting target years ≥2030 by a country-specific PRISMA delay (`start_npi_ndc.R`).

**So a 3-column header proves nothing.** `head` the on-disk `.cs3` and you will see `dummy,dummy,none,npi,ndc` — that is exactly what the **input download ships**: an all-zero dummy with 3 policy columns. It is not stale, and it is not evidence that `affexp` / `ndcdelay` are unusable. Under the default config the file is regenerated — with real numbers and the needed column — before GAMS ever reads it. Both policies are wired into named scenario presets (`config/scenario_config.csv:51`). (Tell the two files apart by the header: a `* origin: calcOutput(...)` comment block = the pristine download; **no** comment block = a previous regeneration.)

**The one real footgun (narrow, non-default):** the whole guard lives inside `if(cfg$recalc_npi_ndc=="ifneeded")` (`scripts/start_functions.R:375`). If you override **`cfg$recalc_npi_ndc <- FALSE`**, no regeneration happens and whatever `.cs3` is on disk is `$include`d as-is. Two ways that bites:
1. **Freshly-downloaded `.cs3`** (the all-zero dummy) → **every** policy reads as zero, *including the default `npi`* (`config/default.cfg:1026`) and `ndc`. The run is silently identical to `none`, and it is invisible: all the columns are present. This is the bigger trap.
2. **Stale regenerated `.cs3`** predating the PRISMA/ELEVATE columns → `affexp`/`ndcdelay` are absent from the header, and GAMS zero-fills an absent table column with no error and no warning (the label is declared in `pol32`, `dynamic_may24/sets.gms:19-20`), so `f32_aff_pol(t,j,"ndcdelay") = 0` and `p32_aff_pol = 0` everywhere. GAMS only errors on the converse (an *unknown* column label → domain violation).

If you have disabled recalculation, check the header AND the data:
```bash
head -5 modules/32_forestry/input/npi_ndc_aff_pol.cs3   # '* origin: calcOutput' => still the dummy
awk -F',' 'NR>5 && ($3+0||$4+0||$5+0){n++} END{print n+0" nonzero policy entries"}' \
  modules/32_forestry/input/npi_ndc_aff_pol.cs3          # 0 => all-zero dummy: EVERY policy is silently none
```

### Don't confuse `ndcdelay` with `s32_npi_ndc_reversal` — both say "roll-back"

`ndcdelay` is the PRISMA **"Asymmetric Roll-back"** scenario, and there is a *separate*, unrelated switch whose name also reads like roll-back. They do different things and they stack:

| | `c32_aff_policy = ndcdelay` | `s32_npi_ndc_reversal` |
|---|---|---|
| What | Shifts NDC afforestation **milestone target-years** (≥2030) later, by country cluster (+10 / +20 / +30 y) | The **year in which NPI/NDC afforestation is reversed** — established forest is released back to free bounds |
| Type | A `pol32` policy name, selected via `c32_aff_policy` | A scalar, `dynamic_may24/input.gms:48`, default **`Inf`** (i.e. never) |
| Effect | Delays the ramp-up | Undoes it |

`ndcdelay` **delays** afforestation; it does not reverse anything once land is established. If you want the PRISMA scenario, leave `s32_npi_ndc_reversal` at its `Inf` default — otherwise you are stacking a reversal on top of a delay and the run will not mean what you think.

### 🚩 How this note got written — a cautionary tale worth keeping

The first version of this file asserted the opposite: that `ndcdelay` was **broken** — "selectable but unfed", silently producing a zero policy — and recommended reporting it to the PRISMA authors. Every *premise* was true and verified (no GAMS branch; the on-disk `.cs3` really does have only 3 policy columns; `affexp`/`ndcdelay` really do appear 0 times in its 6405 lines; neither feature commit bumped `cfg$input`). The **conclusion was false**, because the reasoning never left the GAMS layer: it inferred the provenance of a *gitignored, regenerated* artifact from git history alone.

The guards that refute it (`affexp_missing`, `ndcdelay_missing`) were added **by the very commits being accused** — `a54cd02c6` and `58bde5788` each modified `scripts/start_functions.R`. The author had already handled the exact failure mode.

**The transferable lesson:** a file under `modules/*/input/` is **not** necessarily an input you were given. It may be produced by `scripts/` at run start. **Before claiming an input is missing or stale, grep `scripts/` for the switch name and for the file name — not just `modules/` and `git log`.** One `grep -rn "c32_aff_policy" .` would have surfaced `scripts/start_functions.R:380` immediately.

---

## 💡 Lessons Learned

- 2026-07-14: `c32_aff_policy` is a pure data lookup with no GAMS code branch (`preloop.gms:182`) — but the file it looks into (`npi_ndc_aff_pol.cs3`) is **regenerated by the R start layer** whenever the on-disk file is all-zero (the shipped dummy — the usual case, including the default `npi`) **or** the selected policy's column is missing (`scripts/start_functions.R:380-391`, default `cfg$recalc_npi_ndc <- "ifneeded"`). Do not reason about MAgPIE input files from `modules/*/input/` contents plus git history alone: `*.cs*` is gitignored and several inputs are run-time products. (Source: session experience — an agent-generated "silent zero" bug report that was refuted by an adversarial audit.)
- 2026-07-14: GAMS zero-fills a `table` column that is declared in the set but absent from the `$ondelim` `.cs3` header — no error, no warning. That IS a genuine silent-failure mode; it is simply not reachable here under the default config, only if you set `cfg$recalc_npi_ndc <- FALSE`. (Source: session experience.)

---

## See also

- `module_32.md` — primary documentation (§9.2 Afforestation Policy)
- `module_56_notes.md` — C-price-induced afforestation is a *different*, reward-driven channel (`vm_reward_cdr_aff`), independent of `c32_aff_policy`
- `agent/helpers/debugging_infeasibility.md` — for runs that fail loudly; a zero-filled policy column fails **quietly**
