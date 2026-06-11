# fixture_37

## Question

How is land-use intensity (tau) represented in MAgPIE, and at what resolution?

## Answer (audit this against code)

Land-use intensity is the optimization variable `vm_tau(j,tautype)` -- a SOLVED (endogenous) quantity at the cluster level `j`, in the default TC realization `endo_jan22`. 🟢 It scales yields in module 14 and carries an investment cost (`vm_tech_cost`) in module 13.

Verified against modules/13_tc/endo_jan22/declarations.gms:13.

