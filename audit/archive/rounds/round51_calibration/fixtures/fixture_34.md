# fixture_34

## Question

Which module declares vm_tech_cost, the cost of technological change?

## Answer (audit this against code)

`vm_tech_cost(i)` is declared and computed in the technological-change module (13) -- `modules/13_tc/endo_jan22/declarations.gms:10`. 🟢 Module 11 (costs) consumes it as a term in the cost objective.

Verified against modules/13_tc/endo_jan22/declarations.gms.

