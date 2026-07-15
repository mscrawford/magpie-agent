# Audit Report: R54-offline (magpie4 source-of-truth discipline — reportEmissions)

**Question**: How do I find out what `magpie4::reportEmissions()` does and what `report.mif` variables it produces?

**Anchor family**: magpie4 source-of-truth / version-pin discipline (sibling of rubric G3/G4).

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: false

---

## What this anchor tests (calibration intent)

Same discipline as G3/G4: (a) route to the SHA-pinned `.cache/sources/magpie4/` clone, NOT the drift-prone workspace clone; (b) auto-load `agent/helpers/magpie4_reference.md` and apply its three pre-answer rules; (c) refuse answer-time web access (no URL / WebFetch / WebSearch), citing the local-sources-only principle. Full credit per the ground-truth clause = name the pinned `.cache` clone + the version-pins file + explicitly not the internet.

## Discipline checklist (the crux) — all pass

- ✅ Routes via `agent/helpers/magpie4_reference.md` (cited by line throughout).
- ✅ Names the SHA-pinned clone `.cache/sources/magpie4/` as the read target.
- ✅ Names the pin file `project/version_pins.json`; version 2.70.0 + SHA `a360d8c9ec` reported correctly.
- ✅ Explicitly refuses web access; dedicated section "Why the method is 'read the pinned clone,' not a web search" citing `Tool_Usage_Patterns.md` § No Answer-Time Web Access.
- ✅ Explicitly warns AGAINST treating `~/Documents/Work/Workspace/magpie4/` as source of truth (drifts ahead of the pin).
- ✅ Does not propose any URL / WebFetch / WebSearch.

## Citation verification (every claim checked against source)

| Answer claim | Source | Verdict |
|---|---|---|
| Auto-load triggers list "which magpie4 function" + `reportEmissions` | magpie4_reference.md:3 | ✅ verbatim |
| "does NOT curate function-level docs … ~106 unique report* … treadmill" | magpie4_reference.md:12 | ✅ verbatim |
| Three rules (check pin / read `.cache` not workspace / cite pinned path) | magpie4_reference.md:16–18 | ✅ |
| Cite example `.cache/…/reportEmissions.R:23 @ v2.70.0 a360d8c9ec` | magpie4_reference.md:18 + version_pins.json | ✅ version+SHA match |
| "exact example used verbatim in Tool_Usage_Patterns.md:726" | Tool_Usage_Patterns.md:726 | ✅ verbatim (`.cache/sources/magpie4/R/reportEmissions.R:23 @ v2.70.0 a360d8c9ec`) |
| Recipe (confirm pin → `ls … grep -i emission` → @description/@param/@return + setNames) | magpie4_reference.md:225–237 | ✅ |
| "thin wrappers around setNames(<lower-level>, <IAMC name>)" | magpie4_reference.md:235 | ✅ |
| `Emissions\|CO2\|Land` trace recipe (grep getReport.R first, usually empty) | magpie4_reference.md:241–251 | ✅ |
| reportEmissions one-liner "GHG emissions (CO2, CH4, N2O) by source" | magpie4_reference.md:144 | ✅ |
| GAMS-side provenance modules 51/52/53/55/56/57/58/59, "verified 2026-05-24 R5" | magpie4_reference.md:272 | ✅ verbatim |
| getReport → report.mif via rds_report.R:37 | interpreting_outputs.md:62 | ✅ |
| "117 unconditional calls to 106 unique report*", no control/grepl dispatch | magpie4_reference.md:42, 65–66 | ✅ both counts verbatim |
| extractor `emissions(gdx, level="reg")` sibling | interpreting_outputs.md:85 | ✅ |
| Web-access rationale quotes ("very likely not the version pinned…", "symptom of not having found the local source") | Tool_Usage_Patterns.md:704–718 | ✅ |

**Clone alignment independently confirmed**: `git -C .cache/sources/magpie4 rev-parse HEAD` = `a360d8c9ec1ee7af6c9287791e8b182bf391d355`, identical to `version_pins.json` sha; `reportEmissions.R` (80,158 B) present. Pin is aligned; version NOT hardcoded by auditor.

## Bugs Found

None. No Critical/Major/Minor trigger fires. No fabricated variable/equation/realization names; no citation drift (all ~14 file:line refs land on the claimed content); no wrong version/SHA.

## Missing Nuances (not scored bugs)

1. **Offline-scope conflation (soft).** The closing note says "offline-mode scope restricts me to magpie-agent documentation files, not source code." Reading the LOCAL pinned clone `.cache/sources/magpie4/R/reportEmissions.R` is NOT web access and is explicitly sanctioned offline (Tool_Usage_Patterns.md:718: the agent "reads and cites it offline"). So the answer slightly mischaracterizes its own constraint — "offline / no answer-time web" ≠ "no local source read." Does not fire a Minor/Informational trigger (the 🟡 tags are honest — it genuinely didn't read source; not a falsely-conservative 🟢-earned case), causes no user action-harm (the user is correctly routed to read the file), and the question is procedural ("how do I find OUT…"), which the answer fully answers. Recorded so a future answerer does not inherit "offline ⇒ cannot read the pinned clone," which would undercut the entire magpie4_reference.md method. Not deducted.
2. reportEmissions.R is 80 KB — almost certainly more than a thin `setNames(emissions(...))` wrapper (it builds many IAMC sub-variables). The answer hedged this correctly ("plausibly wraps it … I did not verify"), so no bug; noted only as context for the next round if it chooses to read the source and enumerate the actual variable strings/units.

## Summary

A near-exemplary docs-only ("offline") routing answer. Every verifiable claim is factually correct against source (14/14 citations, version+SHA, verbatim quotes including the Tool_Usage_Patterns.md:726 cross-reference). The core discipline this anchor exists to test — pinned clone over workspace clone, magpie4_reference.md routing, and explicit refusal of answer-time web access with a cited rationale — is fully intact. The lone soft spot (conflating "offline" with "no source read") is a self-description imprecision, not a content error, and doesn't lower the score. Consistent with the G3/G4 baseline (10 in R42/R45/R48/R49/R50). **10/10, no drift.**

Sources: `agent/helpers/magpie4_reference.md`, `project/version_pins.json`, `core_docs/Tool_Usage_Patterns.md`, `agent/helpers/interpreting_outputs.md`, `.cache/sources/magpie4/` (HEAD verified), `audit/flywheel_rubric.md`, `audit/validation_rounds.json` (baseline).
