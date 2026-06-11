# fixture_17

## Question

Which modules consume pm_land_conservation (the protected-area targets)?

## Answer (audit this against code)

`pm_land_conservation` is consumed by the land-pool modules 29, 31, 32, and 35 (which must respect protected-area lower bounds) and by module 13 (TC), which adjusts technological-change expectations based on the cropland share under conservation (`endo_jan22/presolve.gms:40`). 🟢 All five react to binding conservation targets.

Based on cross_module documentation.

