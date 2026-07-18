// The five doc pages (ADR-0017): each is a `.page-body prose` root with a `.page-head` (h1 + lede) and
// deep `<section>`s. Bilingual by construction (es ? EN : ES), KaTeX via <Equation>/<InlineMath>,
// theme-aware SVG figures via <Figure>, honest <Callout>, and inline <Cite>/<Refs> from data/citations.
// Introduction is authored to the full bar here; Methodology/Implementation/Experiments/Benchmark are in
// the correct layout and are being deepened per-unit to the same bar.
import { useEffect, useState } from 'react';
import { Callout, Cite, Equation, Figure, InlineMath, Refs, useShellLang } from '@fasl-work/caos-app-shell';
import { useT } from '../i18n/useT';
import { loadIndex, loadManifest } from '../api/artifacts';
import type { CaseIndex, CaseManifest } from '../lib/contract.types';

// ---------------------------------------------------------------------------------------------------
// Introduction (full ADR-0017 bar): overview pipeline SVG + 5 deep sections + 3 captioned equations +
// a >=10-symbol glossary + an honest callout + inline Cite/Refs per section, bilingual.
// ---------------------------------------------------------------------------------------------------
function PipelineSVG({ es }: { es: boolean }) {
  const L = es
    ? ['Ensamble DFN', 'Transiente p_wD(t_D)', 'Derivada de Bourdet', 'Matriz DTW', 'Catálogo k-medoids', 'Asignación conformal']
    : ['DFN ensemble', 'Transient p_wD(t_D)', 'Bourdet derivative', 'DTW matrix', 'k-medoids catalogue', 'Conformal assignment'];
  const w = 760, h = 150, bw = 116, gap = (w - L.length * bw) / (L.length - 1 || 1), y = 40, bh = 62;
  return (
    <Figure caption={es
      ? 'Figura 1. El pipeline de extremo a extremo: de un ensamble de redes de fractura a una asignación conformal con garantía de cobertura, todo gobernado por la forma del transiente de presión.'
      : 'Figure 1. The end-to-end pipeline: from a fracture-network ensemble to a coverage-guaranteed conformal assignment, all governed by the shape of the pressure transient.'}>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img"
        aria-label={es ? 'Diagrama del pipeline de Pulso' : 'Pulso pipeline diagram'} style={{ maxWidth: 760 }}>
        {L.map((label, i) => {
          const x = i * (bw + gap);
          return (
            <g key={i}>
              <rect x={x} y={y} width={bw} height={bh} rx={8} fill="var(--bg-3, #eef1f5)"
                stroke="currentColor" strokeOpacity={0.35} />
              <text x={x + bw / 2} y={y + bh / 2 + 4} textAnchor="middle" fontSize={11.5} fill="currentColor">
                {label.length > 16 ? label.slice(0, 15) + '…' : label}
              </text>
              {i < L.length - 1 && (
                <path d={`M${x + bw + 3} ${y + bh / 2} L${x + bw + gap - 3} ${y + bh / 2}`}
                  stroke="currentColor" strokeOpacity={0.5} strokeWidth={1.5} markerEnd="url(#pf-arr)" />
              )}
            </g>
          );
        })}
        <defs>
          <marker id="pf-arr" viewBox="0 0 8 8" refX="6" refY="4" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0 0 L8 4 L0 8 z" fill="currentColor" fillOpacity={0.6} />
          </marker>
        </defs>
        <text x={w / 2} y={h - 8} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.6}>
          {es ? 'offline (bake) --- live (navegador): generación + DTW + conformal + ONNX'
            : 'offline (bake) --- live (browser): generation + DTW + conformal + ONNX'}
        </text>
      </svg>
    </Figure>
  );
}

