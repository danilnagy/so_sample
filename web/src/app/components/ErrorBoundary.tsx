import { Component, type ErrorInfo, type ReactNode } from 'react';

/**
 * The last line of defence: a render error shows a plain message with a reload button
 * instead of a blank page. Nothing is lost: every project and sample lives in the
 * browser's database, which a reload reads again.
 */
export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error): { error: Error } {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('SoSample stopped:', error, info.componentStack);
  }

  render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return (
      <div className="crash" role="alert">
        <strong>SoSample hit a problem and stopped.</strong>
        <p>Your projects and samples are stored on this device and are not affected. Reloading brings them back.</p>
        <pre>{this.state.error.message}</pre>
        <button onClick={() => location.reload()}>Reload</button>
      </div>
    );
  }
}
