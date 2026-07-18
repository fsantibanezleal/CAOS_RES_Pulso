# onnxruntime-web — live learned inference in the browser

**What / why.** The learned tier (1D-CNN, autoencoder, contrastive encoder) is trained offline with
PyTorch and exported to ONNX; **onnxruntime-web** runs those ONNX models **live in the browser**
(WebAssembly, no server) as the user tunes the curve. This is what makes FlowDNA a web that tests
the precomputed hard tools, not just displays them.

**Install.** `npm install onnxruntime-web` (frontend). The WASM binary is bundled + path-resolved by
vite's ESM integration — do not override `ort.env.wasm.wasmPaths` (that breaks vite's hashed-asset
resolution and 404s a variant). Single-thread (`ort.env.wasm.numThreads = 1`) avoids the
cross-origin-isolation (COOP/COEP) requirement, so it runs on plain GitHub Pages with no headers.

**How FlowDNA uses it.** `frontend/src/engine/onnx.ts`:
- `loadDeep()` fetches `reference.json` + creates three `InferenceSession`s (`geotype_cnn.onnx`,
  `curve_ae.onnx`, `curve_embed.onnx`) with the `wasm` execution provider.
- `classifyCNN(curve)` → class probabilities; `autoencode(curve)` → `{latent, reconError}`;
  `embedAndRetrieve(curve)` → embedding + nearest-neighbour label against the baked training cloud.
- The Live lab (`pages/LiveLab.tsx`) preprocesses the tuned curve exactly as the models expect
  (resample → Bourdet derivative → z-score, via the TS engine) then runs inference on every slider
  change.

**Reference artifact.** `models/deep/reference.json` (copied to `public/models` by `copy-data.mjs`)
carries the medoids, class-conditional calibration scores, and the embedding/latent point clouds, so
the DTW/conformal TS tools and the learned-model viz all share one coherent baked catalogue.

**Gotchas.**
- ONNX must be **self-contained** (weights embedded), not external-data — the browser can't fetch a
  `.onnx.data` sidecar by relative URL. The training export enforces this.
- The committed model + reference + WASM are all served from the site's own origin (no CDN), so the
  live lane works offline and under a strict CSP.
- The 26 MB WASM (gzip ~6 MB) is fetched **on demand** the first time a learned tab is opened, not on
  page load — the classical/SOTA/novel tabs need no WASM.
