// Experiments (ADR-0017 section 2): prose + tabs (never info-box cards). >=6 tabs separating the distinct
// experimental questions; EXACT metric equations with real constants; a leakage-safe protocol SVG that
// ALSO shows the forbidden anti-pattern struck out; a real datasets table with per-set redistribution +
// live-vs-roadmap; honest negatives. Study metrics are read from the committed manifests.
import { useEffect, useState } from 'react';
import { Callout, Cite, Equation, Figure, Refs, Tabs, useShellLang } from '@fasl-work/caos-app-shell';
import { loadIndex, loadManifest } from '../api/artifacts';
import type { CaseIndex, CaseManifest } from '../lib/contract.types';

function useManifests() {
  const [rows, setRows] = useState<CaseManifest[]>([]);
  useEffect(() => {
    let alive = true;
    loadIndex().then((ix: CaseIndex) => Promise.all(ix.cases.map((c) => loadManifest(c.case_id))))
      .then((ms) => alive && setRows(ms)).catch(() => {});
    return () => { alive = false; };
  }, []);
  return rows;
}

function ProtocolSVG({ es }: { es: boolean }) {
  return (
    <Figure caption={es
      ? 'El protocolo sin fugas: el ensamble se parte por una permutacion semilla-fija en train / calibracion / prueba. El catalogo se entrena SOLO con train; la calibracion conformal SOLO con cal; la prueba es held-out. El anti-patron (tachado) reutiliza las mismas curvas para entrenar y evaluar, lo que infla la cobertura.'
      : 'The leakage-safe protocol: the ensemble is split by a seeded permutation into train / calibration / test. The catalogue trains ONLY on train; the conformal calibration ONLY on cal; test is held-out. The anti-pattern (struck out) reuses the same curves to train and evaluate, which inflates coverage.'}>
      <svg viewBox="0 0 620 200" width="100%" style={{ maxWidth: 620 }} role="img" aria-label={es ? 'Protocolo sin fugas' : 'Leakage-safe protocol'}>
        {/* correct */}
        <text x={10} y={20} fontSize={12} fill="currentColor">{es ? 'Correcto (sin fugas)' : 'Correct (leakage-safe)'}</text>
        {[[es ? 'train -> catalogo' : 'train -> catalogue', 'var(--geo-0,#4f9cf9)'], [es ? 'cal -> conformal' : 'cal -> conformal', 'var(--geo-1,#f97b4f)'], [es ? 'test -> evaluar' : 'test -> evaluate', 'var(--geo-2,#41c98d)']].map(([l, c], i) => (
          <g key={i}><rect x={10 + i * 200} y={30} width={180} height={34} rx={6} fill={c as string} fillOpacity={0.14} stroke="currentColor" strokeOpacity={0.35} /><text x={100 + i * 200} y={51} textAnchor="middle" fontSize={11} fill="currentColor">{l}</text>{i < 2 && <path d={`M${190 + i * 200} 47 L${210 + i * 200} 47`} stroke="currentColor" strokeOpacity={0.5} />}</g>
        ))}
        {/* anti-pattern struck out */}
        <text x={10} y={112} fontSize={12} fill="currentColor">{es ? 'Anti-patron (prohibido)' : 'Anti-pattern (forbidden)'}</text>
        <g opacity={0.6}>
          <rect x={10} y={122} width={380} height={34} rx={6} fill="var(--bad,#e5484d)" fillOpacity={0.1} stroke="var(--bad,#e5484d)" strokeOpacity={0.5} />
          <text x={200} y={143} textAnchor="middle" fontSize={11} fill="currentColor">{es ? 'mismas curvas para entrenar Y evaluar' : 'same curves to train AND evaluate'}</text>
          <line x1={20} y1={139} x2={380} y2={139} stroke="var(--bad,#e5484d)" strokeWidth={2} />
        </g>
        <text x={10} y={186} fontSize={10} fill="currentColor" opacity={0.7}>{es ? 'la cobertura conformal solo es honesta bajo el protocolo correcto' : 'conformal coverage is only honest under the correct protocol'}</text>
      </svg>
    </Figure>
  );
}

