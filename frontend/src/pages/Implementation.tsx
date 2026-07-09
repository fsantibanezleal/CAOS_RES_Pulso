// Implementation (ADR-0017 section 2): the system, tab by tab. >=8 tabs; a real architecture SVG
// (offline bake -> committed artifact -> CDN -> thin live) with a determinism banner; each tab states the
// EXACT stages + constants + the live/precompute boundary + the artifact/ONNX contract; a real Deployment
// tab. Theme-aware SVGs use currentColor + var(--bg-3). Transcribed from the repo's docs/architecture.
import { Callout, Equation, Figure, Refs, Tabs, useShellLang } from '@fasl-work/caos-app-shell';

const box = { fill: 'var(--bg-3, #eef1f5)', stroke: 'currentColor', strokeOpacity: 0.35 } as const;

function ArchSVG({ es }: { es: boolean }) {
  const offline = es ? ['Datos / sims', 'Pipeline .venv (CPU)', 'GPU .venv-train'] : ['Data / sims', 'Pipeline .venv (CPU)', 'GPU .venv-train'];
  const artifacts = es ? ['trace.json (pulso.study/v2)', 'manifest.json (gate)', 'modelo.onnx'] : ['trace.json (pulso.study/v2)', 'manifest.json (gate)', 'model.onnx'];
  return (
    <Figure caption={es
      ? 'Arquitectura: el procesamiento pesado corre OFFLINE (bake determinista + entrenamiento GPU) y se compromete como artefactos estaticos; GitHub Pages los sirve por CDN; el navegador corre EN VIVO solo las piezas ligeras (generacion + DTW + conformal + inferencia ONNX). No hay backend.'
      : 'Architecture: the heavy processing runs OFFLINE (deterministic bake + GPU training) and is committed as static artifacts; GitHub Pages serves them over a CDN; the browser runs LIVE only the light pieces (generation + DTW + conformal + ONNX inference). There is no backend.'}>
      <svg viewBox="0 0 720 210" width="100%" style={{ maxWidth: 720 }} role="img"
        aria-label={es ? 'Diagrama de arquitectura' : 'Architecture diagram'}>
        <text x={110} y={16} textAnchor="middle" fontSize={11} fill="currentColor" opacity={0.7}>OFFLINE</text>
        {offline.map((s, i) => (<g key={i}><rect x={20} y={28 + i * 42} width={180} height={32} rx={6} {...box} /><text x={110} y={48 + i * 42} textAnchor="middle" fontSize={11} fill="currentColor">{s}</text></g>))}
        <text x={360} y={16} textAnchor="middle" fontSize={11} fill="currentColor" opacity={0.7}>{es ? 'ARTEFACTOS COMPROMETIDOS' : 'COMMITTED ARTIFACTS'}</text>
        {artifacts.map((s, i) => (<g key={i}><rect x={270} y={28 + i * 42} width={180} height={32} rx={6} fill="var(--accent,#4f9cf9)" fillOpacity={0.12} stroke="currentColor" strokeOpacity={0.35} /><text x={360} y={48 + i * 42} textAnchor="middle" fontSize={10.5} fill="currentColor">{s}</text></g>))}
        <text x={610} y={16} textAnchor="middle" fontSize={11} fill="currentColor" opacity={0.7}>{es ? 'NAVEGADOR (CDN)' : 'BROWSER (CDN)'}</text>
        <rect x={520} y={44} width={180} height={100} rx={6} {...box} />
        <text x={610} y={70} textAnchor="middle" fontSize={11} fill="currentColor">{es ? 'React + onnxruntime-web' : 'React + onnxruntime-web'}</text>
        <text x={610} y={90} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.75}>{es ? 'genera + DTW + conformal' : 'generate + DTW + conformal'}</text>
        <text x={610} y={106} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.75}>{es ? 'inferencia ONNX en vivo' : 'live ONNX inference'}</text>
        <path d="M200 44 L270 44" stroke="currentColor" strokeOpacity={0.5} strokeWidth={1.5} />
        <path d="M450 60 L520 80" stroke="currentColor" strokeOpacity={0.5} strokeWidth={1.5} />
        <text x={360} y={196} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.7}>{es ? 'determinista: misma entrada -> mismo artefacto (sin Date.now / random en el bake)' : 'deterministic: same input -> same artifact (no Date.now / random in the bake)'}</text>
      </svg>
    </Figure>
  );
}

