# fixture_04

## Question

How does MAgPIE model forest loss from wildfire in natural vegetation (module 35)?

## Answer (audit this against code)

Module 35 (natveg, default `pot_forest_may24`) represents wildfire disturbance dynamically. 🟢 It computes an annual fire risk as a function of climate drivers (temperature and precipitation) and standing biomass, and releases the corresponding carbon when forest burns. Losses are tracked in `p35_disturbance_loss_secdf`/`p35_disturbance_loss_primf`.

Verified against modules/35_natveg/pot_forest_may24/presolve.gms.

