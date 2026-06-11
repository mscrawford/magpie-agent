# fixture_03

## Question

Which interface variables does module 51 (nitrogen) receive, and from which module?

## Answer (audit this against code)

Module 51 (nitrogen emissions) receives several inputs. 🟢 From Module 50 (NR Soil Budget): `vm_manure_recycling(i,'nr')` -- manure nitrogen recycled to cropland (Mt N), read at `equations.gms:25`. Module 51 uses these flows to compute N2O and NH3 pathways.

Based on module_51.md documentation.

