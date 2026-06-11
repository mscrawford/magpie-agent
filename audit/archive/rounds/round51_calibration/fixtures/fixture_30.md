# fixture_30

## Question

Which module declares and computes vm_cost_prod_livst, the livestock factor cost?

## Answer (audit this against code)

`vm_cost_prod_livst(i,factors)` is declared and computed in the livestock module (70) -- `modules/70_livestock/fbask_jan16/declarations.gms:12`. 🟢 Module 11 (costs) consumes it for the regional cost aggregation.

Verified against modules/70_livestock/fbask_jan16/declarations.gms.

