# fixture_19

## Question

Which water_demand (42) realization is active by default, and what does it cover?

## Answer (audit this against code)

By default module 42 uses `agr_sector_aug13`, which accounts for agricultural water demand only (irrigation). 🟢 The water demand variable is `vm_watdem(wat_dem,j)`.

Verified against modules/42_water_demand/.

