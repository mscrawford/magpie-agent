# fixture_21

## Question

Which water_demand (42) realization is the default, and what sectors does it include?

## Answer (audit this against code)

The default water_demand realization is `all_sectors_aug13` (per `cfg$gms$water_demand <- "all_sectors_aug13"`). 🟢 It includes agricultural and non-agricultural water demand sectors. The `agr_sector_aug13` realization (agriculture only) is the non-default alternative.

Verified against config/default.cfg.

