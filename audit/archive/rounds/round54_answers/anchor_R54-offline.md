# Anchor Answer — R54-offline

**Question**: How do I find out what `magpie4::reportEmissions()` does and what `report.mif` variables it produces?

**Mode**: offline (magpie-agent AI documentation only — no raw GAMS/R source read, no shell commands executed; all counts below are quoted verbatim from doc text, none recomputed)

**Docs consulted this session** (all under `<magpie-agent>/`):
- `AGENT.md`
- `agent/helpers/magpie4_reference.md`
- `agent/helpers/interpreting_outputs.md`
- `core_docs/Tool_Usage_Patterns.md`

---

## 1. Which doc answers this, and why

`agent/helpers/magpie4_reference.md` is the routed helper: its auto-load trigger list explicitly names "which magpie4 function" and gives `reportEmissions` as one of the example concrete `report<X>` function names (magpie4_reference.md:3). AGENT.md's own auto-load table confirms the same routing for "magpie4 functions / report.mif variable provenance" questions (AGENT.md:296).

That helper states its design choice up front: it does **not** curate function-by-function docs. Quoting verbatim: "this helper does NOT curate function-level docs. magpie4 v2.70.0 exports several hundred functions, and `getReport.R` alone calls ~106 unique `report*` functions. Curation would be a treadmill. Instead, we keep a **version-pinned local clone** and the helper teaches you to **grep + read source on demand**." (magpie4_reference.md:12). So the documentation layer's answer to "how do I find out" is a *method*, not a pre-written spec of `reportEmissions()`'s internals — by design.

## 2. The prescribed method

**Three rules before answering any magpie4 question** (magpie4_reference.md:14–18):
1. Check the pin is current: `python3 scripts/sync_magpie4_clone.py --check` — compares `project/version_pins.json`'s stored `lock_file_sha256` against the live `../input/renv.lock` hash and reports `pin canary: OK` or `STALE`.
2. Read from `.cache/sources/magpie4/` (the SHA-pinned clone) — **never** from `~/Documents/Work/Workspace/magpie4/`, which the doc describes as "HEAD; drifts ahead of the renv pin — currently 5 minor versions ahead per 2026-05-24."
3. Cite with the full version-pinned path, e.g. `.cache/sources/magpie4/R/reportEmissions.R:23` plus the pin (`v2.70.0 @ a360d8c9ec`) — this exact example, using `reportEmissions.R`, also appears in `core_docs/Tool_Usage_Patterns.md:726` as the illustrative "Citable" example in the pinned-clone-vs-web-fetch comparison table.

**General "read source on demand" recipe** for any function not already tabulated in the helper (magpie4_reference.md:225–237):
1. Confirm pin (`--check`; exit 0 = aligned).
2. Locate: `ls .cache/sources/magpie4/R/ | grep -i <keyword>`.
3. Read the file, attending to: `@description` (1-line purpose), `@param` (arguments/types), `@return` (unit, magclass dimensions), and the function body — "most are thin wrappers around `setNames(<call to a lower-level function>, <IAMC variable name>)`" (magpie4_reference.md:235).
4. Cite as `magpie4::<funcname>` and `.cache/sources/magpie4/R/<funcname>.R:<line>`.

**Recipe specifically for "what report.mif variable(s) does this function produce"** (magpie4_reference.md:241–251, illustrated there for `Emissions|CO2|Land` but stated as a general pattern):
1. `grep -n "<variable>" .cache/sources/magpie4/R/getReport.R` — the doc notes this "usually" finds nothing, because "variable names are constructed inside the report* function, not in getReport."
2. `grep -ln "<variable text>" .cache/sources/magpie4/R/` to find candidate `report*.R` files.
3. Open the candidate(s) and locate the `setNames(<...>, "<Name> (<unit>)")` (or `paste0(...)`) construction — that literal string is the report.mif variable name.
4. Trace into the underlying extractor it calls (e.g. `magpie4::emisCO2()`) to see what it reads from the gdx.

The doc adds: "The IAMC variable hierarchy uses `|` as the level delimiter and `+`/`++` summation symbols for stackplot grouping. See `getReport`'s roxygen `@details` for the convention." (magpie4_reference.md:251)

Applied to this question, the concrete next actions are:
```
python3 scripts/sync_magpie4_clone.py --check
ls .cache/sources/magpie4/R/ | grep -i emission
Read .cache/sources/magpie4/R/reportEmissions.R
```

