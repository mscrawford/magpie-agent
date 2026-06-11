# fixture_18

## Question

Which realization does the livestock module (70) use by default?

## Answer (audit this against code)

The livestock module (70) default realization is `fbask_jan16` (per `cfg$gms$livestock <- "fbask_jan16"`). 🟢 The alternative `fbask_jan16_sticky` adds inertial feed-basket adjustment but is not the default.

Verified against config/default.cfg.

