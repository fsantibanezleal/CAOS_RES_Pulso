// Methodology (ADR-0017 section 2): the method ladder as deep method-family Tabs. Each tab carries
// >=4 dense bilingual paragraphs naming the build's exact behaviour + constants, >=2 captioned KaTeX
// equations, >=1 hand-authored theme-aware SVG, one honest Callout, and an inline Refs. >=2 tabs are the
// learned methods. Transcribed from docs/methods/{01..05} + docs/frameworks. Theme-aware SVGs use
// currentColor + var(--bg-3) so they read in light and dark.
import { Callout, Cite, Equation, Figure, Refs, Tabs, useShellLang } from '@fasl-work/caos-app-shell';

const box = { fill: 'var(--bg-3, #eef1f5)', stroke: 'currentColor', strokeOpacity: 0.35 } as const;

function PreprocSVG({ es }: { es: boolean }) {
  const steps = es
    ? ['p_wD(t_D) crudo', 'grilla log-tiempo', "Bourdet p'", 'z-score']
    : ['raw p_wD(t_D)', 'log-time grid', "Bourdet p'", 'z-score'];
  return (
    <Figure caption={es
      ? 'El preproceso: la presion cruda se remuestrea a una grilla log-uniforme, se deriva (Bourdet) y se normaliza a media cero y varianza uno, de modo que solo la FORMA sobrevive.'
      : 'Preprocessing: the raw pressure is resampled onto a log-uniform grid, differentiated (Bourdet), and normalised to zero mean and unit variance, so that only the SHAPE survives.'}>
      <svg viewBox="0 0 620 90" width="100%" style={{ maxWidth: 620 }} role="img"
        aria-label={es ? 'Diagrama del preproceso' : 'Preprocessing diagram'}>
        {steps.map((s, i) => (
          <g key={i}>
            <rect x={i * 155} y={22} width={132} height={40} rx={7} {...box} />
            <text x={i * 155 + 66} y={46} textAnchor="middle" fontSize={12} fill="currentColor">{s}</text>
            {i < steps.length - 1 && <path d={`M${i * 155 + 134} 42 L${i * 155 + 153} 42`} stroke="currentColor" strokeOpacity={0.5} strokeWidth={1.5} />}
          </g>
        ))}
      </svg>
    </Figure>
  );
}

function DtwGridSVG({ es }: { es: boolean }) {
  const n = 8, cell = 26, pad = 26, w = pad * 2 + n * cell;
  const path = [[0, 0], [1, 0], [1, 1], [2, 1], [3, 2], [4, 3], [5, 3], [6, 4], [6, 5], [7, 6], [7, 7]];
  const band = 2;
  return (
    <Figure caption={es
      ? 'La matriz de alineacion DTW: el camino optimo (azul) serpentea para emparejar rasgos que ocurren en tiempos distintos; la banda de Sakoe-Chiba (sombreada) lo restringe a |i-j| <= w, dando invariancia a la escala de tiempo sin permitir alineaciones degeneradas.'
      : 'The DTW alignment matrix: the optimal path (blue) meanders to match features that occur at different times; the Sakoe-Chiba band (shaded) constrains it to |i-j| <= w, giving time-scale invariance without allowing degenerate alignments.'}>
      <svg viewBox={`0 0 ${w} ${w}`} width="100%" style={{ maxWidth: 260 }} role="img"
        aria-label={es ? 'Rejilla de alineacion DTW' : 'DTW alignment grid'}>
        {Array.from({ length: n }).map((_, i) => Array.from({ length: n }).map((__, j) => {
          const inBand = Math.abs(i - j) <= band;
          return <rect key={`${i}-${j}`} x={pad + j * cell} y={pad + i * cell} width={cell} height={cell}
            fill={inBand ? 'var(--accent, #4f9cf9)' : 'transparent'} fillOpacity={inBand ? 0.08 : 0}
            stroke="currentColor" strokeOpacity={0.15} />;
        }))}
        <path d={path.map((p, k) => `${k === 0 ? 'M' : 'L'}${pad + p[1] * cell + cell / 2} ${pad + p[0] * cell + cell / 2}`).join(' ')}
          fill="none" stroke="var(--accent, #4f9cf9)" strokeWidth={2.4} />
        <text x={pad} y={16} fontSize={10} fill="currentColor" opacity={0.7}>{es ? 'curva A' : 'curve A'}</text>
        <text x={w - 4} y={w - 6} fontSize={10} fill="currentColor" opacity={0.7} textAnchor="end">{es ? 'curva B' : 'curve B'}</text>
      </svg>
    </Figure>
  );
}

function MedoidSVG({ es }: { es: boolean }) {
  return (
    <Figure caption={es
      ? 'PAM elige MEDOIDES (curvas miembro reales, en color) que minimizan la distancia total dentro del cluster, no centroides sinteticos. Cada GeoType es por tanto una respuesta observada, no un promedio inventado.'
      : 'PAM picks MEDOIDS (real member curves, coloured) that minimise the total within-cluster distance, not synthetic centroids. Each GeoType is therefore an observed response, not an invented average.'}>
      <svg viewBox="0 0 360 150" width="100%" style={{ maxWidth: 360 }} role="img"
        aria-label={es ? 'Medoides vs centroides' : 'Medoids vs centroids'}>
        {[[70, 70, 'var(--geo-0, #4f9cf9)'], [270, 80, 'var(--geo-1, #f97b4f)']].map(([cx, cy, c], g) => (
          <g key={g}>
            {Array.from({ length: 9 }).map((_, i) => {
              const a = (i / 9) * Math.PI * 2, r = 34 + (i % 3) * 6;
              return <circle key={i} cx={(cx as number) + Math.cos(a) * r} cy={(cy as number) + Math.sin(a) * r} r={3} fill={c as string} fillOpacity={0.3} />;
            })}
            <circle cx={cx as number} cy={cy as number} r={6} fill={c as string} stroke="currentColor" strokeWidth={1.5} />
            <text x={cx as number} y={(cy as number) - 46} textAnchor="middle" fontSize={11} fill="currentColor">GT{g} {es ? 'medoide' : 'medoid'}</text>
          </g>
        ))}
      </svg>
    </Figure>
  );
}

