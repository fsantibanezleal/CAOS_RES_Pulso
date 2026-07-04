// Per-panel error boundary: a single bad case/panel must not blank the whole app (a bug this
// discipline exists to prevent). Renders a small inline notice instead.
import { Component, type ReactNode } from 'react';

export class ErrorBoundary extends Component<{ children: ReactNode; label?: string }, { err: Error | null }> {
  state = { err: null as Error | null };
  static getDerivedStateFromError(err: Error) {
    return { err };
  }
  render() {
    if (this.state.err) {
      return (
        <div className="panel" style={{ borderColor: 'var(--bad)' }}>
          <b style={{ color: 'var(--bad)' }}>{this.props.label ?? 'panel'} failed to render</b>
          <p className="muted" style={{ fontSize: '.85rem', margin: '.4rem 0 0' }}>{String(this.state.err.message)}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
