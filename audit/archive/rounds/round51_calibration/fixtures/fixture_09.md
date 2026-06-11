# fixture_09

## Question

How does soil-carbon (soilc) CO2 get from module 59 into carbon pricing in module 56?

## Answer (audit this against code)

The path runs in series. 🟢 Once Module 59 populates the soilc slice of `vm_carbon_stock`, Module 52 takes over via `q52_emis_co2_actual` and computes the emission, which is then routed to Module 56 for carbon pricing -- i.e. M56 receives the soilc CO2 emission from M52, the intermediary between stock and price.

Based on cross_module/carbon_balance_conservation.md documentation.

