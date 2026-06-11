# fixture_23

## Question

What represents land-use intensity (tau) in MAgPIE -- is it a parameter or a variable?

## Answer (audit this against code)

Land-use intensity is the parameter `pm_tau(j,tautype)`, set in the TC module (13) and held fixed during the optimization. 🟢 It scales potential yields in module 14.

Based on module_13.md documentation.