function Contract3SVG({ es }: { es: boolean }) {
  const fields = ['members', 'envelopes', 'dtw', 'embedding', 'method_comparison', 'representations', 'attribution_plus'];
  return (
    <Figure caption={es
      ? 'El artefacto de estudio pulso.study/v2 (CONTRACT-3): compromete el ENSAMBLE completo (curvas miembro decimadas, envolventes p10/p50/p90, matriz DTW cuantizada, embedding MDS) mas los bloques de metodos, de modo que la web renderiza sin recomputar.'
      : 'The pulso.study/v2 study artifact (CONTRACT-3): commits the WHOLE ensemble (decimated member curves, p10/p50/p90 envelopes, quantised DTW matrix, MDS embedding) plus the method blocks, so the web renders without recomputation.'}>
      <svg viewBox="0 0 560 150" width="100%" style={{ maxWidth: 560 }} role="img" aria-label="CONTRACT-3">
        <rect x={10} y={10} width={540} height={130} rx={8} {...box} />
        <text x={24} y={32} fontSize={12} fill="currentColor">pulso.study/v2</text>
        {fields.map((f, i) => (<g key={f}><rect x={24 + (i % 4) * 130} y={48 + Math.floor(i / 4) * 40} width={120} height={30} rx={6} fill="var(--accent,#4f9cf9)" fillOpacity={0.1} stroke="currentColor" strokeOpacity={0.3} /><text x={84 + (i % 4) * 130} y={67 + Math.floor(i / 4) * 40} textAnchor="middle" fontSize={10.5} fill="currentColor">{f}</text></g>))}
      </svg>
    </Figure>
  );
}

function Architecture({ es }: { es: boolean }) {
  return (
    <div>
      <Callout variant="strong" title={es ? 'Offline-pesado, backend-opcional, replay determinista' : 'Offline-heavy, backend-optional, deterministic replay'}>
        {es ? 'Pulso sigue el arquetipo de producto-datos (ADR-0057): el trabajo pesado se hornea offline y se compromete; la web es estatica y determinista. La misma entrada produce el mismo artefacto byte-a-byte (nada de Date.now ni aleatoriedad sin semilla en el bake).' : 'Pulso follows the data-product archetype (ADR-0057): the heavy work is baked offline and committed; the web is static and deterministic. The same input produces the same artifact byte-for-byte (no Date.now or unseeded randomness in the bake).'}
      </Callout>
      <p>{es
        ? 'Hay tres carriles. OFFLINE (el pipeline por lotes en .venv-pipeline y el entrenamiento GPU en .venv-train) hace todo el procesamiento pesado: la matriz DTW NxN, PAM, el entrenamiento de los modelos aprendidos. El resultado se comprime a artefactos compactos comprometidos en el repo. LIVE (el navegador) reejecuta solo las piezas ligeras. REPLAY reproduce lo horneado. La web no tiene servidor.'
        : 'There are three lanes. OFFLINE (the batch pipeline in .venv-pipeline and the GPU training in .venv-train) does all the heavy processing: the NxN DTW matrix, PAM, the training of the learned models. The result is compressed to compact artifacts committed to the repo. LIVE (the browser) re-runs only the light pieces. REPLAY reproduces the baked output. The web has no server.'}</p>
      <ArchSVG es={es} />
      <p>{es
        ? 'El limite live/precompute es explicito: un caso de estudio se clasifica en vivo (el navegador genera una curva y la asigna con pygeotypes en numpy/TS contra el catalogo horneado); la matriz DTW offline y PAM nunca corren en vivo. Cada artefacto lleva un veredicto de gate que registra su carril medido.'
        : 'The live/precompute boundary is explicit: a study case is classified live (the browser generates a curve and assigns it with pygeotypes in numpy/TS against the baked catalogue); the offline DTW matrix and PAM never run live. Each artifact carries a gate verdict recording its measured lane.'}</p>
      <Refs ids={['khait2018']} label="Refs" />
    </div>
  );
}

