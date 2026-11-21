import { format } from "date-fns";
import { pl } from "date-fns/locale";
import { useMemo, useRef } from "react";

import { EmptyState } from "@/components/States";
import { StatusBadge, UrgencyBadge } from "@/components/StatusBadges";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { groupByDeadline } from "@/features/calendar/derive";
import { t } from "@/features/calendar/i18n";
import { formatShortDate } from "@/lib/format";
import type { Case } from "@/lib/types";

type DayDialogProps = {
  day: Date | null;
  cases: Case[];
  onClose: () => void;
  onSelectCase: (caseId: string) => void;
};

export function DayDialog({ day, cases, onClose, onSelectCase }: DayDialogProps) {
  // Podczas animacji zamykania `day` jest już puste — trzymamy ostatni dzień,
  // żeby lista nie mrugnęła pustym stanem.
  const lastDay = useRef<Date | null>(null);
  if (day) lastDay.current = day;
  const shownDay = day ?? lastDay.current;

  const dayCases = useMemo(() => {
    if (!shownDay) return [];
    return groupByDeadline(cases).get(format(shownDay, "yyyy-MM-dd")) ?? [];
  }, [cases, shownDay]);

  return (
    <Dialog
      open={day !== null}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {shownDay ? t.day.title(shownDay) : t.day.description}
          </DialogTitle>
          <DialogDescription>{t.day.description}</DialogDescription>
        </DialogHeader>

        {dayCases.length === 0 ? (
          <EmptyState title={t.day.empty} />
        ) : (
          <ul className="space-y-2">
            {dayCases.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => onSelectCase(item.id)}
                  className="flex w-full flex-col gap-2 rounded-lg border p-3 text-left transition-colors hover:bg-accent"
                >
                  <span className="text-sm font-medium">{item.subject}</span>
                  <span className="text-xs text-muted-foreground">
                    {item.case_number} · wpływ {formatShortDate(item.inflow_date)} ·
                    termin {formatShortDate(item.deadline)}
                  </span>
                  <span className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={item.status} />
                    <UrgencyBadge
                      urgency={item.urgency}
                      days={item.days_remaining}
                    />
                    <span className="text-xs text-muted-foreground">
                      {t.day.open}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {shownDay ? (
          <p className="text-xs text-muted-foreground">
            {format(shownDay, "EEEE, d MMMM yyyy", { locale: pl })}
          </p>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
