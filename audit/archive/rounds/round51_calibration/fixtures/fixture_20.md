# fixture_20

## Question

Do any modules read vm_land via solution-level attributes (.l/.lo), or only as a regular variable?

## Answer (audit this against code)

Modules consume `vm_land(j,land)` as a regular optimization variable inside their equations. 🟢 No module reads it at the solution level (`.l`/`.lo`/`.fx`) in presolve/postsolve; solution-level access is not used for vm_land.

Based on Module_Dependencies.md documentation.

