# fixture_12

## Question

Where is the land-area balance equation in module 10 and how is it structured?

## Answer (audit this against code)

The land-area balance is `q10_land_area(j2)` at `modules/10_land/landmatrix_dec18/equations.gms:13-15`. 🟢 It is a set-based sum over land types that holds total area constant:

```
sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```

Keeping it set-based (not enumerating land types) prevents double-counting and area creation/destruction.

Verified against modules/10_land/landmatrix_dec18/equations.gms:13-15.