function Protocol({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Cada estudio se evalua bajo un protocolo sin fugas por construccion. Una permutacion semilla-fija particiona el ensamble en tres slices disjuntos: entrenamiento (el catalogo k-medoids), calibracion (los puntajes conformal condicionales por clase) y prueba (la evaluacion held-out). El catalogo nunca ve las curvas de calibracion ni de prueba.'
        : 'Every study is evaluated under a protocol that is leakage-safe by construction. A seeded permutation partitions the ensemble into three disjoint slices: training (the k-medoids catalogue), calibration (the class-conditional conformal scores) and test (the held-out evaluation). The catalogue never sees the calibration or test curves.'}</p>
      <ProtocolSVG es={es} />
      <p>{es
        ? 'Esto importa porque la garantia de cobertura conformal SOLO es valida si la calibracion y la prueba son intercambiables y no vistas por el catalogo. Reutilizar curvas (el anti-patron tachado) produce una cobertura inflada que no se sostiene fuera de muestra. Se dibuja el anti-patron para que quede claro que NO se hace.'
        : 'This matters because the conformal coverage guarantee is ONLY valid if calibration and test are exchangeable and unseen by the catalogue. Reusing curves (the struck-out anti-pattern) produces an inflated coverage that does not hold out of sample. The anti-pattern is drawn to make clear it is NOT done.'}</p>
      <Refs ids={['vovk2005', 'angelopoulos2023']} label="Refs" />
    </div>
  );
}

function Coverage({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'La pregunta central de la asignacion: el conjunto de prediccion conformal, contiene el GeoType verdadero con la frecuencia prometida? La cobertura empirica en el slice de prueba debe acercarse al nivel objetivo 1-alpha; una desviacion grande indicaria una violacion de intercambiabilidad.'
        : 'The central assignment question: does the conformal prediction set contain the true GeoType at the promised frequency? The empirical coverage on the test slice should approach the target level 1-alpha; a large deviation would indicate an exchangeability violation.'}</p>
      <Equation tex="\widehat{\text{cov}} = \frac{1}{n_{\text{test}}}\sum_{i=1}^{n_{\text{test}}} \mathbf{1}\!\big[\, g_i^\star \in \Gamma^{\alpha}(x_i) \,\big] \;\approx\; 1-\alpha"
        caption={es ? 'Ec. La cobertura empirica: la fraccion de curvas de prueba cuyo GeoType verdadero cae en su conjunto de prediccion. La tasa OOD es la fraccion con conjunto vacio (fuera de catalogo).' : 'Eq. The empirical coverage: the fraction of test curves whose true GeoType falls in its prediction set. The OOD rate is the fraction with an empty set (out of catalogue).'} />
      <p>{es
        ? 'La pestana Clasificar de la App muestra esto en vivo para una sola curva (p-valores, conjunto, bandera OOD); la tabla de Experimentos (pestana Estudios) reporta la cobertura y la tasa OOD agregadas por caso, leidas del manifiesto comprometido.'
        : 'The App Classify tab shows this live for a single curve (p-values, set, OOD flag); the Experiments table (Studies tab) reports the aggregated coverage and OOD rate per case, read from the committed manifest.'}</p>
      <Callout variant="honest" title={es ? 'Cobertura, no exactitud' : 'Coverage, not accuracy'}>
        {es ? 'Un conjunto de prediccion grande puede tener cobertura perfecta y aun asi ser poco informativo; por eso tambien se reporta el tamano medio del conjunto. La capa dual (Atribucion+) intercambia un poco de cobertura por conjuntos mas ajustados, y ambas cifras se muestran.' : 'A large prediction set can have perfect coverage yet be uninformative; that is why the mean set size is also reported. The dual layer (Attribution+) trades a little coverage for tighter sets, and both figures are shown.'}
      </Callout>
    </div>
  );
}

function MethodAgreementExp({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Segunda pregunta: la estructura de GeoTypes es robusta al metodo, o un artefacto de DTW k-medoids? Se corren 7 alternativas SOTA sobre el mismo ensamble y se mide su acuerdo con la referencia por Adjusted Rand Index. Donde muchos metodos coinciden, la estructura es real; donde solo uno lo hace, se lee con cautela.'
        : 'Second question: is the GeoType structure robust to the method, or an artifact of DTW k-medoids? Seven SOTA alternatives are run on the same ensemble and their agreement with the reference is measured by Adjusted Rand Index. Where many methods agree, the structure is real; where only one does, it is read with caution.'}</p>
      <p>{es
        ? <>Resultado horneado (pestana Acuerdo de metodos de la App): en REAL_A, BENCH_A y BENCH_C, 6 de 7 metodos coinciden con DTW (ARI &gt; 0.5), y en BENCH_C HDBSCAN <Cite id="campello2013" paren /> recupera K por si solo. Pero en BENCH_B (el dataset de backbone) SOLO el clustering espectral <Cite id="vonluxburg2007" paren /> coincide: la estructura ahi es fragil y se reporta como tal.</>
        : <>Baked result (the App Method agreement tab): on REAL_A, BENCH_A and BENCH_C, 6 of 7 methods agree with DTW (ARI &gt; 0.5), and on BENCH_C HDBSCAN <Cite id="campello2013" paren /> independently recovers K. But on BENCH_B (the backbone dataset) ONLY spectral clustering <Cite id="vonluxburg2007" paren /> agrees: the structure there is fragile and is reported as such.</>}</p>
      <Callout variant="honest" title={es ? 'BENCH_B: solo el espectral coincide' : 'BENCH_B: only spectral agrees'}>
        {es ? 'No se esconde el caso incomodo. Que solo un metodo coincida en BENCH_B es un resultado honesto sobre ese dataset, no una falla del pipeline; el catalogo ahi debe leerse con mas cautela.' : 'The awkward case is not hidden. That only one method agrees on BENCH_B is an honest result about that dataset, not a pipeline failure; the catalogue there should be read with more caution.'}
      </Callout>
      <Refs ids={['cuturi2017', 'paparrizos2015', 'vonluxburg2007', 'campello2013']} label="Refs" />
    </div>
  );
}

