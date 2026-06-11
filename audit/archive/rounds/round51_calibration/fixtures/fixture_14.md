# fixture_14

## Question

What are the key optimization variables for trade in MAgPIE?

## Answer (audit this against code)

Trade in MAgPIE is represented by the optimization variable `v21_trade(i_ex,i_im,k_trade)` -- bilateral trade flows between exporting and importing regions, in mio. tDM. 🟢 It sits alongside the other core optimization variables (`vm_land`, `vm_prod`, `vm_cost_glo`) and is solved jointly to balance regional supply and demand.

Based on core_docs/Data_Flow.md documentation.

