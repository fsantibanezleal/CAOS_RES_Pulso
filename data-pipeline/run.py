"""Bake the Pulso artifacts: `python data-pipeline/run.py [all|<case>|index] [--seed N] [--kinds ...]`.

A path-invoked entry point, deliberately NOT an installed distribution (a product declares no package of
its own). Running this file puts data-pipeline/ first on sys.path, so `pipeline` resolves without a shim.
The science is the `fracpta` package pinned in requirements.txt."""
from pipeline.pipeline import main

if __name__ == "__main__":
    main()