function InceptionSVG({ es }: { es: boolean }) {
  const kernels = ['1x1', 'k=9', 'k=19', 'k=39', 'pool'];
  return (
    <Figure caption={es
      ? 'Un modulo Inception: un cuello de botella 1x1 seguido de convoluciones paralelas de kernel creciente (multi-escala) mas una rama de max-pooling; las salidas se concatenan. Apilar estos modulos con atajos residuales cada 3 da el clasificador InceptionTime.'
      : 'One Inception module: a 1x1 bottleneck feeding parallel convolutions of increasing kernel size (multi-scale) plus a max-pool branch; the outputs are concatenated. Stacking these with a residual shortcut every 3 gives the InceptionTime classifier.'}>
      <svg viewBox="0 0 460 170" width="100%" style={{ maxWidth: 460 }} role="img"
        aria-label={es ? 'Modulo Inception' : 'Inception module'}>
        <rect x={10} y={70} width={70} height={30} rx={6} {...box} />
        <text x={45} y={89} textAnchor="middle" fontSize={11} fill="currentColor">{es ? 'entrada' : 'input'}</text>
        {kernels.map((k, i) => (
          <g key={k}>
            <rect x={160} y={12 + i * 30} width={90} height={24} rx={6} {...box} />
            <text x={205} y={28 + i * 30} textAnchor="middle" fontSize={11} fill="currentColor">{k}</text>
            <path d={`M80 85 L160 ${24 + i * 30}`} stroke="currentColor" strokeOpacity={0.35} />
            <path d={`M250 ${24 + i * 30} L340 85`} stroke="currentColor" strokeOpacity={0.35} />
          </g>
        ))}
        <rect x={340} y={70} width={100} height={30} rx={6} fill="var(--accent, #4f9cf9)" fillOpacity={0.14} stroke="currentColor" strokeOpacity={0.35} />
        <text x={390} y={89} textAnchor="middle" fontSize={11} fill="currentColor">concat + BN</text>
      </svg>
    </Figure>
  );
}

function DualConformalSVG({ es }: { es: boolean }) {
  return (
    <Figure caption={es
      ? 'El conformal de doble representacion: el conjunto de prediccion es la INTERSECCION del conjunto conforme en forma (DTW) y el conforme en descriptores fisicos (RF). Una curva de la zona amarilla (forma correcta) pero fuera del azul (fisica implausible) queda excluida: es "forma correcta, fisica incorrecta".'
      : 'The dual-representation conformal set is the INTERSECTION of the shape-conformal set (DTW) and the descriptor-conformal set (RF). A curve in the yellow zone (right shape) but outside the blue (implausible physics) is excluded: it is "right shape, wrong physics".'}>
      <svg viewBox="0 0 360 180" width="100%" style={{ maxWidth: 360 }} role="img"
        aria-label={es ? 'Conformal de doble representacion' : 'Dual-representation conformal'}>
        <circle cx={140} cy={90} r={70} fill="#d8c14a" fillOpacity={0.16} stroke="currentColor" strokeOpacity={0.4} />
        <circle cx={220} cy={90} r={70} fill="var(--accent, #4f9cf9)" fillOpacity={0.16} stroke="currentColor" strokeOpacity={0.4} />
        <text x={95} y={90} textAnchor="middle" fontSize={11} fill="currentColor">{es ? 'forma' : 'shape'}</text>
        <text x={95} y={104} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.7}>DTW</text>
        <text x={265} y={90} textAnchor="middle" fontSize={11} fill="currentColor">{es ? 'descriptores' : 'descriptors'}</text>
        <text x={265} y={104} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.7}>RF</text>
        <text x={180} y={90} textAnchor="middle" fontSize={11} fill="currentColor">{es ? 'aceptar' : 'accept'}</text>
        <text x={180} y={104} textAnchor="middle" fontSize={9.5} fill="currentColor" opacity={0.8}>∩</text>
      </svg>
    </Figure>
  );
}

// ---------------------------------------------------------------------------------------------------

function Preprocessing({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Toda la escalera opera sobre la FORMA de la respuesta de presion, no sobre su amplitud absoluta. El primer paso convierte cada transiente crudo en una firma comparable. La presion adimensional de fondo se remuestrea a una grilla log-uniforme de tiempo (los ensayos abarcan varias decadas de tiempo, y la fisica de interes vive en el eje logaritmico), y sobre esa grilla se toma la derivada de Bourdet con una ventana de suavizado de L ciclos-log.'
        : 'The entire ladder operates on the SHAPE of the pressure response, not its absolute amplitude. The first step turns each raw transient into a comparable signature. The dimensionless wellbore pressure is resampled onto a log-uniform time grid (tests span several decades of time, and the physics of interest lives on the log axis), and on that grid the Bourdet derivative is taken with a smoothing window of L log-cycles.'}</p>
      <Equation tex="p'_{wD}(t_D) = \frac{d\,p_{wD}}{d\ln t_D}, \qquad \hat p'_i = \frac{\Delta p_L / \Delta x_L + \Delta p_R / \Delta x_R}{\;\;}\Big/\!\left(\tfrac{1}{\Delta x_L}+\tfrac{1}{\Delta x_R}\right)"
        caption={es ? 'Ec. La derivada de Bourdet con la ventana de dos lados de L ciclos-log (izquierda/derecha), que suaviza el ruido sin borrar el valle de doble porosidad.' : 'Eq. The Bourdet derivative with the two-sided L-log-cycle window (left/right), which smooths noise without erasing the dual-porosity valley.'} />
      <p>{es
        ? 'La derivada suavizada se normaliza a media cero y varianza uno (z-score). Este paso es lo que hace que un pozo de alta permeabilidad y uno de baja permeabilidad con la MISMA fisica de fractura caigan en el mismo GeoType: la normalizacion elimina la escala vertical y deja solo el patron de regimenes.'
        : 'The smoothed derivative is normalised to zero mean and unit variance (z-score). This step is what makes a high-permeability well and a low-permeability well with the SAME fracture physics fall into the same GeoType: normalisation removes the vertical scale and leaves only the regime pattern.'}</p>
      <Equation tex="\tilde x_i = \frac{p'_{wD}(t_{D,i}) - \mu}{\sigma}, \qquad \mu = \frac{1}{n}\sum_i p'_{wD}(t_{D,i}), \quad \sigma^2 = \frac{1}{n}\sum_i \big(p'_{wD}(t_{D,i})-\mu\big)^2"
        caption={es ? 'Ec. La normalizacion z-score sobre los n puntos de la grilla; el vector resultante es la firma que alimenta a DTW y a los modelos.' : 'Eq. The z-score normalisation over the n grid points; the resulting vector is the signature fed to DTW and the models.'} />
      <PreprocSVG es={es} />
      <p>{es
        ? 'Este preproceso es exactamente el que corre EN VIVO en el navegador (numpy/TS puro) cuando el usuario ajusta una curva sintetica, y el mismo que corrio OFFLINE al hornear cada caso; por eso la asignacion en vivo es identica a la comprometida.'
        : 'This preprocessing is exactly what runs LIVE in the browser (pure numpy/TS) when the user tunes a synthetic curve, and the same that ran OFFLINE when each case was baked; that is why the live assignment matches the committed one.'}</p>
      <Callout variant="honest" title={es ? 'Suavizado, no invencion' : 'Smoothing, not invention'}>
        {es ? 'La ventana L suaviza la derivada de datos ruidosos; una L demasiado grande borra el valle de doble porosidad y una demasiado chica lo llena de ruido. Se elige por caso y se documenta, y la curva cruda siempre esta disponible en el explorador de ensamble.' : 'The window L smooths the derivative of noisy data; too large an L erases the dual-porosity valley and too small floods it with noise. It is chosen per case and documented, and the raw curve is always available in the ensemble explorer.'}
      </Callout>
      <Refs ids={['bourdet1989', 'gringarten2008']} label="Refs" />
    </div>
  );
}

