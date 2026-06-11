# fixture_10

## Question

Which equation enforces the land balance in module 10, and where exactly?

## Answer (audit this against code)

The land balance is enforced by `q10_land_area(j2)` at `modules/10_land/landmatrix_dec18/equations.gms:20`. 🟢 It constrains the sum of all land-use types to equal total available land:

```
sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```

This keeps total land area constant over time.

Verified against modules/10_land/landmatrix_dec18/equations.gms.

