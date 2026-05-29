# Round 27 synthesis (coverage) — 2026-05-29

**Context**: Interactive recovery run (continuation of R26) after the scheduled 00:00 overnight run failed to fire (see `project_overnight_run_scheduling`). User directed 2 rounds total (R26+R27); R28 skipped; 05:30 time guard overridden by explicit instruction. Answerer Sonnet 4.6 (magpie-helper, docs-only); auditor Opus 4.8 (general-purpose, vs origin/develop). Commits local only; nothing pushed.

**Type**: fresh coverage of 5 never-deeply-probed modules + regression anchors G1/G2.

## Results

| Q | Module(s) | Archetype | Score | Crit | Maj | Min | Source | Doc fix |
|---|---|---|---|---|---|---|---|---|
| R27-Q1 | 18 / 17 / 16 / 50 | default+causal | 7 | 0 | 1 | 1 | mixed | 1 (gj→ge) |
| R27-Q2 | 53 / 70 / 30 / 56 | quantitative | 7 | 0 | 1 | 1 | doc_error | 2 (GWP, vm_area) |
| R27-Q3 | 31 / 70 / 14 / 10 / 22 | causal+conservation | 8 | 0 | 0 | 2 | answerer slip | no |
| R27-Q4 | 40 / 11 / 17 | cost provenance | 5 | 0 | 1 | 3 | mixed | 1 (M11 formula+chain) |
| R27-Q5 | 20 / 17 / 16 / 21 / 15 | causal+conservation | 4 | 0 | 2 | 2 | answerer confab | no (doc correct) |
| R27-G1 | 14 | regression anchor | 10 | 0 | 0 | 0 | clean | n/a |
| R27-G2 | 52 / 56 / 29 / 31 / 32 / 34 / 35 / 59 | regression anchor | 9 | 0 | 0 | 1 | n/a | no (recovered) |

**Mean 7.1** (range 4-10). Bugs: 15 (0 Critical, 5 Major, 10 Minor); doc_error 5, answerer_confabulation 10. **Fixed: 5** (all doc_error). 0 bombs.

**Reading the mean**: the 7.1 is dragged by Q4 (M40, real doc error - fixed) and Q5 (M20, 4/10). Q5 is an **answerer-confabulation artifact against a verified-correct doc**, NOT a doc-quality failure - excluding it, doc quality is solid.

## Fixes applied (verified vs origin/develop; validators re-run clean)

1. **M18 attribute set** (Q1-B2 Minor): `module_18.md:105` listed `gj` (a unit) among attribute-set members; the member is `ge` (gross energy). Corrected vs `core/sets.gms` attributes set.
2. **M53 CH4 GWP** (Q2-B1 Major): `module_53.md` claimed CH4 GWP=25 (AR4) used in M56. Actual M56 uses **GWP=28 (AR5)** per `modules/56_ghg_policy/price_aug22/preloop.gms:78,80` (`12/44*28`). Corrected at `:443`, `:859-863`, `:867`; resolves the contradiction with `module_56.md` (already 28).
3. **M53 vm_area attribution** (Q2-B2 Minor): "Module 30 (Croparea) or Module 17 (Production)" -> "Module 30" at `:277/:409/:410/:413`. `vm_area` is declared only in `30_croparea` (`detail_apr24:21`, `simple_apr24:18`), never M17.
4. **M40 M11 cost aggregation** (Q4-B1 Major + B2 Minor): `module_40.md:171-174` carried a self-labelled "inferred" (and wrong) formula `sum(j2, vm_cost_transp(j2,k))`. Replaced with the verified `+ sum((cell(i2,j2),k), vm_cost_transp(j2,k))` (`modules/11_costs/default/equations.gms:21`, collapses both the cell->region map and `k`) + added the objective chain `q11_cost_reg -> v11_cost_reg -> q11_cost_glo -> vm_cost_glo`.

Two follow-up self-corrections after the first validator re-run: made the new M40 cross-module cites full `modules/...` paths (citation check), and reworded "verified against" -> "per" on line 171 (it collided with the realization-validity check's "Verified Against" footer parser, misreading `default` as a module-40 realization).

## NOT fixed (answerer confabulation against correct docs - no doc change)
- **Q5 (M20)** all 4 bugs: answerer put `vm_dem_food` on M16 (it is M15's) and `v20_dem_processing` on the wrong set; `module_20.md` is correct. Optional future hardening (add explicit declaration row) noted, not done.
- **Q1 (M18) Major**: answerer cited the M50 link at the wrong equation/line; `module_18.md` is correct.
- **Q3 (M31)** 2 Minor + **Q4 (M40)** B3/B4: answerer citation imprecisions / embellishments.

## Anchors
- G1 (M14): 10, stable (R22/23/25/26/27). No drift.
- G2 (M52/56): **9, RECOVERED from R26's 7**. The R26 populator-list doc fix held - R27's answerer read the corrected docs and enumerated 29/31/32/34/35/59 correctly. 1 Minor (answer-prose mislabel; cite correct). No doc fix.

## Validators (post-fix, vs baseline)
All unchanged from baseline: `validate_consistency.sh` 39/41 (2 advisories), `check_consumer_attribution.py` 9, `check_units.py` 5 advisory.

## Bookkeeping notes
- `probe_dedup_check.py` Step-5c was a no-op: the documented BARE command takes the design-time recognition SCAN path and reads empty stdin, so it never appends (NOT an off-by-one; `auto_detect_next_round()`'s latest+1 is correct for the scan). _Corrected in follow-up implementation_: Step-5c now uses `--append-latest`, plus a TTY foot-gun guard and a `--self-test`; the ledger was repopulated via `--append-latest` (which also added `module_70`, missed by the initial manual add). The R27 probe modules 18/53/31/40/20 were initially added by hand (eligible_after=30).
- Aggregate-count markers (`<!--count:-->` in AGENT.md + 3 files) NOT refreshed: refreshing requires deploying AGENT.md into the experiment-branch parent repo. Deferred to avoid disturbing the user's parent tree. Current cumulative: 27 rounds, 508 found, 332 fixed.
