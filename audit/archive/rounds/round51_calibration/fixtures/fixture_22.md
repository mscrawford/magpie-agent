# fixture_22

## Question

By default, is MAgPIE's food demand price-elastic?

## Answer (audit this against code)

Yes. By default `s15_elastic_demand = 1`, so food demand responds to prices via the iterative demand-price loop. 🟢 Module 15 (food, default `anthro_iso_jun22`) recomputes demand against shadow prices each intersolve iteration.

Verified against modules/15_food/ and config/default.cfg.

