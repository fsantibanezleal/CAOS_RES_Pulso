# dtaidistance — C-accelerated DTW matrices (offline backend)

**What / why.** [dtaidistance](https://github.com/wannesm/dtaidistance) (Apache-2.0, KU Leuven) is
the offline accelerator behind `pygeotypes.distance.dtw_matrix(backend="auto")`: full pairwise DTW
matrices over training ensembles run in its OpenMP C core instead of the pure-numpy DP (orders of
magnitude faster at n≥100 curves). The numpy DP remains the reference implementation and the ONLY
one the live lane uses (dtaidistance has no Pyodide wheel).

**Install.** `pip install dtaidistance==2.4.0` (binary wheels for Windows/Linux, Python 3.12).
Pinned in `data-pipeline/requirements.txt`; pulled into `.venv-pipeline` via
`pip install -e ../CAOS_GeoTypes[fast]`.

**Parity (the reason we can swap backends).** Same Sakoe-Chiba band semantics and the same
sqrt-of-accumulated-squared-cost convention; `CAOS_GeoTypes/tests/test_distance.py::
test_matrix_dtaidistance_parity_if_available` asserts numerical parity (rtol 1e-9) on every CI run.
The manifest records which backend baked each case (`engine.dtw_backend`).

**Gotchas.**
- dtaidistance's `window` parameter counts the full band differently than the half-width our DP
  uses: the adapter passes `window + 1` to keep parity (verified by the test above).
- `distance_matrix_fast` returns `inf` on the untouched triangle in some versions; the adapter
  symmetrizes (`max(D, D.T)`) after zeroing infs.
