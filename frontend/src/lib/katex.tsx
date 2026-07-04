// KaTeX render helpers (inline + block). Equations are authored once and rendered client-side.
import katex from 'katex';
import 'katex/dist/katex.min.css';

export function TeX({ children, block = false }: { children: string; block?: boolean }) {
  const html = katex.renderToString(children, { displayMode: block, throwOnError: false });
  return block ? (
    <div className="katex-block" dangerouslySetInnerHTML={{ __html: html }} />
  ) : (
    <span dangerouslySetInnerHTML={{ __html: html }} />
  );
}
