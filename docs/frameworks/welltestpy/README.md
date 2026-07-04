# welltestpy — real field pumping-test campaigns (the field-data lane)

**What / why.** [welltestpy](https://github.com/GeoStat-Framework/welltestpy) (MIT, GeoStat-Framework)
is the loader for FlowDNA's REAL field-data lane: transient pumping-test drawdown from two aquifer
field sites, used to show the GeoType shape-diagnostic methodology **generalizes beyond fractured
reservoirs to real aquifer field data**. It provides the `Campaign` / `PumpingTest` / `Observation`
data model and reads the `.cmp` campaign files.

**Data + license.** `GeoStat-Examples/welltestpy-field-site-analysis` (MIT, Zenodo **4139374** v1.0.1,
8.5 MB): `horkheim.cmp` (Horkheimer Insel, Heilbronn) + `lauswiesen.cmp` (Lauswiesen, Tuebingen).
MIT: an OFFLINE dependency, vault-only (`$FLOWDNA_VAULT/field/`), never vendored into the repo (like
the 4TU corpus). The repo commits only the derived study trace (decimated), never the raw `.cmp`.

**API path (verified 2026-07-04).**
- `welltestpy.load_campaign(cmp_file)` -> `Campaign` with `.fieldsite`, `.wells` (each Well has
  `.coordinates` (x, y), `.welldepth`, `.screensize`, `.aquiferdepth`, `.radius`), and `.tests`.
- each `.tests[name]` is a `PumpingTest` with `.pumpingwell`, `.pumpingrate` (Q, m^3/s) and
  `.observations` (one per observation well).
- each observation `o` is a transient: `o.time` (ndarray) + `o.observation` (drawdown ndarray).
- the radial distance r = |coordinates(pumping well) - coordinates(observation well)|.

**Integration (`io/field_data.py`, `field` case kind).** `load_field(sites)` iterates
(site, pumping test, observation well), extracts the usable transient drawdown s(t) (>= 10 finite
t>0 samples, r > 0.1 m, real drawdown span; long series decimated to a log grid), and builds the
descriptor table `[log_r, log_Q, site, well_depth, screen_size, aquifer_depth]`. `_precompute_field`
runs it through the SAME study pipeline as the 4TU real lane, except the curves are RAW drawdown so
preprocessing uses the Bourdet first derivative (`derivative_order=1`). ~44 usable curves across both
sites -> AquiferType catalogue + conformal + attribution.

**Honesty posture.** Aquifer pumping tests are a DIFFERENT physical system from fractured reservoirs;
only the derivative-shape diagnostic transfers, and T/S are unknown (welltestpy ESTIMATES them), so
curves are clustered by shape, not a T/S-referenced dimensionless response. The honest finding is
that both well-characterized aquifers are predominantly one infinite-acting-radial (Theis) type with
a few outlier wells, and the AquiferType is not predictable from distance/rate/site (a real null
result the attribution gate reports rather than manufacturing a control). See `docs/cases`.
