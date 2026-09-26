"""Make the path-invoked build tooling (`pipeline`) importable from the tests, exactly as data-pipeline/run.py
does at bake time. The engine (`fracpta`) is an installed dependency."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "data-pipeline"))
