# fixture_26

## Question

What is the index domain of the land-use intensity variable vm_tau?

## Answer (audit this against code)

`vm_tau(i,tautype)` is indexed by region `i` and tau type. 🟢 It gives the agricultural land-use intensity per region, used to scale yields.

Based on module_13.md documentation.

