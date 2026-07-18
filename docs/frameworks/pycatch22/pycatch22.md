# Framework card: `pycatch22`

## What & why

`pycatch22` (GPL-3, [DynamicsAndNeuralSystems/pycatch22](https://github.com/DynamicsAndNeuralSystems/pycatch22))
is the Python binding to the C implementation of **catch22** (CAnonical Time-series CHaracteristics; Lubba
et al., *catch22: canonical time-series characteristics*, Data Mining and Knowledge Discovery 33, 2019).
catch22 is a curated set of 22 features distilled from the ~7700-feature hctsa library by filtering for
low redundancy and high classification performance across a broad benchmark, so a 22-number signature
describes a time series in interpretable, well-studied terms (distribution shape, autocorrelation
structure, entropy, trend, outliers, ...).

Pulso uses it in the P2b representations group to describe each flow-behaviour cluster in feature terms:
the per-cluster mean of the 22 features, so the Representations tab can answer "what actually
distinguishes these GeoTypes?" with named, sourced features rather than only a geometric layout. It was
chosen (over reimplementing the features) precisely because the deep-work rule forbids a hand-rolled
substitute for a SOTA engine: catch22's exact definitions live in the C library.

## Install (exact, verified)

Pinned in `data-pipeline/requirements.txt`:

```
pycatch22>=0.4.0     # catch22 canonical TS features (Lubba 2019); offline, consume-not-vendor
```

It builds a C extension from source (no PyPI wheel on Windows). On this machine the build needs the MSVC
toolchain visible to setuptools; the reproducible recipe (Visual Studio 2022 Community, C++ workload):

```bat
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
set DISTUTILS_USE_SDK=1
set MSSdk=1
python -m pip install --no-build-isolation "pycatch22>=0.4.0"
```

On Linux/WSL a normal `pip install pycatch22` builds with gcc. offline-only (features are baked into the
`representations.catch22` block); never in the live lane or Pyodide. If the wheel cannot be built the
block degrades to a recorded `skipped`, never a crash.

## Usage

```python
import pycatch22
r = pycatch22.catch22_all(series.tolist())   # {'names': [...22], 'values': [...22]}
```

## Applying it here

Called from `flowdnalab/methods/representations.py::compute_representations` per committed member curve,
then aggregated to a per-cluster mean +/- std table (`representations.catch22.per_cluster`). The
Representations tab ranks the features by between-cluster spread and shows the most discriminating ones.

## Caveats / license

- **GPL-3.** Used the same way as the other GPL engines in the offline lane (open-DARTS, dtaidistance
  backend): consumed as an offline analysis tool. Its OUTPUT (feature numbers) is committed data, not a
  derivative work of the library, and the GPL code is never redistributed inside the web bundle. Do not
  vendor its source into Pulso.
- Some features are undefined for degenerate (constant) series and return NaN; the aggregation uses
  `nanmean`/`nanstd` so a few NaNs do not poison the cluster table.

## References

- C. H. Lubba, S. S. Sethi, P. Knaute, S. R. Schultz, B. D. Fulcher, N. S. Jones. *catch22: canonical
  time-series characteristics.* Data Mining and Knowledge Discovery 33, 1821-1852, 2019.
