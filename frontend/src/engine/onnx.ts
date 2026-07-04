// onnxruntime-web wrapper — the LIVE lane for the LEARNED tools. Loads the committed ONNX models
// (trained offline in .venv-pipeline, PINN-Lab pattern) + reference.json, and runs live inference on
// the user's tuned curve in the browser. WASM backend, no server.
import * as ort from 'onnxruntime-web';

export interface DeepReference {
  k: number;
  n_points: number;
  labels: number[];
  dtw_window: number;
  embedding: number[][];
  latent: number[][];
  medoids: number[][];
  calibration_scores: Record<string, number[]>;
  preprocessing: { derivative_order: number; norm: string; n_points: number };
  metrics: Record<string, number>;
}

let cnn: ort.InferenceSession | null = null;
let ae: ort.InferenceSession | null = null;
let embed: ort.InferenceSession | null = null;
let reference: DeepReference | null = null;
let loading: Promise<void> | null = null;

const base = import.meta.env.BASE_URL;

export function getReference(): DeepReference | null {
  return reference;
}

export async function loadDeep(): Promise<void> {
  if (loading) return loading;
  loading = (async () => {
    ort.env.wasm.numThreads = 1; // single-thread: no cross-origin-isolation needed on Pages.
    // No wasmPaths override: vite's onnxruntime-web ESM integration bundles + resolves the wasm.
    const url = (p: string) => `${base}models/${p}`;
    reference = await (await fetch(url('reference.json'))).json();
    const opt: ort.InferenceSession.SessionOptions = { executionProviders: ['wasm'] };
    [cnn, ae, embed] = await Promise.all([
      ort.InferenceSession.create(url('geotype_cnn.onnx'), opt),
      ort.InferenceSession.create(url('curve_ae.onnx'), opt),
      ort.InferenceSession.create(url('curve_embed.onnx'), opt),
    ]);
  })();
  return loading;
}

function tensor(curve: number[]): ort.Tensor {
  return new ort.Tensor('float32', Float32Array.from(curve), [1, 1, curve.length]);
}

// 1D-CNN GeoType classifier -> class probabilities (live).
export async function classifyCNN(curve: number[]): Promise<number[]> {
  if (!cnn) await loadDeep();
  const out = await cnn!.run({ curve: tensor(curve) });
  return Array.from(out[cnn!.outputNames[0]].data as Float32Array);
}

// Autoencoder -> { latent (for the latent-space point), reconError (anomaly/OOD score) } (live).
export async function autoencode(curve: number[]): Promise<{ latent: number[]; reconError: number }> {
  if (!ae) await loadDeep();
  const out = await ae!.run({ curve: tensor(curve) });
  const names = ae!.outputNames;
  return {
    latent: Array.from(out[names[0]].data as Float32Array),
    reconError: (out[names[1]].data as Float32Array)[0],
  };
}

// Contrastive embedding + nearest-neighbour retrieval against the baked training cloud (live).
export async function embedAndRetrieve(curve: number[]): Promise<{ embedding: number[]; nnLabel: number; nnIndex: number }> {
  if (!embed || !reference) await loadDeep();
  const out = await embed!.run({ curve: tensor(curve) });
  const e = Array.from(out[embed!.outputNames[0]].data as Float32Array);
  let best = -1;
  let bestD = Infinity;
  reference!.embedding.forEach((r, i) => {
    let d = 0;
    for (let j = 0; j < e.length; j++) d += (e[j] - r[j]) ** 2;
    if (d < bestD) {
      bestD = d;
      best = i;
    }
  });
  return { embedding: e, nnLabel: reference!.labels[best], nnIndex: best };
}
