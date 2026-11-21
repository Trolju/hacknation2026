import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import { apiErrorMessage, apiErrorTitle } from "@/components/errorMessages";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export type LoadingVariant = "table" | "cards" | "list" | "text";

/**
 * Szkielet ładowania. Kształt naśladuje to, co pojawi się po odpowiedzi
 * serwera, więc układ nie „przeskakuje” po dociągnięciu danych.
 */
export function LoadingState({
  rows = 3,
  variant = "table",
  label = "Ładowanie danych…",
}: {
  rows?: number;
  variant?: LoadingVariant;
  label?: string;
}) {
  return (
    <div aria-busy="true" aria-live="polite" role="status">
      <span className="sr-only">{label}</span>
      {variant === "table" ? (
        <div className="overflow-hidden rounded-lg border">
          <div className="flex items-center gap-4 border-b bg-muted/40 px-3 py-3">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-40" />
            <Skeleton className="ml-auto h-3 w-16" />
          </div>
          <div className="divide-y">
            {Array.from({ length: rows }).map((_, index) => (
              <div key={index} className="flex items-center gap-4 px-3 py-3">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {variant === "cards" ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: rows }).map((_, index) => (
            <div key={index} className="space-y-3 rounded-lg border p-4">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-8 w-16" />
            </div>
          ))}
        </div>
      ) : null}

      {variant === "list" ? (
        <div className="space-y-2">
          {Array.from({ length: rows }).map((_, index) => (
            <Skeleton key={index} className="h-14 w-full" />
          ))}
        </div>
      ) : null}

      {variant === "text" ? (
        <div className="space-y-2">
          {Array.from({ length: rows }).map((_, index) => (
            <Skeleton
              key={index}
              className={cn("h-4", index === rows - 1 ? "w-2/3" : "w-full")}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function InlineSpinner({ label }: { label?: string }) {
  return (
    <span
      role="status"
      className="inline-flex items-center gap-2 text-sm text-muted-foreground"
    >
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      {label ?? "Ładowanie…"}
    </span>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed px-4 py-12 text-center">
      <span className="text-muted-foreground" aria-hidden="true">
        {icon ?? <Inbox className="h-8 w-8" />}
      </span>
      <p className="font-medium">{title}</p>
      {description ? (
        <p className="max-w-md text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action}
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
  title,
  compact = false,
}: {
  error: unknown;
  onRetry?: () => void;
  title?: string;
  compact?: boolean;
}) {
  return (
    <Alert variant="destructive" className={cn(compact && "py-2")}>
      <AlertTriangle className="h-4 w-4" aria-hidden="true" />
      <AlertTitle>{title ?? apiErrorTitle(error)}</AlertTitle>
      <AlertDescription className="flex flex-col gap-2">
        <span>{apiErrorMessage(error)}</span>
        {onRetry ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="w-fit"
          >
            Spróbuj ponownie
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}