function Distances({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Dos transientes con la MISMA sucesion de regimenes pero desfasados en el tiempo (por distinta permeabilidad o radio) deben considerarse similares. La distancia euclidiana punto a punto los penaliza por el desfase; el Dynamic Time Warping (DTW) los alinea bajo un emparejamiento monotono antes de medir, absorbiendo la escala de tiempo.'
        : 'Two transients with the SAME sequence of regimes but shifted in time (by different permeability or radius) must be considered similar. Point-wise Euclidean distance penalises them for the shift; Dynamic Time Warping (DTW) aligns them under a monotonic matching before measuring, absorbing the time scale.'}</p>
      <Equation tex="D_{\mathrm{DTW}}(a,b) = \min_{\pi \in \Pi_w} \sum_{(i,j)\in\pi} \big(a_i - b_j\big)^2"
        caption={es ? 'Ec. La distancia DTW: el minimo sobre todos los caminos de alineacion monotonos pi dentro de la banda de ancho w.' : 'Eq. The DTW distance: the minimum over all monotonic alignment paths pi inside the band of width w.'} />
      <p>{es
        ? <>El minimo se calcula por programacion dinamica con la recurrencia de costo acumulado, restringida a la banda de Sakoe-Chiba <Cite id="sakoe1978" paren /> que prohibe alineaciones degeneradas (un punto emparejado con muchos):</>
        : <>The minimum is computed by dynamic programming with the accumulated-cost recurrence, restricted to the Sakoe-Chiba band <Cite id="sakoe1978" paren /> that forbids degenerate alignments (one point matched to many):</>}</p>
      <Equation tex="\gamma(i,j) = (a_i-b_j)^2 + \min\{\gamma(i-1,j),\,\gamma(i,j-1),\,\gamma(i-1,j-1)\}, \quad |i-j| \le w"
        caption={es ? 'Ec. La recurrencia de DTW con la restriccion de banda |i-j| <= w. El backend offline es la implementacion C de dtaidistance via pygeotypes; el navegador reimplementa la misma recurrencia en TypeScript.' : 'Eq. The DTW recurrence with the band constraint |i-j| <= w. The offline backend is the C implementation in dtaidistance via pygeotypes; the browser reimplements the same recurrence in TypeScript.'} />
      <DtwGridSVG es={es} />
      <p>{es
        ? 'Sobre el conjunto de entrenamiento se calcula la matriz de distancias completa NxN, que es el objeto que consume el clustering. Para el benchmark de corpus completo (miles de curvas) se reutiliza la matriz precomputada del corpus 4TU en lugar de recalcular NxN.'
        : 'Over the training set the full NxN distance matrix is computed, which is the object the clustering consumes. For the full-corpus benchmark (thousands of curves) the corpus 4TU precomputed matrix is reused instead of recomputing NxN.'}</p>
      <Callout variant="honest" title={es ? 'Por que no euclidiana' : 'Why not Euclidean'}>
        {es ? 'La comparacion de metodos (pestana Acuerdo de metodos en la App) incluye una linea base de k-medoids euclidiana y de correlacion precisamente para mostrar cuando la alineacion DTW gana su costo y cuando no: no se asume, se mide.' : 'The method comparison (Method agreement tab in the App) includes a Euclidean and a correlation k-medoids baseline precisely to show when the DTW alignment earns its cost and when it does not: it is not assumed, it is measured.'}
      </Callout>
      <Refs ids={['sakoe1978', 'kaufman1990']} label="Refs" />
    </div>
  );
}

