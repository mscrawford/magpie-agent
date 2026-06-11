# fixture_13

## Question

How does MAgPIE aggregate total livestock feed intake across animal types in module 70?

## Answer (audit this against code)

MAgPIE aggregates feed intake in the livestock module (70). 🟢 The regional total across all animal classes is carried by `vm_feed_intake_total(i)`, computed in `q70_feed_intake`. Regional feed demand including byproducts is `vm_dem_feed(i,kap,kall)`.

Verified against modules/70_livestock/fbask_jan16/declarations.gms.

