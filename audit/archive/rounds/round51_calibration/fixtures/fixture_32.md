# fixture_32

## Question

What realizations does the carbon module (52) offer, and which is the default?

## Answer (audit this against code)

Module 52 (carbon) has a single realization, `normal_dec17`, which is therefore the default (`cfg$gms$carbon <- "normal_dec17"`). 🟢 It handles vegetation/litter/soil carbon stock accounting.

Verified against modules/52_carbon/ and config/default.cfg.

