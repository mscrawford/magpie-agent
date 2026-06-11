# fixture_08

## Question

By default, when MAgPIE afforests land, does the new forest grow as a managed plantation or as natural regrowth?

## Answer (audit this against code)

By default MAgPIE establishes afforested land as managed plantations. 🟢 The switch `s32_aff_plantation` defaults to 1, so afforested area follows plantation growth curves rather than natural regrowth. Afforestation is handled in the forestry module (32), default `dynamic_may24`.

Verified against modules/32_forestry/dynamic_may24/.