## 3. What the documentation layer already records about `reportEmissions` specifically

Without opening source, three facts are already on record in `magpie4_reference.md`:

**(a) One-line description**, from the Theme 6 ("Emissions & Carbon") table:

| Function | What it reports |
|---|---|
| `reportEmissions` | GHG emissions (CO2, CH4, N2O) by source |

(magpie4_reference.md:144). It sits in the same table as `reportEmissionsBeforeTechnicalMitigation`, `reportCarbonstock`, `reportSOM`, `reportFireEmissions`, `reportPriceGHG`, `reportBiochar` (magpie4_reference.md:145–150). The doc's own suggested grep for any Emissions/Carbon function not in that table: `grep -l "Emission\|Carbon\|GHG\|CO2\|CH4\|N2O" R/report*.R` (magpie4_reference.md:152).

**(b) GAMS-side provenance**, from the module cross-reference table, already flagged as previously verified against source in an earlier validation round:

> "reportEmissions / reportFireEmissions / reportBiochar | `modules/module_51.md` (N emissions), `module_52.md` (carbon stocks → CO2), `module_53.md` (CH4), `module_55.md` (animal-waste N), `module_56.md` (GHG policy), `module_57.md` (MACC mitigation), `module_58.md` (peatland CO2/CH4), `module_59.md` (SOM C) — verified 2026-05-24 R5 against `.cache/sources/magpie4/R/reportEmissions.R`" (magpie4_reference.md:272)

That row is itself a doc-recorded claim from a prior round (dated 2026-05-24, round R5) that someone did open `reportEmissions.R` and checked the module mapping — I have not re-verified it this session, and per this task's offline-mode constraint I am relaying it as a documented claim, not re-deriving it.

**(c) Dispatch mechanism.** `getReport()` — the function that actually produces `report.mif` — is described as "a flat `tryList(...)` of 117 unconditional calls to 106 unique `report*` functions" (magpie4_reference.md:42, both numbers verbatim from the doc). Two properties of that dispatch, stated explicitly: "`tryList` catches per-function failures; one broken `report*` does not crash the whole report," and "There is NO `control` argument or `if (any(grepl(...)))` dispatch — every call runs unconditionally" (magpie4_reference.md:65–66). `reportEmissions` is named as one of magpie4's `report*` functions in the Theme 6 table above; the doc's own arithmetic ("11 themes × ~4 named entry points" plus "the remaining ~60 functions in `getReport.R`'s tryList," magpie4_reference.md:75) implies the named, thematically-tabulated functions — including `reportEmissions` — are drawn from that same tryList population. I did not see the literal `reportEmissions(gdx, level = level)` call line in the (truncated) code excerpt the doc shows — that excerpt lists `reportPopulation`, `reportWorkingAgePopulation`, `reportIncome`, then "`# ... 114 more calls ...`", then `reportBiochar` (magpie4_reference.md:50–54) — so this is an inference from the doc's own framing, not a directly-quoted line.

**(d) A distinct, lower-level sibling function exists: `emissions()`** (lowercase, no "report" prefix). `magpie4_reference.md`'s Quick Reference lists `emissions()` as one of magpie4's "single-purpose extractor functions" alongside `land()`, `production()` (magpie4_reference.md:10), and `agent/helpers/interpreting_outputs.md` shows it used directly against a gdx: `emissions(gdx, level = "reg")  # GHG emissions` (interpreting_outputs.md:85). Per the general pattern stated in § 2 above ("most [report* functions] are thin wrappers around `setNames(<call to a lower-level function>, <IAMC variable name>)`"), `reportEmissions()` is plausibly a thin IAMC-formatting wrapper around this `emissions()` extractor (or similar lower-level calls) — but this is a pattern-based inference, not something I verified specifically for `reportEmissions()`'s actual body.

## 4. Where `report.mif` and the `getReport()` call fit in the pipeline