function Catalogue({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'El catalogo de GeoTypes se descubre por Partitioning Around Medoids (PAM) sobre la matriz DTW. PAM elige K medoides (curvas miembro reales) que minimizan la distancia total dentro del cluster; a diferencia de k-means, el prototipo de cada GeoType es una respuesta OBSERVADA, no un promedio sintetico que podria no corresponder a ninguna fisica real.'
        : 'The GeoType catalogue is discovered by Partitioning Around Medoids (PAM) over the DTW matrix. PAM picks K medoids (real member curves) that minimise the total within-cluster distance; unlike k-means, each GeoType prototype is an OBSERVED response, not a synthetic average that might correspond to no real physics.'}</p>
      <Equation tex="\{m_1,\dots,m_K\} = \arg\min_{\{m_g\}} \sum_{i=1}^{n} \min_{g} D_{\mathrm{DTW}}(x_i, m_g)"
        caption={es ? 'Ec. El objetivo de PAM k-medoids: elegir K medoides que minimizan la distancia DTW total de cada curva a su medoide mas cercano. Se resuelve con reinicios (n_init escala con el tamano: 10 para <=800 curvas, menos para el benchmark).' : 'Eq. The PAM k-medoids objective: pick K medoids minimising the total DTW distance of each curve to its nearest medoid. Solved with restarts (n_init scales with size: 10 for <=800 curves, fewer for the benchmark).'} />
      <p>{es
        ? <>El numero de GeoTypes K no se fija a mano: se barre un rango y se elige por el coeficiente de silueta <Cite id="kaufman1990" paren />, que mide cuan compacto y separado esta cada cluster en la geometria DTW.</>
        : <>The number of GeoTypes K is not fixed by hand: a range is swept and K is chosen by the silhouette coefficient <Cite id="kaufman1990" paren />, which measures how compact and separated each cluster is in the DTW geometry.</>}</p>
      <Equation tex="s(i) = \frac{b(i) - a(i)}{\max\{a(i),\,b(i)\}}, \qquad s = \frac{1}{n}\sum_i s(i)"
        caption={es ? 'Ec. La silueta: a(i) es la distancia media de la curva i a su propio cluster, b(i) la del cluster vecino mas cercano. El K con mayor silueta media s es el elegido.' : 'Eq. The silhouette: a(i) is the mean distance of curve i to its own cluster, b(i) to the nearest neighbouring cluster. The K with the highest mean silhouette s is chosen.'} />
      <MedoidSVG es={es} />
      <p>{es
        ? 'La pestana Predictibilidad-vs-K (Atribucion+) muestra la silueta Y la exactitud del bosque aleatorio a lo largo de K, para verificar que el K elegido no es solo geometricamente compacto sino tambien ATRIBUIBLE a descriptores fisicos.'
        : 'The Predictability-vs-K tab (Attribution+) shows the silhouette AND the random-forest accuracy across K, to verify that the chosen K is not only geometrically compact but also ATTRIBUTABLE to physical descriptors.'}</p>
      <Callout variant="honest" title={es ? 'K se descubre, no se impone' : 'K is discovered, not imposed'}>
        {es ? 'Casos control degenerados (una sola respuesta dominante) producen K=1 o siluetas bajas, y se etiquetan como tales; no se fuerza un K "bonito" para aparentar estructura.' : 'Degenerate control cases (a single dominant response) yield K=1 or low silhouettes, and are labelled as such; a "nice" K is never forced to fake structure.'}
      </Callout>
      <Refs ids={['kaufman1990', 'kameltarghi2026']} label="Refs" />
    </div>
  );
}

function ClusteringComparison({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'El catalogo DTW k-medoids es la referencia; la escalera lo mide honestamente contra las alternativas SOTA sobre los MISMOS datos. Cada metodo se evalua por silueta (calidad en geometria DTW) y por Adjusted Rand Index (ARI, acuerdo corregido por azar con las etiquetas de referencia).'
        : 'The DTW k-medoids catalogue is the reference; the ladder measures it honestly against the SOTA alternatives on the SAME data. Each method is scored by silhouette (quality in DTW geometry) and by Adjusted Rand Index (ARI, chance-corrected agreement with the reference labels).'}</p>
      <p>{es
        ? <>Las alternativas: soft-DTW k-means con baricentros diferenciables <Cite id="cuturi2017" paren />, k-Shape por correlacion cruzada normalizada sin DTW <Cite id="paparrizos2015" paren />, clustering espectral sobre una afinidad DTW gaussiana <Cite id="vonluxburg2007" paren />, y HDBSCAN por densidad con ruido y K libre <Cite id="campello2013" paren />.</>
        : <>The alternatives: soft-DTW k-means with differentiable barycentres <Cite id="cuturi2017" paren />, k-Shape by normalised cross-correlation with no DTW <Cite id="paparrizos2015" paren />, spectral clustering on a Gaussian DTW affinity <Cite id="vonluxburg2007" paren />, and HDBSCAN density clustering with noise and free K <Cite id="campello2013" paren />.</>}</p>
      <Equation tex="\mathrm{soft\text{-}DTW}_\gamma(a,b) = -\gamma \log \sum_{\pi \in \Pi} \exp\!\Big(-\tfrac{1}{\gamma}\textstyle\sum_{(i,j)\in\pi}(a_i-b_j)^2\Big)"
        caption={es ? 'Ec. soft-DTW reemplaza el min de DTW por un soft-min diferenciable (gamma=1.0), lo que permite optimizar un baricentro sintetico como prototipo, la contraparte de centroide del medoide.' : 'Eq. soft-DTW replaces the DTW min with a differentiable soft-min (gamma=1.0), enabling optimisation of a synthetic barycentre prototype, the centroid counterpart of the medoid.'} />
      <Equation tex="\mathrm{ARI} = \frac{\sum_{ij}\binom{n_{ij}}{2} - \big[\sum_i\binom{a_i}{2}\sum_j\binom{b_j}{2}\big]/\binom{n}{2}}{\tfrac12\big[\sum_i\binom{a_i}{2}+\sum_j\binom{b_j}{2}\big] - \big[\sum_i\binom{a_i}{2}\sum_j\binom{b_j}{2}\big]/\binom{n}{2}}"
        caption={es ? 'Ec. El Adjusted Rand Index entre una particion alternativa y la referencia DTW: 1 = identica, ~0 = azar. Es el numero honesto de titular en la pestana Acuerdo de metodos.' : 'Eq. The Adjusted Rand Index between an alternative partition and the DTW reference: 1 = identical, ~0 = chance. It is the honest headline number in the Method agreement tab.'} />
      <Callout variant="honest" title={es ? 'Ningun metodo gana en todo' : 'No single method wins everywhere'}>
        {es ? 'Resultado horneado real: en REAL_A/BENCH_A/BENCH_C, 6 de 7 metodos coinciden con DTW (ARI>0.5) y HDBSCAN recupera K por si solo en C; pero en BENCH_B (dataset de backbone) solo el espectral coincide. Se reporta, no se esconde.' : 'Real baked result: on REAL_A/BENCH_A/BENCH_C, 6 of 7 methods agree with DTW (ARI>0.5) and HDBSCAN independently recovers K on C; but on BENCH_B (backbone dataset) only spectral agrees. This is reported, not hidden.'}
      </Callout>
      <Refs ids={['cuturi2017', 'paparrizos2015', 'vonluxburg2007', 'campello2013']} label="Refs" />
    </div>
  );
}

