/** Ostrzeżenia o twierdzeniach bez pokrycia w źródłach. */

import { AlertTriangle, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { TEXT } from "@/features/drafting/i18n";

export type UnsupportedItem = {
  claim: string;
  /** Nagłówek sekcji, w której pada twierdzenie; `null`, gdy nie da się go wskazać. */
  section: string | null;
};

type UnsupportedPanelProps = {
  items: UnsupportedItem[];
  onGoTo: (section: string) => void;
};

export function UnsupportedPanel({ items, onGoTo }: UnsupportedPanelProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">{TEXT.unsupportedHint}</p>
      <ul className="space-y-2">
        {items.map((item) => {
          const section = item.section;
          return (
            <li
              key={item.claim}
              className="rounded-lg border border-amber-200 bg-amber-50/60 p-2.5 text-sm"
            >
              <div className="flex gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                <p className="leading-snug text-amber-950">{item.claim}</p>
              </div>
              {section ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="mt-1 h-7 px-2 text-xs text-amber-900 hover:bg-amber-100"
                  onClick={() => onGoTo(section)}
                >
                  {TEXT.unsupportedGoTo}
                  <ArrowRight className="ml-1 h-3.5 w-3.5" />
                </Button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