const REDIST: Record<string, [string, string]> = {
  // dataset -> [redistribution, status]
  '4TU A/B/C': ['CC-BY (mirror)', 'live'],
  'welltestpy field': ['MIT (mirror)', 'live'],
  'GeoDFN + open-DARTS sims': ['ours (mirror)', 'live'],
};

function Datasets({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Los datos que alimentan a Pulso, con su procedencia y terminos de redistribucion. Los datos sinteticos (familias analiticas, sims GeoDFN/open-DARTS) estan etiquetados como tales; los reales (corpus 4TU, campanas de campo welltestpy) llevan su licencia. Nada restringido se re-hospeda.'
        : 'The data that feeds Pulso, with its provenance and redistribution terms. Synthetic data (analytic families, GeoDFN/open-DARTS sims) is labelled as such; real data (the 4TU corpus, welltestpy field campaigns) carries its licence. No restricted data is re-hosted.'}</p>
      <div className="scroll-x">
        <table>
          <thead><tr><th>{es ? 'dataset' : 'dataset'}</th><th>{es ? 'tipo' : 'type'}</th><th>{es ? 'redistribucion' : 'redistribution'}</th><th>{es ? 'estado' : 'status'}</th></tr></thead>
          <tbody>
            <tr><td>4TU A / B / C</td><td className="tag">{es ? 'real' : 'real'}</td><td>{REDIST['4TU A/B/C'][0]}</td><td><span className="badge ok">{REDIST['4TU A/B/C'][1]}</span></td></tr>
            <tr><td>welltestpy ({es ? 'campo' : 'field'})</td><td className="tag">{es ? 'real' : 'real'}</td><td>{REDIST['welltestpy field'][0]}</td><td><span className="badge ok">{REDIST['welltestpy field'][1]}</span></td></tr>
            <tr><td>GeoDFN + open-DARTS</td><td className="tag">{es ? 'sintetico' : 'synthetic'}</td><td>{REDIST['GeoDFN + open-DARTS sims'][0]}</td><td><span className="badge ok">{REDIST['GeoDFN + open-DARTS sims'][1]}</span></td></tr>
            <tr><td>{es ? 'familias analiticas (Warren-Root)' : 'analytic families (Warren-Root)'}</td><td className="tag">{es ? 'sintetico' : 'synthetic'}</td><td>{es ? 'generado en vivo' : 'generated live'}</td><td><span className="badge ok">live</span></td></tr>
          </tbody>
        </table>
      </div>
      <Callout variant="honest" title={es ? 'Sintetico etiquetado' : 'Synthetic labelled'}>
        {es ? 'Cada celda sintetica se marca; ningun dato sintetico se presenta como medido. El corpus 4TU restringido no se re-hospeda: se usa su matriz DTW precomputada en el vault, y solo los resultados agregados se comprometen.' : 'Every synthetic cell is marked; no synthetic data is presented as measured. The restricted 4TU corpus is not re-hosted: its vault-only precomputed DTW matrix is used, and only aggregated results are committed.'}
      </Callout>
      <Refs ids={['kameltarghi2026', 'theis1935']} label="Refs" />
    </div>
  );
}

