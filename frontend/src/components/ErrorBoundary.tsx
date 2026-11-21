import { AlertTriangle, RotateCcw } from "lucide-react";
import { Component, type ErrorInfo, type ReactNode } from "react";

import { Button } from "@/components/ui/button";

type ErrorBoundaryProps = {
  children: ReactNode;
  /** Własny widok awarii; domyślnie pełnoekranowy panel z przyciskiem „Odśwież”. */
  fallback?: (error: Error, reset: () => void) => ReactNode;
  /** Krótki opis miejsca, żeby komunikat mówił, co padło. */
  scope?: string;
};

type ErrorBoundaryState = { error: Error | null };

/**
 * Granica błędu — łapie wyjątki z drzewa Reacta, których nie obsłużył
 * TanStack Query, i pokazuje komunikat zamiast pustej strony.
 *
 * Musi być klasą: React nie udostępnia odpowiednika w API hooków.
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Nieobsłużony błąd interfejsu", error, info.componentStack);
  }

  private reset = (): void => {
    this.setState({ error: null });
  };

  private reload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;
    if (this.props.fallback) return this.props.fallback(error, this.reset);

    return (
      <div
        role="alert"
        className="mx-auto flex max-w-xl flex-col items-center gap-4 rounded-lg border border-destructive/40 bg-destructive/5 p-6 text-center"
      >
        <AlertTriangle className="h-8 w-8 text-destructive" aria-hidden="true" />
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">Ekran nie mógł się wyświetlić</h2>
          <p className="text-sm text-muted-foreground">
            {this.props.scope
              ? `Wystąpił nieoczekiwany błąd w sekcji „${this.props.scope}”.`
              : "Wystąpił nieoczekiwany błąd interfejsu."}{" "}
            Odśwież stronę, żeby wrócić do pracy. Zapisane dane nie zostały
            utracone.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          <Button type="button" onClick={this.reload}>
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            Odśwież
          </Button>
          <Button type="button" variant="outline" onClick={this.reset}>
            Spróbuj ponownie
          </Button>
        </div>
        <details className="w-full text-left">
          <summary className="cursor-pointer text-xs text-muted-foreground">
            Szczegóły techniczne
          </summary>
          <pre className="mt-2 max-h-40 overflow-auto rounded bg-muted p-2 text-xs">
            {error.message}
          </pre>
        </details>
      </div>
    );
  }
}
