# R59 — FIX PLAN (Phase 5)

21 fixable doc findings → **9 root interventions**. Grouped by shared root cause, not one patch
per finding ([[feedback_synthetic_interventions]]).

## BINDING PRE-CONDITIONS (do not skip — [[magpie_agent_lens_bridge_diagnostic]], R44/R48)

The doc-error rule auto-mandates an edit keyed on the **auditor's classification**. Auditors
mis-tag, and an auditor's proposed *fix* can itself introduce a new error. So for EVERY item:

1. **Open the doc and verify the classification's PREMISE** — is the doc actually wrong, or did the
   ANSWERER garble a correct doc? (R44: two `doc_error` tags were wrong; blindly trusting them would
   have edited two correct docs.)
2. **Verify the proposed FIX against code** with `rg`, both `NAME(` and `NAME.` forms. (R48: doc was
   genuinely wrong but the recommended fix would have introduced a new error.)
3. If the classification was wrong, **do not edit** — report it. Count these as
   `auditor_root_cause_corrections` in the round record.

## HARD EXCLUSIONS (PLAN §0.6 — held for Mike)

Do **NOT** touch, and do **NOT** write a truth number into:
- `modules/module_56.md:1138` and `:1150`
- `modules/module_17.md:899`
- `core_docs/Module_Dependencies.md` dependent counts

Verified: **none of the 21 findings targets these**, so no intervention below is in tension with the
hold. If a fixer finds itself editing one of those, it must stop.

Also: **do NOT edit AGENT.md's hub list** (§0.4). Not a fix target this round.

## AGENT REQUIREMENTS

- Model **Sonnet**; `isolation: "worktree"` **MANDATORY** (§0.5 — R58 lost work when three fixers
  shared one tree and two ran `git stash`).
- Each agent owns a disjoint file set. No agent runs `git stash`/`checkout`/`reset`.
- After edits: `bash scripts/validate_consistency.sh` must stay at **0 errors**.

---

## THE 9 INTERVENTIONS

### I1 — `module_35.md` §8 is unsourced against `presolve.gms` (ROOT: 5 findings)
Covers **B1-B1 (Major), B1-L1 (Major), B1-L2 (Minor), B1-L4 (Minor)**, and informs B1-L3.
Root: §8 compresses `35_natveg/pot_forest_may24/presolve.gms:140-234` into three unsourced bullets,
so a docs-only reader **cannot** recover the per-pool Module 22 restrictions. This will reproduce in
every future natveg answer until §8 is sourced.
Fix: source §8 properly — `vm_land.lo(j,"primforest")` floor at `:162`,
`vm_land.lo(j,"secdforest") = protect + restore` at `:201`, `vm_land.lo(j,"other") = ...` at `:231`
(the ONLY per-pool M22 restriction on `other`). Correct `:89` (currently cites `presolve.gms:143-145`,
a pure comment block) and source `:90`'s harvest→secdforest claim.
**Highest-value item in the round** — it is the reason B1 scored 6/10.

### I2 — `module_52.md` never got R58's `stockType` correction (ROOT: B5-L1, **Critical**)
R58 applied the correction to `module_29.md` and `cross_module/carbon_balance_conservation.md` but
**missed `module_52.md`**. Line 422 enumerates `stockType` as `("actual")` only; `904-906` invents
non-existent members "planned, potential". So `actualNoAcEst` — the slice Module 56 prices **by
default** (`price_aug22/input.gms:90`) — is invisible in the carbon module's own doc.
This is the **G2 anchor regression pattern verbatim**. Fix `:422` and `:904-906`, cross-link to
`module_29.md:265-272`.

### I3 — `module_70_notes.md` false consumer claim (ROOT: A4-L1, **Critical**)
Notes assert "M70 reads it" of `vm_costs_additional_mon`. False — the token appears **zero** times
under `modules/70_livestock/`; the variable is M71's
(`71_disagg_lvst/foragebased_jul23/declarations.gms:11`), and this contradicts `module_70.md:822`.
R20 consumer-set anchor class. The irony: the entry exists specifically to prevent M70/M71
misattribution. Fix the notes entry; keep the (correct) M71 attribution.

