// The five detailed prose pages (Introduction / Methodology / Implementation / Experiments /
// Benchmark). Prose + KaTeX + DOI refs, driven by the i18n dict — never card grids (ADR-0016).
import { useEffect, useState } from 'react';
import { TeX } from '../lib/katex';
import { useT } from '../i18n/useT';
import { loadIndex, loadManifest } from '../api/artifacts';
import type { CaseIndex, CaseManifest } from '../lib/contract.types';

export function Introduction() {
  const t = useT();
  return (
    <article className="prose">
      <h1>{t.intro.title}</h1>
      <p style={{ fontSize: '1.05rem' }}>{t.intro.lead}</p>
      <h2>{t.intro.s1h}</h2>
      <p>{t.intro.s1}</p>
      <h2>{t.intro.s2h}</h2>
      <p>{t.intro.s2}</p>
      <h2>{t.intro.s3h}</h2>
      <p>{t.intro.s3}</p>
      <h2>{t.intro.sourceh}</h2>
      <p className="ref">
        {t.intro.source}{' '}
        <a href="https://doi.org/10.1007/s10596-026-10459-w" target="_blank" rel="noreferrer">
          DOI 10.1007/s10596-026-10459-w
        </a>
        .
      </p>
    </article>
  );
}

export function Methodology() {
  const t = useT();
  const refs = [
    ['Bourdet, Ayoub & Pirard (1989), SPE Formation Evaluation 4(2)', '10.2118/12777-PA'],
    ['Warren & Root (1963), SPE Journal 3(3)', '10.2118/426-PA'],
    ['Sakoe & Chiba (1978), IEEE TASSP 26(1)', '10.1109/TASSP.1978.1163055'],
    ['Kaufman & Rousseeuw (1990), Finding Groups in Data', '10.1002/9780470316801'],
    ['Angelopoulos & Bates (2023), Found. Trends ML 16(4)', '10.1561/2200000101'],
    ['Lundberg et al. (2020), Nature Machine Intelligence 2', '10.1038/s42256-019-0138-9'],
    ['Kamel Targhi et al. (2026), Computational Geosciences 30:57', '10.1007/s10596-026-10459-w'],
  ];
  return (
    <article className="prose">
      <h1>{t.method.title}</h1>
      <p style={{ fontSize: '1.05rem' }}>{t.method.lead}</p>
      <h2>{t.method.s1h}</h2>
      <p>{t.method.s1}</p>
      <h2>{t.method.s2h}</h2>
      <p>{t.method.s2}</p>
      <TeX block>{t.method.dtw}</TeX>
      <h2>{t.method.s3h}</h2>
      <p>{t.method.s3}</p>
      <h2>{t.method.s4h}</h2>
      <p>{t.method.s4}</p>
      <TeX block>{t.method.conf}</TeX>
      <h2>{t.method.s5h}</h2>
      <p>{t.method.s5}</p>
      <h2>{t.method.s6h}</h2>
      <p>{t.method.s6}</p>
      <h2>{t.method.refh}</h2>
      <ul className="ref">
        {refs.map(([txt, doi]) => (
          <li key={doi}>
            {txt} · <a href={`https://doi.org/${doi}`} target="_blank" rel="noreferrer">DOI {doi}</a>
          </li>
        ))}
      </ul>
    </article>
  );
}

export function Implementation() {
  const t = useT();
  const S = ({ h, p }: { h: string; p: string }) => (
    <>
      <h2>{h}</h2>
      <p>{p}</p>
    </>
  );
  return (
    <article className="prose">
      <h1>{t.impl.title}</h1>
      <p style={{ fontSize: '1.05rem' }}>{t.impl.lead}</p>
      <S h={t.impl.lanesh} p={t.impl.lanes} />
      <S h={t.impl.stagesh} p={t.impl.stages} />
      <S h={t.impl.contractsh} p={t.impl.contracts} />
      <S h={t.impl.stackh} p={t.impl.stack} />
    </article>
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
    return () => {
      alive = false;
    };
  }, []);
  return rows;
}

export function Experiments() {
  const t = useT();
  const rows = useManifests();
  const studies = rows.filter((m) => m.artifact.trace_schema.startsWith('flowdna.trace/'));
  const num = (m: CaseManifest, k: string) => {
    const v = (m.metrics as Record<string, unknown>)[k];
    return typeof v === 'number' ? v.toFixed(3) : '—';
  };
  return (
    <article className="prose" style={{ maxWidth: 940 }}>
      <h1>{t.exp.title}</h1>
      <p style={{ fontSize: '1.05rem' }}>{t.exp.lead}</p>
      <h2>{t.exp.studies}</h2>
      <div className="scroll-x">
        <table>
          <thead>
            <tr>
              <th>case</th>
              <th>K</th>
              <th>{t.common.silhouette}</th>
              <th>{t.common.coverage}</th>
              <th>{t.common.oodRate}</th>
            </tr>
          </thead>
          <tbody>
            {studies.map((m) => {
              const conf = (m.metrics as { conformal?: Record<string, number> }).conformal ?? {};
              return (
                <tr key={m.case_id}>
                  <td>{m.case_id}</td>
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
      <h2>{t.exp.findingsh}</h2>
      <ul>
        <li>{t.exp.f1}</li>
        <li>{t.exp.f2}</li>
        <li>{t.exp.f3}</li>
      </ul>
    </article>
  );
}

export function Benchmark() {
  const t = useT();
  const S = ({ h, p }: { h: string; p: string }) => (
    <>
      <h2>{h}</h2>
      <p>{p}</p>
    </>
  );
  return (
    <article className="prose">
      <h1>{t.bench.title}</h1>
      <p style={{ fontSize: '1.05rem' }}>{t.bench.lead}</p>
      <S h={t.bench.crossh} p={t.bench.cross} />
      <S h={t.bench.kh} p={t.bench.k} />
      <S h={t.bench.engineh} p={t.bench.engine} />
    </article>
  );
}