function Representations({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'Mas alla de la geometria de distancias, el ensamble se dispone y describe con representaciones complementarias, todas alineadas curva-a-curva con los miembros comprometidos. El MDS clasico embebe la matriz DTW en 2D/3D preservando distancias; UMAP y t-SNE dan disposiciones de variedad (manifold) que a veces revelan estructura que el MDS lineal comprime.'
        : 'Beyond the distance geometry, the ensemble is laid out and described with complementary representations, all aligned curve-for-curve with the committed members. Classical MDS embeds the DTW matrix in 2D/3D preserving distances; UMAP and t-SNE give manifold layouts that sometimes reveal structure the linear MDS compresses.'}</p>
      <Equation tex="\text{stress} = \sqrt{\frac{\sum_{i<j}\big(\lVert y_i - y_j\rVert - D_{\mathrm{DTW}}(x_i,x_j)\big)^2}{\sum_{i<j} D_{\mathrm{DTW}}(x_i,x_j)^2}}"
        caption={es ? 'Ec. El stress de SMACOF que MDS minimiza: la discrepancia entre las distancias euclidianas en el embedding y las distancias DTW originales.' : 'Eq. The SMACOF stress that MDS minimises: the discrepancy between the Euclidean distances in the embedding and the original DTW distances.'} />
      <p>{es
        ? <>El PCA funcional descompone la matriz de curvas centrada por SVD; los modos propios son las FORMAS dominantes de variacion (interpretables), y las puntuaciones dan un scatter 2D <Cite id="ramsay2005" paren />. Las features catch22 <Cite id="lubba2019" paren /> reducen cada curva a 22 caracteristicas canonicas, agregadas por cluster como una firma interpretable.</>
        : <>Functional PCA decomposes the centred curve matrix by SVD; the eigen-modes are the dominant SHAPES of variation (interpretable), and the scores give a 2D scatter <Cite id="ramsay2005" paren />. The catch22 features <Cite id="lubba2019" paren /> reduce each curve to 22 canonical characteristics, aggregated per cluster as an interpretable signature.</>}</p>
      <Equation tex="X_c = U\,\Sigma\,V^{\top}, \qquad \text{modes} = V^{\top}_{1:m}, \quad \text{scores} = U_{:,1:m}\,\Sigma_{1:m}"
        caption={es ? 'Ec. El PCA funcional por SVD de la matriz de curvas centrada X_c: las filas de V^T son los modos (eigen-formas sobre la grilla log-tiempo), y U*Sigma son las puntuaciones por miembro (m=4 modos comprometidos).' : 'Eq. Functional PCA by SVD of the centred curve matrix X_c: the rows of V^T are the modes (eigen-shapes on the log-time grid), and U*Sigma are the per-member scores (m=4 committed modes).'} />
      <Callout variant="honest" title={es ? 'Distancias UMAP no son metricas' : 'UMAP distances are not metric'}>
        {es ? 'En un grafico UMAP las distancias entre clusters son cualitativas, no una regla; el MDS-DTW sigue siendo la disposicion fiel a la metrica. Se ofrecen ambos y se dice cual es cual.' : 'In a UMAP plot the distances between clusters are qualitative, not a ruler; the DTW-MDS remains the metric-faithful layout. Both are offered and which is which is stated.'}
      </Callout>
      <Refs ids={['mcinnes2018', 'vandermaaten2008', 'ramsay2005', 'lubba2019']} label="Refs" />
    </div>
  );
}

function Diagnostics({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'La capa de diagnostico clasica corre EN VIVO en el navegador (TypeScript puro, sin artefacto horneado) sobre la curva que el usuario ajusta. Detecta y marca los regimenes de flujo en la derivada de Bourdet log-log por su pendiente caracteristica, y ajusta modelos analiticos que RECUPERAN los parametros directamente de la curva.'
        : 'The classical diagnostic layer runs LIVE in the browser (pure TypeScript, no baked artifact) on the curve the user tunes. It auto-detects and marks the flow regimes on the log-log Bourdet derivative by their characteristic slope, and fits analytic models that RECOVER the parameters straight from the curve.'}</p>
      <p>{es
        ? <>Las pendientes canonicas <Cite id="bourdet1989" paren />: flujo radial = plateau en 0.5 (pendiente 0), flujo lineal = 1/2, bilineal = 1/4, limite = pendiente unitaria. El valle de doble porosidad se detecta por VALOR (la derivada bien por debajo de 0.5), no por pendiente, porque sus flancos son empinados.</>
        : <>The canonical slopes <Cite id="bourdet1989" paren />: radial flow = 0.5 plateau (slope 0), linear = 1/2, bilinear = 1/4, boundary = unit slope. The dual-porosity valley is detected by VALUE (the derivative well below 0.5), not by slope, because its flanks are steep.</>}</p>
      <Equation tex="\hat\omega,\hat\lambda = \arg\min_{\omega,\lambda}\; \sum_i \big(\ln p_{wD,i} - \ln \tilde p_{wD}(t_{D,i};\omega,\lambda)\big)^2"
        caption={es ? 'Ec. El ajuste Warren-Root en vivo: recupera (omega, lambda) minimizando el residuo log-presion por una grilla gruesa + refinamiento local, barato por movimiento de slider.' : 'Eq. The live Warren-Root fit: recovers (omega, lambda) by minimising the log-pressure residual via a coarse grid + local refine, cheap per slider move.'} />
      <Equation tex="p_{wD}^{\text{Theis}}(t_D) = \tfrac12\,E_1\!\left(\tfrac{1}{4 t_D}\right) + S, \qquad E_1(u) = \int_u^{\infty}\frac{e^{-\tau}}{\tau}\,d\tau"
        caption={es ? 'Ec. El modelo homogeneo de Theis con skin S (integral exponencial E_1); el modelo de menor RMSE entre Warren-Root y Theis es el que sostienen los datos.' : 'Eq. The homogeneous Theis model with skin S (exponential integral E_1); the lower-RMSE model between Warren-Root and Theis is the one the data supports.'} />
      <Callout variant="honest" title={es ? 'Recuperar lo que fijaste' : 'Recover what you set'}>
        {es ? 'Que el ajuste recupere los valores que el usuario fijo en los sliders es la prueba honesta del ajustador: en una curva limpia recupera omega=0.049 vs 0.050 fijado (RMSE 0.0099), y Theis pierde en una curva de doble porosidad.' : 'That the fit recovers the values the user set on the sliders is the honest test of the fitter: on a clean curve it recovers omega=0.049 vs 0.050 set (RMSE 0.0099), and Theis loses on a dual-porosity curve.'}
      </Callout>
      <Refs ids={['bourdet1989', 'warren1963', 'theis1935']} label="Refs" />
    </div>
  );
}

