# fixture_07

## Question

What are the realizations of the SOM module (59) and which is the default?

## Answer (audit this against code)

Module 59 (som, soil organic matter) has two realizations: 🟢 `cellpool_jan23` (the default, per `cfg$gms$som <- "cellpool_jan23"`) and `static_jan19` (non-default). The default tracks soil carbon in cell-level pools.

Verified against config/default.cfg and modules/59_som/.