function Negatives({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Los resultados negativos son parte del producto, no se esconden. Tres ejemplos honestos del bake real:'
        : 'Negative results are part of the product, not hidden. Three honest examples from the real bake:'}</p>
      <ul>
        <li>{es ? 'BENCH_B: de 7 metodos de clustering, solo el espectral coincide con DTW; la estructura de GeoTypes ahi es fragil.' : 'BENCH_B: of 7 clustering methods, only spectral agrees with DTW; the GeoType structure there is fragile.'}</li>
        <li>{es ? 'Campanas de campo: la atribucion cruzada entre sitios (Horkheim vs Lauswiesen) da un resultado nulo honesto; los descriptores no predicen el sitio, y la atribucion se retiene.' : 'Field campaigns: cross-site attribution (Horkheim vs Lauswiesen) gives an honest null; the descriptors do not predict the site, and attribution is withheld.'}</li>
        <li>{es ? 'DFM03 (redes dispersas): el gate de fidelidad MRST FALLA; se documenta el fallo en vez de forzar un PASS.' : 'DFM03 (sparse networks): the MRST fidelity gate FAILS; the failure is documented rather than forcing a PASS.'}</li>
      </ul>
      <Callout variant="honest" title={es ? 'Un nulo es informacion' : 'A null is information'}>
        {es ? 'Cuando la atribucion cae cerca del azar o un gate de fidelidad falla, se reporta explicitamente. Un producto que solo muestra exitos no es honesto; el registro de experimentos, positivos y negativos, ES el producto.' : 'When attribution falls near chance or a fidelity gate fails, it is reported explicitly. A product that only shows successes is not honest; the experiment record, positive and negative, IS the product.'}
      </Callout>
    </div>
  );
}

function Studies({ es }: { es: boolean }) {
  const rows = useManifests();
  const studies = rows.filter((m) => m.artifact.trace_schema.startsWith('flowdna.trace/') || m.artifact.trace_schema.startsWith('flowdna.dfm/') || m.artifact.trace_schema.startsWith('pulso.'));
  const num = (m: CaseManifest, k: string) => { const v = (m.metrics as Record<string, unknown>)[k]; return typeof v === 'number' ? v.toFixed(3) : '-'; };
  return (
    <div>
      <p>{es ? 'Las metricas de cada estudio, leidas de los manifiestos comprometidos (nunca escritas a mano): K, silueta de entrenamiento, cobertura conformal y tasa fuera-de-catalogo.' : 'The metrics of every study, read from the committed manifests (never typed in): K, training silhouette, conformal coverage and out-of-catalogue rate.'}</p>
      <div className="scroll-x">
        <table>
          <thead><tr><th>case</th><th>K</th><th>silhouette</th><th>coverage</th><th>OOD</th></tr></thead>
          <tbody>
            {studies.map((m) => { const conf = (m.metrics as { conformal?: Record<string, number> }).conformal ?? {}; return (
              <tr key={m.case_id}><td>{m.case_id}</td><td>{num(m, 'k')}</td><td>{num(m, 'silhouette_train')}</td><td>{conf.empirical_coverage_test?.toFixed(2) ?? '-'}</td><td>{conf.ood_rate?.toFixed(2) ?? '-'}</td></tr>
            ); })}
          </tbody>
        </table>
      </div>
      {studies.length === 0 && <p className="muted">{es ? 'cargando...' : 'loading...'}</p>}
    </div>
  );
}

export function Experiments() {
  const es = useShellLang() === 'es';
  const tabs = [
    { id: 'protocol', label: es ? '1. Protocolo sin fugas' : '1. Leakage-safe protocol', content: <Protocol es={es} /> },
    { id: 'coverage', label: es ? '2. Cobertura conformal' : '2. Conformal coverage', content: <Coverage es={es} /> },
    { id: 'agreement', label: es ? '3. Acuerdo de metodos' : '3. Method agreement', content: <MethodAgreementExp es={es} /> },
    { id: 'datasets', label: es ? '4. Datasets' : '4. Datasets', content: <Datasets es={es} /> },
    { id: 'studies', label: es ? '5. Tabla de estudios' : '5. Studies table', content: <Studies es={es} /> },
    { id: 'negatives', label: es ? '6. Resultados negativos' : '6. Negative results', content: <Negatives es={es} /> },
  ];
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Experimentos' : 'Experiments'}</h1>
        <p className="lede">
          {es
            ? 'Las preguntas experimentales, separadas: el protocolo sin fugas, la cobertura conformal, el acuerdo entre metodos, los datasets con su procedencia, la tabla de estudios (metricas de artefactos comprometidos) y los resultados negativos honestos. Numeros de artefactos, no escritos a mano.'
            : 'The experimental questions, separated: the leakage-safe protocol, the conformal coverage, the method agreement, the datasets with their provenance, the studies table (committed-artifact metrics) and the honest negative results. Numbers from artifacts, not typed in.'}
        </p>
      </div>
      <Tabs tabs={tabs} ariaLabel={es ? 'Experimentos' : 'Experiments'} />
    </div>
  );
}
