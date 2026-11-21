import { Badge } from "@/components/ui/badge";
import {
  STATUS_LABEL,
  URGENCY_CLASS,
  URGENCY_LABEL,
  type Urgency,
} from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * Warianty ciemne dla oznaczeń pilności.
 *
 * `URGENCY_CLASS` w `lib/format.ts` jest zamrożony i opisuje tylko motyw jasny.
 * W ciemnym jasne tło z ciemnym tekstem byłoby czytelne, ale rażąco odstawało
 * od reszty interfejsu — dlatego dokładamy odpowiedniki o tym samym kontraście.
 */
const URGENCY_DARK: Record<Urgency, string> = {
  overdue: "dark:bg-red-950 dark:text-red-200 dark:border-red-800",
  today: "dark:bg-orange-950 dark:text-orange-200 dark:border-orange-800",
  tomorrow: "dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800",
  soon: "dark:bg-yellow-950 dark:text-yellow-200 dark:border-yellow-800",
  normal: "dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800",
  closed: "dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
};

export function UrgencyBadge({
  urgency,
  days,
}: {
  urgency: Urgency;
  days?: number;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "whitespace-nowrap",
        URGENCY_CLASS[urgency],
        URGENCY_DARK[urgency],
      )}
    >
      {URGENCY_LABEL[urgency]}
      {typeof days === "number" && urgency !== "closed" ? ` · ${days} d` : null}
    </Badge>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="secondary" className="whitespace-nowrap">
      {STATUS_LABEL[status] ?? status}
    </Badge>
  );
}
