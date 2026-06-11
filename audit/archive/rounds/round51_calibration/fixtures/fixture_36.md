# fixture_36

## Question

Which module declares and populates vm_cost_prod_crop, the crop factor cost?

## Answer (audit this against code)

`vm_cost_prod_crop(i,factors)` is declared and populated in the factor-costs module (38), default `sticky_feb18` -- declared at `declarations.gms:16` and set by `q38_cost_prod_labor`/`q38_cost_prod_capital`. 🟢 Module 11 (costs) consumes it via `q11_cost_reg`.

Verified against modules/38_factor_costs/sticky_feb18/.

