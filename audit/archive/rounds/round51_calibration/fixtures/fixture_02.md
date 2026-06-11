# fixture_02

## Question

What is the default realization of the croparea module (30), and what does it track?

## Answer (audit this against code)

The croparea module (30) default realization is `detail_apr24`, which disaggregates cropland into individual crop types per cell. 🟢 It tracks `vm_area(j,kcr,w)` indexed by crop (`kcr`) and water supply (`w`, rainfed/irrigated), and sits downstream of the cropland module (29).

Verified against modules/30_croparea/detail_apr24/declarations.gms.

