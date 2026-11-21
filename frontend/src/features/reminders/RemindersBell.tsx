/**
 * Dzwonek z licznikiem przypomnień w nagłówku (W11).
 *
 * Lista jest liczona przez backend przy odczycie — nie ma schedulera ani
 * powiadomień push. Dzwonek odświeża się co minutę i pokazuje, ile wniosków
 * jest po terminie, na dziś albo na jutro.
 */

import { Bell } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { RemindersPanel } from "@/features/reminders/RemindersPanel";
import { useReminders } from "@/features/reminders/api";
import { reminderCounterLabel } from "@/features/reminders/derive";

export function RemindersBell() {
  const [open, setOpen] = useState(false);
  const { data, isLoading, error, refetch } = useReminders();
  const reminders = data ?? [];
  const count = reminders.length;
  const label = isLoading ? "Przypomnienia" : reminderCounterLabel(count);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={label}
          title={label}
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
          {count > 0 ? (
            <span
              aria-hidden="true"
              className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold leading-none text-destructive-foreground"
            >
              {count}
            </span>
          ) : null}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <RemindersPanel
          reminders={reminders}
          isLoading={isLoading}
          error={error}
          onRetry={() => void refetch()}
          onNavigate={() => setOpen(false)}
        />
      </PopoverContent>
    </Popover>
  );
}
