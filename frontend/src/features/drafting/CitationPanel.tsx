/** Panel cytowań — numer, etykieta, źródło i fragment tekstu. */

import { useEffect, useRef } from "react";

import { Badge } from "@/components/ui/badge";
import { SOURCE_CLASS, SOURCE_LABEL, TEXT } from "@/features/drafting/i18n";
import type { Citation } from "@/lib/types";
import { cn } from "@/lib/utils";

type CitationPanelProps = {
  citations: Citation[];
  activeRef: number | null;
  onSelect: (ref: number) => void;
};

export function CitationPanel({ citations, activeRef, onSelect }: CitationPanelProps) {
  const items = useRef(new Map<number, HTMLButtonElement>());

  useEffect(() => {
    if (activeRef === null) return;
    items.current.get(activeRef)?.scrollIntoView({ block: "nearest" });
  }, [activeRef]);

  if (citations.length === 0) {
    return <p className="text-sm text-muted-foreground">{TEXT.citationsEmpty}</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">{TEXT.citationsHint}</p>
      <ol className="space-y-2">
        {citations.map((citation) => (
          <li key={`${citation.source_type}-${citation.source_id}-${citation.ref}`}>
            <button
              type="button"
              ref={(node) => {
                if (node) items.current.set(citation.ref, node);
                else items.current.delete(citation.ref);
              }}
              onClick={() => onSelect(citation.ref)}
              aria-current={activeRef === citation.ref ? "true" : undefined}
              className={cn(
                "w-full rounded-lg border p-2.5 text-left transition-colors hover:bg-muted/60",
                activeRef === citation.ref && "border-primary bg-primary/5 ring-1 ring-primary",
              )}
            >
              <div className="flex items-center gap-2">
                <span className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded bg-muted px-1 text-xs font-semibold tabular-nums">
                  {citation.ref}
                </span>
                <Badge
                  variant="outline"
                  className={cn("whitespace-nowrap", SOURCE_CLASS[citation.source_type])}
                >
                  {SOURCE_LABEL[citation.source_type]}
                </Badge>
              </div>
              <p className="mt-1.5 text-sm font-medium leading-snug">{citation.label}</p>
              {citation.excerpt ? (
                <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">
                  {citation.excerpt}
                </p>
              ) : null}
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}