function LearnedClassifiers({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'El nivel aprendido entrena arquitecturas SOTA en la GPU (torch cu124, .venv-train) y las exporta a ONNX con paridad < 1e-4, para correr EN VIVO en el navegador via onnxruntime-web. Dos clasificadores forman un par CNN-vs-transformer sobre la misma tarea de GeoType.'
        : 'The learned tier trains SOTA architectures on the GPU (torch cu124, .venv-train) and exports them to ONNX with parity < 1e-4, to run LIVE in the browser via onnxruntime-web. Two classifiers form a CNN-vs-transformer pair on the same GeoType task.'}</p>
      <p>{es
        ? <>InceptionTime <Cite id="ismailfawaz2020" paren /> apila modulos Inception (cuello de botella 1x1 + convoluciones paralelas de kernel [9,19,39] + rama de pooling, concatenadas) con atajos residuales cada 3 y pooling promedio global; exactitud held-out 0.911.</>
        : <>InceptionTime <Cite id="ismailfawaz2020" paren /> stacks Inception modules (1x1 bottleneck + parallel convolutions of kernel [9,19,39] + a pooling branch, concatenated) with residual shortcuts every 3 and global average pooling; held-out accuracy 0.911.</>}</p>
      <InceptionSVG es={es} />
      <p>{es
        ? <>PatchTST-lite <Cite id="nie2023" paren /> divide la curva en parches (largo 16, paso 8), los embebe linealmente con un embedding posicional aprendido, y los pasa por un encoder Transformer (d=64, 4 cabezas, 2 capas); es la contraparte transformer de InceptionTime, exactitud 0.902.</>
        : <>PatchTST-lite <Cite id="nie2023" paren /> splits the curve into patches (length 16, stride 8), linearly embeds them with a learned positional embedding, and passes them through a Transformer encoder (d=64, 4 heads, 2 layers); it is the transformer counterpart to InceptionTime, accuracy 0.902.</>}</p>
      <Equation tex="\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{Q K^{\top}}{\sqrt{d_k}}\right) V"
        caption={es ? 'Ec. La auto-atencion escalada del encoder PatchTST: cada parche atiende a todos los parches, capturando dependencias de largo alcance en la forma del transiente.' : 'Eq. The scaled self-attention of the PatchTST encoder: each patch attends to all patches, capturing long-range dependencies in the transient shape.'} />
      <Equation tex="\hat y = \mathrm{softmax}\big(W\,\bar h + b\big), \qquad \bar h = \tfrac{1}{T}\textstyle\sum_t h_t \;\;(\text{InceptionTime, GAP})"
        caption={es ? 'Ec. La cabeza de clasificacion: softmax sobre el pooling promedio global (InceptionTime) o el aplanado de parches (PatchTST). El softmax se aplica en la exportacion, de modo que el navegador lee probabilidades directamente.' : 'Eq. The classification head: softmax over the global average pool (InceptionTime) or the flattened patches (PatchTST). Softmax is applied at export, so the browser reads probabilities directly.'} />
      <Callout variant="honest" title={es ? 'Herramientas, no tabla de metricas' : 'Tools, not a metrics table'}>
        {es ? 'Los modelos aprendidos aparecen como HERRAMIENTAS en vivo (clasifica esta curva), no como una tabla de metricas; la exactitud held-out se muestra junto a la prediccion, y la paridad ONNX-torch se verifica antes de comprometer cada modelo.' : 'The learned models appear as live TOOLS (classify this curve), not a metrics table; the held-out accuracy is shown next to the prediction, and the ONNX-torch parity is verified before each model is committed.'}
      </Callout>
      <Refs ids={['ismailfawaz2020', 'nie2023']} label="Refs" />
    </div>
  );
}

