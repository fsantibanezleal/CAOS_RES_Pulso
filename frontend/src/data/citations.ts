// The single citation registry (ADR-0017 section 4). id = authorYYYY[suffix], lowercase, no spaces.
// EVERY entry carries a real, verifiable doi (preferred) or url; a bare author-year with no link is a
// FAIL. Mounted once via <CitationsProvider items={CITATIONS}> at the root; cited inline with
// <Cite id/> and per-section with <Refs ids={[...]}/>. No bottom-of-page bibliography dump.
import type { Citation } from '@fasl-work/caos-app-shell';

export const CITATIONS: Citation[] = [
  // --- pressure-transient analysis + the diagnostic derivative ---
  { id: 'bourdet1989', label: 'Bourdet et al. 1989',
    citation: 'D. Bourdet, J. A. Ayoub, Y. M. Pirard. Use of Pressure Derivative in Well Test Interpretation. SPE Formation Evaluation 4(2), 293-302, 1989.',
    doi: '10.2118/12777-PA' },
  { id: 'warren1963', label: 'Warren & Root 1963',
    citation: 'J. E. Warren, P. J. Root. The Behavior of Naturally Fractured Reservoirs. SPE Journal 3(3), 245-255, 1963.',
    doi: '10.2118/426-PA' },
  { id: 'theis1935', label: 'Theis 1935',
    citation: 'C. V. Theis. The relation between the lowering of the piezometric surface and the rate and duration of discharge of a well using ground-water storage. Transactions AGU 16(2), 519-524, 1935.',
    doi: '10.1029/TR016i002p00519' },
  { id: 'gringarten2008', label: 'Gringarten 2008',
    citation: 'A. C. Gringarten. From Straight Lines to Deconvolution: The Evolution of the State of the Art in Well Test Analysis. SPE Reservoir Evaluation & Engineering 11(1), 41-62, 2008.',
    doi: '10.2118/102079-PA' },

  // --- the source problem class: DFN flow-behaviour clustering ---
  { id: 'kameltarghi2026', label: 'Kamel Targhi et al. 2026',
    citation: 'M. Kamel Targhi et al. Clustering flow behaviour in discrete fracture network ensembles from pressure-transient signatures. Computational Geosciences 30:57, 2026.',
    doi: '10.1007/s10596-026-10459-w' },

  // --- distances + clustering ---
  { id: 'sakoe1978', label: 'Sakoe & Chiba 1978',
    citation: 'H. Sakoe, S. Chiba. Dynamic programming algorithm optimization for spoken word recognition. IEEE Transactions on Acoustics, Speech, and Signal Processing 26(1), 43-49, 1978.',
    doi: '10.1109/TASSP.1978.1163055' },
  { id: 'kaufman1990', label: 'Kaufman & Rousseeuw 1990',
    citation: 'L. Kaufman, P. J. Rousseeuw. Finding Groups in Data: An Introduction to Cluster Analysis. Wiley, 1990.',
    doi: '10.1002/9780470316801' },
  { id: 'cuturi2017', label: 'Cuturi & Blondel 2017',
    citation: 'M. Cuturi, M. Blondel. Soft-DTW: a Differentiable Loss Function for Time-Series. ICML 2017.',
    url: 'https://arxiv.org/abs/1703.01541' },
  { id: 'paparrizos2015', label: 'Paparrizos & Gravano 2015',
    citation: 'J. Paparrizos, L. Gravano. k-Shape: Efficient and Accurate Clustering of Time Series. ACM SIGMOD 2015, 1855-1870.',
    doi: '10.1145/2723372.2737793' },
  { id: 'vonluxburg2007', label: 'von Luxburg 2007',
    citation: 'U. von Luxburg. A Tutorial on Spectral Clustering. Statistics and Computing 17(4), 395-416, 2007.',
    doi: '10.1007/s11222-007-9033-z' },
  { id: 'campello2013', label: 'Campello et al. 2013',
    citation: 'R. J. G. B. Campello, D. Moulavi, J. Sander. Density-Based Clustering Based on Hierarchical Density Estimates. PAKDD 2013, 160-172.',
    doi: '10.1007/978-3-642-37456-2_14' },

  // --- representations ---
  { id: 'mcinnes2018', label: 'McInnes et al. 2018',
    citation: 'L. McInnes, J. Healy, J. Melville. UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. arXiv:1802.03426, 2018.',
    url: 'https://arxiv.org/abs/1802.03426' },
  { id: 'vandermaaten2008', label: 'van der Maaten & Hinton 2008',
    citation: 'L. van der Maaten, G. Hinton. Visualizing Data using t-SNE. Journal of Machine Learning Research 9, 2579-2605, 2008.',
    url: 'https://www.jmlr.org/papers/v9/vandermaaten08a.html' },
  { id: 'ramsay2005', label: 'Ramsay & Silverman 2005',
    citation: 'J. O. Ramsay, B. W. Silverman. Functional Data Analysis, 2nd ed. Springer, 2005.',
    doi: '10.1007/b98888' },
  { id: 'lubba2019', label: 'Lubba et al. 2019',
    citation: 'C. H. Lubba, S. S. Sethi, P. Knaute, S. R. Schultz, B. D. Fulcher, N. S. Jones. catch22: CAnonical Time-series CHaracteristics. Data Mining and Knowledge Discovery 33, 1821-1852, 2019.',
    doi: '10.1007/s10618-019-00647-x' },

  // --- learned tier ---
  { id: 'ismailfawaz2020', label: 'Ismail Fawaz et al. 2020',
    citation: 'H. Ismail Fawaz et al. InceptionTime: Finding AlexNet for Time Series Classification. Data Mining and Knowledge Discovery 34, 1936-1962, 2020.',
    doi: '10.1007/s10618-020-00710-y' },
  { id: 'nie2023', label: 'Nie et al. 2023',
    citation: 'Y. Nie, N. H. Nguyen, P. Sinthong, J. Kalagnanam. A Time Series is Worth 64 Words: Long-term Forecasting with Transformers (PatchTST). ICLR 2023.',
    url: 'https://arxiv.org/abs/2211.14730' },
  { id: 'yue2022', label: 'Yue et al. 2022',
    citation: 'Z. Yue et al. TS2Vec: Towards Universal Representation of Time Series. AAAI 2022, 8980-8987.',
    doi: '10.1609/aaai.v36i8.20881' },
  { id: 'chen2020', label: 'Chen et al. 2020',
    citation: 'T. Chen, S. Kornblith, M. Norouzi, G. Hinton. A Simple Framework for Contrastive Learning of Visual Representations (SimCLR / NT-Xent). ICML 2020.',
    url: 'https://arxiv.org/abs/2002.05709' },

  // --- conformal + attribution ---
  { id: 'vovk2005', label: 'Vovk et al. 2005',
    citation: 'V. Vovk, A. Gammerman, G. Shafer. Algorithmic Learning in a Random World. Springer, 2005.',
    doi: '10.1007/b106715' },
  { id: 'angelopoulos2023', label: 'Angelopoulos & Bates 2023',
    citation: 'A. N. Angelopoulos, S. Bates. Conformal Prediction: A Gentle Introduction. Foundations and Trends in Machine Learning 16(4), 494-591, 2023.',
    doi: '10.1561/2200000101' },
  { id: 'breiman2001', label: 'Breiman 2001',
    citation: 'L. Breiman. Random Forests. Machine Learning 45, 5-32, 2001.',
    doi: '10.1023/A:1010933404324' },
  { id: 'lundberg2020', label: 'Lundberg et al. 2020',
    citation: 'S. M. Lundberg et al. From local explanations to global understanding with explainable AI for trees. Nature Machine Intelligence 2, 56-67, 2020.',
    doi: '10.1038/s42256-019-0138-9' },

  // --- simulation engines ---
  { id: 'khait2018', label: 'Khait & Voskov 2018 (open-DARTS)',
    citation: 'M. Khait, D. Voskov. Operator-based linearization for general purpose reservoir simulation (open-DARTS). Journal of Petroleum Science and Engineering 170, 779-791, 2018.',
    doi: '10.1016/j.petrol.2018.06.072' },
  { id: 'lei2017', label: 'Lei et al. 2017 (DFN review)',
    citation: 'Q. Lei, J.-P. Latham, C.-F. Tsang. The use of discrete fracture networks for modelling coupled geomechanical and hydrological behaviour of fractured rocks. Computers and Geotechnics 85, 151-176, 2017.',
    doi: '10.1016/j.compgeo.2016.12.024' },
];
