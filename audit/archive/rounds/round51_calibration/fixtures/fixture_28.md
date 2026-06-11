# fixture_28

## Question

Which equation computes the CO2 emission cost in module 56?

## Answer (audit this against code)

The CO2 cost is applied in `q56_carbon_pricing`, which multiplies priced emissions by the carbon-price path. 🟢 The result feeds `vm_emission_costs(i)` into the objective function.

Based on module_56.md documentation.

