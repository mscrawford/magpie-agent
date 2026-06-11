# fixture_15

## Question

How does module 35 represent forest disturbance / wildfire losses?

## Answer (audit this against code)

Module 35 (natveg, `pot_forest_may24`) applies forest loss from INPUT data, not a mechanistic fire model. 🟢 `p35_disturbance_loss_secdf`/`p35_disturbance_loss_primf` are computed from the input share `f35_forest_lost_share(i,...)` (e.g. shifting_agriculture) and, for generic scenarios, `f35_forest_shock(t,scenario)`, scaled by timestep length (presolve.gms:14-32). 'wildfire' appears as a loss-category label in sets.gms:12; it is not a simulated process driven by climate or biomass.

Verified against modules/35_natveg/pot_forest_may24/presolve.gms and sets.gms.

