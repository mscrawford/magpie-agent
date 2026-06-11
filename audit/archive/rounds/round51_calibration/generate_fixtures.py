#!/usr/bin/env python3
"""Generate R51 calibration fixtures + ground-truth key from one source.

37 fixtures: 12 Critical + 12 Major (7 historical-replay, 5 invented) planted,
+ 13 clean controls (many true-twins of planted bugs, to measure over-correction).

Each planted fixture carries exactly ONE code-verifiable wrong claim embedded
among verified-true claims; clean fixtures are fully correct. ALL ground truth
verified by hand against /tmp/magpie_develop_ro @ea383032d before authoring.

Neutral IDs (fixture_01..37) are assigned by list position, and the list is
interleaved so planted/clean and bug-classes are not clustered. The key
(ground_truth.json) lives in the repo and is NEVER copied into the auditor's
/tmp working set.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FIX_DIR = os.path.join(HERE, "fixtures")
os.makedirs(FIX_DIR, exist_ok=True)

# fields: tag(internal), planted, source(invented|replay|clean), bug_class,
# severity(Critical|Major|None), question, answer, wrong_claim, code_truth,
# citation, difficulty, [survival]
F = []
def add(**k): F.append(k)

# ---- 01 CLEAN: cropland default (true-twin of croparea wrong-default) ----
add(tag="CL-cropland", planted=False, source="clean", bug_class=None, severity=None,
    question="What is the default realization of the cropland module (29)?",
    answer="The cropland module (29) default realization is `detail_apr24`. \U0001F7E2 This is set in config/default.cfg (`cfg$gms$cropland <- \"detail_apr24\"`); it is the detailed cropland representation used in the standard configuration.\n\nVerified against config/default.cfg.\n",
    wrong_claim=None,
    code_truth="TRUE: cropland(29) default IS detail_apr24 (default.cfg). True-twin of the croparea fixture, where detail_apr24 would be WRONG.",
    citation="config/default.cfg (cfg$gms$cropland <- \"detail_apr24\")", difficulty="trap (true-twin)")

# ---- 02 CRITICAL invented: croparea wrong default ----
add(tag="F1-croparea-default", planted=True, source="invented",
    bug_class="wrong realization as default", severity="Critical",
    question="What is the default realization of the croparea module (30), and what does it track?",
    answer="The croparea module (30) default realization is `detail_apr24`, which disaggregates cropland into individual crop types per cell. \U0001F7E2 It tracks `vm_area(j,kcr,w)` indexed by crop (`kcr`) and water supply (`w`, rainfed/irrigated), and sits downstream of the cropland module (29).\n\nVerified against modules/30_croparea/detail_apr24/declarations.gms.\n",
    wrong_claim="croparea(30) default realization is `detail_apr24`",
    code_truth="croparea default is `simple_apr24` (default.cfg). detail_apr24 is the NON-default sibling. (vm_area(j,kcr,w) is correct in both.)",
    citation="config/default.cfg (cfg$gms$croparea <- \"simple_apr24\")", difficulty="medium")

# ---- 03 MAJOR replay: vm_manure_recycling producer mis-attribution ----
add(tag="RP3-manure", planted=True, source="replay",
    bug_class="producer mis-attribution (DECLARED/POPULATED vs READ)", severity="Major",
    survival="present through R30-R39 all-module-doc push; caught R50",
    question="Which interface variables does module 51 (nitrogen) receive, and from which module?",
    answer="Module 51 (nitrogen emissions) receives several inputs. \U0001F7E2 From Module 50 (NR Soil Budget): `vm_manure_recycling(i,'nr')` -- manure nitrogen recycled to cropland (Mt N), read at `equations.gms:25`. Module 51 uses these flows to compute N2O and NH3 pathways.\n\nBased on module_51.md documentation.\n",
    wrong_claim="vm_manure_recycling comes 'From Module 50'",
    code_truth="vm_manure_recycling is DECLARED in Module 55 (awms, ipcc2006_aug16/declarations.gms:21) and POPULATED there (equations.gms:84, LHS =e=). M50 only READS it (RHS). Source is 55, not 50.",
    citation="modules/55_awms/ipcc2006_aug16/declarations.gms:21 + equations.gms:84", difficulty="hard")

# ---- 04 MAJOR invented: module 35 fire mechanistic ----
add(tag="F4-fire", planted=True, source="invented",
    bug_class="parameterized presented as mechanistic", severity="Major",
    question="How does MAgPIE model forest loss from wildfire in natural vegetation (module 35)?",
    answer="Module 35 (natveg, default `pot_forest_may24`) represents wildfire disturbance dynamically. \U0001F7E2 It computes an annual fire risk as a function of climate drivers (temperature and precipitation) and standing biomass, and releases the corresponding carbon when forest burns. Losses are tracked in `p35_disturbance_loss_secdf`/`p35_disturbance_loss_primf`.\n\nVerified against modules/35_natveg/pot_forest_may24/presolve.gms.\n",
    wrong_claim="module 35 computes fire risk dynamically from climate (temp/precip) and biomass",
    code_truth="M35 applies loss from FIXED INPUT shares f35_forest_lost_share + scenario shock f35_forest_shock, scaled by timestep (presolve.gms:14-32). No climate/biomass fire model; 'wildfire' is a loss LABEL (sets.gms:12). The p35_disturbance_loss_* params DO exist.",
    citation="modules/35_natveg/pot_forest_may24/presolve.gms:14-32; sets.gms:12", difficulty="hard")

# ---- 05 CRITICAL invented: vm_cost_prod_crop owner ----
add(tag="F10-costcrop", planted=True, source="invented",
    bug_class="wrong module attribution for a cost variable", severity="Critical",
    question="Which module computes vm_cost_prod_crop (the crop factor cost), and in which equation?",
    answer="`vm_cost_prod_crop(i,factors)` is the regional factor cost (capital and labor) of crop production. \U0001F7E2 It is computed in Module 11 (costs) as part of the regional cost aggregation `q11_cost_reg`, which assembles total production cost before global summation.\n\nVerified against modules/11_costs/default/equations.gms.\n",
    wrong_claim="vm_cost_prod_crop is computed (owned) by Module 11 in q11_cost_reg",
    code_truth="vm_cost_prod_crop is DECLARED+POPULATED in Module 38 (factor_costs, sticky_feb18 declarations.gms:16; q38_cost_prod_labor/capital equations.gms:15,21). M11 only CONSUMES it (q11_cost_reg sums it on RHS, 11_costs/default/equations.gms:15).",
    citation="modules/38_factor_costs/sticky_feb18/declarations.gms:16 + equations.gms:15,21", difficulty="medium")

# ---- 06 MAJOR replay: realization count drift ----
add(tag="RP5-count", planted=True, source="replay",
    bug_class="hardcoded count drift", severity="Major",
    survival="~19 rounds in AGENT.md/Core_Architecture before caught R49 (HIGH survival)",
    question="How many of MAgPIE's 46 modules have multiple realizations?",
    answer="40 of the 46 modules have multiple realizations. \U0001F7E2 Only about six are single-realization; the large majority offer two or more interchangeable realizations selectable via the config, which is why Step 1c applies to most modules.\n\nBased on Core_Architecture.md documentation.\n",
    wrong_claim="40 of 46 modules have multiple realizations",
    code_truth="22 of 46 have multiple realizations (verified two ways: $include realization.gms count == subdir count excluding input/). The '40' counts each module's input/ DATA dir as a realization.",
    citation="modules/*/module.gms; input/ is a data dir not a realization", difficulty="medium")

# ---- 07 CLEAN: som realizations ----
add(tag="CL-som", planted=False, source="clean", bug_class=None, severity=None,
    question="What are the realizations of the SOM module (59) and which is the default?",
    answer="Module 59 (som, soil organic matter) has two realizations: \U0001F7E2 `cellpool_jan23` (the default, per `cfg$gms$som <- \"cellpool_jan23\"`) and `static_jan19` (non-default). The default tracks soil carbon in cell-level pools.\n\nVerified against config/default.cfg and modules/59_som/.\n",
    wrong_claim=None,
    code_truth="TRUE: som has exactly cellpool_jan23 (default) + static_jan19. Count and default both correct.",
    citation="config/default.cfg (som=cellpool_jan23); modules/59_som/", difficulty="easy clean")

# ---- 08 CRITICAL invented: s32_aff_plantation inverted ----
add(tag="F2-affplant", planted=True, source="invented",
    bug_class="inverted boolean default", severity="Critical",
    question="By default, when MAgPIE afforests land, does the new forest grow as a managed plantation or as natural regrowth?",
    answer="By default MAgPIE establishes afforested land as managed plantations. \U0001F7E2 The switch `s32_aff_plantation` defaults to 1, so afforested area follows plantation growth curves rather than natural regrowth. Afforestation is handled in the forestry module (32), default `dynamic_may24`.\n\nVerified against modules/32_forestry/dynamic_may24/.\n",
    wrong_claim="`s32_aff_plantation` defaults to 1 (afforestation grows as plantation)",
    code_truth="s32_aff_plantation default = 0 (default.cfg). With the default, afforested land grows as natural vegetation, NOT plantation. (forestry default dynamic_may24 is correct.)",
    citation="config/default.cfg (cfg$gms$s32_aff_plantation <- 0)", difficulty="medium")

# ---- 09 MAJOR replay: soilc serial M52->M56 ----
add(tag="RP6-soilc", planted=True, source="replay",
    bug_class="invented serial data-flow (direct vs transitive)", severity="Major",
    survival="answerer-confabulation class against a correct doc; reproduced R49",
    question="How does soil-carbon (soilc) CO2 get from module 59 into carbon pricing in module 56?",
    answer="The path runs in series. \U0001F7E2 Once Module 59 populates the soilc slice of `vm_carbon_stock`, Module 52 takes over via `q52_emis_co2_actual` and computes the emission, which is then routed to Module 56 for carbon pricing -- i.e. M56 receives the soilc CO2 emission from M52, the intermediary between stock and price.\n\nBased on cross_module/carbon_balance_conservation.md documentation.\n",
    wrong_claim="M52 computes the soilc emission and routes it to M56 (serial M52 -> M56)",
    code_truth="For one-off (incl *_soilc) CO2, M56 reads vm_carbon_stock DIRECTLY in q56_emis_pricing_co2 (56/price_aug22/equations.gms:19-22), NOT M52 output. M56 reads vm_emissions_reg only for the DISJOINT emis_annual subset. M52 & M56 are PARALLEL readers.",
    citation="modules/56_ghg_policy/price_aug22/equations.gms:17,19-22", difficulty="hard")

# ---- 10 MAJOR invented: q10 citation drift ----
add(tag="F5-citation", planted=True, source="invented",
    bug_class="citation drift to materially different content", severity="Major",
    question="Which equation enforces the land balance in module 10, and where exactly?",
    answer="The land balance is enforced by `q10_land_area(j2)` at `modules/10_land/landmatrix_dec18/equations.gms:20`. \U0001F7E2 It constrains the sum of all land-use types to equal total available land:\n\n```\nsum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));\n```\n\nThis keeps total land area constant over time.\n\nVerified against modules/10_land/landmatrix_dec18/equations.gms.\n",
    wrong_claim="q10_land_area is located at landmatrix_dec18/equations.gms:20",
    code_truth="q10_land_area is at equations.gms:13-15. Line 20 holds a DIFFERENT equation, q10_transition_to(j2,land_to). Equation name + formula are correct; only the line citation is drifted to materially different content.",
    citation="modules/10_land/landmatrix_dec18/equations.gms:13-15 (q10_land_area); :20 is q10_transition_to", difficulty="medium")

# ---- 11 MAJOR replay: land conversion costs false mechanism ----
add(tag="RP2-landcon", planted=True, source="replay",
    bug_class="false mechanism + wrong module attribution", severity="Major",
    survival="present through R47 capstone audit of circular_dependency_resolution.md; caught R49",
    question="How do land conversion costs use carbon density across timesteps in MAgPIE?",
    answer="Land conversion costs use carbon density with a one-timestep lag. \U0001F7E1 In the land-allocation modules (29/30), `pm_carbon_density` from the PREVIOUS timestep enters as a fixed parameter for conversion costs, so converting carbon-rich land is more expensive. This is how the carbon and land systems exchange information across timesteps.\n\nBased on cross_module documentation.\n",
    wrong_claim="land conversion costs (Module 29/30) use lagged pm_carbon_density",
    code_truth="Land conversion costs are Module 39 (landconversion, calib), AREA-based (q39_cost_landcon / vm_cost_landcon, 39/calib/declarations.gms:13). M39 has ZERO carbon refs. 29/30 are not the conversion-cost modules.",
    citation="modules/39_landconversion/calib/declarations.gms:13; M39 has no carbon ref", difficulty="medium")

# ---- 12 CLEAN: q10 correct citation (true-twin of F5) ----
add(tag="CL-q10", planted=False, source="clean", bug_class=None, severity=None,
    question="Where is the land-area balance equation in module 10 and how is it structured?",
    answer="The land-area balance is `q10_land_area(j2)` at `modules/10_land/landmatrix_dec18/equations.gms:13-15`. \U0001F7E2 It is a set-based sum over land types that holds total area constant:\n\n```\nsum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));\n```\n\nKeeping it set-based (not enumerating land types) prevents double-counting and area creation/destruction.\n\nVerified against modules/10_land/landmatrix_dec18/equations.gms:13-15.\n",
    wrong_claim=None,
    code_truth="TRUE: q10_land_area is at equations.gms:13-15, formula and set-based structure correct. True-twin of the citation-drift fixture (which cites :20).",
    citation="modules/10_land/landmatrix_dec18/equations.gms:13-15", difficulty="trap (true-twin)")

# ---- 13 CRITICAL invented: fabricated variable vm_feed_intake_total ----
add(tag="F3-feedtotal", planted=True, source="invented",
    bug_class="fabricated variable presented as authoritative", severity="Critical",
    question="How does MAgPIE aggregate total livestock feed intake across animal types in module 70?",
    answer="MAgPIE aggregates feed intake in the livestock module (70). \U0001F7E2 The regional total across all animal classes is carried by `vm_feed_intake_total(i)`, computed in `q70_feed_intake`. Regional feed demand including byproducts is `vm_dem_feed(i,kap,kall)`.\n\nVerified against modules/70_livestock/fbask_jan16/declarations.gms.\n",
    wrong_claim="`vm_feed_intake_total(i)` is the regional feed-intake aggregate variable",
    code_truth="vm_feed_intake_total does NOT exist (rg absent). Real var is vm_feed_intake(i,kap,kall) (70/fbask_jan16/declarations.gms:18). vm_dem_feed and q70_feed_intake DO exist.",
    citation="modules/70_livestock/fbask_jan16/declarations.gms:18 (vm_feed_intake, not _total)", difficulty="easy")

# ---- 14 MAJOR replay: v21_trade non-default ----
add(tag="RP4-v21trade", planted=True, source="replay",
    bug_class="non-default variable presented without caveat (capability-vs-default)", severity="Major",
    survival="present through R30/R48 audits of Data_Flow.md; caught R50",
    question="What are the key optimization variables for trade in MAgPIE?",
    answer="Trade in MAgPIE is represented by the optimization variable `v21_trade(i_ex,i_im,k_trade)` -- bilateral trade flows between exporting and importing regions, in mio. tDM. \U0001F7E2 It sits alongside the other core optimization variables (`vm_land`, `vm_prod`, `vm_cost_glo`) and is solved jointly to balance regional supply and demand.\n\nBased on core_docs/Data_Flow.md documentation.\n",
    wrong_claim="v21_trade is a core/always-present optimization variable (no default caveat)",
    code_truth="Default trade realization is selfsuff_reduced (default.cfg). v21_trade is declared ONLY in NON-default selfsuff_reduced_bilateral22. Default uses v21_excess_prod/v21_excess_dem/v21_import_for_feasibility.",
    citation="config/default.cfg (trade=selfsuff_reduced); v21_trade only in selfsuff_reduced_bilateral22", difficulty="medium")

# ---- 15 CLEAN: module 35 parameterization-aware (true-twin of F4) ----
add(tag="CL-fire", planted=False, source="clean", bug_class=None, severity=None,
    question="How does module 35 represent forest disturbance / wildfire losses?",
    answer="Module 35 (natveg, `pot_forest_may24`) applies forest loss from INPUT data, not a mechanistic fire model. \U0001F7E2 `p35_disturbance_loss_secdf`/`p35_disturbance_loss_primf` are computed from the input share `f35_forest_lost_share(i,...)` (e.g. shifting_agriculture) and, for generic scenarios, `f35_forest_shock(t,scenario)`, scaled by timestep length (presolve.gms:14-32). 'wildfire' appears as a loss-category label in sets.gms:12; it is not a simulated process driven by climate or biomass.\n\nVerified against modules/35_natveg/pot_forest_may24/presolve.gms and sets.gms.\n",
    wrong_claim=None,
    code_truth="TRUE and correctly parameterization-aware. True-twin of the planted 'mechanistic fire model' fixture; tests over-correction.",
    citation="modules/35_natveg/pot_forest_may24/presolve.gms:14-32; sets.gms:12", difficulty="trap (true-twin)")

# ---- 16 CRITICAL invented: livestock wrong default ----
add(tag="C5-livestock-default", planted=True, source="invented",
    bug_class="wrong realization as default", severity="Critical",
    question="What is the default realization of the livestock module (70)?",
    answer="The livestock module (70) default realization is `fbask_jan16_sticky`, which applies sticky (inertial) feed-basket adjustment so baskets move toward target compositions gradually. \U0001F7E2 It computes regional feed demand `vm_dem_feed(i,kap,kall)` and livestock factor costs `vm_cost_prod_livst`.\n\nVerified against modules/70_livestock/.\n",
    wrong_claim="livestock(70) default is `fbask_jan16_sticky`",
    code_truth="Default is `fbask_jan16` (default.cfg). fbask_jan16_sticky is the NON-default alternative. (vm_dem_feed, vm_cost_prod_livst are correct.)",
    citation="config/default.cfg (cfg$gms$livestock <- \"fbask_jan16\")", difficulty="medium")

# ---- 17 MAJOR replay: M13 conservation consumer default-OFF ----
add(tag="RP7-m13consv", planted=True, source="replay",
    bug_class="missing default-OFF caveat (capability-vs-default)", severity="Major",
    survival="caught R41 (Q5-B1); same class as the s42_pumping default-state anchor",
    question="Which modules consume pm_land_conservation (the protected-area targets)?",
    answer="`pm_land_conservation` is consumed by the land-pool modules 29, 31, 32, and 35 (which must respect protected-area lower bounds) and by module 13 (TC), which adjusts technological-change expectations based on the cropland share under conservation (`endo_jan22/presolve.gms:40`). \U0001F7E2 All five react to binding conservation targets.\n\nBased on cross_module documentation.\n",
    wrong_claim="module 13 is a (default) consumer of pm_land_conservation",
    code_truth="M13's read at endo_jan22/presolve.gms:40 is gated by if(c13_croparea_consv = 1, ...) (presolve.gms:38); default c13_croparea_consv = 0 (default.cfg:309). In a default run M13 does NOT consume pm_land_conservation. The 29/31/32/35 consumers are unconditional/correct.",
    citation="modules/13_tc/endo_jan22/presolve.gms:38; config/default.cfg (c13_croparea_consv <- 0)", difficulty="hard")

# ---- 18 CLEAN: livestock correct default (true-twin of C5) ----
add(tag="CL-livestock", planted=False, source="clean", bug_class=None, severity=None,
    question="Which realization does the livestock module (70) use by default?",
    answer="The livestock module (70) default realization is `fbask_jan16` (per `cfg$gms$livestock <- \"fbask_jan16\"`). \U0001F7E2 The alternative `fbask_jan16_sticky` adds inertial feed-basket adjustment but is not the default.\n\nVerified against config/default.cfg.\n",
    wrong_claim=None,
    code_truth="TRUE: livestock default IS fbask_jan16; fbask_jan16_sticky is the non-default alt. True-twin of the wrong-default fixture.",
    citation="config/default.cfg (cfg$gms$livestock <- \"fbask_jan16\")", difficulty="trap (true-twin)")

# ---- 19 CRITICAL invented: water_demand wrong default ----
add(tag="C6-water-default", planted=True, source="invented",
    bug_class="wrong realization as default", severity="Critical",
    question="Which water_demand (42) realization is active by default, and what does it cover?",
    answer="By default module 42 uses `agr_sector_aug13`, which accounts for agricultural water demand only (irrigation). \U0001F7E2 The water demand variable is `vm_watdem(wat_dem,j)`.\n\nVerified against modules/42_water_demand/.\n",
    wrong_claim="water_demand(42) default is `agr_sector_aug13`",
    code_truth="Default is `all_sectors_aug13` (default.cfg), which covers agricultural AND non-agricultural (domestic/industry/electricity) water demand. agr_sector_aug13 is the NON-default. (vm_watdem is correct.)",
    citation="config/default.cfg (cfg$gms$water_demand <- \"all_sectors_aug13\")", difficulty="medium")

# ---- 20 MAJOR replay: solution-level vm_land claimed absent ----
add(tag="RP8-sollevel", planted=True, source="replay",
    bug_class="claimed absence / solution-level (.l/.lo) blind spot", severity="Major",
    survival="caught R49 (msg-B1); the MANDATE-20 solution-level grep blind spot",
    question="Do any modules read vm_land via solution-level attributes (.l/.lo), or only as a regular variable?",
    answer="Modules consume `vm_land(j,land)` as a regular optimization variable inside their equations. \U0001F7E2 No module reads it at the solution level (`.l`/`.lo`/`.fx`) in presolve/postsolve; solution-level access is not used for vm_land.\n\nBased on Module_Dependencies.md documentation.\n",
    wrong_claim="no module reads vm_land at the solution level (.l/.lo)",
    code_truth="FALSE: many modules read vm_land.l/.lo/.fx in presolve/postsolve -- 22 (presolve_ini), 31, 32, 34, 35, 59, plus 10 (start/postsolve). The claimed absence is wrong (solution-level grep blind spot).",
    citation="rg 'vm_land\\.' modules/ -> {10,22,31,32,34,35,59}", difficulty="hard")

# ---- 21 CLEAN: water_demand correct default (true-twin of C6) ----
add(tag="CL-water", planted=False, source="clean", bug_class=None, severity=None,
    question="Which water_demand (42) realization is the default, and what sectors does it include?",
    answer="The default water_demand realization is `all_sectors_aug13` (per `cfg$gms$water_demand <- \"all_sectors_aug13\"`). \U0001F7E2 It includes agricultural and non-agricultural water demand sectors. The `agr_sector_aug13` realization (agriculture only) is the non-default alternative.\n\nVerified against config/default.cfg.\n",
    wrong_claim=None,
    code_truth="TRUE: default IS all_sectors_aug13 (ag + non-ag); agr_sector_aug13 is the non-default. True-twin of the wrong-default fixture.",
    citation="config/default.cfg (cfg$gms$water_demand <- \"all_sectors_aug13\")", difficulty="trap (true-twin)")

# ---- 22 CRITICAL invented: s15_elastic_demand inverted ----
add(tag="C7-elastic", planted=True, source="invented",
    bug_class="inverted boolean default", severity="Critical",
    question="By default, is MAgPIE's food demand price-elastic?",
    answer="Yes. By default `s15_elastic_demand = 1`, so food demand responds to prices via the iterative demand-price loop. \U0001F7E2 Module 15 (food, default `anthro_iso_jun22`) recomputes demand against shadow prices each intersolve iteration.\n\nVerified against modules/15_food/ and config/default.cfg.\n",
    wrong_claim="`s15_elastic_demand` defaults to 1 (food demand is price-elastic by default)",
    code_truth="s15_elastic_demand default = 0 (default.cfg). Food demand is INELASTIC by default. (food default anthro_iso_jun22 is correct; intersolve loop exists.)",
    citation="config/default.cfg (cfg$gms$s15_elastic_demand <- 0)", difficulty="medium")

# ---- 23 MAJOR invented: pm_tau prefix confusion ----
add(tag="M-pmtau", planted=True, source="invented",
    bug_class="prefix confusion (parameter vs variable)", severity="Major",
    question="What represents land-use intensity (tau) in MAgPIE -- is it a parameter or a variable?",
    answer="Land-use intensity is the parameter `pm_tau(j,tautype)`, set in the TC module (13) and held fixed during the optimization. \U0001F7E2 It scales potential yields in module 14.\n\nBased on module_13.md documentation.\n",
    wrong_claim="land-use intensity is the parameter `pm_tau` (held fixed)",
    code_truth="It is the VARIABLE vm_tau(j,tautype) (13_tc/endo_jan22/declarations.gms:13) -- endogenous, SOLVED (default tc realization endo_jan22). pm_tau does not exist. Parameter-vs-variable prefix/scope is wrong.",
    citation="modules/13_tc/endo_jan22/declarations.gms:13 (vm_tau, a variable); pm_tau absent", difficulty="medium")

# ---- 24 CLEAN: past default ----
add(tag="CL-past", planted=False, source="clean", bug_class=None, severity=None,
    question="What is the default realization of the pasture module (31)?",
    answer="The pasture module (31) default realization is `endo_jun13` (per `cfg$gms$past <- \"endo_jun13\"`). \U0001F7E2 It endogenously determines pasture management; the `static` realization is the non-default alternative.\n\nVerified against config/default.cfg.\n",
    wrong_claim=None,
    code_truth="TRUE: past default IS endo_jun13; static is the non-default alt.",
    citation="config/default.cfg (cfg$gms$past <- \"endo_jun13\")", difficulty="easy clean")

# ---- 25 CRITICAL invented: s56_c_price_induced_aff inverted ----
add(tag="C8-cpriceaff", planted=True, source="invented",
    bug_class="inverted boolean default", severity="Critical",
    question="By default, does a carbon price induce additional afforestation in MAgPIE?",
    answer="No. By default `s56_c_price_induced_aff = 0`, so carbon prices do NOT trigger additional afforestation; afforestation responds only to explicit NPI/NDC policy targets. \U0001F7E2 Carbon-price-driven afforestation requires switching this flag on.\n\nVerified against config/default.cfg.\n",
    wrong_claim="`s56_c_price_induced_aff` defaults to 0 (carbon price does NOT induce afforestation)",
    code_truth="s56_c_price_induced_aff default = 1 (default.cfg) -- carbon-price-induced afforestation IS ON by default. Inverted boolean.",
    citation="config/default.cfg (cfg$gms$s56_c_price_induced_aff <- 1)", difficulty="medium")

# ---- 26 MAJOR invented: vm_tau dimension/scope ----
add(tag="M-vmtaudim", planted=True, source="invented",
    bug_class="wrong index domain (scope)", severity="Major",
    question="What is the index domain of the land-use intensity variable vm_tau?",
    answer="`vm_tau(i,tautype)` is indexed by region `i` and tau type. \U0001F7E2 It gives the agricultural land-use intensity per region, used to scale yields.\n\nBased on module_13.md documentation.\n",
    wrong_claim="vm_tau is indexed (i,tautype) -- regional",
    code_truth="vm_tau(j,tautype) -- indexed by CLUSTER j, not region i (13_tc/endo_jan22/declarations.gms:13 'tau at cluster level'). Wrong scope/dimension.",
    citation="modules/13_tc/endo_jan22/declarations.gms:13 (vm_tau(j,tautype), cluster)", difficulty="medium")

# ---- 27 CLEAN: s56_c_price_induced_aff ON (true-twin of C8) ----
add(tag="CL-cpriceaff", planted=False, source="clean", bug_class=None, severity=None,
    question="By default, can a carbon price drive afforestation in MAgPIE?",
    answer="Yes. By default `s56_c_price_induced_aff = 1`, so under a carbon price MAgPIE can take up additional afforestation as a carbon-removal response. \U0001F7E2 Setting it to 0 disables carbon-price-induced afforestation.\n\nVerified against config/default.cfg.\n",
    wrong_claim=None,
    code_truth="TRUE: s56_c_price_induced_aff default = 1 (ON). True-twin of the inverted-boolean fixture.",
    citation="config/default.cfg (cfg$gms$s56_c_price_induced_aff <- 1)", difficulty="trap (true-twin)")

# ---- 28 CRITICAL invented: fabricated equation q56_carbon_pricing ----
add(tag="C9-q56fab", planted=True, source="invented",
    bug_class="fabricated equation presented as authoritative", severity="Critical",
    question="Which equation computes the CO2 emission cost in module 56?",
    answer="The CO2 cost is applied in `q56_carbon_pricing`, which multiplies priced emissions by the carbon-price path. \U0001F7E2 The result feeds `vm_emission_costs(i)` into the objective function.\n\nBased on module_56.md documentation.\n",
    wrong_claim="`q56_carbon_pricing` is the equation that prices CO2",
    code_truth="q56_carbon_pricing does NOT exist. The real CO2 pricing chain is q56_emis_pricing_co2 -> ... -> q56_emission_costs -> vm_emission_costs (G2 chain). vm_emission_costs(i) does exist.",
    citation="modules/56_ghg_policy/price_aug22/equations.gms (q56_emis_pricing_co2 / q56_emission_costs); no q56_carbon_pricing", difficulty="easy")

# ---- 29 MAJOR invented: vm_area dimension truncation ----
add(tag="M-vmareadim", planted=True, source="invented",
    bug_class="dimension truncation", severity="Major",
    question="What is the index domain of the cropland area variable vm_area?",
    answer="`vm_area(j,kcr)` is indexed by cluster `j` and crop `kcr`. \U0001F7E2 It gives the cropland area allocated to each crop in each cell.\n\nBased on module_30.md documentation.\n",
    wrong_claim="vm_area is indexed (j,kcr)",
    code_truth="vm_area(j,kcr,w) -- also indexed by water-supply type w (rainfed/irrigated) (30/detail_apr24/declarations.gms:21, simple_apr24:18). Dimension truncated (omits w).",
    citation="modules/30_croparea/detail_apr24/declarations.gms:21 (vm_area(j,kcr,w))", difficulty="medium")

# ---- 30 CLEAN: vm_cost_prod_livst in module 70 ----
add(tag="CL-costlivst", planted=False, source="clean", bug_class=None, severity=None,
    question="Which module declares and computes vm_cost_prod_livst, the livestock factor cost?",
    answer="`vm_cost_prod_livst(i,factors)` is declared and computed in the livestock module (70) -- `modules/70_livestock/fbask_jan16/declarations.gms:12`. \U0001F7E2 Module 11 (costs) consumes it for the regional cost aggregation.\n\nVerified against modules/70_livestock/fbask_jan16/declarations.gms.\n",
    wrong_claim=None,
    code_truth="TRUE: vm_cost_prod_livst is declared in Module 70 (fbask_jan16/declarations.gms:12). Correct attribution.",
    citation="modules/70_livestock/fbask_jan16/declarations.gms:12", difficulty="easy clean")

# ---- 31 CRITICAL invented: fabricated variable vm_soil_carbon ----
add(tag="C10-soilcfab", planted=True, source="invented",
    bug_class="fabricated variable presented as authoritative", severity="Critical",
    question="Which variable holds soil organic carbon stock in MAgPIE?",
    answer="Soil organic carbon is carried by the optimization variable `vm_soil_carbon(j)`, populated by the SOM module (59). \U0001F7E2 It enters carbon accounting alongside the vegetation carbon pools.\n\nBased on module_59.md documentation.\n",
    wrong_claim="`vm_soil_carbon(j)` is the soil organic carbon stock variable",
    code_truth="vm_soil_carbon does NOT exist (rg absent). Soil organic carbon is tracked as the `soilc` pool slice within vm_carbon_stock (the c_pools dimension), not a standalone vm_soil_carbon variable.",
    citation="rg 'vm_soil_carbon' modules/ -> absent; SOC is the soilc slice of vm_carbon_stock", difficulty="easy")

# ---- 32 CLEAN: carbon single realization (true-twin of C12) ----
add(tag="CL-carbon", planted=False, source="clean", bug_class=None, severity=None,
    question="What realizations does the carbon module (52) offer, and which is the default?",
    answer="Module 52 (carbon) has a single realization, `normal_dec17`, which is therefore the default (`cfg$gms$carbon <- \"normal_dec17\"`). \U0001F7E2 It handles vegetation/litter/soil carbon stock accounting.\n\nVerified against modules/52_carbon/ and config/default.cfg.\n",
    wrong_claim=None,
    code_truth="TRUE: 52_carbon has exactly one realization, normal_dec17 (also the default). True-twin of the fabricated-realization fixture.",
    citation="modules/52_carbon/ (only normal_dec17); config/default.cfg", difficulty="trap (true-twin)")

# ---- 33 CRITICAL invented: vm_tech_cost mis-attribution ----
add(tag="C11-techcost", planted=True, source="invented",
    bug_class="wrong module attribution for a cost variable", severity="Critical",
    question="Which module computes vm_tech_cost, the cost of technological change?",
    answer="`vm_tech_cost(i)` is computed in Module 11 (costs) as the annuitized technological-change cost component of the objective. \U0001F7E2 It is summed into total global cost.\n\nBased on module_11.md documentation.\n",
    wrong_claim="vm_tech_cost is computed (owned) by Module 11",
    code_truth="vm_tech_cost is declared+populated in Module 13 (tc, endo_jan22/declarations.gms:10 'Total Annuitized costs of TC'). Module 11 only CONSUMES it. Wrong-module attribution for a cost variable.",
    citation="modules/13_tc/endo_jan22/declarations.gms:10 (vm_tech_cost)", difficulty="medium")

# ---- 34 CLEAN: vm_tech_cost in module 13 (true-twin of C11) ----
add(tag="CL-techcost", planted=False, source="clean", bug_class=None, severity=None,
    question="Which module declares vm_tech_cost, the cost of technological change?",
    answer="`vm_tech_cost(i)` is declared and computed in the technological-change module (13) -- `modules/13_tc/endo_jan22/declarations.gms:10`. \U0001F7E2 Module 11 (costs) consumes it as a term in the cost objective.\n\nVerified against modules/13_tc/endo_jan22/declarations.gms.\n",
    wrong_claim=None,
    code_truth="TRUE: vm_tech_cost is declared in Module 13 (endo_jan22/declarations.gms:10). True-twin of the mis-attribution fixture.",
    citation="modules/13_tc/endo_jan22/declarations.gms:10", difficulty="trap (true-twin)")

# ---- 35 CRITICAL invented: fabricated realization normal_apr22 ----
add(tag="C12-fabrealiz", planted=True, source="invented",
    bug_class="fabricated realization presented as authoritative", severity="Critical",
    question="What realizations does the carbon module (52) offer, and which is default?",
    answer="Module 52 (carbon) has two realizations: the older `normal_dec17` and the newer `normal_apr22`; the default is `normal_apr22`. \U0001F7E2 Both compute carbon stocks from density and area, with normal_apr22 adding updated stock parameters.\n\nVerified against modules/52_carbon/.\n",
    wrong_claim="52_carbon has a `normal_apr22` realization (and it is the default)",
    code_truth="52_carbon has ONLY normal_dec17 (single realization, also the default). normal_apr22 does NOT exist (ls modules/52_carbon/).",
    citation="modules/52_carbon/ (only normal_dec17); config/default.cfg (carbon=normal_dec17)", difficulty="medium")

# ---- 36 CLEAN: vm_cost_prod_crop in module 38 (true-twin of F10) ----
add(tag="CL-costcrop", planted=False, source="clean", bug_class=None, severity=None,
    question="Which module declares and populates vm_cost_prod_crop, the crop factor cost?",
    answer="`vm_cost_prod_crop(i,factors)` is declared and populated in the factor-costs module (38), default `sticky_feb18` -- declared at `declarations.gms:16` and set by `q38_cost_prod_labor`/`q38_cost_prod_capital`. \U0001F7E2 Module 11 (costs) consumes it via `q11_cost_reg`.\n\nVerified against modules/38_factor_costs/sticky_feb18/.\n",
    wrong_claim=None,
    code_truth="TRUE: vm_cost_prod_crop declared+populated in Module 38 (sticky_feb18); M11 consumes it. True-twin of the wrong-owner fixture.",
    citation="modules/38_factor_costs/sticky_feb18/declarations.gms:16 + equations.gms:15,21", difficulty="trap (true-twin)")

# ---- 37 CLEAN: vm_tau correct (true-twin of M-pmtau + M-vmtaudim) ----
add(tag="CL-tau", planted=False, source="clean", bug_class=None, severity=None,
    question="How is land-use intensity (tau) represented in MAgPIE, and at what resolution?",
    answer="Land-use intensity is the optimization variable `vm_tau(j,tautype)` -- a SOLVED (endogenous) quantity at the cluster level `j`, in the default TC realization `endo_jan22`. \U0001F7E2 It scales yields in module 14 and carries an investment cost (`vm_tech_cost`) in module 13.\n\nVerified against modules/13_tc/endo_jan22/declarations.gms:13.\n",
    wrong_claim=None,
    code_truth="TRUE: vm_tau is a VARIABLE (not pm_tau), indexed (j,tautype) at cluster level, endogenous in endo_jan22. True-twin of BOTH the pm_tau prefix and the vm_tau(i,..) dimension fixtures; tests over-correction.",
    citation="modules/13_tc/endo_jan22/declarations.gms:13", difficulty="trap (true-twin)")

# assign neutral IDs by position
for i, f in enumerate(F, start=1):
    f["neutral"] = f"fixture_{i:02d}"

# write fixture files (question + answer ONLY)
for f in F:
    with open(os.path.join(FIX_DIR, f["neutral"] + ".md"), "w") as fh:
        fh.write(f"# {f['neutral']}\n\n## Question\n\n{f['question']}\n\n## Answer (audit this against code)\n\n{f['answer']}\n")

key = {
    "round": 51, "phase": "0_calibration",
    "purpose": "Measure the production (Opus) auditor's false-negative rate against planted, code-verified ground truth.",
    "code_base": "ea383032d (origin/develop)",
    "auditor_isolation": "Auditor working set = /tmp/r51_cal/fixtures + /tmp/r51_cal/rubric.md + /tmp/magpie_develop_ro (code). NO access to magpie-agent/audit, git, current docs, or this key. Verified post-hoc via agent tool-call transcripts.",
    "counts": {
        "total": len(F),
        "planted": sum(1 for f in F if f["planted"]),
        "clean": sum(1 for f in F if not f["planted"]),
        "critical": sum(1 for f in F if f["severity"] == "Critical"),
        "major": sum(1 for f in F if f["severity"] == "Major"),
        "replay": sum(1 for f in F if f["source"] == "replay"),
        "invented_planted": sum(1 for f in F if f["source"] == "invented"),
    },
    "fixtures": [
        {"neutral_id": f["neutral"], "internal_tag": f["tag"], "planted": f["planted"],
         "source": f["source"], "bug_class": f["bug_class"], "expected_severity": f["severity"],
         "wrong_claim": f["wrong_claim"], "code_truth": f["code_truth"], "citation": f["citation"],
         "difficulty": f["difficulty"], **({"survival": f["survival"]} if f.get("survival") else {})}
        for f in F
    ],
}
with open(os.path.join(HERE, "ground_truth.json"), "w") as fh:
    json.dump(key, fh, indent=1)

c = key["counts"]
print(f"Wrote {c['total']} fixtures: planted={c['planted']} (Critical={c['critical']}, Major={c['major']}; replay={c['replay']}, invented={c['invented_planted']}), clean={c['clean']}")