export function Introduction() {
  const es = useShellLang() === 'es';
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Introducción' : 'Introduction'}</h1>
        <p className="lede">
          {es
            ? <>Pulso es un banco de trabajo para descubrir, catalogar y asignar los comportamientos de flujo recurrentes que se esconden en la forma de un transiente de presión. No es un ajustador de un solo modelo ni un reemplazo del simulador: dado un ensamble de respuestas de presión, agrupa sus derivadas de Bourdet en un catálogo de GeoTypes con <InlineMath tex="k" /> medoides y asigna curvas nuevas con una garantía de cobertura conformal.</>
            : <>Pulso is a workbench for discovering, cataloguing, and assigning the recurring flow behaviours hidden in the shape of a pressure transient. It is not a single-model fitter and not a simulator replacement: given an ensemble of pressure responses, it clusters their Bourdet derivatives into a catalogue of GeoTypes with <InlineMath tex="k" /> medoids and assigns new curves with a conformal coverage guarantee.</>}
        </p>
      </div>

      <PipelineSVG es={es} />

      <section>
        <h2>{es ? '1. El problema industrial' : '1. The industrial problem'}</h2>
        <p>
          {es
            ? 'En un yacimiento o acuífero fracturado, la respuesta de presión de un pozo a la producción o inyección lleva la firma de la red de fracturas que lo rodea. Un ensayo de presión transitoria (pressure-transient test) registra la presión adimensional de fondo de pozo a lo largo del tiempo, y su interpretación clásica busca rectas y regímenes de flujo. El problema aparece a escala de ensamble: cuando se generan cientos de redes discretas de fractura (DFN) estadísticamente equivalentes, sus transientes no son todos distintos, sino que se agrupan en un pequeño número de comportamientos de flujo recurrentes.'
            : "In a fractured reservoir or aquifer, a well's pressure response to production or injection carries the signature of the fracture network around it. A pressure-transient test records the dimensionless wellbore pressure over time, and its classical interpretation hunts for straight lines and flow regimes. The problem appears at ensemble scale: when hundreds of statistically-equivalent discrete fracture networks (DFNs) are generated, their transients are not all distinct but instead cluster into a small number of recurring flow behaviours."}
        </p>
        <p>
          {es
            ? 'Pulso trata ese hecho como el objeto de estudio: no ajusta un pozo aislado, sino que descubre el vocabulario de comportamientos de un ensamble completo (real, simulado o analítico) y lo vuelve una herramienta operativa: un catálogo consultable con asignación cuantificada.'
            : 'Pulso treats that fact as the object of study: it does not fit an isolated well but discovers the vocabulary of behaviours of a whole ensemble (real, simulated, or analytic) and turns it into an operational tool: a queryable catalogue with quantified assignment.'}
        </p>
        <Refs ids={['kameltarghi2026', 'gringarten2008', 'lei2017']} label="Refs" />
      </section>

      <section>
        <h2>{es ? '2. La física: la derivada diagnóstica' : '2. The physics: the diagnostic derivative'}</h2>
        <p>
          {es
            ? <>La huella interpretativa no es la presión sino su derivada logarítmica, la derivada de Bourdet <Cite id="bourdet1989" paren />. En una gráfica log-log revela el régimen de flujo: el flujo radial produce una meseta en 0.5; una fractura de doble porosidad <Cite id="warren1963" paren /> produce un valle de transición por debajo de 0.5; los límites producen una pendiente unitaria tardía. La forma de esa derivada, no su amplitud, es lo que Pulso agrupa.</>
            : <>The interpretive fingerprint is not the pressure but its logarithmic derivative, the Bourdet derivative <Cite id="bourdet1989" paren />. On a log-log plot it reveals the flow regime: radial flow gives a 0.5 plateau; a dual-porosity fracture system <Cite id="warren1963" paren /> gives a transition valley below 0.5; boundaries give a late unit slope. The shape of that derivative, not its amplitude, is what Pulso clusters.</>}
        </p>
        <Equation tex="p'_{wD}(t_D) = \frac{d\,p_{wD}}{d\ln t_D} = t_D\,\frac{d\,p_{wD}}{d t_D}"
          caption={es
            ? 'Ec. 1. La derivada de Bourdet: la derivada de la presión respecto al logaritmo del tiempo adimensional. La meseta radial en 0.5 y el valle de doble porosidad son sus rasgos diagnósticos.'
            : 'Eq. 1. The Bourdet derivative: the derivative of pressure with respect to the log of dimensionless time. The 0.5 radial plateau and the dual-porosity valley are its diagnostic features.'} />
        <Refs ids={['bourdet1989', 'warren1963', 'gringarten2008']} label="Refs" />
      </section>

      <section>
        <h2>{es ? '3. La matemática gobernante' : '3. The governing math'}</h2>
        <p>
          {es
            ? <>Las familias analíticas de Pulso se generan con el modelo de doble porosidad de Warren-Root <Cite id="warren1963" paren /> en espacio de Laplace, con almacenamiento de pozo y skin. La respuesta adimensional de fondo se obtiene invirtiendo la solución de Laplace <InlineMath tex="\bar p_{wD}(s)" />:</>
            : <>Pulso's analytic families are generated from the Warren-Root dual-porosity model <Cite id="warren1963" paren /> in Laplace space, with wellbore storage and skin. The dimensionless wellbore response is obtained by inverting the Laplace-space solution <InlineMath tex="\bar p_{wD}(s)" />:</>}
        </p>
        <Equation tex="\bar p_{wD}(s) = \frac{K_0\!\left(\sqrt{s\,f(s)}\right)}{s\,\sqrt{s\,f(s)}\;K_1\!\left(\sqrt{s\,f(s)}\right)}, \qquad f(s) = \frac{\omega(1-\omega)s + \lambda}{(1-\omega)s + \lambda}"
          caption={es
            ? 'Ec. 2. Presión de pozo de doble porosidad en espacio de Laplace (Warren-Root, flujo interporoso pseudo-estacionario). f(s) es la función de interporosidad; omega y lambda fijan la profundidad y el tiempo del valle de transición.'
            : 'Eq. 2. Dual-porosity wellbore pressure in Laplace space (Warren-Root, pseudo-steady interporosity flow). f(s) is the interporosity function; omega and lambda set the depth and timing of the transition valley.'} />
        <Equation tex="\omega = \frac{(\phi c_t)_f}{(\phi c_t)_f + (\phi c_t)_m}, \qquad \lambda = \alpha\,\frac{k_m}{k_f}\,r_w^2"
          caption={es
            ? 'Ec. 3. El cociente de almacenamiento omega (fracción de la capacidad en las fracturas) y el coeficiente de flujo interporoso lambda (que controla cuándo la matriz alimenta a las fracturas).'
            : 'Eq. 3. The storativity ratio omega (the fraction of capacity in the fractures) and the interporosity flow coefficient lambda (which controls when the matrix feeds the fractures).'} />
        <p className="measure">
          {es ? 'Símbolos: ' : 'Symbols: '}
        </p>
        <ul>
          <li><InlineMath tex="p_{wD}" /> {es ? 'presión adimensional de fondo de pozo' : 'dimensionless wellbore pressure'}</li>
          <li><InlineMath tex="t_D" /> {es ? 'tiempo adimensional' : 'dimensionless time'}</li>
          <li><InlineMath tex="s" /> {es ? 'variable de Laplace' : 'Laplace variable'}</li>
          <li><InlineMath tex="\omega" /> {es ? 'cociente de almacenamiento fractura/total' : 'fracture/total storativity ratio'}</li>
          <li><InlineMath tex="\lambda" /> {es ? 'coeficiente de flujo interporoso' : 'interporosity flow coefficient'}</li>
          <li><InlineMath tex="f(s)" /> {es ? 'función de interporosidad' : 'interporosity function'}</li>
          <li><InlineMath tex="K_0, K_1" /> {es ? 'funciones de Bessel modificadas de segunda especie' : 'modified Bessel functions of the second kind'}</li>
          <li><InlineMath tex="S" /> {es ? 'skin (daño/estimulación de pozo)' : 'skin (wellbore damage/stimulation)'}</li>
          <li><InlineMath tex="C_D" /> {es ? 'coeficiente de almacenamiento de pozo adimensional' : 'dimensionless wellbore storage coefficient'}</li>
          <li><InlineMath tex="k_f, k_m" /> {es ? 'permeabilidad de fractura y de matriz' : 'fracture and matrix permeability'}</li>
          <li><InlineMath tex="r_w" /> {es ? 'radio de pozo' : 'wellbore radius'}</li>
        </ul>
        <Refs ids={['warren1963', 'theis1935']} label="Refs" />
      </section>

      <section>
        <h2>{es ? '4. El pipeline de extremo a extremo' : '4. The end-to-end pipeline'}</h2>
        <p>
          {es ? 'De la geología a una asignación con garantía, en pasos deterministas y reproducibles:' : 'From geology to a guaranteed assignment, in deterministic, reproducible steps:'}
        </p>
        <ol>
          <li>{es ? 'Generar ensambles de redes discretas de fractura (GeoDFN) o tomar datos reales (corpus 4TU, campañas de bombeo de campo) o familias analíticas.' : 'Generate discrete-fracture-network ensembles (GeoDFN), or take real data (the 4TU corpus, field pumping campaigns), or analytic families.'}</li>
          <li>{es ? 'Obtener el transiente: simular la física con open-DARTS ' : 'Obtain the transient: simulate the physics with open-DARTS '}<Cite id="khait2018" paren />{es ? ', o evaluar la solución analítica de doble porosidad.' : ', or evaluate the analytic dual-porosity solution.'}</li>
          <li>{es ? 'Preprocesar: remuestrear a una grilla log-tiempo, tomar la derivada de Bourdet, normalizar (z-score).' : 'Preprocess: resample onto a log-time grid, take the Bourdet derivative, normalize (z-score).'}</li>
          <li>{es ? 'Construir la matriz de distancias DTW con banda de Sakoe-Chiba ' : 'Build the DTW distance matrix with a Sakoe-Chiba band '}<Cite id="sakoe1978" paren />{es ? ' (alineación invariante a escala de tiempo).' : ' (time-scale-invariant alignment).'}</li>
          <li>{es ? 'Descubrir el catálogo: k-medoids PAM sobre la matriz DTW ' : 'Discover the catalogue: PAM k-medoids over the DTW matrix '}<Cite id="kaufman1990" paren />{es ? ', con K elegido por silueta. Cada GeoType es una curva miembro real (medoide).' : ', with K chosen by silhouette. Each GeoType is a real member curve (medoid).'}</li>
          <li>{es ? 'Asignar con conformal condicional por clase (Mondrian) ' : 'Assign with class-conditional (Mondrian) conformal prediction '}<Cite id="vovk2005" paren />{es ? ': p-valores, conjunto de predicción y bandera fuera-de-catálogo.' : ': p-values, a prediction set, and an out-of-catalogue flag.'}</li>
          <li>{es ? 'Atribuir: bosque aleatorio + SHAP hacia los descriptores físicos, con gate de exactitud honesto.' : 'Attribute: random forest + SHAP onto the physical descriptors, with an honest accuracy gate.'}</li>
        </ol>
        <Refs ids={['sakoe1978', 'kaufman1990', 'vovk2005', 'khait2018']} label="Refs" />
      </section>

      <section>
        <h2>{es ? '5. Exacto vs ilustrativo (alcance honesto)' : '5. Exact vs illustrative (honest scope)'}</h2>
        <p>
          {es
            ? 'El procesamiento pesado (la matriz DTW completa, PAM, el entrenamiento GPU de los modelos aprendidos) se ejecuta offline y se compromete como artefactos deterministas. El navegador ejecuta en vivo las piezas ligeras: genera una curva analítica, calcula su distancia DTW a los medoides, la asigna conformemente y ejecuta los modelos aprendidos vía onnxruntime-web.'
            : 'The heavy processing (the full DTW matrix, PAM, the GPU training of the learned models) runs offline and is committed as deterministic artifacts. The browser runs the light pieces live: it generates an analytic curve, computes its DTW distance to the medoids, assigns it conformally, and runs the learned models via onnxruntime-web.'}
        </p>
        <Callout variant="honest" title={es ? 'Ningún método gana en todo' : 'No single method wins everywhere'}>
          {es
            ? 'El catálogo se descubre por caso; su K y su forma dependen del ensamble. Los gráficos muestran datos comprometidos reales, la sintética está etiquetada como tal, y las métricas no se inflan: donde un método falla o la atribución no es fiable, se dice explícitamente.'
            : 'The catalogue is discovered per case; its K and shape depend on the ensemble. The charts show real committed data, synthetic is labelled as such, and metrics are not inflated: where a method fails or attribution is not reliable, it is stated explicitly.'}
        </Callout>
        <Refs ids={['kameltarghi2026', 'angelopoulos2023']} label="Refs" />
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------------
// The remaining four pages: correct `.page-body prose` layout with Cite/Refs, in active deepening to the
// ADR-0017 section 2 bar (tabbed method families, per-tab equations + SVG + callout). Content below is
// the current transcription; each is upgraded per-unit.
// ---------------------------------------------------------------------------------------------------
export function Methodology() {
  const t = useT();
  const es = useShellLang() === 'es';
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{t.method.title}</h1>
        <p className="lede">{t.method.lead}</p>
      </div>
      <section>
        <h2>{t.method.s1h}</h2>
        <p>{t.method.s1}</p>
      </section>
      <section>
        <h2>{t.method.s2h}</h2>
        <p>{t.method.s2}</p>
        <Equation tex={t.method.dtw} caption={es ? 'Distancia DTW con banda de Sakoe-Chiba.' : 'DTW distance with a Sakoe-Chiba band.'} />
        <Refs ids={['sakoe1978', 'kaufman1990']} label="Refs" />
      </section>
      <section>
        <h2>{t.method.s3h}</h2>
        <p>{t.method.s3}</p>
        <Refs ids={['cuturi2017', 'paparrizos2015', 'vonluxburg2007', 'campello2013']} label="Refs" />
      </section>
      <section>
        <h2>{t.method.s4h}</h2>
        <p>{t.method.s4}</p>
        <Equation tex={t.method.conf} caption={es ? 'p-valor conformal condicional por clase.' : 'Class-conditional conformal p-value.'} />
        <Refs ids={['vovk2005', 'angelopoulos2023']} label="Refs" />
      </section>
      <section>
        <h2>{t.method.s5h}</h2>
        <p>{t.method.s5}</p>
        <Refs ids={['ismailfawaz2020', 'nie2023', 'yue2022']} label="Refs" />
      </section>
      <section>
        <h2>{t.method.s6h}</h2>
        <p>{t.method.s6}</p>
        <Refs ids={['breiman2001', 'lundberg2020']} label="Refs" />
      </section>
    </div>
  );
}

export function Implementation() {
  const t = useT();
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{t.impl.title}</h1>
        <p className="lede">{t.impl.lead}</p>
      </div>
      <section><h2>{t.impl.lanesh}</h2><p>{t.impl.lanes}</p></section>
      <section><h2>{t.impl.stagesh}</h2><p>{t.impl.stages}</p></section>
      <section><h2>{t.impl.contractsh}</h2><p>{t.impl.contracts}</p></section>
      <section><h2>{t.impl.stackh}</h2><p>{t.impl.stack}</p></section>
    </div>
  );
}

