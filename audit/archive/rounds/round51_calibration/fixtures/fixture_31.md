# fixture_31

## Question

Which variable holds soil organic carbon stock in MAgPIE?

## Answer (audit this against code)

Soil organic carbon is carried by the optimization variable `vm_soil_carbon(j)`, populated by the SOM module (59). 🟢 It enters carbon accounting alongside the vegetation carbon pools.

Based on module_59.md documentation.

