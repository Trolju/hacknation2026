import {
  addDays,
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  startOfMonth,
  startOfWeek,
} from "date-fns";
import { pl } from "date-fns/locale";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { t } from "@/features/calendar/i18n";
import { groupByDeadline } from "@/features/calendar/derive";
import { URGENCY_LABEL, type Urgency } from "@/lib/format";
import type { Case } from "@/lib/types";
import { cn } from "@/lib/utils";

const URGENCY_PRIORITY: Urgency[] = [
  "overdue",
  "today",
  "tomorrow",
  "soon",
  "normal",
  "closed",
];

const DAY_TONE: Record<Urgency, string> = {
  overdue:
    "border-red-300 bg-red-100 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-200",
  today:
    "border-orange-300 bg-orange-100 text-orange-900 dark:border-orange-800 dark:bg-orange-950 dark:text-orange-200",
  tomorrow:
    "border-amber-300 bg-amber-100 text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200",
  soon: "border-yellow-200 bg-yellow-50 text-yellow-900 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-200",
  normal:
    "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
  closed:
    "border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

const LEGEND: Urgency[] = ["overdue", "today", "tomorrow", "soon", "normal"];

function topUrgency(cases: Case[]): Urgency {
  for (const urgency of URGENCY_PRIORITY) {
    if (cases.some((item) => item.urgency === urgency)) return urgency;
  }
  return "normal";
}

type MonthGridProps = {
  cases: Case[];
  month: Date;
  referenceDate: Date;
  onMonthChange: (month: Date) => void;
  onSelectDay: (day: Date) => void;
};

export function MonthGrid({
  cases,
  month,
  referenceDate,
  onMonthChange,
  onSelectDay,
}: MonthGridProps) {
  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(month), { weekStartsOn: 1 });
    const end = endOfWeek(endOfMonth(month), { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  }, [month]);

  const weekdays = useMemo(() => {
    const start = startOfWeek(referenceDate, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end: addDays(start, 6) }).map((day) =>
      format(day, "EEEEEE", { locale: pl }),
    );
  }, [referenceDate]);

  const byDeadline = useMemo(() => groupByDeadline(cases), [cases]);

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            aria-label={t.month.previous}
            onClick={() => onMonthChange(addMonths(month, -1))}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            aria-label={t.month.next}
            onClick={() => onMonthChange(addMonths(month, 1))}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <p className="text-sm font-medium capitalize">
            {format(month, "LLLL yyyy", { locale: pl })}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onMonthChange(startOfMonth(referenceDate))}
        >
          {t.month.today}
        </Button>
      </div>

      <div className="grid grid-cols-7 gap-1">
        {weekdays.map((label) => (
          <div
            key={label}
            className="pb-1 text-center text-xs font-medium uppercase text-muted-foreground"
          >
            {label}
          </div>
        ))}

        {days.map((day) => {
          const dayCases = byDeadline.get(format(day, "yyyy-MM-dd")) ?? [];
          const urgency = dayCases.length > 0 ? topUrgency(dayCases) : null;
          const outside = !isSameMonth(day, month);
          return (
            <button
              key={day.toISOString()}
              type="button"
              onClick={() => onSelectDay(day)}
              aria-label={t.month.dayLabel(day, dayCases.length)}
              className={cn(
                "flex min-h-24 flex-col gap-1 rounded-md border p-2 text-left transition-colors hover:ring-2 hover:ring-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                urgency ? DAY_TONE[urgency] : "border-dashed bg-background",
                outside && "opacity-40",
                isSameDay(day, referenceDate) && "ring-2 ring-primary",
              )}
            >
              <span className="text-xs font-medium tabular-nums">
                {format(day, "d")}
              </span>
              {dayCases.length > 0 ? (
                <span className="flex flex-col gap-0.5">
                  <span className="w-fit rounded-full bg-background/80 px-1.5 py-0.5 text-xs font-semibold tabular-nums">
                    {dayCases.length}
                  </span>
                  <span className="text-[10px] font-medium leading-tight">
                    {URGENCY_LABEL[urgency ?? "normal"]}
                  </span>
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        {LEGEND.map((urgency) => (
          <span key={urgency} className="inline-flex items-center gap-1">
            <span
              className={cn("h-3 w-3 rounded-sm border", DAY_TONE[urgency])}
              aria-hidden="true"
            />
            {URGENCY_LABEL[urgency]}
          </span>
        ))}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">{t.month.legend}</p>
    </div>
  );
}