function useManifests() {
  const [rows, setRows] = useState<CaseManifest[]>([]);
  useEffect(() => {
    let alive = true;
    loadIndex()
      .then((ix: CaseIndex) => Promise.all(ix.cases.map((c) => loadManifest(c.case_id))))
      .then((ms) => alive && setRows(ms))
      .catch(() => {});
    return () => { alive = false; };
  }, []);
  return rows;
}

const LANE: Record<string, string> = {
  'synthetic-analytic': 'analytic', 'real-4tu': '4TU', 'field-pumping': 'field', 'simulated-dfm': 'DFM',
};

export function Experiments() {
  const t = useT();
  const rows = useManifests();
  const studies = rows.filter(
    (m) => m.artifact.trace_schema.startsWith('flowdna.trace/') ||
      m.artifact.trace_schema.startsWith('flowdna.dfm/') ||
      m.artifact.trace_schema.startsWith('pulso.'),
  );
  const num = (m: CaseManifest, k: string) => {
    const v = (m.metrics as Record<string, unknown>)[k];
    return typeof v === 'number' ? v.toFixed(3) : '—';
  };
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{t.exp.title}</h1>
        <p className="lede">{t.exp.lead}</p>
      </div>
      <section>
        <h2>{t.exp.studies}</h2>
        <div className="scroll-x">
          <table>
            <thead>
              <tr>
                <th>case</th><th>{t.common.source}</th><th>K</th>
                <th>{t.common.silhouette}</th><th>{t.common.coverage}</th><th>{t.common.oodRate}</th>
              </tr>
            </thead>
            <tbody>
              {studies.map((m) => {
                const conf = (m.metrics as { conformal?: Record<string, number> }).conformal ?? {};
                return (
                  <tr key={m.case_id}>
                    <td>{m.case_id}</td>
                    <td className="tag">{LANE[m.real_or_synthetic] ?? m.real_or_synthetic}</td>
                    <td>{num(m, 'k')}</td>
                    <td>{num(m, 'silhouette_train')}</td>
                    <td>{conf.empirical_coverage_test?.toFixed(2) ?? '—'}</td>
                    <td>{conf.ood_rate?.toFixed(2) ?? '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <section>
        <h2>{t.exp.findingsh}</h2>
        <ul>
          <li>{t.exp.f1}</li><li>{t.exp.f2}</li><li>{t.exp.f3}</li><li>{t.exp.f4}</li><li>{t.exp.f5}</li>
        </ul>
      </section>
    </div>
  );
}

export function Benchmark() {
  const t = useT();
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{t.bench.title}</h1>
        <p className="lede">{t.bench.lead}</p>
      </div>
      <section><h2>{t.bench.crossh}</h2><p>{t.bench.cross}</p></section>
      <section><h2>{t.bench.kh}</h2><p>{t.bench.k}</p></section>
      <section><h2>{t.bench.engineh}</h2><p>{t.bench.engine}</p></section>
    </div>
  );
}
