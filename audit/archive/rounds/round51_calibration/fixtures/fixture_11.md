# fixture_11

## Question

How do land conversion costs use carbon density across timesteps in MAgPIE?

## Answer (audit this against code)

Land conversion costs use carbon density with a one-timestep lag. 🟡 In the land-allocation modules (29/30), `pm_carbon_density` from the PREVIOUS timestep enters as a fixed parameter for conversion costs, so converting carbon-rich land is more expensive. This is how the carbon and land systems exchange information across timesteps.

Based on cross_module documentation.

