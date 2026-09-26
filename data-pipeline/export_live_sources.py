"""Write frontend/public/pyodide/sources.json: the pure-Python subset of the installed `fracpta` the optional
Pyodide lane would import (`fracpta.live` and `fracpta.model`). Run after a bake or a pin change and commit the
result; frontend/copy-data.mjs only copies it. A real lane installs fracpta and pygeotypes through micropip;
this file exists so the lane's worker can be developed against the exact engine version the product pins."""
import json
import pathlib

import fracpta

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "pyodide" / "sources.json"
KEEP = ("__init__.py", "live.py", "model/__init__.py", "model/pta.py", "core/__init__.py", "core/rng.py")


def main() -> None:
    pkg = pathlib.Path(fracpta.__file__).parent
    sources = {f"fracpta/{rel}": (pkg / rel).read_text(encoding="utf-8") for rel in KEEP}
    sources["fracpta/VERSION"] = fracpta.__version__
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sources), encoding="utf-8")
    print(f"wrote {len(sources)} entries for fracpta {fracpta.__version__} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