function DataContracts({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Dos contratos de datos congelan la frontera entre el pipeline y la web. CONTRACT-1 es el manifiesto por caso: el veredicto de carril/gate, el tamano en bytes del artefacto, las banderas de preproceso y las metricas. CONTRACT-2/3 es la traza: la forma que la web replica.'
        : 'Two data contracts freeze the boundary between the pipeline and the web. CONTRACT-1 is the per-case manifest: the lane/gate verdict, the artifact byte size, the preprocessing flags and the metrics. CONTRACT-2/3 is the trace: the shape the web replays.'}</p>
      <p>{es
        ? 'CONTRACT-3 (pulso.study/v2) es el artefacto de estudio de ensamble completo. Compromete cada curva miembro decimada (min/max por pixel, 64 columnas), las envolventes p10/p50/p90 por cluster, la matriz DTW ordenada por cluster y cuantizada a uint8 (tope 512), el embedding MDS, y los bloques method_comparison, representations y attribution_plus de la escalera de metodos.'
        : 'CONTRACT-3 (pulso.study/v2) is the full-ensemble study artifact. It commits every decimated member curve (min/max-per-pixel, 64 columns), the per-cluster p10/p50/p90 envelopes, the cluster-ordered DTW matrix quantised to uint8 (capped at 512), the MDS embedding, and the method_comparison, representations and attribution_plus blocks from the method ladder.'}</p>
      <Contract3SVG es={es} />
      <Equation tex="q_{ij} = \mathrm{round}\!\left(\frac{D_{ij}}{d_{\max}}\cdot 255\right), \qquad d_{\max} = \max_{ij} D_{ij}"
        caption={es ? 'Ec. La cuantizacion uint8 de la matriz DTW para transporte compacto; el navegador reconstruye la distancia como q/255 * dmax.' : 'Eq. The uint8 quantisation of the DTW matrix for compact transport; the browser reconstructs the distance as q/255 * dmax.'} />
      <p>{es
        ? 'El contrato se hace cumplir en tiempo de BUILD: la forma TypeScript en contract.types.ts refleja los esquemas Python; una divergencia hace fallar tsc, de modo que la web no puede publicarse leyendo una forma que el pipeline no produce.'
        : 'The contract is enforced at BUILD time: the TypeScript shape in contract.types.ts mirrors the Python schemas; a drift fails tsc, so the web cannot ship reading a shape the pipeline does not produce.'}</p>
      <Callout variant="honest" title={es ? 'Presupuesto de bytes' : 'Byte budget'}>
        {es ? 'Los ensambles grandes (benchmark de corpus completo, miles de curvas) exceden el presupuesto si se comprometen enteros; se compromete un submuestreo estratificado de miembros (los medoides siempre incluidos) y de la matriz DTW, y stats reporta el N completo vs el comprometido. Nada se oculta: el tamano real esta en el manifiesto.' : 'Large ensembles (the full-corpus benchmark, thousands of curves) exceed the budget if committed whole; a stratified subsample of members (medoids always included) and of the DTW matrix is committed, and stats reports the full N vs the committed count. Nothing is hidden: the real size is in the manifest.'}
      </Callout>
    </div>
  );
}

