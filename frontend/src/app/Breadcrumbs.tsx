import { ChevronRight, House } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { buildBreadcrumbs } from "@/app/breadcrumbs";
import { visibleFeatures } from "@/app/registry";
import { cn } from "@/lib/utils";

/** Ścieżka nawigacji w nagłówku — wyliczana z adresu i rejestru ekranów. */
export function Breadcrumbs({ className }: { className?: string }) {
  const { pathname } = useLocation();
  const crumbs = buildBreadcrumbs(pathname, visibleFeatures);

  return (
    <nav aria-label="Ścieżka nawigacji" className={cn("min-w-0", className)}>
      <ol className="flex items-center gap-1 text-sm text-muted-foreground">
        {crumbs.map((crumb, index) => {
          const last = index === crumbs.length - 1;
          return (
            <li
              key={`${crumb.label}-${index}`}
              className="flex min-w-0 items-center gap-1"
            >
              {index > 0 ? (
                <ChevronRight
                  className="h-3.5 w-3.5 shrink-0 opacity-60"
                  aria-hidden="true"
                />
              ) : null}
              {crumb.to && !last ? (
                <Link
                  to={crumb.to}
                  className="flex items-center gap-1 rounded px-1 py-0.5 hover:text-foreground"
                >
                  <House className="h-3.5 w-3.5" aria-hidden="true" />
                  <span className="truncate">{crumb.label}</span>
                </Link>
              ) : (
                <span
                  aria-current={last ? "page" : undefined}
                  className={cn(
                    "truncate",
                    last && "font-medium text-foreground",
                  )}
                >
                  {crumb.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