### I4 — `module_51.md:472` "no feedback loops" is false (ROOT: B3-B1 Major + B3-L2 Major)
Two findings, one line, one fix. Emissions **do** reach crop/livestock decisions:
`vm_emissions_reg` → `q56_emission_costs` → `vm_emission_costs` → Module 11 objective, with a
non-zero default GHG price (`config/default.cfg:1731`).

### I5 — `module_50.md:455` false "surplus feeds into Module 51" (ROOT: B3-L1, Major)
This line is the **origin of the false premise that propagated into R59's own probe design** — it
misled the round designer, not just the answerer. Truth: all 14 `v50_nr_surplus*` occurrences are
inside Module 50; M51 reads only `vm_nr_eff`, `vm_nr_eff_pasture`, `vm_nr_inorg_fert_reg` and
reconstructs a per-source surplus by NUE rescaling.
⚠️ Fix location is **§12 item 8, line 455** — NOT §5.1. The answerer misdiagnosed §5.1; the auditor
corrected it. Use the auditor's location.

### I6 — `module_50.md:99-107` term count (ROOT: B4-B1, Minor)
"Components" list enumerates 8 terms; `q50_nr_inputs` has **nine** addends — the fallow-land
fixation term at `equations.gms:26` is missing. The doc's own adjacent code block already prints all
nine, so this is an internal inconsistency.

### I7 — `module_70.md` two independent errors (ROOT: A3-B1 Major, A3-L1 Major)
(a) `c70_feed_scen` documented as selecting only the feed-basket trajectory; `preloop.gms:13-23`
uses it to slice **three** tables, and the omitted `f70_livestock_productivity` path propagates via
`p70_cattle_stock_proxy` → `pm_past_mngmnt_factor` into **Module 14 pasture yields**.
(b) Circular-dependency section calls `vm_prod_reg` an "exogenous target"; it is endogenous and
never `.fx`-ed anywhere. G2 `doc_error_answerer_beat_it` pattern.

### I8 — `module_29.md` two small items (ROOT: A2-B1 Major, A1-L1 Minor)
(a) `:193` invents a **"Module 33"** — no such module exists; `q33_marginal` is a 33rd-percentile
suitability label, a member of set `marginal_land29`. Corpus sweep (positive control) found exactly
one instance. **New phantom class with zero gate coverage** (see F-5): gates pass green because the
identifier is backticked and real — only the prose module-number attribution is false.
(b) `:797,802` cite `52_carbon/normal_dec17/start.gms:27`/`:30`; the assignments are at `:28`/`:31`
(those lines are comments). Sits *inside* the file's own R58 CORRECTED block, while
`module_52.md:451` has it right.

### I9 — `cross_module/` two items (ROOT: B4-L1 Minor, B1-L3 Minor)
(a) `nitrogen_food_balance.md:104` calls `vm_nr_inorg_fert_reg` "free"; it is declared under
`positive variables` (`50_nr_soil_budget/macceff_aug22/declarations.gms:9-10`).
⚠️ **Inoculate, do not just patch** — the error echoes MAgPIE's OWN source comment at
`equations.gms:20` ("are a free variable"), so any doc written from the `*'` comments regenerates
it (F-6). Add a short note recording the source-prose ambiguity.
(b) `land_balance_conservation.md:207` on primforest→secdforest / other→secdforest being "handled
internally by Module 35".

---

## DEFERRED (not fixed this round, with reason)

- **G1-B1 / G1-B2 (Informational, 0 weight)**: the auditor found **neither** `module_14.md` citation
  convention is wrong — header ranges are bare statements, footer ranges include each equation's
  `*'` doc comment. The real (minor) defect is that the two footers extend in opposite directions
  unlabeled. Not a correctness bug; noted, not patched.
- **F-7** (`c56_carbon_stock_pricing` unreachable from config): **parent-repo** bug.
  `magpiemodel` is push-forbidden. For Mike / the PIK briefing.
- **F-3** (role-map `.scale` false positive): script fix, out of §9 scope.
- **F-1** (ledger backfill R53–R58): out of scope.