function Pipeline({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'El pipeline por lotes es una secuencia de etapas nombradas, cada una con una responsabilidad unica y una salida tipada. Un caso fluye por ellas de forma determinista (split semilla-fija, sin fugas por construccion: el catalogo nunca ve las curvas de calibracion ni de prueba).'
        : 'The batch pipeline is a sequence of named stages, each with a single responsibility and a typed output. A case flows through them deterministically (seeded split, leakage-safe by construction: the catalogue never sees the calibration or test curves).'}</p>
      <ol>
        <li>{es ? 'feature_extraction: cargar/generar el ensamble, preprocesar a la derivada de Bourdet z-score en la grilla log-tiempo.' : 'feature_extraction: load/generate the ensemble, preprocess to the z-scored Bourdet derivative on the log-time grid.'}</li>
        <li>{es ? 'train: matriz DTW -> seleccion de K por silueta -> PAM k-medoids -> calibracion conformal condicional por clase en el slice disjunto -> atribucion RF+SHAP con gate.' : 'train: DTW matrix -> silhouette K-selection -> PAM k-medoids -> class-conditional conformal calibration on the disjoint slice -> gated RF+SHAP attribution.'}</li>
        <li>{es ? 'infer: asignar conformemente el slice de prueba held-out (lo mismo que hara el navegador con la curva del usuario).' : 'infer: conformally assign the held-out test slice (the same thing the browser will do with the user\'s curve).'}</li>
        <li>{es ? 'export: escribir la traza compacta (CONTRACT-3) + el manifiesto con el veredicto de gate medido, los bytes, las banderas y las metricas.' : 'export: write the compact trace (CONTRACT-3) + the manifest with the measured gate verdict, bytes, flags and metrics.'}</li>
      </ol>
      <Equation tex="n = n_{\text{train}} + n_{\text{cal}} + n_{\text{test}}, \qquad n_{\text{cal}} = \lceil f_{\text{cal}}\,n\rceil,\; n_{\text{test}} = \lceil f_{\text{test}}\,n\rceil"
        caption={es ? 'Ec. El split semilla-fijo train/calibracion/prueba: una permutacion determinista particiona el ensamble; el catalogo se entrena solo sobre train, la calibracion conformal solo sobre cal.' : 'Eq. The seeded train/calibration/test split: a deterministic permutation partitions the ensemble; the catalogue trains only on train, the conformal calibration only on cal.'} />
      <Callout variant="honest" title={es ? 'Sin fugas por construccion' : 'Leakage-safe by construction'}>
        {es ? 'Como el split es una permutacion semilla-fija y el catalogo nunca ve cal ni test, la cobertura conformal reportada es honesta; el protocolo se dibuja explicitamente (con el anti-patron tachado) en la pagina de Experimentos.' : 'Because the split is a seeded permutation and the catalogue never sees cal or test, the reported conformal coverage is honest; the protocol is drawn explicitly (with the anti-pattern struck out) on the Experiments page.'}
      </Callout>
    </div>
  );
}

function TwoVenvs({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'El procesamiento se reparte en dos entornos aislados, nunca globales. .venv-pipeline es CPU y determinista: corre el bake por lotes, DTW (backend C de dtaidistance via pygeotypes), PAM, conformal, atribucion, y la simulacion open-DARTS. .venv-train es la GPU (torch 2.6 + cu124): entrena la escalera aprendida y exporta a ONNX. Estan separados a proposito para que el bake determinista no dependa de la GPU.'
        : 'The processing is split across two isolated (never global) environments. .venv-pipeline is CPU and deterministic: it runs the batch bake, DTW (dtaidistance C backend via pygeotypes), PAM, conformal, attribution, and the open-DARTS simulation. .venv-train is the GPU (torch 2.6 + cu124): it trains the learned ladder and exports to ONNX. They are separated on purpose so the deterministic bake does not depend on the GPU.'}</p>
      <p>{es
        ? 'Los motores elegidos por la investigacion se usan de verdad y se fijan en requirements: pygeotypes (Apache-2.0) para el nucleo de forma; dtaidistance para DTW rapido; tslearn/hdbscan/umap-learn/pycatch22 para las alternativas y representaciones; scikit-learn + shap para atribucion; torch + onnx + onnxruntime para el nivel aprendido; open-DARTS (GPL-3, solo offline) para la fisica. Ningun sustituto artesanal de un motor SOTA.'
        : 'The research-chosen engines are used for real and pinned in requirements: pygeotypes (Apache-2.0) for the shape core; dtaidistance for fast DTW; tslearn/hdbscan/umap-learn/pycatch22 for the alternatives and representations; scikit-learn + shap for attribution; torch + onnx + onnxruntime for the learned tier; open-DARTS (GPL-3, offline only) for the physics. No hand-rolled substitute for a SOTA engine.'}</p>
      <ul>
        <li><b>.venv-pipeline</b> {es ? '(CPU): bake determinista + open-DARTS' : '(CPU): deterministic bake + open-DARTS'}</li>
        <li><b>.venv-train</b> {es ? '(cu124): InceptionTime / PatchTST / conv-AE / TS2Vec -> ONNX' : '(cu124): InceptionTime / PatchTST / conv-AE / TS2Vec -> ONNX'}</li>
      </ul>
      <Callout variant="honest" title={es ? 'Aislado, nunca global' : 'Isolated, never global'}>
        {es ? 'pycatch22 compila una extension C (sin wheel de Windows); scripts/setup la construye best-effort con el toolchain MSVC y degrada a un skip registrado si falta, sin romper la instalacion masiva.' : 'pycatch22 compiles a C extension (no Windows wheel); scripts/setup builds it best-effort with the MSVC toolchain and degrades to a recorded skip if absent, without breaking the bulk install.'}
      </Callout>
      <Refs ids={['lubba2019']} label="Refs" />
    </div>
  );
}

