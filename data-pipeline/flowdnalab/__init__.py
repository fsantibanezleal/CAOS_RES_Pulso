"""flowdnalab — the FlowDNA offline+live engine (ADR-0057 product core).

FlowDNA builds catalogues of GeoTypes (recurring fluid-flow behaviours of fractured reservoirs)
from pressure-transient response shapes, with conformal assignment and RF/SHAP attribution of the
controlling fracture-network properties. The shape machinery is the `pygeotypes` library
(CAOS_GeoTypes); this package keeps only the DOMAIN: analytic PTA ensemble generation, GeoDFN
network generation + fracture descriptors, the two data contracts, the staged pipeline, the lane
gate, the manifest/trace, and the cases-by-category registry.
"""

__version__ = "0.07.000"  # display X.XX.XXX; PEP 440 in pyproject (0.7.0)
