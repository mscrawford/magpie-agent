# fixture_05

## Question

Which module computes vm_cost_prod_crop (the crop factor cost), and in which equation?

## Answer (audit this against code)

`vm_cost_prod_crop(i,factors)` is the regional factor cost (capital and labor) of crop production. 🟢 It is computed in Module 11 (costs) as part of the regional cost aggregation `q11_cost_reg`, which assembles total production cost before global summation.

Verified against modules/11_costs/default/equations.gms.