function DtwBackend({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'La distancia DTW es el objeto mas costoso del bake. El backend offline es la implementacion en C de dtaidistance (via pygeotypes), que calcula la matriz NxN con la banda de Sakoe-Chiba en tiempo razonable para cientos de curvas. El navegador reimplementa la MISMA recurrencia en TypeScript para la asignacion en vivo de una sola curva contra los medoides.'
        : 'The DTW distance is the most expensive object in the bake. The offline backend is the C implementation in dtaidistance (via pygeotypes), which computes the NxN matrix with the Sakoe-Chiba band in reasonable time for hundreds of curves. The browser reimplements the SAME recurrence in TypeScript for the live assignment of a single curve against the medoids.'}</p>
      <Equation tex="\text{cost} \sim \mathcal{O}(n^2 \cdot L \cdot w), \qquad n = \#\text{curvas},\; L = \#\text{puntos},\; w = \text{banda}"
        caption={es ? 'Ec. El costo de la matriz DTW crece con el cuadrado del numero de curvas; por eso PAM escala sus reinicios hacia abajo para matrices grandes y el benchmark reutiliza la matriz precomputada del corpus.' : 'Eq. The DTW matrix cost grows with the square of the number of curves; hence PAM scales its restarts down for large matrices and the benchmark reuses the corpus precomputed matrix.'} />
      <p>{es
        ? 'Para el benchmark de corpus completo (cada dataset ~4768 curvas) recomputar NxN seria horas; en su lugar se reutiliza la matriz DTW precomputada de 4768x4768 del corpus 4TU (~90 MB, solo en el vault) y se corta al slice de entrenamiento. El resultado es la contraparte honesta de corpus completo de los casos App de submuestreo.'
        : 'For the full-corpus benchmark (each dataset ~4768 curves) recomputing NxN would be hours; instead the corpus 4TU precomputed 4768x4768 DTW matrix (~90 MB, vault-only) is reused and sliced to the training split. The result is the honest full-corpus counterpart of the subsampled App cases.'}</p>
      <Refs ids={['sakoe1978']} label="Refs" />
    </div>
  );
}