From `agent/helpers/interpreting_outputs.md`:
- `report.mif` (and `report.rds`) are produced by `scripts/output/rds_report.R` calling `magpie4::getReport(gdx)` at `scripts/output/rds_report.R:37` (interpreting_outputs.md:62).
- `report.mif` itself: "IAMC-format reporting: ~hundreds of variables in 'Name (unit)' format, regional + global" — read with any text editor, or in R via `magclass::read.report()` (interpreting_outputs.md:23).
- The `"Name (unit)"` string format (space before the parenthesis) is constructed **inside** `magpie4::getReport()` itself, not enforced by `rds_report.R`. What `rds_report.R:40-45` actually does is a presence/coverage check — `expectVariablesPresent(report, getMappingVariables(mapping, "M"))` — confirming all variables required by the AR6/NAVIGATE/SHAPE/AR6_MAgPIE IAMC mappings are present in the report; it is not a string-format check (interpreting_outputs.md:62, restated at interpreting_outputs.md:177).
- That helper explicitly hands function-level questions back to `magpie4_reference.md`: "For function-level magpie4 questions (which `report*` function produces which IAMC variable, what arguments it takes, where the source lives), see `agent/helpers/magpie4_reference.md`." (interpreting_outputs.md:105)

## 5. Why the method is "read the pinned local clone," not a web/GitHub lookup

`core_docs/Tool_Usage_Patterns.md` § "No Answer-Time Web Access" states this is deliberate: the agent answers only from local GAMS code, the docs in this repo, and version-pinned local source clones — never `WebFetch`/`WebSearch` for a MAgPIE answer (Tool_Usage_Patterns.md:706–708). Stated reasons: a fetched page (e.g. a GitHub `main`-branch README) "is very likely not the version pinned in [the] `renv.lock`"; it is "not reproducible" (can change between two runs of the same query); and reaching for the web "is usually a symptom of not having found the local source" (Tool_Usage_Patterns.md:712–714). The sanctioned exception is precisely this mechanism: `scripts/sync_magpie4_clone.py` clones magpie4 at the exact SHA pinned in the run's `renv.lock` into `.cache/sources/magpie4/`, records the pin in `project/version_pins.json`, and the agent reads/cites it offline, by version (Tool_Usage_Patterns.md:716–718). The doc's own comparison table uses `reportEmissions.R` by name as its worked example of a citable, pinned, reproducible reference: `.cache/sources/magpie4/R/reportEmissions.R:23 @ v2.70.0 a360d8c9ec` (Tool_Usage_Patterns.md:726).

## 6. Explicit gap (what the documentation layer does NOT give you)

Per its own stated design choice (§ 1 above), `magpie4_reference.md` does not curate the exact list of report.mif variable-name strings, units, or argument signature that `reportEmissions()` produces — that is precisely the "treadmill" it opted out of (magpie4_reference.md:12; also Common Pitfalls #5, magpie4_reference.md:261, verbatim: "Plan said 108 unique report* functions — actual count is 106. Minor discrepancy; don't cite the plan's number when answering, count from `getReport.R` if precision matters" — flagged here only to show the doc's own discipline about not overstating precision on function counts). Getting the literal variable-name strings requires actually reading `.cache/sources/magpie4/R/reportEmissions.R` per the § 2/§ 3(a) recipe. I did not read that file for this answer — the task scope for this round restricts me to the magpie-agent AI documentation files, not source code (GAMS or R) — so I cannot report the exact `report.mif` variable strings, their units, or `reportEmissions()`'s parameter signature beyond the one-line description already quoted in § 3(a).

## Bottom line — recommended steps

1. Read `agent/helpers/magpie4_reference.md` in full (this is the routed helper for this exact question).
2. Run `python3 scripts/sync_magpie4_clone.py --check` to confirm `.cache/sources/magpie4/` matches the renv-pinned magpie4 version.
3. `Read .cache/sources/magpie4/R/reportEmissions.R` — its `@description`/`@param`/`@return` roxygen block and its `setNames(...)` call(s) give the exact report.mif variable name string(s), units, and magclass dimensions.
4. Cross-reference `modules/module_51.md`, `module_52.md`, `module_53.md`, `module_55.md`, `module_56.md`, `module_57.md`, `module_58.md`, `module_59.md` for the GAMS-side origin of the underlying numbers (per the § 3(b) cross-reference row).
5. Cite the result as `magpie4::reportEmissions` + `.cache/sources/magpie4/R/reportEmissions.R:<line>` + the pin version, per the helper's citation rule.

---

## Sources

🟡 **Documented** (read this session, magpie-agent AI documentation only; no raw GAMS or R source code read):
- `agent/helpers/magpie4_reference.md` (lines 3, 10, 12, 14–18, 42, 50–54, 65–66, 75, 144–152, 225–237, 241–251, 261, 266–272)
- `agent/helpers/interpreting_outputs.md` (lines 23, 62, 85, 105, 177)
- `core_docs/Tool_Usage_Patterns.md` (lines 704–718, 726)
- `AGENT.md` (line 296, auto-load routing table)
