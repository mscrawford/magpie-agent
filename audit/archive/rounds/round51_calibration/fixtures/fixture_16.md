# fixture_16

## Question

What is the default realization of the livestock module (70)?

## Answer (audit this against code)

The livestock module (70) default realization is `fbask_jan16_sticky`, which applies sticky (inertial) feed-basket adjustment so baskets move toward target compositions gradually. 🟢 It computes regional feed demand `vm_dem_feed(i,kap,kall)` and livestock factor costs `vm_cost_prod_livst`.

Verified against modules/70_livestock/.

