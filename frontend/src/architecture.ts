// ADR-0058 architecture-modal tabs for Pulso. Each tab pairs a themed SVG (served from public/svg/tech/,
// fetched + inlined by the shell so it inherits the theme CSS vars) with a bilingual explanation.
//
// NOTE (P0.1): the SVGs under public/svg/tech/ are still the template placeholders; the deep,
// hand-authored Pulso diagrams are authored in P4 (plan phase P4.20). The tab TEXT below is already
// Pulso-specific and honest, so the modal is meaningful now and only the artwork is upgraded later.
import type { ArchTab } from '@fasl-work/caos-app-shell';

export const ARCH_TABS: ArchTab[] = [
  {
    id: 'what',
    en: 'What Pulso is',
    es: 'Que es Pulso',
    body_en:
      'Pulso catalogues pressure-transient flow behaviours over fracture-network ensembles. A well test perturbs a reservoir or aquifer and the pressure response (a pressure pulse) carries the geometry of the flow paths in its SHAPE. Pulso takes an ensemble of such responses, discovers the recurring behaviour types by unsupervised learning, attributes each type to the network properties that drive it, and assigns new curves with a coverage guarantee.\n\n' +
      'It works on any ensemble in this class: your own discrete-fracture-network + flow simulations, real field pumping-test campaigns, or community benchmark corpora.',
    body_es:
      'Pulso cataloga comportamientos de flujo de transitorios de presion sobre ensambles de redes de fracturas. Un ensayo de pozo perturba un reservorio o acuifero y la respuesta de presion (un pulso de presion) lleva la geometría de los caminos de flujo en su FORMA. Pulso toma un ensamble de esas respuestas, descubre los tipos de comportamiento recurrentes con aprendizaje no supervisado, atribuye cada tipo a las propiedades de la red que lo controlan, y asigna curvas nuevas con una garantia de cobertura.\n\n' +
      'Funciona con cualquier ensamble de esta clase: tus propias simulaciones de redes discretas de fracturas + flujo, campanas reales de ensayos de bombeo, o corpus de referencia comunitarios.',
    svg: 'svg/tech/01-the-app.svg',
  },
  {
    id: 'lanes',
    en: 'The lanes: web vs offline',
    es: 'Los carriles: web vs offline',
    body_en:
      'Three compute lanes. offline (heavy, precomputed): GeoDFN generates geologically consistent networks, open-DARTS simulates their pressure transients, the shape distances (DTW) and clustering (k-medoids and the wider ladder) build the catalogue, and the learned models are trained on the GPU. LIVE (in the browser): the classical diagnostics and the shape/assignment tools run in a TypeScript engine, and the learned models run via onnxruntime-web on the ONNX exported offline. REPLAY: the committed, decimated ensemble artifacts drive every view.\n\n' +
      'Nothing heavy runs on a server; the site is static. The offline lane bakes the artifacts; the browser replays them and runs the learned inference live.',
    body_es:
      'Tres carriles de computo. offline (pesado, precomputado): GeoDFN genera redes geologicamente consistentes, open-DARTS simula sus transitorios de presion, las distancias de forma (DTW) y el agrupamiento (k-medoids y la escalera mas amplia) construyen el catalogo, y los modelos aprendidos se entrenan en la GPU. EN VIVO (en el navegador): los diagnosticos clásicos y las herramientas de forma/asignacion corren en un motor TypeScript, y los modelos aprendidos corren con onnxruntime-web sobre el ONNX exportado offline. REPLAY: los artefactos del ensamble, decimados y comprometidos, alimentan cada vista.\n\n' +
      'Nada pesado corre en un servidor; el sitio es estático. El carril offline hornea los artefactos; el navegador los reproduce y corre la inferencia aprendida en vivo.',
    svg: 'svg/tech/02-lanes.svg',
  },
  {
    id: 'web',
    en: 'The web-app flow',
    es: 'El flujo de la web',
    body_en:
      'The build overlays the committed artifacts (data/derived, models) into the static bundle. The React SPA loads an ensemble case, reads its full-ensemble artifact (every curve decimated, cluster labels, network geometries, the DTW/MDS embeddings, attribution tables, conformal calibration), and renders the workbench: an ensemble curve explorer, per-cluster panels with network thumbnails, property distributions, the shape-space map, cross-ensemble stability, the attribution studio, and the diagnostic bench. Every view is linked-brushed and reacts to the selected case and controls.',
    body_es:
      'El build superpone los artefactos comprometidos (data/derived, models) en el paquete estático. La SPA React carga un caso de ensamble, lee su artefacto de ensamble completo (cada curva decimada, etiquetas de cluster, geometrias de red, los embeddings DTW/MDS, tablas de atribucion, calibracion conforme), y renderiza el workbench: un explorador de curvas del ensamble, paneles por cluster con miniaturas de red, distribuciones de propiedades, el mapa del espacio de formas, la estabilidad entre ensambles, el estudio de atribucion, y el banco de diagnostico. Cada vista esta enlazada por brushing y reacciona al caso seleccionado y a los controles.',
    svg: 'svg/tech/03-web-flow.svg',
  },
  {
    id: 'science',
    en: 'The method ladder',
    es: 'La escalera de métodos',
    body_en:
      'The scientific core is a deep method ladder, classical to SOTA. Diagnostics: Bourdet derivative + flow-regime detection, Warren-Root and Theis fits, deconvolution. Distances and clustering: DTW + PAM (FasterPAM), soft-DTW barycenters, k-Shape, hierarchical, spectral, HDBSCAN. Representations: classical MDS, UMAP, t-SNE, functional PCA, catch22 features. Learned (GPU to ONNX): an InceptionTime classifier, a convolutional autoencoder for out-of-distribution scoring, a contrastive encoder for retrieval, a patch-transformer. Attribution: Random Forest + SHAP with an accuracy gate. Assignment: split-conformal prediction (and a class-conditional variant).',
    body_es:
      'El nucleo cientifico es una escalera profunda de métodos, de clásico a SOTA. Diagnosticos: derivada de Bourdet + detección de regímenes de flujo, ajustes Warren-Root y Theis, deconvolucion. Distancias y agrupamiento: DTW + PAM (FasterPAM), baricentros soft-DTW, k-Shape, jerarquico, espectral, HDBSCAN. Representaciones: MDS clásico, UMAP, t-SNE, PCA funcional, features catch22. Aprendidos (GPU a ONNX): un clasificador InceptionTime, un autoencoder convolucional para puntuar fuera de distribución, un encoder contrastivo para recuperacion, un transformer de parches. Atribucion: Random Forest + SHAP con un gate de exactitud. Asignacion: prediccion split-conforme (y una variante condicional por clase).',
    svg: 'svg/tech/04-the-science.svg',
  },
  {
    id: 'contracts',
    en: 'The data contracts',
    es: 'Los contratos de datos',
    body_en:
      'Two contracts keep the offline pipeline and the web app in lock-step. CONTRACT-1 validates the input curves (finite, positive time, real response span) before anything is baked. CONTRACT-3 is the committed full-ensemble artifact per case: every member curve (decimated min/max-per-pixel), cluster labels and per-cluster quantile envelopes, decimated network geometries with their properties (including the set type), the cluster-ordered DTW matrix, the MDS 2D/3D coordinates, the attribution tables, and the conformal calibration. A TypeScript mirror of the schema makes any drift fail the build.',
    body_es:
      'Dos contratos mantienen el pipeline offline y la web en sincronia. CONTRACT-1 valida las curvas de entrada (finitas, tiempo positivo, rango de respuesta real) antes de hornear nada. CONTRACT-3 es el artefacto de ensamble completo comprometido por caso: cada curva miembro (decimada min/max por pixel), etiquetas de cluster y envolventes de cuantiles por cluster, geometrias de red decimadas con sus propiedades (incluido el tipo de set), la matriz DTW ordenada por cluster, las coordenadas MDS 2D/3D, las tablas de atribucion, y la calibracion conforme. Un espejo TypeScript del esquema hace que cualquier desvio rompa el build.',
    svg: 'svg/tech/05-data-contracts.svg',
  },
];
