# fixture_25

## Question

By default, does a carbon price induce additional afforestation in MAgPIE?

## Answer (audit this against code)

No. By default `s56_c_price_induced_aff = 0`, so carbon prices do NOT trigger additional afforestation; afforestation responds only to explicit NPI/NDC policy targets. 🟢 Carbon-price-driven afforestation requires switching this flag on.

Verified against config/default.cfg.

