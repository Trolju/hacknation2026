/**
 * Typy przypomnień o terminach — lustro `app/modules/reminders/models.py`.
 *
 * Trzymane w module, a nie w `lib/types.ts`: przypomnienie jest widokiem
 * pochodnym wniosku, więc nie należy do zamrożonego kontraktu API.
 */

import type { Urgency } from "@/lib/format";
import type { CaseStatus } from "@/lib/types";

export type Reminder = {
  case_id: string;
  case_number: string;
  subject: string;
  deadline: string;
  /** Dni do terminu przepisane z wniosku — ujemne znaczą „po terminie”. */
  days_remaining: number;
  urgency: Urgency;
  status: CaseStatus;
  handler_initials: string;
  /** Gotowy tekst przypomnienia po polsku — składa go backend. */
  message: string;
};
