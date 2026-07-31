# Flywheel detection rate on seeded bugs — the missing half of the benchmark

**Run** 2026-07-31 · same reverse-apply harness as `audit/seeded_bug_benchmark_2026-07-20.md`
(`audit/tools/seed_known_bugs.py`), with the **detector swapped** from the deterministic
gate to a blind LLM audit.

## Why this exists

`audit/seeded_bug_benchmark_2026-07-20.md` measured what the **gate** catches. But the
gate is the *minority* detector — that benchmark's own closing note says every bug in the
sample "was eventually found by expensive, FNR-limited LLM audits, not by the gate." So
the project had a number for the cheap instrument and none for the expensive one it
actually relies on. This run supplies it.

---

## Headline

| Detector | Result |
|---|---|
| Gate, on the 7 bugs it is structurally blind to | **0 / 7** |
| **Flywheel (blind LLM audit), same 7 bugs** | **6 / 7** |
| Flywheel, positive control (a bug the gate *does* catch) | **1 / 1** |
| **Total** | **7 / 8** |

**The two instruments are complementary, not redundant.** The gate misses these bugs by
construction — they are in classes no var-anchored checker can bind. The flywheel finds
almost all of them.

Also measured, as a by-product: **the gate's own rate has moved 32.7% → 42.9%** (16/49 →
21/49 raw) since 2026-07-20, from Check 41, the owner-less-vars fix, the `/`-separator
fix and Check 42. Quote it against the *raw* 32.7%, not the adjusted 30.4% — comparing
42.9% to 30.4% overstates the gain by mixing bases.

## Pre-registered design

n = 8, fixed **before** running: all 7 hunks from the four classes where the gate scores
0 (`data_source`, `attribution_role`, `citation`, `mechanism`), plus 1 gate-caught hunk
as a positive control on the harness. Stratified toward the gate's blind spots on
purpose — this is **not** a random sample and 6/7 is **not** "the flywheel's detection
rate". It answers the narrower, more decision-relevant question: *does the flywheel cover
what the gate cannot?*

Each auditor received the seeded document with **no indication that anything had been
injected**, and was asked to audit claims against GAMS source — as a real flywheel probe
would.

## Per-item result

| # | Class | Doc | Injected defect | Verdict |
|---|---|---|---|---|
| 0 | mechanism | `module_29_notes.md` | "the `simple_apr24` realization includes fallow land dynamics" (it is `detail_apr24`) | **CAUGHT** — flagged Critical, realization inverted, and noted `detail_apr24` is the *default*, so the error misdirects a default-config user |
| 1 | data_source | `module_10.md` | "**Source**: Land-Use Harmonization 2 (LUH2)" (it is LUH3) | **CAUGHT** — Critical, cited `calcLanduseInitialisationBase.R:75` and `CHANGELOG.md:92` |
| 2 | data_source | `module_10_notes.md` | *removal* of the LUH2/LUH3 provenance section | **CAUGHT** — identified the missing section explicitly, both as "the seed is a stale revision" and as a High "important and missing" finding |
| 3 | attribution_role | `module_40.md` | `vm_prod` producer/consumer roles inverted | **CAUGHT** — Critical; correctly named M30/M31/M71/M73 as the real per-slice populators |
| 4 | attribution_role | `module_58.md` | forestry vars attributed to 10_land; "Dependencies: 5 total" | **CAUGHT** — High; caught both the misattribution and the count |
| 5 | citation | `module_80.md` | bare `solve.gms:16, 174` missing its `lp_nlp_apr17/` realization prefix | **MISSED** — found ~15 *other* real citation defects, but not this one |
| 6 | citation | `module_80.md` | same class: bare `solve.gms:66,77,…` missing the prefix | **CAUGHT, but downgraded** — "the section writes bare `solve.gms` with no realization prefix … Cosmetic" |
| 7 | attribution_read | `module_10.md` | "17 total connections (2 inputs, 15 outputs)" | **CAUGHT** (positive control) — computed the true 2 in / 18 out itself |

## What this does NOT license

- **Not a rate.** n=8, deliberately stratified toward the gate's blind spots. A random
  sample would score differently, almost certainly lower.
- **The same confound R59 flagged, reproduced here by me.** Each auditor was told which
  *class* to attend to ("pay particular attention to ATTRIBUTION claims", "…to
  CITATIONS"). An auditor told where to look finds more than one that is not. Some
  unknown share of 6/7 is method, not capability. **A lead for a matched round, not a
  measured rate.**
- **The weakest class is bare citations**, and it is weak in an interesting way: items 5
  and 6 are the *same* defect (a `solve.gms:NN` citation missing its realization prefix,
  with correct line numbers). One auditor missed it entirely; the other saw it and called
  it cosmetic. So on this class the flywheel is ~50% at best, and even its hit was
  graded away. This is precisely the class MANDATE 16 exists for and that the *gate*
  should own — an LLM will not reliably care about a missing path prefix.
- **Cost asymmetry is enormous and belongs beside the rate.** Each audit ran ~100k–155k
  tokens. The whole gate runs in seconds for effectively nothing. Per bug found, the
  flywheel is orders of magnitude more expensive. "The flywheel catches more" is not an
  argument for running it more often; it is an argument for mechanizing whatever it keeps
  finding.

## By-product: 40+ real defects in unrelated text

The audits were pointed at seeded docs, but they read whole documents and found a great
deal of genuine, pre-existing breakage — none of it planted:

- `module_40.md`: a worked example off by **1000×** (`100 × 30 × 0.02 = 60,000`; it is
  60), self-certified two lines later as "**Arithmetic checked** ✓"; commodity cost
  factors described as "~0.001-0.01" for oilseeds when the readable input file says
  0.046, and no mention that livestock products are 40-70× any crop; `j`/`j2` described
  as ~59,000 cells pre-clustering when `j` *is* the 200-member clustered set.
- `module_80.md`: three `config/default.cfg` citations ~21 lines stale, all landing in
  the module-73 block; `option limcol = 0` glossed as "no limit" when it *suppresses* the
  listing; `s80_add_cplex`/`s80_add_conopt3` read and assigned but **declared nowhere**.
- `module_58.md`: `pm_climate_class` documented as binary when the input file's own
  header says `unit: share` (1116 of 6200 values are fractional) — so the per-cell
  emission factor is an area-weighted blend of up to three climate zones, not one zone's
  EF; peatland area 292 Mha vs an actual 427.6 Mha.
- `module_10.md`: centrality rank "#2 after 09_drivers" when M10 is **#1** (18 consumers
  vs 09's 14), inherited from a stale `detailed_module_analysis.txt`.

**These are unadjudicated auditor output, not confirmed findings.** They are recorded
here as leads, not applied. Several are in colleagues' modules and none has been through
the refutation gate.

## Method note worth keeping

The first attempt at this run reimplemented the harness's hunk-splitting instead of
importing `split_hunks` from it, and silently seeded only 4 of 8 items — the other 4
"would not apply". Importing the real function fixed all 4. Do not reimplement a
harness's internals to reuse it; import them.