function LearnedRetrieval({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'El segundo par de modelos aprendidos no clasifica sino que detecta anomalias y recupera vecinos. Un autoencoder convolucional profundo comprime la curva a un latente y la reconstruye; el ERROR de reconstruccion es una senal honesta de fuera-de-distribucion: una curva distinta al catalogo de entrenamiento reconstruye mal.'
        : 'The second pair of learned models does not classify but detects anomalies and retrieves neighbours. A deep convolutional autoencoder compresses the curve to a latent and reconstructs it; the reconstruction ERROR is an honest out-of-distribution signal: a curve unlike the training catalogue reconstructs poorly.'}</p>
      <Equation tex="z = \mathrm{enc}(x), \quad \hat x = \mathrm{dec}(z), \qquad \mathcal{E}(x) = \tfrac{1}{N}\lVert x - \hat x\rVert_2^2"
        caption={es ? 'Ec. El autoencoder: el error cuadratico medio de reconstruccion E(x) es el puntaje de anomalia; el latente z (dim 8) es una incrustacion 2D-proyectable del comportamiento.' : 'Eq. The autoencoder: the mean-squared reconstruction error E(x) is the anomaly score; the latent z (dim 8) is a 2D-projectable embedding of behaviour.'} />
      <p>{es
        ? <>El encoder estilo TS2Vec <Cite id="yue2022" paren /> es una red de convoluciones dilatadas entrenada contrastivamente: dos vistas enmascaradas de cada curva deben acercarse (positivas) frente a todas las demas (negativas), con la perdida NT-Xent <Cite id="chen2020" paren />. Da una incrustacion L2-normalizada para recuperacion por vecino mas cercano contra la nube de entrenamiento.</>
        : <>The TS2Vec-style encoder <Cite id="yue2022" paren /> is a dilated-convolution network trained contrastively: two masked views of each curve must be pulled together (positives) against all others (negatives), with the NT-Xent loss <Cite id="chen2020" paren />. It gives an L2-normalised embedding for nearest-neighbour retrieval against the training cloud.</>}</p>
      <Equation tex="\mathcal{L}_{\text{NT-Xent}} = -\log \frac{\exp(\mathrm{sim}(z_i, z_i^+)/\tau)}{\sum_{k\neq i}\exp(\mathrm{sim}(z_i, z_k)/\tau)}, \qquad \tau = 0.2"
        caption={es ? 'Ec. La perdida contrastiva NT-Xent: acerca las dos vistas enmascaradas de la misma curva y aleja las de otras, con temperatura tau=0.2. En inferencia el encoder es una pasada determinista, exportable a ONNX.' : 'Eq. The NT-Xent contrastive loss: pulls the two masked views of the same curve together and pushes others apart, with temperature tau=0.2. At inference the encoder is a deterministic forward pass, ONNX-exportable.'} />
      <Callout variant="honest" title={es ? 'La anomalia no es una etiqueta' : 'Anomaly is not a label'}>
        {es ? 'Un error de reconstruccion alto senala que la curva no se parece a nada del catalogo, no que sea "mala"; se combina con la bandera fuera-de-catalogo del conformal para una decision robusta, y ninguno de los dos se presenta como verdad absoluta.' : 'A high reconstruction error signals that the curve resembles nothing in the catalogue, not that it is "bad"; it combines with the conformal out-of-catalogue flag for a robust decision, and neither is presented as absolute truth.'}
      </Callout>
      <Refs ids={['yue2022', 'chen2020']} label="Refs" />
    </div>
  );
}

function Conformal({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'La asignacion no da solo una etiqueta puntual sino un CONJUNTO de prediccion con garantia de cobertura. La prediccion conformal condicional por clase (Mondrian) calibra, por cada GeoType, las distancias DTW de las curvas de calibracion a su medoide; el p-valor de una curva nueva es su rango entre esas distancias.'
        : 'The assignment gives not just a point label but a prediction SET with a coverage guarantee. Class-conditional (Mondrian) conformal prediction calibrates, per GeoType, the DTW distances of the calibration curves to their medoid; a new curve\'s p-value is its rank among those distances.'}</p>
      <Equation tex="p_g(x) = \frac{1 + \#\{\, i : s_i^{(g)} \ge D_{\mathrm{DTW}}(x, m_g) \,\}}{1 + n_g}, \qquad \Gamma^{\alpha}(x) = \{\, g : p_g(x) > \alpha \,\}"
        caption={es ? 'Ec. El p-valor conformal de la curva x para el GeoType g y el conjunto de prediccion al nivel 1-alpha. Un conjunto vacio es una bandera honesta de fuera-de-catalogo.' : 'Eq. The conformal p-value of curve x for GeoType g and the prediction set at level 1-alpha. An empty set is an honest out-of-catalogue flag.'} />
      <p>{es
        ? <>La cobertura marginal esta garantizada por intercambiabilidad <Cite id="vovk2005" paren /><Cite id="angelopoulos2023" paren />: el conjunto contiene el GeoType verdadero con probabilidad al menos 1-alpha. Esta es la capa NOVEL clasica de Pulso, y corre en vivo en el navegador.</>
        : <>Marginal coverage is guaranteed by exchangeability <Cite id="vovk2005" paren /><Cite id="angelopoulos2023" paren />: the set contains the true GeoType with probability at least 1-alpha. This is Pulso\'s classical NOVEL layer, and it runs live in the browser.</>}</p>
      <p>{es
        ? 'Mas alla de SOTA, la asignacion de doble representacion hace conformal conjuntamente sobre DOS espacios: la forma (distancia DTW) Y los descriptores fisicos (implausibilidad del bosque aleatorio). El conjunto es la interseccion por clase, de modo que una curva de forma correcta pero fisica implausible queda marcada, algo que el conformal de un solo puntaje no puede.'
        : 'Beyond SOTA, the dual-representation assignment conformalizes jointly over TWO spaces: the shape (DTW distance) AND the physical descriptors (random-forest implausibility). The set is the per-class intersection, so a right-shape but implausible-physics curve is flagged, which single-score conformal cannot do.'}</p>
      <Equation tex="\Gamma^{\alpha}_{\text{dual}}(x) = \{\, g : p^{\text{shape}}_g(x) > \alpha \;\wedge\; p^{\text{desc}}_g(x) > \alpha \,\}"
        caption={es ? 'Ec. El conjunto conformal de doble representacion: la conjuncion por clase de los p-valores de forma y de descriptores. Resultado horneado: captura 7/100 (REAL_A) y 55/763 (BENCH_A) curvas forma-correcta-fisica-incorrecta.' : 'Eq. The dual-representation conformal set: the per-class conjunction of the shape and descriptor p-values. Baked result: it catches 7/100 (REAL_A) and 55/763 (BENCH_A) right-shape-wrong-physics curves.'} />
      <DualConformalSVG es={es} />
      <Callout variant="honest" title={es ? 'Cobertura vs conjuntos ajustados' : 'Coverage vs tighter sets'}>
        {es ? 'La conjuncion intercambia un poco de cobertura por conjuntos mas ajustados; ambas cifras (forma-sola vs dual) se muestran lado a lado, y si los descriptores son degenerados la capa dual se reduce honestamente a forma-sola.' : 'The conjunction trades a little coverage for tighter sets; both figures (shape-only vs dual) are shown side by side, and if the descriptors are degenerate the dual layer honestly falls back to shape-only.'}
      </Callout>
      <Refs ids={['vovk2005', 'angelopoulos2023']} label="Refs" />
    </div>
  );
}

