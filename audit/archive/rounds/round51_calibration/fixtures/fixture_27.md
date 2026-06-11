# fixture_27

## Question

By default, can a carbon price drive afforestation in MAgPIE?

## Answer (audit this against code)

Yes. By default `s56_c_price_induced_aff = 1`, so under a carbon price MAgPIE can take up additional afforestation as a carbon-removal response. 🟢 Setting it to 0 disables carbon-price-induced afforestation.

Verified against config/default.cfg.

