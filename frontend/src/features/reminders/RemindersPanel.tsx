/**
 * Lista przypomnień w nagłówku (W11).
 *
 * Komponent jest czysto prezentacyjny — dane dostaje z zewnątrz, więc można go
 * wyrenderować w teście bez sieci. Klik w przypomnienie otwiera kartę wniosku
 * w kalendarzu (`?case=<id>`).
 */

import { BellOff } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { UrgencyBadge } from "@/components/StatusBadges";
import { Badge } from "@/components/ui/badge";
import { pluralReminders, reminderHref } from "@/features/reminders/derive";
import type { Reminder } from "@/features/reminders/types";
import { formatShortDate } from "@/lib/format";

type RemindersPanelProps = {
  reminders: Reminder[];
  isLoading?: boolean;
  error?: unknown;
  onRetry?: () => void;
  /** Wywoływane po kliknięciu przypomnienia — pozwala zamknąć popover. */
  onNavigate?: () => void;
};

export function RemindersPanel({
  reminders,
  isLoading = false,
  error,
  onRetry,
  onNavigate,
}: RemindersPanelProps) {
  const count = reminders.length;

  return (
    <div>
      <div className="flex items-center justify-between gap-2 border-b px-3 py-2">
        <p className="text-sm font-medium">Przypomnienia o terminach</p>
        <Badge variant={count > 0 ? "destructive" : "secondary"}>
          {pluralReminders(count)}
        </Badge>
      </div>

      {isLoading ? (
        <div className="p-3">
          <LoadingState rows={2} variant="list" />
        </div>
      ) : error ? (
        <div className="p-3">
          <ErrorState error={error} onRetry={onRetry} compact />
        </div>
      ) : count === 0 ? (
        <div className="p-3">
          <EmptyState
            title="Brak pilnych terminów"
            description="Żaden wniosek nie ma terminu na dziś, jutro ani po terminie."
            icon={<BellOff className="h-6 w-6" />}
          />
        </div>
      ) : (
        <ul className="max-h-80 divide-y overflow-y-auto">
          {reminders.map((reminder) => (
            <li key={reminder.case_id}>
              <Link
                to={reminderHref(reminder)}
                onClick={onNavigate}
                className="block px-3 py-2 hover:bg-accent focus-visible:bg-accent focus-visible:outline-none"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs">{reminder.case_number}</span>
                  <UrgencyBadge
                    urgency={reminder.urgency}
                    days={reminder.days_remaining}
                  />
                </div>
                <p className="mt-1 line-clamp-2 text-sm">{reminder.subject}</p>
                <div className="mt-1 flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>{reminder.message}</span>
                  <span className="whitespace-nowrap">
                    {formatShortDate(reminder.deadline)}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