function Attribution({ es }: { es: boolean }) {
  return (
    <div>
      <p>{es
        ? 'La atribucion responde por que: mapea las etiquetas GeoType a los descriptores fisicos de la red de fractura (intensidad, apertura, conectividad, fraccion en el componente mayor) con un bosque aleatorio + SHAP, con un gate de exactitud honesto que RETIENE las importancias cuando el bosque no puede predecir las etiquetas.'
        : 'Attribution answers why: it maps the GeoType labels to the physical fracture-network descriptors (intensity, aperture, connectivity, fraction in the largest component) with a random forest + SHAP, with an honest accuracy gate that WITHHOLDS the importances when the forest cannot predict the labels.'}</p>
      <Equation tex="\phi_j = \sum_{S \subseteq F\setminus\{j\}} \frac{|S|!\,(|F|-|S|-1)!}{|F|!}\big[f(S\cup\{j\}) - f(S)\big]"
        caption={es ? 'Ec. El valor de Shapley phi_j del descriptor j: su contribucion marginal promediada sobre todos los subconjuntos, calculado eficientemente por TreeSHAP sobre el bosque.' : 'Eq. The Shapley value phi_j of descriptor j: its marginal contribution averaged over all subsets, computed efficiently by TreeSHAP over the forest.'} />
      <p>{es
        ? <>El bosque aleatorio <Cite id="breiman2001" paren /> se entrena con 200 arboles y hoja minima 2; el gate exige exactitud held-out {'>'} 0.7 (balanceada, para que los GeoTypes minoritarios cuenten). SHAP <Cite id="lundberg2020" paren /> da la importancia por clase, y el ROM barre cada descriptor para medir su sensibilidad de asignacion.</>
        : <>The random forest <Cite id="breiman2001" paren /> is trained with 200 trees and min-leaf 2; the gate requires held-out accuracy {'>'} 0.7 (balanced, so minority GeoTypes count). SHAP <Cite id="lundberg2020" paren /> gives the per-class importance, and the ROM sweeps each descriptor to measure its assignment sensitivity.</>}</p>
      <Equation tex="\mathrm{sens}(j) = \max_g\Big(\max_{v \in [q_5, q_{95}]} P(g\mid x_{-j},x_j{=}v) - \min_{v}\,P(g\mid x_{-j},x_j{=}v)\Big)"
        caption={es ? 'Ec. La sensibilidad ROM del descriptor j: el mayor cambio de probabilidad de cualquier GeoType al barrer j en su rango p5..p95 (dependencia parcial), informativa aun bajo desbalance de clases.' : 'Eq. The ROM sensitivity of descriptor j: the largest change in any GeoType probability when sweeping j across its p5..p95 range (partial dependence), informative even under class imbalance.'} />
      <Callout variant="honest" title={es ? 'Retener es un resultado' : 'Withholding is a result'}>
        {es ? 'Cuando el bosque no supera el gate (la atribucion no es fiable), las importancias se retienen con una nota explicita en vez de reportarse como ruido; un gate cerca de 0.5 es informacion honesta, no una falla que ocultar.' : 'When the forest fails the gate (attribution is not reliable), the importances are withheld with an explicit note instead of being reported as noise; a gate near 0.5 is honest information, not a failure to hide.'}
      </Callout>
      <Refs ids={['breiman2001', 'lundberg2020']} label="Refs" />
    </div>
  );
}

export function Methodology() {
  const es = useShellLang() === 'es';
  const tabs = [
    { id: 'preproc', label: es ? '1. Preproceso' : '1. Preprocessing', content: <Preprocessing es={es} /> },
    { id: 'dtw', label: es ? '2. Distancia DTW' : '2. DTW distance', content: <Distances es={es} /> },
    { id: 'catalogue', label: es ? '3. Catalogo k-medoids' : '3. k-medoids catalogue', content: <Catalogue es={es} /> },
    { id: 'compare', label: es ? '4. Comparacion (SOTA)' : '4. Comparison (SOTA)', content: <ClusteringComparison es={es} /> },
    { id: 'reps', label: es ? '5. Representaciones' : '5. Representations', content: <Representations es={es} /> },
    { id: 'diag', label: es ? '6. Diagnosticos' : '6. Diagnostics', content: <Diagnostics es={es} /> },
    { id: 'learned', label: es ? '7. Clasificadores aprendidos' : '7. Learned classifiers', content: <LearnedClassifiers es={es} /> },
    { id: 'learned2', label: es ? '8. Anomalia + recuperacion' : '8. Anomaly + retrieval', content: <LearnedRetrieval es={es} /> },
    { id: 'conformal', label: es ? '9. Asignacion conformal' : '9. Conformal assignment', content: <Conformal es={es} /> },
    { id: 'attr', label: es ? '10. Atribucion' : '10. Attribution', content: <Attribution es={es} /> },
  ];
  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Metodologia' : 'Methodology'}</h1>
        <p className="lede">
          {es
            ? 'La escalera de metodos, familia por familia: del preproceso y la distancia DTW al catalogo k-medoids, las alternativas SOTA de clustering, las representaciones, los diagnosticos en vivo, el nivel aprendido (GPU a ONNX) y la asignacion conformal con atribucion. Cada familia con su baseline clasico o SOTA y, donde es una capacidad del producto, una capa novel mas alla de SOTA.'
            : 'The method ladder, family by family: from preprocessing and the DTW distance to the k-medoids catalogue, the SOTA clustering alternatives, the representations, the live diagnostics, the learned tier (GPU to ONNX), and conformal assignment with attribution. Each family carries a classical or SOTA baseline and, where it is a product capability, a novel-beyond-SOTA layer.'}
        </p>
      </div>
      <Tabs tabs={tabs} ariaLabel={es ? 'Familias de metodos' : 'Method families'} />
    </div>
  );
}