function OnnxExport({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Los cuatro modelos aprendidos se entrenan en la GPU y se exportan a ONNX (opset 18) para correr en el navegador con onnxruntime-web (backend WASM, un hilo, sin necesidad de aislamiento cross-origin en Pages). Cada exportacion se re-guarda como un archivo unico auto-contenido (los pesos embebidos), porque onnxruntime-web no puede resolver el sidecar .onnx.data desde una URL.'
        : 'The four learned models are trained on the GPU and exported to ONNX (opset 18) to run in the browser with onnxruntime-web (WASM backend, single-thread, no cross-origin isolation needed on Pages). Each export is re-saved as a single self-contained file (weights embedded), because onnxruntime-web cannot resolve the .onnx.data sidecar from a URL.'}</p>
      <Equation tex="\varepsilon = \max_k \big|\, y^{\text{torch}}_k - y^{\text{onnx}}_k \,\big| < 10^{-4}"
        caption={es ? 'Ec. El gate de paridad: cada exportacion verifica que la salida ONNX coincide con la de torch dentro de 1e-4 sobre una muestra ANTES de comprometer el modelo. Un modelo que no reproduce nunca se publica.' : 'Eq. The parity gate: every export asserts the ONNX output matches torch within 1e-4 on a sample BEFORE the model is committed. A model that does not round-trip is never shipped.'} />
      <p>{es
        ? 'Junto a los .onnx se compromete reference.json: la nube de embeddings de entrenamiento (para la recuperacion), los latentes, los medoides, la calibracion conformal, el spec de preproceso y las metricas held-out honestas. El navegador carga todo una vez y corre los cuatro modelos en vivo.'
        : 'Alongside the .onnx files, reference.json is committed: the training embedding cloud (for retrieval), the latents, the medoids, the conformal calibration, the preprocessing spec, and the honest held-out metrics. The browser loads it once and runs all four models live.'}</p>
      <Callout variant="honest" title={es ? 'Paridad antes de comprometer' : 'Parity before commit'}>
        {es ? 'La verificacion de paridad no es opcional ni un test aparte: es el gate en la propia funcion de exportacion, de modo que un modelo divergente falla el bake en vez de llegar a produccion.' : 'The parity check is not optional or a separate test: it is the gate inside the export function itself, so a divergent model fails the bake rather than reaching production.'}
      </Callout>
      <Refs ids={['ismailfawaz2020', 'nie2023', 'yue2022']} label="Refs" />
    </div>
  );
}

function LaneGate({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Cada caso lleva un veredicto de gate que clasifica su carril de forma MEDIDA, no declarada. El gate mide el tiempo de la primitiva en vivo (el navegador genera una curva y la clasifica conformemente) y el tamano del artefacto, y decide si el caso es apto para el carril en vivo o solo para replay.'
        : 'Each case carries a gate verdict that classifies its lane in a MEASURED way, not a declared one. The gate times the live primitive (the browser generates a curve and classifies it conformally) and the artifact size, and decides whether the case is fit for the live lane or replay-only.'}</p>
      <p>{es
        ? 'Un estudio GeoType es carril en vivo: la primitiva (generar + asignar con pygeotypes en numpy/scipy) es barata y pura. Una simulacion open-DARTS o una red DFN es nativa (vtk/gmsh/C++) y por tanto solo-replay: la web reproduce el artefacto, nunca simula. El manifiesto registra el veredicto con sus razones.'
        : 'A GeoType study is a live lane: the primitive (generate + assign with pygeotypes in numpy/scipy) is cheap and pure. An open-DARTS simulation or a DFN network is native (vtk/gmsh/C++) and therefore replay-only: the web replays the artifact, never simulates. The manifest records the verdict with its reasons.'}</p>
      <ul>
        <li>{es ? 'live: numpy/scipy/pygeotypes puros, artefacto pequeno, primitiva rapida.' : 'live: pure numpy/scipy/pygeotypes, small artifact, fast primitive.'}</li>
        <li>{es ? 'precompute/replay: motor nativo (open-DARTS, GeoDFN) o artefacto grande.' : 'precompute/replay: native engine (open-DARTS, GeoDFN) or large artifact.'}</li>
      </ul>
      <Callout variant="honest" title={es ? 'Medido, no declarado' : 'Measured, not declared'}>
        {es ? 'El run_ms del gate es una MEDICION de la primitiva en vivo, no del bake offline; asi la etiqueta de carril refleja lo que el navegador realmente puede hacer, no una aspiracion.' : "The gate's run_ms is a MEASUREMENT of the live primitive, not the offline bake; so the lane label reflects what the browser can actually do, not an aspiration."}
      </Callout>
    </div>
  );
}

function Deployment({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'El despliegue es GitHub Pages con un dominio propio (pulso.fasl-work.com, HTTPS) via GitHub Actions. En cada merge a main, la Action corre el prebuild (copy-data.mjs copia data/derived + models/deep a public/, e inlinea las fuentes del pipeline), construye la SPA con Vite y publica dist/. El enrutado es HashRouter para que las rutas profundas funcionen en el hosting estatico.'
        : 'Deployment is GitHub Pages with a custom domain (pulso.fasl-work.com, HTTPS) via GitHub Actions. On each merge to main, the Action runs the prebuild (copy-data.mjs copies data/derived + models/deep into public/, and inlines the pipeline sources), builds the SPA with Vite, and publishes dist/. Routing is HashRouter so deep routes work on static hosting.'}</p>
      <p>{es
        ? 'Los artefactos de datos y los .onnx viven en el repo (data/derived, models/deep) y se copian a public en el prebuild, de modo que el sitio estatico los sirve por CDN sin backend. El versionado es X.XX.XXX con un tag por release; el pie de pagina lee la version desde package.json, una sola fuente de verdad.'
        : 'The data artifacts and the .onnx files live in the repo (data/derived, models/deep) and are copied into public at prebuild, so the static site serves them over a CDN with no backend. Versioning is X.XX.XXX with a tag per release; the footer reads the version from package.json, a single source of truth.'}</p>
      <Callout variant="note" title={es ? 'Sin servidor' : 'No server'}>
        {es ? 'Todo el producto es estatico: no hay backend que mantener, escalar ni asegurar. El costo de computo pesado se paga una vez, offline, y se comprime a artefactos que el CDN sirve.' : 'The whole product is static: there is no backend to maintain, scale, or secure. The heavy compute cost is paid once, offline, and compressed to artifacts the CDN serves.'}
      </Callout>
    </div>
  );
}

export function Implementation() {
  const es = useShellLang() === 'es';
  const tabs = [
    { id: 'arch', label: es ? '1. Arquitectura' : '1. Architecture', content: <Architecture es={es} /> },
    { id: 'contracts', label: es ? '2. Contratos de datos' : '2. Data contracts', content: <DataContracts es={es} /> },
    { id: 'pipeline', label: es ? '3. Pipeline por etapas' : '3. Staged pipeline', content: <Pipeline es={es} /> },
    { id: 'venvs', label: es ? '4. Dos entornos' : '4. Two environments', content: <TwoVenvs es={es} /> },
    { id: 'dtw', label: es ? '5. Backend DTW' : '5. DTW backend', content: <DtwBackend es={es} /> },
    { id: 'onnx', label: es ? '6. Export ONNX + paridad' : '6. ONNX export + parity', content: <OnnxExport es={es} /> },
    { id: 'gate', label: es ? '7. Carril / gate' : '7. Lane / gate', content: <LaneGate es={es} /> },
    { id: 'deploy', label: es ? '8. Despliegue' : '8. Deployment', content: <Deployment es={es} /> },
  ];
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Implementacion' : 'Implementation'}</h1>
        <p className="lede">
          {es
            ? 'El sistema, modulo por modulo: la arquitectura offline-pesada de replay determinista, los dos contratos de datos, el pipeline por etapas, los dos entornos aislados (CPU + GPU), el backend DTW, la exportacion ONNX con gate de paridad, el gate de carril y el despliegue estatico. Sin backend.'
            : 'The system, module by module: the offline-heavy deterministic-replay architecture, the two data contracts, the staged pipeline, the two isolated environments (CPU + GPU), the DTW backend, the ONNX export with a parity gate, the lane gate, and the static deployment. No backend.'}
        </p>
      </div>
      <Tabs tabs={tabs} ariaLabel={es ? 'Modulos de implementacion' : 'Implementation modules'} />
    </div>
  );
}
